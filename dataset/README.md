# Dataset Directory Setup Instructions

To train or fine-tune models on benchmark media manipulation datasets, organize your media files into the following folder structure:

```text
dataset/
├── image/
│   ├── real/          # Authentic RGB images (.jpg, .png, .webp)
│   └── manipulated/   # Forged / Deepfake / GAN-generated images
│
├── video/
│   ├── real/          # Pristine original video files (.mp4, .avi)
│   └── manipulated/   # FaceSwap / Deepfake / Face2Face videos
│
└── audio/
    ├── real/          # Genuine human speech recordings (.wav, .mp3)
    └── synthetic/     # AI voice cloned / TTS synthetic audio
```

## Recommended Benchmark Datasets

1. **Image & Video Forgery:**
   - **FaceForensics++**: [GitHub / Official Site](https://github.com/ondyari/FaceForensics)
   - **DeepFake Detection Challenge (DFDC)**: [Kaggle DFDC](https://www.kaggle.com/c/deepfake-detection-challenge)
   - **Celeb-DF (v2)**: [GitHub Celeb-DF](https://github.com/yuezunli/celeb-deepfakeforensics)

2. **Synthetic Audio & Voice Cloning:**
   - **ASVspoof 2021 / 2019**: [ASVspoof.org](https://www.asvspoof.org/)
   - **WaveFake Dataset**: [GitHub WaveFake](https://github.com/joel-ous/WaveFake)

> **Note:** Due to copyright and licensing regulations, raw dataset binaries are not packaged directly in this repository. Place extracted sample files into their corresponding `real/` or `manipulated/` folders before running `python models/train_image.py`, `python models/train_video.py`, or `python models/train_audio.py`.
