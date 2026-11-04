# Revisão inicial do TCC — 7 de outubro de 2026

Esta revisão cruza a introdução em Word, o modelo institucional em `Doc/projeto_base`, o código em `../followbot_mvp_audited/followbot_mvp_audited` e consultas realizadas no Windows. Propostas de experimento abaixo ainda precisam ser acordadas com o orientador; não são resultados obtidos.

## Entendimento do trabalho

Investigar em quais condições um Raspberry Pi Zero 2 W consegue executar localmente a percepção e o controle visual de um robô que segue uma pessoa. O ESP32 executa os comandos na plataforma existente. A contribuição pode ser a caracterização experimental da relação entre qualidade das detecções, latência e desempenho do seguimento, incluindo as limitações encontradas.

O núcleo do MVP já separa câmera, detector, seleção de alvo, controle, comunicação e registros. Há backends simulados, OpenCV, Picamera2, detector Ultralytics, controle proporcional por caixa delimitadora e serial com sequência/ACK/repetição. Isso oferece uma base para ensaios incrementais, mas não comprova ainda funcionamento do robô físico.

## Diferenças entre a introdução e a implementação

| Tema | Introdução em Word | Implementação atual / decisão necessária |
| --- | --- | --- |
| Seleção inicial | Escolha aleatória quando há várias pessoas | A configuração usa `first`; a primeira detecção não equivale a um sorteio. Definir a política e documentá-la. |
| Perda de alvo | Busca por rotação lenta segundo a tendência horizontal | O orquestrador envia STOP. A busca ainda precisa de estados, duração máxima, limites e critérios de recuperação/parada. |
| Distância | Calibração com distâncias conhecidas e avaliação experimental | O controle usa altura relativa da caixa; não há distância física calibrada. |
| Movimento | Referências de velocidade linear e angular | No MVP sem encoders, `v/w` são referências abstratas calibráveis, não velocidades medidas em m/s e rad/s. |
| Integração ESP32 | Plataforma existente recebe e executa comandos | `applyVelocityReference()` no firmware de exemplo é um ponto de integração vazio. ACK confirma processamento da mensagem, não movimento medido. |
| Câmera | Raspberry Pi Camera, modelo a preencher | A documentação cita a inscrição `UC436`; identificar sensor e interface antes de fechar a descrição. |
| Latência | Tempo entre aquisição da imagem e envio do comando | `cycle_total` inclui espera por ACK e exclui logging/debug posteriores. Não é a mesma métrica. Instrumentar os marcos de aquisição, envio e intervalo entre comandos. |

Não se deve alterar essas promessas silenciosamente: optar por implementá-las ou ajustar o escopo com o orientador.

## Problemas a corrigir antes dos experimentos

1. **Extrapolação indevida de benchmark.** `docs/BENCHMARK_RESULTS_2026-08-24.md` chama um teste desktop com limite de threads de simulação do Pi e conclui viabilidade a 27,8 Hz. O teste não demonstra desempenho no ARM Cortex-A53 com 512 MB. Os números devem permanecer identificados como desktop; viabilidade embarcada depende de medição no Pi. Além disso, definir variáveis OMP/BLAS não comprova quantas threads o NCNN efetivamente utilizou.
2. **Contrato de cores.** Os backends OpenCV e dataset convertem BGR para RGB, mas o detector passa o array diretamente à Ultralytics, cujo pré-processamento local espera BGR e converte novamente. Padronizar a representação de `Frame.image` e as adaptações de entrada e debug antes de comparar qualidade das detecções. Verificar separadamente o formato efetivo da Picamera2.
3. **Dependência opcional importada incondicionalmente.** `camera/__init__.py` importa `DatasetCamera`, que importa `cv2`; isso impede o modo mock em uma instalação mínima sem OpenCV, embora OpenCV seja anunciado como extra.
4. **Métrica de frequência incompleta.** `orchestrator.py` calcula `cycle_total` antes do logging e do debug visual. Para frequência efetiva, medir ciclos concluídos por tempo de parede e a distribuição do intervalo entre comandos; para latência, definir separadamente o marco de aquisição e o de envio. O timestamp atual da câmera é criado depois da leitura, não no instante de exposição do sensor.
5. **Integração e parada ainda precisam de ensaio físico.** O firmware de exemplo não aciona os motores. O STOP inicial no Python é uma tentativa que não impede continuar se o retorno indicar falha. Validar inicialização, perda de comunicação e watchdog na integração real.

O README e a formulação consolidada também têm trechos desatualizados: algumas decisões já consolidadas aparecem novamente como pendentes, e o backend OpenCV já existe embora a formulação o descreva como futuro.

## Verificações executadas nesta revisão

- Sete testes existentes passaram com `python -B -m unittest discover -s tests -v`.
- O pipeline mock executou 20 ciclos em memória, sem periféricos e sem gerar arquivo de log.
- A falha de importação do modo mock sem `cv2` foi reproduzida por simulação da dependência ausente.
- Não houve execução de motores, câmera física ou inferência no Raspberry.
- Os testes existentes não cobrem todos os problemas identificados; passar nesses testes não equivale à validação do robô.

## Diagnóstico da conexão USB no Windows

Na consulta, o dispositivo apareceu assim:

```text
Nome no Windows: Dispositivo Serial USB (COM6)
Descrição fornecida pelo dispositivo: RNDIS/Ethernet Gadget
Hardware ID: USB\VID_0525&PID_A4A2
Driver associado: usbser.inf
Serviço: usbser
```

O dispositivo anuncia rede USB, mas foi associado ao driver serial. Não apareceu adaptador de rede RNDIS. A consulta não encontrou NAT configurado nem endereço local em `192.168.7.0/24`.

As instruções do professor pressupõem uma interface de rede já funcional. Os endereços esperados são PC `192.168.7.1/24` e Pi `192.168.7.2`; o nome da interface precisa ser o que surgir neste computador. A conexão Wi-Fi consultada chama-se `Wi-Fi 2`, não `Wi-Fi`.

### Corrigir o reconhecimento antes de configurar IP

1. Abrir o Gerenciador de Dispositivos e localizar **Dispositivo Serial USB (COM6)**. Conferir o hardware ID acima para não alterar outro dispositivo.
2. Escolher **Atualizar driver → Procurar drivers no meu computador → Permitir que eu escolha**. Se a opção estiver disponível, selecionar **Adaptadores de rede → Microsoft → Remote NDIS Compatible Device**.
3. Se a categoria/modelo não aparecer, o [Microsoft Update Catalog tem um pacote com o hardware ID exato](https://www.catalog.update.microsoft.com/ScopedViewInline.aspx?updateid=38c84d13-eb1b-4327-aae5-e36e8cb7933d). A listagem foi consultada, mas o pacote não foi baixado nem instalado nesta revisão. O driver atual distribuído pelo projeto `raspberrypi/rpi-usb-gadget` usa outro ID (`2E8A:0013`), portanto não assumir que serve para esta imagem antiga.
4. Depois da associação correta, repetir `Get-NetAdapter` e identificar nome/índice e status do novo adaptador.

O Windows possui localmente `C:\Windows\INF\rndiscmp.inf`, com o modelo `Remote NDIS Compatible Device`, mas seu INF contém `ExcludeFromSelect=*`; por isso a disponibilidade desse modelo no assistente precisa ser verificada, e não foi assumida como garantida.

### Configurar e testar a rede após o adaptador aparecer

Em PowerShell administrativo, primeiro verificar os endereços já existentes na interface escolhida. O exemplo usa índice **12 apenas como marcador**; substituir pelo índice real do Raspberry:

```powershell
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, ifIndex
# Substituir 12 pelo índice REAL; não executar com o exemplo sem conferir.
Get-NetIPAddress -InterfaceIndex 12 -AddressFamily IPv4
# Se 192.168.7.1/24 ainda não estiver configurado nessa interface:
New-NetIPAddress -InterfaceIndex 12 -IPAddress 192.168.7.1 -PrefixLength 24
ping 192.168.7.2
Test-NetConnection 192.168.7.2 -Port 22
```

O nome de usuário SSH ainda precisa ser confirmado; uma senha isolada não informa o usuário. Não registrar credenciais no projeto.

NAT/encaminhamento ficam para compartilhar internet depois que o acesso local funcionar. A ligação direta PC–Pi na mesma sub-rede não depende de NAT. Nenhum driver, IP, NAT ou encaminhamento foi alterado nesta revisão.

Fontes técnicas: [identificador do gadget no Linux](https://raw.githubusercontent.com/torvalds/linux/master/drivers/usb/gadget/legacy/ether.c), [procedimento Microsoft de seleção do driver RNDIS, seção More Information](https://support.microsoft.com/en-us/servicing/os/windows/2020/04/0x0000001e-or-0x00000133-stop-error-when-you-transfer-data-through-a-usb-based-rndis-device-on-windo) e [IDs do driver atual da Raspberry Pi](https://github.com/raspberrypi/rpi-usb-gadget/tree/pios/trixie/windows). O artigo Microsoft é antigo; seu hotfix não faz parte desta orientação.

## Sequência recomendada

1. **Acesso ao Pi e inventário:** corrigir driver, testar SSH, confirmar sistema/arquitetura, câmera, espaço e memória. Registrar versões utilizadas.
2. **Topologia de conexões:** no Zero 2 W, a porta de dados usada como gadget para o PC não pode atuar simultaneamente como host USB para o ESP32. Para ESP por USB, planejar acesso de desenvolvimento por Wi-Fi; UART por GPIO é outra opção a estudar se a plataforma permitir. [Documentação oficial de gadget mode](https://www.raspberrypi.com/news/usb-gadget-mode-in-raspberry-pi-os-ssh-over-usb/).
3. **Ambiente e dados confiáveis:** corrigir cores, imports opcionais e métricas; validar câmera e inferência isoladas no Pi, sem motores.
4. **Benchmark embarcado:** começar com uma configuração leve e um conjunto fixo de imagens/vídeos; registrar carga do modelo, memória, latência mediana/p95/p99, frequência efetiva, temperatura e condições do ensaio. Se a configuração couber no hardware, ampliar a comparação.
5. **Integração da plataforma:** obter o firmware real do Juca e o contrato de comandos. Testar serial/ACK/STOP, ligar referências aos motores e calibrar limites com a plataforma elevada antes dos ensaios móveis.
6. **Seguimento básico:** validar uma pessoa, iluminação adequada, velocidades baixas e área livre, mantendo STOP ao perder o alvo como comportamento inicial.
7. **Extensões do texto:** implementar e avaliar calibração de distância e busca por rotação se fizerem parte do escopo acordado.

## Desenho dos experimentos

- Fixar cenas de comparação antes de escolher a configuração vencedora: distâncias, iluminação, deslocamento lateral, oclusões e cruzamento entre pessoas.
- Separar dados usados para ajustar ganhos/limiares daqueles usados na avaliação final.
- Definir como uma detecção corresponde à anotação manual (por exemplo, critério de sobreposição), e como contar falso positivo/falso negativo.
- Medir separadamente detecção, seleção de alvo e controle: detector pode encontrar uma pessoa enquanto o seletor troca a identidade seguida.
- Fixar a convenção de erro horizontal. O controle atual normaliza pela meia largura; o texto menciona normalização pela largura. Ambas são possíveis, mas os valores diferem por fator dois.
- Para cada configuração, repetir os ensaios e registrar taxa de conclusão, tempo mantendo o alvo, perdas, trocas, erro de centralização e erro de distância quando houver calibração.
- A meta documental de aproximadamente 1 ciclo/s é uma hipótese inicial; definir critérios quantitativos de sucesso e limites de movimento depois de medir o atraso real.
- Quatro imagens estáticas repetidas servem como ensaio inicial de execução, mas não demonstram seguimento, recuperação ou generalização da detecção.

## Escrita e pendências de definição

### Integração realizada no modelo

- `Doc/projeto_base/tex/cap1.tex` agora contém a introdução do Word, com quatro seções, onze objetivos e as cinco pendências preservadas.
- `tex/siglas.tex` centraliza o cadastro; `\gls{yolo}` e `\gls{ram}` controlam a apresentação das siglas e o cadastro também alimenta a lista institucional existente.
- `monografia.tex` inclui esse cadastro, reinicia o uso das siglas antes da introdução e usa `\captionsetup` para configurar as legendas sem recarregar `caption` com novas opções. Foi removida uma carga redundante de `acronym` em `conf-pacotes.sty`.
- `GUIA_LATEX.md` explica edição, siglas, referências cruzadas, citações e compilação.
- Os três arquivos substituídos foram preservados em `Doc/projeto_base/backup_integracao_2026-10-07`; o patch e as cópias propostas ficam em `integracao_latex_2026-10-07`.
- Na integração inicial, a verificação estrutural passou e os cinco arquivos aplicados eram idênticos às versões revisadas. Posteriormente, em 7 de outubro de 2026, foi instalado o MiKTeX e configurado o LaTeX Workshop no VS Code. O PDF foi compilado com sucesso (32 páginas), a introdução e a lista de siglas foram conferidas visualmente e os capítulos/seções receberam rótulos. Consulte `Doc/projeto_base/GUIA_LATEX.md` para os ajustes de compatibilidade e avisos de conteúdo ainda pendentes.
- O código do robô e as configurações de rede não foram alterados nesta revisão. Os problemas de implementação acima permanecem pendentes.

A introdução em Word fornece um problema de pesquisa coerente e não pressupõe que a plataforma necessariamente terá desempenho suficiente. Preservar essa formulação experimental. O modelo institucional contém material de outro trabalho (capa, capítulos e PDFs pré-textuais); revisar tudo antes de qualquer entrega.

Ainda definir: prazo e tipo da próxima entrega; nome completo e título da capa; acesso ao carrinho e ao firmware real; modelo da câmera; usuário SSH; política inicial de seleção do alvo; prioridade da busca por rotação e da calibração de distância; condições e critérios quantitativos dos ensaios; referências bibliográficas que permanecem marcadas no texto.
