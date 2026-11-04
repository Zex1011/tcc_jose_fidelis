# FollowBot MVP — instalação e teste em Windows e Ubuntu

Este documento prioriza um processo de teste **progressivo e diagnosticável**. A ideia é não misturar, no primeiro teste, Python + IA + câmera + serial + ESP ao mesmo tempo.

## Resultado da auditoria

### O que já está bom

- O núcleo do projeto é portátil: `numpy`, controle, tracking, configuração e logger funcionam em Windows/Linux.
- O modo `configs/profiles/mock.toml` não depende de Raspberry, câmera, Ultralytics ou ESP.
- `Picamera2` e `Ultralytics` só são importados de fato quando os respectivos backends são instanciados.
- O projeto fecha câmera/comunicação e tenta enviar `STOP` em saída normal ou exceção.
- Os testes atuais do controlador e do seletor passam.

### Pontos que podem atrasar ou confundir

1. **Python 3.11+ é obrigatório.** O projeto usa `tomllib`. Ubuntu 22.04 usa Python 3.10 como padrão, então `python3` puro pode ser insuficiente.
2. **A IA não deve ser instalada no primeiro teste.** `ultralytics` traz PyTorch/OpenCV e pode gerar downloads grandes e resolução de dependências demorada.
3. **Picamera2 não é um backend genérico de Windows/Ubuntu desktop.** Para PC/Linux desktop, use o backend OpenCV/USB em `configs/profiles/webcam.toml`.
4. **Os caminhos de `config` e `model_path` são relativos ao diretório de execução.** Rodar a aplicação fora da raiz do repositório pode fazer o modelo/config não ser encontrado. Os scripts abaixo corrigem isso operacionalmente usando sempre a raiz do projeto.
5. **A porta serial muda por SO.** Windows usa algo como `COM4`; Linux normalmente `/dev/ttyACM0` ou `/dev/ttyUSB0`.
6. **Linux pode bloquear a serial por permissão.** O usuário normalmente precisa pertencer ao grupo `dialout`.
7. **Abrir a serial pode reiniciar o ESP32.** `startup_delay_s = 1.5` pode precisar ser aumentado em algumas placas.
8. **O firmware ESP32 incluso não move os motores.** `applyVelocityReference()` é um placeholder; ele permite testar protocolo/ACK/watchdog, não a locomoção final.
9. **O export NCNN é uma etapa separada.** Fazer isso no primeiro `pip install` aumenta muito o tempo e dificulta identificar a origem de uma falha.
10. **Dependências sem versões totalmente travadas variam com o tempo.** Foi adicionado `constraints/test-direct.txt` para estabilizar as dependências diretas do teste de PC, mas dependências transitivas da pilha de IA ainda podem variar.

## Estratégia recomendada

Execute nesta ordem:

```text
A. Python + venv
B. instalação mínima
C. preflight
D. testes unitários
E. loop mock
F. serial com STOP apenas
G. IA no PC
H. export NCNN
I. Raspberry + Picamera2
J. integração completa
```

Se uma fase falhar, não avance para a próxima até entender a causa.

---

# 1. Teste rápido no Windows

## Recomendação

Use **PowerShell** e Python **3.12 x64**. O projeto também aceita Python 3.11+.

A partir da raiz do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_test_windows.ps1
```

Ou, no PowerShell 7:

```powershell
pwsh -File .\scripts\setup_test_windows.ps1
```

Para mudar a quantidade de ciclos:

```powershell
.\scripts\setup_test_windows.ps1 -Cycles 100
```

O script:

1. procura Python 3.12 e depois 3.11;
2. cria `.venv`;
3. atualiza `pip`, `setuptools` e `wheel`;
4. instala apenas dependências de runtime + teste;
5. roda `scripts/preflight.py`;
6. roda `pytest`;
7. executa o FollowBot com câmera/detector/comunicação simulados;
8. resume os tempos gravados em log.

## Se Python não estiver instalado

No Windows 10/11 atual, uma opção é instalar o Python Install Manager:

```powershell
winget install 9NQ7512CXL7T
py install 3.12
```

Depois feche e abra o terminal e rode o instalador do projeto novamente.

## Se PowerShell bloquear o script

Execute apenas para essa chamada:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_test_windows.ps1
```

Não é necessário alterar permanentemente a política do sistema.

---

# 2. Teste rápido no Ubuntu

## Ubuntu 24.04 LTS

O Python padrão já é 3.12. Garanta suporte a venv:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

Depois:

```bash
bash scripts/setup_test_ubuntu.sh
```

## Ubuntu 22.04 LTS

O Python padrão é 3.10, mas o projeto exige 3.11+.

Instale Python 3.11 e venv:

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv
```

Depois:

```bash
bash scripts/setup_test_ubuntu.sh
```

Se `python3.11` não aparecer no seu espelho/repositórios habilitados, não altere o Python do sistema para “forçar” o projeto. Instale uma versão 3.11/3.12 paralela ou prefira Ubuntu 24.04 para o ambiente de teste.

## Mais ciclos

```bash
FOLLOWBOT_TEST_CYCLES=100 bash scripts/setup_test_ubuntu.sh
```

---

# 3. O que significa “teste passou”

O final esperado contém algo semelhante a:

```text
7 passed
...
cycle=20 det=1 target=yes ... ack=yes
...
Ciclos: 20
...
OK: instalação de teste concluída.
```

Também deve existir:

```text
logs/followbot.log
```

Para repetir só a aplicação mock:

### Windows

```powershell
.\.venv\Scripts\python.exe scripts\run_profile.py mock --max-cycles 20
```

### Ubuntu

```bash
.venv/bin/python scripts/run_profile.py mock --max-cycles 20
```

Também é possível executar via `main.py` diretamente, mas prefira `scripts/run_profile.py` para padronização operacional:

```bash
python -m followbot.main --max-cycles 20
```

quando o virtualenv estiver ativo e você estiver na raiz do projeto.

---

# 4. Diagnóstico rápido do ambiente

Com o `.venv` ativo:

```bash
python scripts/preflight.py
```

Para exigir também a pilha Ultralytics:

```bash
python scripts/preflight.py --require-ai
```

O preflight mostra:

- SO e arquitetura;
- versão/executável do Python;
- presença dos arquivos básicos;
- imports de `numpy`, `pyserial` e opcionalmente `ultralytics`;
- carregamento do `configs/profiles/mock.toml`;
- presença de virtualenv.

---

# 5. Testar ESP/serial sem IA e sem movimento

Primeiro liste as portas.

### Windows

```powershell
.\.venv\Scripts\python.exe scripts\list_serial_ports.py
```

Exemplo de resultado:

```text
COM4    USB Serial Device ...
```

### Ubuntu

```bash
.venv/bin/python scripts/list_serial_ports.py
```

Exemplo:

```text
/dev/ttyACM0    USB ...
```

## Ubuntu: permissão da serial

Veja os grupos atuais:

```bash
groups
```

Se `dialout` não estiver presente:

```bash
sudo usermod -aG dialout "$USER"
```

Depois é necessário encerrar a sessão do usuário e entrar novamente.

Evite rodar a aplicação inteira com `sudo`, pois isso costuma criar novos problemas de ambiente/venv e permissões de log.

## Smoke test serial seguro

O script abaixo envia **somente `v=0` e `w=0`**.

### Windows

```powershell
.\.venv\Scripts\python.exe scripts\serial_smoke_test.py --port COM4
```

### Ubuntu

```bash
.venv/bin/python scripts/serial_smoke_test.py --port /dev/ttyACM0
```

Resultado esperado:

```text
STOP 1/3: {'success': True, ..., 'response': 'ACK,1', ...}
STOP 2/3: {'success': True, ..., 'response': 'ACK,2', ...}
STOP 3/3: {'success': True, ..., 'response': 'ACK,3', ...}
```

Se a primeira tentativa falhar e as seguintes funcionarem, o ESP provavelmente está reiniciando ao abrir a serial. Tente:

```text
--startup-delay 2.5
```

ou aumente `startup_delay_s` na configuração real.

---

# 6. Instalar a IA no PC — somente depois do mock

O teste básico não instala Ultralytics de propósito.

Com o `.venv` ativo, para o runtime de IA:

```bash
python -m pip install --no-build-isolation --prefer-binary -c constraints/test-direct.txt -e '.[ai]'
```

No PowerShell, a mesma ideia:

```powershell
python -m pip install --no-build-isolation --prefer-binary -c constraints\test-direct.txt -e ".[ai]"
```

Depois:

```bash
python scripts/preflight.py --require-ai
```

## Atenção ao tamanho do download

Ultralytics instala uma pilha que pode incluir PyTorch e OpenCV. Isso é muito maior que o projeto base e pode levar tempo mesmo quando tudo está correto.

Se a instalação aparentar “parar”, execute novamente com saída detalhada:

```bash
python -m pip install -v --no-build-isolation --prefer-binary -c constraints/test-direct.txt -e '.[ai]'
```

Assim fica claro qual pacote está sendo baixado/construído.

---

# 7. Exportar YOLO26n para NCNN no PC

A exportação deve ser feita em um computador de desenvolvimento, não como parte do primeiro teste do Raspberry Pi Zero.

Instale as dependências de exportação:

```bash
python -m pip install --no-build-isolation --prefer-binary -c constraints/test-direct.txt -e '.[export]'
```

Então:

```bash
python scripts/export_yolo26_ncnn.py --model yolo26n.pt --imgsz 320
```

A primeira execução pode precisar baixar `yolo26n.pt` e dependências adicionais de exportação.

Depois copie a pasta gerada para:

```text
models/yolo26n_ncnn_model/
```

Antes de copiar para o Raspberry, confirme que a pasta realmente contém os arquivos exportados e não apenas um `.pt`.

---

# 8. Teste no Raspberry Pi real

## Ambiente identificado e forma de trabalho

Em 07/10/2026, o equipamento foi identificado como **Raspberry Pi Zero 2 W**, Ubuntu **24.04.4 LTS**, kernel `6.8.0-1057-raspi`, `aarch64`, Python **3.12.3**, com **409 MiB de RAM visível ao sistema**. O SSH funciona em `juca@192.168.7.2`. O driver identificou o sensor CSI **OV5647**. Foram executados no próprio Pi os 15 testes unitários, 20 ciclos do perfil mock e a captura de um JPEG RGB de 640 × 480 pelo módulo do FollowBot. A detecção YOLO e o movimento real ainda não foram testados nele.

A proposta é editar no **VS Code do Windows**, enviar os arquivos por **SCP** e executar pelo terminal **SSH**. Fotos e logs podem voltar ao PC para inspeção. Isso mantém a memória do Pi disponível para o programa: o Remote-SSH instala VS Code Server no destino e seus [requisitos oficiais](https://code.visualstudio.com/docs/remote/ssh#_system-requirements) exigem ao menos 1 GB de RAM.

## Primeiro: verificar a câmera e a rede existentes

Há uma limitação concreta da imagem atual: a [documentação da Canonical](https://ubuntu.com/hardware/docs/boards/how-to/ubuntu_supported/raspberry-pi/#limitations) informa problemas na stack libcamera anterior ao Ubuntu 25.04. Neste equipamento, o pacote 0.2.0 conseguiu enumerar o sensor, mas abortou a captura em `prepareIsp()`. A preparação específica descrita abaixo resolveu essa falha nos testes locais. Ter arquivos `/dev/video*` ou conseguir listar o sensor não comprova uma captura funcional.

## Configuração de câmera validada neste equipamento

No Pi já preparado, abra uma sessão SSH e execute:

```bash
cd ~/followbot
source scripts/env_camera_ubuntu2404.sh
python -m followbot.camera.picamera2_camera --warmup 3 --output camera.jpg
```

O script ativa o venv e seleciona a biblioteca corrigida somente para essa sessão.
As bibliotecas compiladas ficam em `~/followbot-camera-check/runtime`; os pacotes
do Ubuntu permanecem em seus caminhos originais. A captura não requer `sudo`.
Para obter a imagem no Windows, a partir da pasta do projeto:

```powershell
scp juca@192.168.7.2:~/followbot/camera.jpg .\camera-pi.jpg
```

A combinação testada é **libcamera 0.2.0 com correção + Picamera2 0.3.17**.
Há três ajustes registrados nos arquivos do projeto:

- `scripts/patches/libcamera-0.2.0-followbot.patch`: aplica a [correção aceita no libcamera, commit 0dc737d3](https://patchwork.libcamera.org/patch/19446/), que inicializa o identificador de buffer. Também mantém um aviso do GCC 13 como aviso no programa de comunicação com o IPA, permitindo compilar o código gerado dessa versão.
- `scripts/patches/picamera2-0.3.17-headless.patch`: permite usar `NullPreview` sem o módulo gráfico `pykms`. Pedir uma prévia DRM continua produzindo um erro explícito. Esse ajuste é local; reinstalar Picamera2 remove a alteração e exige reaplicá-la.
- `.venv/lib/python3.12/site-packages/followbot-libcamera.pth`: inclui `/usr/lib/aarch64-linux-gnu/python3.12/site-packages`, onde o pacote Ubuntu colocou os bindings que o Python não encontrava por padrão.

O quadro bruto capturado diretamente por V4L2 chegou quase preto. Após a correção,
o processamento da câmera e o módulo Python produziram uma imagem visível do ambiente.
A foto de verificação foi copiada para `logs/camera_rpi_2026-10-07.jpg` no computador.

### Reproduzir a preparação em uma instalação equivalente

Com os arquivos deste projeto em `~/followbot`, instale as dependências de captura
e compilação. O procedimento é específico de Ubuntu 24.04 arm64/Python 3.12;
Raspberry Pi OS deve usar sua instalação normal de Picamera2 pelo apt.

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends \
  libcamera-tools libcamera-ipa python3-libcamera v4l-utils \
  python3.12-venv python3-prctl python3-piexif \
  g++ pkg-config patch curl meson ninja-build libyaml-dev libevent-dev libgnutls28-dev \
  python3-yaml python3-ply python3-jinja2

cd ~/followbot
mkdir -p ~/followbot-camera-check
curl -fL https://codeload.github.com/raspberrypi/libcamera/tar.gz/refs/tags/v0.2.0 \
  -o ~/followbot-camera-check/libcamera-v0.2.0.tar.gz
tar -xzf ~/followbot-camera-check/libcamera-v0.2.0.tar.gz -C ~/followbot-camera-check
patch -p1 -d ~/followbot-camera-check/libcamera-0.2.0 \
  < scripts/patches/libcamera-0.2.0-followbot.patch

meson setup ~/followbot-camera-check/libcamera-0.2.0/build \
  ~/followbot-camera-check/libcamera-0.2.0 \
  --prefix="$HOME/followbot-camera-check/runtime" --buildtype=release \
  -Doptimization=2 -Db_lto=false -Dpipelines=rpi/vc4 -Dipas=rpi/vc4 \
  -Dcam=enabled -Dqcam=disabled -Dgstreamer=disabled -Dtest=false \
  -Ddocumentation=disabled -Dpycamera=disabled -Dv4l2=false -Dlc-compliance=disabled
ninja -C ~/followbot-camera-check/libcamera-0.2.0/build -j1
meson install -C ~/followbot-camera-check/libcamera-0.2.0/build --no-rebuild

python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install 'picamera2==0.3.17'
printf '%s\n' /usr/lib/aarch64-linux-gnu/python3.12/site-packages \
  > .venv/lib/python3.12/site-packages/followbot-libcamera.pth
patch -p1 -d .venv/lib/python3.12/site-packages \
  < scripts/patches/picamera2-0.3.17-headless.patch
.venv/bin/python -m pip install -e .
source scripts/env_camera_ubuntu2404.sh
python -m followbot.camera.picamera2_camera --warmup 3 --output camera.jpg
```

A compilação no Zero 2 W foi lenta e precisou de 512 MiB de swap temporário,
desativado e removido ao concluir a preparação. Uma nova captura pelo módulo passou
com swap em zero (`capture-no-swap.log`). Esse recurso foi usado para preparar as bibliotecas; não é uma medição de memória
do futuro sistema com YOLO. Os registros da sessão estão em
`~/followbot-camera-check/`, incluindo `cam.log` (falha original),
`build-resume.log`, `python-capture.log`, `tests.log` e `mock.log`.

### Consultas para diagnóstico

No terminal SSH do Pi, execute estas consultas:

```bash
getent hosts ports.ubuntu.com
command -v rpicam-hello libcamera-hello cam
python3 -c "import importlib.util; print({m: importlib.util.find_spec(m) is not None for m in ('picamera2', 'libcamera', 'PIL', 'numpy', 'serial')})"
apt-cache policy python3-picamera2 python3-libcamera libcamera-tools rpicam-apps
for f in /sys/class/video4linux/video*/name; do printf '%s: ' "$f"; cat "$f"; done
```

O primeiro comando deve retornar endereços para o domínio. Em 07/10/2026, a resolução DNS, uma requisição HTTPS ao servidor Ubuntu e os downloads de pacotes funcionaram pela conexão USB/NAT. Se essa consulta falhar em outra sessão, verificar a rede antes de instalar dependências.

Use a ferramenta de câmera que estiver presente:

```bash
# Se existir rpicam-hello:
rpicam-hello --list-cameras

# Se existir somente libcamera-hello:
libcamera-hello --list-cameras

# Se existir cam:
cam -l
```

Se os módulos Python estiverem disponíveis, confirme também se conseguem importar e enumerar câmeras:

```bash
python3 -c "import libcamera; from picamera2 import Picamera2; print(Picamera2.global_camera_info())"
```

Uma lista vazia ou erro de importação precisa ser investigado antes da captura. Não usar `pip install picamera2` como correção automática: a biblioteca depende dos bindings e da stack libcamera do sistema. O [projeto Picamera2](https://github.com/raspberrypi/picamera2#installation) recomenda o conjunto compatível instalado pelo apt no Raspberry Pi OS; isso não é uma receita garantida para este Ubuntu 24.04. Este procedimento não troca o sistema operacional.

## Transferir uma cópia pequena do projeto

No **PowerShell do Windows**, entre na pasta que contém `pyproject.toml` deste projeto e execute:

```powershell
ssh juca@192.168.7.2 'mkdir -p ~/followbot'
scp .\pyproject.toml .\config.mock.toml juca@192.168.7.2:~/followbot/
scp -r .\src .\configs .\scripts .\tests juca@192.168.7.2:~/followbot/
```

Esses comandos também servem para reenviar alterações. Eles copiam apenas as pastas indicadas; não copiam `.venv`, a documentação LaTeX, logs ou modelos duplicados. O ambiente Python deve ser criado no Pi, pois executáveis e dependências instalados no PC podem pertencer a outra arquitetura. Execute os comandos seguintes dentro de `~/followbot`.

## Ambiente mínimo e teste mock

Depois de verificar a stack de câmera e confirmar a disponibilidade de `venv` e dos pacotes necessários, crie um ambiente novo que consiga acessar os bindings do sistema:

```bash
cd ~/followbot
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -e .
.venv/bin/python scripts/preflight.py
.venv/bin/python scripts/run_profile.py mock --max-cycles 20
```

O [manual Picamera2, seção sobre ambientes virtuais](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf), orienta `--system-site-packages` porque os bindings libcamera vêm do sistema. Se já existir um venv nesse destino, verificar como foi criado antes de reutilizá-lo. O mock permite verificar o núcleo do programa sem câmera nem IA; passar nele não valida a câmera.

Não usar `setup_test_ubuntu.sh` como instalador de câmera: ele cria um venv isolado, instala ferramentas de teste e limpa logs de execuções anteriores. A instalação mínima acima não instala Ultralytics.

## Capturar uma foto pelo próprio módulo

Com Picamera2/libcamera funcionais no ambiente, confirme também `Pillow`, usado somente para salvar JPG/PNG neste comando:

```bash
.venv/bin/python -c "import libcamera; from picamera2 import Picamera2; from PIL import Image; print(Picamera2.global_camera_info())"
.venv/bin/python -m followbot.camera.picamera2_camera --output camera.jpg --width 640 --height 480 --warmup 1
```

O módulo contém `if __name__ == "__main__"` e pode ser executado com `python -m`. Ele abre a câmera, captura uma imagem, salva o arquivo e fecha o dispositivo; não abre janela gráfica, detector nem serial. Se faltar apenas `Pillow`, providenciar esse pacote no ambiente antes de repetir a captura.

Para ver a imagem no Windows, execute no PowerShell:

```powershell
scp juca@192.168.7.2:~/followbot/camera.jpg .\camera-pi.jpg
```

Abra `camera-pi.jpg` no VS Code e verifique enquadramento, foco, iluminação e cores. Este teste não requer ESP conectado.

## Depois: inferência com comunicação simulada

O perfil **`rpi_vision`** usa câmera Picamera2, detector Ultralytics com NCNN e comunicação **mock**. A gravação visual contínua começa desativada. O perfil antigo **`rpi`** usa serial real e deve ficar para a etapa de integração.

Antes de executar `rpi_vision`, validar a viabilidade da pilha de IA no Pi: o adaptador atual usa Ultralytics, cujas [dependências da versão 8.4.108](https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.108/pyproject.toml) incluem Torch, Torchvision e OpenCV mesmo quando o modelo é NCNN. Não há garantia de que o conjunto caiba confortavelmente na RAM disponível. Um adaptador NCNN direto pode ser avaliado depois, com validação de pré e pós-processamento.

Exportar o modelo no PC, conforme a seção 7. Quando for a hora de testar a IA, enviar a pasta já exportada pelo PowerShell:

```powershell
ssh juca@192.168.7.2 'mkdir -p ~/followbot/models'
scp -r .\models\yolo26n_ncnn_model juca@192.168.7.2:~/followbot/models/
```

Somente após preparar e verificar as dependências de IA no Pi:

```bash
cd ~/followbot
.venv/bin/python scripts/preflight.py --require-ai --require-model
.venv/bin/python scripts/run_profile.py rpi_vision --max-cycles 20 --limit-threads 1
```

Esse teste permite observar detecções, tempos e comandos calculados sem enviá-los ao ESP. O preflight verifica presença de módulos/arquivos; o teste real é que confirma funcionamento e consumo de memória. `--limit-threads` limita variáveis OMP/BLAS/NumExpr, mas não comprova o número de threads interno do NCNN. O `cycle_total` atual também não inclui toda a gravação de logs/imagens; não o tratar como medida completa da frequência do robô.

A sequência fica: **mock → foto → inferência com comunicação mock → serial com STOP → integração de movimento**. Antes da última etapa, implementar e verificar `applyVelocityReference()` no firmware, a parada e o watchdog. Se o ESP for conectado por USB, considerar que a porta de dados do Zero 2 W está atualmente ocupada pela rede USB com o PC; planejar acesso por Wi-Fi ou outra ligação apropriada ao ESP.

---

# 9. Problemas prováveis e solução rápida

## `ModuleNotFoundError: tomllib`

Python antigo. Verifique:

```bash
python --version
```

Use Python 3.11+.

## `No module named venv` / `ensurepip is not available`

Ubuntu:

```bash
sudo apt install python3-venv
```

ou o pacote específico, por exemplo:

```bash
sudo apt install python3.11-venv
```

## `Permission denied: /dev/ttyACM0`

Adicione o usuário a `dialout` e faça login novamente.

## `could not open port COMx`

- confirme a porta com `scripts/list_serial_ports.py`;
- desconecte/reconecte o ESP;
- feche Serial Monitor/Arduino IDE/PlatformIO que possa estar segurando a porta;
- confirme o driver USB da placa.

## `Picamera2 não está disponível`

Em PC Windows/Ubuntu comum isso é esperado com a arquitetura atual. No Raspberry Pi OS, instale via `apt` e use `--system-site-packages`.

## modelo YOLO não encontrado

Execute a partir da raiz do projeto e confira:

```text
models/yolo26n_ncnn_model/
```

O projeto ainda resolve `model_path` relativamente ao diretório atual.

## primeiro ACK falha

A placa pode reiniciar quando a porta abre. Aumente `startup_delay_s`.

## instalação Ultralytics muito lenta

Não é necessária para o teste mock. Termine primeiro o fluxo mínimo. Depois instale IA separadamente com `-v` se precisar diagnosticar downloads/builds.

---

# 10. Melhorias de código recomendadas para uma próxima revisão

Estas não impedem o mock de funcionar, mas aumentariam robustez:

1. Resolver caminhos relativos ao diretório do arquivo de configuração ou à raiz do projeto, não ao CWD.
2. Validar e calibrar a webcam real em múltiplas resoluções (por exemplo 640x480 e 1280x720) para reduzir jitter de bbox.
3. Criar testes unitários para `config`, logger e orquestrador/STOP de segurança.
4. Permitir injeção da implementação serial para testar timeout/ACK sem hardware físico.
5. Validar valores numéricos da configuração (`NaN`, limites negativos, deadbands etc.).
6. Registrar versão do Python e pacotes no início do log de benchmark.
7. Criar um lock completo da pilha de IA quando a combinação final de Python/Ultralytics/PyTorch/NCNN for aprovada no hardware alvo.
8. Implementar `applyVelocityReference()` no ESP antes de considerar o teste de movimento completo.

---

# 11. Arquivos adicionados nesta cópia auditada

```text
INSTALL_TEST.md
constraints/test-direct.txt
scripts/preflight.py
scripts/prepare_yolo_model.py
scripts/run_profile.py
scripts/list_video_devices.py
scripts/setup_test_windows.ps1
scripts/setup_test_ubuntu.sh
scripts/list_serial_ports.py
scripts/serial_smoke_test.py
configs/profiles/mock.toml
configs/profiles/webcam.toml
configs/profiles/synthetic_ultralytics.toml
configs/profiles/rpi.example.toml
docs/PROJECT_MAP.md
docs/INDEX.md
docs/TESTING_PLAYBOOK.md
```

Também foram feitas duas mudanças pequenas:

- o `main.py` agora usa `config.mock.toml` por padrão para evitar tentar abrir hardware por acidente em PC;
- `pyproject.toml` ganhou o extra `export` e o comando de console `followbot`.
