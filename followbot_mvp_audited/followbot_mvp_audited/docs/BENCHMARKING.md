# Benchmarking e Performance do FollowBot

> **Objetivo**: Entender o custo real de detecção e como ele escala para Raspberry Pi Zero 2.

## Por que medir?

O custo computacional de IA (detecção YOLO) é a **maior variável** na latência total do sistema:

- **Captura**: ~10-30ms (negligenciável)
- **Detecção**: ~100-500ms ⚠️ (dominante)
- **Tracking + Controle**: ~10-30ms
- **Comunicação**: ~50-100ms

Se detectar 1 pessoa leva 300ms e temos ~100ms de orçamento para loop de 10 Hz, **não funciona em Raspberry Pi Zero 2 com imgsz=320**.

## Estratégia de medição

### 1. Isolate Detection Cost

Use `dataset_ultralytics.toml` com dados reais:

```bash
.venv/bin/python scripts/prepare_dataset.py --target datasets/sample
.venv/bin/python scripts/run_profile.py --config configs/profiles/dataset_ultralytics.toml --max-cycles 100
```

Isso roda a mesma sequência de imagens 100 vezes, **isolando detecção** de variabilidade de câmera ou hardware.

Exemplo de saída:

```
cycle=1  det=2 target=yes v=0.340 w=0.120 ack=yes total=739.7ms    <- carrega modelo
cycle=2  det=2 target=yes v=0.340 w=0.120 ack=yes total=318.4ms    <- tempo típico de detecção
cycle=3  det=2 target=yes v=0.340 w=0.120 ack=yes total=320.1ms
...
cycle=100 det=2 target=yes v=0.340 w=0.120 ack=yes total=319.8ms
```

**Tempo típico de ciclo** = média dos últimos 90 ciclos (ex: 320ms).

### 2. Comparar Estratégias de Redução

Teste imgsz menor:

```bash
# Copy profile and adjust detector.imgsz
cp configs/profiles/dataset_ultralytics.toml configs/profiles/dataset_ultralytics_224.toml
# Edit: detector.imgsz = 224
.venv/bin/python scripts/run_profile.py --config configs/profiles/dataset_ultralytics_224.toml --max-cycles 100
```

Ganho esperado: imgsz 320 → 224 reduz ~30-40% de tempo.

### 3. Thread Limiting para Estimativa Pi Zero 2

Raspberry Pi Zero 2 tem 4 cores ARM Cortex-A53, mas **ambiente real é restrito**.

Simule com:

```bash
.venv/bin/python scripts/run_profile.py --config configs/profiles/dataset_ultralytics.toml --limit-threads 1 --max-cycles 100
```

Isso força `OMP_NUM_THREADS=1` e reduz concorrência de NumPy/OpenBLAS.

Ganho esperado: 4-core → 1-core aumenta ~2-3x tempo.

## Dados Reais

Para benchmarking final com dados **reais** (não retângulos sintéticos), siga:

1. Baixe dataset COCO val2017 (real-world com pessoas):
   ```bash
   .venv/bin/python scripts/prepare_dataset.py --target datasets/coco_sample --count 50
   ```

2. Crie profile customizado:
   ```toml
   [camera]
   backend = "dataset"
   dataset_path = "datasets/coco_sample"
   width = 640
   height = 480
   
   [detector]
   backend = "ultralytics"
   model_path = "models/yolo26n_ncnn_model"
   imgsz = 320
   confidence = 0.30
   ```

3. Execute:
   ```bash
   .venv/bin/python scripts/run_profile.py --config configs/profiles/dataset_coco.toml --max-cycles 100 --limit-threads 1
   ```

## Matriz de Benchmark

Tabela esperada (exemplo):

| Cenário | imgsz | Threads | Tempo/Ciclo | Viável em Pi Zero 2? |
|---------|-------|---------|------------|----------------------|
| Desktop | 320 | 8 | ~250ms | ✅ (mas sobra) |
| Desktop | 224 | 8 | ~100ms | ✅ (confortável) |
| Pi Zero 2 | 320 | 1 | ~1500ms | ❌ (muito lento) |
| Pi Zero 2 | 224 | 1 | ~600ms | ❌ (ainda lento) |
| Pi Zero 2 | 160 | 1 | ~200ms | ✅ (viável) |

(Números são ilustrativos; medir no seu ambiente)

## Interpretação

- **< 300ms/ciclo**: viável em 1-2 Hz em Pi Zero 2.
- **300-500ms/ciclo**: viável em 1 Hz, margem apertada.
- **> 500ms/ciclo**: repense modelo (imgsz menor, detector alternativo, etc).

## Próximas Decisões

Com dados deste benchmark, você pode:

1. **Aceitar latência**: se 200ms/ciclo for aceitável, use `imgsz=160`.
2. **Trocar modelo**: experimentar `yolo11n` (menor que `yolo26n`).
3. **Rodar em CPU/GPU externa**: Raspberry Pi envia frames para servidor, recebe detecções.

## Monitoramento em Produção

Uma vez no hardware, use logs para monitorar:

```bash
grep "cycle=" logs/followbot.log | awk '{print $NF}' | sort -n | tail -1
# Mostra ciclo mais lento
```

Ou use dashboard/visualização de tempos ao longo do tempo.
