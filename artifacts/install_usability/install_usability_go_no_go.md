# DESi Install-Usability - Go/No-Go

**Result:** `GO`

Goal: make DESi easy to install and test for non-Python users, without leaking secrets, enabling live calls silently, or touching any replay/governance invariant. Offline is the default; live LLM calls require an explicit two-flag opt-in.

| Check | Result |
|---|---|
| install docs created | yes |
| dummy install path works | yes |
| config loader works | yes |
| secrets protected | yes |
| offline default preserved | yes |
| replay invariants touched | no |
| governance invariants touched | no |

## What was added

- `INSTALL.md`, `INSTALL_DUMMIES.md`, `QUICKSTART.md`, `docs/ELI5_DESi.md` (beginner docs, Windows + macOS/Linux).
- `config/desi.example.ini` (committed, keyless) + a gitignored `config/desi.local.ini` slot; `desi.runtime_config` loader (offline default, ENV override, no secret logging).
- `desi config` and `desi doctor` CLI subcommands (offline-safe; never print key values).
- `examples/hello_desi.py` (runs with no API key).
- `scripts/install_dev.sh` / `.ps1` (venv + pip install -e . + doctor; no key prompts, no hidden downloads).

## Invariants

Replay drift = 0 (artifacts byte-identical), determinism scanner clean, core_identity = 1.0, governance intact. No replay artifact was overwritten and no hidden state or silent live-call path was introduced. If usability and replay-governance ever conflict, replay-governance wins.
