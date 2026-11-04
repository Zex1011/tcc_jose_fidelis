from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import sys
from pathlib import Path

MIN_PYTHON = (3, 11)
RECOMMENDED_PYTHON = (3, 12)


def status(ok: bool) -> str:
    return "OK" if ok else "ERRO"


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight portátil do FollowBot MVP")
    parser.add_argument(
        "--require-ai",
        action="store_true",
        help="também exige que ultralytics esteja instalado",
    )
    parser.add_argument(
        "--require-webcam",
        action="store_true",
        help="também exige que OpenCV (cv2) esteja instalado para backend de webcam",
    )
    parser.add_argument(
        "--require-model",
        action="store_true",
        help="também exige que exista um diretório de modelo NCNN válido",
    )
    parser.add_argument(
        "--model-path",
        default="models/yolo26n_ncnn_model",
        help="caminho do diretório de modelo NCNN para validação",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    print(f"FollowBot root : {root}")
    print(f"CWD            : {Path.cwd()}")
    print(f"SO             : {platform.platform()}")
    print(f"Arquitetura    : {platform.machine()}")
    print(f"Python         : {sys.version.split()[0]} ({sys.executable})")
    print()

    errors: list[str] = []
    warnings: list[str] = []

    py_ok = sys.version_info >= MIN_PYTHON
    print(f"[{status(py_ok)}] Python >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}")
    if not py_ok:
        errors.append("Python 3.11+ é obrigatório porque o projeto usa tomllib.")
    elif sys.version_info[:2] != RECOMMENDED_PYTHON:
        warnings.append(
            "Para reproduzir o procedimento de PC com menos variação, Python 3.12 é a versão recomendada."
        )

    required_files = [
        root / "pyproject.toml",
        root / "config.mock.toml",
        root / "src" / "followbot" / "main.py",
    ]
    for path in required_files:
        ok = path.exists()
        print(f"[{status(ok)}] arquivo {path.relative_to(root)}")
        if not ok:
            errors.append(f"Arquivo ausente: {path}")

    packages = ["numpy", "serial"]
    if args.require_ai:
        packages.append("ultralytics")
    if args.require_webcam:
        packages.append("cv2")

    for package in packages:
        ok = importlib.util.find_spec(package) is not None
        print(f"[{status(ok)}] import {package}")
        if not ok:
            errors.append(f"Pacote Python ausente: {package}")

    if args.require_model:
        model_dir = (root / args.model_path).resolve()
        params = list(model_dir.glob("*.param")) if model_dir.is_dir() else []
        bins = list(model_dir.glob("*.bin")) if model_dir.is_dir() else []
        model_ok = model_dir.is_dir() and bool(params) and bool(bins)
        print(f"[{status(model_ok)}] modelo NCNN em {args.model_path}")
        if not model_ok:
            errors.append(
                "Modelo NCNN ausente/incompleto. Rode scripts/prepare_yolo_model.py e confirme .param/.bin."
            )

    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        print(f"[OK] virtualenv ativo: {venv}")
    else:
        warnings.append("Nenhum VIRTUAL_ENV detectado. Use .venv para evitar conflito com o Python do sistema.")

    try:
        from followbot.config import load_config

        cfg = load_config(root / "config.mock.toml")
        if cfg.camera.backend != "synthetic" or cfg.communication.backend != "mock":
            errors.append("config.mock.toml não está totalmente isolado de hardware.")
        else:
            print("[OK] config.mock.toml carrega e usa synthetic/mock")
    except Exception as exc:
        errors.append(f"Falha ao carregar config.mock.toml: {exc}")

    print()
    if warnings:
        print("Avisos:")
        for item in warnings:
            print(f"  - {item}")
        print()

    if errors:
        print("Falhas de preflight:")
        for item in errors:
            print(f"  - {item}")
        return 1

    print("Preflight concluído sem falhas bloqueantes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
