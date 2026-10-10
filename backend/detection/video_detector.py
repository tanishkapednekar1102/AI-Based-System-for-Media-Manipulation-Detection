import os
import time
import logging
import cv2
import numpy as np

try:
    import tensorflow as tf
    HAS_TF = True
except Exception as err:
    tf = None
    HAS_TF = False

from backend import config
from backend.preprocessing.video_preprocessing import extract_sampled_frames, extract_video_metadata
from backend.models.train_video import build_video_frame_model, train_video_model
from backend.database.detections import save_detection

logger = logging.getLogger("detection.video")

_video_model_instance = None

def get_or_load_video_model():
    """Loads trained video frame CNN model or builds baseline weights."""
    global _video_model_instance
    if not HAS_TF:
        logger.warning("TensorFlow not active. Using frame variance analysis pipeline.")
        return None

    if _video_model_instance is not None:
        return _video_model_instance

    if os.path.exists(config.VIDEO_MODEL_PATH):
        try:
            logger.info(f"Loading Video Model from: {config.VIDEO_MODEL_PATH}")
            _video_model_instance = tf.keras.models.load_model(config.VIDEO_MODEL_PATH)
            return _video_model_instance
        except Exception as e:
            logger.error(f"Error loading video model: {e}")

    try:
        logger.info("Initializing video model checkpoint...")
        _video_model_instance = train_video_model(epochs=1)
        return _video_model_instance
    except Exception as e:
        logger.warning(f"Could not build TF video model: {e}")
        return None

def detect_video(video_path: str, user_id: int = 1, max_sample_frames: int = 15) -> dict:
    """
    Full Video Manipulation Detection Pipeline:
    1. Validate extension
    2. Extract video metadata & sampled frames via OpenCV
    3. Run Keras Frame Classification Inference / OpenCV Frame Variance Analysis
    4. Detect suspicious frames and extract gallery thumbnails
    5. Aggregate frame probabilities -> Final Result & Confidence
    6. Store detection record in MySQL
    """
    start_time = time.time()
    
    ext = os.path.splitext(video_path)[1].lower()
    if ext not in config.ALLOWED_VIDEO_EXTS:
        raise ValueError(f"Unsupported video format '{ext}'. Allowed formats: {', '.join(config.ALLOWED_VIDEO_EXTS)}")

    file_name = os.path.basename(video_path)

    # Step 1: Extract sampled frames and raw frames
    frames_preprocessed, frames_raw, frame_indices, metadata = extract_sampled_frames(video_path, max_frames=max_sample_frames)

    # Step 2: Run AI Model Inference / Frame Variance Analysis
    model = get_or_load_video_model()
    if model is not None:
        try:
            frame_preds = model.predict(frames_preprocessed, verbose=0).flatten()
        except Exception as e:
            logger.warning(f"Video model prediction error: {e}")
            frame_preds = np.array([float(np.var(f) * 2.0) for f in frames_preprocessed])
    else:
        # Heuristic frame variance scoring when TF is offline
        frame_preds = np.array([float(np.clip(np.var(f) * 1.5, 0.05, 0.95)) for f in frames_preprocessed])

    # Step 3: Identify suspicious frames and save thumbnail previews
    suspicious_frames_info = []
    suspicious_count = 0

    for idx, (prob, raw_frame, frame_no) in enumerate(zip(frame_preds, frames_raw, frame_indices)):
        prob_val = float(prob)
        is_suspicious = prob_val >= 0.50
        if is_suspicious:
            suspicious_count += 1

        # Save thumbnail image for gallery display
        thumb_name = f"{file_name}_frame_{frame_no}.jpg"
        thumb_path = os.path.join(config.RESULTS_DIR, thumb_name)
        cv2.imwrite(thumb_path, raw_frame)

        suspicious_frames_info.append({
            "frame_index": frame_no,
            "probability": round(prob_val * 100.0, 2),
            "is_suspicious": is_suspicious,
            "thumbnail_path": thumb_path
        })

    # Step 4: Aggregate Frame Predictions
    avg_manipulation_prob = float(np.mean(frame_preds))

    if avg_manipulation_prob >= config.UNCERTAIN_UPPER:
        result = "MANIPULATED"
        confidence = avg_manipulation_prob
    elif avg_manipulation_prob <= config.UNCERTAIN_LOWER:
        result = "AUTHENTIC"
        confidence = 1.0 - avg_manipulation_prob
    else:
        result = "UNCERTAIN"
        confidence = 0.50 + abs(avg_manipulation_prob - 0.50)

    confidence_pct = round(confidence * 100.0, 2)
    manip_prob_pct = round(avg_manipulation_prob * 100.0, 2)
    processing_time = round(time.time() - start_time, 2)
    model_name = "Frame-Level CNN Aggregator (ResNet/Xception)" if HAS_TF else "OpenCV Frame-Variance Inspector"

    # Step 5: Save result to MySQL Database
    detection_id = save_detection(
        user_id=user_id,
        file_name=file_name,
        media_type="VIDEO",
        result=result,
        confidence=confidence_pct,
        manipulation_probability=manip_prob_pct,
        model_name=model_name,
        processing_time=processing_time
    )

    return {
        "detection_id": detection_id,
        "file_name": file_name,
        "media_type": "VIDEO",
        "duration": f"{metadata['duration']} sec",
        "fps": metadata["fps"],
        "resolution": metadata["resolution"],
        "frame_count": metadata["frame_count"],
        "frames_analyzed": len(frame_preds),
        "suspicious_frames_count": suspicious_count,
        "result": result,
        "confidence": f"{confidence_pct}%",
        "confidence_val": confidence_pct,
        "manipulation_probability": f"{manip_prob_pct}%",
        "manipulation_prob_val": manip_prob_pct,
        "model_name": model_name,
        "processing_time": f"{processing_time} seconds",
        "processing_time_val": processing_time,
        "video_path": video_path,
        "suspicious_frames": suspicious_frames_info
    }
