from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    index = (len(values) - 1) * p
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume tempos registrados no JSONL do FollowBot")
    parser.add_argument("log", nargs="?", default="logs/followbot.log")
    args = parser.parse_args()

    timings: dict[str, list[float]] = {}
    cycles = 0

    for line in Path(args.log).read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        data = record.get("data") or {}
        current = data.get("timings_ms")
        if not current:
            continue
        cycles += 1
        for name, value in current.items():
            timings.setdefault(name, []).append(float(value))

    if cycles == 0:
        print("Nenhum ciclo com timings encontrado.")
        return

    print(f"Ciclos: {cycles}")
    print(f"{'etapa':<18} {'média':>10} {'mediana':>10} {'p95':>10} {'p99':>10} {'máx':>10}")
    for name, values in timings.items():
        print(
            f"{name:<18} "
            f"{statistics.fmean(values):>10.2f} "
            f"{statistics.median(values):>10.2f} "
            f"{percentile(values, 0.95):>10.2f} "
            f"{percentile(values, 0.99):>10.2f} "
            f"{max(values):>10.2f}"
        )


if __name__ == "__main__":
    main()
