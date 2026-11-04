param(
    [int]$Cycles = 20
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

function Test-PythonVersion {
    param([string]$Command, [string[]]$PrefixArgs = @())
    try {
        & $Command @PrefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

$PythonCommand = $null
$PythonPrefix = @()

if (Get-Command py -ErrorAction SilentlyContinue) {
    if (Test-PythonVersion -Command "py" -PrefixArgs @("-3.12")) {
        $PythonCommand = "py"
        $PythonPrefix = @("-3.12")
    } elseif (Test-PythonVersion -Command "py" -PrefixArgs @("-3.11")) {
        $PythonCommand = "py"
        $PythonPrefix = @("-3.11")
    }
}

if (-not $PythonCommand -and (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Test-PythonVersion -Command "python") {
        $PythonCommand = "python"
    }
}

if (-not $PythonCommand) {
    Write-Host "ERRO: Python 3.11+ não encontrado." -ForegroundColor Red
    Write-Host "No Windows 10/11 atual, instale o Python Install Manager e o Python 3.12, por exemplo:"
    Write-Host "  winget install 9NQ7512CXL7T"
    Write-Host "  py install 3.12"
    exit 2
}

Write-Host "[1/6] Python selecionado"
& $PythonCommand @PythonPrefix --version
if ($LASTEXITCODE -ne 0) { throw "Falha ao executar Python." }

Write-Host "[2/6] Criando/reutilizando .venv"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    & $VenvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Virtualenv existente usa Python antigo; recriando .venv."
        Remove-Item -Recurse -Force (Join-Path $Root ".venv")
    }
}
if (-not (Test-Path $VenvPython)) {
    & $PythonCommand @PythonPrefix -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Falha ao criar .venv." }
}
if (-not (Test-Path $VenvPython)) {
    throw "A criação do virtualenv falhou."
}

Write-Host "[3/6] Atualizando ferramentas de empacotamento"
& $VenvPython -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar pip/setuptools/wheel." }

Write-Host "[4/6] Instalando FollowBot + dependências de teste (SEM Ultralytics)"
& $VenvPython -m pip install --no-build-isolation --prefer-binary -c constraints\test-direct.txt -e ".[dev]"
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências do FollowBot." }

Write-Host "[5/6] Preflight e testes unitários"
& $VenvPython scripts\preflight.py
if ($LASTEXITCODE -ne 0) { throw "Preflight falhou." }
& $VenvPython -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Testes unitários falharam." }

Write-Host "[6/6] Smoke test mock ($Cycles ciclos)"
Get-ChildItem -Path logs -Filter "followbot.log*" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
& $VenvPython -m followbot.main --config config.mock.toml --max-cycles $Cycles
if ($LASTEXITCODE -ne 0) { throw "Smoke test mock falhou." }
& $VenvPython scripts\summarize_logs.py logs\followbot.log
if ($LASTEXITCODE -ne 0) { throw "Falha ao resumir logs." }

Write-Host ""
Write-Host "OK: instalação de teste concluída." -ForegroundColor Green
Write-Host "Para repetir apenas o mock:"
Write-Host "  .\.venv\Scripts\python.exe -m followbot.main --config config.mock.toml --max-cycles 20"
