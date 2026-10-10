from nicegui import ui
from backend import config
from frontend.components.layout import STYLE_BG, STYLE_CARD, render_public_header, render_disclaimer_card

def register_public_routes():
    @ui.page('/')
    def page_home():
        ui.query('body').style(STYLE_BG)
        render_public_header()

        # Hero Section
        with ui.column().classes("w-full max-w-6xl mx-auto px-6 py-16 items-center text-center gap-6"):
            ui.label("AI-BASED SYSTEM FOR").classes("text-xs font-bold tracking-widest text-cyan-400 bg-cyan-950 px-4 py-1.5 rounded-full border border-cyan-800")
            ui.label(config.APP_TITLE).classes("text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight")
            ui.label(config.APP_SUBTITLE).classes("text-xl text-cyan-300 font-medium")
            ui.label(
                "An AI-powered platform for analyzing images, videos, and audio to identify possible digital manipulation and synthetic content."
            ).classes("text-base text-gray-300 max-w-2xl leading-relaxed")

            with ui.row().classes("gap-4 mt-4"):
                ui.button("Start Detection", on_click=lambda: ui.navigate.to('/detect/image')).props("unelevated size=lg color=cyan-6 icon=radar").classes("rounded-xl px-6 font-bold shadow-lg shadow-cyan-950")
                ui.button("Learn More", on_click=lambda: ui.navigate.to('/how-it-works')).props("outline size=lg color=cyan-3 icon=info").classes("rounded-xl px-6 font-semibold")

        # Why Media Authenticity Matters
        with ui.column().classes("w-full max-w-6xl mx-auto px-6 py-10 gap-6"):
            with ui.card().style(STYLE_CARD).classes("w-full p-8"):
                ui.label("Why Media Authenticity Matters").classes("text-2xl font-bold text-white mb-2")
                ui.label(
                    "With recent advancements in Generative AI, Deepfake synthesis, neural voice cloning, and sophisticated image editing software, "
                    "digital media can easily be altered or artificially created. Establishing media integrity is essential for journalism, law enforcement, "
                    "digital forensics, cyber-defense, and public trust."
                ).classes("text-sm text-gray-300 leading-relaxed")

        # Supported Media Section
        with ui.column().classes("w-full max-w-6xl mx-auto px-6 py-10 gap-6"):
            ui.label("Supported Media Modalities").classes("text-2xl font-bold text-white text-center")
            with ui.row().classes("w-full grid grid-cols-1 md:grid-cols-3 gap-6"):
                # Image Card
                with ui.card().style(STYLE_CARD).classes("hover:border-cyan-400 transition-all cursor-pointer p-6 gap-3").on('click', lambda: ui.navigate.to('/detect/image')):
                    ui.icon("image", size="lg", color="cyan")
                    ui.label("IMAGE DETECTION").classes("text-lg font-bold text-white")
                    ui.label("Detect manipulated or AI-generated images using CNN & Error Level Analysis (ELA).").classes("text-xs text-gray-300 leading-relaxed")
                    ui.label("Supported: JPG, JPEG, PNG, WEBP").classes("text-xs text-cyan-400 font-mono mt-2")

                # Video Card
                with ui.card().style(STYLE_CARD).classes("hover:border-cyan-400 transition-all cursor-pointer p-6 gap-3").on('click', lambda: ui.navigate.to('/detect/video')):
                    ui.icon("videocam", size="lg", color="cyan")
                    ui.label("VIDEO DETECTION").classes("text-lg font-bold text-white")
                    ui.label("Analyze video frames, extract suspicious frames, and identify facial manipulation.").classes("text-xs text-gray-300 leading-relaxed")
                    ui.label("Supported: MP4, AVI, MOV, MKV").classes("text-xs text-cyan-400 font-mono mt-2")

                # Audio Card
                with ui.card().style(STYLE_CARD).classes("hover:border-cyan-400 transition-all cursor-pointer p-6 gap-3").on('click', lambda: ui.navigate.to('/detect/audio')):
                    ui.icon("graphic_eq", size="lg", color="cyan")
                    ui.label("AUDIO DETECTION").classes("text-lg font-bold text-white")
                    ui.label("Analyze acoustic features, Mel Spectrograms, and identify synthetic speech or voice cloning.").classes("text-xs text-gray-300 leading-relaxed")
                    ui.label("Supported: WAV, MP3, FLAC, M4A").classes("text-xs text-cyan-400 font-mono mt-2")

        # How It Works Pipeline
        with ui.column().classes("w-full max-w-6xl mx-auto px-6 py-12 gap-6 text-center"):
            ui.label("How It Works").classes("text-2xl font-bold text-white")
            with ui.row().classes("w-full flex justify-between items-center gap-2 overflow-x-auto py-4"):
                steps = [
                    ("Upload Media", "cloud_upload"),
                    ("Preprocess", "tune"),
                    ("Feature Extraction", "analytics"),
                    ("AI Model", "psychology"),
                    ("Prediction", "fact_check"),
                    ("Report", "picture_in_picture")
                ]
                for idx, (title, icon) in enumerate(steps):
                    with ui.column().classes("items-center gap-2 min-w-[120px]"):
                        with ui.avatar(icon=icon, color="cyan-9", text_color="cyan-3", size="lg"):
                            pass
                        ui.label(title).classes("text-xs font-semibold text-gray-200")
                    if idx < len(steps) - 1:
                        ui.icon("chevron_right", color="gray", size="md")

        # Key Features Grid
        with ui.column().classes("w-full max-w-6xl mx-auto px-6 py-10 gap-6"):
            ui.label("Key System Features").classes("text-2xl font-bold text-white text-center")
            with ui.row().classes("w-full grid grid-cols-2 md:grid-cols-4 gap-4"):
                features = [
                    ("Image Detection", "image"), ("Video Detection", "videocam"),
                    ("Audio Detection", "graphic_eq"), ("AI Prediction", "psychology"),
                    ("Detection History", "history"), ("Analytics", "insights"),
                    ("PDF Reports", "picture_as_pdf"), ("Secure Login", "lock")
                ]
                for title, icon in features:
                    with ui.card().style(STYLE_CARD).classes("p-4 flex flex-row items-center gap-3"):
                        ui.icon(icon, color="cyan", size="sm")
                        ui.label(title).classes("text-xs font-bold text-white")

        render_disclaimer_card()

    @ui.page('/about')
    def page_about():
        ui.query('body').style(STYLE_BG)
        render_public_header()
        with ui.column().classes("w-full max-w-5xl mx-auto px-6 py-12 gap-6"):
            ui.label("About The System").classes("text-3xl font-extrabold text-white")
            with ui.card().style(STYLE_CARD).classes("w-full p-8 gap-4"):
                ui.label("Final Year BE Major Project Overview").classes("text-xl font-bold text-cyan-400")
                ui.label(
                    "This project represents a comprehensive, multi-modal AI platform designed to detect digital media manipulation "
                    "across image, video, and audio signals. Built using Python, TensorFlow/Keras, OpenCV, Librosa, and NiceGUI, "
                    "the application provides real-time model inference, visual feature inspection, MySQL-backed analysis history, "
                    "and automated ReportLab PDF report generation."
                ).classes("text-sm text-gray-300 leading-relaxed")

                ui.label("Technology Stack").classes("text-lg font-bold text-white mt-4")
                with ui.row().classes("gap-2 flex-wrap"):
                    techs = ["Python", "NiceGUI", "MySQL", "TensorFlow", "Keras", "OpenCV", "Librosa", "Pillow", "ReportLab", "Scikit-learn", "bcrypt"]
                    for t in techs:
                        ui.chip(t, color="cyan-9", text_color="cyan-2").classes("font-mono text-xs")

    @ui.page('/how-it-works')
    def page_how_it_works():
        ui.query('body').style(STYLE_BG)
        render_public_header()
        with ui.column().classes("w-full max-w-5xl mx-auto px-6 py-12 gap-6"):
            ui.label("Detection Workflow & Technical Architecture").classes("text-3xl font-extrabold text-white")
            
            workflows = [
                ("1. Image Manipulation Pipeline", "image", "Loads RGB image, resizes to (224, 224, 3), and normalizes pixel intensities. Computes Error Level Analysis (ELA) to expose re-compression variances, then inputs tensor into a Multi-Stage CNN Classifier."),
                ("2. Video Frame Extraction Pipeline", "videocam", "Opens video container via OpenCV, extracts evenly spaced sample frames, normalizes frame arrays, runs CNN classification across individual frames, flags suspicious frames, and aggregates predictions into a final score."),
                ("3. Audio Spectrogram Pipeline", "graphic_eq", "Reads audio signal via Librosa, extracts 128-band Mel Spectrograms and 20 MFCC coefficients, plots acoustic figures, and evaluates spectral matrices using a 2D Spectrogram Neural Classifier.")
            ]
            for title, icon, desc in workflows:
                with ui.card().style(STYLE_CARD).classes("w-full p-6 gap-2"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon(icon, color="cyan", size="md")
                        ui.label(title).classes("text-lg font-bold text-white")
                    ui.label(desc).classes("text-sm text-gray-300 leading-relaxed")

    @ui.page('/research')
    def page_research():
        ui.query('body').style(STYLE_BG)
        render_public_header()
        with ui.column().classes("w-full max-w-5xl mx-auto px-6 py-12 gap-6"):
            ui.label("Academic Literature Review & Research Basis").classes("text-3xl font-extrabold text-white")
            
            # Research Gap Card
            with ui.card().style(STYLE_CARD).classes("w-full p-6 border-l-4 border-l-cyan-400 bg-slate-900"):
                ui.label("RESEARCH GAP STATEMENT").classes("text-xs font-bold text-cyan-400 tracking-wider")
                ui.label(
                    "Existing media manipulation detection research often focuses on particular media types or manipulation techniques. "
                    "This project aims to integrate image, video, and audio analysis into a single user-oriented platform with unified detection, history, analytics, and reporting."
                ).classes("text-sm text-gray-200 mt-1 leading-relaxed")

            # Key Papers
            papers = [
                {
                    "title": "FaceForensics++: Learning to Detect Manipulated Facial Images",
                    "authors": "Andreas Rössler, Davide Cozzolino, Luisa Verdoliva, Christian Riess, Justus Thies, Matthias Nießner",
                    "year": "2019",
                    "dataset": "FaceForensics++ (1.8M frames, Deepfakes, Face2Face, FaceSwap, NeuralTextures)",
                    "method": "XceptionNet fine-tuned on domain-specific facial forgery images",
                    "contribution": "Established benchmark dataset and proved high transfer accuracy of constrained CNNs on compressed video forgeries.",
                    "limitation": "Accuracy degrades under extreme lossy social media compression codecs.",
                    "relevance": "Provides foundational CNN architecture baseline for image and frame-level facial manipulation detection in our system."
                },
                {
                    "title": "The DeepFake Detection Challenge (DFDC) Dataset",
                    "authors": "Brian Dolhansky, Joanna Bitton, Ben Pflaum, Jaron Lu, Russ Howes, Menglin Wang, Cristian Canton Ferrer",
                    "year": "2020",
                    "dataset": "DFDC (100,000+ total video clips with diverse subjects, lighting, and backgrounds)",
                    "method": "Multi-frame ensemble model with 3D CNNs and ResNet backbones",
                    "contribution": "Introduced large-scale real-world facial swap dataset with variable resolution and lighting artifacts.",
                    "limitation": "High computational overhead for full video temporal sequences.",
                    "relevance": "Guides our video frame sampling strategy and threshold calibration."
                },
                {
                    "title": "DeepFakeBench: A Comprehensive Benchmark of Deepfake Detection",
                    "authors": "DeepFakeBench Research Team",
                    "year": "2023",
                    "dataset": "Unified evaluation across FF++, Celeb-DF, DFDC, and WildDeepfake",
                    "method": "Standardized evaluation pipeline comparing spatial, frequency, and temporal deep learning models",
                    "contribution": "Proved necessity of combining spatial CNN features with frequency-domain features (such as ELA / FFT).",
                    "limitation": "Single-modal focus on image/video without audio integration.",
                    "relevance": "Directly inspires our hybrid CNN + Error Level Analysis (ELA) multi-modal feature design."
                }
            ]

            for p in papers:
                with ui.card().style(STYLE_CARD).classes("w-full p-6 gap-3"):
                    ui.label(p["title"]).classes("text-xl font-bold text-white")
                    with ui.row().classes("gap-4 text-xs font-mono text-cyan-400"):
                        ui.label(f"Authors: {p['authors']}")
                        ui.label(f"Year: {p['year']}")
                    
                    with ui.column().classes("gap-1 text-xs text-gray-300 mt-2"):
                        ui.label(f"• Dataset Used: {p['dataset']}")
                        ui.label(f"• Detection Method: {p['method']}")
                        ui.label(f"• Core Contribution: {p['contribution']}")
                        ui.label(f"• Limitation: {p['limitation']}")
                        ui.label(f"• Relevance to Project: {p['relevance']}").classes("text-cyan-300 font-semibold")

    @ui.page('/contact')
    def page_contact():
        ui.query('body').style(STYLE_BG)
        render_public_header()
        with ui.column().classes("w-full max-w-4xl mx-auto px-6 py-12 gap-6"):
            ui.label("Academic Contact & Project Inquiries").classes("text-3xl font-extrabold text-white")
            with ui.card().style(STYLE_CARD).classes("w-full p-8 gap-4"):
                ui.label("Department of Computer Engineering").classes("text-lg font-bold text-cyan-400")
                ui.label("Project Title: AI-Based System for Media Manipulation Detection").classes("text-sm text-white font-semibold")
                ui.label("Bachelor of Engineering (B.E.) Major Project").classes("text-sm text-gray-300")
                ui.separator().classes("bg-gray-700")
                
                with ui.column().classes("gap-3 max-w-md w-full"):
                    c_name = ui.input("Your Name").props("outlined dark color=cyan")
                    c_email = ui.input("Your Email").props("outlined dark color=cyan")
                    c_msg = ui.textarea("Message").props("outlined dark color=cyan")
                    ui.button("Send Inquiry", on_click=lambda: ui.notify("Message sent successfully!", type="positive")).props("unelevated color=cyan-7")
