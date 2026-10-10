import os
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf
import config

def evaluate_single_model(model_path: str, model_name: str, test_data=None, test_labels=None):
    """
    Evaluates a Keras model on a given test dataset using Scikit-Learn evaluation metrics.
    """
    print(f"\n--- Evaluating Model: {model_name} ---")
    if not os.path.exists(model_path):
        print(f"[STATUS] Model binary not found at: {model_path}")
        print("Run the corresponding training script to generate the model checkpoint.")
        return None

    try:
        model = tf.keras.models.load_model(model_path)
    except Exception as e:
        print(f"Error loading model from {model_path}: {e}")
        return None

    if test_data is None or test_labels is None:
        print(f"No test dataset passed for {model_name}. Displaying model architecture summary:")
        model.summary()
        return {
            "Model": model_name,
            "Status": "Checkpoint Loaded (No Test Data Provided)",
            "Accuracy": "N/A",
            "Precision": "N/A",
            "Recall": "N/A",
            "F1 Score": "N/A",
            "ROC-AUC": "N/A"
        }

    # Predict probabilities
    probs = model.predict(test_data)
    preds = (probs > 0.5).astype(int)

    acc = accuracy_score(test_labels, preds)
    prec = precision_score(test_labels, preds, zero_division=0)
    rec = recall_score(test_labels, preds, zero_division=0)
    f1 = f1_score(test_labels, preds, zero_division=0)
    
    try:
        auc = roc_auc_score(test_labels, probs)
    except Exception:
        auc = 0.5

    cm = confusion_matrix(test_labels, preds)

    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {auc:.4f}")
    print("Confusion Matrix:")
    print(cm)

    return {
        "Model": model_name,
        "Accuracy": round(float(acc), 4),
        "Precision": round(float(prec), 4),
        "Recall": round(float(rec), 4),
        "F1 Score": round(float(f1), 4),
        "ROC-AUC": round(float(auc), 4),
        "Confusion Matrix": str(cm.tolist())
    }

def run_evaluation_suite():
    """Runs evaluation across Image, Video, and Audio models."""
    print("==========================================================")
    print("AI Media Manipulation Detection - Model Evaluation Suite")
    print("==========================================================")

    results = []
    
    res_img = evaluate_single_model(config.IMAGE_MODEL_PATH, "CNN Image Detector")
    if res_img: results.append(res_img)

    res_vid = evaluate_single_model(config.VIDEO_MODEL_PATH, "CNN Video Frame Detector")
    if res_vid: results.append(res_vid)

    res_aud = evaluate_single_model(config.AUDIO_MODEL_PATH, "2D Spectrogram Audio Detector")
    if res_aud: results.append(res_aud)

    if results:
        df = pd.DataFrame(results)
        print("\n=== Model Comparison Table ===")
        print(df.to_string(index=False))

if __name__ == "__main__":
    run_evaluation_suite()
