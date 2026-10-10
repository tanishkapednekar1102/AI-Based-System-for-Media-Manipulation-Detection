import os
import librosa
import soundfile as sf
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    from backend import config
except ImportError:
    import config

def extract_audio_features(audio_path: str, duration_sec: float = 5.0, sample_rate: int = 22050):
    """
    Loads audio using Librosa and extracts acoustic features:
    - Mel Spectrogram (2D matrix)
    - MFCC (20 coefficients)
    - Spectral Centroid
    - Zero Crossing Rate
    Returns normalized feature matrix for CNN model input and acoustic metadata dict.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Load audio signal
    y, sr = librosa.load(audio_path, sr=sample_rate, duration=duration_sec)
    actual_duration = librosa.get_duration(y=y, sr=sr)
    file_size_bytes = os.path.getsize(audio_path)

    # Pad or trim signal to fixed duration (e.g., 5 seconds)
    target_length = int(sample_rate * duration_sec)
    if len(y) < target_length:
        y = np.pad(y, (0, target_length - len(y)), mode='constant')
    else:
        y = y[:target_length]

    # Feature 1: Mel Spectrogram
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

    # Feature 2: MFCCs
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)

    # Feature 3: Spectral Centroid
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    mean_centroid = float(np.mean(spectral_centroid))

    # Feature 4: Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y)
    mean_zcr = float(np.mean(zcr))

    # Prepare 2D Spectrogram input array for model (128, 128, 1)
    # Resize / pad mel_spec_db along time axis to 128
    if mel_spec_db.shape[1] < 128:
        mel_norm = np.pad(mel_spec_db, ((0, 0), (0, 128 - mel_spec_db.shape[1])), mode='edge')
    else:
        mel_norm = mel_spec_db[:, :128]

    # Normalize to [0, 1]
    mel_norm = (mel_norm - mel_norm.min()) / (mel_norm.max() - mel_norm.min() + 1e-8)
    mel_input = np.expand_dims(mel_norm, axis=(0, -1)) # Shape (1, 128, 128, 1)

    metadata = {
        "duration": round(actual_duration, 2),
        "sample_rate": sr,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
        "mean_spectral_centroid": round(mean_centroid, 2),
        "mean_zero_crossing_rate": round(mean_zcr, 4)
    }

    return mel_input, y, sr, mel_spec_db, metadata

def generate_audio_visualizations(y: np.ndarray, sr: int, mel_spec_db: np.ndarray, output_filename_prefix: str) -> str:
    """
    Renders combined Waveform and Mel-Spectrogram figure using Matplotlib.
    Saves image in RESULTS_DIR and returns image path for NiceGUI UI display.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4), facecolor="#1C2541")
    
    # Plot 1: Waveform
    ax1.set_facecolor("#0B132B")
    time_axis = np.linspace(0, len(y) / sr, num=len(y))
    ax1.plot(time_axis, y, color="#00B4D8", alpha=0.8, linewidth=1.0)
    ax1.set_title("Audio Signal Waveform", color="#FEFCFB", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Amplitude", color="#A0AEC0", fontsize=8)
    ax1.tick_params(colors="#A0AEC0", labelsize=8)
    ax1.grid(True, linestyle="--", alpha=0.2, color="#1282A2")

    # Plot 2: Mel Spectrogram
    ax2.set_facecolor("#0B132B")
    img = librosa.display.specshow(mel_spec_db, x_axis='time', y_axis='mel', sr=sr, ax=ax2, cmap='magma')
    ax2.set_title("Mel Spectrogram Frequency Matrix", color="#FEFCFB", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Hz", color="#A0AEC0", fontsize=8)
    ax2.set_xlabel("Time (s)", color="#A0AEC0", fontsize=8)
    ax2.tick_params(colors="#A0AEC0", labelsize=8)

    plt.tight_layout()

    viz_path = os.path.join(config.RESULTS_DIR, f"{output_filename_prefix}_audio_viz.png")
    plt.savefig(viz_path, dpi=120, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)

    return viz_path
