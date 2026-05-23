# Installing DESi

> New to Python? Read **[INSTALL_DUMMIES.md](INSTALL_DUMMIES.md)** instead —
> it explains every step. This page is the concise reference.

DESi (`desi-governance`) is an **experimental, alpha** package
(`0.1.0a0`). It runs **fully offline by default**; no API key is
required to install or test it.

## Requirements

- Python **>= 3.11**
- pip

## Install

```bash
git clone https://github.com/hstre/DESi.git
cd DESi
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e .
```

Optional extras:

```bash
pip install -e ".[test]"    # pytest, to run the test suite
pip install -e ".[tools]"   # sympy, for the symbolic tool sandbox
pip install -e ".[neo4j]"   # optional Neo4j projection
```

## Verify

```bash
desi doctor        # environment readiness check (offline-safe)
desi config        # show providers + offline/live mode (no secrets)
desi replay        # replay-stability + determinism smoke test
python examples/hello_desi.py
```

## Configuration (optional — only for live LLM calls)

DESi is offline by default. To enable real LLM calls (e.g. via
OpenRouter), copy the example config to a **local, gitignored** file:

```bash
cp config/desi.example.ini config/desi.local.ini
```

Edit `config/desi.local.ini`:

```ini
[openrouter]
api_key = sk-or-...        # your key (this file is gitignored)

[desi]
offline_mode = false
allow_live_llm_calls = true
```

Rules:

- **Never** put a real key in `config/desi.example.ini` (it is committed).
- `config/desi.local.ini`, `.env`, `*.key`, and `secrets/` are gitignored.
- Environment variables override the INI, e.g. `OPENROUTER_API_KEY`,
  `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DESI_OFFLINE_MODE`,
  `DESI_ALLOW_LIVE_LLM_CALLS`.
- If no key is set anywhere, DESi stays offline. Live calls happen
  **only** when `allow_live_llm_calls = true` and `offline_mode = false`.
- API key **values** are never printed by the CLI and never written to
  artifacts.

## One-line dev setup (optional)

```bash
# macOS / Linux
bash scripts/install_dev.sh
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts/install_dev.ps1
```

These only create a venv, upgrade pip, run `pip install -e .`, and run
`desi doctor`. They never ask for or store secrets.

## Uninstall

```bash
pip uninstall desi-governance
```
