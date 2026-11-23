"""ROS 2 publisher for an ESP reached through an external micro-ROS Agent.

Provisional contract: geometry_msgs/Twist on /cmd_vel (v=linear.x,
w=angular.z). Confirm topic, type, units and QoS against the Juca firmware.
This is not a CommunicationLink backend: local publication is not an ACK.
"""
from __future__ import annotations

import argparse
from concurrent.futures import Future
from contextlib import ExitStack
from dataclasses import dataclass
import json
import math
import threading
import time


class CommandSupersededError(RuntimeError):
    """A newer command replaced a command which had not been published."""


@dataclass(frozen=True, slots=True)
class _PendingVelocity:
    linear: float
    angular: float
    expires_at: float
    future: Future[None]


class _RosPublisher:
    """All instances and methods belong exclusively to the worker thread."""

    def __init__(self, topic: str, node_name: str, domain_id: int | None,
                 command_timeout_s: float) -> None:
        try:
            from geometry_msgs.msg import Twist
            from rclpy.context import Context
            from rclpy.duration import Duration
            from rclpy.executors import SingleThreadedExecutor
            from rclpy.node import Node
            from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
        except ImportError as exc:
            raise RuntimeError(
                "ROS 2/rclpy e geometry_msgs não estão disponíveis neste Python. "
                "Carregue o ambiente ROS 2 antes de iniciar o módulo."
            ) from exc

        self._resources = ExitStack()
        try:
            context = Context()
            # A private context avoids changing the application's signal handlers.
            self._resources.callback(context.destroy)
            self._resources.callback(context.try_shutdown)
            context.init(args=[], domain_id=domain_id)
            self._node = Node(node_name, context=context, enable_rosout=False,
                              start_parameter_services=False, use_global_arguments=False)
            self._resources.callback(self._node.destroy_node)
            self._executor = SingleThreadedExecutor(context=context)
            self._resources.callback(self._executor.shutdown, timeout_sec=0.0)
            qos = QoSProfile(
                history=HistoryPolicy.KEEP_LAST, depth=1,
                reliability=ReliabilityPolicy.RELIABLE,
                durability=DurabilityPolicy.VOLATILE,
                lifespan=Duration(seconds=command_timeout_s),
            )
            self._publisher = self._node.create_publisher(Twist, topic, qos)
            self._message_type = Twist
            self._executor.add_node(self._node)
        except BaseException:
            self._resources.close()
            raise

    def subscriber_count(self) -> int:
        return self._publisher.get_subscription_count()

    def publish(self, linear: float, angular: float) -> None:
        message = self._message_type()
        message.linear.x = linear
        message.angular.z = angular
        self._publisher.publish(message)

    def spin_once(self) -> None:
        self._executor.spin_once(timeout_sec=0.02)

    def close(self) -> None:
        self._resources.close()


class MicroRosCommunication:
    """Publish (v, w) from a dedicated ROS thread, without opening the UART.

    send_velocity() is nonblocking. Its Future completes when publish() returns,
    not when the ESP receives/applies the command. Only the latest waiting
    command is retained; it expires after command_timeout_s. There is no
    periodic replay. The ESP must stop motion with its own command watchdog.

    close() attempts one STOP, releases ROS resources and joins the worker.
    STOP delivery cannot be confirmed without the firmware's feedback contract.
    """

    def __init__(self, topic: str = "/cmd_vel", node_name: str = "followbot_velocity",
                 domain_id: int | None = None, command_timeout_s: float = 0.5,
                 startup_timeout_s: float = 5.0, shutdown_timeout_s: float = 2.0) -> None:
        for name, value in (("command_timeout_s", command_timeout_s),
                            ("startup_timeout_s", startup_timeout_s),
                            ("shutdown_timeout_s", shutdown_timeout_s)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} deve ser finito e maior que zero.")
        if not topic.strip() or not node_name.strip():
            raise ValueError("topic e node_name não podem ser vazios.")
        if domain_id is not None and (type(domain_id) is not int or domain_id < 0):
            raise ValueError("domain_id deve ser um inteiro não negativo ou None.")
        self._command_timeout_s = command_timeout_s
        self._shutdown_timeout_s = shutdown_timeout_s
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._pending: _PendingVelocity | None = None
        self._failure: BaseException | None = None
        self._cleanup_failure: Exception | None = None
        self._thread = threading.Thread(
            target=self._run, args=(topic, node_name, domain_id),
            name="followbot-micro-ros", daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(startup_timeout_s):
            self._stop.set()
            self._thread.join(shutdown_timeout_s)
            raise TimeoutError("Tempo esgotado ao iniciar a thread ROS 2.")
        if self._failure is not None:
            self._thread.join(shutdown_timeout_s)
            raise RuntimeError(f"Falha ao iniciar comunicação ROS 2: {self._failure}") from self._failure

    @staticmethod
    def _reject(command: _PendingVelocity | None, error: BaseException) -> None:
        # Claim the Future before completing it, so cancellation cannot race us.
        if command is not None and command.future.set_running_or_notify_cancel():
            command.future.set_exception(error)

    def send_velocity(self, linear: float, angular: float) -> Future[None]:
        """Queue a fresh command. Future.result() confirms local publication only."""
        linear, angular = float(linear), float(angular)
        if not math.isfinite(linear) or not math.isfinite(angular):
            raise ValueError("As velocidades devem ser finitas.")
        command = _PendingVelocity(
            linear, angular, time.monotonic() + self._command_timeout_s, Future(),
        )
        with self._lock:
            if self._stop.is_set():
                raise RuntimeError("Comunicação encerrada ou thread ROS 2 indisponível.") from self._failure
            previous, self._pending = self._pending, command
        # Never run user Future callbacks while holding the mailbox lock.
        self._reject(previous, CommandSupersededError("Comando substituído por uma velocidade mais recente."))
        return command.future

    def _publish_pending(self, ros: _RosPublisher) -> None:
        with self._lock:
            command = self._pending
        if command is None:
            return
        expired = time.monotonic() >= command.expires_at
        if not expired and not command.future.cancelled() and ros.subscriber_count() == 0:
            return
        with self._lock:
            # A newer command or close() may have replaced the mailbox meanwhile.
            if self._pending is not command or self._stop.is_set():
                return
            self._pending = None
        if not command.future.set_running_or_notify_cancel():
            return
        if time.monotonic() >= command.expires_at:
            command.future.set_exception(TimeoutError("Comando expirou antes da publicação ROS 2."))
            return
        try:
            ros.publish(command.linear, command.angular)
        except BaseException as exc:
            command.future.set_exception(exc)
            raise
        command.future.set_result(None)

    def _run(self, topic: str, node_name: str, domain_id: int | None) -> None:
        ros = None
        try:
            ros = _RosPublisher(topic, node_name, domain_id, self._command_timeout_s)
            self._ready.set()
            while not self._stop.is_set():
                self._publish_pending(ros)
                ros.spin_once()
        except BaseException as exc:
            self._failure = exc
        finally:
            with self._lock:
                self._stop.set()
                pending, self._pending = self._pending, None
            self._ready.set()
            try:
                self._reject(pending, RuntimeError(f"Thread ROS 2 encerrada: {self._failure or 'close'}"))
            finally:
                if ros is not None:
                    try:
                        ros.publish(0.0, 0.0)  # Best effort, never reported as an ACK.
                    except Exception:
                        pass
                    finally:
                        try:
                            ros.close()
                        except Exception as exc:
                            self._cleanup_failure = exc

    def close(self) -> None:
        """Cancel queued work and join; report a worker that cannot stop in time."""
        with self._lock:
            self._stop.set()
            pending, self._pending = self._pending, None
        self._reject(pending, RuntimeError("Comunicação encerrada antes da publicação."))
        if threading.current_thread() is not self._thread:
            self._thread.join(self._shutdown_timeout_s)
            if self._thread.is_alive():
                raise TimeoutError("A thread ROS 2 ainda não encerrou; recursos permanecem sob sua responsabilidade.")
            if self._cleanup_failure is not None:
                raise RuntimeError("Falha ao liberar recursos ROS 2.") from self._cleanup_failure

    def __enter__(self) -> MicroRosCommunication:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publica (v,w) via ROS 2/micro-ROS; padrão: STOP.")
    parser.add_argument("--topic", default="/cmd_vel")
    parser.add_argument("--domain-id", type=int, default=None)
    parser.add_argument("--linear", type=float, default=0.0)
    parser.add_argument("--angular", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=3.0,
                        help="Validade do comando enquanto espera descoberta/publicação, em segundos.")
    args = parser.parse_args(argv)
    try:
        with MicroRosCommunication(topic=args.topic, domain_id=args.domain_id,
                                   command_timeout_s=args.timeout) as communication:
            communication.send_velocity(args.linear, args.angular).result(timeout=args.timeout + 0.5)
            print(json.dumps({"published_locally": True, "esp_acknowledged": False,
                              "topic": args.topic, "linear": args.linear, "angular": args.angular}))
        return 0
    except (RuntimeError, TimeoutError, ValueError) as exc:
        print(f"Falha na comunicação: {exc}")
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
