import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
