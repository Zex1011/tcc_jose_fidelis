from .mock_link import MockCommunicationLink
from .serial_link import SerialCommunicationLink


def __getattr__(name: str):
    # Keep ROS optional and allow `python -m ...micro_ros_link` without preloading it.
    if name == "MicroRosCommunication":
        from .micro_ros_link import MicroRosCommunication
        return MicroRosCommunication
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["MockCommunicationLink", "SerialCommunicationLink", "MicroRosCommunication"]
