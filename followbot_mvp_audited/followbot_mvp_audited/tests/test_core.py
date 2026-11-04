from __future__ import annotations

import time
import unittest

import numpy as np

from followbot.control import BBoxProportionalController
from followbot.models import BoundingBox, Detection, Frame
from followbot.tracking import NearestBBoxSelector


def frame(width: int = 640, height: int = 480) -> Frame:
    return Frame(
        image=np.zeros((height, width, 3), dtype=np.uint8),
        sequence=1,
        captured_monotonic_s=time.monotonic(),
    )


def detection(cx: float, cy: float, width: float = 100, height: float = 200) -> Detection:
    return Detection(
        bbox=BoundingBox(cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2),
        confidence=0.9,
        class_id=0,
        class_name="person",
    )


class SelectorTests(unittest.TestCase):
    def test_first_selection(self) -> None:
        f = frame()
        a = detection(100, 200)
        b = detection(500, 200)
        selector = NearestBBoxSelector(initial_strategy="first")
        self.assertIs(selector.select([a, b], f), a)

    def test_next_selection_is_nearest_to_previous(self) -> None:
        f = frame()
        selector = NearestBBoxSelector(initial_strategy="first", max_center_distance=1.0)
        first = detection(100, 200)
        selector.select([first], f)
        near = detection(120, 210)
        far = detection(500, 210)
        self.assertIs(selector.select([far, near], f), near)

    def test_large_jump_is_rejected(self) -> None:
        f = frame()
        selector = NearestBBoxSelector(initial_strategy="first", max_center_distance=0.10)
        selector.select([detection(100, 200)], f)
        self.assertIsNone(selector.select([detection(600, 200)], f))


class ControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.f = frame()
        self.controller = BBoxProportionalController(
            desired_height_ratio=0.5,
            height_deadband=0.01,
            horizontal_deadband=0.01,
            kp_linear=1.0,
            kp_angular=1.0,
            max_linear=1.0,
            max_angular=1.0,
        )

    def test_centered_far_target_moves_forward(self) -> None:
        target = detection(320, 240, width=60, height=120)
        command = self.controller.compute(target, self.f)
        self.assertGreater(command.linear, 0)
        self.assertAlmostEqual(command.angular, 0.0)

    def test_target_on_left_turns_left(self) -> None:
        target = detection(120, 240, width=100, height=240)
        command = self.controller.compute(target, self.f)
        self.assertGreater(command.angular, 0)

    def test_target_on_right_turns_right(self) -> None:
        target = detection(520, 240, width=100, height=240)
        command = self.controller.compute(target, self.f)
        self.assertLess(command.angular, 0)

    def test_close_target_does_not_advance_when_reverse_disabled(self) -> None:
        target = detection(320, 240, width=200, height=400)
        command = self.controller.compute(target, self.f)
        self.assertEqual(command.linear, 0.0)


if __name__ == "__main__":
    unittest.main()
