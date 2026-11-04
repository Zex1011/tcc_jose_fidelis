# Debug Visual e Histórico de Runs

O FollowBot captura frames anotados e metadados por ciclo para diagnóstico visual. Cada run é automaticamente **armazenada com timestamp** para não ser perdida.

## Estrutura de um Debug Run

Cada execução com `debug.enabled = true` cria uma pasta como:

```
logs/visual_debug/
└── 2026-08-24_18-03-01_webcam_ultralytics_debug/    (timestamp + profile name)
    ├── cycle_000001.ppm                             (imagem anotada em PPM)
    ├── cycle_000001.json                            (metadados do ciclo)
    ├── cycle_000002.ppm
    ├── cycle_000002.json
    └── ...
```

**Nenhum run é perdido**: cada execução cria uma pasta nova com timestamp.

## Habilitando Debug

### Opção 1: Editar profile TOML

```toml
[debug]
enabled = true
```

Então execute:

```bash
.venv/bin/python scripts/run_profile.py --config configs/profiles/webcam_ultralytics_debug.toml --max-cycles 50
```

### Opção 2: Copiar profile e habilitar

```bash
cp configs/profiles/webcam_ultralytics.toml configs/profiles/webcam_ultralytics_debug_custom.toml
# Edite para: [debug] enabled = true
.venv/bin/python scripts/run_profile.py --config configs/profiles/webcam_ultralytics_debug_custom.toml --max-cycles 50
```

## Navegando Histórico

### Listar todos os runs

```bash
.venv/bin/python scripts/list_debug_runs.py
```

Saída:

```
📁 Last 20 debug runs (most recent first):

#  Run Name                                   Cycles  Profile
───────────────────────────────────────────────────────────
1  2026-08-24_18-03-01_dataset_ultralytics   3       ?
2  webcam_ultralytics                        20      ?
```

### Inspecionar um run específico

```bash
.venv/bin/python scripts/list_debug_runs.py --open logs/visual_debug/2026-08-24_18-03-01_dataset_ultralytics
```

Isso mostra:
- Número de imagens (PPM) capturadas
- Número de metadatas (JSON)
- Amostra do primeiro ciclo (detecções, target, tempo total)

### Visualizar manualmente

```bash
ls logs/visual_debug/2026-08-24_18-03-01_dataset_ultralytics/
```

Imagens PPM podem ser abertas com:
- `feh`, `eog` (Eye of GNOME)
- `display` (ImageMagick)
- Conversor online PPM→PNG/JPEG

## Metadados de Ciclo

Cada arquivo `cycle_XXXXXX.json` contém:

```json
{
  "cycle": 1,
  "frame": {
    "sequence": 1,
    "width": 640,
    "height": 480
  },
  "detections": [
    {
      "bbox": {"x1": 200, "y1": 150, "x2": 400, "y2": 350},
      "confidence": 0.95,
      "class_id": 0,
      "class_name": "person",
      "track_id": 1
    }
  ],
  "target": {
    "bbox": {...},
    "confidence": 0.95,
    ...
  },
  "command": {
    "linear": 0.340,
    "angular": 0.120
  },
  "communication": {
    "sent_ok": true,
    "ack_ok": true,
    "elapsed_ms": 25.5
  },
  "timings_ms": {
    "detect_ms": 45.2,
    "track_ms": 2.1,
    "control_ms": 1.5,
    "comm_ms": 25.5,
    "total_ms": 75.3
  }
}
```

Útil para análise temporal:
- Quanto tempo a detecção levou?
- Quantas detecções houve por ciclo?
- O target foi mantido?
- Comandos (v, w) foram enviados?

## Organização de Pasta

Recomendação de fluxo:

```bash
# Teste 1: webcam real + synthetic detector
.venv/bin/python scripts/run_profile.py webcam --max-cycles 30
# Resultado: logs/visual_debug/ vazio (debug=false)

# Teste 2: webcam real + detector real com debug
cp configs/profiles/webcam_ultralytics.toml configs/profiles/webcam_ultralytics_debug.toml
# Edite: enabled = true
.venv/bin/python scripts/run_profile.py --config configs/profiles/webcam_ultralytics_debug.toml --max-cycles 50
# Resultado: logs/visual_debug/2026-08-24_XX-XX-XX_webcam_ultralytics_debug/

# Revisão posterior
.venv/bin/python scripts/list_debug_runs.py
.venv/bin/python scripts/list_debug_runs.py --open logs/visual_debug/2026-08-24_XX-XX-XX_webcam_ultralytics_debug/
```

## Troubleshooting

### "No debug runs found"

- Nenhum run com `debug.enabled = true` foi executado ainda.
- Verifique config TOML: `[debug] enabled = true`.
- Execute: `.venv/bin/python scripts/run_profile.py --config <seu_profile> --max-cycles 5`.

### Pasta logs/visual_debug não aparece

- Run foi executado com `enabled = false`.
- Ative debug e execute novamente.

### PPM não abre

- Use conversor: `ffmpeg -i cycle_000001.ppm cycle_000001.png`
- Ou visualize direto no VS Code com extensão PPM.

## Análise Avançada

Para processar metadatas em massa:

```python
import json
from pathlib import Path

run_dir = Path("logs/visual_debug/2026-08-24_18-03-01_dataset_ultralytics")
total_detect_ms = 0
cycle_count = 0

for json_file in sorted(run_dir.glob("cycle_*.json")):
    with json_file.open() as f:
        data = json.load(f)
    total_detect_ms += data["timings_ms"].get("detect_ms", 0)
    cycle_count += 1

print(f"Average detection time: {total_detect_ms / cycle_count:.1f}ms")
```

Isso te permite gerar gráficos de latência, overhead de tracking, etc.
