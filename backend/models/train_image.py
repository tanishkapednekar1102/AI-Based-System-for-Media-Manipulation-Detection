import os
import sys
import numpy as np

from backend import config

try:
    import tensorflow as tf
    from tensorflow.keras import layers, models, optimizers
    HAS_TF = True
except Exception as err:
    tf = None
    HAS_TF = False

def build_image_model(input_shape=(224, 224, 3)):
    """
    Builds a Convolutional Neural Network (CNN) for Image Media Manipulation Detection.
    Architecture: Multi-stage Conv2D + BatchNorm + MaxPooling + Dense Dropout Classifier.
    """
    if not HAS_TF:
        raise RuntimeError("TensorFlow is not available in the current environment.")

    model = models.Sequential([
        layers.Input(shape=input_shape),
        
        # Block 1
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        # Block 2
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        # Block 3
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        # Dense Classifier
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(1, activation='sigmoid')  # Output: Probability of Manipulation (1=Manipulated, 0=Authentic)
    ])
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-4),
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.Precision(name='precision'), tf.keras.metrics.Recall(name='recall')]
    )
    return model

def train_image_model(epochs=5, batch_size=8):
    """
    Training pipeline for Image Manipulation Detector.
    Loads dataset from dataset/image/ (real vs manipulated).
    """
    if not HAS_TF:
        raise RuntimeError("TensorFlow is required to train the image model.")

    print("=" * 60)
    print("Starting Image Manipulation Detection Model Training Pipeline")
    print("=" * 60)

    dataset_path = config.DATASET_DIR / "image"
    real_dir = dataset_path / "real"
    manipulated_dir = dataset_path / "manipulated"

    real_files = [f for f in os.listdir(real_dir) if not f.startswith('.')] if real_dir.exists() else []
    manip_files = [f for f in os.listdir(manipulated_dir) if not f.startswith('.')] if manipulated_dir.exists() else []

    print(f"Found {len(real_files)} authentic image samples in {real_dir}")
    print(f"Found {len(manip_files)} manipulated image samples in {manipulated_dir}")

    model = build_image_model()

    if len(real_files) > 0 and len(manip_files) > 0:
        print("\nLoading dataset using tf.keras.utils.image_dataset_from_directory...")
        train_ds = tf.keras.utils.image_dataset_from_directory(
            dataset_path,
            validation_split=0.2,
            subset="training",
            seed=123,
            image_size=(224, 224),
            batch_size=batch_size
        )
        val_ds = tf.keras.utils.image_dataset_from_directory(
            dataset_path,
            validation_split=0.2,
            subset="validation",
            seed=123,
            image_size=(224, 224),
            batch_size=batch_size
        )

        # Normalize images
        normalization_layer = layers.Rescaling(1./255)
        train_ds = train_ds.map(lambda x, y: (normalization_layer(x), y))
        val_ds = val_ds.map(lambda x, y: (normalization_layer(x), y))

        print(f"\nTraining model for {epochs} epochs...")
        history = model.fit(train_ds, validation_data=val_ds, epochs=epochs)
        print("Training completed.")
    else:
        print("\n[NOTICE] No images found in dataset/image/ subdirectories.")
        print("Initializing base architecture and saving initial model weights to allow inference...")

    os.makedirs(os.path.dirname(config.IMAGE_MODEL_PATH), exist_ok=True)
    model.save(config.IMAGE_MODEL_PATH)
    print(f"Saved Image Detection Model to: {config.IMAGE_MODEL_PATH}")
    return model

if __name__ == "__main__":
    train_image_model()
