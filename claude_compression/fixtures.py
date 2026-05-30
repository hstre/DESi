"""Fixture chat histories WITH pre-registered ground-truth epistemic markers.

Each fixture carries:
  * `chat`: a realistic multi-turn dialog (system/user/assistant)
  * `ground_truth`: the architecture decisions / discarded hypotheses / open conflicts / etc.
    that MUST survive compression. These are the LISTED markers from the brief.

Important: ground-truth is set HERE, by the author, BEFORE the extractor runs — not derived
from the extractor's own output. So the evaluation cannot be self-congratulatory.
"""
from __future__ import annotations

FIXTURE_1 = {
    "id": "research_pipeline",
    "chat": [
        {"role": "system", "content": "You help design a research pipeline."},
        {"role": "user", "content": "Goal: build a reproducible pipeline that audits markdown papers for "
                                    "numeric inconsistencies, duplicate paragraphs, and overclaim terms. "
                                    "We need to keep it offline and deterministic."},
        {"role": "assistant", "content": "Sounds good. Should we use embeddings for semantic duplicate detection?"},
        {"role": "user", "content": "Rejected: embeddings — they break determinism and add a heavy dependency. "
                                    "We dropped that idea earlier in a Wikipedia probe."},
        {"role": "assistant", "content": "Then lexical Jaccard for duplicates and regex for numeric ranges?"},
        {"role": "user", "content": "Decision: we will use lexical Jaccard for near-duplicate paragraphs, "
                                    "threshold 0.6. Architecture decision: a single CLI `audit.py paper.md` "
                                    "with no external services."},
        {"role": "assistant", "content": "What about overclaim terms — fixed list or learnable?"},
        {"role": "user", "content": "Decision: fixed list (breakthrough, revolutionary, unknown unknowns…). "
                                    "Problem: we still need a traceability check for 'all claims derived from "
                                    "artifacts' style boilerplate."},
        {"role": "user", "content": "Tested: numeric_consistency check passed on README.md, found the "
                                    "compression-range mismatch at line 14 vs 406. Confirmed: the paper has "
                                    "the inconsistency we suspected."},
        {"role": "user", "content": "Tension: should the auditor edit the paper, or only report? "
                                    "Decided: report only — auto-editing is too risky."},
        {"role": "user", "content": "References: README.md, utility_evolution/paper_audit/audit.py, "
                                    "https://github.com/hstre/DESi."},
        {"role": "user", "content": "Open question: how do we extend to multi-file docs without breaking "
                                    "the offline / single-file CLI?"},
    ],
    "ground_truth": {
        "active_goals": ["audit markdown papers for numeric inconsistencies, duplicates, overclaim"],
        "open_problems": ["multi-file docs without breaking single-file CLI",
                          "traceability-boilerplate check"],
        "confirmed_findings": ["numeric_consistency found compression-range mismatch in README"],
        "discarded_hypotheses": ["embeddings (breaks determinism)",
                                  "auto-editing the paper (too risky)"],
        "architecture_decisions": ["lexical Jaccard at threshold 0.6 for duplicates",
                                     "single CLI audit.py with no external services",
                                     "fixed overclaim-term list"],
        "open_conflicts": ["editing vs report-only"],
        "references": ["README.md", "audit.py", "github.com/hstre/DESi"],
    },
}

FIXTURE_2 = {
    "id": "topic_shift_negative",
    "chat": [
        {"role": "system", "content": "You help analyze topic-shift robustness."},
        {"role": "user", "content": "Goal: test whether DESi compression survives abrupt topic switches "
                                    "on stitched DeepDialogue trajectories."},
        {"role": "assistant", "content": "What is the spike rule for shift detection?"},
        {"role": "user", "content": "Decision: spike rule = trajectory-internal mean + 1 std, fixed BEFORE "
                                    "the run, not tuned to labels. No semantic sensors."},
        {"role": "user", "content": "Tested: 300 trajectories. Result: F1_B (DESi state) = 0.138, F1_A (raw "
                                    "novelty proxy) = 0.292, separation 0.048, catastrophic 205/300."},
        {"role": "assistant", "content": "F1_B is below F1_A. Should we tune the threshold?"},
        {"role": "user", "content": "Rejected: tuning the threshold to recover F1. We pre-registered no "
                                    "tuning on benchmark labels. Decision: report honestly and stop."},
        {"role": "user", "content": "Confirmed: on short chat utterances the lexical state cannot separate "
                                    "real topic boundaries from ordinary turn-to-turn churn."},
        {"role": "user", "content": "Conflict: this contradicts the DriftBench dual-layer success — same "
                                    "compression idea, very different result depending on domain."},
        {"role": "user", "content": "References: benchmarks/trajectory/run_topic_shift_trace.py, "
                                    "reports/topic_shift_trace_report.md."},
    ],
    "ground_truth": {
        "active_goals": ["test compression under abrupt topic switching"],
        "open_problems": [],
        "confirmed_findings": ["lexical state cannot separate shifts on short chat",
                                "F1_B 0.138 below F1_A 0.292"],
        "discarded_hypotheses": ["tuning the spike threshold to fit labels"],
        "architecture_decisions": ["spike rule = mean+1*std, fixed pre-run"],
        "open_conflicts": ["DriftBench success vs topic-shift failure — domain dependence"],
        "references": ["run_topic_shift_trace.py", "topic_shift_trace_report.md"],
    },
}

FIXTURE_3 = {
    "id": "decision_buddy_design",
    "chat": [
        {"role": "system", "content": "You help design a deterministic decision recorder."},
        {"role": "user", "content": "Goal: a tool that records option-vs-criteria trade-offs and replays them."},
        {"role": "assistant", "content": "Should the tool integrate an LLM to rationalize the choice?"},
        {"role": "user", "content": "Rejected: LLM rationalization — non-deterministic, breaks replay."},
        {"role": "user", "content": "Decision: pure weighted sum with explicit higher_is_better flag, "
                                    "replay-hashed via desi.core.replay_kernel."},
        {"role": "user", "content": "Architecture decision: separate `decide()` (logic) and `format_record()` "
                                    "(rendering). The recommendation always lists the price (the criterion "
                                    "the runner-up beats it on)."},
        {"role": "user", "content": "Tested: passes 5 unit tests including a higher_is_better=False case."},
        {"role": "user", "content": "Problem: the renderer used bold markdown that broke a test assertion. "
                                    "Decided: fix the assertion, not the renderer — bold is the right output."},
        {"role": "user", "content": "Open question: do we want a CLI front-door, or only the Python API?"},
        {"role": "user", "content": "References: utility_evolution/decision_record/decide.py, "
                                    "tests/utility_evolution/test_decision_record.py."},
    ],
    "ground_truth": {
        "active_goals": ["record option-vs-criteria trade-offs reproducibly"],
        "open_problems": ["CLI front-door or Python-API-only"],
        "confirmed_findings": ["passes 5 unit tests including higher_is_better=False"],
        "discarded_hypotheses": ["LLM rationalization (non-deterministic)"],
        "architecture_decisions": ["pure weighted sum, replay-hashed",
                                     "separate decide() from format_record()",
                                     "recommendation lists the trade-off price"],
        "open_conflicts": [],
        "references": ["decide.py", "test_decision_record.py"],
    },
}

def _long_session():
    """Concatenate the three sessions into one long research dialog. The ground truth is the
    UNION of the individual truths (every per-session marker must still survive). This tests
    whether compression scales with input length (the paper's regime)."""
    chat = []
    gt = {k: [] for k in FIXTURE_1["ground_truth"]}
    for fx in (FIXTURE_1, FIXTURE_2, FIXTURE_3):
        chat.extend(fx["chat"])
        for k, vs in fx["ground_truth"].items():
            gt[k].extend(vs)
    return {"id": "long_session_concat", "chat": chat, "ground_truth": gt}


FIXTURE_LONG = _long_session()
ALL_FIXTURES = (FIXTURE_1, FIXTURE_2, FIXTURE_3, FIXTURE_LONG)
