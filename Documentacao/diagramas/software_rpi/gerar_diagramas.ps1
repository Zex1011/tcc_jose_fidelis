[CmdletBinding()]
param(
    [switch]$PrepararFerramenta,
    [string]$Java = 'java'
)

$ErrorActionPreference = 'Stop'
$versaoPlantUml = '1.2026.5'
$nomeJar = "plantuml-java8-$versaoPlantUml.jar"
$pastaFerramentas = Join-Path (Split-Path -Parent $PSScriptRoot) '.tools'
$arquivoJar = Join-Path $pastaFerramentas $nomeJar
$hashEsperado = '547674a4b16833e786a2fcf3a6b5b965a8c5910c9cfd5abb290c36e8bf040c1d'

Get-Command $Java -ErrorAction Stop | Out-Null
if (-not (Test-Path -LiteralPath $arquivoJar)) {
    if (-not $PrepararFerramenta) {
        throw 'PlantUML ausente. Execute novamente com -PrepararFerramenta para baixar a ferramenta oficial.'
    }
    New-Item -ItemType Directory -Path $pastaFerramentas -Force | Out-Null
    $uriJar = "https://github.com/plantuml/plantuml/releases/download/v$versaoPlantUml/$nomeJar"
    Invoke-WebRequest -UseBasicParsing -Uri $uriJar -OutFile $arquivoJar
}

$hashObtido = (Get-FileHash -LiteralPath $arquivoJar -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hashObtido -ne $hashEsperado) {
    throw 'O hash do PlantUML difere do SHA-256 publicado na distribuicao oficial.'
}

$fontes = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.puml' | Sort-Object Name | ForEach-Object { $_.FullName })
if ($fontes.Count -eq 0) { throw 'Nenhuma fonte .puml encontrada.' }
New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot 'renderizados') -Force | Out-Null
$argumentosJava = @('-Djava.awt.headless=true', '-DPLANTUML_LIMIT_SIZE=8192', '-jar', $arquivoJar, '-charset', 'UTF-8')

& $Java @argumentosJava '-checkonly' @fontes
if ($LASTEXITCODE -ne 0) { throw 'Falha na validacao da sintaxe PlantUML.' }

foreach ($formato in @('svg', 'png')) {
    & $Java @argumentosJava '-failfast2' "-t$formato" '-o' 'renderizados' @fontes
    if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar $formato." }
}

foreach ($fonte in $fontes) {
    foreach ($formato in @('svg', 'png')) {
        $imagem = Join-Path $PSScriptRoot ("renderizados\{0}.{1}" -f [IO.Path]::GetFileNameWithoutExtension($fonte), $formato)
        if (-not (Test-Path -LiteralPath $imagem)) { throw "Imagem esperada nao foi gerada: $imagem" }
    }
}
Write-Output ("Gerados {0} diagramas em SVG e PNG: {1}" -f $fontes.Count, (Join-Path $PSScriptRoot 'renderizados'))
