from __future__ import annotations

import glob
from pathlib import Path


def main() -> int:
    devices = sorted(glob.glob("/dev/video*"))
    if not devices:
        print("Nenhum dispositivo /dev/video* encontrado.")
        return 1

    print("Dispositivos detectados:")
    for dev in devices:
        print(f"  - {dev}")

    try:
        import cv2
    except ImportError:
        print()
        print("OpenCV (cv2) não instalado; pulando teste de abertura.")
        return 0

    print()
    print("Teste de abertura com OpenCV:")
    for dev in devices:
        # /dev/videoN -> N
        idx = int(Path(dev).name.replace("video", ""))
        cap = cv2.VideoCapture(idx)
        ok = cap.isOpened()
        print(f"  - index={idx}: {'OK' if ok else 'FALHA'}")
        if ok:
            ret, frame = cap.read()
            print(f"    frame: {'OK' if ret and frame is not None else 'FALHA'}")
        cap.release()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
