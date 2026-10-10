# AI-Based System for Media Manipulation Detection

> **Bachelor of Engineering (B.E.) Major Project**  
> **Subtitle:** Detect. Analyze. Verify Digital Media.

---

## 1. Project Overview

The **AI-Based System for Media Manipulation Detection** is a multi-modal cyber-forensic research and evaluation web platform built entirely in Python using **NiceGUI**, **MySQL**, **TensorFlow/Keras**, **OpenCV**, **Librosa**, **Pillow**, and **ReportLab**.

The platform enables forensic analysts, security researchers, and end users to upload digital images, video sequences, and audio clips to determine whether the media is authentic or manipulated/synthetic. The system outputs real AI confidence scores, manipulation probabilities, model metadata, extracted feature maps (such as Error Level Analysis variance and Mel-Spectrograms), suspicious video frame galleries, MySQL-backed analysis history, interactive analytics charts, and downloadable PDF forensic reports.

---

## 2. Problem Statement

With the rapid proliferation of Generative Adversarial Networks (GANs), Diffusion Models, Deepfake face-swapping software, and neural voice cloning algorithms (e.g., ElevenLabs, VALL-E), digital media can be forged with high realism. Existing detection systems are often fragmented—focusing exclusively on a single media modality (e.g. only images or only audio)—and lack unified user interfaces, session management, analysis logging, and formal forensic report generation.

---

## 3. Motivation & Objectives

### Motivation
- Protect public trust in digital journalism and legal evidence.
- Provide a unified, transparent platform capable of handling multi-modal media artifacts (Image, Video, and Audio).
- Eliminate fake accuracy claims by anchoring detection thresholds in empirical model predictions.

### Objectives
1. Develop a **Python-only web interface** powered by NiceGUI with a modern dark navy cyber-forensics aesthetic.
2. Integrate **MySQL database** persistence for user authentication (bcrypt hashed), detection logs, and PDF report metadata.
3. Build deep learning pipelines for **Image** (CNN + Error Level Analysis), **Video** (Frame-by-frame extraction & facial manipulation classification), and **Audio** (Librosa 2D Mel-Spectrogram CNN).
4. Provide real-time generation of formal **ReportLab PDF reports** complete with inspection metadata, metric tables, and legal disclaimers.

---

## 4. Existing System vs. Proposed System

| Feature | Existing Systems | Proposed System |
| :--- | :--- | :--- |
| **Media Support** | Single modality (e.g., Image-only) | Multi-modal (Image, Video, Audio) |
| **User Interface** | Terminal scripts or basic demos | NiceGUI Cyber-Forensics Web App |
| **Database** | File-based or SQLite | MySQL 8.0+ Relational DB with FKs & Indexes |
| **Authentication** | Plain text or None | bcrypt Salted Password Hashing & Protected Routes |
| **Reporting** | On-screen text only | Formatted ReportLab PDF Downloads |
| **Visual Features** | Raw prediction score | ELA Variance Maps, Video Gallery, Mel Spectrograms |

---

## 5. Research Gap

Existing media manipulation detection research often focuses on particular media types or manipulation techniques. This project aims to integrate image, video, and audio analysis into a single user-oriented platform with unified detection, history, analytics, and reporting.

---

## 6. Literature Review

### Paper 1: FaceForensics++: Learning to Detect Manipulated Facial Images
- **Authors:** Andreas Rössler et al. (2019)
- **Dataset:** FaceForensics++ (1.8M frames across 1,000 videos)
- **Method:** XceptionNet constrained CNN classifier fine-tuned on facial forgeries.
- **Contribution:** Standardized facial forgery detection benchmark and proved high transfer accuracy of spatial CNNs.
- **Limitation:** Performance degrades under extreme lossy social media re-compression.
- **Relevance:** Serves as the primary architectural inspiration for our Image and Video frame classifiers.

### Paper 2: The DeepFake Detection Challenge (DFDC) Dataset
- **Authors:** Brian Dolhansky et al. (2020)
- **Dataset:** DFDC (100,000+ total video clips)
- **Method:** Multi-frame spatial-temporal CNN ensemble.
- **Contribution:** Created large-scale benchmark containing diverse lighting, ethnicity, and resolution variations.
- **Limitation:** High computational latency for temporal sequence alignment.
- **Relevance:** Guided our frame sampling frequency strategy in `video_detector.py`.

### Paper 3: DeepFakeBench: A Comprehensive Benchmark of Deepfake Detection
- **Authors:** DeepFakeBench Team (2023)
- **Dataset:** Cross-dataset benchmark (FF++, Celeb-DF, WildDeepfake)
- **Method:** Evaluated spatial, frequency-domain, and blending artifact detectors.
- **Contribution:** Demonstrated that combining spatial CNNs with frequency features (e.g., ELA/FFT) improves robustness.
- **Limitation:** Single-modal scope excluding acoustic synthetic voice detection.
- **Relevance:** Inspired our hybrid CNN + Error Level Analysis (ELA) detection pipeline.

---

## 7. Technology Stack

- **Core Language:** Python 3.10+
- **Web Interface:** NiceGUI (Python component-based UI)
- **Database:** MySQL 8.0+ (`mysql-connector-python`)
- **Deep Learning:** TensorFlow / Keras
- **Image Processing:** OpenCV (`opencv-python`), Pillow
- **Audio Processing:** Librosa, SoundFile
- **Data Processing & ML:** NumPy, Pandas, Scikit-Learn, Joblib
- **Visualization & PDF Reports:** Matplotlib, ReportLab
- **Security:** bcrypt, python-dotenv

---

## 8. Database Architecture (MySQL)

Database Name: `media_manipulation_detection`

### 1. `users` Table
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. `detections` Table
```sql
CREATE TABLE detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    media_type VARCHAR(20) NOT NULL, -- IMAGE, VIDEO, AUDIO
    result VARCHAR(20) NOT NULL,     -- AUTHENTIC, MANIPULATED, SYNTHETIC, UNCERTAIN
    confidence FLOAT NOT NULL,
    manipulation_probability FLOAT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    processing_time FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 3. `reports` Table
```sql
CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    detection_id INT NOT NULL,
    report_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE
);
```

---

## 9. Installation & Setup Instructions

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/yourusername/AI_Media_Manipulation_Detection.git
cd AI_Media_Manipulation_Detection
python -m venv venv
# On Windows:
venv\Scripts\activate
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: MySQL Database Setup
1. Ensure MySQL Server is running on your machine.
2. Create database or configure credentials in `.env`:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=media_manipulation_detection
```
3. Initialize tables automatically by running database connection script or executing `database/database.sql` in MySQL Workbench / Command Line:
```bash
mysql -u root -p < database/database.sql
```

### Step 4: Model Training (Optional / Pre-evaluation)
To train models on your local datasets:
```bash
python models/train_image.py
python models/train_video.py
python models/train_audio.py
python models/evaluate_models.py
```

### Step 5: Run Application
```bash
python app.py
```
Open browser at: `http://127.0.0.1:8080`

---

## 10. System Disclaimer

> **DISCLAIMER:** This system provides an AI-based estimation of whether digital media may have been manipulated. Detection results are not guaranteed to be 100% accurate and should not be treated as definitive forensic evidence.

---

## 11. References

1. Rössler, A., et al. (2019). *FaceForensics++: Learning to Detect Manipulated Facial Images*. ICCV.
2. Dolhansky, B., et al. (2020). *The DeepFake Detection Challenge (DFDC) Dataset*. arXiv:2006.07397.
3. DeepFakeBench Team. (2023). *DeepFakeBench: A Comprehensive Benchmark of Deepfake Detection*. NeurIPS.
