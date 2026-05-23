# DESi Quickstart

Five minutes, no API key, fully offline.

## 1. Install

```bash
git clone https://github.com/hstre/DESi.git
cd DESi
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
```

(Full guide: [INSTALL_DUMMIES.md](INSTALL_DUMMIES.md). What DESi is, in
plain words: [docs/ELI5_DESi.md](docs/ELI5_DESi.md).)

## 2. Check your setup

```bash
desi doctor
```

Expected: a checklist ending in `DESi is ready for offline use.`

## 3. The CLI (all offline, all read-only)

```bash
desi config       # which providers are configured; offline/live mode (no secrets)
desi replay       # replay-stability + determinism smoke test
desi audit        # internal documentation overreach audit
desi review       # role-based skeptical reviewer summary
desi benchmark    # external benchmark verdict summary
```

## 4. Run an example

```bash
python examples/hello_desi.py
```

Other minimal examples in `examples/`:

```bash
python examples/replay_example.py
python examples/concept_gate_example.py
python examples/reviewer_port_example.py
```

## 5. Use it from Python

```python
from desi.core import replay_kernel
from desi.gates import concept_gate
from desi.reviewer import reviewer_port

print(replay_kernel.replay_hash({"claim": "x", "evidence": ["y"]}))
print("gate passes:", concept_gate.passes_all(
    concept_gate.phase_gate("external_benchmarks")))
```

## Notes

- DESi is **experimental** (`0.1.0a0`). Treat results as exploratory.
- DESi runs **offline by default**. Live LLM calls require an explicit
  opt-in — see [INSTALL.md](INSTALL.md#configuration-optional--only-for-live-llm-calls).
- DESi does not replace ChatGPT/Claude/DeepSeek; it governs and records
  how statements are formed. See [docs/ELI5_DESi.md](docs/ELI5_DESi.md).
