from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    HealthCheckView,
    AnalyzeVideoView,
    JobStatusView,
    ReportExportView,
    ReportDetailView,
    RecentReportsView,
    VideoCommentsListView,
    RegisterView,
    MeView,
    MyAnalysesListView,
    CompareVideosView,
    DraftReplyView,
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('videos/analyze/', AnalyzeVideoView.as_view(), name='video-analyze'),
    path('jobs/<int:id>/status/', JobStatusView.as_view(), name='job-status'),
    path('analyses/my/', MyAnalysesListView.as_view(), name='analyses-my'),
    path('analyses/compare/', CompareVideosView.as_view(), name='analyses-compare'),
    path('reports/recent/', RecentReportsView.as_view(), name='reports-recent'),
    path('reports/<int:job_id>/export/', ReportExportView.as_view(), name='report-export'),
    path('reports/<int:job_id>/', ReportDetailView.as_view(), name='report-detail'),
    path('videos/<str:id>/comments/', VideoCommentsListView.as_view(), name='video-comments'),
    path('comments/<int:comment_id>/draft-reply/', DraftReplyView.as_view(), name='comment-draft-reply'),
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
]
