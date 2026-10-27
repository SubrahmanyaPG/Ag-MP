import logging
from django.utils import timezone
from celery import shared_task
from analyzer.models import AnalysisJob, Comment, Report, Video
from analyzer.services.youtube import YouTubeService
from analyzer.nlp.pipeline import run_nlp_pipeline
from analyzer.llm import generate_recommendations_and_titles

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='analyzer.tasks.analyze_video_task')
def analyze_video_task(self, job_id: int, max_comments: int = 100):
    """
    Celery task that performs end-to-end video comment analysis:
    1. Fetches/updates comments from YouTube API (if key is set).
    2. Runs NLP pipeline (cleaning, spam detection, VADER sentiment, K-Means clustering, requests).
    3. Updates Comment records in PostgreSQL.
    4. Creates/updates the Report record with sentiment breakdown and topics.
    5. Updates AnalysisJob status (running -> done / failed).
    """
    try:
        job = AnalysisJob.objects.select_related('video').get(id=job_id)
    except AnalysisJob.DoesNotExist:
        logger.error(f"AnalysisJob with id {job_id} does not exist.")
        return {'error': f'Job {job_id} not found'}

    job.status = AnalysisJob.STATUS_RUNNING
    job.error_message = ''
    job.save(update_fields=['status', 'error_message'])
    logger.info(f"Started analysis for Job #{job.id} (Video: {job.video.youtube_video_id})")

    try:
        # 1. Fetch fresh comments from YouTube if API key configured
        fetch_error = None
        try:
            yt_service = YouTubeService()
            yt_service.fetch_and_store(
                video_url_or_id=job.video.youtube_video_id,
                max_comments=max_comments
            )
        except Exception as yt_err:
            fetch_error = yt_err
            logger.warning(
                f"YouTube API fetch skipped or encountered an error ({yt_err}). "
                f"Checking for existing comments stored in database."
            )

        # 2. Retrieve comments for this video from PostgreSQL
        comments_qs = Comment.objects.filter(video=job.video)
        if not comments_qs.exists():
            if fetch_error:
                error_str = str(fetch_error)
                if "comments are disabled" in error_str.lower() or "commentsdisabled" in error_str.lower():
                    raise ValueError(
                        f"Comments are disabled on YouTube for video '{job.video.youtube_video_id}'. "
                        f"The creator or YouTube policy (e.g. 'Made for Kids' or auto-generated music track) has disabled comments for this video."
                    )
                elif "quota" in error_str.lower():
                    raise ValueError(
                        f"YouTube Data API daily quota limit reached. Please wait for quota reset or configure an alternate API key."
                    )
                elif "no video found" in error_str.lower() or "notfound" in error_str.lower():
                    raise ValueError(
                        f"Video '{job.video.youtube_video_id}' was not found on YouTube or has been set to private."
                    )
                else:
                    raise ValueError(
                        f"Unable to retrieve comments for video '{job.video.youtube_video_id}': {error_str}"
                    )
            else:
                raise ValueError(
                    f"This video currently has 0 comments on YouTube. Please select a video with active audience comments to analyze."
                )

        comments_data = [
            {
                'id': c.id, 
                'text': c.text, 
                'author': c.author,
                'like_count': c.like_count,
                'published_at': c.published_at
            }
            for c in comments_qs
        ]

        # 3. Execute NLP Pipeline
        nlp_results = run_nlp_pipeline(comments_data, video_title=job.video.title)

        # 4. Update Comment annotations in DB
        for item in nlp_results['annotated_comments']:
            if 'id' in item:
                Comment.objects.filter(id=item['id']).update(
                    is_spam=item['is_spam'],
                    spam_reason=item.get('spam_reason', ''),
                    sentiment_label=item['sentiment_label'],
                    sentiment_score=item['sentiment_score'],
                    language=item.get('language', 'en'),
                    aspect=item.get('aspect', 'general'),
                    emotion=item.get('emotion', 'neutral'),
                    needs_response=item.get('needs_response', False),
                    draft_reply=item.get('draft_reply', '')
                )

        # 5. Call LLM for Content Recommendations & Suggested Titles
        # Passes aggregated metrics ONLY (no raw comments) to optimize token usage
        llm_insights = generate_recommendations_and_titles(
            video_title=job.video.title,
            channel=job.video.channel,
            sentiment_summary=nlp_results['sentiment_summary'],
            top_keywords=nlp_results['top_keywords'],
            top_requests=nlp_results['top_requests'],
            topic_clusters=nlp_results.get('topic_clusters', [])
        )

        # 6. Create or Update Report in DB
        report, _ = Report.objects.update_or_create(
            job=job,
            defaults={
                'sentiment_summary': nlp_results['sentiment_summary'],
                'sentiment_timeline': nlp_results.get('sentiment_timeline', []),
                'aspect_sentiment': nlp_results.get('aspect_sentiment', {}),
                'emotion_breakdown': nlp_results.get('emotion_breakdown', {}),
                'weighted_compound': nlp_results.get('weighted_compound', 0.0),
                'top_keywords': nlp_results['top_keywords'],
                'top_requests': nlp_results['top_requests'],
                'recommendations': llm_insights.get('recommendations', ''),
                'suggested_titles': llm_insights.get('suggested_titles', []),
            }
        )

        # 7. Mark Job Completed
        job.status = AnalysisJob.STATUS_DONE
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'completed_at'])

        logger.info(f"Successfully completed AnalysisJob #{job.id} for Video {job.video.youtube_video_id}")
        return {
            'job_id': job.id,
            'status': 'done',
            'report_id': report.id,
            'comments_analyzed': len(comments_data),
            'spam_count': nlp_results['spam_count'],
        }

    except Exception as exc:
        logger.exception(f"Error processing AnalysisJob #{job.id}: {exc}")
        job.status = AnalysisJob.STATUS_FAILED
        job.error_message = str(exc)
        job.save(update_fields=['status', 'error_message'])
        raise exc
