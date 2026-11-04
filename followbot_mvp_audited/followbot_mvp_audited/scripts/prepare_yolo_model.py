from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _validate_ncnn_dir(path: Path) -> tuple[bool, str]:
    if not path.exists() or not path.is_dir():
        return False, f"Diretorio inexistente: {path}"

    params = list(path.glob("*.param"))
    bins = list(path.glob("*.bin"))

    if not params:
        return False, f"Nenhum arquivo .param encontrado em: {path}"
    if not bins:
        return False, f"Nenhum arquivo .bin encontrado em: {path}"
    return True, "OK"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepara o modelo YOLO para o FollowBot: baixa o .pt (se necessario) "
            "e exporta para NCNN no caminho esperado pelo projeto."
        )
    )
    parser.add_argument("--model", default="yolo26n.pt", help="Peso base YOLO (.pt)")
    parser.add_argument("--imgsz", type=int, default=320, help="Resolucao de inferencia/export")
    parser.add_argument(
        "--target-dir",
        default="models/yolo26n_ncnn_model",
        help="Diretorio final do modelo NCNN usado pelo config",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Apenas baixa/carrega o .pt e valida diretorio existente em --target-dir",
    )
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERRO: Ultralytics nao instalado.")
        print("Instale com: pip install -e '.[ai,export]'")
        return 2

    target_dir = Path(args.target_dir).resolve()
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"Carregando modelo base: {args.model}")
    model = YOLO(args.model)

    if args.skip_export:
        ok, reason = _validate_ncnn_dir(target_dir)
        if not ok:
            print(f"ERRO: {reason}")
            return 3
        print(f"Modelo NCNN valido em: {target_dir}")
        return 0

    print(f"Exportando para NCNN com imgsz={args.imgsz}...")
    export_result = model.export(format="ncnn", imgsz=args.imgsz)
    exported_dir = Path(str(export_result)).resolve()

    if not exported_dir.exists() or not exported_dir.is_dir():
        print("ERRO: export retornou caminho invalido:")
        print(f"  {exported_dir}")
        return 4

    if target_dir != exported_dir:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(exported_dir, target_dir)

    ok, reason = _validate_ncnn_dir(target_dir)
    if not ok:
        print(f"ERRO: {reason}")
        return 5

    print("Modelo NCNN pronto.")
    print(f"Diretorio final: {target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())