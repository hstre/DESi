"""Benchmark runner: cases -> turns -> responses -> metrics.

The model sits behind a chat seam (``messages -> text``) like the GSM
solver seam, so the whole pipeline runs offline with ``ScriptedChat`` and
the tests never need a network. ``build_openrouter_chat`` is the live
swap-in (OpenRouter, OPENROUTER_API_KEY) for real runs — the pilot's model
family (Llama-3.1-8B-Instruct) is the default.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .markers import FRAMEWORK_TERMS
from .metrics import comparison_summary, score_run
from .prompts import baseline_turns, hygiene_turns, review_messages, system_prompt

Chat = Callable[[list[dict]], str]

DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"
DEFAULT_MAX_TOKENS = 700
MODES = ("baseline", "desi_hygiene")


def sampling_config(model: str, temperature: float, seed: int | None,
                    max_tokens: int, provider_order: tuple[str, ...] | None = None,
                    allow_fallbacks: bool = True) -> dict:
    """Normalized, auditable sampling configuration + its SHA-256.

    Records exactly the sampling- and routing-relevant request parameters (no
    prompt content), so a run's configuration is reconstructable from the
    ledger. The hash is over the canonical {model, temperature, seed,
    max_tokens, provider_order, allow_fallbacks} — so pinning a provider, or
    forbidding fallbacks, changes the config hash.
    """
    core = {"model": model, "temperature": float(temperature),
            "seed": seed, "max_tokens": int(max_tokens),
            "provider_order": list(provider_order) if provider_order else None,
            "allow_fallbacks": bool(allow_fallbacks)}
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return {**core, "config_sha256": hashlib.sha256(canonical.encode()).hexdigest()}



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
    # mirrors the live chat's auditable attributes (None offline by default)
    config: dict | None = None
    last_provider: str | None = None
    last_model: str | None = None

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


def _chat_config(chat: Chat) -> dict | None:
    """The auditable sampling config a live/scripted chat exposes, if any."""
    return getattr(chat, "config", None)


def run_case(chat: Chat, case: Case, mode: str, persona: str = "neutral",
             max_chars: int = 8000, protocol: str = "standard",
             density: int = 5, ledger=None, reanchor: bool = False,
             reviewer: Chat | None = None, repeat_index: int = 0,
             framework_terms: tuple[str, ...] | None = None) -> dict:
    """Drive one case through one arm; returns responses + metrics.

    ``max_chars`` truncates the raw source (the pilot worked with 2k/8k
    token slices, not whole files); applied before either arm so both see
    the same source slice. ``protocol`` selects the turn sequence
    ("standard" 4-turn or "extended" multi-turn pressure form); ``density``
    the hygiene-state structure level (ignored by the baseline arm).

    Sampling provenance: the chat callable exposes its auditable sampling
    config (model, temperature, seed, max_tokens, config_sha256) and the
    upstream provider returned by OpenRouter, if any; both are recorded in the
    result and ledger so the run's sampling/routing is reconstructable. Prompt
    content is never stored — only the responses' sha256.

    When a ``ledger`` is supplied (any object with the local-Layer-9
    ``record(kind, payload, ...)`` shape, e.g. ``desi_router.ledger.Ledger``),
    the run is appended as a ``context_contamination`` event.
    """
    raw = case.raw_text[:max_chars]
    if mode == "baseline":
        turns = baseline_turns(raw, persona=persona, protocol=protocol,
                               reanchor=reanchor)
    else:
        turns = hygiene_turns(raw, persona=persona, protocol=protocol,
                              density=density, reanchor=reanchor,
                              framework_terms=framework_terms)

    messages: list[dict] = [{"role": "system", "content": system_prompt()}]
    responses: list[str] = []
    providers: list[str | None] = []
    served_models: list[str | None] = []
    for user_turn in turns:
        messages.append({"role": "user", "content": user_turn})
        draft = chat(messages)
        providers.append(getattr(chat, "last_provider", None))
        served_models.append(getattr(chat, "last_model", None))
        # Optional cross-model review/revise pass. The reviewer sees only the
        # draft (never the raw context), and its corrected text becomes the
        # delivered answer that is scored and carried in the conversation —
        # so single-model and mixed arms stay metric-comparable, differing
        # only in whether the reviewer is the same model or a different one.
        if reviewer is not None:
            reply = reviewer(review_messages(draft))
            providers.append(getattr(reviewer, "last_provider", None))
            served_models.append(getattr(reviewer, "last_model", None))
        else:
            reply = draft
        messages.append({"role": "assistant", "content": reply})
        responses.append(reply)

    score_terms = FRAMEWORK_TERMS if framework_terms is None else framework_terms
    metrics = score_run(responses, score_terms)
    sampling = _chat_config(chat)
    reviewer_sampling = _chat_config(reviewer) if reviewer is not None else None
    # provider_sequence / served_model_sequence: the ordered per-call upstream
    # provider and the served model id (None where unreported). The set views
    # (providers_seen / served_models_seen) give the distinct routing. The
    # served model id matters because different providers can serve different
    # quantizations of the same model id — a routing confound below the
    # provider name itself.
    provider_sequence = list(providers)
    providers_seen = sorted({p for p in providers if p})
    served_model_sequence = list(served_models)
    served_models_seen = sorted({m for m in served_models if m})
    result = {
        "case_id": case.case_id,
        "mode": mode,
        "persona": persona,
        "protocol": protocol,
        "density": density,
        "reanchor": reanchor,
        "reviewed": reviewer is not None,
        "repeat_index": repeat_index,
        "sampling": sampling,
        "reviewer_sampling": reviewer_sampling,
        "providers_seen": providers_seen,
        "provider_sequence": provider_sequence,
        "served_models_seen": served_models_seen,
        "served_model_sequence": served_model_sequence,
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
                "reanchor": reanchor,
                "reviewed": reviewer is not None,
                "repeat_index": repeat_index,
                # sampling/routing provenance (no prompt content)
                "sampling": sampling,
                "reviewer_sampling": reviewer_sampling,
                "providers_seen": providers_seen,
                "provider_sequence": provider_sequence,
                "served_models_seen": served_models_seen,
                "served_model_sequence": served_model_sequence,
                "attribution_failures": metrics["attribution_failures"],
                "register_drift": metrics["register_drift"],
                "framing_leakage": metrics["framing_leakage"],
                "role_adoption": metrics["role_adoption"],
                "loop_detected": metrics["loop_detected"],
                "responses_sha256": hashlib.sha256(
                    json.dumps(responses, ensure_ascii=False).encode("utf-8")
                ).hexdigest(),
            },
        )
    return result


def run_benchmark(cases: list[Case], chat: Chat, persona: str = "neutral",
                  max_chars: int = 8000, protocol: str = "standard",
                  density: int = 5, ledger=None, repeat_index: int = 0,
                  framework_terms: tuple[str, ...] | None = None) -> dict:
    """Both arms over all cases + per-case comparison summaries."""
    runs = {
        mode: {
            c.case_id: run_case(chat, c, mode, persona, max_chars, protocol,
                                density, ledger, repeat_index=repeat_index,
                                framework_terms=framework_terms)
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
                           repeats: int = 1, density: int = 5, ledger=None,
                           framework_terms: tuple[str, ...] | None = None) -> dict:
    """Run the benchmark ``repeats`` times and estimate variance per metric.

    Provider sampling is not seedable even at temperature 0, so repeats are the
    only honest way to separate a real arm difference from run-to-run jitter.
    Per (arm, case, metric) this reports mean ± stdev and the raw values; with
    repeats=1 it degrades to a single run plus the per-repeat report list.
    """
    per_repeat = [
        run_benchmark(cases, chat, persona, max_chars, protocol, density, ledger,
                      repeat_index=i, framework_terms=framework_terms)
        for i in range(max(1, repeats))
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
                      repeats: int = 1, ledger=None,
                      framework_terms: tuple[str, ...] | None = None) -> dict:
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
    for i in range(max(1, repeats)):
        base = {
            c.case_id: run_case(chat, c, "baseline", persona, max_chars,
                                protocol, ledger=ledger, repeat_index=i,
                                framework_terms=framework_terms)
            for c in cases
        }
        baselines.append(base)
        for k in ks:
            hyg = {
                c.case_id: run_case(chat, c, "desi_hygiene", persona, max_chars,
                                    protocol, density=k, ledger=ledger, repeat_index=i,
                                    framework_terms=framework_terms)
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


# 2x2 factorial arms: (ingestion path) x (turn-level frame re-anchoring).
FACTORIAL_ARMS: dict[str, dict] = {
    "A_raw":              {"mode": "baseline",     "reanchor": False},
    "B_hygiene":          {"mode": "desi_hygiene", "reanchor": False},
    "C_reanchor":         {"mode": "baseline",     "reanchor": True},
    "D_hygiene_reanchor": {"mode": "desi_hygiene", "reanchor": True},
}


def _aggregate_over_cases(per_case_metrics: dict[str, dict], metric: str) -> float:
    """One number per (arm, repeat): sum over cases; register_drift = max."""
    vals = [m[metric] for m in per_case_metrics.values()]
    return max(vals) if metric == "register_drift" else sum(vals)


def run_factorial(cases: list[Case], chat: Chat, persona: str = "neutral",
                  max_chars: int = 8000, protocol: str = "standard",
                  density: int = 5, repeats: int = 1, ledger=None) -> dict:
    """2x2 ablation: ingestion hygiene x turn-level frame re-anchoring.

    Tests the previously untested mechanism conjecture — that interaction-
    driven register drift needs a turn-level control — instead of asserting
    it. Same cases, same user turns, same metrics in all four arms:

        A_raw                raw source,    no re-anchor
        B_hygiene            hygiene state, no re-anchor
        C_reanchor           raw source,    re-anchor before every turn
        D_hygiene_reanchor   hygiene state, re-anchor before every turn

    Per metric and repeat the arms aggregate over cases (sum; drift = max),
    then the factorial effects are computed per repeat and summarized:

        main_hygiene   = ((B + D) - (A + C)) / 2
        main_reanchor  = ((C + D) - (A + B)) / 2
        interaction    = (D - B) - (C - A)

    Negative main effects mean the factor reduced the metric.
    """
    per_repeat: list[dict] = []
    for i in range(max(1, repeats)):
        arms = {}
        for arm, cfg in FACTORIAL_ARMS.items():
            arms[arm] = {
                c.case_id: run_case(chat, c, cfg["mode"], persona, max_chars,
                                    protocol, density, ledger,
                                    reanchor=cfg["reanchor"], repeat_index=i)
                for c in cases
            }
        per_repeat.append(arms)

    arm_metrics = {
        arm: {
            metric: _summarize_repeats([
                _aggregate_over_cases(
                    {cid: run["metrics"] for cid, run in rep[arm].items()}, metric
                )
                for rep in per_repeat
            ])
            for metric in _VARIANCE_METRICS
        }
        for arm in FACTORIAL_ARMS
    }

    effects: dict[str, dict] = {}
    for metric in _VARIANCE_METRICS:
        per_rep_effects = {"main_hygiene": [], "main_reanchor": [], "interaction": []}
        for rep in per_repeat:
            agg = {
                arm: _aggregate_over_cases(
                    {cid: run["metrics"] for cid, run in rep[arm].items()}, metric
                )
                for arm in FACTORIAL_ARMS
            }
            a, b = agg["A_raw"], agg["B_hygiene"]
            c, d = agg["C_reanchor"], agg["D_hygiene_reanchor"]
            per_rep_effects["main_hygiene"].append(((b + d) - (a + c)) / 2)
            per_rep_effects["main_reanchor"].append(((c + d) - (a + b)) / 2)
            per_rep_effects["interaction"].append((d - b) - (c - a))
        effects[metric] = {k: _summarize_repeats(v) for k, v in per_rep_effects.items()}

    loops = {
        arm: sum(1 for rep in per_repeat for run in rep[arm].values()
                 if run["metrics"]["loop_detected"])
        for arm in FACTORIAL_ARMS
    }
    return {
        "persona": persona,
        "protocol": protocol,
        "density": density,
        "repeats": max(1, repeats),
        "arms": arm_metrics,
        "effects": effects,
        "loops": loops,
        "raw": per_repeat,
    }


def run_mixed_experiment(cases: list[Case], analyst_chat: Chat, reviewer_chat: Chat,
                         *, analyst_name: str, reviewer_name: str,
                         persona: str = "neutral", max_chars: int = 8000,
                         protocol: str = "standard", density: int = 5,
                         repeats: int = 1, ledger=None) -> dict:
    """Mixed-model DESi vs single-model controls (does orchestration help?).

    The deterministic hygiene state is unchanged (the DESi invariant: rules,
    not a model). The model dimension under test is a cross-model review pass:
    one model analyzes, a different model reviews and revises. Arms:

        A_analyst_raw       analyst alone, raw context (no hygiene, no review)
        B_analyst_hygiene   analyst alone, hygiene state
        B_reviewer_hygiene  reviewer model alone, hygiene state (the confound
                            control — how good is the reviewer model by itself?)
        C_mixed             hygiene state, analyst analyzes, reviewer reviews

    The decisive comparison is ``mixed_vs_best_single`` = C minus the better of
    the two single-model hygiene arms, per metric. A negative value means the
    mixed pipeline beat the best constituent model used alone — i.e. the gain
    is architectural, not merely "the reviewer model is more robust".
    """
    def _single(chat, mode, i, reviewer=None):
        return {
            c.case_id: run_case(chat, c, mode, persona, max_chars, protocol,
                                density, ledger, reviewer=reviewer, repeat_index=i)
            for c in cases
        }

    per_repeat: list[dict] = []
    for i in range(max(1, repeats)):
        per_repeat.append({
            "A_analyst_raw":      _single(analyst_chat, "baseline", i),
            "B_analyst_hygiene":  _single(analyst_chat, "desi_hygiene", i),
            "B_reviewer_hygiene": _single(reviewer_chat, "desi_hygiene", i),
            "C_mixed":            {
                c.case_id: run_case(analyst_chat, c, "desi_hygiene", persona,
                                    max_chars, protocol, density, ledger,
                                    reviewer=reviewer_chat, repeat_index=i)
                for c in cases
            },
        })

    arm_names = ("A_analyst_raw", "B_analyst_hygiene", "B_reviewer_hygiene", "C_mixed")
    arm_metrics = {
        arm: {
            metric: _summarize_repeats([
                _aggregate_over_cases(
                    {cid: run["metrics"] for cid, run in rep[arm].items()}, metric
                )
                for rep in per_repeat
            ])
            for metric in _VARIANCE_METRICS
        }
        for arm in arm_names
    }

    # mixed vs the better single-model hygiene arm, per repeat then summarized
    mixed_vs_best: dict[str, dict] = {}
    for metric in _VARIANCE_METRICS:
        deltas = []
        for rep in per_repeat:
            def agg(arm):
                return _aggregate_over_cases(
                    {cid: run["metrics"] for cid, run in rep[arm].items()}, metric
                )
            best_single = min(agg("B_analyst_hygiene"), agg("B_reviewer_hygiene"))
            deltas.append(agg("C_mixed") - best_single)
        mixed_vs_best[metric] = _summarize_repeats(deltas)

    loops = {
        arm: sum(1 for rep in per_repeat for run in rep[arm].values()
                 if run["metrics"]["loop_detected"])
        for arm in arm_names
    }
    return {
        "persona": persona,
        "protocol": protocol,
        "density": density,
        "repeats": max(1, repeats),
        "analyst": analyst_name,
        "reviewer": reviewer_name,
        "arms": arm_metrics,
        "mixed_vs_best_single": mixed_vs_best,
        "loops": loops,
        "raw": per_repeat,
    }


def build_openrouter_chat(model: str = DEFAULT_MODEL, *, api_key: str | None = None,
                          temperature: float = 0.0, seed: int | None = None,
                          max_tokens: int = DEFAULT_MAX_TOKENS,
                          provider_order: tuple[str, ...] | None = None,
                          allow_fallbacks: bool = True,
                          timeout: int = 120, retries: int = 2) -> Chat:
    """Live chat via OpenRouter (OpenAI-compatible). Needs OPENROUTER_API_KEY.

    The client **sends** ``temperature`` (default 0.0) on every request, and
    ``seed`` only when explicitly provided (omitted otherwise so providers
    without seed support are not handed a null field). OpenRouter **accepts**
    these OpenAI-compatible parameters, but their **actual application is not
    guaranteed** by the routed upstream provider — temperature 0.0 does not
    make outputs deterministic, and seed is best-effort only (see the README
    methodology section). Do not assume reproducibility from either.

    The returned callable exposes ``.config`` (the auditable sampling config
    from ``sampling_config``) and ``.last_provider`` (the upstream provider
    OpenRouter reports per response, if any). Raises RuntimeError when no key
    is configured.
    """
    import os

    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "No OPENROUTER_API_KEY configured — live mode unavailable. "
            "Use --dry-run with fixture responses instead."
        )

    def chat(messages: list[dict]) -> str:
        payload: dict = {"model": model, "messages": messages,
                         "temperature": float(temperature), "max_tokens": max_tokens}
        if seed is not None:
            payload["seed"] = seed
        if provider_order:
            # OpenRouter provider routing: pin order, optionally forbid
            # fallbacks so the call fails rather than silently re-routing —
            # the only way to get a clean single-backend condition.
            payload["provider"] = {"order": list(provider_order),
                                   "allow_fallbacks": allow_fallbacks}
        body = json.dumps(payload).encode()
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
                # capture the actually-routed upstream provider and served
                # model id (often a provider-specific quantization), if reported
                chat.last_provider = d.get("provider")
                chat.last_model = d.get("model")
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

    chat.config = sampling_config(model, temperature, seed, max_tokens,
                                  provider_order, allow_fallbacks)
    chat.last_provider = None
    chat.last_model = None
    return chat


def _stats(values: list[float]) -> dict:
    """mean / stdev / median / min / max / n for a value list."""
    n = len(values)
    return {
        "mean": round(statistics.mean(values), 4) if values else 0.0,
        "stdev": round(statistics.stdev(values), 4) if n > 1 else 0.0,
        "median": round(statistics.median(values), 4) if values else 0.0,
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
        "n": n,
    }


def run_temperature_comparison(
        cases: list[Case], build_chat: Callable[[float], Chat],
        *, temperatures: tuple[float, ...] = (0.0, 0.7),
        persona: str = "neutral", max_chars: int = 8000,
        protocol: str = "standard", density: int = 5, repeats: int = 5,
        ledger=None) -> dict:
    """Controlled temperature comparison on identical models, cases and prompts.

    Runs the two-arm benchmark at each temperature for ``repeats`` repetitions
    and produces a paired comparison. ``build_chat`` is a factory
    ``temperature -> Chat`` so every condition differs only in temperature.

    The comparison reports, per metric and per (case, arm) cell: mean / stdev /
    median / min / max at each temperature, the mean difference (high minus
    low), and — for the hygiene effect (hygiene minus baseline) per case — a
    flag when the sign of the effect changes between temperatures.
    """
    if len(temperatures) != 2:
        raise ValueError("temperature comparison expects exactly two temperatures")
    t_low, t_high = sorted(temperatures)

    per_temperature: dict[str, dict] = {}
    for t in (t_low, t_high):
        chat = build_chat(t)
        reports = [
            run_benchmark(cases, chat, persona, max_chars, protocol, density,
                          ledger, repeat_index=i)
            for i in range(max(1, repeats))
        ]
        per_temperature[str(t)] = {
            "sampling": getattr(chat, "config", None),
            "reports": reports,
        }

    def _cell_values(t: float, metric: str, case_id: str, arm: str) -> list[float]:
        return [rep["runs"][arm][case_id]["metrics"][metric]
                for rep in per_temperature[str(t)]["reports"]]

    comparison: dict[str, dict] = {}
    for metric in _VARIANCE_METRICS:
        by_cell: dict[str, dict] = {}
        effect_dir: dict[str, dict] = {}
        for c in cases:
            for arm in MODES:
                lo = _cell_values(t_low, metric, c.case_id, arm)
                hi = _cell_values(t_high, metric, c.case_id, arm)
                by_cell[f"{c.case_id}|{arm}"] = {
                    str(t_low): _stats(lo), str(t_high): _stats(hi),
                    "diff_mean": round(
                        (statistics.mean(hi) if hi else 0.0)
                        - (statistics.mean(lo) if lo else 0.0), 4),
                }
            # paired hygiene effect (hygiene minus baseline) per temperature
            def _effect(t):
                b = statistics.mean(_cell_values(t, metric, c.case_id, "baseline"))
                h = statistics.mean(_cell_values(t, metric, c.case_id, "desi_hygiene"))
                return round(h - b, 4)
            e_lo, e_hi = _effect(t_low), _effect(t_high)
            sign = lambda x: (x > 0) - (x < 0)  # noqa: E731
            effect_dir[c.case_id] = {
                str(t_low): e_lo, str(t_high): e_hi,
                "direction_changed": sign(e_lo) != sign(e_hi),
            }
        comparison[metric] = {"by_case_arm": by_cell, "hygiene_effect": effect_dir}

    return {
        "model_factory": "build_chat",
        "temperatures": [t_low, t_high],
        "repeats": max(1, repeats),
        "persona": persona,
        "protocol": protocol,
        "density": density,
        "per_temperature": per_temperature,
        "comparison": comparison,
    }
