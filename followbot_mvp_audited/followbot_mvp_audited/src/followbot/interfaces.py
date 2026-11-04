from __future__ import annotations

from abc import ABC, abstractmethod

from .models import CommunicationResult, Detection, Frame, MotionCommand


class Camera(ABC):
    @abstractmethod
    def capture(self) -> Frame:
        """Return one current frame when requested."""

    def close(self) -> None:
        pass


class Detector(ABC):
    @abstractmethod
    def detect(self, frame: Frame) -> list[Detection]:
        """Return detections of interest for one frame."""

    def close(self) -> None:
        pass


class TargetSelector(ABC):
    @abstractmethod
    def select(self, detections: list[Detection], frame: Frame) -> Detection | None:
        """Select the target that should be followed in this cycle."""

    @abstractmethod
    def reset(self) -> None:
        """Forget tracking state."""


class Controller(ABC):
    @abstractmethod
    def compute(self, target: Detection, frame: Frame) -> MotionCommand:
        """Convert a target bounding box into a motion command."""


class CommunicationLink(ABC):
    @abstractmethod
    def send(self, command: MotionCommand) -> CommunicationResult:
        """Send a motion command and return acknowledgement information."""

    def close(self) -> None:
        pass
