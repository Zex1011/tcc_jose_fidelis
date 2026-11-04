from __future__ import annotations

import time

from ..interfaces import CommunicationLink
from ..models import CommunicationResult, MotionCommand


class SerialCommunicationLink(CommunicationLink):
    """Line-based USB/serial protocol with sequence-numbered ACKs.

    Pi -> ESP: CMD,<seq>,<linear>,<angular>\n
    ESP -> Pi: ACK,<seq>\n
    ESP -> Pi: ERR,<seq>,<reason>\n   (optional)
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        ack_timeout_s: float = 0.25,
        write_timeout_s: float = 0.25,
        retries: int = 2,
        startup_delay_s: float = 1.5,
    ) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("pyserial não está instalado.") from exc

        self._serial_module = serial
        self._ack_timeout_s = ack_timeout_s
        self._retries = retries
        self._sequence = 0
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=ack_timeout_s,
            write_timeout=write_timeout_s,
        )
        if startup_delay_s > 0:
            time.sleep(startup_delay_s)
        self._serial.reset_input_buffer()

    def _next_sequence(self) -> int:
        self._sequence = (self._sequence + 1) % 2_147_483_647
        return self._sequence

    def send(self, command: MotionCommand) -> CommunicationResult:
        sequence = self._next_sequence()
        payload = f"CMD,{sequence},{command.linear:.5f},{command.angular:.5f}\n".encode("ascii")
        expected_ack = f"ACK,{sequence}"
        started = time.perf_counter()
        last_response: str | None = None
        last_error: str | None = None

        for attempt in range(1, self._retries + 2):
            try:
                self._serial.write(payload)
                self._serial.flush()
                deadline = time.perf_counter() + self._ack_timeout_s

                while time.perf_counter() < deadline:
                    raw = self._serial.readline()
                    if not raw:
                        break
                    response = raw.decode("utf-8", errors="replace").strip()
                    last_response = response
                    if response == expected_ack:
                        return CommunicationResult(
                            success=True,
                            sequence=sequence,
                            response=response,
                            attempts=attempt,
                            latency_ms=(time.perf_counter() - started) * 1000.0,
                        )
                    if response.startswith(f"ERR,{sequence},"):
                        last_error = response
                        break

            except (self._serial_module.SerialException, self._serial_module.SerialTimeoutException) as exc:
                last_error = str(exc)

        return CommunicationResult(
            success=False,
            sequence=sequence,
            response=last_response,
            attempts=self._retries + 1,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            error=last_error or "ACK timeout",
        )

    def close(self) -> None:
        if self._serial.is_open:
            self._serial.close()
