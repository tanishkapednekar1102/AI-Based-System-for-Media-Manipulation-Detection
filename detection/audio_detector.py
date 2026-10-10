import os
import time
import logging
import numpy as np
import tensorflow as tf

import config
from preprocessing.audio_preprocessing import extract_audio_features, generate_audio_visualizations
from models.train_audio import build_audio_model, train_audio_model
from database.detections import save_detection

logger = logging.getLogger("detection.audio")

_audio_model_instance = None

def get_or_load_audio_model():
    """Loads trained audio 2D Spectrogram model or builds baseline architecture."""
    global _audio_model_instance
    if _audio_model_instance is not None:
        return _audio_model_instance

    if os.path.exists(config.AUDIO_MODEL_PATH):
        try:
            logger.info(f"Loading Audio Model from: {config.AUDIO_MODEL_PATH}")
            _audio_model_instance = tf.keras.models.load_model(config.AUDIO_MODEL_PATH)
            return _audio_model_instance
        except Exception as e:
            logger.error(f"Error loading audio model: {e}")

    logger.info("Audio model file not found. Initializing audio model checkpoint...")
    _audio_model_instance = train_audio_model(epochs=1)
    return _audio_model_instance

def detect_audio(audio_path: str, user_id: int = 1) -> dict:
    """
    Full Audio Manipulation / Deepfake Detection Pipeline:
    1. Validate extension
    2. Extract audio features (Mel Spectrogram, MFCCs, Spectral Centroid, ZCR) via Librosa
    3. Generate Waveform & Spectrogram visualizer figure
    4. Run Keras 2D Spectrogram CNN Inference
    5. Determine Result (AUTHENTIC / SYNTHETIC / UNCERTAIN) & Confidence
    6. Save detection record in MySQL
    """
    start_time = time.time()
    
    ext = os.path.splitext(audio_path)[1].lower()
    if ext not in config.ALLOWED_AUDIO_EXTS:
        raise ValueError(f"Unsupported audio format '{ext}'. Allowed formats: {', '.join(config.ALLOWED_AUDIO_EXTS)}")

    file_name = os.path.basename(audio_path)

    # Step 1: Preprocess Audio & Extract Features
    mel_input, y, sr, mel_spec_db, metadata = extract_audio_features(audio_path)

    # Step 2: Render Waveform & Spectrogram preview image
    viz_image_path = generate_audio_visualizations(y, sr, mel_spec_db, output_filename_prefix=file_name)

    # Step 3: Run AI Model Inference
    model = get_or_load_audio_model()
    raw_pred = float(model.predict(mel_input, verbose=0)[0][0])

    # Step 4: Determine Result & Confidence
    if raw_pred >= config.UNCERTAIN_UPPER:
        result = "SYNTHETIC"
        confidence = raw_pred
    elif raw_pred <= config.UNCERTAIN_LOWER:
        result = "AUTHENTIC"
        confidence = 1.0 - raw_pred
    else:
        result = "UNCERTAIN"
        confidence = 0.50 + abs(raw_pred - 0.50)

    confidence_pct = round(confidence * 100.0, 2)
    manip_prob_pct = round(raw_pred * 100.0, 2)
    processing_time = round(time.time() - start_time, 2)
    model_name = "2D Mel-Spectrogram CNN + MFCC Analyzer"

    # Step 5: Save result to MySQL Database
    detection_id = save_detection(
        user_id=user_id,
        file_name=file_name,
        media_type="AUDIO",
        result=result,
        confidence=confidence_pct,
        manipulation_probability=manip_prob_pct,
        model_name=model_name,
        processing_time=processing_time
    )

    return {
        "detection_id": detection_id,
        "file_name": file_name,
        "media_type": "AUDIO",
        "duration": f"{metadata['duration']} sec",
        "sample_rate": f"{metadata['sample_rate']} Hz",
        "file_size": f"{metadata['file_size_mb']} MB",
        "spectral_centroid": metadata["mean_spectral_centroid"],
        "zero_crossing_rate": metadata["mean_zero_crossing_rate"],
        "result": result,
        "confidence": f"{confidence_pct}%",
        "confidence_val": confidence_pct,
        "manipulation_probability": f"{manip_prob_pct}%",
        "manipulation_prob_val": manip_prob_pct,
        "model_name": model_name,
        "processing_time": f"{processing_time} seconds",
        "processing_time_val": processing_time,
        "audio_path": audio_path,
        "visualization_path": viz_image_path
    }
