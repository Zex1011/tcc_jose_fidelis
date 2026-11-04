# Resumo das alterações e dos objetivos cumpridos no chat

**Data de consolidação:** 7 de outubro de 2026.  
**Projeto:** TCC de José Henrique Schmitt Fidelis.  
**Escopo:** trabalho realizado nesta conversa, desde a leitura inicial da documentação até a integração e o teste da câmera no Raspberry Pi.

Este documento registra alterações, configurações, decisões, testes e pendências. Distingue o que já existia no projeto, o que foi modificado e o que ainda depende de implementação ou validação. Os resultados abaixo correspondem às condições testadas durante a conversa.

## 1. Situação alcançada

- O TCC pode ser editado e visualizado em PDF no VS Code. A introdução do Word foi integrada ao modelo institucional, com siglas automáticas, rótulos e dados acadêmicos preenchidos.
- O Raspberry passou a ser reconhecido pelo Windows como dispositivo de rede USB. O acesso SSH e o compartilhamento de internet pelo computador funcionaram nos testes.
- O código mínimo foi transferido para o Raspberry, recebeu um ambiente Python próprio e passou nos testes automatizados e no fluxo simulado.
- O módulo de câmera pode ser executado diretamente para salvar uma foto. Uma imagem real foi obtida no Raspberry, transferida para o computador e inspecionada.
- A detecção com YOLO no Raspberry, a comunicação física com o ESP32 e o seguimento com motores ainda não foram validados.

### Tarefas originalmente anotadas

| Tarefa | Situação ao final deste registro |
| --- | --- |
| Criar diagrama de classes ou de blocos | Pendente; a arquitetura existente foi analisada, mas o diagrama não foi produzido. |
| Criar diagrama de estados UML | Pendente; primeiro é necessário alinhar perda de alvo, busca, recuperação e falhas. |
| Portar detecção/reconhecimento de imagens para o RPi | Parcial: código básico, ambiente e câmera funcionam; inferência YOLO e desempenho embarcado ainda precisam de ensaio. |
| Instalar ferramentas para editar LaTeX | Concluído: MiKTeX instalado e LaTeX Workshop configurado no VS Code. |
| Organizar capítulos em arquivos separados | A separação já existia no modelo; foi mantida e preparada para edição, com comentários de arquivo principal e rótulos. O conteúdo dos capítulos seguintes permanece incompleto. |
| Registrar e referenciar siglas com a sintaxe do modelo | Concluído para a integração atual, incluindo YOLO e RAM. |
| Personalizar título, autor e ano | Concluído, com confirmação do autor. |
| Adicionar rótulos aos capítulos e às seções | Concluído nos arquivos atuais, inclusive nos exemplos ainda herdados do modelo. |
| Transferir a documentação elaborada para o LaTeX | Introdução em Word transferida; incorporação do restante da documentação técnica aos capítulos ainda pendente. |

## 2. Entendimento e decisões sobre o projeto

O objetivo discutido é investigar um sistema de seguimento de pessoas com percepção e controle visual locais no **Raspberry Pi Zero 2 W**, usando o ESP32 para executar comandos na plataforma móvel existente.

O MVP já tinha módulos separados de câmera, detecção, seleção de alvo, controle, comunicação e registros. Seu fluxo é sequencial: **capturar → detectar → selecionar alvo → calcular controle → enviar comando e aguardar resposta → registrar → repetir**. Essa arquitetura foi revisada e preservada.

A seleção atual associa caixas delimitadoras; não constitui reconhecimento de identidade de pessoas. O controle utiliza posição e altura relativa da caixa. As referências `v/w` ainda precisam de integração e calibração na plataforma, portanto não representam velocidades físicas medidas e comprovadas.

Foram esclarecidos e confirmados:

- A câmera está conectada diretamente ao **Raspberry**, e não ao ESP32.
- A preferência de edição do TCC é **VS Code com prévia de PDF**.
- Os testes devem evoluir por etapas: **mock → foto → inferência com comunicação simulada → serial/STOP → movimento**.
- A configuração proposta para avaliação inclui YOLO26n exportado para NCNN, inicialmente com entrada de 320 pixels. Sua viabilidade no Pi permanece uma hipótese a medir.
- A meta documental de aproximadamente um ciclo por segundo ainda não é um resultado experimental.

## 3. Revisão inicial e integração da documentação

Foram lidos a introdução em Word, o modelo institucional, o README e partes relevantes do código, configurações, testes e firmware de exemplo. A revisão encontrou diferenças entre as intenções da introdução e o comportamento atual do software.

Foram criados:

- [REVISAO_INICIAL_2026-10-07.md](REVISAO_INICIAL_2026-10-07.md): diagnóstico inicial, diferenças entre texto e código, problemas encontrados e propostas de experimentos.
- [preparar_integracao_latex.py](preparar_integracao_latex.py): utilitário de conversão e preparação da integração, com leitura do DOCX, tratamento de caracteres LaTeX, verificações estruturais, geração de alterações e opção de aplicação com backup.
- [integracao_latex_2026-10-07](integracao_latex_2026-10-07): versões preparadas e patch da integração inicial.
- [backup_integracao_2026-10-07](Doc/projeto_base/backup_integracao_2026-10-07): cópias dos arquivos originais substituídos naquela etapa.

O Word e o projeto institucional de exemplo foram preservados. A conversão verificou 35 parágrafos não vazios da fonte, quatro seções, onze objetivos específicos e cinco marcações de pendências.

**Contexto histórico:** a revisão inicial contém situações anteriores às correções posteriores, como câmera não testada, nome ainda pendente e rede não configurada. Este resumo registra a evolução subsequente. O script de integração também corresponde à migração inicial; não é o comando de compilação cotidiana e precisa ser revisto antes de reaplicá-lo sobre os arquivos já personalizados.

## 4. Alterações no TCC em LaTeX

### Introdução, siglas e referências automáticas

Em [tex/cap1.tex](Doc/projeto_base/tex/cap1.tex), o texto anterior foi substituído pela introdução do Word. Foram mantidos o conteúdo, quatro seções, onze objetivos específicos e cinco avisos de pendências em vermelho, sem inventar fontes ou resultados.

As pendências preservadas abrangem referência sobre YOLO, fonte para as características do Pi, identificação da câmera, trabalhos relacionados e critérios experimentais. O sensor foi identificado depois como OV5647, mas essa descoberta ainda precisa ser incorporada ao texto da introdução.

Em [tex/siglas.tex](Doc/projeto_base/tex/siglas.tex), foi centralizado o cadastro de siglas:

```latex
\registrarsigla{yolo}{YOLO}{You Only Look Once}
\registrarsigla{ram}{RAM}{memória de acesso aleatório}
```

O comando `\gls{yolo}` apresenta a expansão na primeira ocorrência e a sigla nas seguintes. O cadastro alimenta tanto o pacote `glossaries` quanto a lista institucional de abreviaturas. Foi incluído `\glsresetall` antes da introdução; essa configuração dispensa uma etapa separada de `makeglossaries`.

Os cadastros herdados necessários à compatibilidade do modelo foram mantidos. A lista atual inclui todas as siglas cadastradas, portanto deverá ser limpa quando os capítulos forem revisados.

A organização em `cap1.tex` a `cap5.tex`, apêndices e anexos já existia. Foram acrescentados comentários `% !TEX root = ../monografia.tex` e rótulos para referências automáticas, por exemplo `cap:intro`, `cap:fundamentacao`, `cap:metodologia`, `cap:resultados`, `cap:consideracoes-finais` e rótulos de seções. Exemplos de apêndices e anexos também receberam rótulos.

### Dados acadêmicos e apresentação

Os seguintes dados foram preenchidos ou confirmados em [monografia.tex](Doc/projeto_base/monografia.tex):

| Campo | Valor |
| --- | --- |
| Autor | José Henrique Schmitt Fidelis |
| Título | Sistema de seguimento de pessoas com visão computacional embarcada no Raspberry Pi Zero 2 W |
| Instituição e campus | Instituto Federal de Santa Catarina — Florianópolis |
| Curso | Engenharia Eletrônica |
| Departamento | Departamento Acadêmico de Eletrônica |
| Orientador | Matheus Leitzke Pinto |
| Ano de defesa | 2026 |
| Palavras-chave provisórias | Visão computacional; Robótica móvel; Seguimento de pessoas |
| Keywords provisórias | Computer vision; Mobile robotics; Person following |

O título, o nome, a instituição, o curso, o orientador e o ano foram confirmados pelo autor. A vinculação do curso ao departamento foi consultada na [página institucional do DAELN](https://www.ifsc.edu.br/web/campus-florianopolis/daeln). A indicação `Me` do orientador foi mantida como estava no modelo, sem nova comprovação de titulação.

Departamento e curso passaram a ser centralizados por `\departamentotcc` e `\cursotcc`, utilizados por [conf-ifsc.sty](Doc/projeto_base/conf-ifsc.sty) na capa e na folha de rosto. Foram substituídos campos `XXXXX`/`XXXX` e corrigida a grafia de “GRADUAÇÃO”. O ano ficou sem ponto final extra. Nome, título, assunto e palavras-chave também foram atualizados nos metadados do PDF. `\palavraschavetcc` e `\keywordstcc` centralizam os termos dos resumos.

### Correções para compilar o modelo

- A configuração repetida de `caption` foi substituída por `\captionsetup`, evitando recarregar o pacote com opções conflitantes.
- Foi removida uma importação redundante do pacote `acronym` em [conf-pacotes.sty](Doc/projeto_base/conf-pacotes.sty).
- Em [conf-comandos.sty](Doc/projeto_base/conf-comandos.sty), as listas ordenadas de siglas e símbolos passaram a tratar bases auxiliares vazias, permitindo a primeira compilação.
- Foram retiradas redefinições antigas de macros de substring que interferiam no `abntex2cite` e geravam declarações duplicadas de bibliografia.
- Os links próprios de `glossaries` foram desativados com `\glsdisablehyper`, pois a lista institucional não cria seus destinos. As referências cruzadas do documento continuam disponíveis.
- Os auxiliares afetados pela configuração antiga foram regenerados durante a correção da compilação.

O PDF compilou com sucesso e ficou com **32 páginas** na versão verificada. Introdução e lista de siglas foram inspecionadas visualmente; texto e metadados da capa também foram conferidos. Isso valida a geração da prévia, não a conclusão acadêmica de todos os capítulos.

### Arquivos e conteúdo ainda genéricos

Os capítulos 2 a 5 ainda contêm exemplos ou texto incompleto, incluindo trechos de outro trabalho sobre robótica educacional, Bluetooth/Flutter e elementos ilustrativos do modelo. Resumo, abstract, dedicatória, agradecimentos, epígrafe, apêndices e anexos também precisam de revisão.

Os PDFs `pdf/fichacatalografica.pdf` e `pdf/tcc-aprovado.pdf` continuam herdados do modelo e devem ser substituídos pelos documentos deste TCC. As referências `ref:ibmm`, `ref:mulligan` e `ref:Nuseibeh` estão ausentes da base bibliográfica; a bibliografia permanece vazia enquanto os registros reais não são citados. Permanecem avisos de compatibilidade do modelo e do MiKTeX, apesar da compilação bem-sucedida.

## 5. Ambiente LaTeX no VS Code

A extensão **LaTeX Workshop 10.19.0 já estava instalada**. Foi instalado o **MiKTeX 25.12**, no escopo do usuário Windows, e configurada uma receita com `texify`, sem exigir instalação separada de Perl.

Foram criados ou ajustados:

- [.vscode/settings.json](../.vscode/settings.json): receita de compilação, compilação ao salvar, PDF em aba lateral, quebra visual de linhas e descoberta do documento principal.
- [.vscode/extensions.json](../.vscode/extensions.json): recomendação da extensão LaTeX Workshop.
- [GUIA_LATEX.md](Doc/projeto_base/GUIA_LATEX.md): instruções de edição, compilação, siglas, referências, metadados e pendências.

A receita usa `texify.exe`, geração de PDF e SyncTeX, instalação automática de pacotes necessários e `%DOC_EXT%` para passar o nome completo do arquivo. O caminho configurado aponta para `C:\Users\zehen\AppData\Local\Programs\MiKTeX\miktex\bin\x64`; outro computador precisará de ajuste.

A busca do arquivo principal foi limitada ao `projeto_base`, excluindo projeto de exemplo, backups, versões intermediárias e ambientes virtuais. A receita foi executada com sucesso e o PDF foi aberto no VS Code.

Uso cotidiano: **Ctrl+S** salva e recompila; **Ctrl+Alt+B** compila; **Ctrl+Alt+V** abre a prévia. Não foi realizada uma atualização completa da distribuição MiKTeX.

## 6. Correção da rede USB e acesso ao Raspberry

### Driver e endereço local

O dispositivo inicialmente aparecia como **Dispositivo Serial USB (COM6)**, associado ao driver `usbser.inf`, embora anunciasse uma interface de rede. Foi identificado o hardware ID `USB\VID_0525&PID_A4A2`.

O procedimento do Gerenciador de Dispositivos foi explicado e foi localizado um [pacote correspondente no Microsoft Update Catalog](https://www.catalog.update.microsoft.com/ScopedViewInline.aspx?updateid=38c84d13-eb1b-4327-aae5-e36e8cb7933d). O usuário realizou a troca do driver e confirmou a instalação bem-sucedida de **USB Ethernet/RNDIS Gadget**.

A interface passou a aparecer como **Ethernet 2**, índice 53 na sessão consultada. Foi configurado o endereço **192.168.7.1/24** no Windows. O Pi já usava **192.168.7.2/24** em `usb0`, com rota padrão via `192.168.7.1`.

### Compartilhamento de internet e SSH

Foi configurado o NAT **PiNAT** para `192.168.7.0/24`, com encaminhamento IPv4 habilitado nas interfaces USB e de saída. A conexão de internet do computador chamava-se **Wi-Fi 2**, índice 19, diferentemente de “Wi-Fi” no exemplo inicial do professor. Nomes e índices devem ser conferidos novamente se o hardware ou a configuração mudar.

Na etapa inicial, o Pi alcançava o Windows, mas não o endereço externo testado. Depois dos ajustes, foram confirmados resolução DNS, acesso HTTPS ao servidor Ubuntu com resposta HTTP 200 e downloads por `apt`/`pip` a partir do Pi.

Foram verificados ping entre as máquinas, porta TCP 22 e acesso SSH. O usuário conseguiu entrar e, posteriormente, os comandos remotos e transferências também foram executados diretamente pelas ferramentas do assistente.

| Item | Valor verificado |
| --- | --- |
| Hostname | `companionboard1` |
| Usuário SSH | `juca` |
| Endereço do Pi | `192.168.7.2` |
| Endereço USB do Windows | `192.168.7.1` |
| Rede interna do NAT | `192.168.7.0/24` |

A autenticação utilizada foi por senha; não foram configuradas chaves SSH. Senhas não são registradas neste resumo. O Wi-Fi do Pi estava desativado no inventário e não foi configurado nesta etapa. A persistência de toda a conexão após reinicialização/reconexão completa ainda não foi ensaiada.

## 7. Inventário do hardware e do sistema

| Item | Resultado |
| --- | --- |
| Placa | Raspberry Pi Zero 2 W Rev 1.0 |
| Sistema | Ubuntu 24.04.4 LTS, Noble Numbat |
| Kernel observado | `6.8.0-1057-raspi` |
| Arquitetura | ARM64 / `aarch64` |
| Python | 3.12.3 |
| RAM reportada pelo sistema | Aproximadamente 409 MiB utilizáveis, em placa de 512 MB |
| Partição principal no inventário inicial | 29 GB, cerca de 7 GB usados e 21 GB disponíveis |
| Swap inicial e final | Zero; houve apenas swap temporário para compilação |
| Sensor da câmera | OV5647, identificado pelo sistema e pelo driver |
| Captura CSI | Pipeline Unicam, `/dev/video0`, sensor em `/dev/v4l-subdev0` e grafo em `/dev/media0` |

Os vários arquivos `/dev/video*` não representam várias câmeras físicas: parte deles corresponde a codecs e processamento de imagem. A inscrição comercial `UC436` presente na documentação anterior não foi suficiente para fechar a identificação comercial/revisão do módulo; a identificação confirmada é a do sensor OV5647.

O sistema operacional foi mantido. A configuração de boot já continha `camera_auto_detect=1` e não foi alterada.

## 8. Alterações no software FollowBot

Nesta seção, os caminhos são relativos a [followbot_mvp_audited/followbot_mvp_audited](../followbot_mvp_audited/followbot_mvp_audited).

| Arquivo | Alteração e finalidade |
| --- | --- |
| `src/followbot/camera/__init__.py` | Carregamento sob demanda dos adaptadores, evitando exigir dependências opcionais no mock e evitando importação antecipada ao executar o módulo de câmera. |
| `src/followbot/camera/dataset_camera.py` | Importação de OpenCV movida para a criação desse adaptador, com erro explicativo caso a dependência falte. |
| `src/followbot/models.py` | Documentado o contrato de `Frame.image`: array RGB, `uint8`, dimensões altura × largura × canais. |
| `src/followbot/camera/picamera2_camera.py` | Captura compatível com o contrato RGB, execução independente, validação de parâmetros, aquecimento configurável e fechamento da câmera em situações de erro. |
| `src/followbot/vision/ultralytics_detector.py` | Conversão de RGB interno para BGR contíguo antes da chamada ao detector, preservando o array original. |
| `configs/profiles/rpi_vision.toml` | Novo perfil com câmera e detector reais, comunicação simulada e gravação visual desativada inicialmente. |
| `scripts/run_profile.py` | Registro do novo perfil `rpi_vision`. |
| `tests/test_camera_debug.py` | Seis testes para o comando de câmera, validações, salvamento e liberação de recursos. |
| `tests/test_detector_colors.py` | Dois testes para conversão de cores, contiguidade e preservação da imagem de origem. |
| `README.md` e `INSTALL_TEST.md` | Atualização do estado do hardware, preparação, comandos de teste, limitações e procedimento usado no Ubuntu. |
| `scripts/env_camera_ubuntu2404.sh` | Ativação do ambiente Python e das bibliotecas privadas de câmera testadas no Pi. |
| `scripts/patches/libcamera-0.2.0-followbot.patch` | Registro das duas alterações usadas para compilar e corrigir a biblioteca de câmera. |
| `scripts/patches/picamera2-0.3.17-headless.patch` | Registro da adaptação para uso sem prévia gráfica DRM/`pykms`. |

### Execução independente da câmera

O módulo recebeu `main(argv=None)` e `if __name__ == "__main__"`. Ele usa o mesmo método de captura da aplicação e permite salvar JPEG ou PNG com Pillow, sem carregar o detector ou abrir serial e janela gráfica.

Foram acrescentadas opções de saída, largura, altura e aquecimento. Os padrões são 640 × 480 e um segundo de aquecimento. O código cria diretórios de saída quando necessário, valida dimensões e aquecimento finito/não negativo e fecha a câmera após captura, erro ou interrupção. O fechamento é idempotente e também ocorre quando a inicialização falha.

Foi adotado o formato `BGR888` da Picamera2/libcamera para obter a ordem de bytes RGB esperada no array desta integração. A adaptação para BGR acontece na entrada da Ultralytics. Essa distinção evita uma troca de canais entre captura e inferência.

O perfil `rpi_vision` aponta para `models/yolo26n_ncnn_model`, com entrada 320, confiança 0,35 e classe `person`. Foi preparado e validado como configuração, mas ainda não executado com inferência real no Pi. O perfil `rpi` existente continua destinado à comunicação serial real.

## 9. Integração da câmera no Ubuntu do Raspberry

A integração exigiu mais que instalar uma biblioteca Python: a imagem Ubuntu apresentava problemas na combinação de libcamera, bindings e Picamera2.

### Diagnóstico e correção da captura nativa

1. Foram instalados `libcamera-tools`, `libcamera-ipa`, `python3-libcamera` e `v4l-utils`, com suas dependências. Uma falha inicial de download por índices antigos foi resolvida com atualização das listas do `apt` e nova instalação.
2. A enumeração detectava OV5647, mas a captura falhava em `prepareIsp()` com a asserção `it != buffers_.end()`.
3. Uma captura Bayer bruta via V4L2 confirmou que o sensor produzia dados. Sua conversão diagnóstica ficou muito escura e não foi considerada a foto final validada.
4. Foi identificada uma [correção upstream do libcamera](https://patchwork.libcamera.org/patch/19446/) que inicializa `params.buffers.embedded = 0`.
5. O código Raspberry Pi libcamera **v0.2.0** foi baixado, corrigido e compilado no Pi com o pipeline `rpi/vc4`. Foram instaladas as ferramentas e bibliotecas de desenvolvimento necessárias, incluindo Meson, Ninja e dependências de YAML, eventos, GnuTLS e geração de código.
6. Um aviso do GCC 13 tratado como erro bloqueou a compilação do worker IPA. Foi aplicada, apenas a esse alvo, a opção `-Wno-error=maybe-uninitialized`. Essa adaptação de compilação é distinta da correção upstream da captura.
7. A compilação usou um processo por vez e **512 MiB de swap temporário**. Terminou com sucesso, e o runtime foi instalado em `~/followbot-camera-check/runtime`.

A biblioteca compilada ficou em um prefixo privado do usuário, sem substituir os arquivos da libcamera do sistema. Foram obtidos quadros processados com o runtime corrigido; esse ensaio isolado da câmera não é benchmark de YOLO ou do robô.

### Ambiente Python e Picamera2

- Foi transferida uma cópia pequena do projeto para **`~/followbot`**, incluindo código, configurações, testes e scripts. O ambiente virtual existente no computador não foi copiado.
- Foi criado um ambiente `.venv` novo no Pi com `--system-site-packages`, após instalar o suporte a `venv` necessário. O projeto foi instalado em modo editável.
- Foram instaladas dependências Python da câmera. A tentativa com Picamera2 **0.3.12** apresentou incompatibilidade de API; a versão final utilizada foi **0.3.17**.
- O pacote Ubuntu de bindings libcamera estava em `/usr/lib/aarch64-linux-gnu/python3.12/site-packages`, fora do caminho usual de importação. Foi acrescentado `followbot-libcamera.pth` no ambiente virtual do projeto para disponibilizar esse diretório.
- A importação de Picamera2 exigia `pykms` mesmo para captura sem interface gráfica. Foi aplicada uma adaptação local que permite `NullPreview` quando somente `pykms` está ausente e informa erro se uma prévia DRM for solicitada. A captura continua usando a câmera e bibliotecas reais.
- Os patches foram preservados no projeto e conferidos contra os arquivos modificados no Pi. Reinstalar Picamera2 pode sobrescrever a adaptação e exigir reaplicação.
- O script `env_camera_ubuntu2404.sh` ativa o ambiente virtual e configura caminhos de bibliotecas, módulos IPA, executáveis auxiliares e arquivos de ajuste da libcamera apenas no shell em que for carregado.

Essa é a combinação testada nesta imagem Ubuntu. O procedimento detalhado está na seção 8 de [INSTALL_TEST.md](../followbot_mvp_audited/followbot_mvp_audited/INSTALL_TEST.md); não deve ser confundido com uma instalação padrão de Picamera2 no Raspberry Pi OS.

### Foto obtida e limpeza final

Foi capturada uma imagem JPEG real de **640 × 480**, usando o módulo Python do projeto. A imagem foi copiada para o computador e inspecionada:

[Abrir foto de teste — camera_rpi_2026-10-07.jpg](../followbot_mvp_audited/followbot_mvp_audited/logs/camera_rpi_2026-10-07.jpg)

O arquivo local possui 25.827 bytes e mostra uma cena interna. A captura comprova funcionamento da câmera nessa configuração, mas ainda será necessário ajustar enquadramento e iluminação para os experimentos de seguimento.

O swap temporário foi desativado e seu arquivo removido. Uma nova foto foi capturada com swap em zero, registrada no Pi como `~/followbot/logs/camera_no_swap.jpg`. A sessão SSH de trabalho foi encerrada após os testes, sem compilação em andamento.

## 10. Validações realizadas

| Verificação | Resultado e alcance |
| --- | --- |
| Testes originais do projeto | Sete testes passaram na revisão inicial. |
| Dependências opcionais | A falha de importação sem OpenCV foi reproduzida e corrigida; o mock foi verificado sem depender da pilha de visão. |
| Testes após as alterações de câmera e cores | Quinze testes passaram no computador: sete existentes e oito acrescentados. |
| Execução simulada no computador | Vinte ciclos concluídos, sem periféricos reais. |
| Compilação LaTeX | Receita do VS Code concluída com sucesso; PDF de 32 páginas e inspeções de conteúdo/formatação. |
| Rede local e SSH | Ping, porta 22 e autenticação SSH funcionaram. |
| Internet no Pi pelo Windows | DNS, HTTPS ao servidor Ubuntu e downloads de dependências funcionaram. |
| Sensor e captura | OV5647 identificado; captura bruta, quadros processados e foto pelo módulo Python obtidos. |
| Testes no Raspberry | Quinze testes passaram, em aproximadamente 2,176 segundos na execução registrada. |
| Execução simulada no Raspberry | Vinte ciclos concluídos; comunicação e comandos permaneceram simulados. |
| Runtime privado da câmera | Captura com os caminhos configurados pelo script de ambiente concluída com sucesso. |
| Câmera sem swap | Nova captura concluída após a remoção do swap temporário. |
| Patches e script de ambiente | Patches conferidos por aplicação reversa em modo de verificação; sintaxe Bash e carregamento real do ambiente verificados. |

Os testes automatizados de câmera/cores usam substitutos controlados quando apropriado; a foto real é uma evidência adicional e separada. Nenhum desses resultados demonstra ainda desempenho da inferência ou seguimento físico de pessoas.

## 11. Artefatos para retomar o trabalho

### No computador

- [Documento principal](Doc/projeto_base/monografia.tex), [introdução](Doc/projeto_base/tex/cap1.tex), [siglas](Doc/projeto_base/tex/siglas.tex) e [PDF compilado](Doc/projeto_base/monografia.pdf).
- [Guia de LaTeX](Doc/projeto_base/GUIA_LATEX.md), [revisão inicial](REVISAO_INICIAL_2026-10-07.md), [script da integração](preparar_integracao_latex.py), backups e patch da conversão.
- [README do software](../followbot_mvp_audited/followbot_mvp_audited/README.md) e [instruções de instalação/teste](../followbot_mvp_audited/followbot_mvp_audited/INSTALL_TEST.md).
- [Módulo da câmera](../followbot_mvp_audited/followbot_mvp_audited/src/followbot/camera/picamera2_camera.py), [perfil rpi_vision](../followbot_mvp_audited/followbot_mvp_audited/configs/profiles/rpi_vision.toml), [script de ambiente](../followbot_mvp_audited/followbot_mvp_audited/scripts/env_camera_ubuntu2404.sh), [patches](../followbot_mvp_audited/followbot_mvp_audited/scripts/patches) e foto de teste.

### No Raspberry

| Local | Conteúdo |
| --- | --- |
| `~/followbot` | Cópia de trabalho do código, configurações, scripts, testes e ambiente virtual. |
| `~/followbot/logs` | Fotos de captura, incluindo o teste posterior à remoção do swap, e registros de execução. |
| `~/followbot-camera-check/runtime` | Libcamera compilada, ferramentas e arquivos necessários ao processamento da câmera. |
| `~/followbot-camera-check/libcamera-0.2.0` | Código-fonte e diretório de compilação da biblioteca corrigida. |
| `~/followbot-camera-check` | Arquivos de diagnóstico, pacotes de transferência e registros de preparação, compilação, captura e testes. |

Entre os registros remotos estão `cam.log` (falha inicial), `raw.log`, `sensor.raw`, `corrected-cam.log`, `configure.log`, `build.log`, `build-resume.log`, `runtime-install.log`, `python-capture.log`, `final-capture.log`, `capture-no-swap.log`, `tests.log` e `mock.log`. Alguns arquivos documentam tentativas anteriores; o erro em um log inicial não significa que a correção posterior falhou.

### Comandos de retomada já compatíveis com o ambiente preparado

No PowerShell do computador:

```powershell
ssh juca@192.168.7.2
```

No terminal do Raspberry:

```bash
cd ~/followbot
source scripts/env_camera_ubuntu2404.sh
python -m followbot.camera.picamera2_camera --output logs/camera-teste.jpg --width 640 --height 480 --warmup 3
python -m unittest discover -s tests -v
python scripts/run_profile.py mock --max-cycles 20
```

Para copiar a foto, em outro terminal PowerShell, no diretório onde se deseja salvá-la:

```powershell
scp juca@192.168.7.2:~/followbot/logs/camera-teste.jpg .\camera-teste.jpg
```

O comando `source` deve ser repetido em cada novo shell de teste da câmera. Esses comandos pressupõem a conexão USB ativa e os arquivos já preparados; não refazem toda a instalação.

## 12. Problemas identificados que ainda não foram corrigidos

### Coerência entre texto e implementação

- A introdução prevê seleção aleatória; a configuração atual seleciona a primeira detecção.
- A introdução prevê busca por rotação após perder o alvo; o comportamento atual é STOP.
- A proposta de distância calibrada ainda não corresponde ao controle por altura relativa da caixa.
- Texto e código precisam usar a mesma normalização do erro horizontal: largura ou meia largura produzem escalas diferentes.
- A associação por caixa pode trocar a pessoa seguida em cruzamentos; detecção de pessoa não resolve identidade.
- Trechos do README, da formulação e de documentos anteriores ainda precisam de revisão de consistência, mesmo após as atualizações feitas.

### Medição, robustez e integração física

- `cycle_total` inclui espera por ACK e exclui logging/debug posteriores; não mede sozinho a frequência efetiva nem a latência aquisição–envio. O timestamp da câmera é registrado após a captura, não como instante comprovado da exposição.
- O envio de STOP precisa tratar melhor o resultado: há registro de envio sem verificar sucesso e a inicialização não é interrompida quando a tentativa inicial falha.
- Se a criação do detector falhar depois de abrir a câmera em `build_orchestrator`, falta fechamento explícito nesse caminho de erro.
- `applyVelocityReference()` no firmware de exemplo continua sem implementação dos motores. ACK indica processamento da mensagem, não movimento executado ou medido.
- A validação de valores numéricos e limites no protocolo/firmware precisa ser fortalecida.
- O benchmark desktop existente, apresentado como simulação do Pi e associado a 27,8 Hz, não comprova desempenho embarcado e ainda precisa de correção documental.
- Limitar variáveis OMP/BLAS/NumExpr não comprova o número de threads interno do NCNN.
- O adaptador atual usa Ultralytics, cuja pilha inclui Torch/Torchvision/OpenCV mesmo com modelo NCNN. Não foram instaladas e validadas essas dependências de IA no Pi nesta etapa. Um adaptador NCNN direto permanece uma alternativa a avaliar, não uma implementação realizada.
- A porta de dados USB do Zero 2 W está ocupada pelo acesso de rede ao computador. Para conectar o ESP32 como dispositivo USB, será necessário reorganizar o acesso, por exemplo com Wi-Fi; outra possibilidade a estudar é UART adequada à plataforma.

## 13. Próximos passos propostos, ainda sujeitos ao alinhamento do trabalho

1. **Revisar a escrita com o estado real:** atualizar a identificação do sensor, remover exemplos alheios, resolver citações e escolher quais promessas da introdução serão implementadas ou ajustadas com o orientador.
2. **Formalizar a arquitetura e os estados:** criar os diagramas de blocos/classes e UML após definir seleção, perda de alvo, busca, falhas e parada.
3. **Avaliar a inferência embarcada isoladamente:** preparar/exportar o modelo no computador, transferir apenas o necessário e verificar carga, memória e inferência no Pi antes de adicionar comunicação física.
4. **Medir corretamente:** registrar tempo de carregamento, latências e percentis, intervalo entre comandos, frequência efetiva, RAM e temperatura, separando aquisição, inferência, comunicação e escrita de arquivos.
5. **Executar `rpi_vision` quando as dependências de IA estiverem prontas:** combinar câmera e detector com comunicação mock, mantendo o ensaio observável sem acionar motores.
6. **Integrar ESP32 e plataforma:** obter/conferir o firmware real, definir a conexão, implementar os comandos de movimento e testar serial, ACK, STOP e watchdog antes de ensaios móveis.
7. **Conduzir os experimentos e completar os capítulos:** separar cenas de ajuste e avaliação, variar distância/iluminação/oclusões e registrar perdas e trocas de alvo. Quatro imagens repetidas não bastam para avaliar seguimento.

Até este ponto, estão demonstrados o ambiente de escrita, o acesso ao Pi, o funcionamento do núcleo simulado e a captura real pela câmera. A avaliação de detecção e do robô completo constitui a próxima etapa experimental.
