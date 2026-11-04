from __future__ import annotations

import time

from ..interfaces import Camera
from ..models import Frame


class OpenCVCamera(Camera):
    """USB/UVC webcam adapter based on OpenCV VideoCapture."""

    def __init__(
        self,
        width: int,
        height: int,
        device_index: int = 0,
        warmup_s: float = 0.5,
    ) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError(
                "OpenCV não está disponível. Instale com: pip install -e '.[webcam]'"
            ) from exc

        self._cv2 = cv2
        self._capture = cv2.VideoCapture(device_index)
        if not self._capture.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir webcam no índice {device_index}. "
                "Confirme se /dev/video* existe e se o índice está correto."
            )

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
        self._sequence = 0

        if warmup_s > 0:
            deadline = time.monotonic() + warmup_s
            while time.monotonic() < deadline:
                self._capture.read()

    def capture(self) -> Frame:
        ok, image_bgr = self._capture.read()
        if not ok or image_bgr is None:
            raise RuntimeError("Falha ao capturar frame da webcam.")

        image_rgb = self._cv2.cvtColor(image_bgr, self._cv2.COLOR_BGR2RGB)
        self._sequence += 1
        return Frame(
            image=image_rgb,
            sequence=self._sequence,
            captured_monotonic_s=time.monotonic(),
        )

    def close(self) -> None:
        if self._capture.isOpened():
            self._capture.release()