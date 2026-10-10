import os
from datetime import datetime
from nicegui import ui

try:
    from backend.database.detections import get_user_detections, get_analytics_summary
    from backend.reports.pdf_report import generate_pdf_report
    from frontend.components.layout import STYLE_BG, STYLE_CARD, render_dashboard_layout, render_disclaimer_card
except ImportError:
    from database.detections import get_user_detections, get_analytics_summary
    from reports.pdf_report import generate_pdf_report
    from components.layout import STYLE_BG, STYLE_CARD, render_dashboard_layout, render_disclaimer_card

def register_dashboard_routes():
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
