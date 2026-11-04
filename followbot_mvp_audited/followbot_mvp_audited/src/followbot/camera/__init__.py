"""Load camera adapters only when requested, including for module CLI use."""

from importlib import import_module

_MODULES = {
    "DatasetCamera": "dataset_camera",
    "OpenCVCamera": "opencv_camera",
    "Picamera2Camera": "picamera2_camera",
    "SyntheticCamera": "synthetic_camera",
}


def __getattr__(name: str):
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    adapter = getattr(import_module(f".{_MODULES[name]}", __name__), name)
    globals()[name] = adapter
    return adapter

__all__ = ["DatasetCamera", "OpenCVCamera", "Picamera2Camera", "SyntheticCamera"]
