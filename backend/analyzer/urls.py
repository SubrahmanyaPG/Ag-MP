from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    HealthCheckView,
    AnalyzeVideoView,
    VideoPreviewView,
    JobStatusView,
    UserJobsListView,
    ReportExportView,
    ReportDetailView,
    RecentReportsView,
    VideoCommentsListView,
    RegisterView,
    LoginView,
    LogoutView,
    MeView,
    MyAnalysesListView,
    CompareVideosView,
    CompareInsightsView,
    DraftReplyView,
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('videos/preview/', VideoPreviewView.as_view(), name='video-preview'),
    path('videos/analyze/', AnalyzeVideoView.as_view(), name='video-analyze'),
    path('jobs/', UserJobsListView.as_view(), name='jobs-list'),
    path('jobs/<int:id>/status/', JobStatusView.as_view(), name='job-status'),
    path('compare/', CompareVideosView.as_view(), name='compare-videos'),
    path('compare/insights/', CompareInsightsView.as_view(), name='compare-insights'),
    path('analyses/my/', MyAnalysesListView.as_view(), name='analyses-my'),
    path('analyses/compare/', CompareVideosView.as_view(), name='analyses-compare'),
    path('reports/recent/', RecentReportsView.as_view(), name='reports-recent'),
    path('reports/<int:job_id>/export/', ReportExportView.as_view(), name='report-export'),
    path('reports/<int:job_id>/', ReportDetailView.as_view(), name='report-detail'),
    path('videos/<str:id>/comments/', VideoCommentsListView.as_view(), name='video-comments'),
    path('comments/<int:comment_id>/draft-reply/', DraftReplyView.as_view(), name='comment-draft-reply'),
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/token/', LoginView.as_view(), name='token-obtain-pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
]
