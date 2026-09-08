import glob
import threading
import time
from typing import Iterator, Optional, Union

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import ALLOW_LOCAL_WEBCAM_FALLBACK, CAMERA_DEVICE, CAMERA_DEVICE_TIMEOUT_SECONDS


class CameraManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.camera = None
        self.camera_index = None
        self.camera_path = None
        self.last_error = "Camera not available"
        self._open_camera()
        self._retry_thread = threading.Thread(target=self._retry_until_available, daemon=True)
        self._retry_thread.start()

    def _retry_until_available(self) -> None:
        while True:
            if not self.is_available():
                self._open_camera()
            time.sleep(10)

    def reset_camera(self) -> None:
        if self.camera is not None:
            try:
                self.camera.release()
            except Exception:
                pass
        self.camera = None
        self.camera_index = None
        self.camera_path = None
        self.last_error = "Camera not available"
        self._open_camera()

    @staticmethod
    def _device_candidates():
        candidates = []

        if CAMERA_DEVICE != "auto":
            if isinstance(CAMERA_DEVICE, int):
                candidates.append(CAMERA_DEVICE)
            elif str(CAMERA_DEVICE).strip():
                candidates.append(str(CAMERA_DEVICE).strip())
            return candidates

        for device in sorted(glob.glob("/dev/video*")):
            candidates.append(device)

        if ALLOW_LOCAL_WEBCAM_FALLBACK:
            for index in range(0, 12):
                candidates.append(index)

        return candidates

    def _probe_device(self, device: Union[str, int]) -> bool:
        try:
            cap = cv2.VideoCapture(device)
        except Exception:
            return False

        if cap is None or not cap.isOpened():
            if cap is not None:
                cap.release()
            return False

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        start = time.time()
        while time.time() - start < CAMERA_DEVICE_TIMEOUT_SECONDS:
            ret, frame = cap.read()
            if ret and frame is not None:
                cap.release()
                return True
            time.sleep(0.05)

        cap.release()
        return False

    def _open_camera(self) -> bool:
        if self.camera is not None:
            try:
                self.camera.release()
            except Exception:
                pass
            self.camera = None

        for candidate in self._device_candidates():
            try:
                cap = cv2.VideoCapture(candidate)
            except Exception:
                continue

            if cap is None or not cap.isOpened():
                if cap is not None:
                    cap.release()
                continue

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

            start = time.time()
            while time.time() - start < CAMERA_DEVICE_TIMEOUT_SECONDS:
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.camera = cap
                    self.camera_index = candidate if isinstance(candidate, int) else None
                    self.camera_path = str(candidate) if not isinstance(candidate, int) else None
                    self.last_error = ""
                    return True
                time.sleep(0.05)

            cap.release()

        if ALLOW_LOCAL_WEBCAM_FALLBACK:
            self.last_error = "Camera niet gevonden. Geen GoPro/V4L2 USB-camera gevonden; local fallback is actief."
        else:
            self.last_error = "Camera niet gevonden. Gebruik alleen een GoPro/V4L2 USB-camera. Geen laptopwebcam fallback actief."
        return False

    def is_available(self) -> bool:
        return self.camera is not None and self.camera.isOpened()

    def read_frame(self) -> Optional[np.ndarray]:
        if not self.is_available():
            return None

        with self.lock:
            ret, frame = self.camera.read()

        if not ret or frame is None:
            self.last_error = "Camera frame read failed"
            self.reset_camera()
            return None

        return frame

    def capture_frame(self, output_path: str) -> str:
        frame = self.read_frame()
        if frame is None:
            raise RuntimeError(self.last_error or "Camera not available")

        success = cv2.imwrite(output_path, frame)
        if not success:
            raise RuntimeError("Could not save image from camera")

        return output_path

    def _placeholder_image(self, width: int = 1280, height: int = 720) -> np.ndarray:
        image = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        draw.rectangle((40, 40, width - 40, height - 40), outline=(2, 85, 159), width=6)
        draw.rounded_rectangle(
            (120, 180, width - 120, height - 180),
            radius=30,
            outline=(2, 85, 159),
            width=4,
            fill=(245, 248, 251),
        )

        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 56)
            small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except OSError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        message = "CAMERA NIET GEVONDEN"
        sub_message = "Controleer of de GoPro via USB-C is aangesloten."

        bbox = draw.textbbox((0, 0), message, font=font)
        x = (width - (bbox[2] - bbox[0])) / 2
        y = (height - (bbox[3] - bbox[1])) / 2 - 30
        draw.text((x, y), message, font=font, fill=(2, 85, 159))

        sub_bbox = draw.textbbox((0, 0), sub_message, font=small_font)
        sub_x = (width - (sub_bbox[2] - sub_bbox[0])) / 2
        sub_y = y + 90
        draw.text((sub_x, sub_y), sub_message, font=small_font, fill=(36, 54, 68))

        return np.array(image)

    def video_feed(self) -> Iterator[bytes]:
        while True:
            if self.is_available():
                frame = self.read_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue
            else:
                frame = self._placeholder_image()

            encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not encoded:
                time.sleep(0.05)
                continue

            frame_bytes = buffer.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame_bytes
                + b"\r\n"
            )
            time.sleep(0.033)

    def release(self) -> None:
        if self.camera is not None:
            self.camera.release()
            self.camera = None
            self.camera_path = None
            self.camera_index = None
