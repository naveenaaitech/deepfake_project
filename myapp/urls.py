from django.urls import path
from .views import (
    index,
    StartAnalysisAPIView,
    save_detection_result,
    VideoUploadAPIView,
    VideoResultAPIView,
    VideoHistoryAPIView,
)

urlpatterns = [
    path("", index, name="home"),
    path(
        "upload/",
        VideoUploadAPIView.as_view(),
        name="video-upload",
    ),
    path(
        "result/<int:pk>/",
        VideoResultAPIView.as_view(),
        name="video-result",
    ),
    path(
        "history/",
        VideoHistoryAPIView.as_view(),
        name="video-history",
    ),
    path(
    "start/<int:pk>/",
    StartAnalysisAPIView.as_view(),
    name="start-analysis",
),
path(
    "save-result/<int:pk>/",
    save_detection_result,
    name="save-detection-result",
),
]