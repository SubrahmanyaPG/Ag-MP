from rest_framework import serializers
from analyzer.models import Video, Comment, AnalysisJob, Report
from analyzer.services.youtube import extract_video_id


class VideoSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id',
            'youtube_video_id',
            'title',
            'channel',
            'thumbnail_url',
            'fetched_at',
            'comments_count',
        ]

    def get_comments_count(self, obj) -> int:
        return obj.comments.count()


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            'id',
            'comment_id',
            'author',
            'author_profile_image',
            'text',
            'like_count',
            'published_at',
            'is_spam',
            'spam_reason',
            'sentiment_label',
            'sentiment_score',
            'language',
            'aspect',
            'emotion',
            'needs_response',
            'draft_reply',
            'created_at',
        ]


class AnalysisJobSerializer(serializers.ModelSerializer):
    video = VideoSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, default=None)

    class Meta:
        model = AnalysisJob
        fields = [
            'id',
            'video',
            'username',
            'status',
            'error_message',
            'created_at',
            'completed_at',
        ]


class ReportSerializer(serializers.ModelSerializer):
    job_id = serializers.IntegerField(source='job.id', read_only=True)
    video = VideoSerializer(source='job.video', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'job_id',
            'video',
            'sentiment_summary',
            'sentiment_timeline',
            'aspect_sentiment',
            'emotion_breakdown',
            'weighted_compound',
            'top_keywords',
            'top_requests',
            'recommendations',
            'suggested_titles',
            'created_at',
        ]


class AnalyzeVideoRequestSerializer(serializers.Serializer):
    url = serializers.CharField(
        required=True,
        help_text="YouTube video URL or 11-character video ID"
    )
    max_comments = serializers.IntegerField(
        required=False,
        default=100,
        min_value=10,
        max_value=1000,
        help_text="Max comments to fetch and analyze (default: 100)"
    )

    def validate_url(self, value):
        try:
            video_id = extract_video_id(value)
            return video_id
        except ValueError as err:
            raise serializers.ValidationError(str(err))


from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user
