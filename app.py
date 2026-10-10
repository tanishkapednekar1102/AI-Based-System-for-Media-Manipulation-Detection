import os
import sys
import shutil
import logging
from datetime import datetime
from nicegui import ui, app

import config
from database.connection import init_db, is_db_connected
from database.users import register_user, authenticate_user
from database.detections import (
    save_detection, get_user_detections, get_detection_by_id, get_analytics_summary
)
from database.reports import get_report_by_detection_id
from detection.image_detector import detect_image
from detection.video_detector import detect_video
from detection.audio_detector import detect_audio
from reports.pdf_report import generate_pdf_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Initialize MySQL Database tables
init_db()

# Application Page Styling Constants
STYLE_BG = "background-color: #0B132B; color: #FEFCFB; min-height: 100vh; font-family: 'Inter', sans-serif;"
STYLE_NAVBAR = "background-color: #0A1128; border-bottom: 1px solid #1282A2;"
STYLE_CARD = "background-color: #1C2541; border: 1px solid #1282A2; border-radius: 12px; padding: 20px;"
STYLE_SIDEBAR = "background-color: #0A1128; border-right: 1px solid #1282A2; width: 260px;"

def get_current_user():
    """Retrieves authenticated user dict from session storage."""
    return app.storage.user.get('user', None)

def require_auth():
    """Redirects unauthenticated users to the login page."""
    user = get_current_user()
    if not user:
        ui.navigate.to('/login')
        return None
    return user

def render_result_badge(result_str: str):
    """Renders styled result badge for AUTHENTIC, MANIPULATED, SYNTHETIC, UNCERTAIN."""
    res = str(result_str).upper()
    if res == "AUTHENTIC":
        ui.label("AUTHENTIC").classes("px-3 py-1 text-xs font-bold rounded-full bg-emerald-600 text-white")
    elif res == "MANIPULATED":
        ui.label("MANIPULATED").classes("px-3 py-1 text-xs font-bold rounded-full bg-red-600 text-white")
    elif res == "SYNTHETIC":
        ui.label("SYNTHETIC").classes("px-3 py-1 text-xs font-bold rounded-full bg-amber-600 text-white")
    else:
        ui.label("UNCERTAIN").classes("px-3 py-1 text-xs font-bold rounded-full bg-gray-600 text-white")

def render_public_header():
    """Renders navigation header for public pages."""
    user = get_current_user()
    with ui.header().style(STYLE_NAVBAR).classes("w-full px-8 py-3 flex justify-between items-center shadow-lg"):
        with ui.row().classes("items-center gap-3 cursor-pointer").on('click', lambda: ui.navigate.to('/')):
            ui.icon("security", size="md", color="cyan")
            with ui.column().classes("gap-0"):
                ui.label(config.APP_TITLE).classes("text-lg font-bold text-white tracking-wide")
                ui.label(config.APP_SUBTITLE).classes("text-xs text-cyan-400 font-medium")

        with ui.row().classes("gap-6 items-center text-sm font-medium"):
            ui.link("Home", "/").classes("text-gray-200 hover:text-cyan-400 no-underline")
            ui.link("About", "/about").classes("text-gray-200 hover:text-cyan-400 no-underline")
            ui.link("How It Works", "/how-it-works").classes("text-gray-200 hover:text-cyan-400 no-underline")
            ui.link("Research", "/research").classes("text-gray-200 hover:text-cyan-400 no-underline")
            ui.link("Contact", "/contact").classes("text-gray-200 hover:text-cyan-400 no-underline")

            if user:
                ui.button("Dashboard", on_click=lambda: ui.navigate.to('/dashboard')).props("unelevated color=cyan-7 text-color=white icon=dashboard").classes("rounded-lg px-4")
                ui.button("Logout", on_click=lambda: ui.navigate.to('/logout')).props("flat color=grey-4").classes("rounded-lg")
            else:
                ui.button("Login", on_click=lambda: ui.navigate.to('/login')).props("outline color=cyan-4").classes("rounded-lg px-4")
                ui.button("Register", on_click=lambda: ui.navigate.to('/register')).props("unelevated color=cyan-7 text-color=white").classes("rounded-lg px-4")

def render_dashboard_layout(page_title: str):
    """Renders layout with sidebar and header for authenticated dashboard pages."""
    user = require_auth()
    if not user:
        return None

    with ui.header().style(STYLE_NAVBAR).classes("w-full px-8 py-3 flex justify-between items-center shadow-md"):
        with ui.row().classes("items-center gap-3"):
            ui.label(config.APP_TITLE).classes("text-base font-bold text-white")
            ui.label(f"| {page_title}").classes("text-sm text-cyan-400 font-semibold")
        
        with ui.row().classes("items-center gap-4"):
            with ui.row().classes("items-center gap-2 text-sm text-gray-300"):
                ui.icon("account_circle", color="cyan", size="sm")
                ui.label(user.get("full_name", "User")).classes("font-semibold text-white")
            ui.button("Logout", on_click=lambda: ui.navigate.to('/logout')).props("flat size=sm color=red-4 icon=logout")

    with ui.left_drawer(value=True, fixed=True).style(STYLE_SIDEBAR).classes("p-4 flex flex-col gap-2"):
        ui.label("CORE NAVIGATION").classes("text-xs font-bold text-gray-400 px-3 my-2 tracking-wider")
        
        nav_items = [
            ("Dashboard", "dashboard", "/dashboard"),
            ("Image Detection", "image", "/detect/image"),
            ("Video Detection", "videocam", "/detect/video"),
            ("Audio Detection", "graphic_eq", "/detect/audio"),
            ("Detection History", "history", "/history"),
            ("Analytics", "bar_chart", "/analytics"),
            ("PDF Reports", "description", "/reports"),
            ("Profile", "person", "/profile"),
        ]

        for label, icon, path in nav_items:
            has_native_window = hasattr(app, 'native') and app.native and getattr(app.native, 'main_window', None) is not None
            is_active = (app.native.main_window.url if has_native_window else "").endswith(path)
            btn_props = "unelevated color=cyan-8" if is_active else "flat color=grey-3"
            ui.button(label, icon=icon, on_click=lambda p=path: ui.navigate.to(p)).props(f"align=left {btn_props}").classes("w-full rounded-lg text-sm font-medium my-0.5")

        ui.element('div').classes("mt-auto")
        ui.label(f"MySQL DB: {'CONNECTED' if is_db_connected() else 'OFFLINE'}").classes(
            f"text-xs font-semibold px-3 py-1.5 rounded-md {'bg-emerald-950 text-emerald-300' if is_db_connected() else 'bg-red-950 text-red-300'}"
        )

    return user

def render_disclaimer_card():
    """Renders academic disclaimer card at footer of analysis pages."""
    with ui.card().style(STYLE_CARD).classes("w-full mt-8 border-l-4 border-l-amber-500 bg-slate-900"):
        with ui.row().classes("items-center gap-3"):
            ui.icon("warning", color="amber", size="sm")
            ui.label("ACADEMIC DISCLAIMER & LEGAL FORENSIC NOTICE").classes("text-sm font-bold text-amber-400")
        ui.label(
            "This system provides an AI-based estimation of whether digital media may have been manipulated. "
            "Detection results are not guaranteed to be 100% accurate and should not be treated as definitive forensic evidence."
        ).classes("text-xs text-gray-300 mt-1 leading-relaxed")


# ==============================================================================
# PUBLIC PAGES
# ==============================================================================

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

@ui.page('/register')
def page_register():
    ui.query('body').style(STYLE_BG)
    render_public_header()

    with ui.column().classes("w-full max-w-md mx-auto px-6 py-16 gap-6 items-center"):
        with ui.card().style(STYLE_CARD).classes("w-full p-8 gap-4"):
            ui.label("Create New Account").classes("text-2xl font-bold text-white text-center")
            ui.label("Register to access media detection and history").classes("text-xs text-gray-400 text-center")

            full_name = ui.input("Full Name").props("outlined dark color=cyan icon=person").classes("w-full")
            email = ui.input("Email Address").props("outlined dark color=cyan icon=email").classes("w-full")
            password = ui.input("Password", password=True).props("outlined dark color=cyan icon=lock").classes("w-full")
            confirm_pwd = ui.input("Confirm Password", password=True).props("outlined dark color=cyan icon=lock").classes("w-full")

            def handle_register():
                if password.value != confirm_pwd.value:
                    ui.notify("Passwords do not match.", type="negative")
                    return

                success, msg = register_user(full_name.value, email.value, password.value)
                if success:
                    ui.notify(msg, type="positive")
                    ui.navigate.to('/login')
                else:
                    ui.notify(msg, type="negative")

            ui.button("Register Account", on_click=handle_register).props("unelevated color=cyan-7 text-color=white").classes("w-full py-3 rounded-lg font-bold mt-2")
            with ui.row().classes("justify-center text-xs text-gray-400 mt-2"):
                ui.label("Already have an account?")
                ui.link("Login here", "/login").classes("text-cyan-400 font-semibold no-underline")

@ui.page('/login')
def page_login():
    ui.query('body').style(STYLE_BG)
    render_public_header()

    with ui.column().classes("w-full max-w-md mx-auto px-6 py-16 gap-6 items-center"):
        with ui.card().style(STYLE_CARD).classes("w-full p-8 gap-4"):
            ui.label("User Login").classes("text-2xl font-bold text-white text-center")
            ui.label("Sign in to access forensic detection dashboard").classes("text-xs text-gray-400 text-center")

            email = ui.input("Email Address").props("outlined dark color=cyan icon=email").classes("w-full")
            password = ui.input("Password", password=True).props("outlined dark color=cyan icon=lock").classes("w-full")

            def handle_login():
                success, msg, user_info = authenticate_user(email.value, password.value)
                if success and user_info:
                    app.storage.user['user'] = user_info
                    ui.notify(msg, type="positive")
                    ui.navigate.to('/dashboard')
                else:
                    ui.notify(msg, type="negative")

            ui.button("Login to Dashboard", on_click=handle_login).props("unelevated color=cyan-7 text-color=white").classes("w-full py-3 rounded-lg font-bold mt-2")
            with ui.row().classes("justify-center text-xs text-gray-400 mt-2"):
                ui.label("Don't have an account?")
                ui.link("Register here", "/register").classes("text-cyan-400 font-semibold no-underline")

@ui.page('/logout')
def page_logout():
    app.storage.user.clear()
    ui.notify("Logged out successfully.", type="info")
    ui.navigate.to('/')


# ==============================================================================
# PROTECTED DASHBOARD PAGES
# ==============================================================================

@ui.page('/dashboard')
def page_dashboard():
    ui.query('body').style(STYLE_BG)
    user = render_dashboard_layout("Dashboard Overview")
    if not user: return

    summary = get_analytics_summary(user["id"])

    with ui.column().classes("w-full p-8 gap-6 ml-[260px] max-w-[calc(100vw-280px)]"):
        ui.label(f"Welcome back, {user['full_name']}").classes("text-2xl font-extrabold text-white")

        # Metric Cards Grid
        with ui.row().classes("w-full grid grid-cols-2 md:grid-cols-6 gap-4"):
            metrics = [
                ("Total Analyses", summary["total_analyses"], "analytics", "cyan"),
                ("Authentic Media", summary["authentic_count"], "verified", "emerald"),
                ("Manipulated", summary["manipulated_count"], "warning", "red"),
                ("Images Analyzed", summary["images_count"], "image", "blue"),
                ("Videos Analyzed", summary["videos_count"], "videocam", "indigo"),
                ("Audio Analyzed", summary["audio_count"], "graphic_eq", "teal")
            ]
            for title, count, icon, color in metrics:
                with ui.card().style(STYLE_CARD).classes("p-4 gap-1"):
                    with ui.row().classes("justify-between items-center w-full"):
                        ui.label(title).classes("text-xs font-semibold text-gray-400")
                        ui.icon(icon, color=color, size="xs")
                    ui.label(str(count)).classes("text-2xl font-extrabold text-white")

        # Recent Detections Table
        with ui.card().style(STYLE_CARD).classes("w-full p-6 gap-4"):
            ui.label("Recent Detection Logs").classes("text-lg font-bold text-white")

            columns = [
                {'name': 'file_name', 'label': 'File Name', 'field': 'file_name', 'required': True, 'align': 'left'},
                {'name': 'media_type', 'label': 'Media Type', 'field': 'media_type', 'align': 'center'},
                {'name': 'result', 'label': 'Detection Result', 'field': 'result', 'align': 'center'},
                {'name': 'confidence', 'label': 'Confidence', 'field': 'confidence', 'align': 'center'},
                {'name': 'created_at', 'label': 'Timestamp', 'field': 'created_at', 'align': 'right'},
            ]

            rows = []
            for d in summary["recent_detections"]:
                created_str = d["created_at"].strftime("%Y-%m-%d %H:%M") if isinstance(d["created_at"], datetime) else str(d["created_at"])
                rows.append({
                    'file_name': d["file_name"],
                    'media_type': d["media_type"],
                    'result': d["result"],
                    'confidence': f"{d['confidence']}%",
                    'created_at': created_str
                })

            ui.table(columns=columns, rows=rows, row_key='file_name').classes("w-full bg-slate-900 text-white dark")

        render_disclaimer_card()

@ui.page('/detect/image')
def page_detect_image():
    ui.query('body').style(STYLE_BG)
    user = render_dashboard_layout("Image Detection")
    if not user: return

    result_container = ui.column().classes("w-full gap-4 mt-6")

    with ui.column().classes("w-full p-8 gap-6 ml-[260px] max-w-[calc(100vw-280px)]"):
        ui.label("Image Media Manipulation Detection").classes("text-2xl font-extrabold text-white")
        ui.label("Upload an image (JPG, JPEG, PNG, WEBP) to run deep learning forgery and ELA compression analysis.").classes("text-xs text-gray-400")

        with ui.card().style(STYLE_CARD).classes("w-full p-6 items-center text-center border-dashed border-2 border-cyan-500/50"):
            ui.icon("cloud_upload", size="xl", color="cyan")
            ui.label("Drag & Drop Image File Here or Click to Upload").classes("text-sm font-bold text-white mt-2")
            ui.label("Max size: 20MB • Formats: .jpg, .jpeg, .png, .webp").classes("text-xs text-gray-400 mb-4")

            async def handle_upload(e):
                try:
                    file = e.file
                    save_path = os.path.join(config.UPLOAD_DIR, file.name)
                    await file.save(save_path)

                    ui.notify(f"Image '{file.name}' uploaded successfully. Running AI prediction...", type="info")
                    res = detect_image(save_path, user_id=user["id"])

                    result_container.clear()
                    with result_container:
                        render_detection_result_card(res, user)
                except Exception as err:
                    ui.notify(f"Image Analysis Error: {str(err)}", type="negative")

            ui.upload(on_upload=handle_upload, auto_upload=True).props("accept='.jpg,.jpeg,.png,.webp' flat color=cyan-6").classes("w-full max-w-sm")

        # Container for results
        result_container

        render_disclaimer_card()

@ui.page('/detect/video')
def page_detect_video():
    ui.query('body').style(STYLE_BG)
    user = render_dashboard_layout("Video Detection")
    if not user: return

    result_container = ui.column().classes("w-full gap-4 mt-6")

    with ui.column().classes("w-full p-8 gap-6 ml-[260px] max-w-[calc(100vw-280px)]"):
        ui.label("Video Deepfake & Manipulation Detection").classes("text-2xl font-extrabold text-white")
        ui.label("Upload video file (MP4, AVI, MOV, MKV). Analyzes frame-by-frame for facial manipulation.").classes("text-xs text-gray-400")

        with ui.card().style(STYLE_CARD).classes("w-full p-6 items-center text-center border-dashed border-2 border-cyan-500/50"):
            ui.icon("video_library", size="xl", color="cyan")
            ui.label("Upload Video File").classes("text-sm font-bold text-white mt-2")

            async def handle_upload(e):
                try:
                    file = e.file
                    save_path = os.path.join(config.UPLOAD_DIR, file.name)
                    await file.save(save_path)

                    ui.notify(f"Video '{file.name}' uploaded. Extracting and analyzing frames...", type="info")
                    res = detect_video(save_path, user_id=user["id"])

                    result_container.clear()
                    with result_container:
                        render_detection_result_card(res, user)
                except Exception as err:
                    ui.notify(f"Video Analysis Error: {str(err)}", type="negative")

            ui.upload(on_upload=handle_upload, auto_upload=True).props("accept='.mp4,.avi,.mov,.mkv' flat color=cyan-6").classes("w-full max-w-sm")

        result_container
        render_disclaimer_card()

@ui.page('/detect/audio')
def page_detect_audio():
    ui.query('body').style(STYLE_BG)
    user = render_dashboard_layout("Audio Detection")
    if not user: return

    result_container = ui.column().classes("w-full gap-4 mt-6")

    with ui.column().classes("w-full p-8 gap-6 ml-[260px] max-w-[calc(100vw-280px)]"):
        ui.label("Audio Synthetic Speech & Voice Clone Detection").classes("text-2xl font-extrabold text-white")
        ui.label("Upload audio clip (WAV, MP3, FLAC, M4A). Extracts Mel-Spectrograms & MFCC acoustic features.").classes("text-xs text-gray-400")

        with ui.card().style(STYLE_CARD).classes("w-full p-6 items-center text-center border-dashed border-2 border-cyan-500/50"):
            ui.icon("graphic_eq", size="xl", color="cyan")
            ui.label("Upload Audio File").classes("text-sm font-bold text-white mt-2")

            async def handle_upload(e):
                try:
                    file = e.file
                    save_path = os.path.join(config.UPLOAD_DIR, file.name)
                    await file.save(save_path)

                    ui.notify(f"Audio clip '{file.name}' uploaded. Computing spectrogram features...", type="info")
                    res = detect_audio(save_path, user_id=user["id"])

                    result_container.clear()
                    with result_container:
                        render_detection_result_card(res, user)
                except Exception as err:
                    ui.notify(f"Audio Analysis Error: {str(err)}", type="negative")

            ui.upload(on_upload=handle_upload, auto_upload=True).props("accept='.wav,.mp3,.flac,.m4a' flat color=cyan-6").classes("w-full max-w-sm")

        result_container
        render_disclaimer_card()

def render_detection_result_card(res: dict, user: dict):
    """Renders comprehensive analysis result card for image, video, and audio detections."""
    with ui.card().style(STYLE_CARD).classes("w-full p-6 gap-6 bg-slate-900 border-2 border-cyan-500"):
        with ui.row().classes("justify-between items-center w-full"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("fact_check", color="cyan", size="md")
                ui.label(f"Analysis Results: {res['file_name']}").classes("text-xl font-bold text-white")
            render_result_badge(res['result'])

        with ui.row().classes("w-full grid grid-cols-1 md:grid-cols-4 gap-4"):
            with ui.card().style(STYLE_CARD).classes("p-4"):
                ui.label("Detection Result").classes("text-xs text-gray-400")
                ui.label(res['result']).classes("text-xl font-extrabold text-white mt-1")

            with ui.card().style(STYLE_CARD).classes("p-4"):
                ui.label("AI Model Confidence").classes("text-xs text-gray-400")
                ui.label(res['confidence']).classes("text-xl font-extrabold text-cyan-400 mt-1")

            with ui.card().style(STYLE_CARD).classes("p-4"):
                ui.label("Manipulation Probability").classes("text-xs text-gray-400")
                ui.label(res['manipulation_probability']).classes("text-xl font-extrabold text-amber-400 mt-1")

            with ui.card().style(STYLE_CARD).classes("p-4"):
                ui.label("Processing Duration").classes("text-xs text-gray-400")
                ui.label(res['processing_time']).classes("text-xl font-extrabold text-emerald-400 mt-1")

        # Media Specific Visual Previews
        if res["media_type"] == "IMAGE" and os.path.exists(res.get("image_path", "")):
            ui.label("Uploaded Media Inspection Preview").classes("text-sm font-bold text-white mt-2")
            ui.image(res["image_path"]).classes("max-h-64 rounded-lg border border-cyan-800 object-contain")

        elif res["media_type"] == "AUDIO" and os.path.exists(res.get("visualization_path", "")):
            ui.label("Extracted Acoustic Waveform & Mel-Spectrogram Matrix").classes("text-sm font-bold text-white mt-2")
            ui.image(res["visualization_path"]).classes("w-full max-h-80 rounded-lg border border-cyan-800 object-contain")

        elif res["media_type"] == "VIDEO" and res.get("suspicious_frames"):
            ui.label(f"Analyzed Frames ({res['frames_analyzed']} total sampled, {res['suspicious_frames_count']} flagged suspicious)").classes("text-sm font-bold text-white mt-2")
            with ui.row().classes("gap-2 overflow-x-auto p-2 border border-slate-800 rounded-lg w-full"):
                for sf in res["suspicious_frames"][:8]:
                    if os.path.exists(sf["thumbnail_path"]):
                        with ui.column().classes("items-center gap-1 border border-slate-700 p-1 rounded-md bg-slate-950"):
                            ui.image(sf["thumbnail_path"]).classes("w-24 h-20 object-cover rounded")
                            ui.label(f"Frame #{sf['frame_index']}").classes("text-[10px] text-gray-300")
                            ui.label(f"{sf['probability']}%").classes("text-[10px] font-bold text-red-400" if sf['is_suspicious'] else "text-[10px] text-emerald-400")

        # Technical Metadata Table
        with ui.column().classes("w-full gap-2 mt-2"):
            ui.label("Technical Details").classes("text-sm font-bold text-cyan-400")
            ui.label(f"Model Architecture Used: {res['model_name']}").classes("text-xs text-gray-300 font-mono")
            if res.get("dimensions"): ui.label(f"Resolution / Dimensions: {res['dimensions']}").classes("text-xs text-gray-300 font-mono")
            if res.get("duration"): ui.label(f"Media Duration: {res['duration']}").classes("text-xs text-gray-300 font-mono")

        # Action Buttons
        def download_pdf():
            try:
                pdf_path = generate_pdf_report(res, user_name=user["full_name"])
                ui.notify(f"PDF Report generated: {os.path.basename(pdf_path)}", type="positive")
                ui.download(pdf_path)
            except Exception as e:
                ui.notify(f"PDF Generation Error: {str(e)}", type="negative")

        with ui.row().classes("gap-4 mt-4"):
            ui.button("Download PDF Report", on_click=download_pdf).props("unelevated color=cyan-7 icon=picture_as_pdf").classes("rounded-lg font-bold")
            ui.button("New Analysis", on_click=lambda: ui.navigate.to(f"/detect/{res['media_type'].lower()}")).props("outline color=cyan-3 icon=refresh")

@ui.page('/history')
def page_history():
    ui.query('body').style(STYLE_BG)
    user = render_dashboard_layout("Detection History")
    if not user: return

    records_container = ui.column().classes("w-full gap-4 mt-4")

    def load_records(media_filter="ALL", result_filter="ALL"):
        records = get_user_detections(user["id"], media_filter=media_filter, result_filter=result_filter)
        records_container.clear()
        with records_container:
            if not records:
                ui.label("No detection records found matching criteria.").classes("text-sm text-gray-400 italic p-4")
                return

            columns = [
                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                {'name': 'file_name', 'label': 'File Name', 'field': 'file_name', 'align': 'left'},
                {'name': 'media_type', 'label': 'Media Type', 'field': 'media_type', 'align': 'center'},
                {'name': 'result', 'label': 'Result', 'field': 'result', 'align': 'center'},
                {'name': 'confidence', 'label': 'Confidence', 'field': 'confidence', 'align': 'center'},
                {'name': 'model_name', 'label': 'Model', 'field': 'model_name', 'align': 'left'},
                {'name': 'created_at', 'label': 'Date', 'field': 'created_at', 'align': 'right'},
            ]

            rows = []
            for r in records:
                created_str = r["created_at"].strftime("%Y-%m-%d %H:%M") if isinstance(r["created_at"], datetime) else str(r["created_at"])
                rows.append({
                    'id': r["id"],
                    'file_name': r["file_name"],
                    'media_type': r["media_type"],
                    'result': r["result"],
                    'confidence': f"{r['confidence']}%",
                    'model_name': r["model_name"],
                    'created_at': created_str
                })

            ui.table(columns=columns, rows=rows, row_key='id').classes("w-full bg-slate-900 text-white dark")

    with ui.column().classes("w-full p-8 gap-6 ml-[260px] max-w-[calc(100vw-280px)]"):
        ui.label("Media Analysis History").classes("text-2xl font-extrabold text-white")

        # Filters Header
        with ui.card().style(STYLE_CARD).classes("w-full p-4 flex flex-row items-center gap-6"):
            media_sel = ui.select(["ALL", "IMAGE", "VIDEO", "AUDIO"], value="ALL", label="Filter Media Type").props("dark color=cyan").classes("w-48")
            result_sel = ui.select(["ALL", "AUTHENTIC", "MANIPULATED", "UNCERTAIN"], value="ALL", label="Filter Result").props("dark color=cyan").classes("w-48")
            ui.button("Apply Filter", on_click=lambda: load_records(media_sel.value, result_sel.value)).props("unelevated color=cyan-7")

        records_container
        load_records()
        render_disclaimer_card()

@ui.page('/analytics')
def page_analytics():
    ui.query('body').style(STYLE_BG)
    user = render_dashboard_layout("Analytics & Statistics")
    if not user: return

    summary = get_analytics_summary(user["id"])

    with ui.column().classes("w-full p-8 gap-6 ml-[260px] max-w-[calc(100vw-280px)]"):
        ui.label("Forensic Analytics & Media Distribution").classes("text-2xl font-extrabold text-white")

        # Analytics Overview Cards
        with ui.row().classes("w-full grid grid-cols-2 md:grid-cols-4 gap-4"):
            with ui.card().style(STYLE_CARD).classes("p-4"):
                ui.label("Total Analyzed").classes("text-xs text-gray-400")
                ui.label(str(summary["total_analyses"])).classes("text-2xl font-bold text-white")
            with ui.card().style(STYLE_CARD).classes("p-4"):
                ui.label("Authentic Count").classes("text-xs text-gray-400")
                ui.label(str(summary["authentic_count"])).classes("text-2xl font-bold text-emerald-400")
            with ui.card().style(STYLE_CARD).classes("p-4"):
                ui.label("Manipulated / Synthetic").classes("text-xs text-gray-400")
                ui.label(str(summary["manipulated_count"] + summary["synthetic_count"])).classes("text-2xl font-bold text-red-400")
            with ui.card().style(STYLE_CARD).classes("p-4"):
                ui.label("Uncertain Count").classes("text-xs text-gray-400")
                ui.label(str(summary["uncertain_count"])).classes("text-2xl font-bold text-gray-400")

        # Visual ECharts integration in NiceGUI
        with ui.row().classes("w-full grid grid-cols-1 md:grid-cols-2 gap-6 mt-4"):
            # Chart 1: Authentic vs Manipulated Ratio
            with ui.card().style(STYLE_CARD).classes("p-6 gap-2 w-full"):
                ui.label("Authentic vs Manipulated Distribution").classes("text-base font-bold text-white")
                ui.echart({
                    'tooltip': {'trigger': 'item'},
                    'legend': {'top': '5%', 'left': 'center', 'textStyle': {'color': '#FEFCFB'}},
                    'series': [{
                        'name': 'Detection Ratio',
                        'type': 'pie',
                        'radius': ['40%', '70%'],
                        'avoidLabelOverlap': False,
                        'itemStyle': {'borderRadius': 10, 'borderColor': '#1C2541', 'borderWidth': 2},
                        'label': {'show': False},
                        'data': [
                            {'value': summary["authentic_count"], 'name': 'Authentic', 'itemStyle': {'color': '#10B981'}},
                            {'value': summary["manipulated_count"] + summary["synthetic_count"], 'name': 'Manipulated/Synthetic', 'itemStyle': {'color': '#EF4444'}},
                            {'value': summary["uncertain_count"], 'name': 'Uncertain', 'itemStyle': {'color': '#6B7280'}}
                        ]
                    }]
                }).classes("w-full h-64")

            # Chart 2: Media Type Distribution
            with ui.card().style(STYLE_CARD).classes("p-6 gap-2 w-full"):
                ui.label("Media Type Modality Breakdown").classes("text-base font-bold text-white")
                ui.echart({
                    'xAxis': {'type': 'category', 'data': ['Images', 'Videos', 'Audio'], 'axisLabel': {'color': '#FEFCFB'}},
                    'yAxis': {'type': 'value', 'axisLabel': {'color': '#FEFCFB'}},
                    'series': [{
                        'data': [
                            {'value': summary["images_count"], 'itemStyle': {'color': '#00B4D8'}},
                            {'value': summary["videos_count"], 'itemStyle': {'color': '#1282A2'}},
                            {'value': summary["audio_count"], 'itemStyle': {'color': '#0077B6'}}
                        ],
                        'type': 'bar',
                        'barWidth': '40%'
                    }]
                }).classes("w-full h-64")

        render_disclaimer_card()

@ui.page('/reports')
def page_reports():
    ui.query('body').style(STYLE_BG)
    user = render_dashboard_layout("PDF Forensic Reports")
    if not user: return

    summary = get_analytics_summary(user["id"])

    with ui.column().classes("w-full p-8 gap-6 ml-[260px] max-w-[calc(100vw-280px)]"):
        ui.label("Generated Forensic PDF Reports").classes("text-2xl font-extrabold text-white")

        with ui.card().style(STYLE_CARD).classes("w-full p-6 gap-4"):
            if not summary["recent_detections"]:
                ui.label("No reports generated yet. Run a media analysis to generate downloadable PDF reports.").classes("text-sm text-gray-400 italic")
            else:
                for det in summary["recent_detections"]:
                    with ui.row().classes("justify-between items-center w-full p-3 border-b border-gray-800"):
                        with ui.row().classes("items-center gap-3"):
                            ui.icon("description", color="cyan", size="md")
                            with ui.column().classes("gap-0"):
                                ui.label(f"Report: {det['file_name']}").classes("text-sm font-bold text-white")
                                ui.label(f"Type: {det['media_type']} • Result: {det['result']}").classes("text-xs text-gray-400")

                        def gen_and_dl(d=det):
                            pdf_path = generate_pdf_report(d, user_name=user["full_name"])
                            ui.notify(f"PDF generated: {os.path.basename(pdf_path)}", type="positive")
                            ui.download(pdf_path)

                        ui.button("Download PDF", on_click=gen_and_dl).props("unelevated size=sm color=cyan-7 icon=download")

        render_disclaimer_card()

@ui.page('/profile')
def page_profile():
    ui.query('body').style(STYLE_BG)
    user = render_dashboard_layout("User Profile")
    if not user: return

    with ui.column().classes("w-full p-8 gap-6 ml-[260px] max-w-[calc(100vw-280px)]"):
        ui.label("User Account Profile").classes("text-2xl font-extrabold text-white")

        with ui.card().style(STYLE_CARD).classes("max-w-lg w-full p-8 gap-4"):
            with ui.row().classes("items-center gap-4"):
                ui.avatar(icon="person", color="cyan-8", text_color="white", size="xl")
                with ui.column().classes("gap-0"):
                    ui.label(user.get("full_name", "User")).classes("text-xl font-bold text-white")
                    ui.label(user.get("email", "")).classes("text-xs text-cyan-400 font-mono")

            ui.separator().classes("bg-gray-700 my-2")
            ui.label("Role: Registered Researcher / Inspector").classes("text-xs text-gray-300 font-semibold")
            ui.label("Authentication Protocol: bcrypt salted hash").classes("text-xs text-gray-300 font-mono")


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title=config.APP_TITLE,
        host=config.APP_HOST,
        port=config.APP_PORT,
        storage_secret=config.SECRET_KEY,
        dark=True,
        reload=False
    )
