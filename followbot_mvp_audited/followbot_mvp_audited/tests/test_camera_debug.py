from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from followbot.camera.picamera2_camera import Picamera2Camera, main


class CameraDebugTests(unittest.TestCase):
    def test_picamera_configuration_and_rgb_frame(self):
        device = MagicMock()
        device.capture_array.return_value = np.array([[[255, 0, 17]]], dtype=np.uint8)
        module = SimpleNamespace(Picamera2=MagicMock(return_value=device))
        with patch.dict(sys.modules, {"picamera2": module}):
            camera = Picamera2Camera(640, 480, warmup_s=0)
            config = device.create_preview_configuration.call_args.kwargs
            self.assertEqual(config["main"]["format"], "BGR888")
            self.assertFalse(config["queue"])
            self.assertEqual(camera.capture().image[0, 0].tolist(), [255, 0, 17])
            camera.close()
            camera.close()
        device.stop.assert_called_once()
        device.close.assert_called_once()

    def test_initialization_failure_releases_camera(self):
        device = MagicMock()
        device.configure.side_effect = RuntimeError("sensor unavailable")
        with patch.dict(sys.modules, {"picamera2": SimpleNamespace(Picamera2=lambda: device)}):
            with self.assertRaisesRegex(RuntimeError, "sensor unavailable"):
                Picamera2Camera(640, 480, warmup_s=0)
        device.close.assert_called_once()

    def test_cli_saves_rgb_png_and_releases_camera(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow required for PNG round-trip")
        device = MagicMock()
        pixels = np.array([[[255, 0, 17], [0, 25, 255]]], dtype=np.uint8)
        device.capture_array.return_value = pixels
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture.png"
            with patch.dict(sys.modules, {"picamera2": SimpleNamespace(Picamera2=lambda: device)}):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--output", str(output), "--warmup", "0"]), 0)
            with Image.open(output) as saved:
                np.testing.assert_array_equal(np.asarray(saved), pixels)
        device.stop.assert_called_once()
        device.close.assert_called_once()

    def test_capture_failure_returns_error_and_releases_camera(self):
        device = MagicMock()
        device.capture_array.side_effect = RuntimeError("capture failed")
        image_module = SimpleNamespace(fromarray=MagicMock())
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(sys.modules, {
                "picamera2": SimpleNamespace(Picamera2=lambda: device),
                "PIL": SimpleNamespace(Image=image_module),
            }):
                with redirect_stderr(io.StringIO()) as errors:
                    result = main(["--output", str(Path(directory) / "capture.png"), "--warmup", "0"])
            self.assertEqual(result, 1)
            self.assertIn("capture failed", errors.getvalue())
            self.assertFalse((Path(directory) / "capture.png").exists())
        device.close.assert_called_once()

    def test_mock_and_camera_help_do_not_import_optional_backends(self):
        # A fresh interpreter catches accidental package-level imports even if
        # other tests have already imported the real cv2/PIL libraries.
        script = """
import runpy
import sys
for name in ('cv2', 'picamera2', 'ultralytics', 'PIL'):
    sys.modules[name] = None
sys.argv = ['picamera2_camera', '--help']
try:
    runpy.run_module('followbot.camera.picamera2_camera', run_name='__main__')
except SystemExit as result:
    assert result.code == 0
from followbot.main import build_orchestrator
from followbot.camera import SyntheticCamera
assert SyntheticCamera(2, 2).capture().width == 2
"""
        result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--output", result.stdout)
        self.assertNotIn("RuntimeWarning", result.stderr)

    def test_nonfinite_warmup_rejected_before_camera_open(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                main(["--warmup", "nan"])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
