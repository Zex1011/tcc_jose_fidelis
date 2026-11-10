# Arquitetura de software

As figuras editáveis de blocos, classes e estados estão no [guia de diagramas do RPi](../../Documentacao/diagramas/software_rpi/README.md). O diagrama de estados previsto inclui busca por rotação; o guia distingue essa proposta do comportamento atual do código.

Para um mapa rápido de pastas e responsabilidades, veja também `docs/PROJECT_MAP.md`.

## Objetivo central

O orquestrador deve conhecer **contratos**, não bibliotecas e hardware concretos.

```text
                   ┌────────────┐
                   │   Camera   │
                   └─────┬──────┘
                         │ Frame
                         ▼
                   ┌────────────┐
                   │  Detector  │
                   └─────┬──────┘
                         │ List[Detection]
                         ▼
                  ┌──────────────┐
                  │TargetSelector│
                  └──────┬───────┘
                         │ Detection | None
                         ▼
                   ┌────────────┐
                   │ Controller │
                   └─────┬──────┘
                         │ MotionCommand(v,w)
                         ▼
                 ┌─────────────────┐
                 │CommunicationLink│
                 └────────┬────────┘
                          │ USB/Serial
                          ▼
                         ESP
```

O `Orchestrator` apenas executa essas etapas na ordem correta.

O transporte USB/Serial do exemplo acima continua nos perfis atuais. A
[shield Juca/Pi R02](../../Hardware/Juca_PiZero2_Shield/README.md) prevê UART pelo
header, com integração física pendente. O backend serial já permite configurar
a porta, preservando o contrato `CommunicationLink` e o restante do pipeline.

## Modelos compartilhados

Arquivo: `src/followbot/models.py`

### Frame

Contém:

- array numpy da imagem;
- número de sequência;
- timestamp monotônico;
- propriedades `width` e `height`.

### BoundingBox

Formato escolhido:

```text
(x1, y1, x2, y2)
```

em pixels da imagem original entregue ao detector.

Ela calcula:

- largura;
- altura;
- área;
- centro;
- distância normalizada entre centros.

### Detection

```text
bbox
confidence
class_id
class_name
track_id | None
```

`track_id` é opcional porque o detector inicial não precisa fornecer identidade temporal.

### MotionCommand

```text
linear
angular
```

Possui também `MotionCommand.stop()`.

### CommunicationResult

Guarda:

- sucesso;
- sequência;
- resposta recebida;
- número de tentativas;
- latência;
- erro.

## Interfaces

Arquivo: `src/followbot/interfaces.py`

### Camera

```text
capture() -> Frame
close()
```

### Detector

```text
detect(Frame) -> List[Detection]
close()
```

### TargetSelector

```text
select(List[Detection], Frame) -> Detection | None
reset()
```

O estado temporal fica dentro deste módulo, não no Main.

### Controller

```text
compute(Detection, Frame) -> MotionCommand
```

### CommunicationLink

```text
send(MotionCommand) -> CommunicationResult
close()
```

## Módulo de câmera

### Picamera2Camera

Arquivo:

`src/followbot/camera/picamera2_camera.py`

Responsabilidade única:

```text
Picamera2 -> ndarray -> Frame
```

A câmera permanece inicializada durante o programa, mas uma nova imagem só é entregue ao restante do sistema quando `capture()` é chamado.

Configuração inicial:

```text
BGR888 (configuração libcamera; array entregue em RGB)
640 x 480
2 buffers
queue=False
```

A resolução é configurável.

### SyntheticCamera

Permite executar o software sem periférico físico.

## Módulo de IA

### UltralyticsPersonDetector

Arquivo:

`src/followbot/vision/ultralytics_detector.py`

Responsabilidades:

1. carregar o modelo;
2. descobrir o `class_id` correspondente a `person` pelo nome;
3. executar inferência em uma imagem;
4. filtrar a classe desejada;
5. traduzir a resposta da biblioteca para `Detection`.

Nenhum outro módulo acessa objetos internos da Ultralytics.

Consequência:

```text
Ultralytics hoje
      ↓
NCNN C++ amanhã
```

pode manter a mesma saída do módulo.

## Módulo de tracking

### NearestBBoxSelector

Arquivo:

`src/followbot/tracking/nearest_bbox_selector.py`

Estado interno:

```text
_previous: Detection | None
_missed: int
```

Primeira seleção configurável:

```text
first
largest
center
confidence
```

Configuração inicial usa `first`, preservando a hipótese original do projeto.

Depois:

```text
argmin distância(centro bbox anterior, centro bbox atual)
```

Se a distância for maior que o limite, o alvo é rejeitado.

Não é um identificador persistente verdadeiro. É uma associação geométrica simples.

## Módulo de controle

### BBoxProportionalController

Arquivo:

`src/followbot/control/bbox_controller.py`

Entrada:

```text
bbox da pessoa + tamanho do frame
```

Saída:

```text
linear, angular
```

### Erro horizontal

```text
ex = (centro_imagem - centro_alvo) / meia_largura
```

Faixa aproximadamente:

```text
[-1, +1]
```

Controle:

```text
w = Kpw * ex
```

com deadband e saturação.

### Erro de distância visual

```text
h = altura_bbox / altura_imagem
ed = h_desejado - h
v = Kpv * ed
```

Sem marcha a ré, erros negativos são truncados em zero.

### Acoplamento mínimo direção/avanço

O cálculo de `v` é reduzido quando `|ex|` cresce.

Isso não é um PID multivariável; é apenas uma regra de segurança simples para evitar avançar forte com o alvo próximo da borda da câmera.

## Comunicação

### SerialCommunicationLink

Arquivo:

`src/followbot/communication/serial_link.py`

Responsabilidades:

- serializar comando;
- incrementar sequência;
- enviar bytes;
- esperar ACK correspondente;
- repetir em timeout;
- devolver resultado estruturado.

A transformação de `(v,w)` em PWM **não pertence ao Raspberry** nesta arquitetura.

## Logger

Arquivo:

`src/followbot/logging_setup.py`

O logger possui saída independente do pipeline.

Atualmente:

```text
FollowBot logger
   ├── console
   └── JSONL rotativo
```

Futuro:

```text
   └── Bluetooth handler
```

O arquivo usa rotação para evitar crescimento ilimitado.

## Orquestrador

Arquivo:

`src/followbot/orchestrator.py`

Fluxo real:

```text
1. envia STOP inicial
2. captura frame
3. mede tempo de captura
4. detecta pessoas
5. mede tempo de inferência
6. seleciona alvo
7. mede tempo de tracking
8. calcula comando ou STOP
9. mede tempo de controle
10. envia comando
11. mede tempo de comunicação
12. registra o ciclo completo
13. repete
```

Em saída normal ou exceção:

```text
tenta enviar STOP
fecha detector
fecha câmera
fecha comunicação
```

## Main / composição

Arquivo:

`src/followbot/main.py`

O `main.py` lê TOML e escolhe as implementações concretas.

Exemplo:

```text
camera.backend = picamera2
       ↓
Picamera2Camera
```

O `Orchestrator` não contém nenhum `if Raspberry`, `if YOLO` ou `if serial`.

Essa é a principal propriedade que permite trocar hardware sem reescrever a lógica do sistema.
