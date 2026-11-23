from __future__ import annotations

from concurrent.futures import Future
from contextlib import redirect_stdout
import io
import json
import queue
import subprocess
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from followbot.communication import micro_ros_link as module


class ControlledPublisher:
    """Advance exactly one worker iteration per token, without a ROS runtime."""

    def __init__(self, *args):
        self.arguments = args
        self.calls = [("init", threading.get_ident())]
        self.messages = []
        self.subscribers = 1
        self.fail_publish = False
        self.fail_close = False
        self.closed = threading.Event()
        self._tokens = queue.Queue()
        self._condition = threading.Condition()
        self.spins = 0

    def subscriber_count(self):
        self.calls.append(("subscriber_count", threading.get_ident()))
        return self.subscribers

    def publish(self, linear, angular):
        self.calls.append(("publish", threading.get_ident()))
        if self.fail_publish and (linear or angular):
            raise RuntimeError("publication failed")
        self.messages.append((linear, angular))

    def spin_once(self):
        self.calls.append(("spin_once", threading.get_ident()))
        with self._condition:
            self.spins += 1
            self._condition.notify_all()
        token = self._tokens.get(timeout=5)
        if isinstance(token, BaseException):
            raise token

    def step(self, error=None):
        self._tokens.put(error)

    def wait_spin(self, count):
        with self._condition:
            if not self._condition.wait_for(lambda: self.spins >= count, timeout=2):
                raise AssertionError(f"Worker did not enter iteration {count}")

    def close(self):
        self.calls.append(("close", threading.get_ident()))
        self.closed.set()
        if self.fail_close:
            raise RuntimeError("cleanup failed")


class MicroRosCommunicationTests(unittest.TestCase):
    def setUp(self):
        self.links = []
        self.publishers = []

        def create(*args):
            publisher = ControlledPublisher(*args)
            self.publishers.append(publisher)
            return publisher

        self.publisher_patch = patch.object(module, "_RosPublisher", side_effect=create)
        self.factory = self.publisher_patch.start()
        self.addCleanup(self.publisher_patch.stop)

    def start(self, **kwargs):
        kwargs.setdefault("command_timeout_s", 10.0)
        kwargs.setdefault("shutdown_timeout_s", 1.0)
        link = module.MicroRosCommunication(**kwargs)
        publisher = self.publishers[-1]
        self.links.append((link, publisher))
        publisher.wait_spin(1)
        return link, publisher

    def close_link(self, link, publisher, expected_error=None):
        errors = []

        def close():
            try:
                link.close()
            except BaseException as exc:
                errors.append(exc)

        closer = threading.Thread(target=close)
        closer.start()
        self.assertTrue(link._stop.wait(1))
        publisher.step()
        closer.join(2)
        self.assertFalse(closer.is_alive(), "close() left a waiting caller")
        if expected_error is None:
            self.assertFalse(errors, errors)
        else:
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], expected_error)
        self.assertFalse(link._thread.is_alive())
        return errors

    def tearDown(self):
        for link, publisher in self.links:
            self.close_link(link, publisher)

    def test_ros_lifetime_runs_in_one_worker_and_future_means_local_publish(self):
        caller = threading.get_ident()
        link, publisher = self.start(topic="/juca/velocity", domain_id=17)
        future = link.send_velocity(0.2, -0.4)
        self.assertFalse(future.done())
        publisher.step()
        self.assertIsNone(future.result(timeout=2))
        self.assertEqual(publisher.messages, [(0.2, -0.4)])
        self.close_link(link, publisher)
        self.assertEqual(publisher.messages, [(0.2, -0.4), (0.0, 0.0)])
        owners = {owner for _, owner in publisher.calls}
        self.assertEqual(len(owners), 1)
        self.assertNotIn(caller, owners)
        self.assertEqual(publisher.arguments[:3], ("/juca/velocity", "followbot_velocity", 17))

    def test_latest_waiting_command_replaces_previous_futures(self):
        link, publisher = self.start()
        first = link.send_velocity(0.1, 0.0)
        second = link.send_velocity(0.2, 0.0)
        last = link.send_velocity(0.3, -0.2)
        for future in (first, second):
            with self.assertRaises(module.CommandSupersededError):
                future.result(timeout=0)
        publisher.step()
        self.assertIsNone(last.result(timeout=2))
        self.assertEqual(publisher.messages, [(0.3, -0.2)])

    def test_no_subscriber_waits_and_expiration_prevents_publication(self):
        clock = SimpleNamespace(now=100.0)
        with patch.object(module, "time", SimpleNamespace(monotonic=lambda: clock.now)):
            link, publisher = self.start(command_timeout_s=0.5)
            publisher.subscribers = 0
            future = link.send_velocity(0.2, 0.0)
            publisher.step()
            publisher.wait_spin(2)
            self.assertFalse(future.done())
            self.assertEqual(publisher.messages, [])
            clock.now += 0.6
            publisher.step()
            with self.assertRaises(TimeoutError):
                future.result(timeout=2)
            self.assertEqual(publisher.messages, [])

    def test_cancelled_waiting_command_is_not_published(self):
        link, publisher = self.start()
        future = link.send_velocity(0.2, -0.1)
        self.assertTrue(future.cancel())
        publisher.step()
        publisher.wait_spin(2)
        self.assertTrue(future.cancelled())
        self.assertEqual(publisher.messages, [])

    def test_completed_velocity_is_not_periodically_replayed(self):
        link, publisher = self.start()
        future = link.send_velocity(0.2, 0.1)
        publisher.step()
        future.result(timeout=2)
        publisher.wait_spin(2)
        for count in range(3, 7):
            publisher.step()
            publisher.wait_spin(count)
        self.assertEqual(publisher.messages, [(0.2, 0.1)])

    def test_executor_failure_rejects_pending_command_and_closes_worker(self):
        link, publisher = self.start()
        future = link.send_velocity(0.2, 0.1)
        publisher.step(RuntimeError("executor failed"))
        with self.assertRaisesRegex(RuntimeError, "executor failed"):
            future.result(timeout=2)
        self.assertTrue(publisher.closed.wait(2))
        self.assertEqual(publisher.messages, [(0.0, 0.0)])
        with self.assertRaises(RuntimeError):
            link.send_velocity(0.0, 0.0)

    def test_publish_failure_finishes_future_and_attempts_stop(self):
        link, publisher = self.start()
        publisher.fail_publish = True
        future = link.send_velocity(0.2, 0.1)
        publisher.step()
        with self.assertRaisesRegex(RuntimeError, "publication failed"):
            future.result(timeout=2)
        self.assertTrue(publisher.closed.wait(2))
        self.assertEqual(publisher.messages, [(0.0, 0.0)])

    def test_close_rejects_queued_motion_sends_stop_and_is_idempotent(self):
        link, publisher = self.start()
        future = link.send_velocity(0.3, 0.2)
        self.close_link(link, publisher)
        with self.assertRaisesRegex(RuntimeError, "encerrada"):
            future.result(timeout=0)
        self.assertEqual(publisher.messages, [(0.0, 0.0)])
        link.close()
        self.assertEqual(publisher.messages, [(0.0, 0.0)])
        with self.assertRaises(RuntimeError):
            link.send_velocity(0.1, 0.0)

    def test_nonfinite_velocity_is_rejected_before_queueing(self):
        link, publisher = self.start()
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    link.send_velocity(value, 0.0)
                with self.assertRaises(ValueError):
                    link.send_velocity(0.0, value)
        publisher.step()
        publisher.wait_spin(2)
        self.assertEqual(publisher.messages, [])

    def test_invalid_configuration_does_not_start_ros(self):
        cases = [
            {"command_timeout_s": 0}, {"startup_timeout_s": -1},
            {"shutdown_timeout_s": float("nan")}, {"command_timeout_s": float("inf")},
            {"topic": " "}, {"node_name": ""}, {"domain_id": -1}, {"domain_id": True},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                module.MicroRosCommunication(**kwargs)
        self.factory.assert_not_called()

    def test_initialization_failure_reaches_constructor(self):
        self.factory.side_effect = RuntimeError("ROS unavailable")
        with self.assertRaisesRegex(RuntimeError, "ROS unavailable"):
            module.MicroRosCommunication(startup_timeout_s=1)

    def test_cleanup_failure_reaches_close_caller(self):
        link, publisher = self.start()
        publisher.fail_close = True
        errors = self.close_link(link, publisher, expected_error=RuntimeError)
        self.links.remove((link, publisher))
        self.assertIn("liberar recursos", str(errors[0]))
        self.assertEqual(str(errors[0].__cause__), "cleanup failed")
        self.assertEqual(publisher.messages, [(0.0, 0.0)])

    def test_context_manager_closes_when_body_raises(self):
        link, publisher = self.start()

        def release_during_close():
            if link._stop.wait(2):
                publisher.step()

        releaser = threading.Thread(target=release_during_close)
        releaser.start()
        with self.assertRaisesRegex(ValueError, "application failed"):
            with link:
                raise ValueError("application failed")
        releaser.join(2)
        self.assertFalse(releaser.is_alive())
        self.assertTrue(publisher.closed.is_set())
        self.assertEqual(publisher.messages, [(0.0, 0.0)])

    def test_close_reports_blocked_worker_then_can_finish_after_unblock(self):
        link, publisher = self.start(shutdown_timeout_s=0.02)
        future = link.send_velocity(0.3, 0.0)
        with self.assertRaises(TimeoutError):
            link.close()
        with self.assertRaises(RuntimeError):
            future.result(timeout=0)
        self.assertFalse(publisher.closed.is_set())
        publisher.step()
        self.assertTrue(publisher.closed.wait(2))
        link.close()
        self.assertEqual(publisher.messages, [(0.0, 0.0)])


class RosAdapterTests(unittest.TestCase):
    def fake_modules(self):
        events = []
        context = MagicMock()
        node = MagicMock()
        executor = MagicMock()
        publisher = node.create_publisher.return_value
        context.try_shutdown.side_effect = lambda: events.append("shutdown context")
        context.destroy.side_effect = lambda: events.append("destroy context")
        node.destroy_node.side_effect = lambda: events.append("destroy node")
        executor.shutdown.side_effect = lambda **kwargs: events.append("shutdown executor")

        def twist():
            vector = lambda: SimpleNamespace(x=0.0, y=0.0, z=0.0)
            return SimpleNamespace(linear=vector(), angular=vector())

        modules = {
            "geometry_msgs.msg": SimpleNamespace(Twist=twist),
            "rclpy.context": SimpleNamespace(Context=MagicMock(return_value=context)),
            "rclpy.duration": SimpleNamespace(Duration=lambda **kwargs: SimpleNamespace(**kwargs)),
            "rclpy.executors": SimpleNamespace(SingleThreadedExecutor=MagicMock(return_value=executor)),
            "rclpy.node": SimpleNamespace(Node=MagicMock(return_value=node)),
            "rclpy.qos": SimpleNamespace(
                QoSProfile=lambda **kwargs: SimpleNamespace(**kwargs),
                HistoryPolicy=SimpleNamespace(KEEP_LAST="keep_last"),
                ReliabilityPolicy=SimpleNamespace(RELIABLE="reliable"),
                DurabilityPolicy=SimpleNamespace(VOLATILE="volatile"),
            ),
        }
        return SimpleNamespace(modules=modules, context=context, node=node,
                               executor=executor, publisher=publisher, events=events)

    def test_twist_qos_private_context_and_reverse_order_cleanup(self):
        fake = self.fake_modules()
        with patch.dict(sys.modules, fake.modules):
            ros = module._RosPublisher("/juca/velocity", "test_node", 7, 0.5)
            ros.publish(0.25, -0.4)
            ros.spin_once()
            fake.publisher.get_subscription_count.return_value = 2
            self.assertEqual(ros.subscriber_count(), 2)
            ros.close()
            ros.close()
        fake.context.init.assert_called_once_with(args=[], domain_id=7)
        node_kwargs = fake.modules["rclpy.node"].Node.call_args.kwargs
        self.assertIs(node_kwargs["context"], fake.context)
        self.assertFalse(node_kwargs["enable_rosout"])
        self.assertFalse(node_kwargs["start_parameter_services"])
        _, topic, qos = fake.node.create_publisher.call_args.args
        self.assertEqual(topic, "/juca/velocity")
        self.assertEqual((qos.history, qos.depth, qos.reliability, qos.durability),
                         ("keep_last", 1, "reliable", "volatile"))
        self.assertEqual(qos.lifespan.seconds, 0.5)
        message = fake.publisher.publish.call_args.args[0]
        self.assertEqual(vars(message.linear), {"x": 0.25, "y": 0.0, "z": 0.0})
        self.assertEqual(vars(message.angular), {"x": 0.0, "y": 0.0, "z": -0.4})
        fake.executor.spin_once.assert_called_once_with(timeout_sec=0.02)
        self.assertEqual(fake.events, ["shutdown executor", "destroy node",
                                       "shutdown context", "destroy context"])

    def test_failed_publisher_creation_releases_all_started_resources(self):
        fake = self.fake_modules()
        fake.node.create_publisher.side_effect = RuntimeError("invalid topic")
        with patch.dict(sys.modules, fake.modules):
            with self.assertRaisesRegex(RuntimeError, "invalid topic"):
                module._RosPublisher("invalid topic", "node", None, 0.5)
        self.assertEqual(fake.events, ["shutdown executor", "destroy node",
                                       "shutdown context", "destroy context"])


class MicroRosCliTests(unittest.TestCase):
    def test_default_cli_only_requests_stop_and_reports_no_esp_ack(self):
        client = MagicMock()
        result = Future()
        result.set_result(None)
        client.send_velocity.return_value = result
        with patch.object(module, "MicroRosCommunication") as factory:
            factory.return_value.__enter__.return_value = client
            with redirect_stdout(io.StringIO()) as output:
                status = module.main([])
        self.assertEqual(status, 0)
        client.send_velocity.assert_called_once_with(0.0, 0.0)
        body = json.loads(output.getvalue())
        self.assertTrue(body["published_locally"])
        self.assertFalse(body["esp_acknowledged"])
        factory.return_value.__exit__.assert_called_once()

    def test_cli_timeout_returns_failure_and_releases_context(self):
        client = MagicMock()
        result = Future()
        result.set_exception(TimeoutError("expired before discovery"))
        client.send_velocity.return_value = result
        with patch.object(module, "MicroRosCommunication") as factory:
            factory.return_value.__enter__.return_value = client
            with redirect_stdout(io.StringIO()) as output:
                status = module.main(["--topic", "/juca/velocity", "--domain-id", "4"])
        self.assertEqual(status, 1)
        self.assertIn("expired before discovery", output.getvalue())
        factory.return_value.__exit__.assert_called_once()
        self.assertEqual(factory.call_args.kwargs["domain_id"], 4)

    def test_import_and_help_work_without_ros_installation(self):
        script = """
import sys
sys.modules['rclpy'] = None
sys.modules['geometry_msgs'] = None
from followbot.communication.micro_ros_link import main
try:
    main(['--help'])
except SystemExit as exc:
    assert exc.code == 0
else:
    raise AssertionError('--help did not exit')
"""
        result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--topic", result.stdout)


if __name__ == "__main__":
    unittest.main()
