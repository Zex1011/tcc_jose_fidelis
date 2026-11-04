from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Any

import numpy as np


@dataclass(slots=True)
class Frame:
    """Camera image in RGB channel order, with uint8 dtype and HWC shape."""

    image: np.ndarray
    sequence: int
    captured_monotonic_s: float

    @property
    def height(self) -> int:
        return int(self.image.shape[0])

    @property
    def width(self) -> int:
        return int(self.image.shape[1])


@dataclass(frozen=True, slots=True)
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2.0

    def normalized_center_distance(self, other: "BoundingBox", frame_width: int, frame_height: int) -> float:
        diagonal = hypot(frame_width, frame_height)
        if diagonal <= 0:
            return float("inf")
        return hypot(self.cx - other.cx, self.cy - other.cy) / diagonal

    def as_dict(self) -> dict[str, float]:
        return {
            "x1": round(self.x1, 3),
            "y1": round(self.y1, 3),
            "x2": round(self.x2, 3),
            "y2": round(self.y2, 3),
        }


@dataclass(frozen=True, slots=True)
class Detection:
    bbox: BoundingBox
    confidence: float
    class_id: int
    class_name: str
    track_id: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "bbox": self.bbox.as_dict(),
            "confidence": round(float(self.confidence), 4),
            "class_id": int(self.class_id),
            "class_name": self.class_name,
            "track_id": self.track_id,
        }


@dataclass(frozen=True, slots=True)
class MotionCommand:
    linear: float
    angular: float

    @classmethod
    def stop(cls) -> "MotionCommand":
        return cls(0.0, 0.0)

    def as_dict(self) -> dict[str, float]:
        return {
            "linear": round(float(self.linear), 5),
            "angular": round(float(self.angular), 5),
        }


@dataclass(frozen=True, slots=True)
class CommunicationResult:
    success: bool
    sequence: int
    response: str | None
    attempts: int
    latency_ms: float
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "sequence": self.sequence,
            "response": self.response,
            "attempts": self.attempts,
            "latency_ms": round(self.latency_ms, 3),
            "error": self.error,
        }
