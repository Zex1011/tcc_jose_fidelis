# Escrita do TCC em LaTeX

Arquivo principal: `monografia.tex`. Introdução: `tex/cap1.tex`.
A introdução foi convertida do Word com quatro seções e onze objetivos específicos. As cinco pendências de referências, câmera e critérios experimentais continuam visíveis em vermelho; não foram inventados dados ou fontes. O Word permanece como fonte original da conversão.

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

Recompile até estabilizar sumário, referências e lista de siglas. A conversão passou por verificações estruturais, mas não foi compilada nem conferida visualmente porque não foi encontrado compilador nesta máquina.

## Antes de entregar

A capa ainda contém o nome MATHEUS RODRIGUES DA CUNHA e título sobre aplicativo móvel de outro trabalho. Substitua pelos seus dados confirmados. Os outros capítulos, referências, ficha catalográfica e folha de aprovação também vieram do modelo e precisam de revisão. Não use PDFs de aprovação de outra pessoa como seus. O conteúdo do capítulo 1 foi trocado; o restante do modelo não representa automaticamente este TCC.

As propostas de escolha aleatória, calibração da distância e busca por rotação foram preservadas do Word; ainda não correspondem ao comportamento atual do MVP. Consulte `../../REVISAO_INICIAL_2026-10-07.md` para o diagnóstico e decisões pendentes.
