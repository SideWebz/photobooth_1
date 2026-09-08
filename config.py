import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TEST_MODE = False

HOST = "0.0.0.0"
PORT = 8000

# ============================================================
# CAMERA
# ============================================================

CAMERA_DEVICE = "auto"

ALLOW_LOCAL_WEBCAM_FALLBACK = os.getenv(
    "ALLOW_LOCAL_WEBCAM_FALLBACK",
    "1" if sys.platform != "linux" else "0",
).lower() in {"1", "true", "yes", "on"}

CAMERA_DEVICE_TIMEOUT_SECONDS = 2.0


# ============================================================
# PRINTER
# ============================================================

PRINTER_NAME = "DNP-DSRX1"
PRINT_PAGE_SIZE = "w288h432-div2"
PRINT_COLOR_MODEL = "CMYK"
PRINT_IMAGE_TYPE = "Photo"
PRINT_RESOLUTION = "300dpi"
PRINT_LAMINATE = "Glossy"


# ============================================================
# BRAND COLORS
# ============================================================

PRIMARY_BLUE = "#02559F"
LIGHT_BLUE = "#247BBB"
GREEN = "#C9DD03"
WHITE = "#FFFFFF"


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

PHOTOS_DIR = BASE_DIR / "photos"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_FOLDER = BASE_DIR / "templates"
STATIC_FOLDER = BASE_DIR / "static"
PHOTO_CARD_TEMPLATE = BASE_DIR / "PhotoCard.png"

# Alle foto-afmetingen en posities staan hier bij elkaar voor eenvoudige finetuning.
PHOTO_LAYOUT = {
    "width": 530,
    "height": 400,
    "photo1": {"x": 35, "y": 271},
    "photo2": {"x": 35, "y": 700},
    "photo3": {"x": 35, "y": 1129},
    "gap": 29,
}

# Logo staat in de ROOT van het project.
LOGO_CANDIDATES = [
    BASE_DIR / "logo.png",
    BASE_DIR / "logo.jpg",
    BASE_DIR / "logo.jpeg",
    BASE_DIR / "logo.webp",
    BASE_DIR / "logo.svg",
]
