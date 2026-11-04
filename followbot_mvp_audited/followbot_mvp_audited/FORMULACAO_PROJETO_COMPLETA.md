# FollowBot MVP — Formulação consolidada do projeto

**Versão documental:** 0.2 — consolidada após auditoria de instalação Windows/Ubuntu  
**Objetivo desta versão:** reunir em um único documento a arquitetura, decisões já tomadas, hipóteses ainda em validação, processo de instalação/teste, riscos e próximos passos do protótipo.

---

## 1. Visão geral

O **FollowBot** é um protótipo de carrinho autônomo capaz de **detectar uma pessoa por câmera, selecionar um alvo, estimar seu deslocamento relativo na imagem e gerar comandos de movimento `(v, w)` para segui-la**.

A arquitetura foi deliberadamente mantida simples e modular. O Raspberry executa visão, seleção do alvo, controle visual, comunicação e logging. Um ESP32 recebe referências de movimento via USB/Serial e faz a interface com o sistema de locomoção já existente do carrinho.

O foco do MVP não é resolver navegação autônoma completa. O objetivo é primeiro demonstrar, medir e documentar um pipeline funcional de **seguimento visual de pessoa**, com comportamento previsível, logs suficientes para análise e uma instalação reproduzível em ambiente de desenvolvimento.

Fluxo conceitual:

```text
Câmera
  -> detecção de pessoas
  -> seleção/reassociação do alvo
  -> cálculo de erro visual
  -> controlador gera (v, w)
  -> USB/Serial
  -> ESP32
  -> acionamento do carrinho
```

A versão atual executa esse fluxo de forma **sequencial e síncrona**. Concorrência, filas, ROS, controle distribuído e otimizações de baixo nível só devem ser considerados após medições demonstrarem necessidade.

---

## 2. Objetivo técnico do MVP

O MVP deve provar que é possível:

1. capturar imagens de forma contínua no Raspberry;
2. detectar pessoas em cada frame;
3. escolher e manter um alvo entre frames consecutivos com uma heurística simples;
4. calcular referências de velocidade a partir da posição e do tamanho aparente da pessoa;
5. transmitir essas referências ao ESP32 com confirmação de recebimento;
6. parar o robô quando o alvo desaparece ou quando ocorre falha crítica;
7. registrar tempos de cada etapa para medir desempenho real;
8. executar o software em modo totalmente simulado para validar o pipeline sem hardware;
9. possuir um procedimento de instalação e diagnóstico claro em Windows e Ubuntu;
10. atingir inicialmente uma frequência prática de aproximadamente **1 ciclo por segundo ou superior**, sujeita a benchmark no Raspberry Pi Zero 2.

A frequência de 1 Hz é uma **meta inicial de viabilidade**, não uma garantia arquitetural nem o limite desejável para a versão final.

---

## 3. Escopo do projeto

### Incluído no MVP

- aquisição de imagem;
- detecção da classe `person`;
- seleção inicial de um alvo;
- reassociação simples por proximidade de bounding boxes;
- geração de comando linear/angular;
- comunicação Serial com ESP32;
- ACK, retry e watchdog;
- STOP em perda de alvo, inicialização, encerramento e falhas críticas;
- logs estruturados;
- medição de latência por etapa;
- modo mock completo;
- testes unitários do núcleo de tracking e controle;
- scripts de instalação e preflight para Windows e Ubuntu;
- exportação de modelo para NCNN em máquina de desenvolvimento;
- configuração externa em TOML.

### Fora do escopo inicial

- SLAM;
- planejamento de rotas;
- desvio de obstáculos completo;
- ROS/ROS2;
- mapa do ambiente;
- navegação por GPS;
- re-identificação robusta de pessoas;
- múltiplos alvos simultâneos;
- controle fechado de velocidade no Raspberry;
- projeto elétrico/mecânico dos motores e driver;
- interface gráfica completa;
- otimização prematura em C++.

Alguns desses itens podem ser incorporados posteriormente caso a validação demonstre necessidade.

---

## 4. Hardware-alvo atualmente definido

### Computador embarcado

**Raspberry Pi Zero 2**.

O software deve ser benchmarkado no hardware real antes de considerar o modelo de IA aprovado. O Zero 2 possui recursos significativamente menores que um PC de desenvolvimento, portanto decisões sobre resolução, backend e frequência devem ser tomadas com dados do dispositivo final.

### Microcontrolador

**ESP32**.

Responsabilidades esperadas:

- receber `(v, w)` pela serial;
- validar/parsing dos comandos;
- responder `ACK`;
- manter watchdog local;
- converter a referência `(v, w)` para a interface já existente dos motores;
- garantir STOP local quando a comunicação desaparece.

### Locomoção

Carrinho com **duas rodas motrizes e um ponto/roda de apoio**, portanto mecanicamente compatível com a ideia de acionamento diferencial.

O controle será inicialmente **em malha aberta**. A parte física dos motores/driver já existe e não é o foco deste projeto. O ponto de integração necessário é definir como o ESP32 transforma a referência recebida em comandos compatíveis com esse hardware.

Encoders não são requisito do MVP atual.

### Câmera

A câmera disponível possui a identificação **`UC436`**, mas ainda não está confirmado se essa inscrição corresponde ao modelo comercial, controlador ou apenas a uma marcação da placa.

Essa é uma pendência relevante porque o código atual possui um backend `Picamera2Camera`, adequado ao ecossistema de câmeras Raspberry/libcamera. Se a UC436 for uma câmera USB/UVC ou usar outro driver, será necessário implementar um backend adicional, provavelmente via OpenCV/V4L2, mantendo a mesma interface `Camera`.

Consequentemente:

```text
Picamera2 = backend existente e hipótese para Raspberry Camera
UC436     = hardware real ainda a confirmar
```

A arquitetura já permite trocar o backend sem alterar o orquestrador.

---

## 5. Arquitetura de software

Princípio central:

> O orquestrador conhece contratos, não bibliotecas ou hardware específico.

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
                        ESP32
```

O pipeline real por ciclo é:

```text
1. capturar frame
2. detectar pessoas
3. selecionar/reassociar alvo
4. calcular comando ou STOP
5. enviar comando
6. aguardar ACK
7. registrar dados e tempos
8. iniciar próximo ciclo
```

Na inicialização é enviado um STOP de segurança. Na saída normal, interrupção ou exceção, o sistema tenta enviar outro STOP antes de fechar os componentes.

---

## 6. Organização dos módulos

### `Camera`

Contrato:

```python
capture() -> Frame
close()
```

Implementações atuais:

- `SyntheticCamera` — testes sem hardware;
- `Picamera2Camera` — Raspberry/libcamera.

Backend futuro provável se a câmera UC436 for USB/UVC:

- `OpenCVCamera` ou `V4L2Camera`.

### `Detector`

Contrato:

```python
detect(Frame) -> list[Detection]
close()
```

Implementações atuais:

- `SyntheticPersonDetector`;
- `UltralyticsPersonDetector`.

O restante do sistema não depende diretamente de objetos da Ultralytics.

### `TargetSelector`

Contrato:

```python
select(detections, frame) -> Detection | None
reset()
```

Implementação atual:

- `NearestBBoxSelector`.

### `Controller`

Contrato:

```python
compute(target, frame) -> MotionCommand
```

Implementação atual:

- `BBoxProportionalController`.

### `CommunicationLink`

Contrato:

```python
send(command) -> CommunicationResult
close()
```

Implementações atuais:

- `MockCommunicationLink`;
- `SerialCommunicationLink`.

---

## 7. Modelos de dados compartilhados

### `Frame`

Contém:

- imagem `numpy.ndarray`;
- sequência;
- timestamp monotônico;
- largura e altura derivadas da imagem.

### `BoundingBox`

Formato:

```text
(x1, y1, x2, y2)
```

Fornece:

- largura;
- altura;
- área;
- centro;
- distância normalizada entre centros.

### `Detection`

```text
bbox
confidence
class_id
class_name
track_id opcional
```

### `MotionCommand`

```text
linear
angular
```

Inclui `MotionCommand.stop()`.

### `CommunicationResult`

Registra:

- sucesso;
- sequência;
- resposta;
- tentativas;
- latência;
- erro.

---

## 8. Aquisição de imagem

A implementação `Picamera2Camera` inicializa a câmera uma vez e mantém o periférico ativo.

Configuração atual:

```text
RGB888
640 x 480
buffer_count = 2
queue = False
```

O uso de `queue=False` foi escolhido para reduzir a chance de processar deliberadamente um frame antigo que ficou aguardando enquanto a inferência anterior era executada.

A aplicação só solicita a próxima imagem quando o ciclo anterior terminou, mantendo a semântica síncrona do MVP.

---

## 9. Detecção de pessoas

A implementação concreta atual usa a API da Ultralytics.

Hipótese inicial de implantação:

```text
YOLO26n
-> exportação NCNN
-> inferência no Raspberry
-> imgsz inicial = 320
-> classe = person
```

O modelo/resolução ainda não estão aprovados para o Raspberry Pi Zero 2. Precisam ser medidos em:

- tempo médio de inferência;
- mediana;
- p95 e p99;
- RAM;
- CPU;
- temperatura;
- estabilidade;
- precisão em diferentes distâncias.

Resoluções candidatas para comparação incluem 256, 320 e 416, conforme viabilidade.

Se a camada Python/Ultralytics for pesada demais, a arquitetura permite substituir apenas o detector por um backend NCNN nativo, inclusive C++, preservando a saída `list[Detection]`.

---

## 10. Seleção e tracking do alvo

O MVP não utiliza ainda um tracker persistente como ByteTrack ou BoT-SORT.

A lógica atual é propositalmente simples.

### Primeiro frame

Estratégias suportadas:

- `first`;
- `largest`;
- `center`;
- `confidence`.

Configuração atual:

```text
initial_strategy = first
```

### Frames seguintes

O seletor compara o centro da bounding box anterior com os centros das detecções atuais e escolhe a mais próxima.

A distância é normalizada pela diagonal do frame.

Parâmetro atual:

```text
max_center_distance = 0.30
```

Se nenhuma detecção estiver suficientemente próxima, o alvo é rejeitado e o carrinho recebe STOP.

O seletor mantém a referência anterior durante alguns ciclos:

```text
max_missed_frames = 3
```

Isso permite uma tentativa limitada de reaquisição.

### Limitação conhecida

A heurística pode trocar de pessoa em:

- cruzamentos;
- oclusões;
- movimentos rápidos;
- múltiplas pessoas próximas.

Um tracker mais sofisticado só deve ser adicionado se os testes mostrarem que a heurística atual é insuficiente para o cenário experimental.

---

## 11. Controle visual

O controlador usa duas informações da bounding box:

1. deslocamento horizontal;
2. altura relativa.

### 11.1 Controle angular

Erro horizontal:

```text
ex = (centro_da_imagem - centro_do_alvo) / meia_largura
```

Faixa aproximada:

```text
[-1, +1]
```

Convenção antes de `angular_sign`:

```text
+w = virar para a esquerda / anti-horário
-w = virar para a direita / horário
```

Lei proporcional:

```text
w = Kpw * ex
```

com deadband e saturação.

Se o sentido real do carrinho estiver invertido, pode-se usar:

```toml
angular_sign = -1.0
```

### 11.2 Controle de aproximação

A versão atual usa:

```text
height_ratio = bbox_height / image_height
```

O objetivo configurado é:

```text
desired_height_ratio = 0.55
```

Erro:

```text
ed = desired_height_ratio - height_ratio
v = Kpv * ed
```

Sem marcha à ré, valores negativos são truncados para zero.

### 11.3 Redução de avanço ao fazer curva

Quando o alvo está muito deslocado lateralmente, o avanço é reduzido.

Parâmetros atuais:

```text
forward_slowdown_error = 0.35
forward_stop_error     = 0.75
```

Com erro lateral grande, o carrinho primeiro tenta se orientar e só depois avançar.

---

## 12. Calibração bbox ↔ distância

O MVP atual controla **distância visual**, não metros.

Entretanto, a arquitetura deve permitir calibração posterior usando a altura aparente da pessoa.

Uma calibração simples pode usar uma referência conhecida:

```text
K = distancia_referencia * altura_bbox_referencia

distancia_estimada ≈ K / altura_bbox_atual
```

Isso é equivalente a uma aproximação pinhole quando câmera, enquadramento e altura real do alvo permanecem suficientemente consistentes.

Uma versão melhor pode armazenar:

- altura aproximada da pessoa;
- distância de calibração;
- altura em pixels observada nessa distância;
- FOV ou parâmetros intrínsecos da câmera, se disponíveis.

Ainda assim, a estimativa varia com postura, oclusão, inclinação da câmera e diferenças de altura entre pessoas. Portanto, para o MVP, a razão da bbox deve continuar sendo tratada como a variável principal de controle, e a conversão para metros como uma camada de calibração opcional.

---

## 13. Semântica de `(v, w)`

O projeto transmite dois valores `float`:

```text
v = referência linear
w = referência angular
```

No MVP em malha aberta, eles devem ser tratados como **referências abstratas calibráveis**, não como velocidades físicas garantidas.

No futuro, com encoders e geometria conhecida, o contrato poderia migrar para:

```text
v em m/s
w em rad/s
```

sem exigir alteração do protocolo serial.

Para o carrinho diferencial, uma eventual conversão física seria:

```text
v_left  = v - w * wheel_base / 2
v_right = v + w * wheel_base / 2
```

Mas, na configuração atual sem feedback, o ESP32 pode simplesmente mapear as referências para o comando já utilizado pelo subsistema de motores.

---

## 14. Comunicação Raspberry ↔ ESP32

Transporte inicial:

```text
USB / Serial
115200 baud
8N1
```

### Comando

```text
CMD,<seq>,<linear>,<angular>\n
```

Exemplo:

```text
CMD,42,0.28000,-0.37000
```

### ACK

```text
ACK,<seq>\n
```

Exemplo:

```text
ACK,42
```

### Erro opcional

```text
ERR,<seq>,<reason>\n
```

O número de sequência impede que um ACK antigo seja confundido com a confirmação do comando atual.

### Retry

Se o ACK não chegar dentro de `ack_timeout_s`, o Raspberry reenvia o **mesmo comando com a mesma sequência**.

Configuração atual:

```text
ack_timeout_s   = 0.25
write_timeout_s = 0.25
retries         = 2
startup_delay_s = 1.5   # configuração Raspberry
```

Após esgotar as tentativas, a configuração atual considera a comunicação perdida uma falha fatal do loop.

---

## 15. Firmware ESP32

Existe um firmware de exemplo em:

```text
esp32_example/esp32_velocity_receiver.ino
```

Ele já implementa:

- leitura por linha;
- parsing de `CMD`;
- sequência;
- `ACK`;
- mensagens simples de erro;
- `READY` no startup;
- watchdog;
- STOP no watchdog.

O ponto ainda propositalmente incompleto é:

```cpp
applyVelocityReference(float linear, float angular)
```

Essa função deve ser ligada ao controle de motores já existente no carrinho.

O comentário antigo do firmware menciona hardware/geometria como indefinidos; documentalmente isso deve ser interpretado apenas como “integração ainda não codificada”. O alvo atual já é um carrinho diferencial de duas rodas motrizes com apoio e ESP32.

---

## 16. Watchdog

O watchdog do ESP32 é uma camada de segurança independente do processo Python.

Se não chegar comando válido durante o timeout:

```text
v = 0
w = 0
```

O exemplo atual usa:

```text
COMMAND_TIMEOUT_MS = 2000
```

Esse valor é provisório.

A calibração correta deve ocorrer após benchmark do loop real:

```text
watchdog > p99 do tempo normal do ciclo + margem
```

mas suficientemente curto para interromper o movimento rapidamente se:

- o Raspberry travar;
- o processo morrer;
- o cabo desconectar;
- a IA bloquear por tempo anormal.

---

## 17. Logging e instrumentação

O logger grava:

- console;
- arquivo JSON Lines rotativo.

Por ciclo são registrados:

- sequência e resolução do frame;
- detecções;
- alvo;
- comando `(v, w)`;
- status de comunicação;
- número de tentativas;
- latência de ACK;
- tempo de captura;
- tempo de inferência;
- tempo de tracking;
- tempo de controle;
- tempo de comunicação;
- tempo total do ciclo.

O script:

```bash
python scripts/summarize_logs.py logs/followbot.log
```

calcula estatísticas como média, mediana, p95, p99 e máximo.

Esses dados devem ser usados para decidir se a meta de frequência foi alcançada e qual estágio precisa de otimização.

### Imagens

A versão atual **não persiste os frames**. Isso reduz armazenamento e evita introduzir prematuramente questões de retenção de imagens de pessoas.

---

## 18. Configuração atual de referência

Valores iniciais do controlador:

```toml
[control]
desired_height_ratio = 0.55
height_deadband = 0.05
horizontal_deadband = 0.06
kp_linear = 1.0
kp_angular = 1.3
max_linear = 0.40
max_angular = 1.20
allow_reverse = false
forward_slowdown_error = 0.35
forward_stop_error = 0.75
angular_sign = 1.0
```

Tracking:

```toml
[tracking]
initial_strategy = "first"
max_center_distance = 0.30
max_missed_frames = 3
```

Esses números são parâmetros de partida para experimentação, não valores finais de controle.

---

## 19. Modo mock

O projeto possui um caminho completo sem hardware:

```text
SyntheticCamera
SyntheticPersonDetector
NearestBBoxSelector real
BBoxProportionalController real
MockCommunicationLink
logger real
```

Isso permite validar:

- instalação;
- composição de módulos;
- loop;
- tracking;
- controle;
- logging;
- encerramento seguro;

sem Raspberry, câmera, YOLO ou ESP32.

Após a auditoria, `main.py` usa por padrão:

```text
config.mock.toml
```

Isso evita que uma execução acidental no PC tente abrir a câmera/serial reais.

---

## 20. Dependências

### Base

```text
Python >= 3.11
numpy >= 1.24
pyserial >= 3.5
```

### Desenvolvimento

```text
pytest >= 8
```

### IA

```text
ultralytics >= 8.4.108,<9
```

### Exportação

```text
ultralytics[export] >= 8.4.108,<9
```

A exportação foi separada do runtime porque pode instalar dependências pesadas que não são necessárias para validar o núcleo do projeto.

---

## 21. Instalação de teste — Windows

Ambiente recomendado:

```text
Windows 10/11
PowerShell
Python 3.12 x64
```

Python 3.11+ é aceito.

Na raiz do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_test_windows.ps1
```

O script:

1. procura Python 3.12 e depois 3.11;
2. cria `.venv`;
3. atualiza `pip`, `setuptools`, `wheel`;
4. instala dependências mínimas e de teste;
5. executa o preflight;
6. executa os testes unitários;
7. executa o loop mock;
8. resume os logs.

Para 100 ciclos:

```powershell
.\scripts\setup_test_windows.ps1 -Cycles 100
```

---

## 22. Instalação de teste — Ubuntu

### Ubuntu 24.04

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
bash scripts/setup_test_ubuntu.sh
```

### Ubuntu 22.04

O Python padrão é 3.10 e não atende à exigência atual de 3.11+.

Usar Python 3.11/3.12 em paralelo, sem substituir à força o Python do sistema.

Exemplo, quando disponível no repositório configurado:

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv
bash scripts/setup_test_ubuntu.sh
```

Para mais ciclos:

```bash
FOLLOWBOT_TEST_CYCLES=100 bash scripts/setup_test_ubuntu.sh
```

---

## 23. Preflight

Com o virtualenv ativo:

```bash
python scripts/preflight.py
```

Valida:

- sistema operacional;
- arquitetura;
- versão do Python;
- executável Python;
- virtualenv;
- arquivos básicos;
- imports de NumPy e pySerial;
- leitura da configuração mock.

Com IA:

```bash
python scripts/preflight.py --require-ai
```

---

## 24. Teste serial seguro

Antes de qualquer teste de movimento:

```bash
python scripts/list_serial_ports.py
```

Depois usar:

```bash
python scripts/serial_smoke_test.py --port <PORTA>
```

Exemplos:

```text
Windows: COM4
Ubuntu:  /dev/ttyACM0
```

Esse smoke test envia **somente STOP (`v=0`, `w=0`)**.

Ele serve para validar:

- driver USB;
- porta correta;
- baudrate;
- reset do ESP ao abrir a porta;
- parsing;
- ACK;
- timeout/retry.

---

## 25. Instalação da IA

A pilha de IA não faz parte da primeira instalação de teste.

Somente após mock e testes básicos:

```bash
python -m pip install --no-build-isolation --prefer-binary \
  -c constraints/test-direct.txt -e '.[ai]'
```

Depois:

```bash
python scripts/preflight.py --require-ai
```

Separar essa etapa torna falhas de PyTorch/OpenCV/Ultralytics mais fáceis de diagnosticar.

---

## 26. Exportação NCNN

A exportação deve preferencialmente ocorrer no PC de desenvolvimento.

```bash
python -m pip install --no-build-isolation --prefer-binary \
  -c constraints/test-direct.txt -e '.[export]'

python scripts/export_yolo26_ncnn.py --model yolo26n.pt --imgsz 320
```

A pasta exportada deve ser copiada para:

```text
models/yolo26n_ncnn_model/
```

O Raspberry não deve ser usado como primeira escolha para executar a conversão do modelo.

---

## 27. Instalação no Raspberry

O Raspberry Pi OS deve ser tratado separadamente de Ubuntu/Windows desktop.

Para Picamera2:

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-venv

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
python -m pip install -e '.[ai]'
```

Teste a câmera isoladamente antes do FollowBot:

```bash
rpicam-hello
```

Se a câmera UC436 não for compatível com Picamera2/libcamera, esta etapa deverá ser substituída pelo backend correspondente ao hardware real.

---

## 28. Estratégia de validação

### Fase A — software puro

```text
mock completo
pytest
100+ ciclos
```

Critérios:

- sem exceções;
- comandos coerentes;
- logs criados;
- STOP no início/final.

### Fase B — câmera isolada

Sem IA e sem motores.

Validar:

- detecção do dispositivo;
- resolução;
- orientação;
- iluminação;
- tempo de captura.

### Fase C — IA isolada

```text
câmera real
IA real
comunicação mock
```

Medir pelo menos algumas centenas de ciclos.

### Fase D — serial isolada

Motores desabilitados ou carrinho suspenso.

Validar:

- ACK;
- retry;
- reset da placa;
- watchdog.

### Fase E — integração do comando no ESP

Implementar `applyVelocityReference()` usando a interface de motores já existente.

Testar primeiro com limites muito baixos.

### Fase F — controle físico

Ambiente controlado, área livre e possibilidade de parada física imediata.

Calibrar:

- sentido angular;
- intensidade de `v`;
- intensidade de `w`;
- deadbands;
- distância visual desejada;
- watchdog.

### Fase G — benchmark final

Verificar:

```text
frequência média
p95/p99 do ciclo
RAM
CPU
temperatura
qualidade do tracking
estabilidade da serial
```

Critério inicial importante:

```text
>= aproximadamente 1 ciclo/s de forma sustentada
```

---

## 29. Segurança

Seguir visualmente uma pessoa **não equivale a navegação segura**.

O sistema atual não detecta de forma independente:

- paredes baixas;
- degraus;
- móveis;
- objetos pequenos;
- animais;
- obstáculos fora da região da pessoa.

Portanto, antes de testes com velocidade relevante, recomenda-se:

- área controlada;
- velocidade reduzida;
- carrinho inicialmente elevado ou motores desacoplados para testes de serial;
- botão/chave física de corte ou outra parada independente;
- considerar sensor de proximidade/bumper antes de uso autônomo mais livre.

Software não deve ser a única forma de interromper o protótipo.

---

## 30. Problemas e riscos já identificados na auditoria

### 30.1 Caminhos relativos ao diretório atual

`config` e `model_path` ainda dependem do diretório de onde o programa é executado.

Melhoria recomendada:

- resolver arquivos em relação ao arquivo TOML ou à raiz do projeto.

### 30.2 Picamera2 não é backend genérico de PC

Windows/Ubuntu desktop não devem ser usados para validar Picamera2 como se fossem Raspberry Pi OS.

### 30.3 Câmera real ainda não confirmada

Se `UC436` for USB/UVC, implementar backend OpenCV/V4L2.

### 30.4 Dependências de IA pesadas

Ultralytics pode puxar PyTorch/OpenCV e downloads grandes. Por isso foi removido do primeiro teste de instalação.

### 30.5 Lock incompleto

`constraints/test-direct.txt` reduz variação direta, mas ainda não é um lock transitivo completo da pilha de IA.

Criar lock definitivo após validar a combinação real de:

```text
SO + arquitetura + Python + Ultralytics + backend NCNN
```

### 30.6 Testes ainda limitados

Os testes atuais cobrem o núcleo de tracking e controle, mas faltam testes dedicados para:

- parsing/configuração;
- orquestrador;
- STOP em falha;
- logger;
- timeout/retry serial com serial simulada;
- validação de parâmetros extremos/NaN.

### 30.7 `applyVelocityReference()` é placeholder

O protocolo serial já pode ser validado, mas o movimento real ainda depende da integração dessa função com o código existente dos motores.

### 30.8 Loop sem período fixo

A aplicação executa tão rápido quanto cada ciclo permitir.

Isto é desejável na fase de benchmark. Se futuramente for preciso uma frequência fixa, o controle de período deve ser introduzido de forma explícita.

### 30.9 Ausência de sensor de obstáculos

É o maior risco funcional para testes autônomos fora de um ambiente muito controlado.

---

## 31. Mudanças introduzidas na última auditoria

Foram acrescentados:

```text
INSTALL_TEST.md
constraints/test-direct.txt
scripts/preflight.py
scripts/setup_test_windows.ps1
scripts/setup_test_ubuntu.sh
scripts/list_serial_ports.py
scripts/serial_smoke_test.py
```

Também foram feitas estas alterações:

1. `main.py` passou a usar `config.mock.toml` por padrão;
2. `pyproject.toml` recebeu extra separado `export`;
3. foi adicionado o comando de console `followbot`;
4. a instalação inicial deixou de instalar a pilha de IA por padrão;
5. Windows e Ubuntu ganharam processos separados e reproduzíveis;
6. foi criado um preflight explícito;
7. foi criado um teste serial que envia apenas STOP;
8. foram documentadas permissões de serial no Ubuntu;
9. foi documentado o caso de reset do ESP ao abrir a serial;
10. Raspberry/Picamera2 passou a ser tratado como ambiente específico, não como instalação genérica de Linux.

Validação realizada durante a auditoria:

```text
7/7 testes existentes aprovados
loop mock executado corretamente
```

O ambiente usado para a auditoria não possuía acesso externo ao PyPI, portanto o download completo das dependências não foi reproduzido nele. Os scripts foram criados justamente para repetir essa validação em uma máquina conectada.

---

## 32. Estrutura atual do repositório

```text
followbot_mvp/
├── pyproject.toml
├── config.mock.toml
├── config.rpi.example.toml
├── README.md
├── ARCHITECTURE.md
├── SERIAL_PROTOCOL.md
├── VALIDATION_PLAN.md
├── PENDING_DECISIONS.md
├── INSTALL_TEST.md
├── FORMULACAO_PROJETO_COMPLETA.md
├── constraints/
│   └── test-direct.txt
├── models/
├── logs/
├── esp32_example/
│   └── esp32_velocity_receiver.ino
├── scripts/
│   ├── export_yolo26_ncnn.py
│   ├── summarize_logs.py
│   ├── preflight.py
│   ├── setup_test_windows.ps1
│   ├── setup_test_ubuntu.sh
│   ├── list_serial_ports.py
│   └── serial_smoke_test.py
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

---

## 33. Estado atual: implementado vs pendente

### Implementado

- arquitetura modular por interfaces;
- orquestrador sequencial;
- câmera sintética;
- backend Picamera2;
- detector sintético;
- detector Ultralytics;
- estruturas de detecção/bbox;
- tracking simples;
- controle proporcional visual;
- comunicação serial;
- ACK/retry;
- comunicação mock;
- STOP de segurança no processo Python;
- watchdog de exemplo no ESP32;
- logs JSONL e console;
- medição por etapa;
- configuração TOML;
- scripts Windows/Ubuntu;
- preflight;
- smoke test serial STOP-only;
- resumo de benchmarks;
- testes básicos automatizados.

### Próximas implementações prioritárias

1. identificar de forma conclusiva a câmera UC436 e seu backend;
2. integrar `applyVelocityReference()` ao código de motores do ESP32;
3. testar serial real sem movimento;
4. validar câmera real isoladamente;
5. exportar/testar modelo NCNN;
6. benchmarkar a IA no Raspberry Pi Zero 2;
7. confirmar se a meta de aproximadamente 1 Hz é atingida;
8. calibrar `(v, w)` em baixa potência;
9. calibrar relação bbox/distância visual;
10. ajustar watchdog com p99 real;
11. adicionar testes automatizados do orquestrador e serial;
12. corrigir resolução de paths;
13. avaliar necessidade de backend de câmera USB;
14. avaliar necessidade de tracker mais robusto somente após testes;
15. incorporar mecanismo independente de prevenção/parada antes de testes autônomos mais agressivos.

---

## 34. Critério de conclusão do MVP

O MVP pode ser considerado funcional quando, em ambiente controlado:

1. o Raspberry inicia o pipeline sem intervenção manual além da execução;
2. uma pessoa é detectada;
3. o alvo é mantido entre frames em situações simples;
4. a direção do carrinho acompanha coerentemente a posição lateral do alvo;
5. o avanço diminui conforme o alvo se aproxima visualmente;
6. a ausência de alvo gera STOP;
7. falha persistente da serial interrompe o loop;
8. o watchdog do ESP32 para o carrinho se o Raspberry deixa de enviar comandos;
9. a integração com os motores responde a `(v, w)` com comportamento calibrado;
10. o sistema sustenta a frequência mínima experimental definida para o protótipo, inicialmente cerca de 1 Hz;
11. logs permitem reproduzir e explicar os resultados do experimento;
12. a instalação de desenvolvimento pode ser repetida em Windows ou Ubuntu seguindo a documentação.

---

## 35. Direção arquitetural recomendada após o MVP

A ordem recomendada de evolução é orientada por medições:

```text
1. medir
2. identificar gargalo real
3. otimizar apenas o módulo necessário
```

Possíveis evoluções:

```text
Detector Python/Ultralytics lento
    -> NCNN nativo

Tracking geométrico insuficiente
    -> ByteTrack/BoT-SORT/outro

Loop síncrono insuficiente
    -> captura/inferência assíncrona com política explícita de frame mais recente

Controle aberto inconsistente
    -> encoders + controle de velocidade local no ESP

Distância visual insuficiente
    -> calibração geométrica ou sensor complementar

Segurança insuficiente
    -> sensores de obstáculo/bumper/parada física
```

A modularidade atual foi escolhida justamente para permitir essas substituições sem reescrever todo o sistema.

---

# Resumo final

A versão atual do FollowBot já possui um **núcleo de software coerente e testável sem hardware**, com interfaces bem separadas, tracking e controle simples, protocolo serial com ACK/retry, logging estruturado e mecanismos básicos de STOP.

A última revisão fortaleceu principalmente a **reprodutibilidade de instalação e diagnóstico em Windows e Ubuntu**, separando o teste básico da pesada pilha de IA e adicionando scripts de preflight e serial seguro.

O maior trabalho restante não está na arquitetura geral, mas na **validação do hardware real**: identificar corretamente a câmera, ligar o ESP32 ao controle de motores existente, benchmarkar a inferência no Raspberry Pi Zero 2 e calibrar o comportamento físico do carrinho.

A estratégia recomendada continua sendo incremental: **mock → serial STOP → câmera → IA → integração ESP/motores → movimento lento → calibração → benchmark final**.
