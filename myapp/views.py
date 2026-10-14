import os
import threading
from django.shortcuts import render
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view

from .models import VideoAnalysis
from .serializers import VideoAnalysisSerializer
from .services.deepfake_detector import detect_deepfake_in_video


def index(request):
    """Render main application dashboard."""
    return render(request, "index.html")


def _run_video_analysis_task(analysis_id):
    """
    Background worker thread to execute the AI deepfake analysis pipeline.
    Ensures safe SQLite connection management and robust error logging.
    """
    try:
        try:
            analysis = VideoAnalysis.objects.get(pk=analysis_id)
        except VideoAnalysis.DoesNotExist:
            print(f"[AnalysisWorker] Analysis record {analysis_id} not found.")
            return

        video_path = None
        if analysis.video:
            try:
                if os.path.exists(analysis.video.path):
                    video_path = analysis.video.path
            except Exception:
                pass
            if not video_path and os.path.exists(str(analysis.video)):
                video_path = str(analysis.video)

        if not video_path:
            analysis.status = "failed"
            analysis.error_message = "Uploaded video file not found on filesystem."
            analysis.save(update_fields=["status", "error_message"])
            return

        print(f"[AnalysisWorker] Commencing deepfake analysis for Video #{analysis_id}: {analysis.video.name}")

        # Run AI detection pipeline (OpenCV frame/face extraction + ViT inference)
        verdict = detect_deepfake_in_video(video_path, max_frames=8)

        analysis.result = verdict["result"]
        analysis.confidence = verdict["confidence"]
        analysis.status = "completed"
        analysis.error_message = verdict.get("error_message", "")
        analysis.save(update_fields=["result", "confidence", "status", "error_message"])

        print(
            f"[AnalysisWorker] Analysis #{analysis_id} completed: "
            f"Result={analysis.result.upper()}, Confidence={analysis.confidence}"
        )

    except Exception as exc:
        print(f"[AnalysisWorker] Error processing video #{analysis_id}: {exc}")
        try:
            analysis = VideoAnalysis.objects.get(pk=analysis_id)
            analysis.status = "failed"
            analysis.error_message = f"Inference pipeline failed: {str(exc)}"
            analysis.save(update_fields=["status", "error_message"])
        except Exception:
            pass
    finally:
        connection.close()


class VideoUploadAPIView(APIView):
    """Handle video upload and validate file parameters."""
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = VideoAnalysisSerializer(data=request.data)

        if serializer.is_valid():
            analysis = serializer.save()

            return Response(
                {
                    "message": "Video uploaded successfully.",
                    "analysis": VideoAnalysisSerializer(analysis).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class VideoResultAPIView(APIView):
    """Retrieve the analysis status and detection result for a given record."""

    def get(self, request, pk):
        try:
            analysis = VideoAnalysis.objects.get(pk=pk)
        except VideoAnalysis.DoesNotExist:
            return Response(
                {"error": "Analysis not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = VideoAnalysisSerializer(analysis)
        return Response(serializer.data)


class VideoHistoryAPIView(APIView):
    """Fetch chronological history of all analyzed media."""

    def get(self, request):
        analyses = VideoAnalysis.objects.all().order_by("-created_at")
        serializer = VideoAnalysisSerializer(analyses, many=True)

        return Response({
            "count": analyses.count(),
            "results": serializer.data,
        })


class StartAnalysisAPIView(APIView):
    """
    Trigger the deepfake AI pipeline on an uploaded video.
    Spawns a daemon background thread so the HTTP request returns immediately.
    """

    def post(self, request, pk):
        try:
            analysis = VideoAnalysis.objects.get(pk=pk)
        except VideoAnalysis.DoesNotExist:
            return Response(
                {"error": "Video analysis not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if analysis.status == "processing":
            return Response(
                {"message": "Analysis is already in progress."},
                status=status.HTTP_409_CONFLICT,
            )

        # Update status to processing
        analysis.status = "processing"
        analysis.error_message = ""
        analysis.save(update_fields=["status", "error_message"])

        # Launch analysis asynchronously in background thread
        thread = threading.Thread(
            target=_run_video_analysis_task,
            args=(analysis.id,),
            daemon=True,
        )
        thread.start()

        return Response(
            {
                "message": "Analysis started.",
                "analysis": VideoAnalysisSerializer(analysis).data,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
def save_detection_result(request, pk):
    """Manual/external endpoint to save or override a detection result."""
    try:
        analysis = VideoAnalysis.objects.get(pk=pk)
    except VideoAnalysis.DoesNotExist:
        return Response(
            {"error": "Analysis not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    result = request.data.get("result")
    confidence = request.data.get("confidence")

    if result not in ["real", "deepfake", "inconclusive"]:
        return Response(
            {"error": "Invalid detection result."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if confidence is None:
        return Response(
            {"error": "Confidence is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        return Response(
            {"error": "Confidence must be a number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not 0 <= confidence <= 1:
        return Response(
            {"error": "Confidence must be between 0 and 1."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    analysis.result = result
    analysis.confidence = confidence
    analysis.status = "completed"
    analysis.error_message = ""
    analysis.save()

    return Response({
        "message": "Detection result saved successfully.",
        "id": analysis.id,
        "status": analysis.status,
        "result": analysis.result,
        "confidence": analysis.confidence,
    })
