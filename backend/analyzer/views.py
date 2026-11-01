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
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from analyzer.models import Video, Comment, AnalysisJob, Report
from rest_framework_simplejwt.views import TokenObtainPairView
from analyzer.serializers import (
    VideoSerializer,
    CommentSerializer,
    AnalysisJobSerializer,
    ReportSerializer,
    AnalyzeVideoRequestSerializer,
    UserSerializer,
    UserRegistrationSerializer,
    EmailOrUsernameTokenObtainPairSerializer,
)
from analyzer.services.youtube import extract_video_id, YouTubeService
from analyzer.services.pdf_generator import generate_report_pdf
from analyzer.tasks import analyze_video_task


def _run_in_background(job_id: int, max_comments: int = 100, include_replies: bool = False):
    """
    Executes the analysis task in a daemon background thread
    with clean database connection management.
    """
    close_old_connections()
    try:
        analyze_video_task(job_id, max_comments=max_comments, include_replies=include_replies)
    except Exception as e:
        try:
            job = AnalysisJob.objects.get(id=job_id)
            job.status = AnalysisJob.STATUS_FAILED
            job.stage = 'failed'
            job.error_message = str(e)
            job.save(update_fields=['status', 'stage', 'error_message'])
        except Exception:
            pass
    finally:
        close_old_connections()


def get_job_for_user(job_id: int, user):
    """
    Retrieves an AnalysisJob if the requesting user is the owner,
    or if the user is staff.
    Existing jobs with owner=None are visible ONLY to staff.
    Raises NotFound (HTTP 404) if not found or unauthorized,
    preventing ID enumeration / probing.
    """
    try:
        job = AnalysisJob.objects.select_related('video').get(id=job_id)
    except (AnalysisJob.DoesNotExist, ValueError):
        raise NotFound("Analysis job not found.")

    if getattr(user, 'is_staff', False):
        return job

    if getattr(user, 'is_authenticated', False) and job.owner_id is not None and job.owner_id == user.id:
        return job

    raise NotFound("Analysis job not found.")


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class HealthCheckView(APIView):
    """
    Basic health check endpoint.
    """
    permission_classes = [permissions.AllowAny]

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
    Requires authentication.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'analyze'

    def post(self, request):
        serializer = AnalyzeVideoRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video_id = serializer.validated_data['url']  # validate_url returns the extracted 11-char ID
        max_comments = serializer.validated_data.get('max_comments', 100)
        include_replies = serializer.validated_data.get('include_replies', False)
        force_refresh = request.data.get('refresh', False)
        auth_user = request.user

        # 1. Fetch or create Video stub record
        video, _ = Video.objects.get_or_create(
            youtube_video_id=video_id,
            defaults={'title': f'YouTube Video ({video_id})'}
        )

        # 2. Check for recent cached analysis (< 24 hours) for this user to preserve YouTube API quota
        if not force_refresh:
            recent_completed_job = (
                AnalysisJob.objects
                .filter(video=video, status=AnalysisJob.STATUS_DONE, report__isnull=False, owner=auth_user)
                .order_by('-completed_at')
                .first()
            )
            if recent_completed_job and recent_completed_job.completed_at:
                age_hours = (timezone.now() - recent_completed_job.completed_at).total_seconds() / 3600
                if age_hours < 24:
                    return Response({
                        "job_id": recent_completed_job.id,
                        "status": "done",
                        "video_id": video.youtube_video_id,
                        "cached": True,
                        "message": f"Loaded cached analysis from {int(age_hours * 60)} minutes ago."
                    }, status=status.HTTP_200_OK)

        # 3. Create AnalysisJob with owner=request.user
        job = AnalysisJob.objects.create(
            video=video,
            owner=auth_user,
            status=AnalysisJob.STATUS_PENDING,
            stage='queued',
            total_estimate=max_comments or 0
        )

        # 4. Trigger async analysis
        # Celery worker is preferred; fallback to thread if broker is unreachable
        is_eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
        if is_eager:
            threading.Thread(target=_run_in_background, args=(job.id, max_comments, include_replies), daemon=True).start()
        else:
            try:
                analyze_video_task.delay(job.id, max_comments=max_comments, include_replies=include_replies)
            except Exception:
                threading.Thread(target=_run_in_background, args=(job.id, max_comments, include_replies), daemon=True).start()

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
    Polls the current execution status and multi-stage progress of an AnalysisJob.
    Accessible only to the job owner or staff.
    """
    def get(self, request, id):
        job = get_job_for_user(id, request.user)
        return Response({
            "job_id": job.id,
            "status": job.status,
            "stage": job.stage,
            "progress_percent": job.progress_percent,
            "fetched_count": job.fetched_count,
            "total_estimate": job.total_estimate,
            "video_id": job.video.youtube_video_id,
            "video_title": job.video.title,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "has_report": hasattr(job, 'report'),
        }, status=status.HTTP_200_OK)


class VideoPreviewView(APIView):
    """
    GET /api/videos/preview/?url=<url_or_id>
    Fetches lightweight statistics (title, comment count, and estimated quota units)
    before running a full analysis.
    """
    def get(self, request):
        url = request.query_params.get('url', '').strip()
        if not url:
            return Response({'error': 'The url query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from analyzer.services.youtube import fetch_video_preview
            preview = fetch_video_preview(url)
            return Response(preview, status=status.HTTP_200_OK)
        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)


class ReportDetailView(APIView):
    """
    GET /api/reports/{job_id}/
    Returns full analysis Report for a completed AnalysisJob.
    Accessible only to the job owner or staff.
    """
    def get(self, request, job_id):
        job = get_job_for_user(job_id, request.user)

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
            raise NotFound("Report not found for this completed job.")

        serializer = ReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecentReportsView(APIView):
    """
    GET /api/reports/recent/
    Returns list of up to 8 recently analyzed reports belonging to the user (or all if staff).
    """
    def get(self, request):
        if getattr(request.user, 'is_staff', False):
            reports = (
                Report.objects
                .select_related('job', 'job__video')
                .order_by('-created_at')[:8]
            )
        else:
            reports = (
                Report.objects
                .filter(job__owner=request.user)
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
    Allowed only if the user owns at least one job for that video (or is staff).
    """
    pagination_class = StandardResultsSetPagination

    def get(self, request, id):
        if str(id).isdigit():
            video = get_object_or_404(Video, id=int(id))
        else:
            video = get_object_or_404(Video, youtube_video_id=str(id))

        if not getattr(request.user, 'is_staff', False):
            has_job = AnalysisJob.objects.filter(video=video, owner=request.user).exists()
            if not has_job:
                raise NotFound("Video comments not found.")
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


from rest_framework.renderers import JSONRenderer


class ReportExportView(APIView):
    """
    GET /api/reports/{job_id}/export/
    Exports report comments and summary as CSV or PDF.
    Requires authentication and verifies job ownership (or staff).
    Returns 404 for unowned jobs to prevent ID enumeration.
    """
    renderer_classes = [JSONRenderer]

    def perform_content_negotiation(self, request, force=False):
        # Return JSONRenderer so auth and validation errors render as JSON,
        # while get() returns file stream HttpResponses directly.
        return (JSONRenderer(), 'application/json')

    def get(self, request, job_id):
        job = get_job_for_user(job_id, request.user)
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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

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
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/token/
    Accepts username OR email, along with password, and returns access and refresh tokens.
    """
    serializer_class = EmailOrUsernameTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the provided refresh token so it cannot be used again.
    Requires authentication.
    """
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required to log out."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Successfully logged out and token blacklisted."},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"error": "Invalid or already blacklisted token."},
                status=status.HTTP_400_BAD_REQUEST
            )


class MyAnalysesListView(APIView):
    """
    GET /api/analyses/my/
    Returns all analysis jobs belonging to the authenticated user (or all if staff).
    """
    def get(self, request):
        if getattr(request.user, 'is_staff', False):
            jobs = (
                AnalysisJob.objects
                .select_related('video', 'report')
                .order_by('-created_at')
            )
        else:
            jobs = (
                AnalysisJob.objects
                .filter(owner=request.user)
                .select_related('video', 'report')
                .order_by('-created_at')
            )
        serializer = AnalysisJobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserJobsListView(APIView):
    """
    GET /api/jobs/
    Returns paginated list of completed analysis jobs for the authenticated user (or all if staff).
    Populates video picker dropdowns for comparison and history dashboards.
    """
    def get(self, request):
        if getattr(request.user, 'is_staff', False):
            qs = AnalysisJob.objects.filter(status=AnalysisJob.STATUS_DONE, report__isnull=False)
        else:
            qs = AnalysisJob.objects.filter(owner=request.user, status=AnalysisJob.STATUS_DONE, report__isnull=False)

        qs = qs.select_related('video', 'report').order_by('-completed_at', '-created_at')

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)

        results = []
        for job in (page if page is not None else qs):
            summary = job.report.sentiment_summary if hasattr(job, 'report') else {}
            results.append({
                'id': job.id,
                'job_id': job.id,
                'video_id': job.video.youtube_video_id,
                'video_title': job.video.title,
                'channel': job.video.channel,
                'thumbnail_url': job.video.thumbnail_url,
                'comment_count': summary.get('total', 0) or job.video.comments.count(),
                'positive_percentage': summary.get('positive_percentage', 0.0),
                'neutral_percentage': summary.get('neutral_percentage', 0.0),
                'negative_percentage': summary.get('negative_percentage', 0.0),
                'average_compound': summary.get('average_compound', 0.0),
                'weighted_compound': getattr(job.report, 'weighted_compound', 0.0),
                'created_at': job.created_at,
                'completed_at': job.completed_at,
            })

        if page is not None:
            return paginator.get_paginated_response(results)
        return Response(results, status=status.HTTP_200_OK)


def _compute_comparison_data(job_a, job_b):
    r_a = job_a.report
    r_b = job_b.report
    s_a = r_a.sentiment_summary or {}
    s_b = r_b.sentiment_summary or {}

    total_a = s_a.get('total', 0)
    total_b = s_b.get('total', 0)
    spam_a = s_a.get('spam_filtered', 0)
    spam_b = s_b.get('spam_filtered', 0)
    raw_a = s_a.get('total_raw', total_a + spam_a)
    raw_b = s_b.get('total_raw', total_b + spam_b)

    spam_rate_a = round((spam_a / raw_a) * 100, 2) if raw_a > 0 else 0.0
    spam_rate_b = round((spam_b / raw_b) * 100, 2) if raw_b > 0 else 0.0

    pos_a = float(s_a.get('positive_percentage', 0.0))
    pos_b = float(s_b.get('positive_percentage', 0.0))
    neu_a = float(s_a.get('neutral_percentage', 0.0))
    neu_b = float(s_b.get('neutral_percentage', 0.0))
    neg_a = float(s_a.get('negative_percentage', 0.0))
    neg_b = float(s_b.get('negative_percentage', 0.0))

    avg_comp_a = float(s_a.get('average_compound', 0.0))
    avg_comp_b = float(s_b.get('average_compound', 0.0))
    weighted_comp_a = float(getattr(r_a, 'weighted_compound', 0.0))
    weighted_comp_b = float(getattr(r_b, 'weighted_compound', 0.0))

    requests_a = r_a.top_requests or []
    requests_b = r_b.top_requests or []

    def extract_kw_strings(kws):
        items = []
        for item in kws or []:
            if isinstance(item, dict):
                kw = item.get('keyword') or item.get('term') or ''
            else:
                kw = str(item)
            if kw.strip():
                items.append(kw.strip().lower())
        return items

    kw_list_a = extract_kw_strings(r_a.top_keywords)[:10]
    kw_list_b = extract_kw_strings(r_b.top_keywords)[:10]

    set_a = set(kw_list_a)
    set_b = set(kw_list_b)
    intersection = sorted(list(set_a.intersection(set_b)))
    union = set_a.union(set_b)
    jaccard_similarity = round(len(intersection) / len(union), 4) if union else 0.0

    unique_a = sorted(list(set_a - set_b))
    unique_b = sorted(list(set_b - set_a))

    deltas = {
        'comments_analyzed': total_a - total_b,
        'spam_rate': round(spam_rate_a - spam_rate_b, 2),
        'positive_percentage': round(pos_a - pos_b, 2),
        'neutral_percentage': round(neu_a - neu_b, 2),
        'negative_percentage': round(neg_a - neg_b, 2),
        'average_compound': round(avg_comp_a - avg_comp_b, 4),
        'weighted_compound': round(weighted_comp_a - weighted_comp_b, 4),
        'viewer_requests_count': len(requests_a) - len(requests_b),
    }

    return {
        'video_a': {
            'job_id': job_a.id,
            'video': VideoSerializer(job_a.video).data,
            'comments_analyzed': total_a,
            'spam_count': spam_a,
            'spam_rate': spam_rate_a,
            'positive_percentage': pos_a,
            'neutral_percentage': neu_a,
            'negative_percentage': neg_a,
            'average_compound': avg_comp_a,
            'weighted_compound': weighted_comp_a,
            'top_keywords': kw_list_a,
            'unique_keywords': unique_a,
            'viewer_requests': requests_a[:5],
            'viewer_requests_count': len(requests_a),
            'aspect_sentiment': r_a.aspect_sentiment,
            'emotion_breakdown': r_a.emotion_breakdown,
        },
        'video_b': {
            'job_id': job_b.id,
            'video': VideoSerializer(job_b.video).data,
            'comments_analyzed': total_b,
            'spam_count': spam_b,
            'spam_rate': spam_rate_b,
            'positive_percentage': pos_b,
            'neutral_percentage': neu_b,
            'negative_percentage': neg_b,
            'average_compound': avg_comp_b,
            'weighted_compound': weighted_comp_b,
            'top_keywords': kw_list_b,
            'unique_keywords': unique_b,
            'viewer_requests': requests_b[:5],
            'viewer_requests_count': len(requests_b),
            'aspect_sentiment': r_b.aspect_sentiment,
            'emotion_breakdown': r_b.emotion_breakdown,
        },
        'shared_keywords': intersection,
        'jaccard_similarity': jaccard_similarity,
        'deltas': deltas,
        'video1': {
            'job_id': job_a.id,
            'video': VideoSerializer(job_a.video).data,
            'sentiment_summary': s_a,
            'weighted_compound': weighted_comp_a,
            'aspect_sentiment': r_a.aspect_sentiment,
            'emotion_breakdown': r_a.emotion_breakdown,
            'top_keywords': r_a.top_keywords,
            'top_requests': requests_a,
        },
        'video2': {
            'job_id': job_b.id,
            'video': VideoSerializer(job_b.video).data,
            'sentiment_summary': s_b,
            'weighted_compound': weighted_comp_b,
            'aspect_sentiment': r_b.aspect_sentiment,
            'emotion_breakdown': r_b.emotion_breakdown,
            'top_keywords': r_b.top_keywords,
            'top_requests': requests_b,
        },
        'comparison_insights': {
            'higher_positivity_video_id': job_a.video.youtube_video_id if pos_a >= pos_b else job_b.video.youtube_video_id,
            'higher_engagement_score': job_a.video.youtube_video_id if weighted_comp_a >= weighted_comp_b else job_b.video.youtube_video_id,
            'lower_spam_count': job_a.video.youtube_video_id if spam_a <= spam_b else job_b.video.youtube_video_id,
        }
    }


class CompareVideosView(APIView):
    """
    GET /api/compare/?a=<id>&b=<id>
    Compares two analyzed videos side by side across sentiment, topics, aspects, and spam metrics.
    Only allows comparison of jobs owned by the requesting user (or staff).
    Validates a != b and both jobs are completed.
    Returns per-video metrics plus deltas (A minus B), keyword overlap & Jaccard similarity.
    """
    def get(self, request):
        job_a_id = request.query_params.get('a') or request.query_params.get('job1')
        job_b_id = request.query_params.get('b') or request.query_params.get('job2')

        if not job_a_id or not job_b_id:
            return Response({
                "error": "Both 'a' and 'b' query parameters are required for comparative analysis."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            id_a = int(job_a_id)
            id_b = int(job_b_id)
        except ValueError:
            return Response({"error": "Job IDs must be valid integers."}, status=status.HTTP_400_BAD_REQUEST)

        if id_a == id_b:
            return Response({
                "error": "Cannot compare a video with itself. Please select two distinct video jobs."
            }, status=status.HTTP_400_BAD_REQUEST)

        job_a = get_job_for_user(id_a, request.user)
        job_b = get_job_for_user(id_b, request.user)

        if job_a.status != AnalysisJob.STATUS_DONE or not hasattr(job_a, 'report'):
            return Response({
                "error": f"Job #{job_a.id} is not completed yet."
            }, status=status.HTTP_400_BAD_REQUEST)

        if job_b.status != AnalysisJob.STATUS_DONE or not hasattr(job_b, 'report'):
            return Response({
                "error": f"Job #{job_b.id} is not completed yet."
            }, status=status.HTTP_400_BAD_REQUEST)

        comparison = _compute_comparison_data(job_a, job_b)
        return Response(comparison, status=status.HTTP_200_OK)


class CompareInsightsView(APIView):
    """
    POST /api/compare/insights/
    Accepts { "a": <job_id>, "b": <job_id> } and generates 3 LLM-powered comparative bullet points.
    Strictly passes aggregated numbers (never raw comments) to Groq.
    """
    def post(self, request):
        job_a_id = request.data.get('a') or request.data.get('job1')
        job_b_id = request.data.get('b') or request.data.get('job2')

        if not job_a_id or not job_b_id:
            return Response({"error": "Both 'a' and 'b' job IDs are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            id_a = int(job_a_id)
            id_b = int(job_b_id)
        except ValueError:
            return Response({"error": "Job IDs must be valid integers."}, status=status.HTTP_400_BAD_REQUEST)

        if id_a == id_b:
            return Response({"error": "Cannot compare identical jobs."}, status=status.HTTP_400_BAD_REQUEST)

        job_a = get_job_for_user(id_a, request.user)
        job_b = get_job_for_user(id_b, request.user)

        if job_a.status != AnalysisJob.STATUS_DONE or not hasattr(job_a, 'report') or job_b.status != AnalysisJob.STATUS_DONE or not hasattr(job_b, 'report'):
            return Response({"error": "Both jobs must be completed to generate comparative insights."}, status=status.HTTP_400_BAD_REQUEST)

        comp_data = _compute_comparison_data(job_a, job_b)
        from analyzer.llm.service import generate_comparison_insights
        insights = generate_comparison_insights(comp_data)
        return Response({"insights": insights}, status=status.HTTP_200_OK)


class DraftReplyView(APIView):
    """
    POST /api/comments/<int:comment_id>/draft-reply/
    Generates a personalized creator response for a specific comment.
    Allowed only if the user owns a job for that video (or is staff).
    """
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment.objects.select_related('video'), id=comment_id)
        if not getattr(request.user, 'is_staff', False):
            if not AnalysisJob.objects.filter(video=comment.video, owner=request.user).exists():
                raise NotFound("Comment not found.")

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



