from __future__ import annotations

import time
from pathlib import Path

from ..interfaces import Camera
from ..models import Frame


class DatasetCamera(Camera):
    """Read images from a folder in alphabetical order.
    
    Useful for deterministic benchmarking of detection/tracking
    with real-world images without camera hardware.
    """

    def __init__(self, dataset_path: str, width: int = 640, height: int = 480) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError(
                "OpenCV não está disponível. Instale o extra webcam para ler o dataset."
            ) from exc
        self._cv2 = cv2
        self.width = width
        self.height = height
        self.dataset_path = Path(dataset_path)
        
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset path not found: {self.dataset_path}")
        
        # Find all image files
        self.image_files = sorted([
            f for f in self.dataset_path.iterdir()
            if f.suffix.lower() in {'.png', '.jpg', '.jpeg'}
        ])
        
        if not self.image_files:
            raise FileNotFoundError(f"No images found in {self.dataset_path}")
        
        self._current_index = 0
        self._sequence = 0

    def capture(self) -> Frame:
        """Read next image from dataset, recycling when reaching end."""
        self._sequence += 1
        
        # Wrap around at end of dataset
        if self._current_index >= len(self.image_files):
            self._current_index = 0
        
        image_path = self.image_files[self._current_index]
        self._current_index += 1
        
        # Read image in BGR (OpenCV default)
        image = self._cv2.imread(str(image_path))
        if image is None:
            raise IOError(f"Failed to read image: {image_path}")
        
        # Resize to target dimensions
        if image.shape[:2] != (self.height, self.width):
            image = self._cv2.resize(image, (self.width, self.height), interpolation=self._cv2.INTER_LINEAR)
        
        # Convert BGR to RGB for consistency with other backends
        image = self._cv2.cvtColor(image, self._cv2.COLOR_BGR2RGB)
        
        return Frame(
            image=image,
            sequence=self._sequence,
            captured_monotonic_s=time.monotonic()
        )

    def close(self) -> None:
        """Cleanup (no resources to release for dataset)."""
        pass
