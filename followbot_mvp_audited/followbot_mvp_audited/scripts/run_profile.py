from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

DEFAULT_PROFILE_DIR = Path("configs/profiles")
DEFAULTS = {
    "mock": DEFAULT_PROFILE_DIR / "mock.toml",
    "webcam": DEFAULT_PROFILE_DIR / "webcam.toml",
    "webcam_ultralytics": DEFAULT_PROFILE_DIR / "webcam_ultralytics.toml",
    "webcam_ultralytics_debug": DEFAULT_PROFILE_DIR / "webcam_ultralytics_debug.toml",
    "synthetic_ultralytics": DEFAULT_PROFILE_DIR / "synthetic_ultralytics.toml",
    "synthetic_ultralytics_lowpower": DEFAULT_PROFILE_DIR / "synthetic_ultralytics_lowpower.toml",
    "rpi": DEFAULT_PROFILE_DIR / "rpi.example.toml",
    "rpi_vision": DEFAULT_PROFILE_DIR / "rpi_vision.toml",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa o FollowBot com perfis nomeados para reduzir erro operacional."
    )
    parser.add_argument(
        "profile",
        nargs="?",
        help=(
            "Perfil: mock, webcam, webcam_ultralytics, webcam_ultralytics_debug, "
            "synthetic_ultralytics, synthetic_ultralytics_lowpower, rpi, rpi_vision"
        ),
    )
    parser.add_argument("--config", help="Caminho TOML explícito (sobrescreve profile)")
    parser.add_argument("--max-cycles", type=int, default=None)
    parser.add_argument(
        "--limit-threads",
        type=int,
        default=None,
        help="Se informado, limita OMP/BLAS/NumExpr para N threads neste processo.",
    )
    parser.add_argument("--list", action="store_true", help="Lista perfis disponíveis")
    args = parser.parse_args()

    if args.list:
        print("Perfis disponíveis:")
        for name, path in DEFAULTS.items():
            print(f"  - {name}: {path}")
        return 0

    config_path: Path | None = None
    if args.config:
        config_path = Path(args.config)
    elif args.profile:
        if args.profile not in DEFAULTS:
            print(f"ERRO: perfil desconhecido: {args.profile}")
            print("Use --list para ver perfis válidos.")
            return 2
        config_path = DEFAULTS[args.profile]

    if config_path is None:
        print("ERRO: informe um profile ou use --config.")
        print("Exemplo: python scripts/run_profile.py mock --max-cycles 20")
        return 2

    if not config_path.exists():
        print(f"ERRO: arquivo de config não encontrado: {config_path}")
        return 3

    cmd = [sys.executable, "-m", "followbot.main", "--config", str(config_path)]
    if args.max_cycles is not None:
        cmd.extend(["--max-cycles", str(args.max_cycles)])

    if args.limit_threads is not None:
        n = max(1, int(args.limit_threads))
        for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            os.environ[key] = str(n)

    print("Executando:")
    print(" ".join(cmd))
    os.execv(sys.executable, cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
