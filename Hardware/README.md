# Hardware do TCC

Esta pasta reúne os projetos eletrônicos e os registros de integração física do sistema. O código continua em [FollowBot](../followbot_mvp_audited/followbot_mvp_audited/README.md), e a redação acadêmica em [Documentacao](../Documentacao/).

| Elemento | Papel no sistema | Material disponível |
|---|---|---|
| Raspberry Pi Zero 2 W | Captura, detecção de pessoas e cálculo dos comandos | Integração descrita na documentação do software |
| Câmera CSI, sensor identificado como OV5647 | Aquisição de imagens diretamente no Pi | [Roteiro de câmera e testes](../followbot_mvp_audited/followbot_mvp_audited/INSTALL_TEST.md) |
| Shield Juca / Pi Zero 2 W | Interligação UART, alimentação e suporte mecânico | [Guia da placa e revisão R02](Juca_PiZero2_Shield/README.md) |
| Placa Juca / ESP32 e carrinho | Recepção dos comandos e acionamento existente dos motores | Esquema completo e revisão da Juca ainda não incorporados |

## Organização das revisões

Cada placa tem uma pasta própria. Arquivos recebidos ficam preservados em uma revisão identificada; análises e decisões do TCC ficam fora dessa revisão. Quando iniciarmos uma adaptação, criaremos a próxima revisão com registro das mudanças e novas saídas de fabricação. Gerbers antigos não devem ser tratados como saídas de um CAD modificado.

Nesta importação não foi alterado o circuito da R02 nem configurada a UART do equipamento. Os arquivos da placa e seus relatórios permitem estudar o projeto; a validação do conjunto montado exige os ensaios descritos na análise.
