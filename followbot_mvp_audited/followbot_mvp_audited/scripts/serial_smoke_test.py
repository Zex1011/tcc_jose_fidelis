from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from followbot.communication import SerialCommunicationLink
from followbot.models import MotionCommand


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Teste seguro do protocolo serial: envia somente STOP (v=0, w=0)."
    )
    parser.add_argument("--port", required=True, help="Ex.: COM4 ou /dev/ttyACM0")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--startup-delay", type=float, default=1.5)
    args = parser.parse_args()

    link = SerialCommunicationLink(
        port=args.port,
        baudrate=args.baudrate,
        ack_timeout_s=0.5,
        write_timeout_s=0.5,
        retries=2,
        startup_delay_s=args.startup_delay,
    )
    try:
        for i in range(args.count):
            result = link.send(MotionCommand.stop())
            print(f"STOP {i + 1}/{args.count}: {result.as_dict()}")
            if not result.success:
                return 1
    finally:
        try:
            link.send(MotionCommand.stop())
        finally:
            link.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
