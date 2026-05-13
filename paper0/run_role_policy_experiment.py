"""paper0 — role-policy experiment harness.

No scheduler changes. No detector changes. Role-policy evaluation only.

Conditions:
- A: LABEL ONLY — system message is literally "[ROLE: NAME]", nothing else.
- B: PREFIX POLICY — current production prefixes from src/desi/roles.py
                     plus GLOBAL_CONSTRAINTS, exactly as committed in e17efd8.
- C: PREFIX + ADVERSARIAL AUDIT — same as B, but the auditor receives an
                                   extra mandatory directive that requires
                                   it to attack every analyst conclusion
                                   before issuing a verdict.

The user payload is held constant across conditions. Only the system
message changes. This isolates the role-prefix variable.

Outputs:
- outputs/role_policy/condition_{A,B,C}/<trajectory_id>/<role>.md
- outputs/role_policy/condition_{A,B,C}/<trajectory_id>/payload.txt
- outputs/role_policy/metrics.json
- outputs/role_policy/role_policy_report.md  (written separately)

Usage:
    python paper0/run_role_policy_experiment.py            # all 10 × 3
    python paper0/run_role_policy_experiment.py --smoke    # first traj only
    python paper0/run_role_policy_experiment.py --only A   # one condition

Requires DEEPSEEK_API_KEY in .env.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from desi.config import load_config  # noqa: E402
from desi.deepseek_client import ChatMessage, DeepSeekClient  # noqa: E402
from desi.diagnostics import compute_all  # noqa: E402
from desi.phase_detector import detect_phases  # noqa: E402
from desi.roles import (  # noqa: E402
    GLOBAL_CONSTRAINTS,
    ROLE_ATTRACTOR_DIAGNOSTICIAN,
    ROLE_EN_EVENT_ANALYST,
    ROLE_REPORT_SYNTHESIZER,
    ROLE_SKEPTICAL_AUDITOR,
    ROLE_TRAJECTORY_ANALYST,
)
from desi.trajectory_loader import load_trajectory  # noqa: E402


_LOG = logging.getLogger("paper0")

ROLE_ORDER = (
    "TRAJECTORY_ANALYST",
    "ATTRACTOR_DIAGNOSTICIAN",
    "EN_EVENT_ANALYST",
    "SKEPTICAL_AUDITOR",
    "REPORT_SYNTHESIZER",
)

# ---------------------------------------------------------------------------
# Condition prefixes
# ---------------------------------------------------------------------------

CONDITION_A_LABEL_ONLY: dict[str, str] = {
    "TRAJECTORY_ANALYST": "[ROLE: TRAJECTORY_ANALYST]",
    "ATTRACTOR_DIAGNOSTICIAN": "[ROLE: ATTRACTOR_DIAGNOSTICIAN]",
    "EN_EVENT_ANALYST": "[ROLE: EN_EVENT_ANALYST]",
    "SKEPTICAL_AUDITOR": "[ROLE: SKEPTICAL_AUDITOR]",
    "REPORT_SYNTHESIZER": "[ROLE: REPORT_SYNTHESIZER]",
}

CONDITION_B_PREFIX_POLICY_RAW: dict[str, str] = {
    "TRAJECTORY_ANALYST": ROLE_TRAJECTORY_ANALYST,
    "ATTRACTOR_DIAGNOSTICIAN": ROLE_ATTRACTOR_DIAGNOSTICIAN,
    "EN_EVENT_ANALYST": ROLE_EN_EVENT_ANALYST,
    "SKEPTICAL_AUDITOR": ROLE_SKEPTICAL_AUDITOR,
    "REPORT_SYNTHESIZER": ROLE_REPORT_SYNTHESIZER,
}

ADVERSARIAL_AUDIT_DIRECTIVE = """

[paper0 CONDITION C — ADVERSARIAL AUDIT MODE]

You must produce one explicit attack on every conclusion made by every
analyst role (TRAJECTORY_ANALYST, ATTRACTOR_DIAGNOSTICIAN, EN_EVENT_ANALYST)
before issuing your verdict. For each attack:
- name the analyst role and the specific conclusion under attack
- state what evidence would invalidate the conclusion
- assign severity: low / medium / high

Do not produce a verdict line until every analyst conclusion has been
attacked. If a conclusion cannot be attacked because no metric or loop
either supports or contradicts it, mark it "UNFALSIFIABLE — high severity"
(which always blocks an ACCEPT verdict).
"""


def _wrap_with_global(prefix: str) -> str:
    return f"{GLOBAL_CONSTRAINTS.strip()}\n\n{prefix.strip()}"


def condition_b_system(role: str) -> str:
    return _wrap_with_global(CONDITION_B_PREFIX_POLICY_RAW[role])


def condition_c_system(role: str) -> str:
    base = CONDITION_B_PREFIX_POLICY_RAW[role]
    if role == "SKEPTICAL_AUDITOR":
        base = base + ADVERSARIAL_AUDIT_DIRECTIVE
    return _wrap_with_global(base)


def system_message(condition: str, role: str) -> str:
    if condition == "A":
        return CONDITION_A_LABEL_ONLY[role]
    if condition == "B":
        return condition_b_system(role)
    if condition == "C":
        return condition_c_system(role)
    raise ValueError(f"unknown condition: {condition}")


# ---------------------------------------------------------------------------
# User-payload composer (held constant across conditions)
# ---------------------------------------------------------------------------


def _metrics_block(trajectory) -> str:
    m = compute_all(trajectory)
    phases = detect_phases(trajectory)
    out: list[str] = []
    out.append(f"trajectory_id: {trajectory.trajectory_id}")
    out.append(f"domain: {trajectory.domain or '-'}")
    out.append(f"seed: {trajectory.seed or '-'}")
    out.append(f"persona: {trajectory.persona or '-'}")
    out.append(f"n_steps: {m.n_steps}")
    out.append(f"n_en_events: {m.n_en_events}")

    out.append("\nEN classifications:")
    for c in m.en_classifications:
        out.append(f"  loop={c.loop_index} eni_novelty={c.eni_novelty:.2f} -> {c.label}")

    out.append("\nNovelty recoveries:")
    for r in m.novelty_recoveries:
        dd = "n/a" if r.dup_delta is None else f"{r.dup_delta:+.2f}"
        nc = "n/a" if r.novel_claims_next is None else r.novel_claims_next
        out.append(
            f"  loop={r.loop_index} dup_delta={dd} novel_claims_next={nc} recovered={r.recovered}"
        )

    p = m.penultimate
    out.append("\nPenultimate-EN assessment:")
    out.append(
        f"  has_candidate={p.has_candidate} penultimate_loop={p.penultimate_loop} ({p.penultimate_label}) "
        f"last_loop={p.last_loop} ({p.last_label})"
    )
    out.append(f"  note: {p.note}")

    a = m.attractor
    out.append("\nTerminal attractor candidates (heuristic):")
    out.append(f"  candidate_claim_ids={a.candidate_claim_ids}")
    out.append(f"  method={a.method}; note={a.note}")

    out.append("\nFailure modes:")
    out.append(f"  terminal={m.failure.terminal}")
    for loop_idx, fm in m.failure.per_step:
        out.append(f"  loop={loop_idx} failure_mode={fm}")

    out.append("\nPhase detection:")
    if not phases.phases:
        out.append("  (no phase detected)")
    for ps in phases.phases:
        out.append(
            f"  {ps.name} loops {ps.start_loop}..{ps.end_loop} confidence={ps.confidence}"
        )
        for ev in ps.trigger_evidence:
            out.append(f"    - {ev}")

    return "\n".join(out)


def base_payload(trajectory) -> str:
    return (
        "## Deterministic metrics (authoritative)\n"
        f"{_metrics_block(trajectory)}\n\n"
        "## Trajectory (JSON)\n"
        f"```json\n{json.dumps(trajectory.model_dump(mode='json'), indent=2, ensure_ascii=False)}\n```\n"
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


@dataclass
class RoleResult:
    role: str
    content: str
    error: str | None = None
    seconds: float = 0.0


@dataclass
class RunResult:
    trajectory_id: str
    condition: str
    outputs: dict[str, RoleResult] = field(default_factory=dict)


_SANDBOX_DNS_HINT = "Host resolves to a private/reserved IP"


def call_role(
    client: DeepSeekClient,
    system_text: str,
    user_text: str,
    *,
    harness_retries: int = 4,
) -> tuple[str, str | None, float]:
    """Wrap DeepSeek client with harness-level retry for sandbox DNS warm-up.

    The DESi client treats HTTP 403 as non-transient, which is the correct
    default. In this sandbox, the outbound proxy occasionally returns 403
    with body "Host resolves to a private/reserved IP" before the DNS
    resolver settles. We retry that pattern (only that pattern) here,
    without modifying the shared client.
    """
    t0 = time.time()
    msgs = [
        ChatMessage(role="system", content=system_text),
        ChatMessage(role="user", content=user_text),
    ]
    last_err: str | None = None
    for attempt in range(1, harness_retries + 1):
        try:
            content = client.chat(msgs)
            return content, None, time.time() - t0
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            last_err = msg
            if _SANDBOX_DNS_HINT in msg and attempt < harness_retries:
                sleep_s = 2 * attempt
                _LOG.warning("sandbox DNS warm-up (attempt %d) — sleeping %ds", attempt, sleep_s)
                time.sleep(sleep_s)
                continue
            break
    return "", last_err, time.time() - t0


def run_one(
    client: DeepSeekClient,
    trajectory,
    condition: str,
    out_dir: Path,
) -> RunResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = base_payload(trajectory)
    (out_dir / "payload.txt").write_text(base, encoding="utf-8")
    (out_dir / "system_prompts.md").write_text(
        "\n\n".join(f"## {r}\n\n{system_message(condition, r)}" for r in ROLE_ORDER),
        encoding="utf-8",
    )

    result = RunResult(trajectory_id=trajectory.trajectory_id, condition=condition)
    role_outputs: list[tuple[str, str]] = []  # (role, body) — for downstream roles

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

        sys_text = system_message(condition, role)
        _LOG.info("  -> %s (system=%d chars)", role, len(sys_text))
        content, err, secs = call_role(client, sys_text, payload)
        result.outputs[role] = RoleResult(role=role, content=content, error=err, seconds=secs)
        body = content if not err else f"[ERROR: {err}]"
        role_outputs.append((role, body))
        (out_dir / f"{role}.md").write_text(body, encoding="utf-8")

    return result


# ---------------------------------------------------------------------------
# Scoring — 8 metrics per (condition, trajectory)
# ---------------------------------------------------------------------------

# The deterministic ground truth is the authority. Scoring functions read
# the role outputs as text and compare against the ground truth where they
# can; otherwise apply transparent heuristics. Each function is documented
# inline; the report explains the heuristic limits.

# Patterns
RE_NUMBER_OR_LOOP = re.compile(r"\b(loop\s*\d+|\d+\.\d+|0\.\d+|metric\b|deterministic\b)", re.IGNORECASE)
RE_STRONG_CONFIDENCE = re.compile(
    r"\b(confirmed|established|proves?|clearly|certainly|definitively|demonstrates?|conclusive|undeniabl[ey])\b",
    re.IGNORECASE,
)
RE_CAUSAL = re.compile(
    r"\b(because|due to|caused by|led to|resulted in|drives?|triggers?|produces?|forced)\b",
    re.IGNORECASE,
)
RE_SENTENCE = re.compile(r"(?<=[\.\!\?])\s+(?=[A-Z\[])")

CONTRADICTORY_PAIRS = (
    (re.compile(r"\battractor\s+(lock|formed|present|confirmed|detected)\b", re.IGNORECASE),
     re.compile(r"\bno\s+attractor\b|\battractor\s+(absent|not\s+present|not\s+detected)\b", re.IGNORECASE)),
    (re.compile(r"\brecovered\s*(=|:)?\s*true|novelty\s+recovery\s+(present|occurred|happened)", re.IGNORECASE),
     re.compile(r"\brecovered\s*(=|:)?\s*false|no\s+(novelty\s+)?recovery", re.IGNORECASE)),
    (re.compile(r"\bgenuine\s+transformation\b", re.IGNORECASE),
     re.compile(r"\bfalse\s+return\b|local\s+variation", re.IGNORECASE)),
)


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return [s.strip() for s in RE_SENTENCE.split(text) if s.strip()]


def m1_contradiction_count(outputs: dict[str, str]) -> int:
    """Count cross-role logical contradictions on the same axis."""
    sentences = []
    for role, body in outputs.items():
        for s in split_sentences(body):
            sentences.append((role, s))
    n = 0
    for pos_re, neg_re in CONTRADICTORY_PAIRS:
        has_pos = any(pos_re.search(s) for _, s in sentences)
        has_neg = any(neg_re.search(s) for _, s in sentences)
        if has_pos and has_neg:
            n += 1
    return n


def m2_unsupported_claims(outputs: dict[str, str]) -> int:
    """Count assertive sentences in the synthesizer output with no loop /
    metric citation. Heuristic — assertive = contains is/are/was/were/shows."""
    synth = outputs.get("REPORT_SYNTHESIZER", "")
    n = 0
    for s in split_sentences(synth):
        if re.search(r"\b(is|are|was|were|shows?|demonstrates?|indicates?|implies)\b", s, re.IGNORECASE):
            if not RE_NUMBER_OR_LOOP.search(s):
                n += 1
    return n


def m3_overclaim_count(outputs: dict[str, str]) -> int:
    """Count occurrences of strong-confidence words not followed by a
    citation in the same sentence."""
    n = 0
    for body in outputs.values():
        for s in split_sentences(body):
            if RE_STRONG_CONFIDENCE.search(s) and not RE_NUMBER_OR_LOOP.search(s):
                n += 1
    return n


def m4_recovery_misclassification(trajectory, outputs: dict[str, str]) -> int:
    """For each EN event with deterministic recovered flag, check whether
    the EN_EVENT_ANALYST output classifies it consistently. We look for
    'loop N' followed (within ~120 chars) by recovered-positive or -negative
    language and compare to ground truth."""
    m = compute_all(trajectory)
    en_text = outputs.get("EN_EVENT_ANALYST", "").lower()
    misses = 0
    for r in m.novelty_recoveries:
        # Find a window mentioning this loop
        loop_token = f"loop {r.loop_index}"
        idx = en_text.find(loop_token)
        if idx < 0:
            # EN analyst didn't mention this loop -> count as miss (silence)
            misses += 1
            continue
        window = en_text[idx : idx + 240]
        says_recovered = bool(re.search(r"\brecover", window))
        says_not_recovered = bool(re.search(r"no recover|did not recover|not\s+recover|no novelty recovery", window))
        if r.recovered and says_not_recovered and not says_recovered:
            misses += 1
        elif (not r.recovered) and says_recovered and not says_not_recovered:
            misses += 1
    return misses


def m5_attractor_misclassification(trajectory, outputs: dict[str, str]) -> int:
    """Compare the attractor diagnostician's claim against the deterministic
    candidate list. If determ has candidates -> diagnostician should
    affirm; if empty -> should refrain."""
    m = compute_all(trajectory)
    deterministic_has = bool(m.attractor.candidate_claim_ids)
    ad_text = outputs.get("ATTRACTOR_DIAGNOSTICIAN", "").lower()
    affirms = bool(re.search(r"\battractor\s+(lock|formed|present|confirmed|detected|candidate)|terminal\s+convergence", ad_text))
    denies = bool(re.search(r"no\s+attractor|attractor\s+(absent|not\s+present|not\s+detected)|no\s+convergence", ad_text))
    if deterministic_has and denies and not affirms:
        return 1
    if (not deterministic_has) and affirms and not denies:
        return 1
    return 0


def m6_phase_overlap_count(trajectory, outputs: dict[str, str]) -> int:
    """Count phase mentions in role outputs that overlap impossibly without
    disclaimer (e.g. III + V in same loop range, no 'concurrent' / 'after'
    qualifier on that sentence)."""
    text = " ".join(outputs.values()).lower()
    # Crude: count co-mentions of incompatible phase pairs in the same paragraph.
    overlap_pairs = (
        ("phase iii", "phase v"),
        ("development", "terminal convergence"),
        ("phase ii", "phase iv"),
    )
    n = 0
    paragraphs = re.split(r"\n\s*\n", text)
    for para in paragraphs:
        for a, b in overlap_pairs:
            if a in para and b in para:
                if not re.search(r"(after|then|subsequently|reversal|recovery|overlap)", para):
                    n += 1
                    break
    return n


def m7_hallucinated_causal_claims(outputs: dict[str, str]) -> int:
    """Count causal-language sentences with no metric / loop citation."""
    n = 0
    for body in outputs.values():
        for s in split_sentences(body):
            if RE_CAUSAL.search(s) and not RE_NUMBER_OR_LOOP.search(s):
                n += 1
    return n


def m8_agreement_with_deterministic_metrics(trajectory, outputs: dict[str, str]) -> float:
    """Score [0,1]: fraction of deterministic findings echoed in role outputs.

    Checks:
    - each EN classification's label mentioned within ~120 chars of its loop
    - each phase name mentioned somewhere
    - each attractor candidate id mentioned (if any)
    """
    m = compute_all(trajectory)
    phases = detect_phases(trajectory)
    bag = " ".join(outputs.values()).lower()

    checks = 0
    hits = 0

    # EN classifications
    en_text = (outputs.get("EN_EVENT_ANALYST", "") + " " + outputs.get("REPORT_SYNTHESIZER", "")).lower()
    for c in m.en_classifications:
        checks += 1
        loop_token = f"loop {c.loop_index}"
        idx = en_text.find(loop_token)
        if idx >= 0:
            window = en_text[idx : idx + 240]
            label_words = c.label.split("_")
            if any(w in window for w in label_words):
                hits += 1

    # Phase names
    for ps in phases.phases:
        checks += 1
        roman = ps.name.split("_", 1)[0].lower()  # i, ii, iii, iv, v
        if f"phase {roman}" in bag or ps.name.lower().replace("_", " ").lower() in bag:
            hits += 1

    # Attractor candidates
    for cid in m.attractor.candidate_claim_ids:
        checks += 1
        if cid.lower() in bag:
            hits += 1

    if checks == 0:
        return 1.0
    return round(hits / checks, 3)


SCORERS: dict[str, Callable] = {
    "contradiction_count": lambda t, o: m1_contradiction_count(o),
    "unsupported_claims": lambda t, o: m2_unsupported_claims(o),
    "overclaim_count": lambda t, o: m3_overclaim_count(o),
    "recovery_misclassification": lambda t, o: m4_recovery_misclassification(t, o),
    "attractor_misclassification": lambda t, o: m5_attractor_misclassification(t, o),
    "phase_overlap_count": lambda t, o: m6_phase_overlap_count(t, o),
    "hallucinated_causal_claims": lambda t, o: m7_hallucinated_causal_claims(o),
    "agreement_with_deterministic_metrics": lambda t, o: m8_agreement_with_deterministic_metrics(t, o),
}


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
    return scored


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="first trajectory only")
    parser.add_argument("--only", choices=["A", "B", "C"], help="run only one condition")
    parser.add_argument(
        "--root", default=str(REPO / "outputs" / "role_policy"), help="output root"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    cfg = load_config()
    cfg.require_api_key()
    client = DeepSeekClient(cfg)

    trajectories_dir = REPO / "data" / "adversarial"
    paths = sorted(trajectories_dir.glob("*.json"))
    if args.smoke:
        paths = paths[:1]

    conditions = ["A", "B", "C"] if not args.only else [args.only]
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)

    metrics_path = root / "metrics.json"
    all_metrics: dict = {}
    if metrics_path.exists():
        all_metrics = json.loads(metrics_path.read_text())

    for p in paths:
        trajectory = load_trajectory(p)
        tid = trajectory.trajectory_id
        all_metrics.setdefault(tid, {})
        for cond in conditions:
            _LOG.info("== %s | condition %s ==", tid, cond)
            out_dir = root / f"condition_{cond}" / tid
            run = run_one(client, trajectory, cond, out_dir)
            all_metrics[tid][cond] = score(trajectory, run)
            metrics_path.write_text(json.dumps(all_metrics, indent=2))
        _LOG.info("  metrics %s -> %s", tid, all_metrics[tid])

    _LOG.info("Done. metrics: %s", metrics_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
