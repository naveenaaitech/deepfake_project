import os
import cv2
import numpy as np
from pathlib import Path

try:
    from django.conf import settings
    BASE_DIR = str(settings.BASE_DIR)
except Exception:
    BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)

# Path to the pretrained YuNet ONNX face detection model
YUNET_MODEL_PATH = os.path.join(
    BASE_DIR, "models", "face_detector", "face_detection_yunet_2023mar.onnx"
)

_CACHED_FACE_DETECTOR = None


def get_face_detector():
    """
    Get or initialize a cached singleton instance of the OpenCV YuNet face detector.
    """
    global _CACHED_FACE_DETECTOR
    if _CACHED_FACE_DETECTOR is not None:
        return _CACHED_FACE_DETECTOR

    if not os.path.exists(YUNET_MODEL_PATH):
        return None

    try:
        # Initialize YuNet with default 320x320 size, threshold 0.6, NMS 0.3
        detector = cv2.FaceDetectorYN_create(
            YUNET_MODEL_PATH,
            "",
            (320, 320),
            score_threshold=0.6,
            nms_threshold=0.3,
            top_k=5000,
        )
        _CACHED_FACE_DETECTOR = detector
        return detector
    except Exception as exc:
        print(f"[VideoProcessor] Failed to load YuNet face detector: {exc}")
        return None


def validate_video_file(video_path):
    """
    Check if the video file exists, is non-empty, and can be read by OpenCV.
    Raises ValueError with descriptive reason on failure.
    """
    if not os.path.exists(video_path):
        raise ValueError(f"Video file does not exist: {video_path}")

    if os.path.getsize(video_path) == 0:
        raise ValueError("Video file is empty (0 bytes).")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Unable to open the uploaded video file. Corrupted or unsupported format.")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)

        if total_frames <= 0 or width <= 0 or height <= 0:
            raise ValueError("Video stream contains no readable frames or invalid dimensions.")

        return {
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "fps": fps,
            "duration_sec": total_frames / fps if fps > 0 else 0,
        }
    finally:
        cap.release()


def extract_frames(video_path, max_frames=20):
    """
    Extract up to max_frames evenly spaced frames from a video.
    Returns a list of BGR numpy array frames.
    """
    validate_video_file(video_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Unable to open the uploaded video.")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise ValueError("Video contains no readable frames.")

        frame_count = min(total_frames, max_frames)
        frames = []

        for i in range(frame_count):
            frame_index = int(i * total_frames / frame_count)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            success, frame = cap.read()

            if success and frame is not None and frame.size > 0:
                frames.append(frame)

        if not frames:
            raise ValueError("Could not extract any valid video frames.")

        return frames
    finally:
        cap.release()


def crop_face_with_margin(frame, bbox, margin_ratio=0.25):
    """
    Crop face bounding box with equal square padding to preserve natural facial
    aspect ratios and prevent horizontal/vertical squashing during model resize.
    bbox format: [x, y, w, h]
    """
    h_img, w_img = frame.shape[:2]
    x, y, w, h = bbox

    # Determine square dimensions centered on the face
    cx = x + w / 2.0
    cy = y + h / 2.0
    sq_size = max(w, h) * (1.0 + margin_ratio)

    x1 = max(0, int(cx - sq_size / 2.0))
    y1 = max(0, int(cy - sq_size / 2.0))
    x2 = min(w_img, int(cx + sq_size / 2.0))
    y2 = min(h_img, int(cy + sq_size / 2.0))

    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    # Replicate borders if face is near frame boundary to maintain exact square
    ch, cw = crop.shape[:2]
    if ch != cw:
        max_d = max(ch, cw)
        pad_y = (max_d - ch) // 2
        pad_x = (max_d - cw) // 2
        crop = cv2.copyMakeBorder(
            crop,
            pad_y,
            max_d - ch - pad_y,
            pad_x,
            max_d - cw - pad_x,
            cv2.BORDER_REPLICATE,
        )

    return crop


def extract_faces_from_frames(frames, min_face_size=60, margin_ratio=0.25):
    """
    Detect and crop human faces from a list of video frames using OpenCV YuNet.
    Uses downscaled detection (max 640px) for ultra-fast (<10ms) performance
    even on 4K UHD videos, then crops the full-resolution face with anti-aliased square padding.
    """
    detector = get_face_detector()
    face_crops = []
    metadata = []

    for frame_idx, frame in enumerate(frames):
        h, w = frame.shape[:2]

        if detector is not None:
            try:
                # Downscale large frames to max 640px for ultra-fast face detection (<10ms)
                if w > 640:
                    scale = 640.0 / float(w)
                    det_w = 640
                    det_h = int(h * scale)
                    det_frame = cv2.resize(frame, (det_w, det_h), interpolation=cv2.INTER_LINEAR)
                else:
                    scale = 1.0
                    det_w, det_h = w, h
                    det_frame = frame

                detector.setInputSize((det_w, det_h))
                _, faces = detector.detect(det_frame)

                if faces is not None and len(faces) > 0:
                    # Rescale bounding boxes back to original frame coordinates
                    scaled_faces = []
                    for f in faces:
                        f_orig = f.copy()
                        if scale != 1.0:
                            f_orig[0:4] = f_orig[0:4] / scale
                        scaled_faces.append(f_orig)

                    # Filter faces by minimum resolution to ignore distant background crowd
                    valid_faces = [
                        f for f in scaled_faces
                        if f[2] >= min_face_size and f[3] >= min_face_size
                    ]

                    if not valid_faces:
                        continue

                    # Select the primary foreground face (largest area)
                    best_face = max(valid_faces, key=lambda f: f[2] * f[3])
                    bbox = [int(v) for v in best_face[0:4]]
                    confidence = float(best_face[-1]) if len(best_face) > 4 else 1.0

                    cropped = crop_face_with_margin(frame, bbox, margin_ratio=margin_ratio)
                    if cropped is not None and cropped.size > 0:
                        face_crops.append(cropped)
                        metadata.append({
                            "frame_index": frame_idx,
                            "bbox": bbox,
                            "confidence": confidence,
                        })
            except Exception as e:
                print(f"[VideoProcessor] Face detection error on frame {frame_idx}: {e}")

    return face_crops, metadata


def process_video_for_analysis(video_path, max_frames=8):
    """
    Comprehensive video analysis preprocessor:
    1. Validates the video file.
    2. Extracts representative frames.
    3. Detects and extracts normalized face crops.
    """
    video_info = validate_video_file(video_path)
    frames = extract_frames(video_path, max_frames=max_frames)
    face_crops, face_meta = extract_faces_from_frames(frames)

    return {
        "video_info": video_info,
        "frames": frames,
        "face_crops": face_crops,
        "face_metadata": face_meta,
        "total_frames_extracted": len(frames),
        "total_faces_detected": len(face_crops),
    }