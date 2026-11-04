from __future__ import annotations

from pathlib import Path

import numpy as np

from ..interfaces import Detector
from ..models import BoundingBox, Detection, Frame


class UltralyticsPersonDetector(Detector):
    """YOLO detector adapter.

    The rest of the project only receives Detection objects and does not know
    whether the model is PyTorch, ONNX, NCNN, etc. For Raspberry Pi, the initial
    deployment target is an Ultralytics-exported NCNN model directory.
    """

    def __init__(
        self,
        model_path: str,
        imgsz: int = 320,
        confidence: float = 0.35,
        class_name: str = "person",
    ) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics não está instalado. Instale o extra de IA com: pip install -e '.[ai]'"
            ) from exc

        if not model_path:
            raise ValueError("detector.model_path precisa apontar para um modelo YOLO.")

        self._model_path = Path(model_path)
        self._model = YOLO(str(self._model_path), task="detect")
        self._imgsz = imgsz
        self._confidence = confidence
        self._wanted_class_name = class_name
        self._class_id = self._resolve_class_id(class_name)

    def _resolve_class_id(self, class_name: str) -> int:
        names = self._model.names
        if isinstance(names, dict):
            pairs = names.items()
        else:
            pairs = enumerate(names)

        for class_id, name in pairs:
            if str(name).lower() == class_name.lower():
                return int(class_id)

        raise ValueError(
            f"Classe {class_name!r} não encontrada no modelo. Classes disponíveis: {names}"
        )

    def detect(self, frame: Frame) -> list[Detection]:
        # Frame uses RGB; Ultralytics expects BGR for NumPy image inputs.
        bgr_image = np.ascontiguousarray(frame.image[:, :, ::-1])
        results = self._model.predict(
            source=bgr_image,
            imgsz=self._imgsz,
            conf=self._confidence,
            classes=[self._class_id],
            verbose=False,
            device="cpu",
        )
        if not results:
            return []

        result = results[0]
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return []

        def scalar(value) -> float:
            if hasattr(value, "detach"):
                value = value.detach()
            if hasattr(value, "cpu"):
                value = value.cpu()
            if hasattr(value, "item"):
                return float(value.item())
            return float(value)

        def vector(value) -> list[float]:
            if hasattr(value, "detach"):
                value = value.detach()
            if hasattr(value, "cpu"):
                value = value.cpu()
            if hasattr(value, "tolist"):
                return [float(v) for v in value.tolist()]
            return [float(v) for v in value]

        detections: list[Detection] = []
        for box in boxes:
            xyxy = vector(box.xyxy[0])
            confidence = scalar(box.conf[0])
            class_id = int(scalar(box.cls[0]))
            track_id = None
            if getattr(box, "id", None) is not None:
                track_id = int(scalar(box.id[0]))

            detections.append(
                Detection(
                    bbox=BoundingBox(*map(float, xyxy)),
                    confidence=confidence,
                    class_id=class_id,
                    class_name=self._wanted_class_name,
                    track_id=track_id,
                )
            )

        return detections
