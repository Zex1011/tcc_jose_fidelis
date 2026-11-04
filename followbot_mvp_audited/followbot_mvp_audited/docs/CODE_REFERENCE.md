# Referencia de Codigo

Este documento detalha a funcao de cada parte relevante do codigo, com foco operacional.

## Nucleo da Aplicacao

- src/followbot/main.py
Funcao: ponto de entrada CLI.
Responsabilidades: parse de argumentos, leitura de configuracao, montagem dos adaptadores por backend e inicio do orquestrador.

- src/followbot/orchestrator.py
Funcao: coordenador sequencial do pipeline.
Responsabilidades: executar captura -> deteccao -> selecao -> controle -> comunicacao, medir tempos por etapa, logar cada ciclo e enviar STOP de seguranca em startup/shutdown.

- src/followbot/interfaces.py
Funcao: contratos abstratos da arquitetura.
Responsabilidades: definir assinaturas minimas para Camera, Detector, TargetSelector, Controller e CommunicationLink, permitindo troca de implementacao sem alterar o orquestrador.

- src/followbot/models.py
Funcao: modelos de dados comuns.
Responsabilidades: representar frame, bbox, deteccao, comando de movimento e resultado de comunicacao.

- src/followbot/config.py
Funcao: carregamento tipado da configuracao.
Responsabilidades: converter TOML em dataclasses imutaveis de configuracao por modulo.

- src/followbot/logging_setup.py
Funcao: configuracao de logs.
Responsabilidades: logger com saida em arquivo e console, incluindo rotacao.

- src/followbot/debug/visual_debug_recorder.py
Funcao: gravacao de debug visual por ciclo.
Responsabilidades: salvar frame anotado e metadados JSON para inspeção de detecções/alvo/comandos.

## Captura de Camera

- src/followbot/camera/picamera2_camera.py
Funcao: backend de camera para Raspberry Pi/libcamera.
Quando usar: alvo Raspberry com stack Picamera2 instalada no sistema.

- src/followbot/camera/opencv_camera.py
Funcao: backend de webcam via OpenCV.
Quando usar: notebook/desktop Linux com /dev/video*.

- src/followbot/camera/synthetic_camera.py
Funcao: gerar frames sinteticos para teste offline (matriz vazia em memória).
Quando usar: validação de pipeline sem hardware, testes unitários.

- src/followbot/camera/dataset_camera.py
Funcao: ler imagens estáticas de pasta em sequência.
Quando usar: benchmark determinístico de IA com dados reais sem hardware. Veja datasets/README.md.

## Visao e Deteccao

- src/followbot/vision/ultralytics_detector.py
Funcao: adaptador de inferencia YOLO.
Responsabilidades: carregar modelo, resolver classe person, rodar predict e converter saida para Detection.

- src/followbot/vision/synthetic_detector.py
Funcao: detector sintetico previsivel (bbox gerada por função seno do ciclo).
Quando usar: testes de controle/tracking sem IA real.

## Tracking e Controle

- src/followbot/tracking/nearest_bbox_selector.py
Funcao: manter alvo por proximidade de centro de bbox.
Responsabilidades: inicializar alvo e realizar associacao simples entre frames com tolerancia de distancia.

- src/followbot/control/bbox_controller.py
Funcao: transformar bbox em comando linear/angular.
Responsabilidades: controle proporcional com limites, deadbands e regra de seguranca para reduzir avanço com erro lateral alto.

## Comunicacao

- src/followbot/communication/serial_link.py
Funcao: transporte serial com protocolo CMD/ACK.
Responsabilidades: envio de comandos, timeout/retry e consolidacao de latencia/erro.

- src/followbot/communication/mock_link.py
Funcao: mock de comunicacao (sempre responde ACK).
Quando usar: testes de pipeline sem microcontrolador.

## Scripts Operacionais

- scripts/preflight.py
Funcao: diagnostico de ambiente.
Checa: Python, pacotes, config base, webcam opcional, IA opcional e modelo opcional.

- scripts/run_profile.py
Funcao: executor padronizado por perfil.
Beneficio: reduz erro humano de comando e garante caminho de config consistente.

- scripts/prepare_yolo_model.py
Funcao: preparar artefato de modelo.
Responsabilidades: carregar/baixar .pt via Ultralytics, exportar para NCNN e validar .param/.bin no diretorio final.

- scripts/list_video_devices.py
Funcao: diagnostico de camera no Linux.
Responsabilidades: listar /dev/video* e testar abertura por indice via OpenCV.

- scripts/prepare_dataset.py
Funcao: preparar dataset de imagens para benchmark.
Responsabilidades: fazer download de imagens de teste (COCO public) e validar.

- scripts/validate_dataset.py
Funcao: validar integridade de dataset.
Responsabilidades: checar pasta, listar imagens, verificar se sao legiveis, estatísticas.

- scripts/list_debug_runs.py
Funcao: navegador de histórico de debug visual.
Responsabilidades: listar todos os runs com timestamp, inspecionar conteúdo, abrir em file manager.

- scripts/export_yolo26_ncnn.py
Funcao: export simples/manual para NCNN.
Observacao: preferir prepare_yolo_model.py para fluxo completo automatizado.

- scripts/setup_test_ubuntu.sh e scripts/setup_test_windows.ps1
Funcao: bootstrap de ambiente de teste em um comando.

## Perfis de Configuracao

- configs/profiles/mock.toml
Objetivo: smoke test totalmente isolado de hardware e IA.

- configs/profiles/webcam.toml
Objetivo: validar captura real da camera sem IA real.

- configs/profiles/synthetic_ultralytics.toml
Objetivo: validar IA real sem camera fisica (detector + frames sintéticos).

- configs/profiles/synthetic_ultralytics_lowpower.toml
Objetivo: validar IA real em modo baixo consumo (imgsz menor, threads limitadas).

- configs/profiles/dataset_ultralytics.toml
Objetivo: **benchmark determinístico de IA com imagens reais estáticas** (não-tempo-real).

- configs/profiles/webcam_ultralytics.toml
Objetivo: validar camera real + IA real sem ESP (tempo-real).

- configs/profiles/webcam_ultralytics_debug.toml
Objetivo: validar camera real + IA real com artefatos visuais de diagnóstico por ciclo.

- configs/profiles/rpi.example.toml
Objetivo: base de integracao no hardware alvo Raspberry + serial.
