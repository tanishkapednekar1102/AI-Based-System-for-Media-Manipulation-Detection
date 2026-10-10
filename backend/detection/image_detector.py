import os
import time
import logging
import numpy as np

try:
    import tensorflow as tf
    HAS_TF = True
except Exception as err:
    tf = None
    HAS_TF = False

from backend import config
from backend.preprocessing.image_preprocessing import preprocess_image, convert_to_ela_image
from backend.models.train_image import build_image_model, train_image_model
from backend.database.detections import save_detection

logger = logging.getLogger("detection.image")

_image_model_instance = None

def get_or_load_image_model():
    """Loads trained TensorFlow image model or initializes architecture gracefully."""
    global _image_model_instance
    if not HAS_TF:
        logger.warning("TensorFlow not active. Using hybrid feature analysis pipeline.")
        return None

    if _image_model_instance is not None:
        return _image_model_instance

    if os.path.exists(config.IMAGE_MODEL_PATH):
        try:
            logger.info(f"Loading Image Model from: {config.IMAGE_MODEL_PATH}")
            _image_model_instance = tf.keras.models.load_model(config.IMAGE_MODEL_PATH)
            return _image_model_instance
        except Exception as e:
            logger.error(f"Error loading image model file: {e}")

    try:
        logger.info("Building lightweight baseline image model...")
        _image_model_instance = train_image_model(epochs=1)
        return _image_model_instance
    except Exception as e:
        logger.warning(f"Could not build TF model: {e}")
        return None

def detect_image(image_path: str, user_id: int = 1) -> dict:
    """
    Full Image Manipulation Detection Pipeline:
    1. Validate extension & size
    2. Preprocess image & compute ELA features
    3. Run Keras CNN Inference / ELA Forensic Analyzer
    4. Calculate Confidence & Manipulation Probability
    5. Evaluate UNCERTAIN threshold
    6. Store detection record in MySQL
    """
    start_time = time.time()
    
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in config.ALLOWED_IMAGE_EXTS:
        raise ValueError(f"Unsupported image format '{ext}'. Allowed formats: {', '.join(config.ALLOWED_IMAGE_EXTS)}")

    # Step 1: Preprocess Image
    input_batch, metadata = preprocess_image(image_path)
    file_name = os.path.basename(image_path)

    # Step 2: Extract ELA (Error Level Analysis) variance score
    try:
        ela_array = convert_to_ela_image(image_path)
        ela_variance = float(np.var(ela_array)) / 1000.0  # Normalized variance score
    except Exception as e:
        logger.warning(f"ELA calculation skipped: {e}")
        ela_variance = 0.05

    # Step 3: AI Model Inference
    model = get_or_load_image_model()
    if model is not None:
        try:
            raw_pred = float(model.predict(input_batch, verbose=0)[0][0])
        except Exception as e:
            logger.warning(f"Model prediction exception: {e}")
            raw_pred = min(ela_variance, 0.95)
    else:
        # Fallback to ELA compression analysis score when TF model binary is absent
        raw_pred = min(ela_variance, 0.95)
    
    # Combine Deep Learning raw prediction with ELA compression artifact score
    combined_prob = float(np.clip(0.7 * raw_pred + 0.3 * min(ela_variance, 1.0), 0.0, 1.0))

    # Step 4: Determine Result & Confidence
    if combined_prob >= config.UNCERTAIN_UPPER:
        result = "MANIPULATED"
        confidence = combined_prob
    elif combined_prob <= config.UNCERTAIN_LOWER:
        result = "AUTHENTIC"
        confidence = 1.0 - combined_prob
    else:
        result = "UNCERTAIN"
        confidence = 0.50 + abs(combined_prob - 0.50)

    confidence_pct = round(confidence * 100.0, 2)
    manip_prob_pct = round(combined_prob * 100.0, 2)
    processing_time = round(time.time() - start_time, 2)
    model_name = "Xception / CNN + ELA Hybrid" if HAS_TF else "ELA Compression Variance Analyzer"

    # Step 5: Save result to MySQL Database
    detection_id = save_detection(
        user_id=user_id,
        file_name=file_name,
        media_type="IMAGE",
        result=result,
        confidence=confidence_pct,
        manipulation_probability=manip_prob_pct,
        model_name=model_name,
        processing_time=processing_time
    )

    return {
        "detection_id": detection_id,
        "file_name": file_name,
        "media_type": "IMAGE",
        "file_size": f"{metadata['file_size_mb']} MB",
        "dimensions": metadata["dimensions"],
        "result": result,
        "confidence": f"{confidence_pct}%",
        "confidence_val": confidence_pct,
        "manipulation_probability": f"{manip_prob_pct}%",
        "manipulation_prob_val": manip_prob_pct,
        "model_name": model_name,
        "processing_time": f"{processing_time} seconds",
        "processing_time_val": processing_time,
        "image_path": image_path,
        "ela_variance": round(ela_variance, 3)
    }
