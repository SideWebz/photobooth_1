import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from config import (
    OUTPUT_DIR,
    PRINT_COLOR_MODEL,
    PRINT_IMAGE_TYPE,
    PRINT_LAMINATE,
    PRINT_PAGE_SIZE,
    PRINT_RESOLUTION,
    PRINTER_NAME,
    TEST_MODE,
)


def print_strip(image_path: str):
    image_file = Path(image_path)

    if TEST_MODE:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        target = OUTPUT_DIR / f"photobooth_test_{timestamp}.jpg"
        shutil.copy2(str(image_file), str(target))
        return {
            "success": True,
            "mode": "test",
            "message": "TEST PRINT KLAAR",
            "output_path": str(target),
        }

    try:
        result = subprocess.run(
            [
                "lp",
                "-d",
                PRINTER_NAME,
                "-o",
                f"PageSize={PRINT_PAGE_SIZE}",
                "-o",
                f"ColorModel={PRINT_COLOR_MODEL}",
                "-o",
                f"StpImageType={PRINT_IMAGE_TYPE}",
                "-o",
                f"Resolution={PRINT_RESOLUTION}",
                "-o",
                f"StpLaminate={PRINT_LAMINATE}",
                str(image_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Printer unavailable",
            "message": "PRINTER NIET BESCHIKBAAR",
        }

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        return {
            "success": False,
            "error": stderr or "Printer unavailable",
            "message": "PRINTER NIET BESCHIKBAAR",
        }

    return {
        "success": True,
        "mode": "production",
        "message": "JE STRIP WORDT GEPRINT",
    }
