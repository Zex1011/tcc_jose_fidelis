from __future__ import annotations

from ..interfaces import CommunicationLink
from ..models import CommunicationResult, MotionCommand


class MockCommunicationLink(CommunicationLink):
    def __init__(self) -> None:
        self._sequence = 0

    def send(self, command: MotionCommand) -> CommunicationResult:
        self._sequence += 1
        return CommunicationResult(
            success=True,
            sequence=self._sequence,
            response=f"ACK,{self._sequence}",
            attempts=1,
            latency_ms=0.0,
        )
