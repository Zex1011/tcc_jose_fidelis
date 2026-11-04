from __future__ import annotations

import argparse
from contextlib import closing
import math
from pathlib import Path
import sys
import time

from ..interfaces import Camera
from ..models import Frame


class Picamera2Camera(Camera):
    """On-demand Raspberry Pi camera adapter using Picamera2.

    `queue=False` asks Picamera2 not to hand back a previously queued frame,
    matching the project goal of obtaining a fresh image at capture time.
    """

    def __init__(self, width: int, height: int, warmup_s: float = 1.0) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Largura e altura devem ser positivas.")
        if not math.isfinite(warmup_s) or warmup_s < 0:
            raise ValueError("O tempo de aquecimento deve ser finito e não negativo.")
        try:
            from picamera2 import Picamera2
        except ImportError as exc:
            raise RuntimeError(
                "Picamera2 não está disponível neste Python. Verifique primeiro a stack "
                "libcamera do sistema. No Raspberry Pi OS, use o pacote apt e um venv "
                "com --system-site-packages; no Ubuntu, confirme a compatibilidade da imagem."
            ) from exc

        self._camera = Picamera2()
        self._closed = False
        try:
            config = self._camera.create_preview_configuration(
                # libcamera BGR888 produces RGB bytes in the numpy array.
                # Keep the same RGB contract as the OpenCV/dataset adapters.
                main={"size": (width, height), "format": "BGR888"},
                buffer_count=2,
                queue=False,
            )
            self._camera.configure(config)
            self._camera.start()
            if warmup_s > 0:
                time.sleep(warmup_s)
        except BaseException:
            self._closed = True
            self._camera.close()
            raise
        self._sequence = 0

    def capture(self) -> Frame:
        image = self._camera.capture_array("main")
        self._sequence += 1
        return Frame(
            image=image,
            sequence=self._sequence,
            captured_monotonic_s=time.monotonic(),
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._camera.stop()
        finally:
            self._camera.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Captura uma foto da câmera do Raspberry, sem detector, serial ou janela gráfica."
    )
    parser.add_argument("--output", type=Path, default=Path("camera.jpg"), help="Arquivo .jpg ou .png")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--warmup", type=float, default=1.0, help="Aquecimento em segundos (padrão: 1)")
    args = parser.parse_args(argv)
    if args.width <= 0 or args.height <= 0:
        parser.error("--width e --height devem ser positivos")
    if not math.isfinite(args.warmup) or args.warmup < 0:
        parser.error("--warmup deve ser finito e não negativo")
    if args.output.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        parser.error("--output deve terminar em .jpg, .jpeg ou .png")

    try:
        from PIL import Image

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with closing(Picamera2Camera(args.width, args.height, args.warmup)) as camera:
            frame = camera.capture()
            Image.fromarray(frame.image).save(args.output)
        print(f"Imagem salva: {args.output.resolve()} ({frame.width}x{frame.height}, RGB)")
        return 0
    except ImportError as exc:
        print(f"ERRO: dependência ausente ({exc}). A gravação JPG/PNG requer Pillow.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Captura interrompida.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERRO na captura: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
