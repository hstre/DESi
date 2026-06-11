"""Benchmark runner: cases -> turns -> responses -> metrics.

The model sits behind a chat seam (``messages -> text``) like the GSM
solver seam, so the whole pipeline runs offline with ``ScriptedChat`` and
the tests never need a network. ``build_openrouter_chat`` is the live
swap-in (OpenRouter, OPENROUTER_API_KEY) for real runs — the pilot's model
family (Llama-3.1-8B-Instruct) is the default.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .metrics import comparison_summary, score_run
from .prompts import baseline_turns, hygiene_turns, system_prompt

Chat = Callable[[list[dict]], str]

DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"
MODES = ("baseline", "desi_hygiene")


@dataclass
class Case:
    case_id: str
    raw_text: str
    path: str = ""


@dataclass
class ScriptedChat:
    """Offline deterministic chat: returns injected responses in order.

    What you inject is what you get — it answers nothing, so it can never
    smuggle a real result into an offline run.
    """

    responses: list[str] = field(default_factory=list)
    default: str = ""
    calls: list[list[dict]] = field(default_factory=list)

    def __call__(self, messages: list[dict]) -> str:
        # snapshot — the runner keeps mutating the live list after this call
        self.calls.append([dict(m) for m in messages])
        idx = len(self.calls) - 1
        return self.responses[idx] if idx < len(self.responses) else self.default


def load_cases(data_dir: str | Path, pattern: str = "advText*.txt") -> list[Case]:
    """Load Jacoby-style adversarial context files from a directory.

    The upstream dataset (GPL-3.0) is fetched at runtime — see the README —
    and is deliberately NOT vendored into this (MIT) repository.
    """
    root = Path(data_dir)
    cases = [
        Case(case_id=p.stem, raw_text=p.read_text(encoding="utf-8"), path=str(p))
        for p in sorted(root.glob(pattern))
    ]
    if not cases:
        raise FileNotFoundError(
            f"no adversarial context files matching {pattern!r} in {root} — "
            "fetch the dataset first (see context_contamination/README.md)"
        )
    return cases


def run_case(chat: Chat, case: Case, mode: str, persona: str = "neutral",
             max_chars: int = 8000, protocol: str = "standard",
             density: int = 5, ledger=None) -> dict:
    """Drive one case through one arm; returns responses + metrics.

    ``max_chars`` truncates the raw source (the pilot worked with 2k/8k
    token slices, not whole files); applied before either arm so both see
    the same source slice. ``protocol`` selects the turn sequence
    ("standard" 4-turn or "extended" multi-turn pressure form); ``density``
    the hygiene-state structure level (ignored by the baseline arm).

    When a ``ledger`` is supplied (any object with the local-Layer-9
    ``record(kind, payload, ...)`` shape, e.g. ``desi_router.ledger.Ledger``),
    the run is appended as a ``context_contamination`` event — slim metrics
    plus a sha256 over the responses — so the Reviewer Port / ledger CLI can
    show what happened without storing the transcripts themselves.
    """
    import hashlib
    import json as _json

    raw = case.raw_text[:max_chars]
    if mode == "baseline":
        turns = baseline_turns(raw, persona=persona, protocol=protocol)
    else:
        turns = hygiene_turns(raw, persona=persona, protocol=protocol,
                              density=density)

    messages: list[dict] = [{"role": "system", "content": system_prompt()}]
    responses: list[str] = []
    for user_turn in turns:
        messages.append({"role": "user", "content": user_turn})
        reply = chat(messages)
        messages.append({"role": "assistant", "content": reply})
        responses.append(reply)

    metrics = score_run(responses)
    result = {
        "case_id": case.case_id,
        "mode": mode,
        "persona": persona,
        "protocol": protocol,
        "density": density,
        "responses": responses,
        "metrics": metrics,
    }
    if ledger is not None:
        ledger.record(
            "context_contamination",
            {
                "task_class": "context_contamination",
                "case_id": case.case_id,
                "arm": mode,
                "persona": persona,
                "protocol": protocol,
                "density": density,
                "attribution_failures": metrics["attribution_failures"],
                "register_drift": metrics["register_drift"],
                "framing_leakage": metrics["framing_leakage"],
                "role_adoption": metrics["role_adoption"],
                "loop_detected": metrics["loop_detected"],
                "responses_sha256": hashlib.sha256(
                    _json.dumps(responses, ensure_ascii=False).encode("utf-8")
                ).hexdigest(),
            },
        )
    return result


def run_benchmark(cases: list[Case], chat: Chat, persona: str = "neutral",
                  max_chars: int = 8000, protocol: str = "standard",
                  density: int = 5, ledger=None) -> dict:
    """Both arms over all cases + per-case comparison summaries."""
    runs = {
        mode: {
            c.case_id: run_case(chat, c, mode, persona, max_chars, protocol,
                                density, ledger)
            for c in cases
        }
        for mode in MODES
    }
    comparisons = [
        comparison_summary(
            c.case_id,
            runs["baseline"][c.case_id]["metrics"],
            runs["desi_hygiene"][c.case_id]["metrics"],
        )
        for c in cases
    ]
    return {"persona": persona, "protocol": protocol, "density": density,
            "runs": runs, "comparisons": comparisons}


_VARIANCE_METRICS = (
    "attribution_failures",
    "register_drift",
    "framing_leakage",
    "role_adoption",
)


def _summarize_repeats(values: list[float]) -> dict:
    """mean / min / max / sample-stdev for one metric across repeats."""
    n = len(values)
    mean = sum(values) / n if n else 0.0
    if n > 1:
        var = sum((v - mean) ** 2 for v in values) / (n - 1)
        stdev = var ** 0.5
    else:
        stdev = 0.0
    return {
        "mean": round(mean, 4),
        "stdev": round(stdev, 4),
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
        "values": values,
    }


def run_benchmark_repeated(cases: list[Case], chat: Chat, persona: str = "neutral",
                           max_chars: int = 8000, protocol: str = "standard",
                           repeats: int = 1, density: int = 5, ledger=None) -> dict:
    """Run the benchmark ``repeats`` times and estimate variance per metric.

    Provider sampling is not seedable even at temperature 0, so repeats are the
    only honest way to separate a real arm difference from run-to-run jitter.
    Per (arm, case, metric) this reports mean ± stdev and the raw values; with
    repeats=1 it degrades to a single run plus the per-repeat report list.
    """
    per_repeat = [
        run_benchmark(cases, chat, persona, max_chars, protocol, density, ledger)
        for _ in range(max(1, repeats))
    ]

    variance: dict[str, dict] = {}
    for mode in MODES:
        variance[mode] = {}
        for case in cases:
            cid = case.case_id
            variance[mode][cid] = {
                metric: _summarize_repeats(
                    [rep["runs"][mode][cid]["metrics"][metric] for rep in per_repeat]
                )
                for metric in _VARIANCE_METRICS
            }
    return {
        "persona": persona,
        "protocol": protocol,
        "density": density,
        "repeats": max(1, repeats),
        "variance": variance,
        "reports": per_repeat,
    }


def run_density_sweep(cases: list[Case], chat: Chat, persona: str = "neutral",
                      max_chars: int = 8000, protocol: str = "standard",
                      densities: tuple[int, ...] | None = None,
                      repeats: int = 1, ledger=None) -> dict:
    """Sweep the hygiene-state density ("k") against a shared baseline.

    The model-profiling step for this task family: per repeat, the baseline
    arm runs ONCE and every density level runs only the hygiene arm against
    it — so the per-density comparisons differ exactly in the state density,
    and the sweep costs (1 + len(densities)) case-runs per repeat instead of
    2 × len(densities).
    """
    from .hygiene import DENSITY_LEVELS

    ks = tuple(densities) if densities else DENSITY_LEVELS
    for k in ks:
        if k not in DENSITY_LEVELS:
            raise ValueError(f"unknown density {k!r}; choose from {DENSITY_LEVELS}")

    sweeps: dict[int, list[dict]] = {k: [] for k in ks}
    baselines: list[dict] = []
    for _ in range(max(1, repeats)):
        base = {
            c.case_id: run_case(chat, c, "baseline", persona, max_chars,
                                protocol, ledger=ledger)
            for c in cases
        }
        baselines.append(base)
        for k in ks:
            hyg = {
                c.case_id: run_case(chat, c, "desi_hygiene", persona, max_chars,
                                    protocol, density=k, ledger=ledger)
                for c in cases
            }
            sweeps[k].append({
                "runs": hyg,
                "comparisons": [
                    comparison_summary(c.case_id, base[c.case_id]["metrics"],
                                       hyg[c.case_id]["metrics"])
                    for c in cases
                ],
            })

    # per density: variance summary of the hygiene arm across repeats
    profile: dict[int, dict] = {}
    for k in ks:
        profile[k] = {
            c.case_id: {
                metric: _summarize_repeats(
                    [rep["runs"][c.case_id]["metrics"][metric]
                     for rep in sweeps[k]]
                )
                for metric in _VARIANCE_METRICS
            }
            for c in cases
        }
    baseline_profile = {
        c.case_id: {
            metric: _summarize_repeats(
                [b[c.case_id]["metrics"][metric] for b in baselines]
            )
            for metric in _VARIANCE_METRICS
        }
        for c in cases
    }
    return {
        "persona": persona,
        "protocol": protocol,
        "densities": list(ks),
        "repeats": max(1, repeats),
        "baseline": baseline_profile,
        "by_density": profile,
        "sweeps": sweeps,
        "baseline_runs": baselines,
    }


def build_openrouter_chat(model: str = DEFAULT_MODEL, *, api_key: str | None = None,
                          timeout: int = 120, retries: int = 2) -> Chat:
    """Live chat via OpenRouter (OpenAI-compatible). Needs OPENROUTER_API_KEY.

    temperature=0 for as much replay stability as the provider allows. Raises
    RuntimeError when no key is configured, so the CLI can report the live
    path as unavailable cleanly.
    """
    import os

    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "No OPENROUTER_API_KEY configured — live mode unavailable. "
            "Use --dry-run with fixture responses instead."
        )

    def chat(messages: list[dict]) -> str:
        body = json.dumps(
            {"model": model, "messages": messages, "temperature": 0, "max_tokens": 700}
        ).encode()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/hstre/DESi",
                "X-Title": "DESi context-contamination benchmark",
            },
        )
        last = ""
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    d = json.loads(r.read())
                return d["choices"][0]["message"]["content"] or ""
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}"
                if e.code in (400, 401, 403, 404):
                    break
            except Exception as e:  # transient network failure -> retry
                last = f"{type(e).__name__}: {str(e)[:200]}"
            if attempt + 1 < retries:
                time.sleep(2**attempt)
        raise RuntimeError(f"OpenRouter call failed: {last}")

    return chat
