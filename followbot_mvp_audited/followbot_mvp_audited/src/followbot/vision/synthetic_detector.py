from __future__ import annotations

import math

from ..interfaces import Detector
from ..models import BoundingBox, Detection, Frame


class SyntheticPersonDetector(Detector):
    """Produces one moving fake person to exercise the complete pipeline."""

    def __init__(self) -> None:
        self._cycle = 0

    def detect(self, frame: Frame) -> list[Detection]:
        self._cycle += 1
        t = self._cycle / 6.0

        cx = frame.width * (0.5 + 0.30 * math.sin(t))
        height = frame.height * (0.36 + 0.16 * (0.5 + 0.5 * math.sin(t / 2.0)))
        width = height * 0.42
        cy = frame.height * 0.52

        bbox = BoundingBox(
            x1=max(0.0, cx - width / 2.0),
            y1=max(0.0, cy - height / 2.0),
            x2=min(float(frame.width), cx + width / 2.0),
            y2=min(float(frame.height), cy + height / 2.0),
        )
        return [Detection(bbox=bbox, confidence=0.95, class_id=0, class_name="person")]
