# Shield Juca / Raspberry Pi Zero 2 W

A **[R05](R05/README.md)** é a revisão mantida no repositório. Ela conecta sinais e alimentação entre a Juca e o Raspberry Pi Zero 2 W, com o Pi voltado para baixo, CSI oposto a J5, jumpers PTH com capinhas e furos elétricos de 1 mm. A câmera permanece no CSI do Raspberry; o acionamento dos motores fica na Juca/ESP32.

## Arquivos da revisão atual

- [Projeto KiCad](R05/Juca_PiZero2_Shield_R05.kicad_pro), [esquemático](R05/Juca_PiZero2_Shield_R05.kicad_sch) e [PCB](R05/Juca_PiZero2_Shield_R05.kicad_pcb).
- [Montagem, pinagem e furação](R05/README.md).
- [Revisão elétrica e de layout](R05/documentacao/REVISAO_ELETRICA_E_LAYOUT.md).
- [Prévia do roteamento nas duas faces](R05/documentacao/roteamento_R05.png) e [orientação de montagem](R05/documentacao/orientacao_R04_R05.png).
- [Gerbers e furação](R05/fabricacao/) e [estado das verificações](R05/verificacao/README.md).

Abra o projeto com KiCad 9.0.8 ou compatível. As bibliotecas locais `JucaShield.kicad_sym` e `JucaShield.pretty`, assim como suas tabelas, devem acompanhar os fontes; os caminhos usam `${KIPRJMOD}`. O histórico dos arquivos CAD, a preparação CAM e os testes físicos têm escopos distintos: consulte os relatórios atuais antes de fabricar.

## Integração com o FollowBot

O protocolo serial exige **JP3 e JP4 fechados**, para comandos e ACKs. J5-3/TX do ESP chega ao pino físico 10/GPIO15/RX do Raspberry; o pino físico 8/GPIO14/TX retorna por JP4/J5-4 ao RX do ESP. Os demais jumpers permanecem abertos enquanto seu uso não estiver definido.

**JP13 liga GPIO3 da Juca ao GPIO17/pino físico 11 do Raspberry.** O pino físico 18 fica sem conexão na shield. As demais conexões constam na [tabela de pinagem](R05/pinagem_R05.csv).

J11-2 alimenta os pinos físicos 2/4 do Pi com +5 V; J11-4 liga o GND ao físico 9. Remover as capinhas não interrompe essa alimentação. A shield não inclui regulador, conversão de níveis ou seleção entre fontes. Conferir a alimentação, a variante do ESP32-S3 e os níveis dos sinais antes dos ensaios.

Em CNC sem metalização, cada via precisa de ligação física entre as duas faces. Diâmetro da broca, isolamento, registro entre faces e soldagem devem ser definidos no CAM e na montagem. O [guia da R05](R05/README.md) reúne essas condições; a configuração UART e o acionamento real ainda dependem da integração com o [FollowBot](../../followbot_mvp_audited/followbot_mvp_audited/README.md).

## Organização

```text
Juca_PiZero2_Shield/
├── README.md
├── R05/          CAD, bibliotecas, documentação e exportações atuais
└── analise/      verificadores da R05
```

Os verificadores da R05 usam os arquivos desta revisão e sua especificação explícita, sem depender das revisões antigas. Os comandos e os limites de cada teste estão em [verificacao/README.md](R05/verificacao/README.md).

## Histórico local

As pastas `R02/` e `R04/`, os respectivos ZIPs em `origem/` e suas análises específicas são mantidos apenas no computador, ignorados pelo Git. Não acompanham novos clones. A retirada do controle atual não reescreve os commits antigos que já contêm esses arquivos.

As menções a R02/R04 e a ilustração comparativa dentro da documentação da R05 registram a evolução do projeto. A R03 não foi recebida. Gerbers e moldes históricos não devem ser utilizados para fabricar o CAD atual.
