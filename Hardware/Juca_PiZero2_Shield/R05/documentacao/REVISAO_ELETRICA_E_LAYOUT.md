# R05 — revisão elétrica, pinagem e montagem

**Escopo:** shield Juca / Raspberry Pi Zero 2 W, com JP13 ligado a GPIO17/pino físico 11 do Raspberry. A revisão confronta a pinagem do projeto com documentos dos fabricantes e distingue verificações do CAD de condições que dependem da montagem e dos ensaios.

Os arquivos de referência são o [esquemático](../Juca_PiZero2_Shield_R05.kicad_sch), a [PCB](../Juca_PiZero2_Shield_R05.kicad_pcb), a [pinagem CSV](../pinagem_R05.csv), o [mapeamento JSON](../mapeamento_pinos.json) e o [guia da R05](../README.md). A [R04 recebida](../../R04/README.md) permanece como fonte histórica para as conexões da Juca. **O esquemático completo da Juca e a identificação da variante física do ESP32-S3 não estão disponíveis no acervo consultado.** Assim, a correspondência J5–ESP abaixo conserva o mapeamento recebido e ainda requer conferência na placa real.

## Pinagem dos sinais

O número do jumper corresponde ao número do pino de J5. A numeração BCM identifica o GPIO do Raspberry; ela não corresponde à numeração física de seu header nem ao número de GPIO do ESP32-S3.

| Jumper / J5 | GPIO ESP32-S3 / sinal Juca | Pi físico / BCM | Função no Raspberry |
|---|---|---|---|
| JP1 / 1 | 40 / SDA | 3 / 2 | I²C SDA |
| JP2 / 2 | 39 / SCL | 5 / 3 | I²C SCL |
| JP3 / 3 | 43 / TXD0 | 10 / 15 | UART RX, ESP → Pi |
| JP4 / 4 | 44 / RXD0 | 8 / 14 | UART TX, Pi → ESP |
| JP5 / 5 | 38 | 24 / 8 | SPI0 CE0 |
| JP6 / 6 | 37 | 21 / 9 | SPI0 MISO |
| JP7 / 7 | 36 | 23 / 11 | SPI0 SCLK |
| JP8 / 8 | 35 | 19 / 10 | SPI0 MOSI |
| JP9 / 9 | 45 | 15 / 22 | GPIO |
| JP10 / 10 | 48 | 12 / 18 | PWM0 / GPIO |
| JP11 / 11 | 47 | 33 / 13 | PWM1 / GPIO |
| JP12 / 12 | 46 | 16 / 23 | GPIO |
| JP13 / 13 | 3 | 11 / 17 | GPIO |

Os destinos físicos/BCM, I²C, UART e SPI coincidem com a [pinagem oficial Raspberry](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio). PWM0 em BCM18/ALT5 e PWM1 em BCM13/ALT0 constam na tabela 6-31 e na seção 9.5 do [manual oficial de periféricos BCM2835](https://pip.raspberrypi.com/documents/RP-008249-DS), indicado pela documentação Raspberry para as funções alternativas da família Zero.

**JP1–JP12 mantêm o mapeamento da R04. JP13 passa de GPIO24/pino físico 18 para GPIO17/pino físico 11; o pino físico 18 fica NC na shield.** A origem de JP13 continua sendo J5-13/GPIO3 da Juca. O pino 11 está em X = 15,77 e Y = 41,07 mm, na referência local da placa.

O cruzamento UART é correto: o TX do ESP chega ao RX do Pi, e o TX do Pi chega ao RX do ESP. TXD0/GPIO43 e RXD0/GPIO44 constam no [datasheet ESP32-S3-WROOM-1/WROOM-1U, seção 3.2](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf). O firmware, a seleção da UART Linux e a eventual ocupação por console ou depuração continuam sendo condições de integração.

Os headers JP são montados; **aberto significa sem capinha removível**. Para o protocolo serial do FollowBot, habilitar JP3 e JP4. Os demais podem permanecer abertos. Fechar um JP estabelece contato elétrico e não configura automaticamente periféricos, direção ou nível de um GPIO. Em uma futura ligação SPI com o Pi como controlador, MOSI, SCLK e CE0 saem do Pi; MISO retorna do periférico ao Pi. O ESP precisa receber a configuração correspondente.

## Restrições do ESP32-S3 e do I²C

As restrições abaixo constam no [datasheet oficial do módulo, versão 1.8, seções 3.2 e 4](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf):

| Linhas | Condição a conferir antes de habilitar |
|---|---|
| JP6–JP8 / GPIO37, 36, 35 | Indisponíveis para outros usos em módulos com PSRAM Octal R8/R16V. |
| JP10/JP11 / GPIO48, 47 | Domínio de 1,8 V em módulos com ESP32-S3R16V; ligação direta aos 3,3 V do Pi é incompatível nessa variante. |
| JP9 / GPIO45 | Seleção de VDD_SPI no reset, sujeita aos eFuses. |
| JP12 / GPIO46 | Participa do boot e da impressão ROM; download com GPIO0 baixo exige GPIO46 baixo. |
| JP13 / GPIO3 | Seleção da origem JTAG conforme eFuses; ignorado na configuração padrão da tabela 4-5. |

A marcação completa do módulo determina quais restrições se aplicam. A informação de que a Juca possui **R14 de 10 kΩ para GND em GPIO45** vem da R04 e precisa ser confirmada no hardware instalado.

A R04 também informa que SDA/SCL da Juca compartilham um **MPU-6050**. Essa conexão ainda não foi confirmada por esquemático próprio da Juca ou medição. BCM2/3 do Pi possuem pull-ups fixos de 1,8 kΩ para 3,3 V, conforme o [esquemático oficial Zero 2 W](https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-reduced-schematics.pdf). Resistores adicionais da Juca ou do módulo MPU devem ser considerados em paralelo.

Fechar JP1 e JP2 une os participantes ao mesmo barramento. É necessário definir quem o controla e como os firmwares coordenam transações, endereços e inicialização. O ESP32-S3 pode operar como controlador ou periférico I²C; SDA/SCL usam saídas de dreno aberto e pull-ups. Essa capacidade não comprova que dois firmwares existentes estejam preparados para compartilhar o controle. [Documentação oficial ESP-IDF I²C](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/i2c.html).

## Alimentação e retorno

As ligações de alimentação conservam a R04: J11-2 leva +5 V aos pinos físicos 2/4 do Pi, e J11-4 liga GND ao físico 9. J11-1/+BATT e J11-3/+3,3 V ficam NC. **Remover todas as capinhas não desliga nem isola a alimentação.**

O físico 9 é um GND válido e pertence à mesma rede dos demais GND no Pi, conforme seu [esquemático oficial](https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-reduced-schematics.pdf). Usar apenas esse contato não constitui erro de pinagem; a capacidade de corrente do contato e o desempenho do retorno da shield precisam ser verificados sob carga. Ausência de erros de conectividade no CAD não demonstra queda de tensão, aquecimento ou imunidade ao ruído dos motores.

A shield não inclui regulador, conversor de níveis ou seleção de fontes. O USB de dados utilizado para acesso em modo gadget também pode alimentar o Pi, como documenta a [orientação oficial de SSH por USB](https://www.raspberrypi.com/news/usb-gadget-mode-in-raspberry-pi-os-ssh-over-usb/). Portanto, o ensaio com Juca e computador conectados deve definir uma fonte e um caminho de alimentação compatíveis, sem presumir isolamento na Juca. Os GPIOs do Pi operam em 3,3 V e não toleram 5 V, segundo a [documentação GPIO oficial](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio).

## Sentido de montagem e folgas

A montagem foi confrontada com o [desenho mecânico oficial Zero 2 W](https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-mechanical-drawing.pdf). Na vista superior da shield, microSD fica no topo e CSI/flat embaixo, oposto a J5. Com a face dos componentes do Pi voltada para baixo, o header fica à esquerda: ímpares internos em X = 15,77; pares externos em X = 13,23 mm. O pino 1 quadrado fica no topo à direita de JPI1, próximo ao microSD. Essa orientação está representada na [comparação R04/R05](orientacao_R04_R05.svg).

J5/J11 são montados embaixo da shield, em B.Cu; JPI1 e os jumpers ficam em cima, em F.Cu. O macho do Raspberry deve apontar para o soquete JPI1 com o Pi nessa orientação. Conferir o pad quadrado e o encaixe de todas as posições antes de energizar.

O corpo do Pi ocupa X = 11…41 e Y = 20…85 mm. Sua projeção cobre H3, em X = 39 e Y = 68 mm. A altura dos conectores e espaçadores deve liberar a cabeça desse fixador e os componentes voltados para baixo. Também é necessário conferir o acesso à trava CSI, o trajeto do flat e o espaço dos plugues USB. Os 3 mm entre a extremidade CSI do Pi e a borda inferior da shield não comprovam essas folgas em altura.

## Fabricação CNC e limites de validação

Pads elétricos PTH usam furo de 1 mm; as vias usam ilha de 2 mm e furo de 1 mm. H1–H4 conservam furo mecânico de 3,2 mm, e H5–H8, de 2,75 mm. A padronização dos furos elétricos não substitui os diâmetros necessários à fixação.

Em usinagem sem metalização, cada via exige ligação entre faces por fio compatível com o furo e solda dos dois lados. Fazer essas conexões antes de instalar headers que possam esconder a região de soldagem. As faces de chegada e as distâncias entre vias e plásticos dos conectores precisam ser avaliadas com os componentes escolhidos. Um furo isolado não estabelece continuidade entre F.Cu e B.Cu.

Os Gerbers/Excellon são entradas para o CAM; ferramenta efetiva, registro das duas faces, profundidade de isolamento, tolerâncias, espaçadores e acabamento ainda precisam ser definidos para a máquina usada. Os ensaios de continuidade, alimentação sob carga, inicialização e comunicação pertencem à validação física.

## Larguras, roteamento e verificações do CAD

Cada rede roteada mantém uma única largura, inclusive entre F.Cu e B.Cu:

| Rede / grupo | Antes desta revisão de layout | Valor aplicado |
|---|---|---|
| `PI_GPIO*` | 0,508 mm | 0,55 mm |
| `JUCA_*` | 0,762 mm | 1,0 mm |
| `+5V` | 1,0 / 1,8 mm | 2,0 mm |
| `GND` | 1,8 mm | 2,0 mm |

O percurso longitudinal dos 5 V foi redesenhado para retirar o estreitamento de 1 mm, contornando as reservas dos fixadores. A largura uniforme de 0,60 mm nos sinais do Pi foi avaliada, mas violava separações da geometria existente; 0,55 mm mantém o mínimo de 0,508 mm. Os valores foram registrados nas classes `Default`, `JucaSignals` e `Power` do projeto. Os jumpers separam as redes Juca/Pi e são o ponto onde os dois grupos de larguras se encontram.

Seis pontos de passagem entre faces foram corrigidos por proximidade do contorno nominal dos conectores:

| Via | Posição anterior X; Y (mm) | Posição atual X; Y (mm) | Folga nominal entre ilha e corpo |
|---|---|---|---|
| GPIO17, próxima de JPI1 | 17,50; 41,50 | 18,30; 41,50 | 0,26 mm |
| GND, próxima de J11 | 43,80; 85,70 | 42,60; 86,30 | Maior que 0,30 mm |
| GPIO23, próxima de JPI1 | 11,10; 46,15 | 10,70; 47,00 | 0,26 mm |
| GPIO14, próxima de JP4 | 14,90; 13,20 | 14,90; 13,60 | 0,29 mm |
| GPIO15, próxima de JP3 | 12,30; 13,30 | 12,30; 13,60 | 0,29 mm |
| GPIO3, próxima de JP2 | 9,30; 13,10 | 9,30; 13,60 | 0,29 mm |

Essas folgas usam o contorno nominal dos footprints: F.Fab nos jumpers e a representação em serigrafia nos headers JPI1/J5/J11, que ainda não possuem modelos 3D dos componentes escolhidos. Na via GPIO17, o desvio exigiu pequenos ajustes nas trilhas F.Cu de GND e GPIO22, preservando seus destinos e larguras. A via GND mantém 0,70 mm entre sua ilha e a borda inferior da placa. As alterações liberam esses contornos nominais; a dimensão real dos componentes e o volume dos filetes de solda ainda precisam ser conferidos na montagem.

A análise das 41 vias contra os 16 contornos nominais resultou em 656 comparações, sem sobreposições e com folga mínima de 0,26 mm. Também foi ampliado o afastamento dos 5 V em relação à reserva circular de H1: a menor distância adicional à reserva de raio 3,5 mm passou de aproximadamente 0,016 para 0,148 mm. A reserva deve ser confrontada com o fixador efetivamente utilizado.

A numeração das colunas 1–13 foi deslocada para a borda superior, acima de J5, para não sobrepor os furos das vias. Cada número identifica a mesma coluna de J5 e do respectivo JP. A anotação de montagem J5/Juca permanece em Dwgs.User, na margem direita.

A passagem de uma face para outra é feita pelas **41 vias**, todas com contato de cobre nas duas camadas. Os **57 pads utilizados** têm contato direto com trilha da mesma rede na face acessível prevista: F.Cu em J5/J11, B.Cu em JPI1 e nos jumpers. Essa verificação não conta com metalização implícita dos terminais dos headers. A soldagem física das vias continua necessária na fabricação CNC sem metalização.

As trilhas usam trechos horizontais, verticais ou diagonais de 45°. Nas junções verificadas fora dos pads/vias, não foram encontrados cotovelos de 90°, pontas soltas, segmentos duplicados ou vias usadas por uma só face. A auditoria estrutural tem escopo limitado e é complementada pelo DRC nativo; esses resultados não demonstram desempenho de alta frequência ou imunidade eletromagnética. Em particular, GPIO17 conserva um percurso longo em torno da região do header, e o retorno de GND chega ao Pi por um único contato.

Os relatórios estão em [verificacao](../verificacao/README.md), e a [vista conjunta do roteamento](roteamento_R05.png) apresenta as duas faces e sua sobreposição. Os arquivos de [fabricação](../fabricacao/) são exportados da mesma revisão. A conferência digital não substitui os ensaios e medições de montagem descritos acima.

A chegada de `PI_GPIO2` ao pino 2 de JP1 foi simplificada em B.Cu: uma diagonal de 45° liga diretamente o corredor em X = 5,5 mm à ilha do jumper, mantendo 0,55 mm de largura. O percurso dessa rede diminuiu aproximadamente 4,53 mm. Foi removido um segmento redundante de 0,0656 mm que permanecia sobreposto à trilha vertical; a conectividade, os pads e as vias foram preservados.

Resultados registrados em 16/11/2026: **190 segmentos, 41 vias; DRC/ERC sem violações, nenhuma conexão aberta ou divergência com o esquemático; 408 verificações estruturais e 29 verificações das exportações aprovadas**. Os 132 furos exportados correspondem ao CAD. Os relatórios explicitam o alcance de cada verificação.
