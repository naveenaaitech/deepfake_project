import os
import time
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from myapp.models import VideoAnalysis
from myapp.views import _run_video_analysis_task
from myapp.services.video_processor import validate_video_file


class VideoAnalysisAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.sample_video_path = os.path.join(
            "media", "videos", "5237521-hd_1080_1920_30fps.mp4"
        )

    def test_upload_api_success(self):
        """Test video upload endpoint with valid file."""
        video_content = b"fake video content simulating mp4"
        uploaded_video = SimpleUploadedFile(
            "test_sample.mp4",
            video_content,
            content_type="video/mp4",
        )
        url = reverse("video-upload")
        response = self.client.post(url, {"video": uploaded_video}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("analysis", response.data)
        self.assertEqual(response.data["analysis"]["status"], "pending")

    def test_upload_api_invalid_format(self):
        """Test video upload with unsupported content type."""
        uploaded_doc = SimpleUploadedFile(
            "document.txt",
            b"text content",
            content_type="text/plain",
        )
        url = reverse("video-upload")
        response = self.client.post(url, {"video": uploaded_doc}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_result_api_not_found(self):
        """Test retrieving nonexistent analysis record returns 404."""
        url = reverse("video-result", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_history_api(self):
        """Test video analysis history listing."""
        VideoAnalysis.objects.create(status="completed", result="real", confidence=0.92)
        VideoAnalysis.objects.create(status="completed", result="deepfake", confidence=0.88)

        url = reverse("video-history")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_start_analysis_not_found(self):
        """Test starting nonexistent analysis returns 404."""
        url = reverse("start-analysis", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_video_file_failure_handling(self):
        """Test that missing video file results in 'failed' status with clear error."""
        analysis = VideoAnalysis.objects.create(
            video="videos/nonexistent_file_xyz.mp4",
            status="pending",
        )
        _run_video_analysis_task(analysis.id)

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, "failed")
        self.assertIn("not found", analysis.error_message.lower())

    def test_video_processor_invalid_file(self):
        """Test validate_video_file raises ValueError for missing path."""
        with self.assertRaises(ValueError):
            validate_video_file("nonexistent_path.mp4")

    def test_full_pipeline_on_sample_video(self):
        """
        Integration test: verify that running the full AI pipeline on the
        sample video completes, persists a valid prediction, and sets confidence.
        """
        if not os.path.exists(self.sample_video_path):
            self.skipTest("Sample video file not available on disk.")

        analysis = VideoAnalysis.objects.create(
            video="videos/5237521-hd_1080_1920_30fps.mp4",
            status="pending",
        )

        # Run analysis worker directly
        _run_video_analysis_task(analysis.id)

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, "completed")
        self.assertIn(analysis.result, ["real", "deepfake", "inconclusive"])
        self.assertIsNotNone(analysis.confidence)
        self.assertTrue(0.0 <= analysis.confidence <= 1.0)
