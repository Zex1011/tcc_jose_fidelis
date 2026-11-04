from __future__ import annotations

import argparse
from pathlib import Path

from .camera import DatasetCamera, OpenCVCamera, Picamera2Camera, SyntheticCamera
from .communication import MockCommunicationLink, SerialCommunicationLink
from .config import AppConfig, load_config
from .control import BBoxProportionalController
from .debug import DebugRunManager, VisualDebugRecorder
from .logging_setup import configure_logging
from .orchestrator import Orchestrator
from .tracking import NearestBBoxSelector
from .vision import SyntheticPersonDetector, UltralyticsPersonDetector


def build_orchestrator(config: AppConfig, config_path: str = "") -> Orchestrator:
    if config.camera.backend == "picamera2":
        camera = Picamera2Camera(
            width=config.camera.width,
            height=config.camera.height,
            warmup_s=config.camera.warmup_s,
        )
    elif config.camera.backend == "opencv":
        camera = OpenCVCamera(
            width=config.camera.width,
            height=config.camera.height,
            device_index=config.camera.device_index,
            warmup_s=config.camera.warmup_s,
        )
    elif config.camera.backend == "dataset":
        camera = DatasetCamera(
            dataset_path=config.camera.dataset_path,
            width=config.camera.width,
            height=config.camera.height,
        )
    elif config.camera.backend == "synthetic":
        camera = SyntheticCamera(width=config.camera.width, height=config.camera.height)
    else:
        raise ValueError(f"Camera backend desconhecido: {config.camera.backend}")

    if config.detector.backend == "ultralytics":
        detector = UltralyticsPersonDetector(
            model_path=config.detector.model_path,
            imgsz=config.detector.imgsz,
            confidence=config.detector.confidence,
            class_name=config.detector.class_name,
        )
    elif config.detector.backend == "synthetic":
        detector = SyntheticPersonDetector()
    else:
        raise ValueError(f"Detector backend desconhecido: {config.detector.backend}")

    selector = NearestBBoxSelector(
        initial_strategy=config.tracking.initial_strategy,
        max_center_distance=config.tracking.max_center_distance,
        max_missed_frames=config.tracking.max_missed_frames,
    )

    controller = BBoxProportionalController(
        desired_height_ratio=config.control.desired_height_ratio,
        height_deadband=config.control.height_deadband,
        horizontal_deadband=config.control.horizontal_deadband,
        kp_linear=config.control.kp_linear,
        kp_angular=config.control.kp_angular,
        max_linear=config.control.max_linear,
        max_angular=config.control.max_angular,
        allow_reverse=config.control.allow_reverse,
        forward_slowdown_error=config.control.forward_slowdown_error,
        forward_stop_error=config.control.forward_stop_error,
        angular_sign=config.control.angular_sign,
    )

    if config.communication.backend == "serial":
        communication = SerialCommunicationLink(
            port=config.communication.port,
            baudrate=config.communication.baudrate,
            ack_timeout_s=config.communication.ack_timeout_s,
            write_timeout_s=config.communication.write_timeout_s,
            retries=config.communication.retries,
            startup_delay_s=config.communication.startup_delay_s,
        )
    elif config.communication.backend == "mock":
        communication = MockCommunicationLink()
    else:
        raise ValueError(f"Communication backend desconhecido: {config.communication.backend}")

    logger = configure_logging(config.logging)

    visual_debugger = None
    if config.debug.enabled:
        # Extract profile name from config path for timestamped directory
        profile_name = Path(config_path).stem if config_path else "debug_run"
        debug_run_dir = DebugRunManager.create_run_dir(profile_name)
        
        visual_debugger = VisualDebugRecorder(
            output_dir=str(debug_run_dir),
            save_every_n=config.debug.save_every_n,
            max_images=config.debug.max_images,
        )

    return Orchestrator(
        camera=camera,
        detector=detector,
        selector=selector,
        controller=controller,
        communication=communication,
        logger=logger,
        abort_on_comm_failure=config.system.abort_on_comm_failure,
        visual_debugger=visual_debugger,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FollowBot person-following orchestrator")
    parser.add_argument("--config", default="config.mock.toml")
    parser.add_argument("--max-cycles", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    orchestrator = build_orchestrator(config, config_path=args.config)
    orchestrator.run(max_cycles=args.max_cycles)


if __name__ == "__main__":
    main()
