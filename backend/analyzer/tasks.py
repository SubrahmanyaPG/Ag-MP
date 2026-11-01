import logging
from django.utils import timezone
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from analyzer.models import AnalysisJob, Comment, Report, Video
from analyzer.services.youtube import YouTubeService
from analyzer.nlp.pipeline import run_nlp_pipeline
from analyzer.llm import generate_recommendations_and_titles

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='analyzer.tasks.analyze_video_task', soft_time_limit=1800, time_limit=1900)
def analyze_video_task(self, job_id: int, max_comments: int = 100, include_replies: bool = False):
    """
    Celery task that performs end-to-end video comment analysis with stage tracking:
    1. Fetches comments from YouTube API with pagination and progress reporting.
    2. Runs NLP pipeline (cleaning, spam detection, VADER sentiment, K-Means clustering, requests).
    3. Batch updates Comment records in PostgreSQL via bulk_update.
    4. Creates/updates Report record with sentiment breakdown, timeline, aspects, and topics.
    5. Updates AnalysisJob status and progress percentage.
    """
    try:
        job = AnalysisJob.objects.select_related('video').get(id=job_id)
    except AnalysisJob.DoesNotExist:
        logger.error(f"AnalysisJob with id {job_id} does not exist.")
        return {'error': f'Job {job_id} not found'}

    job.status = AnalysisJob.STATUS_RUNNING
    job.stage = 'fetching'
    job.progress_percent = 5
    job.fetched_count = 0
    job.total_estimate = max_comments or 0
    job.error_message = ''
    job.save(update_fields=['status', 'stage', 'progress_percent', 'fetched_count', 'total_estimate', 'error_message'])
    logger.info(f"Started analysis for Job #{job.id} (Video: {job.video.youtube_video_id})")

    try:
        # 1. Fetch fresh comments from YouTube API
        fetch_error = None
        def on_fetch_progress(fetched: int, total: int):
            try:
                job.fetched_count = fetched
                job.total_estimate = total
                # Progress during fetching: 5% to 30%
                pct = 5 + int(25 * (fetched / max(1, total)))
                job.progress_percent = min(30, pct)
                job.save(update_fields=['fetched_count', 'total_estimate', 'progress_percent'])
            except Exception:
                pass

        try:
            yt_service = YouTubeService()
            yt_service.fetch_and_store(
                video_url_or_id=job.video.youtube_video_id,
                max_comments=max_comments,
                include_replies=include_replies,
                progress_callback=on_fetch_progress
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

        comments_list = list(comments_qs)
        job.fetched_count = len(comments_list)
        job.total_estimate = len(comments_list)
        job.stage = 'filtering'
        job.progress_percent = 35
        job.save(update_fields=['stage', 'progress_percent', 'fetched_count', 'total_estimate'])

        comments_data = [
            {
                'id': c.id, 
                'text': c.text, 
                'author': c.author,
                'like_count': c.like_count,
                'published_at': c.published_at
            }
            for c in comments_list
        ]

        # 3. Execute NLP Pipeline (Spam, Sentiment, Aspect, Emotion, Topics)
        job.stage = 'sentiment'
        job.progress_percent = 55
        job.save(update_fields=['stage', 'progress_percent'])

        nlp_results = run_nlp_pipeline(comments_data, video_title=job.video.title)

        job.stage = 'topics'
        job.progress_percent = 75
        job.save(update_fields=['stage', 'progress_percent'])

        # 4. Batch update Comment annotations in DB using bulk_update
        comments_by_id = {c.id: c for c in comments_list}
        updated_comments = []
        for item in nlp_results['annotated_comments']:
            c_obj = comments_by_id.get(item.get('id'))
            if c_obj:
                c_obj.is_spam = item['is_spam']
                c_obj.spam_reason = item.get('spam_reason', '')
                c_obj.sentiment_label = item['sentiment_label']
                c_obj.sentiment_score = item['sentiment_score']
                c_obj.language = item.get('language', 'en')
                c_obj.aspect = item.get('aspect', 'general')
                c_obj.emotion = item.get('emotion', 'neutral')
                c_obj.needs_response = item.get('needs_response', False)
                c_obj.draft_reply = item.get('draft_reply', '')
                updated_comments.append(c_obj)

        if updated_comments:
            Comment.objects.bulk_update(
                updated_comments,
                [
                    'is_spam', 
                    'spam_reason', 
                    'sentiment_label', 
                    'sentiment_score', 
                    'language', 
                    'aspect', 
                    'emotion', 
                    'needs_response', 
                    'draft_reply'
                ],
                batch_size=1000
            )

        # 5. Call LLM for Content Recommendations & Suggested Titles
        job.stage = 'insights'
        job.progress_percent = 90
        job.save(update_fields=['stage', 'progress_percent'])

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
        job.stage = 'done'
        job.progress_percent = 100
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'stage', 'progress_percent', 'completed_at'])

        logger.info(f"Successfully completed AnalysisJob #{job.id} for Video {job.video.youtube_video_id}")
        return {
            'job_id': job.id,
            'status': 'done',
            'report_id': report.id,
            'comments_analyzed': len(comments_data),
            'spam_count': nlp_results['spam_count'],
        }

    except SoftTimeLimitExceeded:
        logger.error(f"AnalysisJob #{job.id} timed out (SoftTimeLimitExceeded).")
        job.status = AnalysisJob.STATUS_FAILED
        job.stage = 'failed'
        job.error_message = "Analysis timed out. The video has an extensive volume of comments. Try selecting a smaller sample depth."
        job.save(update_fields=['status', 'stage', 'error_message'])
        return {'job_id': job.id, 'status': 'failed', 'error': job.error_message}

    except Exception as exc:
        logger.exception(f"Error processing AnalysisJob #{job.id}: {exc}")
        job.status = AnalysisJob.STATUS_FAILED
        job.stage = 'failed'
        job.error_message = str(exc)
        job.save(update_fields=['status', 'stage', 'error_message'])
        raise exc
