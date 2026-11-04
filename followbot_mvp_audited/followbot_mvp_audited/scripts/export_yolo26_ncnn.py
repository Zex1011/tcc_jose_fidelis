from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exporta YOLO26n para NCNN. Preferencialmente rode em um PC de desenvolvimento."
    )
    parser.add_argument("--model", default="yolo26n.pt")
    parser.add_argument("--imgsz", type=int, default=320)
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.model)
    result = model.export(format="ncnn", imgsz=args.imgsz)
    print(result)


if __name__ == "__main__":
    main()
