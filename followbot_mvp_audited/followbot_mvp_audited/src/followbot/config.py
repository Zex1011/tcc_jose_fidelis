from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True, slots=True)
class CameraConfig:
    backend: str = "picamera2"
    width: int = 640
    height: int = 480
    device_index: int = 0
    dataset_path: str = ""
    warmup_s: float = 1.0


@dataclass(frozen=True, slots=True)
class DetectorConfig:
    backend: str = "ultralytics"
    model_path: str = "models/yolo26n_ncnn_model"
    imgsz: int = 320
    confidence: float = 0.35
    class_name: str = "person"


@dataclass(frozen=True, slots=True)
class TrackingConfig:
    initial_strategy: str = "first"
    max_center_distance: float = 0.30
    max_missed_frames: int = 3


@dataclass(frozen=True, slots=True)
class ControlConfig:
    desired_height_ratio: float = 0.55
    height_deadband: float = 0.05
    horizontal_deadband: float = 0.06
    kp_linear: float = 1.0
    kp_angular: float = 1.3
    max_linear: float = 0.40
    max_angular: float = 1.20
    allow_reverse: bool = False
    forward_slowdown_error: float = 0.35
    forward_stop_error: float = 0.75
    angular_sign: float = 1.0


@dataclass(frozen=True, slots=True)
class CommunicationConfig:
    backend: str = "serial"
    port: str = "/dev/ttyACM0"
    baudrate: int = 115200
    ack_timeout_s: float = 0.25
    write_timeout_s: float = 0.25
    retries: int = 2
    startup_delay_s: float = 1.5


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/followbot.log"
    max_bytes: int = 2_000_000
    backup_count: int = 3
    console: bool = True


@dataclass(frozen=True, slots=True)
class SystemConfig:
    abort_on_comm_failure: bool = True


@dataclass(frozen=True, slots=True)
class DebugConfig:
    enabled: bool = False
    output_dir: str = "logs/visual_debug"
    save_every_n: int = 1
    max_images: int = 200


@dataclass(frozen=True, slots=True)
class AppConfig:
    camera: CameraConfig
    detector: DetectorConfig
    tracking: TrackingConfig
    control: ControlConfig
    communication: CommunicationConfig
    logging: LoggingConfig
    system: SystemConfig
    debug: DebugConfig


def load_config(path: str | Path) -> AppConfig:
    path = Path(path)
    with path.open("rb") as file:
        raw = tomllib.load(file)

    return AppConfig(
        camera=CameraConfig(**raw.get("camera", {})),
        detector=DetectorConfig(**raw.get("detector", {})),
        tracking=TrackingConfig(**raw.get("tracking", {})),
        control=ControlConfig(**raw.get("control", {})),
        communication=CommunicationConfig(**raw.get("communication", {})),
        logging=LoggingConfig(**raw.get("logging", {})),
        system=SystemConfig(**raw.get("system", {})),
        debug=DebugConfig(**raw.get("debug", {})),
    )
