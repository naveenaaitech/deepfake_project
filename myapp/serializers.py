from rest_framework import serializers
from .models import VideoAnalysis


class VideoAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoAnalysis
        fields = [
            "id",
            "video",
            "status",
            "result",
            "confidence",
            "error_message",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "result",
            "confidence",
            "error_message",
            "created_at",
        ]

    def validate_video(self, video):
        allowed_types = {
            "video/mp4",
            "video/webm",
            "video/quicktime",
        }

        if video.size > 100 * 1024 * 1024:
            raise serializers.ValidationError(
                "Video size must be less than 100 MB."
            )

        if video.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Upload an MP4, WebM, or MOV video."
            )

        return video
