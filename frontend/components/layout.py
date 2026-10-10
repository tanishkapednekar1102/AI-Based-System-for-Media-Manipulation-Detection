import os
import sys
from nicegui import ui, app

try:
    from backend import config
    from backend.database.connection import is_db_connected
except ImportError:
    import config
    from database.connection import is_db_connected

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
