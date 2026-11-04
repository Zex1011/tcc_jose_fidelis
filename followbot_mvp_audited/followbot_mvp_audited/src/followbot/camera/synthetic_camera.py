from __future__ import annotations

import time

import numpy as np

from ..interfaces import Camera
from ..models import Frame


class SyntheticCamera(Camera):
    """Camera fake for development without Raspberry Pi hardware."""

    def __init__(self, width: int = 640, height: int = 480) -> None:
        self.width = width
        self.height = height
        self._sequence = 0

    def capture(self) -> Frame:
        self._sequence += 1
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        return Frame(image=image, sequence=self._sequence, captured_monotonic_s=time.monotonic())
