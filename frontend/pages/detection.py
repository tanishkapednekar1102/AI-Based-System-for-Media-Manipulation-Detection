import os
from nicegui import ui

try:
    from backend import config
    from backend.detection.image_detector import detect_image
    from backend.detection.video_detector import detect_video
    from backend.detection.audio_detector import detect_audio
    from backend.reports.pdf_report import generate_pdf_report
    from frontend.components.layout import STYLE_BG, STYLE_CARD, render_dashboard_layout, render_disclaimer_card, render_result_badge
except ImportError:
    import config
    from detection.image_detector import detect_image
    from detection.video_detector import detect_video
    from detection.audio_detector import detect_audio
    from reports.pdf_report import generate_pdf_report
    from components.layout import STYLE_BG, STYLE_CARD, render_dashboard_layout, render_disclaimer_card, render_result_badge

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

def register_detection_routes():
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
