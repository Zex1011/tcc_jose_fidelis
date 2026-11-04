# Bibliotecas: Funcao e Racional de Escolha

Este documento registra o papel de cada biblioteca no projeto e o motivo de escolha.

## Dependencias Principais (runtime base)

- numpy
Funcao no projeto: manipulacao de arrays de imagem (Frame.image) e geracao de dados sinteticos.
Motivo da escolha: API madura, desempenho adequado em CPU e padrao de fato para dados numericos em Python.
Alternativas consideradas: listas Python puras (insuficiente para imagens), outras libs de tensor (desnecessarias no nucleo).

- pyserial
Funcao no projeto: comunicacao serial com ESP32.
Motivo da escolha: biblioteca consolidada, simples para timeout/retry e multiplataforma.
Alternativas consideradas: acesso serial manual via SO (mais fragil e menos portavel).

## Dependencias Opcionais

- ultralytics (extra ai)
Funcao no projeto: inferencia YOLO e pipeline de exportacao para formatos de deploy.
Motivo da escolha: reduz custo de integracao inicial, suporte amplo a modelos/export e boa experiencia para MVP.
Trade-off: cadeia de dependencias pesada (torch etc.), maior tempo de instalacao.

- ultralytics[export] (extra export)
Funcao no projeto: disponibilizar utilitarios e dependencias de export de modelo (incluindo NCNN/pnnx conforme necessario).
Motivo da escolha: manter exportacao no ecossistema da propria biblioteca usada na inferencia.

- opencv-python (extra webcam)
Funcao no projeto: acesso a webcam USB/integrada no Linux via VideoCapture.
Motivo da escolha: alta compatibilidade de dispositivos e API simples para captura de frames.
Trade-off: pacote relativamente grande.

- pytest (extra dev)
Funcao no projeto: execucao de testes unitarios.
Motivo da escolha: ecossistema consolidado, sintaxe objetiva e boa integracao com CI/local.

## Dependencias de Plataforma

- picamera2 (instalada via apt no Raspberry Pi OS)
Funcao no projeto: backend nativo de camera no Raspberry com libcamera.
Motivo da escolha: caminho recomendado para hardware de camera no ecossistema Raspberry atual.
Observacao: nao e dependencia padrao de PC/notebook; por isso existe backend OpenCV para desktop.

## Bibliotecas da Stdlib com papel relevante

- tomllib
Funcao no projeto: leitura de arquivos TOML de configuracao.
Motivo da escolha: padrao da linguagem a partir de Python 3.11, sem dependencia externa.

- argparse
Funcao no projeto: CLIs dos scripts e do entrypoint principal.
Motivo da escolha: stdlib robusta para interface de linha de comando.

- dataclasses
Funcao no projeto: modelagem de configuracao e dados com tipos claros.
Motivo da escolha: simplicidade, legibilidade e menor boilerplate.

- logging
Funcao no projeto: telemetria de execucao e diagnostico por ciclo.
Motivo da escolha: padrao Python, integracao nativa e baixo acoplamento.

## Diretriz de Escolha de Novas Bibliotecas

Ao introduzir nova dependencia, avaliar:

1. Impacto no tamanho/tempo de instalacao.
2. Compatibilidade com Raspberry Pi Zero 2 e Linux desktop.
3. Facilidade de mock para testes offline.
4. Maturidade da comunidade/manutencao.
5. Custo de lock de versao e reproducibilidade.
