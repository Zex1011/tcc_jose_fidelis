# Shield Juca + Raspberry Pi Zero 2 W - R04

Revisão de 09/11/2026, adaptada às regras CAD fornecidas para fabricação CNC no IFSC. Projeto editável no KiCad 7 ou superior, com cobre nas duas faces, 13 ligações de sinal selecionáveis e alimentação pelo Juca. A placa mede **48 × 88 mm**, com espessura prevista de 1,6 mm. As posições dos conectores e dos oito furos de fixação foram preservadas.

Abra `Juca_PiZero2_Shield_R04.kicad_pro` depois de extrair o pacote inteiro. As bibliotecas locais acompanham o projeto. O PDF `Guia_de_montagem_R04.pdf` mostra o layout, o mapeamento, a montagem e os moldes em escala 1:1. Consulte `verificacao_DRC.txt` e `verificacao_conexoes.json` para os resultados das verificações digitais.

## O que mudou

A R04 preserva a pinagem, o tamanho da placa, os conectores e os furos da R03. As trilhas de sinal passam a usar **0,508 mm (20 mil) e 0,762 mm (30 mil)**: 20 mil nos escapes e rotas da região congestionada; 30 mil nos demais trajetos, incluindo J5 e as saídas junto ao Pi. Essa faixa é permitida no material fornecido, que recomenda 30 mil. A separação mínima de cobre é **0,508 mm (20 mil) em toda a placa**. As vias passam a ter ilha de 1,8 mm e furo de 0,6 mm.

As ilhas de J11 foram reduzidas de 2,2 para 2,0 mm para obter 0,54 mm entre ilhas vizinhas. O banco de JP1 a JP13 foi deslocado 2 mm para cima, com centro em y = 7 mm a partir da borda superior, para acomodar as trilhas mais largas e suas folgas. O roteamento foi refeito para essas regras.

A compatibilidade descrita é com as **regras CAD do material fornecido**. A usinagem física, a ferramenta, o registro entre faces e a ligação elétrica das vias ainda precisam ser validados no laboratório.

Os **13 pinos de sinal do conector de expansão J5** agora possuem percursos até GPIOs específicos do Raspberry. Cada percurso é interrompido por um espaço para um componente **0 Ω, encapsulamento 1206**, identificado como JP1 a JP13. A fileira fica junto de J5, acima da área ocupada pelo Pi. Os números 1 a 13 na placa correspondem aos jumpers e aos pinos de J5.

**Todos os seletores começam abertos: DNP, componente não montado.** Para habilitar uma linha, soldar o 0 Ω correspondente. Para desabilitar, remover o componente. Estes seletores exigem soldagem; não são pinos com capinha removível. O esquemático registra DNP e os valores dos componentes no PCB identificam a montagem aberta.

O antigo jumper de fio JW3 foi retirado. O GND é contínuo por trilhas e vias. As ligações de alimentação são permanentes; os 13 jumpers selecionam somente os sinais.

## Mapeamento completo

**Pi físico** é a posição no conector de 40 pinos; **BCM** é a identificação de GPIO usada pelo software. O número GPIO da Juca é o do ESP32-S3, não o do Raspberry.

| Jumper | J5 | Sinal Juca | GPIO ESP32 | Pi físico | BCM | Função sugerida |
|---|---:|---|---:|---:|---:|---|
| JP1 | 1 | SDA | 40 | 3 | 2 | I²C SDA |
| JP2 | 2 | SCL | 39 | 5 | 3 | I²C SCL |
| JP3 | 3 | TXD0 | 43 | 10 | 15 | UART: ESP TX → Pi RX |
| JP4 | 4 | RXD0 | 44 | 8 | 14 | UART: Pi TX → ESP RX |
| JP5 | 5 | GPIO38 | 38 | 24 | 8 | SPI0 CE0 |
| JP6 | 6 | GPIO37 | 37 | 21 | 9 | SPI0 MISO; depende da memória |
| JP7 | 7 | GPIO36 | 36 | 23 | 11 | SPI0 SCLK; depende da memória |
| JP8 | 8 | GPIO35 | 35 | 19 | 10 | SPI0 MOSI; depende da memória |
| JP9 | 9 | GPIO45 | 45 | 15 | 22 | GPIO; restrição de boot/VDD_SPI |
| JP10 | 10 | GPIO48 | 48 | 12 | 18 | PWM0 / GPIO; conferir tensão |
| JP11 | 11 | GPIO47 | 47 | 33 | 13 | PWM1 / GPIO; conferir tensão |
| JP12 | 12 | GPIO46 | 46 | 16 | 23 | GPIO; restrição de boot |
| JP13 | 13 | GPIO3 | 3 | 18 | 24 | GPIO; restrição de JTAG |

O mapeamento favorece I²C, UART, SPI0 com um chip select e dois canais PWM do Raspberry. As funções do ESP precisam ser configuradas no firmware, inclusive pelo GPIO matrix quando aplicável. A escolha de periférico não é feita pelo jumper: o componente somente une os dois lados da linha. Um GPIO pode ser usado em outra função digital compatível com o software e as restrições elétricas.

Os BCM0/1 do Raspberry, físicos 27/28, permanecem isolados para não ocupar os pinos de identificação HAT. Os demais pinos do Pi sem destino na tabela ficam sem ligação no shield, exceto os de alimentação indicados abaixo.

## Alimentação

| Juca | Destino | Observação |
|---|---|---|
| J11-2, +5 V | Pi físicos 2 e 4 | Alimentação permanente por cobre |
| J11-4, GND | Pi físico 9 | Referência comum permanente, sem JW3 |
| J11-1, +BATT | Sem ligação | A bateria bruta não deve ir ao header do Pi |
| J11-3, +3,3 V | Sem ligação | Evita unir saídas dos reguladores das duas placas |

A capacidade real da fonte da Juca e a tensão no Raspberry ainda precisam ser verificadas sob carga, com a câmera e os motores em uso. A inscrição “+5 V” no projeto não substitui essa medição. Evitar alimentar o Pi por outra fonte simultaneamente sem gestão apropriada de alimentação.

## Configurações de uso

- **UART básica:** instalar JP3 e JP4; habilitar a UART no Raspberry e no ESP. O cruzamento TX/RX da revisão anterior foi preservado. Se o projeto só usa Pi → ESP, JP4 é a linha de transmissão correspondente.
- **I²C:** instalar JP1 e JP2 juntos, depois de definir a coordenação do barramento compartilhado entre Pi, ESP e MPU-6050. BCM2/3 já possuem pull-ups de 1,8 kΩ no Pi; o shield não acrescenta outros. O módulo MPU pode ter seus próprios resistores.
- **SPI0:** instalar JP5 a JP8 somente se os pinos do módulo ESP estiverem disponíveis. A proposta considera Pi como controlador e ESP como periférico; configurar ambas as pontas no software.
- **PWM/GPIO:** instalar JP10 e/ou JP11 apenas após confirmar compatibilidade com lógica de 3,3 V.
- **GPIO com restrição de boot:** avaliar JP9, JP12 e JP13 individualmente, incluindo os estados elétricos durante reset e inicialização.

Desligar as alimentações antes de alterar os seletores. Após soldar, medir continuidade somente na linha escolhida e verificar ausência de curto com os jumpers vizinhos. Manter os outros seletores abertos até que tenham uma função definida. Não configurar duas saídas para forçar níveis opostos na mesma linha; também evitar sinais aplicados a uma placa desligada. Os jumpers não fornecem proteção, tradução de tensão ou isolamento.

## Restrições do módulo ESP32

O KiCad original identifica U5 apenas como **ESP32-S3-WROOM-1**, sem o sufixo da variante de memória. Conferir a marcação completa do componente físico antes de habilitar os grupos abaixo.

| Seletores | Condição |
|---|---|
| JP6 / JP7 / JP8 | GPIO37/36/35 são usados pela PSRAM Octal nos módulos com ESP32-S3R8/R16V. Nessas variantes, manter os três abertos. |
| JP10 / JP11 | GPIO48/47 operam no domínio de **1,8 V** nas variantes R16V. Nelas, não conectar diretamente ao Pi de 3,3 V; seria necessário um circuito de conversão de nível. |
| JP9 | GPIO45 participa da seleção de VDD_SPI no boot. A Juca possui R14 de 10 kΩ para GND. Evitar que o Pi force nível alto durante reset; os detalhes dependem da variante/eFuse. |
| JP12 | GPIO46 participa da configuração de boot e mensagens ROM. Deve estar baixo para entrar no modo de download quando GPIO0 estiver baixo. |
| JP13 | GPIO3 participa da seleção de JTAG, conforme eFuse. Conferir o efeito na depuração e no reset antes de habilitar. |

GPIO46 é listado como I/O/T no datasheet oficial atual; não é tratado aqui como “somente entrada”. A presença de um destino roteado não significa que o sinal esteja livre para uso em toda variante do módulo.

## Montagem mecânica e soldagem

Os soquetes J5, 1×13, e J11, 1×04, ficam embaixo do shield, encaixando nos pinos machos existentes da Juca. O soquete JPI1, 2×20, fica em cima; o Pi recebe um conector macho apontando para baixo. O Raspberry permanece sobre a região de expansão/MPU, com microSD para o topo e CSI/flat para baixo na vista superior do documento.

As trilhas dos conectores chegam pelo lado acessível à solda: **F.Cu em J5/J11**, **B.Cu em JPI1**. A antiga exigência de afastar o plástico dos soquetes inferiores 2-3 mm do cobre não se aplica a este roteamento de duas faces. Ainda é necessário escolher terminais e espaçadores compatíveis com a espessura da PCB e o encaixe completo dos conectores.

| Peça | Quantidade / especificação |
|---|---|
| PCB | 1, duas faces, 48 × 88 × 1,6 mm previstos |
| Soquetes | 1×13, 1×04 e 2×20, passo 2,54 mm |
| Conector macho do Pi | 1, 2×20, apontando para baixo |
| Seletores de sinal | Até 13 jumpers/resistores de 0 Ω 1206; não montar os não utilizados |
| H1-H4 | Fixação Juca, M3, furos de 3,2 mm |
| H5-H8 | Fixação Pi, M2,5, furos de 2,75 mm |

Respeitar as reservas para cabeças/arruelas: diâmetro máximo de 7 mm em H1-H4 e 6,2 mm em H5-H8. A altura dos espaçadores depende dos conectores reais totalmente encaixados e da folga sobre o MPU. Fixadores metálicos não devem tocar cobre.

## Fabricação de duas faces

As trilhas de sinal usam 0,508 e 0,762 mm (20 e 30 mil); alimentação e retorno principais, 1,8 mm. A separação mínima de projeto é 0,508 mm (20 mil). São 23 vias, com ilha de 1,8 mm e furo de 0,6 mm. O projeto usa vias comuns entre F.Cu e B.Cu; não utiliza microvias.

Para fabricação industrial, usar duas camadas com furos/vias metalizados. Para fabricação CNC ou caseira, a máquina não faz metalização automaticamente. Alinhar rigorosamente as faces e garantir a passagem elétrica em **cada via** com metalização, rebite ou fio curto compatível com o furo de 0,6 mm, soldado dos dois lados e cortado rente. Conferir encaixe e soldabilidade em uma amostra. Um furo sem metalização não une as faces. Executar e testar essas passagens antes dos conectores; não contar com o próprio terminal do conector para uma transição de face não soldada.

O PDF contém moldes vetoriais 1:1. Imprimir a **100%, sem ajustar à página**, e medir a barra de 50 mm. A vista inferior do cobre é espelhada em relação à superior; um processo de transferência de toner pode acrescentar outro espelhamento. Os moldes servem para conferência, e os Gerbers/furações estão em `fabricacao/`. A furação é fornecida em um único arquivo Excellon com PTH e NPTH, conforme o manual do IFSC.

## Regras CNC do IFSC: R03 → R04

| Parâmetro | R03 | R04 |
|---|---|---|
| Separação mínima de cobre | 0,300 mm | 0,508 mm = 20 mil |
| Trilhas de sinal | 0,500 mm | 0,508 / 0,762 mm = 20 / 30 mil |
| Alimentação e GND principais | 1,800 mm | 1,800 mm |
| Diâmetro / furo de via | 1,600 / 0,800 mm | 1,800 / 0,600 mm |
| Diâmetro das ilhas de J11 | 2,200 mm | 2,000 mm |
| Espaço entre ilhas vizinhas de J11 | 0,340 mm | 0,540 mm |
| Centro do banco de jumpers, y a partir do topo | 9,000 mm | 7,000 mm; 2 mm acima |
| Placa, conectores e fixação | 48 × 88 mm; posições existentes | Preservados |
| Mapeamento elétrico | 13 sinais com 0 Ω 1206 | Preservado |

O material **Curso: Laboratório de Pesquisa Avançada em Eletrônica | IFSC**, fornecido em PDF pelo usuário, informa na página 4 clearance acima de 12 mil, com 20 mil recomendados, trilhas de 20 a 30 mil, com 30 mil recomendados, e vias de 1,8 / 0,6 mm. A R04 adota a separação e as vias recomendadas; os sinais usam 30 mil onde há espaço e 20 mil nas rotas e escapes da região congestionada, dentro da faixa permitida. As linhas repetidas “uVia Drill” não foram usadas para introduzir microvias.

A página 6 pede Excellon com **PTH and NPTH in a single file**. O arquivo combinado contém **88 furos: 57 de conectores, 23 vias e 8 de fixação**. Usar esse arquivo junto de F.Cu, B.Cu e Edge.Cuts, mantendo a referência comum de coordenadas. A classificação PTH no CAD indica a intenção elétrica do furo; não significa que uma CNC tenha metalizado a parede.

### Registro e orientação no CAM

O material orienta espelhar a camada inferior e referenciar um furo de alinhamento nas páginas 6-7. Definir a origem e o eixo de virada conforme a fixação real da máquina. Manter cobre, furos e corte registrados, com as transformações correspondentes à face trabalhada, sem aplicar o espelhamento duas vezes. Comparar o CAM com a vista 3D do KiCad e os moldes do PDF antes de fabricar.

Os oito furos mecânicos foram mantidos. Eles podem servir como referências de alinhamento se forem adequados ao dispositivo do laboratório; confirmar isso no CAM e no método de fixação. Não foram acrescentados furos de registro nem alterada a mecânica da placa.

### Limites e validação de fabricação

A seção de duas faces nas páginas 15-16 do PDF fornecido contém trechos de preenchimento e não fornece um procedimento completo. Confirmar a sequência de virada, registro e usinagem com o laboratório. A folga CAD de 0,508 mm deve acomodar a ferramenta efetiva e suas tolerâncias; inspecionar os caminhos de isolamento e verificar se todos os espaços podem ser usinados.

Este pacote não contém G-code. Avanços, rotações, profundidades, compensações de ferramenta e nivelamento devem ser definidos no procedimento local para a ferramenta, material e máquina efetivamente utilizados. Não foram copiados os valores de avanço do PDF, que apresentam unidades ambíguas. Fazer uma amostra para conferir isolamento, furação de 0,6 mm e conexão entre faces antes de montar os conectores.

## Verificação antes do uso

O arquivo nativo foi verificado no KiCad 7: **0 violações de DRC, 0 conexões pendentes e 0 erros de footprint**. A verificação de conexões passou com 28 redes, 83 pads e os 13 seletores inicialmente abertos. Esses resultados verificam o projeto digital, sem substituir o ensaio físico.

Comparar o molde com J5, J11 e os furos reais. Conferir orientação e números dos conectores; verificar a continuidade de +5 V/GND, das vias e dos seletores montados, além da ausência de curtos. Validar os 5 V sob carga antes de encaixar e energizar o Raspberry. As verificações digitais do pacote não são um ensaio físico da alimentação ou da montagem.

## Fontes

- IFSC/LPAE, **Curso: Laboratório de Pesquisa Avançada em Eletrônica**, PDF fornecido pelo usuário, exportado em 09/11/2026. Regras: p. 4; Excellon e alinhamento: pp. 6-7; seção incompleta de duas faces: pp. 15-16. Origem indicada no documento: https://moodle.ifsc.edu.br/course/view.php?id=1480

- Projeto Juca: `hardware/electronics/Kicad/robo_2wd.kicad_pcb` e `robo_2wd.kicad_sch`, do arquivo original `Juca-main.zip`.
- Espressif, ESP32-S3-WROOM-1/1U, datasheet v1.8, pinagem e configuração de boot: https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf
- ESP-IDF, GPIO do ESP32-S3: https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/gpio.html
- Raspberry Pi, GPIO, alimentação e interfaces: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html
- Raspberry Pi Zero 2 W, desenho mecânico: https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-mechanical-drawing.pdf

Consulta técnica: 09/11/2026. O mapeamento em formato estruturado está em `mapeamento_pinos.json`.
