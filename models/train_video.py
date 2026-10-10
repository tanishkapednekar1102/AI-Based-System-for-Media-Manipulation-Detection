import os
import sys
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import config

def build_video_frame_model(input_shape=(224, 224, 3)):
    """
    Builds a Frame-Level Feature Classifier CNN for Video Media Manipulation Detection.
    Evaluates individual sampled video frames for facial manipulation artifacts.
    """
    model = models.Sequential([
        layers.Input(shape=input_shape),
        
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.4),
        layers.Dense(1, activation='sigmoid')  # Output: Probability of frame manipulation
    ])
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-4),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model

def train_video_model(epochs=5, batch_size=8):
    """Training pipeline for Video Manipulation Detector."""
    print("=" * 60)
    print("Starting Video Manipulation Detection Model Training Pipeline")
    print("=" * 60)

    dataset_path = config.DATASET_DIR / "video"
    real_dir = dataset_path / "real"
    manipulated_dir = dataset_path / "manipulated"

    real_files = [f for f in os.listdir(real_dir) if not f.startswith('.')] if real_dir.exists() else []
    manip_files = [f for f in os.listdir(manipulated_dir) if not f.startswith('.')] if manipulated_dir.exists() else []

    print(f"Found {len(real_files)} authentic video samples in {real_dir}")
    print(f"Found {len(manip_files)} manipulated video samples in {manipulated_dir}")

    model = build_video_frame_model()

    os.makedirs(os.path.dirname(config.VIDEO_MODEL_PATH), exist_ok=True)
    model.save(config.VIDEO_MODEL_PATH)
    print(f"Saved Video Frame Detection Model to: {config.VIDEO_MODEL_PATH}")
    return model

if __name__ == "__main__":
    train_video_model()
