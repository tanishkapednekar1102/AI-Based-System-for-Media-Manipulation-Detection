import os
import sys

# Ensure root directory is on Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from frontend.app import run_app

if __name__ in {"__main__", "__mp_main__"}:
    run_app()
