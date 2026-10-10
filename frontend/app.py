import os
import sys
import logging
from nicegui import ui

# Ensure project root is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend import config
from backend.database.connection import init_db
from frontend.pages.public import register_public_routes
from frontend.pages.auth import register_auth_routes
from frontend.pages.dashboard import register_dashboard_routes
from frontend.pages.detection import register_detection_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("frontend.app")

# Initialize MySQL Database
init_db()

# Register UI Page Routes
register_public_routes()
register_auth_routes()
register_dashboard_routes()
register_detection_routes()

def run_app():
    """Launches NiceGUI Web Server."""
    ui.run(
        title=config.APP_TITLE,
        host=config.APP_HOST,
        port=config.APP_PORT,
        storage_secret=config.SECRET_KEY,
        dark=True,
        reload=False
    )

if __name__ in {"__main__", "__mp_main__"}:
    run_app()
