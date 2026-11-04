from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..models import CommunicationResult, Detection, Frame, MotionCommand


class VisualDebugRecorder:
    """Saves annotated frames and per-cycle metadata for visual diagnostics."""

    def __init__(
        self,
        output_dir: str,
        save_every_n: int = 1,
        max_images: int = 200,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.save_every_n = max(1, int(save_every_n))
        self.max_images = max(1, int(max_images))
        self._saved = 0

    @staticmethod
    def _to_uint8_rgb(image: np.ndarray) -> np.ndarray:
        arr = np.asarray(image)
        if arr.ndim == 2:
            arr = np.stack([arr, arr, arr], axis=2)
        if arr.ndim != 3:
            raise ValueError(f"Formato de imagem inesperado: shape={arr.shape}")
        if arr.shape[2] >= 4:
            arr = arr[:, :, :3]
        if arr.dtype != np.uint8:
            arr = np.clip(arr, 0, 255).astype(np.uint8)
        return arr.copy()

    @staticmethod
    def _clip(value: float, lower: int, upper: int) -> int:
        return int(max(lower, min(int(round(value)), upper)))

    @staticmethod
    def _draw_rect(img: np.ndarray, det: Detection, color: tuple[int, int, int], thickness: int = 2) -> None:
        h, w = img.shape[0], img.shape[1]
        x1 = VisualDebugRecorder._clip(det.bbox.x1, 0, w - 1)
        y1 = VisualDebugRecorder._clip(det.bbox.y1, 0, h - 1)
        x2 = VisualDebugRecorder._clip(det.bbox.x2, 0, w - 1)
        y2 = VisualDebugRecorder._clip(det.bbox.y2, 0, h - 1)

        if x2 <= x1 or y2 <= y1:
            return

        for t in range(thickness):
            yt = min(y1 + t, h - 1)
            yb = max(y2 - t, 0)
            xl = min(x1 + t, w - 1)
            xr = max(x2 - t, 0)
            img[yt, x1 : x2 + 1] = color
            img[yb, x1 : x2 + 1] = color
            img[y1 : y2 + 1, xl] = color
            img[y1 : y2 + 1, xr] = color

    @staticmethod
    def _draw_center_crosshair(img: np.ndarray, color: tuple[int, int, int]) -> None:
        h, w = img.shape[0], img.shape[1]
        cx, cy = w // 2, h // 2
        x1 = max(0, cx - 12)
        x2 = min(w - 1, cx + 12)
        y1 = max(0, cy - 12)
        y2 = min(h - 1, cy + 12)
        img[cy, x1 : x2 + 1] = color
        img[y1 : y2 + 1, cx] = color

    @staticmethod
    def _write_ppm(path: Path, image_rgb: np.ndarray) -> None:
        h, w = image_rgb.shape[0], image_rgb.shape[1]
        header = f"P6\n{w} {h}\n255\n".encode("ascii")
        with path.open("wb") as f:
            f.write(header)
            f.write(image_rgb.tobytes(order="C"))

    def record(
        self,
        cycle: int,
        frame: Frame,
        detections: list[Detection],
        target: Detection | None,
        command: MotionCommand,
        communication: CommunicationResult,
        timings_ms: dict[str, float],
    ) -> None:
        if cycle % self.save_every_n != 0:
            return
        if self._saved >= self.max_images:
            return

        image = self._to_uint8_rgb(frame.image)
        self._draw_center_crosshair(image, color=(64, 128, 255))

        for det in detections:
            self._draw_rect(image, det, color=(48, 220, 96), thickness=2)

        if target is not None:
            self._draw_rect(image, target, color=(255, 64, 64), thickness=3)

        stem = f"cycle_{cycle:06d}"
        self._write_ppm(self.output_dir / f"{stem}.ppm", image)

        metadata = {
            "cycle": cycle,
            "frame": {
                "sequence": frame.sequence,
                "width": frame.width,
                "height": frame.height,
            },
            "detections": [d.as_dict() for d in detections],
            "target": target.as_dict() if target else None,
            "command": command.as_dict(),
            "communication": communication.as_dict(),
            "timings_ms": timings_ms,
        }
        with (self.output_dir / f"{stem}.json").open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        self._saved += 1

    def close(self) -> None:
        pass
