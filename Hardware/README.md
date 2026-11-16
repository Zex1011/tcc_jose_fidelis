# Hardware do TCC

Esta pasta reúne os projetos eletrônicos e os registros de integração física do sistema. O código continua em [FollowBot](../followbot_mvp_audited/followbot_mvp_audited/README.md), e a redação acadêmica em [Documentacao](../Documentacao/).

| Elemento | Papel no sistema | Material disponível |
|---|---|---|
| Raspberry Pi Zero 2 W | Captura, detecção de pessoas e cálculo dos comandos | Integração descrita na documentação do software |
| Câmera CSI, sensor identificado como OV5647 | Aquisição de imagens diretamente no Pi | [Roteiro de câmera e testes](../followbot_mvp_audited/followbot_mvp_audited/INSTALL_TEST.md) |
| Shield Juca / Pi Zero 2 W | Sinais selecionáveis, alimentação e suporte mecânico | [Guia da placa: R05 em trabalho; R04/R02 históricas](Juca_PiZero2_Shield/README.md) |
| Placa Juca / ESP32 e carrinho | Recepção dos comandos e acionamento existente dos motores | Esquema completo e revisão da Juca ainda não incorporados |

## Organização das revisões

Cada placa tem uma pasta própria. Arquivos recebidos ficam preservados em uma revisão identificada; análises e decisões do TCC ficam fora dessa revisão. Quando iniciarmos uma adaptação, criaremos a próxima revisão com registro das mudanças e novas saídas de fabricação. Gerbers antigos não devem ser tratados como saídas de um CAD modificado.

A [R05](Juca_PiZero2_Shield/R05/README.md) adapta a montagem para o Raspberry com componentes voltados para baixo e CSI oposto a J5. Usa 13 jumpers PTH com capinhas, furos elétricos de 1 mm e novo roteamento. A R04 recebida em 16/11/2026 e a R02 conservam os bytes originais; a R03 não foi recebida. Consulte o README da R05 para o estado das verificações e as pendências de fabricação, montagem e integração UART.
