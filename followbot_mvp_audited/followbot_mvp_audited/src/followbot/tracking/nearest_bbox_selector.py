from __future__ import annotations

from ..interfaces import TargetSelector
from ..models import Detection, Frame


class NearestBBoxSelector(TargetSelector):
    """Minimal stateful tracker based on bbox-center proximity.

    It intentionally does NOT create a true persistent identity. It only keeps
    the previous selected bounding box and searches for the closest center in
    the next cycle.
    """

    _VALID_INITIAL = {"first", "largest", "center", "confidence"}

    def __init__(
        self,
        initial_strategy: str = "first",
        max_center_distance: float = 0.30,
        max_missed_frames: int = 3,
    ) -> None:
        if initial_strategy not in self._VALID_INITIAL:
            raise ValueError(f"initial_strategy deve ser um de {sorted(self._VALID_INITIAL)}")
        if max_center_distance <= 0:
            raise ValueError("max_center_distance deve ser > 0")
        if max_missed_frames < 0:
            raise ValueError("max_missed_frames deve ser >= 0")

        self.initial_strategy = initial_strategy
        self.max_center_distance = max_center_distance
        self.max_missed_frames = max_missed_frames
        self._previous: Detection | None = None
        self._missed = 0

    def reset(self) -> None:
        self._previous = None
        self._missed = 0

    def _register_miss(self) -> None:
        self._missed += 1
        if self._missed > self.max_missed_frames:
            self.reset()

    def _choose_initial(self, detections: list[Detection], frame: Frame) -> Detection:
        if self.initial_strategy == "first":
            return detections[0]
        if self.initial_strategy == "largest":
            return max(detections, key=lambda d: d.bbox.area)
        if self.initial_strategy == "confidence":
            return max(detections, key=lambda d: d.confidence)

        cx = frame.width / 2.0
        cy = frame.height / 2.0
        return min(
            detections,
            key=lambda d: (d.bbox.cx - cx) ** 2 + (d.bbox.cy - cy) ** 2,
        )

    def select(self, detections: list[Detection], frame: Frame) -> Detection | None:
        if not detections:
            self._register_miss()
            return None

        if self._previous is None:
            selected = self._choose_initial(detections, frame)
            self._previous = selected
            self._missed = 0
            return selected

        selected = min(
            detections,
            key=lambda d: self._previous.bbox.normalized_center_distance(
                d.bbox, frame.width, frame.height
            ),
        )
        distance = self._previous.bbox.normalized_center_distance(
            selected.bbox, frame.width, frame.height
        )

        if distance > self.max_center_distance:
            self._register_miss()
            return None

        self._previous = selected
        self._missed = 0
        return selected
