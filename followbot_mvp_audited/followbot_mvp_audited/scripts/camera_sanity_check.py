from __future__ import annotations

import argparse
from statistics import mean


def main() -> int:
    parser = argparse.ArgumentParser(description="Checa se a webcam está entregando imagem útil.")
    parser.add_argument("--index", type=int, default=0, help="Índice da webcam (ex.: 0)")
    parser.add_argument("--frames", type=int, default=10, help="Quantidade de frames para amostragem")
    parser.add_argument("--min-mean", type=float, default=8.0, help="Média mínima de brilho (0-255)")
    parser.add_argument(
        "--min-std",
        type=float,
        default=4.0,
        help="Desvio-padrão mínimo de intensidade (0-255)",
    )
    args = parser.parse_args()

    try:
        import cv2
        import numpy as np
    except ImportError:
        print("ERRO: OpenCV e NumPy são necessários. Instale o extra webcam.")
        return 2

    cap = cv2.VideoCapture(args.index)
    if not cap.isOpened():
        print(f"ERRO: não foi possível abrir webcam index={args.index}")
        return 3

    means: list[float] = []
    stds: list[float] = []
    collected = 0
    try:
        for _ in range(max(1, args.frames)):
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            means.append(float(np.mean(gray)))
            stds.append(float(np.std(gray)))
            collected += 1
    finally:
        cap.release()

    if collected == 0:
        print("ERRO: nenhum frame válido foi capturado.")
        return 4

    m_mean = mean(means)
    m_std = mean(stds)
    print(f"frames={collected} mean_luma={m_mean:.2f} std_luma={m_std:.2f}")

    likely_blocked = m_mean < args.min_mean or m_std < args.min_std
    if likely_blocked:
        print("ALERTA: imagem parece bloqueada/escura (lente tampada, privacy shutter, permissão, app ocupando câmera).")
        print("Ações sugeridas: abrir app de câmera do sistema, destravar obturador físico, fechar apps que seguram webcam.")
        return 1

    print("OK: webcam está entregando imagem com variação suficiente para inferência.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
