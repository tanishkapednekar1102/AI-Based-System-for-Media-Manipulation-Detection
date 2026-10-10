import os
import cv2
import numpy as np

def extract_video_metadata(video_path: str) -> dict:
    """Reads video file properties using OpenCV."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Unable to open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # Fallback standard FPS if unavailable

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0.0
    file_size_bytes = os.path.getsize(video_path)

    cap.release()

    return {
        "fps": round(fps, 2),
        "frame_count": frame_count,
        "resolution": f"{width} x {height}",
        "width": width,
        "height": height,
        "duration": round(duration, 2),
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 2)
    }

def extract_sampled_frames(video_path: str, max_frames: int = 15, target_size=(224, 224)):
    """
    Extracts evenly spaced sample frames from video file.
    Returns list of processed numpy arrays (target_size) and list of raw OpenCV BGR frames for preview gallery.
    """
    metadata = extract_video_metadata(video_path)
    total_frames = metadata["frame_count"]

    cap = cv2.VideoCapture(video_path)
    frames_preprocessed = []
    frames_raw = []
    frame_indices = []

    if total_frames <= max_frames or max_frames <= 0:
        step = 1
    else:
        step = max(1, total_frames // max_frames)

    curr_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if curr_idx % step == 0 and len(frames_preprocessed) < max_frames:
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize
            resized = cv2.resize(rgb, target_size, interpolation=cv2.INTER_AREA)
            normalized = resized.astype(np.float32) / 255.0

            frames_preprocessed.append(normalized)
            frames_raw.append(frame.copy())
            frame_indices.append(curr_idx)

        curr_idx += 1

    cap.release()

    if not frames_preprocessed:
        raise ValueError("No valid frames could be extracted from video.")

    return np.array(frames_preprocessed), frames_raw, frame_indices, metadata
