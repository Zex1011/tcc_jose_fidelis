# Shield Juca / Raspberry Pi Zero 2 W — R02

Adaptador de **48 × 88 mm**, com cobre somente na face inferior (**B.Cu**), sem vias e com **um jumper de fio isolado, JW3**, na face superior. As duas linhas UART usam trilhas no cobre inferior. Encaixa nos conectores J5 e J11 existentes da Juca e sustenta o Raspberry sobre a região do MPU-6050.

**Estado:** validado digitalmente no KiCad 7.0.11; a fonte, os conectores reais e a montagem ainda precisam de conferência física.

## Abrir e editar

Abra `Juca_PiZero2_Shield_R02.kicad_pro` no KiCad 7 ou posterior. Mantenha juntos o esquemático, a PCB, `JucaShield.kicad_sym`, a pasta `JucaShield.pretty` e as tabelas de bibliotecas. Os símbolos e footprints necessários estão incluídos.

O arquivo `geometria_e_conexoes.json` registra posições, trilhas e percurso de JW3. Consulte `verificacao_DRC.txt` para a checagem de regras da PCB e `verificacao_conexoes.json` para a conferência das cinco redes do esquemático/PCB e da continuidade prevista após instalar JW3. Essas verificações não substituem o teste da placa montada.

## Ligações

Os números abaixo são **pinos físicos**, não números GPIO do Raspberry.

| Origem na Juca | Destino no Raspberry | Caminho |
|---|---|---|
| J5-3, TX do ESP32 | JPI1-10, RX | Trilha B.Cu: ESP_TX |
| J5-4, RX do ESP32 | JPI1-8, TX | Trilha B.Cu: ESP_RX |
| J11-2, +5 V | JPI1-2 e JPI1-4 | Trilhas |
| J11-4, GND | **JPI1-9, GND** | **JW3 obrigatório** |

J11-1 (+BATT), J11-3 (+3,3 V), os demais pinos de J5 e os demais pinos de JPI1 não recebem trilhas. O pino 6 do Raspberry também fica sem ligação no shield: o retorno usado é o **pino 9**.

## Conectores e soldagem em uma face

- J5: soquete fêmea 1×13, passo 2,54 mm, montado embaixo.
- J11: soquete fêmea 1×4, passo 2,54 mm, montado embaixo.
- JPI1: soquete fêmea 2×20, passo 2,54 mm, montado em cima.
- Raspberry: header macho 2×20, com os pinos apontando para baixo.

**J5 e J11 precisam de terminais longos.** Deixe seus corpos plásticos cerca de **2–3 mm afastados do B.Cu**, para alcançar os terminais com o ferro. Soquetes comuns encostados na face de cobre escondem as ilhas e impedem essa soldagem. Para PCB de 1,6 mm, folga de 3 mm e protrusão de 0,5 mm, use cauda de pelo menos **5,1 mm**; confirme a peça antes de comprar ou soldar.

Todas as ligações elétricas são soldadas no B.Cu. Os pads THT do modelo KiCad não exigem metalização dos furos para esta montagem doméstica. Solde JW3 e confira a continuidade antes de encaixar o Raspberry.

## Jumper de GND

Use fio isolado, com condutor de aproximadamente **0,5–0,65 mm de diâmetro**. JW3 liga GND_JUCA a GND_PI, completando o retorno pelo pino físico 9 do Raspberry. O percurso entre os furos é de aproximadamente **6 mm**. Corte com sobra para as pernas e as dobras e mantenha a isolação sobre as trilhas.

**JW3 é obrigatório.** JW1 e JW2 foram removidos nesta revisão: a UART já está ligada pelas trilhas B.Cu.

## Fixação

H1–H4 correspondem aos furos da Juca: broca de **3,2 mm**, para M3. H5–H8 fixam o Raspberry: broca de **2,75 mm**, para M2,5. Foram reservados raios de 3,5 mm e 3,1 mm, respectivamente, ao redor desses centros. A menor folga entre essas áreas é aproximadamente **0,74 mm**; confira as cabeças e os espaçadores reais, preferindo peças menores ou de nylon onde necessário.

A origem do shield corresponde a (62; 66) mm no CAD da Juca. O Raspberry começa em (67,5; 81) mm, girado 90° no sentido horário: microSD para cima e CSI para baixo na vista superior do conjunto.

Escolha a altura dos espaçadores após medir o encaixe completo dos conectores, incluindo a folga de soldagem e os componentes sob o shield. O conjunto deve apoiar sem forçar a PCB ou deixar conectores parcialmente encaixados.

## Fabricação e primeira alimentação

`fabricacao/` contém Gerbers de B.Cu, contorno e serigrafia, além das furações PTH/NPTH. Não há Gerber F.Cu. Os nomes PTH/NPTH seguem a classificação do KiCad; a montagem descrita usa furos sem metalização.

- `cobre_B_Cu_visto_de_cima.svg`: coordenadas da vista superior do KiCad; espelho da vista inferior.
- `cobre_B_Cu_vista_inferior.svg`: aparência ao olhar diretamente o cobre inferior.

Para transferência de toner com a imagem encostada no cobre, a arte **visto_de_cima** inverte durante a transferência. Confirme o processo e imprima em **100%**, sem ajustar à página. Confira 48 × 88 mm e passo de 2,54 mm antes da corrosão.

O projeto Juca prevê entrada de bateria entre 6 e 12 V; o Raspberry recebe apenas o **+5 V regulado do J11**. Não ligue +BATT ao Raspberry nem una os barramentos de 3,3 V. Verifique tensão e estabilidade sob carga com Raspberry e câmera. Evite alimentação USB externa simultânea no Raspberry sem definir o gerenciamento das fontes.

Antes de energizar, confira orientação, ausência de curto entre +5 V/GND e continuidade de cada linha da tabela. Configuração UART, protocolo e ROS ficam a cargo do software.

## Referências

- [Desenho mecânico oficial do Raspberry Pi Zero 2 W](https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-mechanical-drawing.pdf)
- [Esquemático oficial do Raspberry Pi Zero 2 W](https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-reduced-schematics.pdf)
