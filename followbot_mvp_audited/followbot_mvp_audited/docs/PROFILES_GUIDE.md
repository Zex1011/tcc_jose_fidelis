# Guia de Perfis de Configuracao

Este guia explica como funciona `configs/profiles/`, como os perfis sao carregados e como criar novos perfis com seguranca.

## O que e um profile

Um profile e um arquivo TOML que descreve um cenario de execucao do FollowBot.

Exemplos:

- `mock.toml`: sem hardware e sem IA real.
- `webcam.toml`: camera real + detector sintetico.
- `webcam_ultralytics.toml`: camera real + detector real.
- `webcam_ultralytics_debug.toml`: igual ao anterior, com debug visual habilitado.
- `synthetic_ultralytics.toml`: IA real sem camera fisica.
- `synthetic_ultralytics_lowpower.toml`: IA real em modo mais leve.
- `rpi.example.toml`: referencia para Raspberry + serial.

## Onde os perfis entram no fluxo

Fluxo de carga:

1. `scripts/run_profile.py` recebe o nome do profile.
2. Ele traduz o nome para um arquivo em `configs/profiles/`.
3. Executa `python -m followbot.main --config <arquivo>`.
4. `followbot.main` chama `load_config`.
5. `load_config` converte TOML em dataclasses tipadas.
6. `build_orchestrator` cria os backends com base nesses campos.

## Como usar no terminal

Listar perfis:

```bash
.venv/bin/python scripts/run_profile.py --list
```

Rodar por nome:

```bash
.venv/bin/python scripts/run_profile.py webcam_ultralytics --max-cycles 20
```

Rodar por caminho explicito:

```bash
.venv/bin/python scripts/run_profile.py --config configs/profiles/webcam.toml --max-cycles 20
```

## Precedencia e opcoes importantes

- Se passar `--config`, ele tem precedencia sobre o nome do profile.
- `--max-cycles` limita quantos ciclos o orquestrador executa.
- `--limit-threads N` aplica limite de threads no processo (OMP/BLAS/NumExpr).

Variaveis setadas por `--limit-threads`:

- `OMP_NUM_THREADS`
- `OPENBLAS_NUM_THREADS`
- `MKL_NUM_THREADS`
- `NUMEXPR_NUM_THREADS`

## Backends: origem dos dados (real vs. sintetico)

### Camera

- **synthetic**: gera frame preto em memória (matriz NumPy de zeros). Nao lê arquivo ou dataset. Usado para testes de lógica pura.
- **opencv**: captura de webcam USB/UVC em tempo real via `/dev/video*`. Requer hardware.
- **picamera2**: captura via Raspberry Pi Camera (libcamera). Requer hardware Pi + câmera.
- **dataset**: lê imagens estáticas de uma pasta em sequência. Útil para benchmark determinístico de IA em dados reais sem hardware. Veja `datasets/README.md`.

### Detector

- **synthetic**: gera uma bbox com posição/tamanho em função senoidal do ciclo. Nao toca na imagem real. Permite testar pipeline (tracking, controle, comunicação) sem IA.
- **ultralytics**: carrega modelo YOLO (NCNN pré-exportado ou .pt) e roda inferência real. Tempo depende da imagem e do `imgsz`.

### Combinações comuns de impacto no perfil

| Profile | Camera | Detector | Objetivo |
|---------|--------|----------|----------|
| `mock.toml` | synthetic (zero em memória) | synthetic (função seno) | Validar pipeline sem qualquer I/O real |
| `webcam.toml` | opencv (real-time) | synthetic | Validar captura real sem custo de IA |
| `webcam_ultralytics.toml` | opencv (real-time) | ultralytics (real IA) | Teste completo com hardware |
| `synthetic_ultralytics.toml` | synthetic (zero em memória) | ultralytics (real IA) | Benchmark de IA com dados sintéticos |
| `dataset_ultralytics.toml` | dataset (imagens estáticas) | ultralytics (real IA) | **Benchmark determinístico de IA em dados reais** |

## Estrutura de um profile

Secoes comuns:

- `[camera]`: backend (`synthetic`, `opencv`, `picamera2`, `dataset`), resolucao, `device_index` (opencv), `dataset_path` (dataset), `warmup_s`.
- `[detector]`: backend (`synthetic` ou `ultralytics`), `model_path`, `imgsz`, `confidence`.
- `[tracking]`: estrategia inicial e tolerancias.
- `[control]`: ganhos, limites e deadbands.
- `[communication]`: `mock` ou `serial`, com timeouts/retries.
- `[logging]`: arquivo, nivel e rotacao.
- `[system]`: politica de abortar em falha de comunicacao.
- `[debug]` (opcional): captura visual por ciclo.

## Como criar um novo profile

Passo recomendado:

1. Copie um profile existente parecido com seu caso.
2. Ajuste apenas os campos necessarios.
3. Rode preflight com flags do cenario.
4. Rode poucos ciclos (`--max-cycles 5`) para smoke test.
5. Se estiver tudo certo, aumente ciclos.

## Exemplo rapido de profile novo

Objetivo: webcam + modelo + menos carga.

- Base: `webcam_ultralytics.toml`
- Ajustes iniciais:
  - `detector.imgsz = 224`
  - manter `confidence = 0.30`
- Execucao:

```bash
.venv/bin/python scripts/run_profile.py --config configs/profiles/webcam_ultralytics.toml --limit-threads 1 --max-cycles 20
```

## Benchmark determinístico com dataset real

Para medir o impacto real de detecção com dados reais (não tempo-real), use o profile `dataset_ultralytics.toml`.

Primeira vez:

```bash
.venv/bin/python scripts/prepare_dataset.py --target datasets/sample
.venv/bin/python scripts/validate_dataset.py --path datasets/sample
```

Depois, execute:

```bash
.venv/bin/python scripts/run_profile.py --config configs/profiles/dataset_ultralytics.toml --max-cycles 100
```

Isso roda 100 ciclos com as mesmas imagens em loop, oferecendo:
- **Tempo determinístico**: sem variabilidade de captura de câmera.
- **Isolamento de IA**: mede apenas o tempo de detecção + tracking + controle.
- **Reprodutibilidade**: mesmos ciclos, mesmos tempos.

Com dataset real (COCO ou suas próprias imagens), você vê o custo real de detecção, essencial para planejar hardware como Raspberry Pi Zero 2.

## Validacao antes de rodar

Checklist rapido:

```bash
.venv/bin/python scripts/preflight.py --require-webcam --require-ai --require-model
```

Se webcam estiver com frame escuro/bloqueado:

```bash
.venv/bin/python scripts/camera_sanity_check.py --index 0
```

Para validar dataset:

```bash
.venv/bin/python scripts/validate_dataset.py --path datasets/seu_dataset
```

## Erros comuns

- "perfil desconhecido": nome nao existe no mapeamento de `scripts/run_profile.py`.
- "arquivo de config nao encontrado": caminho incorreto.
- `det=0` constante com webcam: verificar camera bloqueada/escura.
- `DatasetCamera: No images found`: pasta datasets vazia; rode `prepare_dataset.py` ou adicione imagens manualmente.
- Exit 139 (segfault): normalmente problema em runtime nativo da stack de IA; repetir com `--limit-threads 1` e comparar estabilidade.
