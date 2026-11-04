# Fundamentação teórica sobre visão computacional e inferência embarcada

**Versão para discussão — 9 de outubro de 2026**  
**TCC de José Henrique Schmitt Fidelis**

> Integrado ao [capítulo 2 em LaTeX](../projeto_base/tex/cap2.tex) em 26/10/2026, com citações em [referencias.bib](../projeto_base/referencias.bib). O corpo deste rascunho e suas notas de revisão foram preservados; a versão diagramada está no [PDF do TCC](../projeto_base/monografia.pdf).

Este texto apresenta os fundamentos necessários para compreender a detecção de pessoas por redes neurais executadas em um sistema embarcado. A exposição parte da representação digital das imagens, introduz o funcionamento das redes convolucionais, apresenta a detecção de objetos com YOLO e discute a execução de modelos em hardware com recursos limitados. As escolhas de implementação, o acompanhamento do alvo, o controle da plataforma e os procedimentos experimentais serão tratados posteriormente, na metodologia e no desenvolvimento.

As citações possuem links para as fontes e correspondem às referências reunidas ao final. Os exemplos numéricos são didáticos e não representam resultados medidos no projeto. A numeração das seções é provisória, para revisão antes da integração ao documento institucional.

## 1 Imagens digitais e visão computacional

### 1.1 Representação de uma imagem

Para o processamento computacional, uma imagem digital pode ser representada por um arranjo de valores numéricos. Sua organização espacial é dada por linhas e colunas, cujas posições correspondem aos pixels. Em uma representação colorida RGB, cada posição contém três componentes, associadas ao vermelho, ao verde e ao azul. Quando cada componente utiliza oito bits sem sinal, seus valores variam de 0 a 255. Essa é uma representação comum, embora existam imagens com outros números de canais e outras profundidades numéricas ([Stanford University, s.d.a][stanford-imagens]).

Considere, como exemplo, uma imagem RGB com largura de 640 pixels e altura de 480 pixels. Ela contém 307.200 posições espaciais e 921.600 valores de componentes de cor. Se cada valor ocupar um byte, o arranjo exige 921.600 bytes, aproximadamente 0,88 MiB, antes de considerar metadados, alinhamento ou cópias. Aqui, um mebibyte, ou MiB, corresponde a 2²⁰ bytes. Esse cálculo descreve o arranjo descomprimido; não corresponde necessariamente ao tamanho de um arquivo JPEG salvo em disco.

A organização dos dados também faz parte da representação. Um tensor é, neste contexto, um arranjo numérico com uma ou mais dimensões. Uma imagem pode ser organizada como altura × largura × canais, enquanto bibliotecas de redes neurais podem utilizar lote × canais × altura × largura. A ordem dos canais também precisa ser conhecida: RGB e BGR contêm as mesmas componentes, mas em posições diferentes. A documentação de inferência da Ultralytics, por exemplo, especifica convenções distintas para imagens NumPy e tensores de entrada ([Ultralytics, s.d.a][ultralytics-predict]).

### 1.2 Da imagem numérica à informação sobre objetos

As tarefas de visão computacional se distinguem pela informação que produzem. Na classificação, o resultado indica uma categoria ou a presença de determinadas categorias na imagem. Na detecção, também é necessário localizar os objetos, normalmente por caixas delimitadoras. Na segmentação, a descrição espacial é mais detalhada, atribuindo rótulos a regiões ou pixels. Essas diferenças aparecem, por exemplo, na definição das tarefas do desafio PASCAL VOC ([PASCAL VOC, 2010][pascal]).

Para situar essas tarefas, imagine uma imagem com duas pessoas. Uma classificação pode indicar a presença da categoria “pessoa”. Um detector pode retornar duas caixas, cada uma associada à categoria prevista. Uma segmentação pode representar as regiões ocupadas pelos corpos. O resultado de detecção, isoladamente, fornece categoria e localização. Neste texto, “detecção de pessoas” designa essa tarefa; a correspondência entre instantes não integra a saída aqui definida ([PASCAL VOC, 2010][pascal]).

A relação entre os valores dos pixels e a categoria de um objeto não é fixa. Iluminação, escala, orientação, postura, fundo e oclusões podem alterar a aparência observada. Pessoas diferentes também apresentam variações de roupa e características visuais. Portanto, o sistema precisa lidar com variações dentro da mesma categoria, além de distinguir categorias diferentes ([Stanford University, s.d.a][stanford-imagens]).

### 1.3 Preparação das imagens para a rede

O pré-processamento adapta a imagem ao formato esperado pelo modelo. Uma operação frequente é o redimensionamento, que calcula uma nova grade de pixels a partir da imagem original. Para isso, utilizam-se métodos de interpolação, como vizinho mais próximo, bilinear ou métodos baseados em áreas. Redimensionar para uma quantidade menor de pixels reduz a representação espacial disponível; ampliar uma imagem por interpolação não equivale a adquirir novos detalhes com a câmera ([OpenCV, s.d.][opencv-transform]).

As proporções também precisam ser consideradas. Em um exemplo geométrico, transformar diretamente 640 × 480 em 320 × 320 aplica fatores diferentes aos dois eixos. Uma alternativa é redimensionar proporcionalmente e completar as bordas, procedimento conhecido como *letterbox*. O preenchimento e as dimensões efetivas dependem da implementação e da configuração do detector. Ao interpretar as caixas previstas, deve-se considerar a transformação realizada sobre a imagem ([Ultralytics, s.d.a][ultralytics-predict]).

Outra operação é a adequação da escala numérica dos valores. Dependendo da rede, isso pode envolver divisão por uma constante, subtração de médias ou divisão por desvios-padrão. A transformação deve seguir a convenção prevista pelo modelo: normalizar valores e redimensionar a imagem são operações distintas. A primeira altera a representação numérica; a segunda modifica as dimensões espaciais. A preparação utilizada na inferência deve ser compatível com aquela associada ao treinamento ([Stanford University, s.d.b][stanford-preprocess]).

## 2 Redes neurais convolucionais

### 2.1 Aprendizado a partir de exemplos

O aprendizado de máquina permite ajustar modelos a partir de dados. No aprendizado supervisionado, os exemplos são acompanhados por respostas de referência, como classes de imagens ou anotações de objetos. Uma rede neural aplica transformações parametrizadas à entrada e produz uma saída. Durante o treinamento, seus parâmetros são ajustados para reduzir uma função de perda, que expressa a discrepância entre as previsões e as referências segundo o problema considerado ([LeCun; Bengio; Hinton, 2015][lecun-2015]).

O treinamento inclui a propagação dos dados pela rede, o cálculo da perda e a obtenção de gradientes por retropropagação. Um algoritmo de otimização utiliza esses gradientes para atualizar os parâmetros. Na inferência, a rede utiliza os parâmetros já aprendidos para calcular respostas para novas entradas. Assim, empregar um modelo pré-treinado na câmera não significa que ele esteja aprendendo continuamente com as imagens recebidas ([LeCun; Bengio; Hinton, 2015][lecun-2015]).

### 2.2 Pesos e funções de ativação

Uma unidade básica de uma rede pode ser descrita por uma soma ponderada seguida de uma função de ativação:

```text
z = w1·x1 + w2·x2 + ... + wn·xn + b
y = f(z)
```

Nessa expressão, `xi` são valores de entrada, `wi` são pesos, `b` é um termo de deslocamento, chamado viés, e `f` é a função de ativação. Os pesos determinam a contribuição das entradas. A composição de unidades e camadas permite produzir transformações mais elaboradas. Funções não lineares são necessárias para que uma sequência de camadas não se reduza apenas a uma transformação afim equivalente. Um exemplo didático é ReLU, definida por `f(z) = max(0, z)` ([Stanford University, s.d.c][stanford-neuron]).

Por exemplo, uma unidade com entradas 0,2 e 0,8, pesos 0,5 e −0,25 e viés 0,1 produz `z = 0,5·0,2 − 0,25·0,8 + 0,1 = 0`. Alterar os pesos modifica a resposta à mesma entrada. O exemplo ilustra o papel dos parâmetros, sem representar um neurônio específico do modelo utilizado.

### 2.3 Convolução e mapas de características

As redes neurais convolucionais, do inglês *Convolutional Neural Networks* (CNNs), exploram a estrutura espacial dos dados. Em uma camada convolucional, cada saída depende de uma região local da entrada, chamada campo receptivo local. Um mesmo conjunto de pesos é aplicado a diferentes posições, produzindo um mapa de características. Esse compartilhamento permite procurar uma característica em vários locais sem aprender um conjunto independente de pesos para cada posição. O trabalho de LeCun et al. sobre reconhecimento de documentos apresenta esses princípios em uma aplicação clássica de redes convolucionais ([LeCun et al., 1998][lecun-1998]).

O conjunto de pesos aplicado à região local é chamado filtro ou *kernel*. A operação envolve multiplicar valores correspondentes da entrada e do filtro e somar os produtos. Nas implementações usuais de CNNs, essa operação geralmente corresponde à correlação cruzada, na qual não se inverte espacialmente o filtro. A expressão “convolução” permanece consagrada para a camada na literatura de aprendizado profundo ([Dumoulin; Visin, 2016][dumoulin]).

Um exemplo com um único canal ajuda a visualizar a operação:

```text
Região da entrada       Filtro
1  2                    1   0
3  4                    0  −1

Resultado nessa posição = 1·1 + 2·0 + 3·0 + 4·(−1) = −3
```

Ao deslocar esse filtro, calculam-se resultados para outras regiões. Em uma convolução convencional, sem agrupamento, o filtro considera todos os canais da entrada e acumula as contribuições correspondentes. Diferentes filtros produzem diferentes canais de saída. Seus valores são aprendidos no treinamento, permitindo extrair características úteis ao objetivo da rede ([Stanford University, s.d.d][stanford-cnn]).

O compartilhamento pode ser ilustrado por uma camada convolucional convencional, sem agrupamento, com 16 filtros de tamanho 3 × 3 sobre uma entrada de três canais. Considerando um viés por filtro, existem `16·(3·3·3 + 1) = 448` parâmetros. Esse número não depende diretamente de quantas posições da imagem serão percorridas. Entretanto, o número de operações aumenta quando há mais posições de saída. O exemplo separa duas grandezas: quantidade de parâmetros e quantidade de cálculos ([LeCun et al., 1998][lecun-1998]).

### 2.4 Dimensões e composição das camadas

O passo de deslocamento do filtro é denominado *stride*. Um passo maior pode produzir um mapa espacialmente menor. O *padding* acrescenta posições nas bordas, geralmente preenchidas com zeros, e influencia o tamanho da saída e o tratamento dos pixels próximos aos limites. Para uma dimensão de entrada `i`, filtro de tamanho `k`, preenchimento simétrico `p` e passo `s`, sem dilatação, a dimensão de saída é `piso((i + 2p − k)/s) + 1`. Por exemplo, entrada 5, filtro 3, preenchimento 0 e passo 1 resultam em saída 3 ([Dumoulin; Visin, 2016][dumoulin]).

As CNNs também podem empregar operações de redução, como *pooling*, que agregam valores de uma vizinhança por uma regra, por exemplo máximo ou média. Camadas de ativação introduzem não linearidades entre transformações. A combinação concreta desses elementos depende da arquitetura; a presença de convoluções não obriga toda CNN a ter a mesma sequência de camadas ou a utilizar pooling ([Stanford University, s.d.d][stanford-cnn]).

Ao encadear camadas que combinam posições espaciais, o campo receptivo em relação à imagem original pode aumentar. A rede pode, assim, combinar informações locais em representações mais abrangentes. Operações pontuais, como uma ativação aplicada separadamente a cada posição, não ampliam por si só essa região. O significado das representações depende dos parâmetros aprendidos, sem exigir que cada filtro corresponda a uma parte fixa do objeto ([Zhang et al., 2023, seção 7.2][d2l-conv]).

### 2.5 Generalização e modelos pré-treinados

A finalidade do treinamento é obter um modelo que produza respostas úteis também para exemplos não utilizados no ajuste. Essa capacidade é denominada generalização. Um modelo pode apresentar baixo erro nos dados de treinamento e ainda responder inadequadamente a novas imagens, fenômeno associado ao sobreajuste. Por isso, desempenho no conjunto de treinamento não constitui, por si só, garantia de funcionamento em outras condições ([Goodfellow; Bengio; Courville, 2016, seção 5.2][goodfellow]).

Modelos pré-treinados permitem aproveitar parâmetros obtidos em um treinamento anterior. É possível utilizá-los diretamente para inferência ou realizar um novo ajuste com dados específicos, procedimento denominado ajuste fino, ou *fine-tuning*. Essas alternativas são distintas: carregar pesos e processar imagens não executa automaticamente um novo treinamento. A adequação dos pesos ao problema depende da relação entre o domínio original e as imagens de interesse ([Zhang et al., 2023, seção 14.2][d2l-finetune]).

## 3 Detecção de objetos e família YOLO

### 3.1 Caixas delimitadoras

Um detector de objetos retorna previsões de localização e categoria. A localização pode ser representada por uma caixa delimitadora retangular alinhada aos eixos da imagem. Na convenção `xyxy`, a caixa é descrita pelos limites `(xmin, ymin, xmax, ymax)`. Na convenção `xywh` empregada pela Ultralytics, a representação utiliza centro, largura e altura. Também existem coordenadas normalizadas em relação às dimensões da imagem ([Ultralytics, s.d.b][ultralytics-detect]).

Adotando coordenadas contínuas no plano da imagem, as relações geométricas são:

```text
cx = (xmin + xmax)/2       cy = (ymin + ymax)/2
w  = xmax − xmin          h  = ymax − ymin
```

Por exemplo, a caixa `(100, 40, 220, 360)` tem centro `(160, 200)`, largura 120 e altura 320, nas unidades de coordenadas adotadas. Essas informações descrevem a extensão prevista do objeto na imagem. A caixa pode incluir partes do fundo, pois não representa seu contorno exato. A distinção entre localização por caixa e descrição precisa da forma é parte da definição da tarefa de detecção ([Ultralytics, s.d.b][ultralytics-detect]).

### 3.2 Classe e confiança da previsão

Além da caixa, o detector produz informações sobre a categoria prevista e uma pontuação de confiança. Essa pontuação é utilizada para ordenar previsões e aplicar limiares. Um limiar mais alto admite um subconjunto mais restrito de previsões, mas a decisão sobre quais detecções são úteis depende do problema. A interpretação do score como probabilidade de acerto exige considerar a calibração do detector: uma pontuação 0,8 não deve ser automaticamente apresentada como uma garantia de 80% de acertos em qualquer situação ([Küppers et al., 2020][kuppers]).

É útil distinguir a decisão da rede e a decisão de uso da aplicação. A rede produz previsões; a aplicação pode conservar somente algumas classes ou pontuações. No código da Ultralytics consultado, o filtro de classes atua sobre previsões já produzidas. Consequentemente, selecionar apenas a classe “pessoa” não transforma automaticamente uma rede multiclasse em uma rede menor, embora possa reduzir o trabalho posterior sobre as saídas. Essa conclusão decorre do fluxo da implementação consultada, não de uma medição de ganho de desempenho neste projeto ([Ultralytics, 2026][ultralytics-nms]).

### 3.3 Sobreposição e detecções redundantes

A interseção sobre união, ou IoU (*Intersection over Union*), expressa a sobreposição entre duas caixas:

```text
IoU(A, B) = área da interseção entre A e B / área da união entre A e B
```

Para caixas válidas e união de área positiva, o resultado varia de zero, quando não há área comum, a um, quando as caixas coincidem. Se duas caixas têm área 100 cada e interseção de área 50, sua união tem área 150 e a IoU é `50/150`, aproximadamente 0,33. É uma relação geométrica entre caixas, distinta da pontuação de confiança produzida pela rede ([Rezatofighi et al., 2019, seção 3][iou]).

Alguns detectores podem gerar várias caixas para um mesmo objeto. Na supressão de não máximos, ou NMS, previsões são ordenadas por pontuação; uma caixa selecionada é mantida e caixas suficientemente sobrepostas podem ser descartadas segundo um limiar. O tratamento pode ser realizado por classe. A finalidade é reduzir redundâncias, mas a necessidade dessa etapa depende da arquitetura e do caminho de inferência ([Ultralytics, 2026][ultralytics-nms]).

### 3.4 A proposta de YOLO

YOLO é a sigla de *You Only Look Once*. Na proposta original de Redmon et al., a detecção é formulada como uma predição conjunta de caixas e classes a partir da imagem completa em uma avaliação da rede. Essa formulação caracteriza uma abordagem de um estágio: não há um módulo separado de propostas de regiões que depois sejam classificadas individualmente. O termo não significa uma rede de uma única camada ou ausência de preparação e tratamento das saídas ([Redmon et al., 2016][yolo-original]).

A versão original organiza previsões por uma grade espacial e utiliza uma formulação específica para caixas, classes e confiança. Esses detalhes pertencem àquele modelo. A família evoluiu, e explicar uma versão posterior exige consultar sua arquitetura e implementação correspondentes. Assim, a ideia de detectar a partir de uma passagem pela rede pode ser apresentada como fundamento, enquanto números de células, quantidade de caixas por célula e fórmulas de score precisam ser associados à versão que os utiliza ([Redmon et al., 2016][yolo-original]).

### 3.5 Componentes e variantes atuais

Uma organização conceitual útil distingue extração de características (*backbone*), combinação de características (*neck*) e produção das previsões (*head*). No YOLO26, os autores descrevem componentes de extração e fusão de características e cabeças destinadas às tarefas de saída. Para a detecção, essas estruturas devem produzir informações de localização e categoria. Diferentes escalas do modelo, identificadas como `n`, `s`, `m`, `l` e `x`, correspondem a configurações distintas da família. O artigo que descreve YOLO26 é, na versão consultada, um preprint ([Jocher et al., 2026][yolo26-paper]).

YOLO26 oferece caminhos de detecção com associação de treinamento *one-to-many* e *one-to-one*: associam-se múltiplas previsões a um objeto, no primeiro caso, ou uma previsão a cada objeto, no segundo. O primeiro caminho utiliza NMS; o segundo permite inferência sem essa supressão. Portanto, NMS não é uma etapa obrigatória de toda execução da família. O caminho efetivo depende da versão e da configuração, inclusive na exportação ([Jocher et al., 2026][yolo26-paper]; [Ultralytics, s.d.c][ultralytics-yolo26]).

O artigo original e a documentação da versão adotada cumprem, portanto, papéis complementares: o primeiro fundamenta a proposta de detecção, e os demais descrevem a concretização atual. As características específicas do modelo selecionado, de seu arquivo exportado e de seus parâmetros de execução serão registradas na metodologia, permitindo relacionar a fundamentação ao experimento efetivamente realizado.

## 4 Inferência em sistemas embarcados

### 4.1 Do modelo treinado às operações no processador

A inferência de uma rede envolve executar operações numéricas sobre os dados de entrada e os parâmetros aprendidos. Nas convoluções, são realizadas muitas multiplicações e acumulações; outras camadas aplicam ativações, reorganizam dados ou combinam resultados. A execução também exige movimentar pesos e resultados intermediários entre níveis de memória. Portanto, o custo depende tanto do cálculo quanto do acesso aos dados, e não apenas da quantidade de camadas descritas no modelo ([Sze et al., 2017, seções III e V][sze]).

Essa execução pode ser representada como um grafo: os nós correspondem a operações, e as conexões indicam os dados consumidos e produzidos. O ONNX, por exemplo, define entradas, saídas, operadores, atributos e inicializadores, que podem armazenar pesos. Um runtime executa esse grafo no ambiente de destino ([ONNX, s.d.][onnx]).

Uma biblioteca de inferência permite integrar essas operações à aplicação embarcada. O NCNN é um exemplo, com implementação em C++ e interfaces para executar redes localmente em diferentes plataformas ([Tencent, s.d.][ncnn]).

Na CPU, o cálculo é realizado por instruções de máquina. A vetorização permite aplicar uma instrução a vários elementos, abordagem denominada SIMD (*Single Instruction, Multiple Data*). A tecnologia Arm Neon oferece esse tipo de operação para dados inteiros e de ponto flutuante. Como exemplo conceitual, vários produtos entre entradas e pesos podem ser organizados em vetores, em vez de tratar cada par isoladamente. Essa forma de paralelismo ocorre no processamento das instruções e é distinta de simplesmente distribuir tarefas entre vários núcleos ([Arm, s.d.][arm-neon]).

### 4.2 Armazenamento e memória durante a execução

O arquivo de um modelo e a memória usada ao executá-lo representam grandezas diferentes. Além dos pesos, a execução mantém entradas, saídas e resultados intermediários, também chamados ativações, e pode utilizar áreas temporárias de trabalho. A organização e a reutilização dessas áreas dependem do runtime. Um grafo pode, por exemplo, permitir a reutilização de um buffer quando seu conteúdo anterior não é mais necessário ([Sze et al., 2017, seções V e VIII][sze]; [ONNX, s.d.][onnx]).

Um cálculo simplificado ajuda a dimensionar os pesos. Se houver `N` parâmetros armazenados com `b` bits por parâmetro, seu armazenamento bruto será `N·b/8` bytes. Em um exemplo hipotético de dois milhões de parâmetros, 32 bits por valor correspondem a oito milhões de bytes, aproximadamente 7,63 MiB. Com 16 bits, seriam aproximadamente 3,81 MiB. O cálculo não inclui estruturas do arquivo, metadados, ativação, cópias ou outras partes do processo.

O mesmo raciocínio se aplica a um tensor. Uma entrada de 320 × 320 com três canais tem 307.200 elementos. A oito bits por elemento, são aproximadamente 0,29 MiB; a 32 bits, aproximadamente 1,17 MiB. Os exemplos mostram por que a profundidade numérica importa mesmo quando as dimensões espaciais não mudam. A representação efetiva deve ser aquela exigida pela rede e pela implementação, e não uma redução arbitrária dos dados.

### 4.3 Resolução e custo da rede

Reduzir a resolução da entrada e a largura de uma rede são estratégias distintas para diminuir seu custo. Em MobileNets, Howard et al. apresentam multiplicadores de resolução e de largura para explorar compromissos entre custo computacional e qualidade das respostas. A ideia geral é que mapas menores e menos canais reduzem a quantidade de operações e dados envolvidos, embora alterem a capacidade de representação disponível ([Howard et al., 2017][mobilenets]).

Se largura e altura de um mapa forem reduzidas pela metade, o número de posições espaciais cai para um quarto. Mantidos filtro e canais de uma convolução convencional, essa redução diminui proporcionalmente o número de posições em que os produtos e somas são calculados. Ela não implica que a aplicação inteira execute exatamente quatro vezes mais rápido: preparação de imagens, transferências, demais operações e custos fixos também participam da execução. Esse exemplo expressa uma relação de contagem, não um benchmark do Raspberry ([Howard et al., 2017][mobilenets]).

### 4.4 Precisão numérica e quantização

A quantização representa valores utilizando um conjunto mais limitado de níveis numéricos. Uma aproximação comum relaciona um inteiro `q` a um valor real por uma escala `s` e um ponto zero `z`, na forma `r ≈ s·(q − z)`. O trabalho de Jacob et al. apresenta uma abordagem de treinamento e inferência que permite realizar operações com aritmética inteira, buscando reduzir custos em dispositivos de aplicação prática ([Jacob et al., 2018][jacob]).

A redução de precisão pode diminuir armazenamento e custo de cálculo, mas introduz aproximações. O resultado depende do modelo, do método de quantização e do suporte do hardware e do software. Usar armazenamento de 16 bits, por exemplo, não significa necessariamente que todas as operações serão executadas nessa precisão ou que qualquer processador obterá aceleração. Assim, uma possibilidade de otimização precisa ser distinguida de uma característica realmente ativada e verificada na aplicação ([Jacob et al., 2018][jacob]; [Tencent, s.d.][ncnn]).

### 4.5 Exportação e bibliotecas de inferência

Exportar um modelo consiste em representá-lo para execução no ambiente de destino, sem necessariamente treiná-lo novamente. A compatibilidade envolve tipos de dados, dimensões e operações. No ONNX, os operadores possuem definições e versões que precisam ser suportadas pelo runtime ([ONNX, s.d.][onnx]).

O NCNN disponibiliza execução em CPU, otimizações para arquiteturas ARM e caminhos de aceleração para plataformas compatíveis. Seu ecossistema também oferece ferramentas de conversão de modelos. A existência desses recursos na biblioteca não garante que todos estejam disponíveis em uma placa particular. A aplicação que envolve o runtime pode adicionar dependências e consumo de recursos próprios. Por isso, distinguir rede, formato exportado, runtime e aplicação completa é necessário para compreender o que será instalado e executado ([Tencent, s.d.][ncnn]).

### 4.6 Contexto do Raspberry Pi Zero 2 W

O Raspberry Pi Zero 2 W é um computador de placa única que utiliza processador Arm Cortex-A53 de quatro núcleos, arquitetura de 64 bits e frequência nominal de 1 GHz, acompanhado de 512 MB de memória LPDDR2. A placa possui interface CSI-2 para câmera e armazenamento por cartão microSD. Essas características são apresentadas na documentação técnica do fabricante ([Raspberry Pi Ltd, 2024, p. 2–3][raspberry]).

O tempo e a memória necessários dependem da combinação de rede, representação dos dados, runtime e plataforma. Resultados de outro processador não estabelecem o desempenho deste dispositivo; a análise precisa considerar a execução concreta do conjunto ([Sze et al., 2017, seções V e VIII][sze]).

A fundamentação apresentada permite compreender essa combinação sem antecipar os resultados do projeto. A metodologia poderá especificar o modelo e a configuração adotados, e o desenvolvimento mostrará como aquisição, pré-processamento e inferência foram integrados no Raspberry.

## Referências

As letras após “s.d.” distinguem documentos de um mesmo autor institucional sem data de publicação claramente indicada. As páginas de documentação são fontes técnicas dos respectivos projetos; os artigos e livros fundamentam os conceitos gerais. As fontes eletrônicas foram consultadas em **9 de outubro de 2026**. A formatação final será ajustada ao padrão bibliográfico do modelo institucional.

- **ARM.** *Neon*. Documentação técnica, s.d. [Apresentação da tecnologia][arm-neon].
- **DUMOULIN, Vincent; VISIN, Francesco.** *A guide to convolution arithmetic for deep learning*. 2016. arXiv:1603.07285. Versão 2 revisada em 2018. Seções 1.1 e 2.4. [DOI e registro](https://doi.org/10.48550/arXiv.1603.07285); [texto da versão consultada][dumoulin].
- **GOODFELLOW, Ian; BENGIO, Yoshua; COURVILLE, Aaron.** *Deep Learning*. Cambridge, MA: MIT Press, 2016. Seção 5.2, p. 108–110. [Livro dos autores](https://www.deeplearningbook.org/); [capítulo consultado][goodfellow].
- **HOWARD, Andrew G. et al.** *MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications*. 2017. arXiv:1704.04861. Seções 3.2 e 3.3. [DOI](https://doi.org/10.48550/arXiv.1704.04861); [texto][mobilenets].
- **JACOB, Benoit et al.** *Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference*. In: IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2018. p. 2704–2713. [Publicação][jacob]; [preprint disponibilizado em 2017](https://arxiv.org/pdf/1712.05877).
- **JOCHER, Glenn; QIU, Jing; LIU, Mengyu; LYU, Shuai; AKYON, Fatih Cagatay; KALFAOGLU, Muhammet Esat.** *Ultralytics YOLO26: Unified Real-Time End-to-End Vision Models*. 2026. Preprint, arXiv:2606.03748v1, submetido em 2 jun. 2026. [DOI e registro](https://doi.org/10.48550/arXiv.2606.03748); [versão consultada][yolo26-paper].
- **KÜPPERS, Fabian; KRONENBERGER, Jan; SHANTIA, Amirhossein; HASELHOFF, Anselm.** *Multivariate Confidence Calibration for Object Detection*. In: IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops, 2020. [Texto dos autores][kuppers].
- **LECUN, Yann; BOTTOU, Léon; BENGIO, Yoshua; HAFFNER, Patrick.** Gradient-based learning applied to document recognition. *Proceedings of the IEEE*, v. 86, n. 11, p. 2278–2324, 1998. Seção II-A. [DOI](https://doi.org/10.1109/5.726791); [publicação na página de um dos autores][lecun-1998].
- **LECUN, Yann; BENGIO, Yoshua; HINTON, Geoffrey.** Deep learning. *Nature*, v. 521, p. 436–444, 2015. [DOI e artigo][lecun-2015]; [cópia para leitura em repositório acadêmico](https://www.cs.cornell.edu/~ginsparg/3950/fa19/LeCun_Bengio_Hinton_Nature2015.pdf).
- **ONNX.** *ONNX Concepts*. Documentação técnica, s.d. Seções sobre grafos, inicializadores, tipos e versões de operadores. [Documento][onnx].
- **OPENCV.** *Geometric Image Transformations*. Documentação técnica, s.d. Seções sobre interpolação e redimensionamento. [Documento][opencv-transform].
- **PASCAL VOC.** *The PASCAL Visual Object Classes Challenge 2010*. 2010. Definições das tarefas de classificação, detecção e segmentação. [Página oficial][pascal].
- **RASPBERRY PI LTD.** *Raspberry Pi Zero 2 W*. Product brief. Abr. 2024. p. 2–3. [Documento do fabricante][raspberry].
- **REDMON, Joseph; DIVVALA, Santosh; GIRSHICK, Ross; FARHADI, Ali.** You Only Look Once: Unified, Real-Time Object Detection. In: IEEE Conference on Computer Vision and Pattern Recognition, 2016. p. 779–788. DOI: 10.1109/CVPR.2016.91. [Artigo][yolo-original].
- **REZATOFIGHI, Hamid; TSOI, Nathan; GWAK, JunYoung; SADEGHIAN, Amir; REID, Ian; SAVARESE, Silvio.** *Generalized Intersection over Union: A Metric and A Loss for Bounding Box Regression*. In: IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2019. Seção 3. [Versão dos autores][iou].
- **STANFORD UNIVERSITY.** *CS231n: Image Classification*. Notas de curso, s.d.a. [Texto][stanford-imagens].
- **STANFORD UNIVERSITY.** *CS231n: Neural Networks Part 2*. Notas de curso, s.d.b. Seção Data Preprocessing. [Texto][stanford-preprocess].
- **STANFORD UNIVERSITY.** *CS231n: Neural Networks Part 1*. Notas de curso, s.d.c. [Texto][stanford-neuron].
- **STANFORD UNIVERSITY.** *CS231n: Convolutional Neural Networks*. Notas de curso, s.d.d. [Texto][stanford-cnn].
- **SZE, Vivienne; CHEN, Yu-Hsin; YANG, Tien-Ju; EMER, Joel.** Efficient Processing of Deep Neural Networks: A Tutorial and Survey. *Proceedings of the IEEE*, v. 105, n. 12, p. 2295–2329, 2017. [DOI](https://doi.org/10.1109/JPROC.2017.2761740); [versão dos autores][sze].
- **TENCENT.** *ncnn*. Repositório e documentação oficial, s.d. Seções de apresentação, conversão e recursos. [Projeto][ncnn].
- **ULTRALYTICS.** *Model Prediction with Ultralytics YOLO*. Documentação técnica, s.d.a. [Documento][ultralytics-predict].
- **ULTRALYTICS.** *Object Detection with Ultralytics YOLO*. Documentação técnica, s.d.b. [Documento][ultralytics-detect].
- **ULTRALYTICS.** *Ultralytics YOLO26*. Documentação técnica, s.d.c. [Documento][ultralytics-yolo26].
- **ULTRALYTICS.** *ultralytics/utils/nms.py*. Código-fonte, versão 8.4.108, 2026. Referência à implementação consultada, sem pressupor que seja a versão final do experimento. [Arquivo em versão fixa][ultralytics-nms].
- **ZHANG, Aston; LIPTON, Zachary C.; LI, Mu; SMOLA, Alexander J.** *Dive into Deep Learning*. Cambridge University Press, 2023. Versão on-line: seções 7.2 e 14.2. [Livro](https://d2l.ai/); [camadas convolucionais][d2l-conv]; [ajuste fino][d2l-finetune].

## Notas para a próxima revisão

Estas notas orientam a revisão do rascunho e não integram a redação final do capítulo.

- O recorte foi limitado aos quatro temas acordados. Seleção e acompanhamento, robótica móvel, avaliação experimental e desenvolvimento ficarão para as partes correspondentes do TCC. As referências pertinentes estão distribuídas no texto.
- Ainda precisamos decidir quanto detalhamento específico de YOLO26 ficará na fundamentação. O projeto já contém configuração para YOLO26n, mas sua execução embarcada e a escolha definitiva não foram estabelecidas pelos testes anteriores.
- O preprint de YOLO26 e a documentação técnica consultada diferem sobre qual caminho de detecção é o padrão. O texto evita fixar um padrão e registra somente a disponibilidade de caminhos com e sem NMS. Na metodologia, será necessário identificar versão do software e configuração exportada.
- A descrição de recursos do NCNN não afirma que todos estão habilitados no Raspberry. Quantização foi apresentada como conceito, não como otimização já implementada no projeto.
- Figuras autorais podem melhorar a próxima versão: organização RGB, filtro percorrendo uma matriz, caixa com coordenadas e separação entre pesos e ativações na memória.
- Para migrar ao LaTeX, converter as referências aprovadas em registros bibliográficos, revisar siglas e transformar as expressões em equações numeradas quando forem referenciadas. Nenhum arquivo do capítulo LaTeX foi alterado nesta etapa.

[stanford-imagens]: https://cs231n.github.io/classification/
[arm-neon]: https://www.arm.com/technologies/neon
[pascal]: https://www.robots.ox.ac.uk/~vgg/projects/pascal/VOC/voc2010/
[opencv-transform]: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html
[stanford-preprocess]: https://cs231n.github.io/neural-networks-2/
[stanford-neuron]: https://cs231n.github.io/neural-networks-1/
[stanford-cnn]: https://cs231n.github.io/convolutional-networks/
[lecun-1998]: https://bottou.org/papers/lecun-98h
[lecun-2015]: https://doi.org/10.1038/nature14539
[dumoulin]: https://arxiv.org/html/1603.07285v2
[d2l-conv]: https://d2l.ai/chapter_convolutional-neural-networks/conv-layer.html
[d2l-finetune]: https://d2l.ai/chapter_computer-vision/fine-tuning.html
[goodfellow]: https://www.deeplearningbook.org/contents/ml.html
[ultralytics-predict]: https://docs.ultralytics.com/modes/predict/
[ultralytics-detect]: https://docs.ultralytics.com/tasks/detect/
[ultralytics-nms]: https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.108/ultralytics/utils/nms.py
[kuppers]: https://arxiv.org/abs/2004.13546
[iou]: https://arxiv.org/pdf/1902.09630
[yolo-original]: https://www.cv-foundation.org/openaccess/content_cvpr_2016/papers/Redmon_You_Only_Look_CVPR_2016_paper.pdf
[yolo26-paper]: https://arxiv.org/html/2606.03748v1
[ultralytics-yolo26]: https://docs.ultralytics.com/models/yolo26/
[sze]: https://arxiv.org/pdf/1703.09039
[onnx]: https://onnx.ai/onnx/intro/concepts.html
[ncnn]: https://github.com/Tencent/ncnn
[mobilenets]: https://arxiv.org/pdf/1704.04861
[jacob]: https://openaccess.thecvf.com/content_cvpr_2018/papers/Jacob_Quantization_and_Training_CVPR_2018_paper.pdf
[raspberry]: https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-product-brief.pdf
