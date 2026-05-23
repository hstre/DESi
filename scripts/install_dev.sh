#!/usr/bin/env bash
# DESi dev install (macOS / Linux). Offline-safe.
#
# Does ONLY: create a venv, upgrade pip, `pip install -e .`, then
# `desi doctor`. It never asks for or stores any API key, and pulls
# nothing beyond declared pip dependencies.
set -euo pipefail

cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
echo "DESi dev install — using: $PY"
"$PY" --version

if [ ! -d ".venv" ]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e .

echo
desi doctor
