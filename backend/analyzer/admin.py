from django.contrib import admin
from .models import Video, Comment, AnalysisJob, Report


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('youtube_video_id', 'title', 'channel', 'fetched_at')
    search_fields = ('youtube_video_id', 'title', 'channel')
    list_filter = ('fetched_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'video', 'is_spam', 'sentiment_label', 'sentiment_score', 'published_at')
    list_filter = ('is_spam', 'sentiment_label', 'published_at')
    search_fields = ('author', 'text', 'comment_id')


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('video__title', 'video__youtube_video_id')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'created_at')
    search_fields = ('job__video__title',)
