# Escrita do TCC em LaTeX

Arquivo principal: `monografia.tex`. Introdução: `tex/cap1.tex`. Fundamentação teórica: `tex/cap2.tex`. Referências: `referencias.bib`.
A introdução foi convertida do Word com quatro seções e onze objetivos específicos. Em 26/10/2026, as referências sobre YOLO e o hardware do Raspberry foram preenchidas com as fontes cadastradas para a fundamentação. Permanecem três marcações na introdução: modelo da câmera, condições experimentais e fontes sobre seguimento visual/avaliação do sistema. O Word permanece como fonte original da conversão.

## Fundamentação integrada em 26/10/2026

O capítulo 2 substitui os exemplos herdados do modelo pelo conteúdo de `../blocos_de_escrita/FUNDAMENTACAO_TEORICA_RASCUNHO.md`: imagens digitais, redes convolucionais, detecção/YOLO e inferência embarcada. São quatro seções, 19 subseções e quatro equações numeradas com rótulos. As notas de revisão do Markdown permanecem no rascunho e não foram incluídas no capítulo.

As 26 fontes do rascunho foram cadastradas em BibTeX, com datas de acesso e metadados conferidos. As duas seções de *Dive into Deep Learning* usam a mesma entrada `d2l-2023`. As três referências preexistentes foram preservadas, totalizando 29 registros; somente as fontes citadas aparecem na bibliografia. Use `\cite{chave}` para citações entre parênteses e `\citeonline{chave}` para citar autores no texto. As letras de documentos do mesmo autor e sem data são calculadas automaticamente; não copie manualmente as letras do Markdown.

O cadastro de siglas foi ampliado para RGB, BGR, JPEG, CNN, ReLU, IoU, NMS, ONNX, CPU, SIMD, CSI-2 e LPDDR2. Produtos e bibliotecas, como NCNN, continuam escritos como nomes próprios. As cópias anteriores dos arquivos alterados e do PDF estão em `backup_fundamentacao_2026-10-26/`.

## Edição e prévia no VS Code

Abra a pasta `C:\Zeral\TCC\tcc_jose_fidelis` no VS Code para carregar a configuração de `.vscode/settings.json`.

1. Abra `Documentacao/Doc/projeto_base/monografia.tex`.
2. Pressione **Ctrl+Alt+B** para compilar. Pela paleta (**Ctrl+Shift+P**), o comando equivalente é **LaTeX Workshop: Build LaTeX project**.
3. Pressione **Ctrl+Alt+V** para abrir o PDF ao lado do texto. Pela paleta, use **LaTeX Workshop: View LaTeX PDF file**.
4. Edite os capítulos em `tex/cap1.tex` a `tex/cap5.tex`. Ao salvar (**Ctrl+S**), a extensão recompila o documento principal e atualiza a prévia.

Os comentários `% !TEX root = ../monografia.tex` nos capítulos indicam o arquivo principal. A busca automática foi limitada ao `projeto_base` para não compilar por engano o modelo de exemplo ou os backups. O PDF gerado é `monografia.pdf` nessa pasta; os PDFs em `pdf/` são elementos pré-textuais herdados do modelo.

A extensão **LaTeX Workshop** já estava instalada. O compilador **MiKTeX** foi instalado para o usuário `zehen`. A receita usa `texify`, que coordena as passagens de LaTeX e as referências bibliográficas sem depender de uma instalação separada de Perl. A primeira compilação pode baixar pacotes adicionais. O caminho do compilador em `.vscode/settings.json` corresponde a este computador; ajuste-o se mover o projeto para outra máquina.

Se os atalhos não responderem, use os comandos da paleta ou o painel **TeX**. Se a extensão não reconhecer a configuração nova, execute **Developer: Reload Window** na paleta. Erros de compilação aparecem no painel **Problems/Problemas** e no canal de saída **LaTeX Workshop**.

Fontes: [LaTeX Workshop — compilação](https://github.com/James-Yu/LaTeX-Workshop/wiki/Compile), [visualização do PDF](https://github.com/James-Yu/LaTeX-Workshop/wiki/View) e [MiKTeX — texify](https://docs.miktex.org/manual/texify.html).

## Siglas e outras entidades

Defina cada sigla uma vez em `tex/siglas.tex`:

```latex
\registrarsigla{yolo}{YOLO}{You Only Look Once}
```

No texto, use `\gls{yolo}`: primeira ocorrência por extenso e sigla; seguintes abreviadas. Use `\acrshort{yolo}` para somente a sigla e `\acrlong{yolo}` para o nome por extenso. `\glsresetall` antes da introdução reinicia a apresentação das siglas, útil quando forem usadas também no resumo.

O cadastro alimenta o `glossaries` e a lista institucional já existente. Não precisa executar `makeglossaries`: a lista usa o arquivo auxiliar `.abrv` do modelo. Nesta solução todas as siglas cadastradas entram na lista; remova cadastros sem uso ao revisar os capítulos herdados. Siglas não são sinônimo de produtos: ESP32 é um nome de família de microcontroladores e pode permanecer como nome próprio.

Use referências e numeração automáticas:

```latex
\section{Procedimento experimental}\label{sec:procedimento}
Conforme a Seção~\ref{sec:procedimento}...
\begin{equation}\label{eq:erro}
    e_x = \frac{x_c-x_p}{W/2}
\end{equation}
Segundo \citeonline{chaveNoBib}, ...
Uma afirmação com fonte~\cite{chaveNoBib}.
```

Cadastre as fontes reais em `referencias.bib`; `chaveNoBib` acima é um exemplo, não uma referência existente. Em figuras, coloque `\label` depois de `\caption`. O modelo também já oferece `siunitx` para unidades e `\simbolo{...}{...}` para cadastro de símbolos. Evite escrever números de capítulos, figuras e referências manualmente.

## Compilação

No Overleaf, envie o conteúdo completo de `projeto_base`, selecione `monografia.tex` como principal e pdfLaTeX como compilador. O modelo usa abnTeX2 com BibTeX (`abntex2cite`), não Biber. Localmente, com uma distribuição TeX instalada, execute dentro de `projeto_base`:

```text
pdflatex -interaction=nonstopmode -halt-on-error monografia.tex
bibtex monografia
pdflatex -interaction=nonstopmode -halt-on-error monografia.tex
pdflatex -interaction=nonstopmode -halt-on-error monografia.tex
```

Em 7 de outubro de 2026, o documento foi compilado com MiKTeX e gerou um PDF de 32 páginas. A introdução e a lista de siglas foram conferidas visualmente, incluindo acentuação e expansão de YOLO na primeira ocorrência. O comando de compilação terminou com sucesso.

Para permitir a primeira compilação, as listas institucionais de siglas/símbolos passaram a tratar arquivos auxiliares ainda vazios. Foi removida uma configuração antiga que desativava macros necessárias ao BibTeX e duplicava a declaração de bibliografia. Os links automáticos de `glossaries` foram desativados porque a lista institucional não cria os alvos desse pacote; as referências de capítulos, seções, figuras e tabelas continuam disponíveis.

Em 26/10/2026, a integração da fundamentação gerou um PDF de 42 páginas, com o capítulo 2 nas páginas impressas 19 a 29 e 26 fontes na bibliografia. A compilação foi conferida com BibTeX e `texify`, sem citações ou referências internas indefinidas e sem texto excedendo as margens. A lista de siglas, o sumário, o capítulo e as referências foram conferidos visualmente.

As citações fictícias `ref:ibmm` e `ref:mulligan` saíram junto com o conteúdo antigo do capítulo 2. A citação fictícia `ref:Nuseibeh` foi removida do exemplo do capítulo 3, com comentário no fonte; a metodologia continua por redigir. O estilo local `abntex2-alf.bst` recebeu uma correção mínima para imprimir as letras de desambiguação também no ano da referência, mantendo correspondência com as citações (por exemplo, `s.d.a` e `s.d.b`). Há avisos de compatibilidade dos pacotes antigos do modelo que não impedem a compilação.

## Antes de entregar

O nome **José Henrique Schmitt Fidelis** foi confirmado e registrado em `monografia.tex`, em caixa alta na capa e na folha de rosto. Os metadados do PDF também usam esse nome. Foram preenchidas as palavras-chave provisórias **Visão computacional**, **Robótica móvel** e **Seguimento de pessoas**, com suas versões em inglês; elas correspondem ao objetivo geral da introdução. Os comandos `\palavraschavetcc` e `\keywordstcc` centralizam os termos exibidos no resumo e no abstract.

O autor confirmou em 07/10/2026 o título sugerido e os dados acadêmicos abaixo.
Departamento e curso do cabeçalho agora são definidos em `monografia.tex`, pelos
comandos `\departamentotcc` e `\cursotcc`, e usados na capa e folha de rosto.
A vinculação da Engenharia Eletrônica ao Departamento Acadêmico de Eletrônica
foi conferida na [página institucional do DAELN](https://www.ifsc.edu.br/web/campus-florianopolis/daeln).

| Campo | Situação atual |
| --- | --- |
| Título | Sistema de seguimento de pessoas com visão computacional embarcada no Raspberry Pi Zero 2 W. |
| Instituição, câmpus e curso | IFSC, Florianópolis e Engenharia Eletrônica, confirmados. |
| Departamento | Departamento Acadêmico de Eletrônica; substituídos os campos `XXXXX` e `XXXX` do cabeçalho. |
| Orientador | Matheus Leitzke Pinto; mantida a indicação de titulação `Me` do modelo. |
| Ano de defesa | 2026, confirmado. |
| Resumo e abstract | Ainda contêm instruções genéricas. Redigir após consolidar método e resultados, sem antecipar conclusões. |
| Ficha catalográfica e aprovação | Os PDFs em `pdf/fichacatalografica.pdf` e `pdf/tcc-aprovado.pdf` vieram do modelo; substituir pelos documentos deste trabalho quando disponíveis. |

O capítulo 2 e suas referências já foram integrados, mas continuam sujeitos à revisão acadêmica. Os capítulos 3 a 5, os apêndices e os anexos ainda contêm material do modelo. Dedicatória, agradecimentos e epígrafe também exibem instruções do modelo e são elementos opcionais.

As propostas de escolha aleatória, calibração da distância e busca por rotação foram preservadas do Word; ainda não correspondem ao comportamento atual do MVP. A busca por rotação e o retorno à observação com nova seleção permitida após tempo esgotado ou ausência de direção foram confirmados em 26/10/2026. Consulte o [guia dos diagramas](../../diagramas/software_rpi/README.md) para a especificação prevista e sua comparação com o código.
