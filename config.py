"""Central configuration for AXEL.

Every threshold, path and app setting lives here so it can be tuned in one
place. Environment variables override the defaults where noted.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _cache_dir():
    """Writable cache location (next to the exe when frozen by PyInstaller)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")


CACHE_DIR = os.environ.get("AXEL_CACHE_DIR", _cache_dir())
CACHE_DB = os.path.join(CACHE_DIR, "axel.db")

# ---------------------------------------------------------------------------
# Risk / recommendation thresholds
# ---------------------------------------------------------------------------

RISK_GPA_THRESHOLD = 5.0        # GPA below this -> at risk
RISK_ATTENDANCE_THRESHOLD = 55.0  # attendance % below this -> at risk
GPA_LOW_THRESHOLD = 40.0        # per-subject % below this -> professor suggested

# ---------------------------------------------------------------------------
# Modelling settings
# ---------------------------------------------------------------------------

RANDOM_STATE = 42
CV_FOLDS = 5                    # K-fold cross-validation splits
KMEANS_MIN_K = 2                # silhouette search range for study-group clusters
KMEANS_MAX_K = 6
MODEL_CANDIDATES = ("linear", "ridge", "random_forest")

# ---------------------------------------------------------------------------
# App settings
# ---------------------------------------------------------------------------

DEFAULT_HOST = "127.0.0.1"
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
DASH_PORT = int(os.environ.get("DASH_PORT", "8050"))
STREAMLIT_PORT = int(os.environ.get("STREAMLIT_PORT", "8501"))

DEBUG = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"} or \
    os.environ.get("DASH_DEBUG", "").lower() in {"1", "true", "yes"}

# Simple shared password gate for the web apps.
# Override in production with the AXEL_PASSWORD environment variable.
AUTH_PASSWORD = os.environ.get("AXEL_PASSWORD", "axel123")
