# Revisão técnica da shield Juca / Pi Zero 2 W — R04

**Revisão recebida:** R04, datada de 09/11/2026. **Incorporação ao projeto:** 16/11/2026. Situação: referência atual de hardware; fabricação e integração física pendentes.

## Arquivos e preservação

O [ZIP original](../origem/Juca_PiZero2_Shield_R04.zip) foi preservado e seus **37 arquivos** foram extraídos em [R04](../R04/), sem alteração de bytes. SHA-256 do ZIP: `9280bf475b4d60a5972cab2b5af624c640d00af0b831829559bf93a90abe0d67`. O [manifesto](manifesto_origem_R04.json) registra o inventário e os hashes de todos os arquivos.

O pacote inclui fontes KiCad, bibliotecas locais, guia PDF, geometria em JSON, mapeamento JSON/CSV, relatórios originais de DRC/conexões e arquivos de fabricação. A [R02](../R02/) e seus relatórios permanecem preservados. A R03 é mencionada no README da R04, mas não está disponível neste repositório.

## Comparação direta com a R02

| Item | R02 | R04 |
|---|---|---|
| Contorno | 48 × 88 mm | Mesmo contorno |
| Conectores e furos | J5, J11, JPI1 e oito furos | Posições preservadas, conferidas nos arquivos |
| Pads elétricos | 59, incluindo JW3 | 83: 57 de conectores e 26 dos seletores |
| Segmentos de trilha | 24 em B.Cu | 452 em F.Cu/B.Cu |
| Vias | 0 | 23, diâmetro de 1,8 mm e furo de 0,6 mm |
| Sinais | Duas linhas UART diretas | 13 linhas com seletores de 0 Ω 1206, DNP |
| Terra | Redes separadas unidas pelo fio JW3 | Rede GND compartilhada no CAD, sem JW3 |
| Furação | Arquivos PTH/NPTH separados | Excellon combinado: 88 furos |

Os conectores continuam com a mesma orientação de montagem: J5/J11 embaixo e JPI1 em cima; o Raspberry recebe pinos machos apontando para baixo. A R04 leva as trilhas de J5/J11 à face superior, acessível à solda, e as de JPI1 à inferior. A folga de 2–3 mm sob os soquetes inferiores, exigida pela soldagem em uma única face na R02, deixa de ser uma exigência desse roteamento. As alturas reais dos conectores e espaçadores ainda precisam ser medidas.

## Seletores e UART do FollowBot

Cada pino de sinal de J5 possui um percurso com duas redes separadas por um espaço para componente. **Todos os 13 seletores estão marcados como DNP no esquemático**; a conexão depende da montagem do respectivo 0 Ω 1206. Isso define a intenção de montagem, sem comprovar o estado de uma placa física.

| Percurso | Mapeamento recebido | Função no protocolo atual |
|---|---|---|
| JP3 | J5-3 / GPIO43 ESP → físico 10 / BCM15 Pi | Retorno de ACK do ESP ao Pi |
| JP4 | Físico 8 / BCM14 Pi → J5-4 / GPIO44 ESP | Envio de comandos ao ESP |
| Alimentação | J11-2 → físicos 2 e 4 | 5 V permanente |
| Terra | J11-4 → físico 9 | GND permanente por trilhas e vias |

O FollowBot espera uma resposta `ACK,<seq>` para cada comando. Assim, **montar somente JP4 não atende ao protocolo atual**, mesmo que permita transmitir Pi → ESP. A integração UART exige JP3 e JP4, porta Linux correta e firmware compatível. O [protocolo serial](../../../followbot_mvp_audited/followbot_mvp_audited/SERIAL_PROTOCOL.md) e o [teste STOP/ACK](../../../followbot_mvp_audited/followbot_mvp_audited/scripts/serial_smoke_test.py) continuam aplicáveis após a validação elétrica.

O mapeamento agora identifica o módulo como ESP32-S3-WROOM-1 e os GPIOs da UART como 43/44. Isso é mais específico que o material da R02, mas o esquema/PCB completos da Juca e a variante física do módulo continuam ausentes. A pinagem TXD0/GPIO43 e RXD0/GPIO44 corresponde ao [datasheet oficial do módulo](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf), seção 3.3; falta verificar que essa é a conexão e configuração da Juca instalada.

Não foi criado perfil UART nem alterado o firmware de exemplo. Ele ainda precisa de integração com o acionamento real, escolha explícita da UART e revisão da parada/watchdog. No Ubuntu do Raspberry, permanecem pendentes a porta, as permissões e a eventual ocupação dos pinos por console ou outros serviços. ACK comprova resposta de protocolo, não movimento dos motores.

## Linhas adicionais e variante do ESP

O [mapeamento completo](../R04/mapeamento_pinos.json) sugere I²C em JP1/JP2, SPI em JP5–JP8 e outras funções digitais em JP9–JP13. Esses destinos não habilitam periféricos automaticamente. A disponibilidade das linhas e a coordenação dos barramentos dependem do firmware e do módulo instalado.

A documentação oficial do ESP32-S3 aponta restrições para pinos usados pela memória e para GPIO3/45/46 na inicialização. No módulo, GPIO35/36/37 ficam indisponíveis quando ligados à PSRAM Octal; GPIO47/48 têm condições de tensão específicas nas variantes R16V. Conferir a marcação completa antes de habilitar esses grupos. [Guia de GPIO do ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/gpio.html), [datasheet do módulo, notas da pinagem](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf).

Para o primeiro ensaio do protocolo atual, somente as duas linhas UART têm função definida. As demais podem permanecer abertas. Os seletores não fornecem conversão de nível, proteção nem isolamento da alimentação.

## Alimentação e fabricação

A alimentação continua ligada independentemente dos seletores. A R04 não acrescenta regulador ou gerenciamento de fontes: confirmar os 5 V da Juca sob carga e a coexistência com alimentação pelo USB do computador. +BATT e +3,3 V de J11 permanecem sem ligação ao Pi.

A R04 é efetivamente um projeto de **duas faces**: inclui Gerbers F.Cu e B.Cu, máscaras, serigrafias, contorno e um Excellon combinado. Os 88 furos correspondem a 57 terminais de conectores, 23 vias e oito fixações. A passagem elétrica entre faces nas vias precisa existir na fabricação; em usinagem sem metalização, requer processo de interligação definido e validado no laboratório.

As regras salvas no `.kicad_pro` incluem separação e largura mínima de 0,508 mm; o roteamento usa sinais de 0,508/0,762 mm e alimentação/retorno de 1,8 mm. A declaração de adequação às regras CNC do IFSC vem do material recebido. O manual de fabricação citado, a ferramenta, o CAM e o processo físico não acompanham esta importação e não foram verificados como procedimento de laboratório. Não há G-code no pacote.

O [guia original](../R04/Guia_de_montagem_R04.pdf) tem seis páginas: layout, pinagem, seletores, montagem, moldes e preparação CNC. As páginas foram lidas e inspecionadas visualmente. O molde está na página 5; usar o PDF em escala e conferir sua barra de 50 mm, em vez de imprimir a prévia do README como gabarito.

## Conferência independente e limites

O [verificador local](verificar_r04.py) produziu [este resultado](revisao_estrutural_R04.json): `PASS_STRUCTURAL_CHECKS_ONLY`.

- Integridade do ZIP e dos 37 arquivos extraídos, com SHA-256 e comparação de bytes.
- 28 redes nomeadas, 83 pads, 452 segmentos, 23 vias e oito furos de montagem.
- Concordância pino a pino entre esquemático, PCB, geometria, mapa JSON e CSV; 13 seletores DNP.
- Dimensões do contorno e posições de conectores/furos preservadas em relação à R02.
- Roteamento e vias serializados compatíveis com o manifesto geométrico; dimensões e posições dos 88 furos Excellon compatíveis com a PCB.
- Regras persistidas do projeto e presença das camadas principais de fabricação.

O verificador confere a estrutura e as declarações dos arquivos. **Não calcula a conectividade geométrica do cobre, curtos ou distâncias de isolamento.** O DRC original informa zero violações, zero conexões pendentes e zero erros de footprint; é um resultado fornecido com o projeto, não reexecutado nesta incorporação. Também não houve ensaio de fonte, montagem, UART ou motores.

## Próximos passos

1. Confirmar a revisão da Juca e a marcação completa do ESP32-S3 físico.
2. Definir fabricação de duas faces, registro, acabamento das vias e inspeção elétrica com o laboratório.
3. Conferir conectores/espaçadores e alimentação, inclusive uso do USB para depuração.
4. Montar JP3/JP4 para o protocolo atual, configurar UART e firmware e validar STOP/ACK.
5. Integrar e ensaiar acionamento, parada e watchdog antes dos testes de seguimento.

Esta incorporação atualiza o acervo e a referência de hardware. A documentação acadêmica poderá descrever a revisão efetivamente fabricada e os resultados de validação quando esses ensaios existirem.
