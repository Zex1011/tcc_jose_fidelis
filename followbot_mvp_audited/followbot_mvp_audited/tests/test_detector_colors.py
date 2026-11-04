from __future__ import annotations

import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import numpy as np

from followbot.models import Frame
from followbot.vision.ultralytics_detector import UltralyticsPersonDetector


class DetectorColorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = Mock()
        self.model.names = {0: "person"}
        self.model.predict.return_value = []
        fake_ultralytics = ModuleType("ultralytics")
        fake_ultralytics.YOLO = Mock(return_value=self.model)
        with patch.dict(sys.modules, {"ultralytics": fake_ultralytics}):
            self.detector = UltralyticsPersonDetector("unused-model.pt")

    def test_numpy_input_uses_bgr_without_changing_rgb_frame(self) -> None:
        rgb = np.array(
            [[[255, 0, 0], [0, 0, 255], [20, 40, 60]]], dtype=np.uint8
        )
        original = rgb.copy()
        frame = Frame(image=rgb, sequence=1, captured_monotonic_s=0.0)

        self.assertEqual(self.detector.detect(frame), [])

        source = self.model.predict.call_args.kwargs["source"]
        np.testing.assert_array_equal(
            source,
            np.array([[[0, 0, 255], [255, 0, 0], [60, 40, 20]]], dtype=np.uint8),
        )
        np.testing.assert_array_equal(frame.image, original)
        self.assertTrue(source.flags.c_contiguous)
        self.assertFalse(np.shares_memory(source, frame.image))

    def test_noncontiguous_camera_frame_becomes_contiguous_model_input(self) -> None:
        rgb = np.array(
            [[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [20, 40, 60]]],
            dtype=np.uint8,
        )
        view = rgb[:, ::-1, :]
        original = rgb.copy()
        self.assertFalse(view.flags.c_contiguous)

        self.detector.detect(Frame(image=view, sequence=2, captured_monotonic_s=0.0))

        source = self.model.predict.call_args.kwargs["source"]
        np.testing.assert_array_equal(
            source,
            np.array(
                [[[0, 255, 0], [0, 0, 255]], [[60, 40, 20], [255, 0, 0]]],
                dtype=np.uint8,
            ),
        )
        self.assertEqual(source.dtype, np.uint8)
        self.assertTrue(source.flags.c_contiguous)
        np.testing.assert_array_equal(rgb, original)


if __name__ == "__main__":
    unittest.main()
