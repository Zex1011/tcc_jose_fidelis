from __future__ import annotations

from serial.tools import list_ports

ports = list(list_ports.comports())
if not ports:
    print("Nenhuma porta serial encontrada.")
else:
    for port in ports:
        print(f"{port.device}\t{port.description}\tVID:PID={port.vid}:{port.pid}")
