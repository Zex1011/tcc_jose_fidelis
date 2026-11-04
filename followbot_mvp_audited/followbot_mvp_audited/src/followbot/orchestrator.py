from __future__ import annotations

import logging
import time
from typing import Any

from .interfaces import Camera, CommunicationLink, Controller, Detector, TargetSelector
from .models import MotionCommand


class Orchestrator:
    """Sequential, synchronous coordinator for the entire MVP pipeline."""

    def __init__(
        self,
        camera: Camera,
        detector: Detector,
        selector: TargetSelector,
        controller: Controller,
        communication: CommunicationLink,
        logger: logging.Logger,
        abort_on_comm_failure: bool = True,
        visual_debugger: Any | None = None,
    ) -> None:
        self.camera = camera
        self.detector = detector
        self.selector = selector
        self.controller = controller
        self.communication = communication
        self.logger = logger
        self.abort_on_comm_failure = abort_on_comm_failure
        self.visual_debugger = visual_debugger
        self._cycle = 0

    @staticmethod
    def _ms(start: float) -> float:
        return (time.perf_counter() - start) * 1000.0

    def _send_stop_best_effort(self, reason: str) -> None:
        try:
            result = self.communication.send(MotionCommand.stop())
            self.logger.warning(
                "STOP de segurança enviado",
                extra={"data": {"reason": reason, "communication": result.as_dict()}},
            )
        except Exception:
            self.logger.exception("Falha ao tentar enviar STOP de segurança")

    def run(self, max_cycles: int | None = None) -> None:
        self.logger.info("Orquestrador iniciado")
        self._send_stop_best_effort("startup")

        try:
            while max_cycles is None or self._cycle < max_cycles:
                self._cycle += 1
                cycle_started = time.perf_counter()

                t = time.perf_counter()
                frame = self.camera.capture()
                capture_ms = self._ms(t)

                t = time.perf_counter()
                detections = self.detector.detect(frame)
                inference_ms = self._ms(t)

                t = time.perf_counter()
                target = self.selector.select(detections, frame)
                tracking_ms = self._ms(t)

                t = time.perf_counter()
                command = (
                    self.controller.compute(target, frame)
                    if target is not None
                    else MotionCommand.stop()
                )
                control_ms = self._ms(t)

                t = time.perf_counter()
                comm_result = self.communication.send(command)
                communication_ms = self._ms(t)

                data = {
                    "cycle": self._cycle,
                    "frame": {
                        "sequence": frame.sequence,
                        "width": frame.width,
                        "height": frame.height,
                    },
                    "detections": [d.as_dict() for d in detections],
                    "target": target.as_dict() if target else None,
                    "command": command.as_dict(),
                    "communication": comm_result.as_dict(),
                    "timings_ms": {
                        "capture": round(capture_ms, 3),
                        "inference": round(inference_ms, 3),
                        "tracking": round(tracking_ms, 3),
                        "control": round(control_ms, 3),
                        "communication": round(communication_ms, 3),
                        "cycle_total": round(self._ms(cycle_started), 3),
                    },
                }
                self.logger.info(
                    "cycle=%d det=%d target=%s v=%.3f w=%.3f ack=%s total=%.1fms",
                    self._cycle,
                    len(detections),
                    "yes" if target else "no",
                    command.linear,
                    command.angular,
                    "yes" if comm_result.success else "no",
                    data["timings_ms"]["cycle_total"],
                    extra={"data": data},
                )

                if self.visual_debugger is not None:
                    try:
                        self.visual_debugger.record(
                            cycle=self._cycle,
                            frame=frame,
                            detections=detections,
                            target=target,
                            command=command,
                            communication=comm_result,
                            timings_ms=data["timings_ms"],
                        )
                    except Exception:
                        self.logger.exception("Falha no visual_debugger.record")

                if not comm_result.success:
                    self.logger.error("Comunicação sem ACK", extra={"data": data})
                    if self.abort_on_comm_failure:
                        raise RuntimeError(f"Falha de comunicação: {comm_result.error}")

        except KeyboardInterrupt:
            self.logger.info("Interrompido pelo usuário")
        except Exception:
            self.logger.exception("Falha fatal no loop")
            raise
        finally:
            self._send_stop_best_effort("shutdown")
            self.close()
            self.logger.info("Orquestrador finalizado")

    def close(self) -> None:
        for component_name, component in (
            ("detector", self.detector),
            ("camera", self.camera),
            ("communication", self.communication),
            ("visual_debugger", self.visual_debugger),
        ):
            if component is None:
                continue
            try:
                component.close()
            except Exception:
                self.logger.exception("Falha ao fechar %s", component_name)
