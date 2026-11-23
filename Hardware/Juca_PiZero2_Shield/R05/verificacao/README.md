# Verificação da R05

Relatórios gerados em 23/11/2026 com **KiCad 9.0.8**, a partir dos fontes desta revisão. O projeto usa clearance mínimo de **0,31 mm entre cobres de redes diferentes**, largura mínima de trilha de **1,0 mm**, vias de 2,0/1,0 mm e furos elétricos de 1,0 mm. As restrições cobre–borda, cobre–furo e furo–furo permanecem em 0,508 mm. As regras ficam no `.kicad_pro`, que deve acompanhar a PCB.

A geometria conferida contém **185 segmentos e 41 vias**, incluindo a simplificação de `PI_GPIO8` em F.Cu de 13 para 3 segmentos. DRC/ERC e os relatórios estrutural e de fabricação foram atualizados para essa versão; os hashes no manifesto identificam os fontes e as exportações correspondentes.

- `DRC_R05.json`: regras geométricas, conexões abertas e correspondência com o esquemático.
- `ERC_R05.json`: regras elétricas do esquemático.
- `netlist_R05.net`: conexões exportadas do esquemático.
- `ESTRUTURA_R05.json`: posição e inversão do Pi, pinagem, furos, regras do projeto, larguras constantes por rede, chegada dos sinais à face de solda dos pads utilizados, direção dos segmentos, candidatos a pontas soltas e vias utilizadas em uma só face.
- `FABRICACAO_R05.json`: comparação de cada furo Excellon com o CAD, inventário dos Gerbers, funções das camadas e hashes dos arquivos.
- `manifesto_cad_R05.json`: hashes dos fontes, bibliotecas locais, dados de pinagem, relatórios e saídas de fabricação desta verificação.

## Repetir as verificações

Com `kicad-cli` disponível no PATH, a partir da raiz do repositório:

```powershell
kicad-cli pcb drc --schematic-parity --all-track-errors --format json -o Hardware/Juca_PiZero2_Shield/R05/verificacao/DRC_R05.json Hardware/Juca_PiZero2_Shield/R05/Juca_PiZero2_Shield_R05.kicad_pcb
kicad-cli sch erc --format json -o Hardware/Juca_PiZero2_Shield/R05/verificacao/ERC_R05.json Hardware/Juca_PiZero2_Shield/R05/Juca_PiZero2_Shield_R05.kicad_sch
kicad-cli sch export netlist --format kicadsexpr -o Hardware/Juca_PiZero2_Shield/R05/verificacao/netlist_R05.net Hardware/Juca_PiZero2_Shield/R05/Juca_PiZero2_Shield_R05.kicad_sch
python Hardware/Juca_PiZero2_Shield/analise/verificar_r05.py --drc Hardware/Juca_PiZero2_Shield/R05/verificacao/DRC_R05.json --erc Hardware/Juca_PiZero2_Shield/R05/verificacao/ERC_R05.json --output Hardware/Juca_PiZero2_Shield/R05/verificacao/ESTRUTURA_R05.json
python Hardware/Juca_PiZero2_Shield/analise/verificar_fabricacao_r05.py --output Hardware/Juca_PiZero2_Shield/R05/verificacao/FABRICACAO_R05.json
```

Os dois verificadores Python usam somente a biblioteca padrão. O verificador estrutural **lê**, mas não executa novamente, os relatórios nativos fornecidos: gere DRC/ERC e a netlist depois de qualquer mudança nos fontes.

As posições, os furos, a orientação e a pinagem esperados da R05 estão declarados explicitamente no verificador. Sua execução não depende dos arquivos R02/R04, que são mantidos apenas no arquivo local e não acompanham novos clones. A conferência estrutural atual inclui os contatos sem conexão e totaliza 435 verificações quando ambos os relatórios nativos são fornecidos.

As larguras verificadas são 1,0 mm em `PI_GPIO*` e `JUCA_*`, e 2,0 mm em `+5V`/`GND`. A face de chegada exigida é F.Cu para J5/J11 e B.Cu para JPI1/JP1–JP13. Esse teste procura contato geométrico direto com cobre da mesma rede na face indicada; não pressupõe metalização do furo nem comprova o acesso físico do ferro de solda.

No KiCad, conferir **Configuração da placa → Regras de projeto → Restrições** e **Classes de rede**. O mínimo global e o clearance das classes devem acompanhar o critério de 0,31 mm. Apenas mudar a largura padrão de uma classe não modifica trilhas existentes nem impõe um mínimo ao DRC; por isso a largura mínima global também foi configurada. Consulte a [documentação oficial do KiCad](https://docs.kicad.org/9.0/en/pcbnew/pcbnew.html#board-setup). A largura efetiva da fresa/ponta e as tolerâncias da máquina continuam pendentes de confirmação para esse isolamento.

## Exportação usada

```powershell
kicad-cli pcb export gerbers -o Hardware/Juca_PiZero2_Shield/R05/fabricacao/ -l F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts --precision 6 Hardware/Juca_PiZero2_Shield/R05/Juca_PiZero2_Shield_R05.kicad_pcb
kicad-cli pcb export drill -o Hardware/Juca_PiZero2_Shield/R05/fabricacao/ --format excellon --drill-origin absolute --excellon-units mm --excellon-zeros-format decimal --generate-map --map-format svg --generate-report --report-path Hardware/Juca_PiZero2_Shield/R05/fabricacao/relatorio_furacao_R05.txt Hardware/Juca_PiZero2_Shield/R05/Juca_PiZero2_Shield_R05.kicad_pcb
```

O Excellon combina furos elétricos e mecânicos, com três diâmetros de broca: 1,0, 2,75 e 3,2 mm. O KiCad separa as vias e os terminais nos índices **T1 e T2, ambos de 1,0 mm**; a mesma broca atende os dois grupos. T3 e T4 correspondem a 2,75 e 3,2 mm. A origem é absoluta e o eixo Y segue a convenção da exportação KiCad; o verificador compara essa transformação com as coordenadas do CAD. Não espelhar manualmente os Gerbers para encaminhá-los a uma fábrica. Para a CNC, a orientação e o registro da segunda face pertencem à preparação CAM e à fixação utilizada na máquina.

## Alcance dos resultados

O DRC/ERC e os verificadores confirmam propriedades dos arquivos CAD. Os testes de pontas e ângulos têm os limites descritos no JSON; não provam, por si, ausência de toda sobreposição ou desvio redundante. O verificador de fabricação compara a furação e os metadados, sem reconstruir a geometria de cobre dos Gerbers.

Continuam pendentes a conferência CAM, o encaixe com os componentes reais, as alturas dos espaçadores, o acesso ao CSI, a continuidade após fabricação e os ensaios de alimentação. Em CNC sem metalização, as 41 vias precisam de fio ou outro processo que conecte eletricamente as duas faces.
