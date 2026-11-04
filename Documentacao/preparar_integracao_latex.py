"""Prepara a introdução em uma pasta separada; --apply aplica com backup."""
from __future__ import annotations

import argparse
import difflib
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'Doc' / 'projeto_base'
DRAFT = ROOT / 'integracao_latex_2026-10-07'
WORD = ROOT / 'Doc' / 'blocos_de_escrita' / 'Introdução.docx'


def escape(text: str) -> str:
    chars = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%',
             '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{',
             '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
             '<': r'\textless{}', '>': r'\textgreater{}'}
    return ''.join(chars.get(c, c) for c in text)


def format_text(text: str) -> str:
    text = text.replace('YOLO (You Only Look Once)', 'YOLO')
    text = re.sub(r'\bYOLO\b', '@@SIGLAYOLO@@', text)
    text = text.replace('memória RAM', '@@SIGLARAM@@')
    result = []
    for part in re.split(r'(<a preencher:.*?>)', text):
        if part.startswith('<a preencher:'):
            result.append(r'\marcador{alterar}{[A preencher: ' + escape(part[13:-1].strip()) + ']}')
        else:
            result.append(escape(part))
    return ''.join(result).replace('@@SIGLAYOLO@@', r'\gls{yolo}').replace('@@SIGLARAM@@', r'\gls{ram}')


def prepare() -> dict[str, str]:
    with ZipFile(WORD) as package:
        document = ET.fromstring(package.read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t', ns)).strip()
                  for p in document.findall('w:body/w:p', ns)]
    paragraphs = [p for p in paragraphs if p]
    assert len(paragraphs) == 35, 'Estrutura do Word mudou: revisar a conversão.'
    assert paragraphs[0] == '1 INTRODUÇÃO'
    output = [r'\chapter{Introdução}', r'\label{cap:intro}', '']
    in_objectives = False
    objective_count = 0
    for paragraph in paragraphs[1:]:
        heading = re.fullmatch(r'1\.[1-4]\s+(.+)', paragraph)
        if heading:
            output.extend([r'\section{' + escape(heading[1]) + '}', ''])
            if heading[1] == 'Objetivos específicos':
                output.append(r'\begin{alineas}')
                in_objectives = True
        elif in_objectives:
            output.append('    ' + r'\item ' + format_text(paragraph))
            objective_count += 1
        else:
            output.extend([format_text(paragraph), ''])
    assert objective_count == 11
    output.extend([r'\end{alineas}', ''])
    chapter = '\n'.join(output)
    assert chapter.count(r'\marcador{alterar}') == 5

    main = (BASE / 'monografia.tex').read_text(encoding='utf-8-sig')
    start = main.index('% Sintaxe:')
    end = main.index('%---------------------------------------------------------------------', start)
    main = main[:start] + '% Cadastro único de siglas: expansão no texto e lista institucional.\n' + r'\input{tex/siglas}' + '\n\n' + main[end:]
    main = main.replace(r'\usepackage[font={bf,small},labelfont=small]{caption}',
                        r'\captionsetup{font={bf,small},labelfont=small}')
    main = main.replace(r'\include{tex/cap1}', r'\glsresetall' + '\n' + r'\include{tex/cap1}')
    packages = (BASE / 'conf-pacotes.sty').read_text(encoding='utf-8-sig')
    packages = packages.replace(r'\usepackage[withpage]{acronym}' + '\n', '')
    acronyms = r'''% Usa glossaries já carregado e preserva a lista de siglas do IFSC.
% Sintaxe: \registrarsigla{chave}{SIGLA}{nome por extenso}
\newcommand{\registrarsigla}[3]{%
    \newacronym{#1}{#2}{#3}%
    \abreviatura{#2}{#3}%
}

\registrarsigla{yolo}{YOLO}{You Only Look Once}
\registrarsigla{ram}{RAM}{memória de acesso aleatório}

% Mantidas para compatibilidade com os demais capítulos do modelo.
\registrarsigla{ifsc}{IFSC}{Instituto Federal de Santa Catarina}
\registrarsigla{daeln}{DAELN}{Departamento Acadêmico de Eletrônica}
\registrarsigla{ihm}{IHM}{Interface Homem-Máquina}
\registrarsigla{iot}{IoT}{Internet das Coisas -- \textit{Internet of Things}}
'''
    guide = r'''# Escrita do TCC em LaTeX

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
'''
    files = {'tex/cap1.tex': chapter, 'tex/siglas.tex': acronyms,
             'monografia.tex': main, 'conf-pacotes.sty': packages,
             'GUIA_LATEX.md': guide}
    DRAFT.mkdir(exist_ok=True)
    patch = []
    for name, content in files.items():
        target = DRAFT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
        original = BASE / name
        old = original.read_text(encoding='utf-8-sig') if original.exists() else ''
        patch.extend(difflib.unified_diff(old.splitlines(keepends=True), content.splitlines(keepends=True),
                                         fromfile='a/' + name, tofile='b/' + name))
    (DRAFT / 'integracao.patch').write_text(''.join(patch), encoding='utf-8')
    print('Validação: 35 parágrafos do Word; 4 seções; 11 objetivos; 5 pendências preservadas.')
    print('Arquivos propostos e patch: ' + str(DRAFT))
    return files


def apply(files: dict[str, str]) -> None:
    backup = BASE / 'backup_integracao_2026-10-07'
    if backup.exists():
        raise RuntimeError('Backup já existe; revisar antes de reaplicar.')
    backup.mkdir()
    for name in files:
        original = BASE / name
        if original.exists():
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, saved)
    # Só substituir depois que todos os backups forem concluídos.
    for name, content in files.items():
        target = BASE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    print('Integração aplicada. Originais preservados em ' + str(backup))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    proposed = prepare()
    if args.apply:
        apply(proposed)
