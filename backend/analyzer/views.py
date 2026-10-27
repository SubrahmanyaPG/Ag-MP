import csv
import threading
from datetime import timedelta
from io import StringIO
from django.conf import settings
from django.db import close_old_connections
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from analyzer.models import Video, Comment, AnalysisJob, Report
from analyzer.serializers import (
    VideoSerializer,
    CommentSerializer,
    AnalysisJobSerializer,
    ReportSerializer,
    AnalyzeVideoRequestSerializer,
    UserSerializer,
    UserRegistrationSerializer,
)
from analyzer.services.youtube import extract_video_id, YouTubeService
from analyzer.services.pdf_generator import generate_report_pdf
from analyzer.tasks import analyze_video_task


def _run_in_background(job_id: int, max_comments: int):
    """
    Executes the analysis task in a daemon background thread
    with clean database connection management.
    """
    close_old_connections()
    try:
        analyze_video_task(job_id, max_comments=max_comments)
    except Exception as e:
        try:
            job = AnalysisJob.objects.get(id=job_id)
            job.status = AnalysisJob.STATUS_FAILED
            job.error_message = str(e)
            job.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
    finally:
        close_old_connections()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class HealthCheckView(APIView):
    """
    Basic health check endpoint.
    """
    def get(self, request):
        return Response({
            "status": "healthy",
            "message": "YouTube Sentiment Analyzer API is active."
        }, status=status.HTTP_200_OK)


class AnalyzeVideoView(APIView):
    """
    POST /api/videos/analyze/
    Accepts a YouTube video URL or ID.
    Creates an AnalysisJob and dispatches the background task.
    """
    def post(self, request):
        serializer = AnalyzeVideoRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video_id = serializer.validated_data['url']  # validate_url returns the extracted 11-char ID
        max_comments = serializer.validated_data.get('max_comments', 100)
        force_refresh = request.data.get('refresh', False)
        auth_user = request.user if request.user and request.user.is_authenticated else None

        # 1. Fetch or create Video stub record
        video, _ = Video.objects.get_or_create(
            youtube_video_id=video_id,
            defaults={'title': f'YouTube Video ({video_id})'}
        )

        # 2. Check for recent cached analysis (< 24 hours) to preserve YouTube API quota
        if not force_refresh:
            recent_completed_job = (
                AnalysisJob.objects
                .filter(video=video, status=AnalysisJob.STATUS_DONE, report__isnull=False)
                .order_by('-completed_at')
                .first()
            )
            if recent_completed_job and recent_completed_job.completed_at:
                age_hours = (timezone.now() - recent_completed_job.completed_at).total_seconds() / 3600
                if age_hours < 24:
                    if auth_user and not recent_completed_job.user:
                        recent_completed_job.user = auth_user
                        recent_completed_job.save(update_fields=['user'])
                    return Response({
                        "job_id": recent_completed_job.id,
                        "status": "done",
                        "video_id": video.youtube_video_id,
                        "cached": True,
                        "message": f"Loaded cached analysis from {int(age_hours * 60)} minutes ago."
                    }, status=status.HTTP_200_OK)

        # 3. Create AnalysisJob
        job = AnalysisJob.objects.create(
            video=video,
            user=auth_user,
            status=AnalysisJob.STATUS_PENDING
        )

        # 4. Trigger async analysis
        # Always run in a non-blocking background worker thread
        # This ensures execution succeeds instantly whether Celery/Redis daemon is running or not!
        is_eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
        if is_eager:
            threading.Thread(target=_run_in_background, args=(job.id, max_comments), daemon=True).start()
        else:
            try:
                analyze_video_task.delay(job.id, max_comments=max_comments)
            except Exception:
                threading.Thread(target=_run_in_background, args=(job.id, max_comments), daemon=True).start()

        return Response({
            "job_id": job.id,
            "status": job.status,
            "video_id": video.youtube_video_id,
            "cached": False,
            "message": "Analysis job initiated successfully."
        }, status=status.HTTP_202_ACCEPTED)


class JobStatusView(APIView):
    """
    GET /api/jobs/{id}/status/
    Polls the current execution status of an AnalysisJob.
    """
    def get(self, request, id):
        job = get_object_or_404(AnalysisJob.objects.select_related('video'), id=id)
        return Response({
            "job_id": job.id,
            "status": job.status,
            "video_id": job.video.youtube_video_id,
            "video_title": job.video.title,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "has_report": hasattr(job, 'report'),
        }, status=status.HTTP_200_OK)


class ReportDetailView(APIView):
    """
    GET /api/reports/{job_id}/
    Returns full analysis Report for a completed AnalysisJob.
    """
    def get(self, request, job_id):
        job = get_object_or_404(AnalysisJob, id=job_id)

        if job.status == AnalysisJob.STATUS_PENDING or job.status == AnalysisJob.STATUS_RUNNING:
            return Response({
                "job_id": job.id,
                "status": job.status,
                "message": "Analysis is still running. Please continue polling."
            }, status=status.HTTP_202_ACCEPTED)

        if job.status == AnalysisJob.STATUS_FAILED:
            return Response({
                "job_id": job.id,
                "status": job.status,
                "error": job.error_message or "Analysis job failed."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            report = job.report
        except Report.DoesNotExist:
            return Response({
                "error": "Report not found for this completed job."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecentReportsView(APIView):
    """
    GET /api/reports/recent/
    Returns list of up to 8 recently analyzed reports with video metadata.
    """
    def get(self, request):
        reports = (
            Report.objects
            .select_related('job', 'job__video')
            .order_by('-created_at')[:8]
        )
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VideoCommentsListView(APIView):
    """
    GET /api/videos/{id}/comments/
    Returns paginated comments for a video, filterable by:
    - ?sentiment=positive|neutral|negative
    - ?is_spam=true|false
    - ?search=keyword
    Accepts numeric DB id or YouTube video ID string.
    """
    pagination_class = StandardResultsSetPagination

    def get(self, request, id):
        if str(id).isdigit():
            video = get_object_or_404(Video, id=int(id))
        else:
            video = get_object_or_404(Video, youtube_video_id=str(id))

        comments = video.comments.all()

        # Filter by sentiment
        sentiment_param = request.query_params.get('sentiment')
        if sentiment_param and sentiment_param.lower() in ('positive', 'neutral', 'negative'):
            comments = comments.filter(sentiment_label=sentiment_param.lower())

        # Filter by spam status
        spam_param = request.query_params.get('is_spam')
        if spam_param is not None:
            if spam_param.lower() in ('true', '1'):
                comments = comments.filter(is_spam=True)
            elif spam_param.lower() in ('false', '0'):
                comments = comments.filter(is_spam=False)

        # Keyword search
        search_query = request.query_params.get('search')
        if search_query:
            comments = comments.filter(text__icontains=search_query)

        # Filter by questions / needs response
        needs_resp = request.query_params.get('needs_response')
        if needs_resp is not None:
            if needs_resp.lower() in ('true', '1'):
                comments = comments.filter(needs_response=True)
            elif needs_resp.lower() in ('false', '0'):
                comments = comments.filter(needs_response=False)

        # Filter by aspect (content, audio, visuals, pacing)
        aspect_param = request.query_params.get('aspect')
        if aspect_param:
            comments = comments.filter(aspect=aspect_param.lower())

        # Filter by emotion (joy, inquiry, frustration, surprise)
        emotion_param = request.query_params.get('emotion')
        if emotion_param:
            comments = comments.filter(emotion=emotion_param.lower())

        # Ordering / Sorting
        ordering = request.query_params.get('ordering')
        if ordering in ('-like_count', 'like_count', '-sentiment_score', 'sentiment_score', '-published_at', 'published_at'):
            comments = comments.order_by(ordering)

        paginator = self.pagination_class()
        paginated_comments = paginator.paginate_queryset(comments, request)
        serializer = CommentSerializer(paginated_comments, many=True)
        return paginator.get_paginated_response(serializer.data)


from django.views import View


class ReportExportView(View):
    """
    GET /api/reports/{job_id}/export/
    Exports report comments and summary as CSV.
    Uses standard Django View to cleanly handle file streaming without DRF content negotiation conflicts.
    """
    def get(self, request, job_id):
        job = get_object_or_404(AnalysisJob.objects.select_related('video'), id=job_id)
        export_format = request.GET.get('format', 'csv').lower()

        try:
            report = job.report
        except (Report.DoesNotExist, Exception):
            return HttpResponse('{"error": "No report available for this job to export."}', content_type='application/json', status=404)

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            filename = f"youtube_sentiment_report_{job.video.youtube_video_id}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            writer = csv.writer(response)
            # Metadata header
            writer.writerow(["Automated Audience Sentiment and Feedback Analysis Report"])
            writer.writerow(["Video Title", job.video.title])
            writer.writerow(["Video ID", job.video.youtube_video_id])
            writer.writerow(["Channel", job.video.channel])
            writer.writerow(["Completed At", str(job.completed_at)])
            writer.writerow([])

            # Sentiment summary
            ss = report.sentiment_summary
            writer.writerow(["--- Sentiment Breakdown ---"])
            writer.writerow(["Positive (%)", ss.get('positive_percentage', 0)])
            writer.writerow(["Neutral (%)", ss.get('neutral_percentage', 0)])
            writer.writerow(["Negative (%)", ss.get('negative_percentage', 0)])
            writer.writerow(["Average Compound Score", ss.get('average_compound', 0)])
            writer.writerow([])

            # Comments detail
            writer.writerow(["--- Comment Details ---"])
            writer.writerow(["Author", "Comment Text", "Published At", "Is Spam", "Sentiment Label", "Sentiment Score", "Like Count"])
            for c in job.video.comments.all():
                writer.writerow([
                    c.author,
                    c.text.replace('\n', ' '),
                    str(c.published_at),
                    "SPAM" if c.is_spam else "HAM",
                    c.sentiment_label or "N/A",
                    c.sentiment_score or 0.0,
                    c.like_count
                ])

            return response

        elif export_format == 'pdf':
            pdf_bytes = generate_report_pdf(report)
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"youtube_sentiment_report_{job.video.youtube_video_id}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        return HttpResponse(f'{{"error": "Unsupported export format \'{export_format}\'."}}', content_type='application/json', status=400)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Registers a new user and returns JWT tokens along with user details.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "message": "User registered successfully."
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """
    GET /api/auth/me/
    Retrieves currently authenticated user info from JWT header.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyAnalysesListView(APIView):
    """
    GET /api/analyses/my/
    Returns all analysis jobs belonging to the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        jobs = (
            AnalysisJob.objects
            .filter(user=request.user)
            .select_related('video', 'report')
            .order_by('-created_at')
        )
        serializer = AnalysisJobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompareVideosView(APIView):
    """
    GET /api/analyses/compare/?job1=<id>&job2=<id>
    Compares two analyzed videos side by side across sentiment, topics, aspects, and spam metrics.
    """
    def get(self, request):
        job1_id = request.query_params.get('job1')
        job2_id = request.query_params.get('job2')

        if not job1_id or not job2_id:
            return Response({
                "error": "Both 'job1' and 'job2' query parameters are required for comparative analysis."
            }, status=status.HTTP_400_BAD_REQUEST)

        job1 = get_object_or_404(AnalysisJob.objects.select_related('video'), id=job1_id)
        job2 = get_object_or_404(AnalysisJob.objects.select_related('video'), id=job2_id)

        try:
            r1 = job1.report
            r2 = job2.report
        except (Report.DoesNotExist, Exception):
            return Response({
                "error": "Both jobs must have successfully completed reports to perform comparison."
            }, status=status.HTTP_400_BAD_REQUEST)

        v1_pos = r1.sentiment_summary.get('positive_percentage', 0)
        v2_pos = r2.sentiment_summary.get('positive_percentage', 0)
        v1_spam = r1.sentiment_summary.get('spam_filtered', 0)
        v2_spam = r2.sentiment_summary.get('spam_filtered', 0)

        comparison = {
            "video1": {
                "job_id": job1.id,
                "video": VideoSerializer(job1.video).data,
                "sentiment_summary": r1.sentiment_summary,
                "weighted_compound": r1.weighted_compound,
                "aspect_sentiment": r1.aspect_sentiment,
                "emotion_breakdown": r1.emotion_breakdown,
                "top_keywords": (r1.top_keywords or [])[:6],
                "top_requests": (r1.top_requests or [])[:4],
            },
            "video2": {
                "job_id": job2.id,
                "video": VideoSerializer(job2.video).data,
                "sentiment_summary": r2.sentiment_summary,
                "weighted_compound": r2.weighted_compound,
                "aspect_sentiment": r2.aspect_sentiment,
                "emotion_breakdown": r2.emotion_breakdown,
                "top_keywords": (r2.top_keywords or [])[:6],
                "top_requests": (r2.top_requests or [])[:4],
            },
            "comparison_insights": {
                "higher_positivity_video_id": job1.video.youtube_video_id if v1_pos >= v2_pos else job2.video.youtube_video_id,
                "higher_engagement_score": job1.video.youtube_video_id if r1.weighted_compound >= r2.weighted_compound else job2.video.youtube_video_id,
                "lower_spam_count": job1.video.youtube_video_id if v1_spam <= v2_spam else job2.video.youtube_video_id,
            }
        }
        return Response(comparison, status=status.HTTP_200_OK)


class DraftReplyView(APIView):
    """
    POST /api/comments/<int:comment_id>/draft-reply/
    Generates a personalized creator response for a specific comment.
    """
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment.objects.select_related('video'), id=comment_id)
        from analyzer.nlp.aspect_emotion import draft_creator_reply
        draft = draft_creator_reply(
            comment.text, 
            author=comment.author, 
            video_title=comment.video.title
        )
        comment.draft_reply = draft
        comment.save(update_fields=['draft_reply'])
        return Response({
            "comment_id": comment.id,
            "author": comment.author,
            "comment_text": comment.text,
            "draft_reply": draft
        }, status=status.HTTP_200_OK)



