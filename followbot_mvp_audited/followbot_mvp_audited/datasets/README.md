# Datasets de Imagens para Teste

Este diretório armazena datasets de imagens reais para benchmark determinístico de detecção.

## Estrutura

```
datasets/
├── README.md (este arquivo)
├── sample/
│   ├── 0001.jpg
│   ├── 0002.jpg
│   └── ...
└── your_dataset/
    ├── 0001.jpg
    ├── 0002.jpg
    └── ...
```

## Propósito

Em vez de usar câmera em tempo real (`opencv`, `picamera2`) ou sintética (`synthetic`), você pode rodar testes com **imagens estáticas** de uma pasta. Isso permite:

- **Benchmark determinístico**: mesmas imagens sempre, sem variabilidade de captura.
- **Reprodutibilidade**: testes exatos do tempo de IA sem latência de câmera.
- **Isolamento**: medir custo real de detecção + tracking sem I/O de hardware.
- **Escalabilidade**: testar com 1.000+ imagens em loop.

## Como usar

1. Prepare imagens em qualquer pasta dentro de `datasets/`:
   - Formato: PNG, JPG, JPEG (OpenCV-compatível).
   - Nomeação: qualquer ordem; o backend ordena alfabeticamente.
   - Resolução: recomendado 640x480 ou maior (compatível com YOLO padrão).

2. Configure o profile TOML:

```toml
[camera]
backend = "dataset"
dataset_path = "datasets/sample"
width = 640
height = 480
warmup_s = 0.0

[detector]
backend = "ultralytics"
model_path = "models/yolo26n.ncnn"
imgsz = 320
confidence = 0.30
```

3. Execute:

```bash
.venv/bin/python scripts/run_profile.py --config configs/profiles/dataset_ultralytics.toml --max-cycles 50
```

O backend `dataset` lê imagens em ordem alfabética, recicla quando atinge o fim, e oferece timing determinístico para análise.

## Adicionando seu dataset

1. Coloque imagens em `datasets/<seu_nome>/`.
2. Valide com:
   ```bash
   .venv/bin/python scripts/validate_dataset.py --path datasets/<seu_nome>
   ```
3. Crie um profile novo copiando `dataset_ultralytics.toml` e atualizando `dataset_path`.

## Recomendações

- **Tamanho mínimo**: 10 imagens para smoke test; 100+ para benchmark estatístico.
- **Variedade**: incluir pessoas em diferentes ângulos, distâncias, iluminação.
- **Resolução**: manter consistente (ex: todas 640x480).
- **Ordem**: o backend lê em ordem alfabética; se quiser ordem específica, numere prefixo (0001, 0002, ...).

## Licença de dados

Se adicionar imagens públicas de datasets conhecidos (ex: COCO, Pascal VOC), documente a fonte e respeite a licença original.
