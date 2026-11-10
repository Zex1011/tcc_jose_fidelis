# FollowBot MVP — Raspberry Pi + ESP

> **Documento consolidado/canônico:** veja [`FORMULACAO_PROJETO_COMPLETA.md`](FORMULACAO_PROJETO_COMPLETA.md).
> **Instalação/teste em Windows e Ubuntu:** veja [`INSTALL_TEST.md`](INSTALL_TEST.md).
> **Mapa rápido de pastas e responsabilidades:** veja [`docs/PROJECT_MAP.md`](docs/PROJECT_MAP.md).
> **Índice de documentação:** veja [`docs/INDEX.md`](docs/INDEX.md).
> Há scripts automáticos para ambos os sistemas e um teste serial que envia apenas STOP.

## Catálogo de Documentação

- Índice geral de documentos: [`docs/INDEX.md`](docs/INDEX.md)
- Arquitetura e contratos: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Mapa de pastas e responsabilidades: [`docs/PROJECT_MAP.md`](docs/PROJECT_MAP.md)
- Função de cada módulo e script: [`docs/CODE_REFERENCE.md`](docs/CODE_REFERENCE.md)
- Função de cada biblioteca e motivo de escolha: [`docs/LIBRARIES_RATIONALE.md`](docs/LIBRARIES_RATIONALE.md)
- Guia operacional de testes por perfil: [`docs/TESTING_PLAYBOOK.md`](docs/TESTING_PLAYBOOK.md)
- Guia de funcionamento dos profiles: [`docs/PROFILES_GUIDE.md`](docs/PROFILES_GUIDE.md)

Perfil de debug visual disponível: `webcam_ultralytics_debug`.


Protótipo modular de carrinho seguidor de pessoas.

A implementação segue deliberadamente um pipeline **sequencial e síncrono**:

```text
capturar imagem
    -> detectar pessoas
    -> escolher a pessoa seguida
    -> calcular (v, w)
    -> enviar ao ESP
    -> receber ACK
    -> registrar logs
    -> capturar próxima imagem
```

O objetivo desta versão é validar o sistema completo antes de introduzir concorrência, filas, ROS, PID, trackers avançados ou otimizações em C++.


## Hardware-alvo consolidado

Estado atual das decisões do MVP:

A placa de interligação prevista com o carrinho está em
[Hardware/Juca_PiZero2_Shield](../../Hardware/Juca_PiZero2_Shield/README.md).
A R02 recebida foi preservada em 04/11/2026, com análise elétrica/mecânica e
pendências para adaptações. Sua ligação usa UART pelo header do Pi; a integração
física e o firmware do carrinho ainda precisam ser validados.

```text
Raspberry Pi Zero 2
ESP32
carrinho diferencial: 2 rodas motrizes + apoio
controle inicial em malha aberta por referências (v, w)
meta inicial: ~1 ciclo/s ou mais
```

A câmera possui a marcação `UC436` registrada no projeto. Em 07/10/2026, o driver
identificou o sensor **OV5647** e a captura CSI foi validada com Picamera2 no Pi.
O código também oferece OpenCV para câmeras USB/UVC.

Equipamento confirmado em outubro de 2026: **Raspberry Pi Zero 2 W**, Ubuntu
24.04.4 LTS aarch64, Python 3.12.3 e 409 MiB de RAM utilizável pelo sistema.
A câmera está conectada diretamente ao Raspberry. A imagem Ubuntu precisou de
uma correção isolada do libcamera e de ajustes de ambiente Python. Veja o roteiro em
[`INSTALL_TEST.md`](INSTALL_TEST.md#8-teste-no-raspberry-pi-real).

Com a stack Picamera2 funcional e o pacote instalado no Pi, capture uma imagem
sem iniciar o detector ou a comunicação com o ESP:

```bash
cd ~/followbot
source scripts/env_camera_ubuntu2404.sh  # preparação específica deste Ubuntu
python -m followbot.camera.picamera2_camera --output camera.jpg
```

O módulo tem seu próprio `main()` e reutiliza `Picamera2Camera.capture()`.
Aceita `--width`, `--height`, `--warmup` e saída JPG/PNG (Pillow), sem janela
gráfica. Para um teste posterior de câmera + YOLO com comunicação simulada:

```bash
python scripts/run_profile.py rpi_vision --max-cycles 20
```

Esse perfil exige modelo e runtime de IA já instalados e validados no Pi;
o perfil `rpi` existente usa serial real. As imagens internas (`Frame.image`)
são RGB; o adaptador Ultralytics converte para o BGR exigido pela entrada NumPy.

## Estrutura

```text
followbot_mvp/
├── configs/
│   └── profiles/
│       ├── mock.toml
│       ├── webcam.toml
│       ├── synthetic_ultralytics.toml
│       └── rpi.example.toml
├── pyproject.toml
├── README.md
├── ARCHITECTURE.md
├── SERIAL_PROTOCOL.md
├── PENDING_DECISIONS.md
├── VALIDATION_PLAN.md
├── esp32_example/
│   └── esp32_velocity_receiver.ino
├── scripts/
│   ├── run_profile.py
│   ├── prepare_yolo_model.py
│   ├── list_video_devices.py
│   └── export_yolo26_ncnn.py
├── src/followbot/
│   ├── main.py
│   ├── orchestrator.py
│   ├── interfaces.py
│   ├── models.py
│   ├── config.py
│   ├── logging_setup.py
│   ├── camera/
│   ├── vision/
│   ├── tracking/
│   ├── control/
│   └── communication/
└── tests/
    └── test_core.py
```

## 1. Testar agora, sem Raspberry, câmera, YOLO ou ESP

Requer Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/run_profile.py mock --max-cycles 20
```

No Linux, se o `python` do `.venv` ficar preso em versão antiga, crie com:

```bash
python3.12 -m venv --copies .venv
```

O modo mock usa:

- câmera sintética;
- uma pessoa sintética que muda de posição e tamanho;
- comunicação que sempre responde ACK.

Isso permite testar o **orquestrador real, tracker real, controlador real e logger real** sem hardware.

## 1.1. Teste básico com webcam USB (sem ESP e sem YOLO)

Para validar captura real da webcam com o restante ainda em modo seguro:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,webcam]'
python scripts/preflight.py --require-webcam
python scripts/list_video_devices.py
python scripts/camera_sanity_check.py --index 0
python scripts/run_profile.py webcam --max-cycles 20
```

Esse teste usa:

- câmera real via OpenCV (`backend = "opencv"`);
- detector sintético;
- comunicação mock (sem serial/ESP).

Se sua webcam não for `device_index = 0`, ajuste o índice em `configs/profiles/webcam.toml`.

## 1.2. Smoke test do pipeline com modelo (sem câmera física e sem ESP)

Para validar detecção real com Ultralytics/NCNN e manter o restante isolado de hardware:

```bash
source .venv/bin/activate
python scripts/prepare_yolo_model.py --model yolo26n.pt --imgsz 320
python scripts/preflight.py --require-ai --require-model
python scripts/run_profile.py synthetic_ultralytics --max-cycles 20
```

Esse teste usa:

- câmera sintética;
- detector real Ultralytics com modelo NCNN;
- comunicação mock.

Os perfis ficam em `configs/profiles/` e podem ser listados com:

```bash
python scripts/run_profile.py --list
```

Para ensaio de baixo consumo (aproximação inicial de hardware restrito):

```bash
python scripts/run_profile.py synthetic_ultralytics_lowpower --limit-threads 1 --max-cycles 120
```

Para gerar artefatos visuais de debug (frames anotados + JSON por ciclo):

```bash
python scripts/run_profile.py webcam_ultralytics_debug --max-cycles 30
```

Para executar os testes:

```bash
pip install -e '.[dev]'
pytest -q
```

## 2. Câmera no Raspberry Pi

A implementação inicial usa `Picamera2Camera`.

Para testes em PC/Linux com webcam USB/UVC, também existe `OpenCVCamera` com `backend = "opencv"`.

Ela inicia o periférico uma única vez e `capture()` solicita uma imagem apenas quando o orquestrador chega à etapa de captura.

A configuração usa `queue=False`, importante para a semântica desejada pelo projeto: não devolver deliberadamente um frame antigo que ficou enfileirado enquanto a IA estava processando o ciclo anterior.

Configuração inicial:

```toml
[camera]
backend = "picamera2"
width = 640
height = 480
warmup_s = 1.0
```

## 3. Detector de pessoas

A primeira implementação concreta é `UltralyticsPersonDetector`.

A interface do projeto é simplesmente:

```text
Frame -> List[Detection]
```

Cada `Detection` possui:

```text
bbox
confidence
class_id
class_name
track_id opcional
```

O `track_id` não é necessário no MVP. O detector é responsável apenas por dizer onde existem pessoas naquele frame.

### Modelo inicial proposto

Para começar os testes, a configuração aponta para:

```text
YOLO26n -> exportado para NCNN -> imgsz 320
```

Isso é uma **hipótese de implementação**, não uma conclusão de desempenho para Raspberry Pi Zero. O tempo e uso de memória precisam ser medidos no hardware real.

A resolução de inferência `320` também é propositalmente inicial. Ela troca precisão por velocidade e deve ser comparada com outras resoluções.

### Exportar em um computador de desenvolvimento

Preferencialmente não faça o trabalho de exportação no Pi Zero.

```bash
pip install ultralytics
python scripts/export_yolo26_ncnn.py --imgsz 320
```

Fluxo recomendado (download + export + organização no caminho esperado pelo projeto):

```bash
pip install -e '.[ai,export]'
python scripts/prepare_yolo_model.py --model yolo26n.pt --imgsz 320
python scripts/preflight.py --require-ai --require-model
```

Depois copie a pasta produzida para:

```text
models/yolo26n_ncnn_model/
```

O código do detector não muda se futuramente o backend for substituído por uma implementação NCNN nativa em C++.

## 4. Seleção / tracking inicial

O módulo `NearestBBoxSelector` implementa exatamente a primeira hipótese do projeto.

No primeiro frame:

```text
seleciona a primeira pessoa
```

Nos frames seguintes:

```text
calcula centro da bbox anterior
calcula centro de cada bbox atual
seleciona a mais próxima
```

A distância é normalizada pela diagonal da imagem para não depender diretamente da resolução.

Existe ainda um limite:

```toml
max_center_distance = 0.30
```

Se todas as pessoas estiverem muito longe da posição anterior, nenhuma delas é automaticamente assumida como sendo o mesmo alvo.

O carrinho para, mas o seletor mantém a bbox anterior por alguns ciclos:

```toml
max_missed_frames = 3
```

Isso permite tentar reencontrar a pessoa antes de esquecer completamente o alvo.

## 5. Controle a partir da bounding box

O `BBoxProportionalController` usa duas variáveis visuais.

### Direção

Calcula o deslocamento horizontal normalizado do centro da pessoa em relação ao centro da imagem.

```text
alvo à esquerda  -> +w
alvo central     -> w ~= 0
alvo à direita   -> -w
```

Antes de `angular_sign`, a convenção adotada é:

```text
+w = anti-horário / esquerda
-w = horário / direita
```

Se o ESP/mecânica usar a convenção oposta:

```toml
angular_sign = -1.0
```

### Distância visual

Nesta versão, a altura da bounding box é utilizada em vez da área.

```text
height_ratio = bbox_height / image_height
```

O controlador tenta manter:

```toml
desired_height_ratio = 0.55
```

Isto **não significa uma distância conhecida em metros**. Significa apenas manter aproximadamente o mesmo tamanho visual da pessoa na imagem.

### Regra adicional de segurança

O robô reduz a velocidade de avanço quando a pessoa está muito fora do centro e deixa de avançar quando o erro lateral ultrapassa um limite.

Assim, o controlador prefere primeiro apontar o carrinho para a pessoa e depois avançar.

Todos os ganhos e limites atuais são valores iniciais de calibração, não parâmetros finais.

## 6. Semântica de `v` e `w`

O Python transmite dois `float`:

```text
linear
angular
```

O núcleo do projeto não impõe a unidade.

Há duas possibilidades a decidir:

### A. Unidades físicas

```text
v = m/s
w = rad/s
```

É a alternativa mais limpa conceitualmente. Para realmente controlar velocidades físicas, o ESP deveria possuir informação da geometria do carrinho e, idealmente, feedback de encoders.

### B. Comandos normalizados

```text
v e w em uma faixa abstrata, por exemplo [-1, 1]
```

É mais simples para um protótipo sem encoders, mas não representa velocidade física medida.

Esta decisão ainda está aberta.

## 7. Comunicação serial

Os perfis atuais usam exemplos de serial USB (`/dev/ttyACM0`). A shield R02 prevê
UART nos pinos físicos 8/10 do Pi. `SerialCommunicationLink` já aceita uma porta
configurável, mas a UART no Ubuntu e os pinos/firmware da Juca ainda precisam de
integração. Consulte a [análise da shield](../../Hardware/Juca_PiZero2_Shield/analise/REVISAO_R02.md).

Protocolo inicial:

```text
Pi -> ESP
CMD,<seq>,<linear>,<angular>\n

ESP -> Pi
ACK,<seq>\n
```

Exemplo:

```text
CMD,42,0.28000,-0.37000
ACK,42
```

O número de sequência evita aceitar por engano um ACK antigo como confirmação do comando atual.

O Raspberry tenta novamente quando não recebe o ACK.

Depois das tentativas configuradas, a versão atual considera a falha fatal e encerra o loop.

## 8. Watchdog do ESP

O exemplo de firmware contém um watchdog de comando.

Se o Raspberry parar de enviar comandos durante certo período:

```text
ESP -> v=0, w=0
```

Isso protege contra casos como:

- processo Python travado;
- Raspberry desligado;
- cabo USB desconectado;
- falha grave de software.

O valor atual de `COMMAND_TIMEOUT_MS` é apenas provisório.

Ele deverá ser definido **depois de medir a distribuição do tempo do loop real**. Um timeout menor que um ciclo de IA legítimo faria o ESP parar o carrinho entre inferências.

## 9. Logs

A versão atual grava:

- console;
- arquivo JSON Lines rotativo.

Por ciclo são registrados:

- resolução e sequência do frame;
- todas as detecções;
- alvo escolhido;
- `(v, w)` calculados;
- ACK e latência de comunicação;
- tempo de captura;
- tempo de inferência;
- tempo de tracking;
- tempo de controle;
- tempo de comunicação;
- tempo total do ciclo.

Exemplo conceitual:

```json
{
  "message":"cycle",
  "data":{
    "cycle":12,
    "command":{"linear":0.21,"angular":-0.18},
    "timings_ms":{"inference":650.2,"cycle_total":663.1}
  }
}
```

Essa instrumentação permitirá decidir, com dados, onde otimizar.

### Bluetooth

Bluetooth ainda **não foi implementado** nesta versão.

A razão é que primeiro precisam ser definidos:

- modelo exato do Raspberry;
- dispositivo que receberá os logs (Android, notebook, outro microcontrolador etc.);
- BLE GATT vs RFCOMM/SPP.

O logger foi mantido separado do restante da aplicação, então adicionar outro `Handler` não exige alterar IA, tracking ou controle.

## 10. Raspberry Pi: instalação inicial

**Atenção ao sistema:** as instruções abaixo são para Raspberry Pi OS.
Para a imagem Ubuntu 24.04.4 atualmente no robô, siga primeiro o diagnóstico
específico de [`INSTALL_TEST.md`](INSTALL_TEST.md#8-teste-no-raspberry-pi-real).
A captura foi validada nesse equipamento com a preparação documentada;
o consumo de memória e o desempenho da IA continuam pendentes.

No Raspberry Pi OS, a instalação recomendada de Picamera2 é via pacotes do sistema. Para usar virtualenv junto com as bindings de `libcamera`, crie o ambiente herdando os pacotes do sistema.

Exemplo:

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-venv

python3 -m venv --system-site-packages .venv
source .venv/bin/activate

pip install -e .
pip install -e '.[ai]'
```

Teste a câmera separadamente antes do projeto:

```bash
rpicam-hello
```

Depois copie o modelo NCNN para `models/` e ajuste `config.rpi.example.toml`.

Para testar:

```bash
python -m followbot.main --config config.rpi.example.toml
```

**Não faça o primeiro teste com as rodas suspensas no chão sem uma forma física de interromper o robô.** Primeiro valide serial e comandos com os motores desabilitados ou o carrinho elevado.

## 11. Onde trocar hardware sem mexer no Main

O `main.py` apenas monta implementações a partir da configuração.

### Outra câmera

Implemente:

```python
class MinhaCamera(Camera):
    def capture(self) -> Frame:
        ...
```

### Outro detector

```python
class MeuDetector(Detector):
    def detect(self, frame: Frame) -> list[Detection]:
        ...
```

### Outro protocolo

```python
class MinhaComunicacao(CommunicationLink):
    def send(self, command: MotionCommand) -> CommunicationResult:
        ...
```

O `Orchestrator` continua igual.

## 12. Estado desta versão

Implementado:

- interfaces entre módulos;
- tipos de dados compartilhados;
- câmera Picamera2;
- câmera mock;
- YOLO via Ultralytics;
- detector mock;
- tracking por bbox mais próxima;
- controle P visual;
- comunicação serial com ACK e retry;
- comunicação mock;
- logs estruturados e tempos por etapa;
- STOP quando não há alvo;
- STOP no startup/shutdown;
- exemplo de watchdog no ESP;
- configuração TOML;
- testes unitários do tracking e controle;
- execução completa sem hardware.

Pendente ou dependente do hardware:

- confirmar Raspberry Pi Zero exato;
- benchmark real da IA;
- decidir unidades de `v/w`;
- implementar acionamento dos motores no ESP;
- definir geometria do carrinho;
- definir encoders ou controle aberto;
- calibrar controlador;
- calibrar watchdog;
- decidir estratégia Bluetooth;
- eventual backend NCNN nativo/C++;
- sensores de prevenção de colisão;
- tracker mais robusto se necessário.

Leia também `PENDING_DECISIONS.md` e `VALIDATION_PLAN.md`.

## 13. Resumir tempos dos logs

Depois de um teste real:

```bash
python scripts/summarize_logs.py logs/followbot.log
```

O script calcula média, mediana, p95, p99 e máximo de cada etapa do pipeline. Isso é útil tanto para decidir otimizações quanto para documentar resultados experimentais no TCC.
