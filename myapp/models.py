from django.db import models


class VideoAnalysis(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    RESULT_CHOICES = [
        ("real", "Real"),
        ("deepfake", "Deepfake"),
        ("inconclusive", "Inconclusive"),
    ]

    video = models.FileField(upload_to="videos/")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        blank=True,
    )
    confidence = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video {self.id} - {self.status}"