import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template

from camera import CameraManager
from config import OUTPUT_DIR, PHOTOS_DIR, TEST_MODE, get_photo_card_template
from printer import print_strip
from strip import create_photo_card

app = Flask(__name__)

camera = CameraManager()
current_session = {"folder": None, "photos": []}


def create_session() -> dict:
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    folder = PHOTOS_DIR / session_id
    folder.mkdir(parents=True, exist_ok=True)
    current_session["folder"] = str(folder)
    current_session["photos"] = []
    return current_session 


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(camera.video_feed(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/status")
def api_status():
    return jsonify(
        {
            "success": camera.is_available(),
            "camera_available": camera.is_available(),
            "camera_path": camera.camera_path,
            "error": camera.last_error,
            "message": camera.last_error or "Camera ready",
        }
    )


@app.route("/api/start", methods=["POST"])
def api_start():
    if not camera.is_available():
        return jsonify(
            {
                "success": False,
                "error": camera.last_error or "Camera not available",
                "message": "Camera niet gevonden. Gebruik alleen een GoPro/V4L2 USB-camera. Geen laptopwebcam fallback actief.",
            }
        ), 503

    create_session()
    return jsonify({"success": True, "session_id": Path(current_session["folder"]).name})


@app.route("/api/capture", methods=["POST"])
def api_capture():
    if not camera.is_available():
        return jsonify(
            {
                "success": False,
                "error": camera.last_error or "Camera not available",
                "message": "Camera niet gevonden. Gebruik alleen een GoPro/V4L2 USB-camera. Geen laptopwebcam fallback actief.",
            }
        ), 503

    folder = current_session.get("folder")
    if not folder:
        create_session()
        folder = current_session.get("folder")

    photo_index = len(current_session["photos"]) + 1
    output_path = Path(folder) / f"photo{photo_index}.jpg"

    try:
        camera.capture_frame(str(output_path))
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc), "message": str(exc)}), 500

    current_session["photos"].append(str(output_path))
    return jsonify({"success": True, "photo_index": photo_index, "image_path": str(output_path)})


@app.route("/api/finish", methods=["POST"])
def api_finish():
    photos = current_session.get("photos") or []
    if len(photos) != 3:
        return jsonify({"success": False, "error": "Need 3 photos to create the strip"}), 400

    session_folder = Path(current_session["folder"]) if current_session.get("folder") else None
    session_id = session_folder.name if session_folder else datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    strip_path = OUTPUT_DIR / f"strip_{session_id}.jpg"

    try:
        create_photo_card(photos, str(strip_path), template_path=get_photo_card_template())
    except Exception as exc:
        return jsonify({"success": False, "error": f"Strip generation failed: {exc}"}), 500

    print_result = print_strip(str(strip_path))

    if session_folder and session_folder.exists():
        shutil.rmtree(session_folder, ignore_errors=True)

    current_session["folder"] = None
    current_session["photos"] = []

    response = {
        "success": print_result["success"],
        "mode": print_result.get("mode", "test" if TEST_MODE else "production"),
        "strip_path": str(strip_path),
        "message": print_result.get("message", "TEST PRINT KLAAR"),
    }

    if not print_result["success"]:
        response["error"] = print_result.get("error", "Printer unavailable")

    return jsonify(response)


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"success": False, "error": "Not found"}), 404


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=8000, debug=False)
