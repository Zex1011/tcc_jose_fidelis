#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CYCLES="${FOLLOWBOT_TEST_CYCLES:-20}"

python_is_supported() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1
}

choose_python() {
  local candidates=(python3.12 python3.11 python3)
  local exe
  for exe in "${candidates[@]}"; do
    if command -v "$exe" >/dev/null 2>&1 && python_is_supported "$exe"; then
      printf '%s' "$exe"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(choose_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  cat >&2 <<'EOF'
ERRO: Python 3.11+ não encontrado.

Ubuntu 24.04 LTS:
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip

Ubuntu 22.04 LTS:
  sudo apt update
  sudo apt install -y python3.11 python3.11-venv

Depois execute este script novamente.
EOF
  exit 2
fi

echo "[1/6] Python selecionado: $($PYTHON_BIN --version 2>&1) ($PYTHON_BIN)"

echo "[2/6] Criando/reutilizando .venv"
if [[ -x .venv/bin/python ]] && ! python_is_supported .venv/bin/python; then
  echo "Virtualenv existente usa Python antigo; recriando .venv."
  rm -rf .venv
fi
if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON_BIN" -m venv --copies .venv || {
    echo >&2 "Falha ao criar venv. Instale o pacote de venv correspondente ao Python escolhido."
    exit 3
  }
fi

VENV_PY="$ROOT/.venv/bin/python"

echo "[3/6] Atualizando ferramentas de empacotamento"
"$VENV_PY" -m pip install --upgrade pip setuptools wheel

echo "[4/6] Instalando FollowBot + dependências de teste (SEM Ultralytics)"
"$VENV_PY" -m pip install --no-build-isolation --prefer-binary -c constraints/test-direct.txt -e '.[dev]'

echo "[5/6] Preflight e testes unitários"
"$VENV_PY" scripts/preflight.py
"$VENV_PY" -m pytest -q

echo "[6/6] Smoke test mock ($CYCLES ciclos)"
rm -f logs/followbot.log logs/followbot.log.1 logs/followbot.log.2 logs/followbot.log.3
"$VENV_PY" -m followbot.main --config config.mock.toml --max-cycles "$CYCLES"
"$VENV_PY" scripts/summarize_logs.py logs/followbot.log

echo
echo "OK: instalação de teste concluída."
echo "Para repetir apenas o mock:"
echo "  .venv/bin/python -m followbot.main --config config.mock.toml --max-cycles 20"
