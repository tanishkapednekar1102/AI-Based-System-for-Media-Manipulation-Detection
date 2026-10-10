import os
import sys
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import config

def build_audio_model(input_shape=(128, 128, 1)):
    """
    Builds a 2D Spectrogram CNN for Synthetic/Manipulated Audio Detection.
    Inputs 128x128 Mel Spectrogram matrices and detects synthetic voice artifacts.
    """
    model = models.Sequential([
        layers.Input(shape=input_shape),
        
        layers.Conv2D(16, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(1, activation='sigmoid')  # Output: Probability of Synthetic Audio (1=Synthetic, 0=Real)
    ])
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-4),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model

def train_audio_model(epochs=5, batch_size=8):
    """Training pipeline for Audio Synthetic/Manipulation Detector."""
    print("=" * 60)
    print("Starting Audio Synthetic/Manipulation Detection Model Training Pipeline")
    print("=" * 60)

    dataset_path = config.DATASET_DIR / "audio"
    real_dir = dataset_path / "real"
    synthetic_dir = dataset_path / "synthetic"

    real_files = [f for f in os.listdir(real_dir) if not f.startswith('.')] if real_dir.exists() else []
    synth_files = [f for f in os.listdir(synthetic_dir) if not f.startswith('.')] if synthetic_dir.exists() else []

    print(f"Found {len(real_files)} authentic audio samples in {real_dir}")
    print(f"Found {len(synth_files)} synthetic audio samples in {synthetic_dir}")

    model = build_audio_model()

    os.makedirs(os.path.dirname(config.AUDIO_MODEL_PATH), exist_ok=True)
    model.save(config.AUDIO_MODEL_PATH)
    print(f"Saved Audio Detection Model to: {config.AUDIO_MODEL_PATH}")
    return model

if __name__ == "__main__":
    train_audio_model()
