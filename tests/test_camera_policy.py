from camera import CameraManager
from config import ALLOW_LOCAL_WEBCAM_FALLBACK


def test_local_webcam_fallback_is_disabled():
    assert ALLOW_LOCAL_WEBCAM_FALLBACK is False


def test_device_candidates_exclude_local_webcam_indices_when_fallback_disabled():
    candidates = CameraManager._device_candidates()
    assert all(not isinstance(candidate, int) for candidate in candidates)
