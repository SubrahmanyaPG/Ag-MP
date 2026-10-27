from django.db import models
from django.contrib.auth.models import User


class Video(models.Model):
    """
    Represents a YouTube video analyzed or tracked in the system.
    """
    youtube_video_id = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=500)
    channel = models.CharField(max_length=255, blank=True, default='')
    thumbnail_url = models.URLField(max_length=500, blank=True, default='')
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fetched_at']
        verbose_name = 'YouTube Video'
        verbose_name_plural = 'YouTube Videos'

    def __str__(self):
        return f"{self.title} ({self.youtube_video_id})"


class Comment(models.Model):
    """
    A single YouTube comment belonging to a Video.
    """
    video = models.ForeignKey(
        Video,
        related_name='comments',
        on_delete=models.CASCADE
    )
    comment_id = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    author = models.CharField(max_length=255, blank=True, default='')
    author_profile_image = models.URLField(max_length=500, blank=True, default='')
    text = models.TextField()
    like_count = models.IntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # NLP classification attributes
    is_spam = models.BooleanField(default=False, db_index=True)
    spam_reason = models.CharField(max_length=255, blank=True, default='', help_text='Explainability: Rule or ML trigger')
    sentiment_label = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        help_text='positive, neutral, or negative'
    )
    sentiment_score = models.FloatField(
        null=True,
        blank=True,
        help_text='Compound sentiment score between -1.0 and 1.0'
    )
    language = models.CharField(max_length=20, blank=True, default='en', help_text='Detected language/dialect e.g. en, hinglish')
    aspect = models.CharField(max_length=50, blank=True, default='general', help_text='content, audio, visuals, pacing')
    emotion = models.CharField(max_length=50, blank=True, default='neutral', help_text='joy, inquiry, frustration, surprise, neutral')
    needs_response = models.BooleanField(default=False, db_index=True, help_text='Flags questions or actionable viewer requests')
    draft_reply = models.TextField(blank=True, default='', help_text='AI-drafted creator response suggestion')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Video Comment'
        verbose_name_plural = 'Video Comments'

    def __str__(self):
        author_display = self.author or 'Anonymous'
        return f"{author_display}: {self.text[:50]}"


class AnalysisJob(models.Model):
    """
    Tracks the asynchronous Celery analysis job for a video.
    """
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_DONE, 'Done'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='analysis_jobs'
    )
    video = models.ForeignKey(
        Video,
        related_name='analysis_jobs',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analysis Job'
        verbose_name_plural = 'Analysis Jobs'

    def __str__(self):
        return f"Job #{self.id} for {self.video.youtube_video_id} [{self.status}]"


class Report(models.Model):
    """
    Final analyzed report with sentiment summary, timeline, aspect analytics,
    keywords, requests, and LLM-generated recommendations + titles.
    """
    job = models.OneToOneField(
        AnalysisJob,
        related_name='report',
        on_delete=models.CASCADE
    )
    sentiment_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text='Breakdown of positive, neutral, negative counts and percentages'
    )
    sentiment_timeline = models.JSONField(
        default=list,
        blank=True,
        help_text='Daily or weekly sentiment timeline points with averages and volume'
    )
    aspect_sentiment = models.JSONField(
        default=dict,
        blank=True,
        help_text='Breakdown across content, audio, visuals, pacing'
    )
    emotion_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text='Emotion percentages: joy, inquiry, frustration, surprise'
    )
    weighted_compound = models.FloatField(
        default=0.0,
        help_text='Like-weighted sentiment polarity score'
    )
    top_keywords = models.JSONField(
        default=list,
        blank=True,
        help_text='List of top extracted keywords or topic clusters'
    )
    top_requests = models.JSONField(
        default=list,
        blank=True,
        help_text='List of extracted audience requests and feedback'
    )
    recommendations = models.TextField(
        blank=True,
        default='',
        help_text='AI-generated content recommendations'
    )
    suggested_titles = models.JSONField(
        default=list,
        blank=True,
        help_text='AI-suggested YouTube video titles'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analysis Report'
        verbose_name_plural = 'Analysis Reports'

    def __str__(self):
        return f"Report for Job #{self.job_id} ({self.job.video.youtube_video_id})"
