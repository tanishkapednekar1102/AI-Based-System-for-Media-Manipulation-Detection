import os
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance

def convert_to_ela_image(image_path: str, quality: int = 90) -> np.ndarray:
    """
    Computes Error Level Analysis (ELA) for image forgery detection.
    ELA highlights differences in JPEG compression rates across an image.
    """
    try:
        temp_filename = image_path + ".temp.jpg"
        original = Image.open(image_path).convert('RGB')
        
        # Save compressed version
        original.save(temp_filename, 'JPEG', quality=quality)
        compressed = Image.open(temp_filename).convert('RGB')
        
        # Compute absolute difference between original and compressed
        ela_img = ImageChops.difference(original, compressed)
        
        # Extrapolate brightness scale
        extrema = ela_img.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff
        
        ela_img = ImageEnhance.Brightness(ela_img).enhance(scale)
        
        # Clean up temporary compressed file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        return np.array(ela_img)
    except Exception as e:
        if os.path.exists(image_path + ".temp.jpg"):
            os.remove(image_path + ".temp.jpg")
        raise RuntimeError(f"Error computing ELA features: {e}")

def preprocess_image(image_path: str, target_size=(224, 224)):
    """
    Validates, resizes, and normalizes an image for deep learning model input.
    Returns normalized float array (1, 224, 224, 3) and image metadata dict.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    file_size_bytes = os.path.getsize(image_path)
    file_size_mb = file_size_bytes / (1024 * 1024)

    with Image.open(image_path) as img:
        width, height = img.size
        img_format = img.format
        img_rgb = img.convert("RGB")

    # Resize for CNN input
    resized = img_rgb.resize(target_size, Image.Resampling.BILINEAR)
    img_array = np.array(resized, dtype=np.float32) / 255.0
    input_batch = np.expand_dims(img_array, axis=0)

    metadata = {
        "width": width,
        "height": height,
        "dimensions": f"{width} x {height}",
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "format": img_format or "UNKNOWN"
    }

    return input_batch, metadata
