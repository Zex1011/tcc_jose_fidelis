# Testing Playbook

Objetivo: executar testes de forma repetível e com menor chance de erro operacional.

## Perfis padronizados

Os perfis ficam em `configs/profiles/`:

- `mock.toml`: sem hardware, sem IA real.
- `webcam.toml`: webcam real + detector sintético.
- `webcam_ultralytics.toml`: webcam real + detector real Ultralytics/NCNN.
- `webcam_ultralytics_debug.toml`: webcam real + detector real + gravação visual de debug.
- `synthetic_ultralytics.toml`: IA real + câmera sintética.
- `synthetic_ultralytics_lowpower.toml`: IA real em modo mais leve para ensaios de hardware fraco.
- `rpi.example.toml`: referência para Raspberry + serial.

## Runner único

Use sempre o runner para padronizar execução:

```bash
.venv/bin/python scripts/run_profile.py --list
.venv/bin/python scripts/run_profile.py mock --max-cycles 20
.venv/bin/python scripts/run_profile.py synthetic_ultralytics --max-cycles 20
```

Também é possível usar config explícita:

```bash
.venv/bin/python scripts/run_profile.py --config configs/profiles/webcam.toml --max-cycles 20
```

### 4) Pipeline completo em notebook (webcam integrada + modelo real, sem ESP)

```bash
.venv/bin/python scripts/preflight.py --require-webcam --require-ai --require-model
.venv/bin/python scripts/run_profile.py webcam_ultralytics --max-cycles 20
```

### 5) Pipeline completo com debug visual

```bash
.venv/bin/python scripts/preflight.py --require-webcam --require-ai --require-model
.venv/bin/python scripts/run_profile.py webcam_ultralytics_debug --max-cycles 30
```

Saída de debug visual:

- `logs/visual_debug/webcam_ultralytics/cycle_000001.ppm`
- `logs/visual_debug/webcam_ultralytics/cycle_000001.json`

Interpretação rápida:

- caixas verdes: todas as detecções;
- caixa vermelha: alvo selecionado;
- cruz no centro: referência para erro lateral do controle.

## Medição e Limite de Recursos

Medir consumo de CPU, RAM e tempo total:

```bash
/usr/bin/time -v .venv/bin/python scripts/run_profile.py synthetic_ultralytics --max-cycles 120
```

Simular ambiente mais restrito (threads limitadas):

```bash
/usr/bin/time -v .venv/bin/python scripts/run_profile.py synthetic_ultralytics_lowpower --limit-threads 1 --max-cycles 120
```

Indicadores-chave para comparar execuções:

- `Elapsed (wall clock) time`
- `Percent of CPU this job got`
- `Maximum resident set size`

## Checklist por cenário

### 1) Pipeline base sem hardware

```bash
.venv/bin/python scripts/preflight.py
.venv/bin/python scripts/run_profile.py mock --max-cycles 20
```

### 2) Pipeline com modelo real (sem câmera física)

```bash
.venv/bin/python scripts/preflight.py --require-ai --require-model
.venv/bin/python scripts/run_profile.py synthetic_ultralytics --max-cycles 20
```

### 3) Pipeline com webcam física

```bash
.venv/bin/python scripts/preflight.py --require-webcam
.venv/bin/python scripts/list_video_devices.py
.venv/bin/python scripts/camera_sanity_check.py --index 0
.venv/bin/python scripts/run_profile.py webcam --max-cycles 20
```

Observações:

- Webcam integrada de notebook funciona normalmente (não precisa ser webcam USB externa).
- Em alguns ambientes de terminal sandbox, `/dev/video*` pode não aparecer mesmo com câmera presente no host.
- Se isso ocorrer, execute o teste em terminal com acesso direto ao host/dispositivos.
- Se os frames ficarem pretos ou com ícone de câmera bloqueada, rode `scripts/camera_sanity_check.py` e destrave o privacy shutter/permissão de câmera do sistema.

## Preparar modelo (uma vez por ambiente)

```bash
.venv/bin/python scripts/prepare_yolo_model.py --model yolo26n.pt --imgsz 320
```

Validação:

```bash
.venv/bin/python scripts/preflight.py --require-ai --require-model
```

## Observações operacionais

- Execute comandos na raiz do repositório.
- Em Linux, preferir venv criada com `python3.12 -m venv --copies .venv` neste host.
- Se webcam não abrir, ajuste `device_index` no perfil `webcam.toml`.
- Em integração com ESP, testar serial com script de smoke antes do loop completo.
