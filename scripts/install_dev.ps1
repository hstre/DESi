# DESi dev install (Windows PowerShell). Offline-safe.
#
# Does ONLY: create a venv, upgrade pip, `pip install -e .`, then
# `desi doctor`. It never asks for or stores any API key, and pulls
# nothing beyond declared pip dependencies.
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "DESi dev install (Windows)"
python --version

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e .

Write-Host ""
desi doctor
