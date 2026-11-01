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
    username = serializers.CharField(source='owner.username', read_only=True, default=None)

    class Meta:
        model = AnalysisJob
        fields = [
            'id',
            'video',
            'username',
            'status',
            'stage',
            'progress_percent',
            'fetched_count',
            'total_estimate',
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
        allow_null=True,
        default=100,
        min_value=10,
        max_value=20000,
        help_text="Max comments to fetch and analyze (default: 100, null for all up to hard cap)"
    )
    include_replies = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Include comment replies where available"
    )

    def validate_url(self, value):
        try:
            video_id = extract_video_id(value)
            return video_id
        except ValueError as err:
            raise serializers.ValidationError(str(err))


from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def validate_username(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Username cannot be empty.")
        if User.objects.filter(username__iexact=value.strip()).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value.strip()

    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email address is required.")
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized

    def validate(self, data):
        password = data.get('password')
        user_for_validation = User(
            username=data.get('username'),
            email=data.get('email')
        )
        try:
            validate_password(password, user=user_for_validation)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Allows user authentication via either username or email address.
    """
    def validate(self, attrs):
        login_identifier = attrs.get(self.username_field)
        password = attrs.get('password')

        if login_identifier:
            login_identifier = login_identifier.strip()
            user = User.objects.filter(
                Q(username__iexact=login_identifier) | Q(email__iexact=login_identifier)
            ).first()
            if user and user.check_password(password):
                attrs[self.username_field] = user.username

        return super().validate(attrs)
