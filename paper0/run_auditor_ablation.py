"""paper0 — auditor-model ablation.

No prompt changes. No detector changes. No scheduler changes. The prefix
policy is exactly Condition B from run_role_policy_experiment.py
(GLOBAL_CONSTRAINTS + production prefixes). The only variable across
conditions is the LLM that backs each role.

Conditions:
- B_BASELINE   : every role on deepseek-v4-flash
- B_PRO_AUDIT  : every role on deepseek-v4-flash EXCEPT SKEPTICAL_AUDITOR,
                 which runs on deepseek-v4-pro

Metrics (eight per (condition, trajectory)):
- overclaim_count                (reused from run_role_policy_experiment)
- unsupported_claims             (reused)
- hallucinated_causal_claims     (reused)
- contradiction_count            (reused)
- threshold_artifact_detection   (new — in SKEPTICAL_AUDITOR output)
- useful_objection_count         (new — in SKEPTICAL_AUDITOR output)
- false_objection_count          (new — in SKEPTICAL_AUDITOR output)
- synthesis_degradation_count    (new — in REPORT_SYNTHESIZER output)

Outputs:
- outputs/role_policy/auditor_model_ablation/<condition>/<trajectory>/<role>.md
- outputs/role_policy/auditor_model_ablation_metrics.json
- outputs/role_policy/auditor_model_ablation.md  (written separately)
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from desi.config import load_config  # noqa: E402
from desi.deepseek_client import ChatMessage, DeepSeekClient  # noqa: E402
from desi.diagnostics import compute_all  # noqa: E402
from desi.phase_detector import detect_phases  # noqa: E402
from desi.trajectory_loader import load_trajectory  # noqa: E402

# Reuse the prefix-policy text, base-payload composer, and the four
# generic scorers from the role-policy experiment harness. No prefix
# changes here — only the model assignment changes.
sys.path.insert(0, str(REPO / "paper0"))
from run_role_policy_experiment import (  # noqa: E402
    CONDITION_B_PREFIX_POLICY_RAW,
    ROLE_ORDER,
    base_payload,
    condition_b_system,
    m1_contradiction_count,
    m2_unsupported_claims,
    m3_overclaim_count,
    m7_hallucinated_causal_claims,
    split_sentences,
)

_LOG = logging.getLogger("paper0.auditor_ablation")


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------

MODEL_FLASH = "deepseek-v4-flash"
MODEL_PRO = "deepseek-v4-pro"

ABLATION_CONDITIONS: dict[str, dict[str, str]] = {
    "B_BASELINE": {role: MODEL_FLASH for role in ROLE_ORDER},
    "B_PRO_AUDIT": {
        **{role: MODEL_FLASH for role in ROLE_ORDER},
        "SKEPTICAL_AUDITOR": MODEL_PRO,
    },
}


# ---------------------------------------------------------------------------
# New scoring functions (auditor-specific)
# ---------------------------------------------------------------------------

RE_THRESHOLD_VALUE = re.compile(r"\b(0\.\d{1,3}|\d{1,2}%)\b")
RE_THRESHOLD_TARGET = re.compile(
    r"\b(threshold|cut-?off|boundary|calibration|sensitivit|near|just\s+(above|below))\b",
    re.IGNORECASE,
)
RE_ARTIFACT_WORD = re.compile(
    r"\b(arbitrary|artifact|artefact|fragile|brittle|miscalibrat|over[-\s]?sensitive"
    r"|sensitive\s+to|depends?\s+on\s+(the\s+)?threshold|would\s+(re)?classify"
    r"|reclassif|borderline)\b",
    re.IGNORECASE,
)
RE_OBJECTION_HEADING = re.compile(
    # Forms we accept as a numbered objection heading:
    #   "### Objection 3"      / "## Attack 2"
    #   "**Objection 3**"      / "Attack 1:"
    #   "3. Objection ..."     / "3) Objection ..."
    #   "1. **MEDIUM severity**" (Flash style — numbered + bolded severity)
    #   "1. **High** - ..."    (compact severity)
    r"(?:"
    r"^\s*(?:###?|\*\*)\s*(?:Objection|Attack)\s*\d+|"
    r"^\s*\d+[\.\)]\s+(?:Objection|Attack)\s*\d*\b|"
    r"^\s*\d+[\.\)]\s+\*\*(?:low|medium|high|critical)\b"
    r")",
    re.IGNORECASE | re.MULTILINE,
)
RE_EXPLICIT_NO_OBJECTIONS = re.compile(
    r"\b(?:no\s+objections?(?:\s+(?:found|raised|to\s+make|that\s+meet))?|"
    r"none\s+of\s+the\s+prior\s+role\s+outputs|"
    r"no\s+other\s+objections|"
    r"no\s+high[-\s]severity\s+unresolved\s+objections?|"
    r"unresolved\s+high[-\s]severity\s+objections?:\s*none|"
    r"no\s+high[-\s]severity\s+objection)\b",
    re.IGNORECASE,
)
RE_LOOP_OR_METRIC_OR_ROLE = re.compile(
    r"\bloop\s*\d+\b|\bmetric\b|\bdup_rate\b|\benib?_\w+\b|\bnovel_claims\b|"
    r"\b(TRAJECTORY|ATTRACTOR|EN[_\s]?EVENT|REPORT)_?(ANALYST|DIAGNOSTICIAN|SYNTHESIZER)\b",
    re.IGNORECASE,
)
RE_FALSE_OBJECTION_PATTERN = re.compile(
    r"may\s+have\s+occurred\s+(after|before)|"
    r"temporal\s+attribution|"
    r"the\s+EN\s+may\s+not\s+have|"
    r"unfalsifiable|"
    r"the\s+(metric|metrics|deterministic\s+block)\s+(?:may\s+be|is)\s+(wrong|incorrect|misleading)|"
    r"cannot\s+be\s+verified\s+from\s+the\s+data\s+alone|"
    r"deterministic\s+(?:metrics|block)\s+(?:may|might)\s+(?:overstate|misclassif)",
    re.IGNORECASE,
)
RE_SYNTH_DEGRADATION = re.compile(
    r"\b(DISPUTED|disputed|REJECTED|rejected|"
    r"downgrad(?:ed?|ing)|"
    r"✅?\s*EXPLORATORY|🔬|"
    r"requires?\s+replication|"
    r"unsupported|"
    r"upheld\s*\\?—?\s*MEDIUM|"
    r"upheld\s*\\?—?\s*HIGH|"
    r"objection\s+\d+\s+\(HIGH|"
    r"objection\s+\d+\s+\(MEDIUM)\b",
    re.IGNORECASE,
)


def m_threshold_artifact_detection(trajectory, outputs: dict[str, str]) -> int:
    """Count sentences in the SKEPTICAL_AUDITOR output that flag a
    deterministic threshold as potentially artifactual.

    A hit requires the sentence to contain BOTH:
      - a numeric threshold reference (a 0.xx value or a %)
      - one of the artifact-style words ('arbitrary', 'borderline', 'just
        above', 'sensitive to', 'reclassify', etc.).
    """
    audit = outputs.get("SKEPTICAL_AUDITOR", "")
    n = 0
    for s in split_sentences(audit):
        if RE_ARTIFACT_WORD.search(s) and (
            RE_THRESHOLD_VALUE.search(s) or RE_THRESHOLD_TARGET.search(s)
        ):
            n += 1
    return n


def _objection_blocks(text: str) -> list[str]:
    """Split an auditor output into per-objection blocks based on numbered
    headings ('Objection N', 'Attack N'). The first block (before any
    heading) is dropped — it is preamble, not an objection."""
    headings = list(RE_OBJECTION_HEADING.finditer(text))
    if not headings:
        return []
    blocks: list[str] = []
    for i, m in enumerate(headings):
        start = m.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        blocks.append(text[start:end])
    return blocks


def m_useful_objection_count(trajectory, outputs: dict[str, str]) -> int:
    """Numbered objections that cite a specific loop / metric / role.

    Auditor outputs that explicitly say 'no objections' return 0 — that is
    a legitimately empty objection space, not a measurement failure.
    """
    audit = outputs.get("SKEPTICAL_AUDITOR", "")
    blocks = _objection_blocks(audit)
    return sum(1 for b in blocks if RE_LOOP_OR_METRIC_OR_ROLE.search(b))


def m_false_objection_count(trajectory, outputs: dict[str, str]) -> int:
    """Numbered objections that match one of the known false-objection
    rhetorical patterns (temporal-attribution drift, 'metrics may be wrong',
    'cannot be verified from the data alone', etc.). Heuristic and
    conservative — false positives are likely under-counted, not over.
    """
    blocks = _objection_blocks(outputs.get("SKEPTICAL_AUDITOR", ""))
    return sum(1 for b in blocks if RE_FALSE_OBJECTION_PATTERN.search(b))


def m_synthesis_degradation_count(trajectory, outputs: dict[str, str]) -> int:
    """Count of findings the synthesizer downgrades / disputes / marks
    exploratory in response to the auditor's objections. Counts distinct
    markers in REPORT_SYNTHESIZER text."""
    synth = outputs.get("REPORT_SYNTHESIZER", "")
    return len(RE_SYNTH_DEGRADATION.findall(synth))


SCORERS: dict[str, Callable] = {
    "overclaim_count": lambda t, o: m3_overclaim_count(o),
    "unsupported_claims": lambda t, o: m2_unsupported_claims(o),
    "hallucinated_causal_claims": lambda t, o: m7_hallucinated_causal_claims(o),
    "contradiction_count": lambda t, o: m1_contradiction_count(o),
    "threshold_artifact_detection": m_threshold_artifact_detection,
    "useful_objection_count": m_useful_objection_count,
    "false_objection_count": m_false_objection_count,
    "synthesis_degradation_count": m_synthesis_degradation_count,
}


# ---------------------------------------------------------------------------
# Orchestration with per-role model override
# ---------------------------------------------------------------------------

_SANDBOX_DNS_HINT = "Host resolves to a private/reserved IP"

# deepseek-v4 returns reasoning_content + content. With the production
# auditor prefix and prior-role evidence packed in, reasoning alone can
# consume 1500+ tokens; bump well above that so the content field is
# never starved.
AUDITOR_MAX_TOKENS = 4096
DEFAULT_MAX_TOKENS = 2048


@dataclass
class RoleResult:
    role: str
    model: str
    content: str
    error: str | None = None
    seconds: float = 0.0
    finish_reason: str | None = None
    used_reasoning_fallback: bool = False


@dataclass
class RunResult:
    trajectory_id: str
    condition: str
    outputs: dict[str, RoleResult] = field(default_factory=dict)


def _post_chat(cfg, model: str, msgs: list[ChatMessage], max_tokens: int) -> dict:
    """Direct POST to /v1/chat/completions so we can read reasoning_content
    as a fallback when content is empty (v4 models)."""
    import requests
    payload = {
        "model": model,
        "messages": [m.to_dict() for m in msgs],
        "temperature": cfg.temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {cfg.require_api_key()}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        f"{cfg.deepseek_base_url.rstrip('/')}/v1/chat/completions",
        json=payload, headers=headers, timeout=cfg.timeout_seconds,
    )
    if r.status_code != 200:
        # Mirror the DESi client's failure surface
        raise RuntimeError(f"DeepSeek HTTP {r.status_code}: {r.text[:500]}")
    return r.json()


def call_role(
    cfg,
    model: str,
    system_text: str,
    user_text: str,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    harness_retries: int = 4,
) -> tuple[str, str | None, float, str | None, bool]:
    """Return (content, error, seconds, finish_reason, used_reasoning_fallback)."""
    t0 = time.time()
    msgs = [
        ChatMessage(role="system", content=system_text),
        ChatMessage(role="user", content=user_text),
    ]
    last_err: str | None = None
    for attempt in range(1, harness_retries + 1):
        try:
            body = _post_chat(cfg, model, msgs, max_tokens)
            choice = body["choices"][0]
            msg = choice["message"]
            content = (msg.get("content") or "").strip()
            reasoning = (msg.get("reasoning_content") or "").strip()
            used_fallback = False
            if not content and reasoning:
                content = reasoning
                used_fallback = True
            finish = choice.get("finish_reason")
            return content, None, time.time() - t0, finish, used_fallback
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            last_err = msg
            if _SANDBOX_DNS_HINT in msg and attempt < harness_retries:
                sleep_s = 2 * attempt
                _LOG.warning("sandbox DNS warm-up (attempt %d) — sleeping %ds", attempt, sleep_s)
                time.sleep(sleep_s)
                continue
            if (("503" in msg) or ("502" in msg) or ("504" in msg) or ("429" in msg)) and attempt < harness_retries:
                sleep_s = 2 ** attempt
                _LOG.warning("transient HTTP (attempt %d) — sleeping %ds", attempt, sleep_s)
                time.sleep(sleep_s)
                continue
            break
    return "", last_err, time.time() - t0, None, False


def run_one(
    cfg,
    trajectory,
    condition: str,
    out_dir: Path,
) -> RunResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = base_payload(trajectory)
    (out_dir / "payload.txt").write_text(base, encoding="utf-8")
    model_map = ABLATION_CONDITIONS[condition]
    (out_dir / "model_map.json").write_text(json.dumps(model_map, indent=2), encoding="utf-8")

    result = RunResult(trajectory_id=trajectory.trajectory_id, condition=condition)
    role_outputs: list[tuple[str, str]] = []

    for role in ROLE_ORDER:
        if role == "SKEPTICAL_AUDITOR":
            payload = base + "\n\n## Prior role outputs (subject to audit)\n"
            for r, body in role_outputs:
                payload += f"\n### {r}\n{body}\n"
        elif role == "REPORT_SYNTHESIZER":
            payload = base + "\n\n## All role outputs\n"
            for r, body in role_outputs:
                payload += f"\n### {r}\n{body}\n"
        else:
            payload = base

        sys_text = condition_b_system(role)  # prefix policy frozen across conditions
        model = model_map[role]
        # The auditor needs more headroom: reasoning + cited objections + verdict.
        budget = AUDITOR_MAX_TOKENS if role == "SKEPTICAL_AUDITOR" else DEFAULT_MAX_TOKENS
        _LOG.info("  -> %s on %s (system=%d chars, max_tokens=%d)", role, model, len(sys_text), budget)
        content, err, secs, finish, used_fallback = call_role(
            cfg, model, sys_text, payload, max_tokens=budget,
        )
        result.outputs[role] = RoleResult(
            role=role, model=model, content=content, error=err, seconds=secs,
            finish_reason=finish, used_reasoning_fallback=used_fallback,
        )
        body = content if not err else f"[ERROR: {err}]"
        role_outputs.append((role, body))
        (out_dir / f"{role}.md").write_text(body, encoding="utf-8")

    return result


def score(trajectory, run: RunResult) -> dict:
    body = {role: (r.content if not r.error else "") for role, r in run.outputs.items()}
    scored = {}
    for name, fn in SCORERS.items():
        try:
            scored[name] = fn(trajectory, body)
        except Exception as exc:  # noqa: BLE001
            scored[name] = f"ERR: {exc}"
    scored["errors"] = {role: r.error for role, r in run.outputs.items() if r.error}
    scored["seconds_total"] = sum(r.seconds for r in run.outputs.values())
    scored["models"] = {role: r.model for role, r in run.outputs.items()}
    return scored


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="first trajectory only")
    parser.add_argument("--only", choices=list(ABLATION_CONDITIONS), help="run only one condition")
    parser.add_argument(
        "--root",
        default=str(REPO / "outputs" / "role_policy" / "auditor_model_ablation"),
        help="output dir for raw role outputs",
    )
    parser.add_argument(
        "--metrics-path",
        default=str(REPO / "outputs" / "role_policy" / "auditor_model_ablation_metrics.json"),
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    cfg = load_config()
    cfg.require_api_key()

    trajectories_dir = REPO / "data" / "adversarial"
    paths = sorted(trajectories_dir.glob("*.json"))
    if args.smoke:
        paths = paths[:1]

    conditions = list(ABLATION_CONDITIONS) if not args.only else [args.only]
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)

    metrics_path = Path(args.metrics_path)
    all_metrics: dict = {}
    if metrics_path.exists():
        try:
            all_metrics = json.loads(metrics_path.read_text())
        except Exception:  # noqa: BLE001
            all_metrics = {}

    for p in paths:
        trajectory = load_trajectory(p)
        tid = trajectory.trajectory_id
        all_metrics.setdefault(tid, {})
        for cond in conditions:
            _LOG.info("== %s | condition %s ==", tid, cond)
            out_dir = root / cond / tid
            run = run_one(cfg, trajectory, cond, out_dir)
            all_metrics[tid][cond] = score(trajectory, run)
            metrics_path.write_text(json.dumps(all_metrics, indent=2))
        _LOG.info("  metrics %s -> %s", tid, all_metrics[tid])

    _LOG.info("Done. metrics: %s", metrics_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
