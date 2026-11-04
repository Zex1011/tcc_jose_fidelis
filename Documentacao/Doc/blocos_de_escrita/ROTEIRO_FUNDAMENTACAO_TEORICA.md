# Roteiro para discutir a fundamentação teórica

**Data:** 9 de outubro de 2026.  
**Situação:** proposta de organização para discussão; ainda não é a redação do capítulo.  
**Trabalho:** Sistema de seguimento de pessoas com visão computacional embarcada no Raspberry Pi Zero 2 W.

**Recorte atualizado após discussão:** a fundamentação será concentrada nos tópicos **1 a 4**. Seleção e acompanhamento, robótica móvel e avaliação serão tratados na metodologia e no desenvolvimento. As referências a outros trabalhos serão distribuídas nos assuntos pertinentes, sem uma seção autônoma de trabalhos relacionados nesta etapa. As propostas ampliadas abaixo ficam como registro da discussão inicial. A primeira redação está em [FUNDAMENTACAO_TEORICA_RASCUNHO.md](FUNDAMENTACAO_TEORICA_RASCUNHO.md).

## Direção proposta

Preparar o leitor de Engenharia para entender como uma imagem pode gerar comandos de movimento e quais limitações aparecem ao executar esse processo em um computador embarcado com poucos recursos.

A sequência de raciocínio proposta é:

**Imagem digital → extração de características → detecção de pessoas → execução embarcada → manutenção do alvo → controle do robô → avaliação do sistema.**

O capítulo deve oferecer profundidade suficiente para justificar as escolhas e interpretar os resultados. Cada assunto precisa ajudar a entender uma parte do projeto. O detalhamento de instalação, nomes de arquivos, valores de configuração e dificuldades com drivers pertence à metodologia, à implementação ou aos apêndices.

## Tópicos candidatos e nível de aprofundamento

### 1. Visão computacional e representação de imagens

**Pergunta orientadora:** o que o computador recebe da câmera e que informação queremos extrair?

Conteúdo a abordar:

- Imagem como matriz de pixels, canais de cor e resolução.
- Quadros sucessivos e diferença entre resolução espacial e frequência de aquisição.
- Distinção entre classificação de imagens, detecção de objetos e acompanhamento ao longo do tempo.
- Diferença entre detectar a classe “pessoa” e reconhecer a identidade de alguém.
- Efeitos de iluminação, movimento, enquadramento, distância e oclusão sobre a imagem disponível.
- Pré-processamento: redimensionamento, preservação da proporção quando aplicável e adequação dos valores/canais à entrada do modelo.

**Profundidade:** introdução curta, voltada ao fluxo usado no projeto. Uma imagem ilustrada pode substituir longas explicações sobre pixels. Detalhes do sensor OV5647 e da montagem entram principalmente na descrição dos materiais.

### 2. Aprendizado de máquina e redes neurais convolucionais

**Pergunta orientadora:** como uma rede aprende padrões e usa esses padrões em uma imagem nova?

Conteúdo a abordar:

- Contextualização breve: inteligência artificial, aprendizado de máquina e aprendizado profundo.
- Aprendizado supervisionado, exemplos anotados e modelo pré-treinado.
- Neurônios, pesos, camadas e funções de ativação, em nível introdutório.
- Separação clara entre treinamento e inferência: o treinamento ajusta parâmetros; a inferência utiliza os parâmetros aprendidos.
- Convolução, filtros, mapas de características e compartilhamento de pesos.
- Noção de campo receptivo, stride e redução das dimensões; pooling apenas na medida necessária à explicação.
- Combinação de características ao longo das camadas, sem atribuir significado fixo a cada filtro.
- Generalização e possíveis diferenças entre imagens de treinamento e o ambiente do robô.

**Profundidade:** uma figura de um filtro percorrendo uma pequena matriz e um esquema de camadas. Se útil, uma expressão simples para a operação. Backpropagation pode ser explicado como o mecanismo de ajuste dos pesos, sem derivar os gradientes. Não há necessidade de apresentar todo o treinamento de uma rede que o trabalho não pretende treinar.

**Fonte inicial consultada:** [notas de redes convolucionais do curso CS231n, Stanford](https://cs231n.github.io/convolutional-networks/). Para a redação final, complementar com livro ou publicação acadêmica e selecionar as passagens efetivamente utilizadas.

### 3. Detecção de objetos, caixas delimitadoras e YOLO

**Pergunta orientadora:** como a rede informa que há uma pessoa e onde ela está?

Conteúdo a abordar:

- Caixa delimitadora (*bounding box*): coordenadas dos limites, centro, largura e altura.
- Classe prevista, pontuação de confiança e limiar de aceitação. A pontuação não deve ser apresentada como garantia de acerto.
- Visão geral de detectores de um estágio; contraste breve com detectores em etapas, somente para situar a proposta.
- Ideia original de YOLO: predição de caixas e classes em uma avaliação da rede.
- Organização conceitual de extração, combinação de características e produção das detecções, ajustada à versão realmente adotada.
- Variantes de tamanho e compromisso entre qualidade das detecções, processamento e memória.
- Pré-processamento, inferência, interpretação das saídas e filtragem da classe pessoa.
- Sobreposição entre caixas e IoU; supressão de detecções duplicadas quando aplicável ao modelo/modo utilizado.

**Profundidade:** uma figura com pessoa, caixa, centro e dimensões, mais um diagrama de entrada e saída do detector. Explicar os conceitos necessários para compreender o algoritmo, sem inventariar cada camada ou todas as gerações de YOLO.

**Cuidado com as versões:** o artigo original serve de base histórica e conceitual; não descreve automaticamente a arquitetura usada no projeto. A documentação atual do YOLO26 apresenta caminhos com e sem NMS. A redação deverá acompanhar a versão do pacote e a exportação efetivamente avaliadas, sem afirmar que todo YOLO usa a mesma grade, âncoras ou pós-processamento. Fontes: [artigo original de YOLO](https://arxiv.org/abs/1506.02640) e [documentação oficial de YOLO26](https://docs.ultralytics.com/models/yolo26/).

### 4. Inferência em sistemas embarcados

**Pergunta orientadora:** o que acontece no hardware quando executamos o modelo e por que isso pode ser lento ou consumir muita memória?

Conteúdo a abordar:

- Computação embarcada e processamento local dos dados da câmera.
- Papel de processador, memória e armazenamento na execução.
- Modelo como operações numéricas e parâmetros: carregar pesos, preparar tensores, calcular camadas, manter resultados intermediários e interpretar a saída.
- Distinção entre tamanho do arquivo do modelo e memória total durante a execução.
- Influência da resolução de entrada, do tamanho da rede e das bibliotecas sobre o custo computacional.
- Diferença entre modelo treinado, formato exportado e biblioteca de inferência.
- Papel de um runtime como NCNN; otimizações para CPU e suporte ao hardware concreto.
- Noção de precisão numérica e quantização, somente com o aprofundamento que os experimentos justificarem.
- Relação entre latência, frequência de atualização, memória e qualidade das detecções.

**Profundidade:** este é um dos pontos centrais do TCC. O leitor deve entender o caminho “pesos e imagem na memória → operações no processador → detecções”, sem precisar estudar compiladores ou arquitetura de processadores em detalhe.

**Ligação com o projeto:** a divisão entre Raspberry para percepção/decisão e ESP32 para execução dos comandos pode ser apresentada conceitualmente. Especificações, versões e montagem entram na metodologia. Não presumir que recursos de GPU ou quantização de uma biblioteca estejam disponíveis e ativos no Pi utilizado.

**Fontes iniciais consultadas:** [projeto oficial NCNN](https://github.com/Tencent/ncnn) e [especificações oficiais do Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/). Os recursos anunciados pelo runtime não substituem a medição do conjunto de software no dispositivo.

### 5. Seleção e acompanhamento de uma pessoa

**Pergunta orientadora:** como relacionar uma pessoa detectada agora à pessoa acompanhada no quadro anterior?

Conteúdo a abordar:

- Separação entre detectar, selecionar o alvo e associar detecções no tempo.
- Associação espacial por proximidade dos centros e/ou sobreposição, conforme a estratégia escolhida.
- Situações com várias pessoas, oclusões, detecções ausentes e trocas de alvo.
- Limitações de uma estratégia sem reconhecimento de identidade.
- Noção de perda e recuperação do alvo; motivação para representar comportamentos por estados.
- Tamanho aparente da pessoa como informação indireta de proximidade.
- Modelo geométrico simplificado de projeção, somente se necessário à calibração de distância prevista na introdução.
- Limitações relacionadas à altura, postura, enquadramento e visibilidade parcial da pessoa.

**Profundidade:** explicar a associação simples que sustenta o trabalho. Filtros de Kalman, DeepSORT, reidentificação e SLAM só merecem aprofundamento se forem usados ou comparados. A caixa fornece observações visuais; não deve ser apresentada como medidor direto e universal de distância.

**Atualização em 26/10/2026:** a busca por rotação foi confirmada no comportamento previsto. Se o tempo de busca expirar ou não houver direção confiável, o sistema deverá solicitar STOP, continuar observando e permitir nova seleção. A busca ainda precisa ser implementada; seus critérios e limites serão definidos na metodologia, conforme o [guia dos diagramas](../../diagramas/software_rpi/README.md). O detalhamento da calibração de distância permanece independente dessa decisão; o controle atual usa altura relativa da caixa.

### 6. Robótica móvel e controle baseado em informações visuais

**Pergunta orientadora:** como transformar a posição da pessoa na imagem em uma ação da plataforma?

Conteúdo a abordar:

- Princípio de locomoção de uma plataforma com tração diferencial.
- Significado de movimento linear e angular e relação qualitativa com as rodas.
- Realimentação visual: capturar, observar erro, calcular ação e observar novamente.
- Erro horizontal do alvo e referência de tamanho aparente ou distância aproximada.
- Controle proporcional, saturação e zona morta, na medida em que sustentem o controlador adotado.
- Efeito de atrasos e baixa frequência de atualização sobre o acompanhamento.
- Diferença entre a malha de acompanhamento por visão e eventual controle de velocidade das rodas.
- Comunicação entre computador e microcontrolador: validade dos comandos, confirmação, timeout, parada e watchdog, em nível conceitual.

**Profundidade:** um esquema de realimentação e as relações simples efetivamente usadas. A introdução informa que os circuitos de acionamento dos motores não serão desenvolvidos neste trabalho; eletrônica de potência, projeto detalhado de drivers e demonstrações extensas de estabilidade não precisam dominar o capítulo.

**Cuidado conceitual:** ausência de encoders não elimina a realimentação visual. É preciso distinguir o nível de controle considerado. As referências abstratas do MVP também não devem ser tratadas como velocidades físicas medidas sem a calibração correspondente.

### 7. Conceitos de avaliação do sistema

**Pergunta orientadora:** o que significa o sistema funcionar bem e como distinguir seus diferentes tipos de erro?

Conteúdo a abordar:

- Acertos, falsas detecções e pessoas não detectadas; precisão e revocação, com critérios definidos.
- IoU como apoio à correspondência entre caixas previstas e anotações.
- AP/mAP em nível introdutório se forem necessárias para interpretar os modelos ou usadas na avaliação.
- Tempo de inferência, latência aquisição–comando e frequência efetiva do sistema como medidas diferentes.
- Erro de centralização, continuidade, perda e troca de alvo.
- Compromisso entre qualidade visual e rapidez de reação.

**Profundidade:** definir o significado das métricas. Quantidade de ensaios, cenas, limiares, anotações e procedimento de medição ficam na metodologia; valores medidos e gráficos ficam nos resultados. Esta seção pode ser curta ou distribuída pelas anteriores para evitar repetição.

### 8. Trabalhos relacionados

**Pergunta orientadora:** como outros trabalhos resolveram problemas próximos e em que contexto se situa esta avaliação?

Proposta de recorte:

- Um pequeno conjunto de trabalhos sobre seguimento visual de pessoas em robôs móveis.
- Estudos de detecção em hardware com recursos limitados.
- A plataforma Juca, se a publicação existente na bibliografia for pertinente à plataforma efetivamente utilizada.
- Comparação por hardware, sensor, detector, estratégia de acompanhamento, controle, métricas e limitações.

**Profundidade:** começar com três a cinco trabalhos próximos e ampliar apenas se necessário. Ainda não foi realizada nesta etapa uma revisão bibliográfica desses trabalhos; não há conclusões comparativas prontas. Essa discussão pode encerrar a fundamentação ou formar uma seção própria, conforme orientação acadêmica.

## Limite de profundidade sugerido

Como estimativa de planejamento, algo em torno de **12 a 18 páginas**, incluindo figuras, poderia comportar o conteúdo. Isso não é uma exigência institucional nem uma meta a preencher: a extensão deve resultar do recorte acordado e das fontes disponíveis.

Priorizar CNN, detecção/YOLO, execução embarcada e a ligação entre visão e controle. A apresentação geral de IA e de robótica pode ser breve. Evitar uma história extensa da IA ou um catálogo de tecnologias sem papel no projeto.

Matemática candidata: uma operação simples de convolução; coordenadas/centro da caixa; IoU; erro visual normalizado e lei proporcional; relações de tração diferencial ou projeção de câmera apenas quando usadas para justificar o método. Apresentar variáveis, unidades e hipóteses sempre que uma equação entrar.

Figuras candidatas: filtro sobre uma imagem pequena; entrada/saída de uma CNN; pessoa com bounding box; pesos e tensores durante a inferência; associação entre dois quadros; malha visual de controle. Ainda não foram produzidas nesta etapa.

## O que pertence a cada parte do TCC

| Fundamentação | Metodologia/implementação | Resultados |
| --- | --- | --- |
| O que são convolução, detecção e inferência | Modelo, versão, exportação e resolução escolhidos | Qualidade e custo das configurações avaliadas |
| O que é um runtime e por que há restrições de recursos | Raspberry, câmera, sistema, bibliotecas e integração | Memória, tempos e frequência medidos |
| Princípios de associação e controle visual | Algoritmo, estados, ganhos e limites adotados | Centralização, perdas, trocas e comportamento do robô |
| Definição e interpretação das métricas | Protocolo experimental e obtenção das referências | Tabelas, gráficos e discussão das limitações |

O capítulo 2 atual ainda contém material herdado sobre educação, BLE e Flutter. Esses assuntos devem ser reavaliados pelo vínculo com este projeto; a presença no modelo não justifica sua permanência. O roteiro não altera esse capítulo.

## Pontos para alinharmos antes de redigir

1. Manter o equilíbrio proposto, com maior espaço para visão/IA embarcada e explicação suficiente de robótica e controle?
2. A busca por rotação está confirmada; falta definir seus parâmetros na metodologia e detalhar a calibração aproximada de distância.
3. Apresentar métricas e trabalhos relacionados no fim deste capítulo ou em seções separadas, conforme preferência do orientador?

Pode-se começar a futura redação pelos conceitos estáveis: imagens, CNN, bounding boxes e inferência. O detalhamento da variante YOLO, dos estados e da calibração deve acompanhar as decisões e os ensaios do projeto.
