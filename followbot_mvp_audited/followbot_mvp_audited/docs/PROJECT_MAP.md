# Mapa do Projeto FollowBot MVP

Este documento explica, de forma objetiva, o que cada pasta e cada bloco principal do codigo faz.

## Visao Geral do Fluxo

```text
camera -> detector -> target_selector -> controller -> communication -> logs
```

A coordenacao deste fluxo fica no `Orchestrator`.

## Pastas da Raiz

- `src/followbot/`: codigo da aplicacao.
- `scripts/`: automacoes de setup, preflight, export e testes de ambiente.
- `configs/profiles/`: perfis TOML padronizados para cada cenário de execução.
- `models/`: artefatos de modelo para inferencia (por exemplo, NCNN exportado).
- `tests/`: testes unitarios de componentes centrais.
- `logs/`: logs de execucao do loop.
- `esp32_example/`: firmware base de referencia para protocolo serial.
- `constraints/`: pinos de versao para reproducibilidade parcial de instalacao.
- `docs/`: guias de organizacao e operacao do projeto.

## Codigo Principal em src/followbot

- `main.py`
Responsavel por carregar config, instanciar backends corretos e iniciar o loop.

- `orchestrator.py`
Executa o pipeline sequencial do MVP, registra timings e aplica politica de falha de comunicacao.

- `interfaces.py`
Define contratos abstratos (`Camera`, `Detector`, `TargetSelector`, `Controller`, `CommunicationLink`).

- `models.py`
Define estruturas compartilhadas (`Frame`, `Detection`, `BoundingBox`, `MotionCommand`, `CommunicationResult`).

- `config.py`
Leitura de TOML e mapeamento para dataclasses de configuracao.

- `logging_setup.py`
Configura log em arquivo + console com rotacao.

## Submodulos por Responsabilidade

- `camera/`
Implementacoes de captura de imagem.

- `camera/picamera2_camera.py`
Backend para Raspberry Pi Camera (Picamera2/libcamera).

- `camera/opencv_camera.py`
Backend para webcam USB/UVC via OpenCV.

- `camera/synthetic_camera.py`
Backend sintético para testes sem hardware.

- `vision/`
Deteccao de pessoas.

- `vision/ultralytics_detector.py`
Adapter do Ultralytics YOLO para o contrato interno de deteccao.

- `vision/synthetic_detector.py`
Detector sintético para validar pipeline sem IA real.

- `tracking/nearest_bbox_selector.py`
Seleciona o alvo atual com base na bbox anterior (heuristica de proximidade).

- `control/bbox_controller.py`
Converte bbox em comando de movimento (`linear`, `angular`) com ganhos proporcionais.

- `communication/serial_link.py`
Implementa protocolo serial com ACK/retry para ESP.

- `communication/mock_link.py`
Mock de comunicacao para testes sem microcontrolador.

## Configuracoes Principais

- `configs/profiles/mock.toml`
Fluxo 100% sem hardware (camera, detector e comunicacao simulados).

- `configs/profiles/webcam.toml`
Camera real de webcam + detector sintético + comunicacao mock.

- `configs/profiles/webcam_ultralytics.toml`
Camera real de webcam + detector real Ultralytics/NCNN + comunicacao mock.

- `configs/profiles/webcam_ultralytics_debug.toml`
Camera real + detector real com gravação de debug visual por ciclo.

- `configs/profiles/synthetic_ultralytics.toml`
Detector real Ultralytics/NCNN + camera sintética + comunicacao mock.

- `configs/profiles/rpi.example.toml`
Referencia para Raspberry + Picamera2 + serial.

## Scripts Recomendados

- `scripts/preflight.py`
Checa prerequisitos de ambiente e pode validar IA, webcam e modelo.

- `scripts/run_profile.py`
Runner unificado para executar perfis nomeados e reduzir erro de comando.

- `scripts/prepare_yolo_model.py`
Baixa/carrega modelo base YOLO e exporta para NCNN no caminho esperado pelo projeto.

- `scripts/list_video_devices.py`
Diagnóstico rápido de `/dev/video*` e teste de abertura por índice via OpenCV.

- `scripts/camera_sanity_check.py`
Detecta se a câmera está aberta mas entregando frames escuros/bloqueados antes do teste completo.

- `scripts/setup_test_ubuntu.sh`
Bootstrap de teste no Ubuntu com venv e smoke test mock.

- `scripts/setup_test_windows.ps1`
Bootstrap equivalente para Windows.

## Ordem de Teste Recomendada

1. `configs/profiles/mock.toml` para validar loop, tracking e controle sem hardware.
2. `configs/profiles/synthetic_ultralytics.toml` para validar detector real sem camera fisica.
3. `configs/profiles/webcam.toml` para validar camera real sem ESP.
4. `configs/profiles/rpi.example.toml` para integracao com serial/ESP no alvo.

## Observacoes de Organizacao

- Artefatos pesados de modelo devem permanecer em `models/` e fora de commits, exceto placeholders.
- Scripts operacionais ficam em `scripts/` para manter a raiz limpa.
- Documentacao de arquitetura/operacao fica em `docs/` com links no README principal.
