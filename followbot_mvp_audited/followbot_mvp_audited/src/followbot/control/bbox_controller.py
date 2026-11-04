from __future__ import annotations

from ..interfaces import Controller
from ..models import Detection, Frame, MotionCommand


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


class BBoxProportionalController(Controller):
    """Simple P controller using target horizontal offset and bbox height.

    Convention before applying `angular_sign`:
      +angular => turn left / counter-clockwise
      -angular => turn right / clockwise

    `linear` and `angular` are reference values. Their physical units depend on
    the contract implemented by the ESP. The recommended final contract is m/s
    and rad/s, but normalized values are also possible for an open-loop MVP.
    """

    def __init__(
        self,
        desired_height_ratio: float = 0.55,
        height_deadband: float = 0.05,
        horizontal_deadband: float = 0.06,
        kp_linear: float = 1.0,
        kp_angular: float = 1.3,
        max_linear: float = 0.40,
        max_angular: float = 1.20,
        allow_reverse: bool = False,
        forward_slowdown_error: float = 0.35,
        forward_stop_error: float = 0.75,
        angular_sign: float = 1.0,
    ) -> None:
        if not 0 < desired_height_ratio <= 1:
            raise ValueError("desired_height_ratio deve estar em (0, 1].")
        if not 0 <= horizontal_deadband < 1:
            raise ValueError("horizontal_deadband deve estar em [0, 1).")
        if not 0 <= forward_slowdown_error < forward_stop_error <= 1:
            raise ValueError("forward_slowdown_error < forward_stop_error <= 1 é obrigatório.")

        self.desired_height_ratio = desired_height_ratio
        self.height_deadband = height_deadband
        self.horizontal_deadband = horizontal_deadband
        self.kp_linear = kp_linear
        self.kp_angular = kp_angular
        self.max_linear = max_linear
        self.max_angular = max_angular
        self.allow_reverse = allow_reverse
        self.forward_slowdown_error = forward_slowdown_error
        self.forward_stop_error = forward_stop_error
        self.angular_sign = angular_sign

    def compute(self, target: Detection, frame: Frame) -> MotionCommand:
        if frame.width <= 0 or frame.height <= 0:
            return MotionCommand.stop()

        # +erro => pessoa à esquerda => virar para a esquerda (+w).
        horizontal_error = ((frame.width / 2.0) - target.bbox.cx) / (frame.width / 2.0)
        horizontal_error = _clamp(horizontal_error, -1.0, 1.0)
        if abs(horizontal_error) < self.horizontal_deadband:
            horizontal_error = 0.0

        angular = self.angular_sign * self.kp_angular * horizontal_error
        angular = _clamp(angular, -self.max_angular, self.max_angular)

        height_ratio = target.bbox.height / frame.height
        distance_error = self.desired_height_ratio - height_ratio
        if abs(distance_error) < self.height_deadband:
            distance_error = 0.0

        linear = self.kp_linear * distance_error
        if not self.allow_reverse:
            linear = max(0.0, linear)
        linear = _clamp(linear, -self.max_linear, self.max_linear)

        # Não avançar rapidamente enquanto o alvo estiver muito fora do eixo.
        abs_horizontal = abs(horizontal_error)
        if abs_horizontal >= self.forward_stop_error:
            linear = min(linear, 0.0) if self.allow_reverse else 0.0
        elif abs_horizontal > self.forward_slowdown_error and linear > 0:
            span = self.forward_stop_error - self.forward_slowdown_error
            factor = (self.forward_stop_error - abs_horizontal) / span
            linear *= _clamp(factor, 0.0, 1.0)

        return MotionCommand(linear=linear, angular=angular)
