# Comunicação provisória com a Juca por micro-ROS

O módulo [micro_ros_link.py](../src/followbot/communication/micro_ros_link.py)
implementa `MicroRosCommunication`: envio de velocidade linear e angular em
uma thread dedicada. A Juca já dispõe de firmware micro-ROS; seu tópico,
tipo de mensagem, unidades e retorno ainda precisam ser conferidos no código
desse firmware. **`/cmd_vel` e `geometry_msgs/msg/Twist` são escolhas provisórias.**

## Onde cada parte executa

```text
Raspberry Pi
  FollowBot → thread Python/rclpy → ROS 2 → micro-ROS Agent
                                                ↕ UART TX/RX
                                           ESP32 da Juca
                                           firmware micro-ROS
```

O Agent é um processo separado que conecta os clientes micro-ROS à rede ROS 2
e oferece transporte serial. Ele abre a UART; o Python publica mensagens ROS
e não abre essa porta com pySerial. Veja a [arquitetura oficial do Agent](https://github.com/micro-ROS/micro-ROS-Agent).

Na R05, JP4 leva TX do Pi ao RX da Juca e JP3 leva TX da Juca ao RX do Pi;
as capinhas das duas linhas precisam estar instaladas. A porta Linux e o baudrate
devem corresponder à UART configurada no firmware. O exemplo serial textual
`esp32_velocity_receiver.ino` é outro protocolo e não representa o firmware
micro-ROS existente na Juca.

## Contrato provisório e API

| Item | Implementação inicial |
|---|---|
| Tópico | `/cmd_vel`, configurável em `topic` |
| Mensagem | `geometry_msgs/msg/Twist` |
| Velocidade linear `v` | `linear.x` |
| Velocidade angular `w` | `angular.z` |
| Demais eixos | Zero |
| QoS | Reliable, Volatile, KeepLast com profundidade 1 |
| Validade na fila e lifespan DDS | `command_timeout_s`, padrão 0,5 s |
| Domínio ROS | `domain_id`; se omitido, configuração do ambiente ROS |
| Confirmação da API | Publicação local, sem ACK do ESP |

[`Twist`](https://github.com/ros2/common_interfaces/blob/jazzy/geometry_msgs/msg/Twist.msg)
possui vetores de velocidade linear e angular. Os valores recebidos pela API
são copiados sem conversão ou calibração. As unidades, o sentido de giro, os
limites e a interpretação desses campos devem ser confirmados no firmware;
o controlador atual do FollowBot ainda usa referências abstratas/calibráveis.

```python
from followbot.communication import MicroRosCommunication

with MicroRosCommunication(topic="/cmd_vel", command_timeout_s=0.5) as communication:
    publication = communication.send_velocity(0.0, 0.0)  # STOP
    # O programa pode continuar trabalhando enquanto a thread processa o envio.
    publication.result(timeout=1.0)  # Apenas publicação local; não é ACK.
```

O construtor inicia a thread e aguarda a inicialização local do ROS, com prazo
de 5 s por padrão. Não aguarda a conexão física com a Juca. O envio espera haver
um assinante no tópico, respeitando a validade do comando. Um assinante também
pode ser uma ferramenta ROS no computador: sua presença não identifica o ESP.

`send_velocity(v, w)` retorna imediatamente um `concurrent.futures.Future`.
Quando a publicação local termina, `result()` retorna `None`. Erros de
publicação, expiração, encerramento ou substituição ficam registrados no Future.
Um comando ainda pendente pode ser cancelado com `cancel()`; uma publicação
já iniciada não pode ser desfeita. Expirar o prazo passado a `result(timeout=...)`
limita apenas a espera do chamador, não cancela automaticamente o comando.

A fila guarda somente o comando pendente mais recente. Substituir um comando
que ainda não saiu produz `CommandSupersededError` no seu Future. Depois que um
comando foi retirado da fila para publicação, ele pode concluir antes do novo.
Não há republicação periódica de velocidades antigas. A thread processa os
eventos ROS com um `SingleThreadedExecutor` e contexto próprios, sem encerrar
outros nós ROS do processo. A organização dos executores pode ser consultada
no [código oficial do rclpy Jazzy](https://github.com/ros2/rclpy/blob/jazzy/rclpy/rclpy/executors.py).

**A validade da fila não é um watchdog dos motores.** Após uma publicação não
zero, o firmware deve parar o carrinho se deixar de receber comandos novos.
Se o firmware exigir frequência fixa, sua cadência e a expiração da referência
de visão precisam ser definidas antes de adicionar republicação periódica.

`close()` cancela o comando pendente, tenta publicar STOP uma vez, libera os
recursos ROS na thread proprietária e aguarda seu encerramento. A tentativa de
STOP não confirma entrega ao ESP. O fechamento é idempotente; se a thread
não terminar no prazo configurado, ele informa `TimeoutError`.

## Depuração isolada no Raspberry

É necessário ter ROS 2, `rclpy`, `geometry_msgs` e o micro-ROS Agent instalados.
ROS 2 Jazzy oferece suporte a Ubuntu 24.04/arm64, conforme a
[matriz oficial REP-2000](https://github.com/ros-infrastructure/rep/blob/master/rep-2000.rst).
O Python do FollowBot deve conseguir importar os pacotes desse ambiente ROS;
`pip install -e .` sozinho não instala essa stack. A construção do Agent está
descrita no [micro_ros_setup](https://github.com/micro-ROS/micro_ros_setup/tree/jazzy#building-micro-ros-agent).
Compatibilidade com a distribuição usada pelo firmware e consumo de memória
junto à visão no Zero 2 W ainda exigem teste real.

Com o ambiente instalado, iniciar o Agent em um terminal. Porta e baudrate
abaixo são **exemplos a conferir**, não dados já verificados na Juca:

```bash
source /opt/ros/jazzy/setup.bash
source ~/microros_ws/install/local_setup.bash  # ajustar ao workspace do Agent
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/serial0 -b 115200
```

As opções `--dev` e `-b` selecionam dispositivo e baudrate do transporte,
conforme a [documentação do Micro XRCE-DDS Agent](https://micro-xrce-dds.docs.eprosima.com/en/latest/agent.html#agent-cli).
Não executar simultaneamente o backend serial textual na mesma UART.

Em outro terminal com o ambiente ROS e o FollowBot disponíveis:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list -t
ros2 topic info /cmd_vel --verbose  # substituir pelo tópico real
python -m followbot.communication.micro_ros_link --topic /cmd_vel --timeout 3
```

O comando Python envia somente STOP por padrão. O JSON `published_locally: true`
informa publicação local; `esp_acknowledged: false` deixa explícito que não há
confirmação do ESP. Sem assinante até o prazo limite, o teste falha por timeout.
`--linear`, `--angular` e `--domain-id` também estão disponíveis; o programa
tenta STOP logo ao sair, portanto esse CLI não é um ensaio de movimento contínuo.

Para inspecionar apenas o mapeamento ROS, é possível abrir
`ros2 topic echo /cmd_vel geometry_msgs/msg/Twist` e executar o CLI. Isso cria
um assinante de teste e **não comprova comunicação UART ou recepção pela Juca**.

`python -m followbot.communication.micro_ros_link --help` funciona sem ROS
instalado. As dependências ROS só são carregadas ao iniciar a comunicação.

## Integração pendente com o pipeline

O módulo ainda não implementa `CommunicationLink.send(MotionCommand)`: esse
contrato exige informação de ACK, que não está definida para o firmware recebido.
Os perfis `serial` e `mock` e o orquestrador sequencial permanecem disponíveis.
Não selecionar `backend = "micro_ros"` nos TOMLs nesta etapa.

Quando o contrato da Juca estiver disponível, conferir tópico, mensagem, QoS,
unidades, domínio, UART, baudrate, frequência de comandos e watchdog. Com isso,
adaptar o mapeamento de `(v,w)` e definir o retorno da comunicação antes de
integrá-la ao orquestrador. Nenhum firmware foi gravado nem ensaio com motores
foi executado para validar este módulo.

## Verificação no Raspberry — 23/11/2026

O módulo foi copiado para `~/followbot/src/followbot/communication/` e executado
por SSH no **companionboard1**, Raspberry Pi Zero 2 W, Ubuntu 24.04.4 LTS,
`aarch64`, Python 3.12.3 e ROS 2 Jazzy. A execução usou **rclpy e DDS reais**,
com um assinante local de `Twist`, domínio ROS 177, descoberta restrita ao
localhost e tópicos temporários exclusivos de teste.

Foram confirmados a publicação de `(0,0)` pela thread `followbot-micro-ros`,
o recebimento pelo assinante ROS local, a conclusão do Future e o encerramento
da thread. Também foi executado o CLI `python -m followbot.communication.micro_ros_link`
com tópico de teste e `--domain-id 177`: terminou com código zero e o assinante
recebeu as mensagens STOP do envio e do fechamento.

Esse ensaio confirma o módulo e sua entrada de depuração no próprio Raspberry.
**Não testa UART, micro-ROS Agent, recepção pelo ESP ou motores.** O teste não
abriu a UART nem iniciou o Agent; os comandos publicados tinham velocidades
linear e angular iguais a zero.

Os testes em `tests/test_micro_ros_link.py` usam um transporte controlado para
verificar concorrência, cancelamento, expiração e encerramento; não substituem
um teste com ROS 2, Agent e ESP reais.
