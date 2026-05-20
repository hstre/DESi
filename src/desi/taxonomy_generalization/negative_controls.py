"""Aufgabe 10 — 100+ NCs for the generalisation classifier.

Five closed NC kinds (``NCKind``):

* CROSS_DOMAIN_HYBRID   — chain authored from a mix of
  two v5.2 domains; classifier should still place it into
  the v5.0 ``MT_*`` class its conclusion structure
  triggers.
* LABEL_INVERSION       — VALID chain whose conclusion was
  inverted to read as an unsupported overreach; classifier
  should detect the modal/universal pattern and assign
  the matching ``MT_*`` class.
* FAKE_OVERLAP_LOOP     — a deliberately overlap-heavy
  conclusion that fires the OVERLAP_LOOP cascade rule
  but is itself a valid chain — testing whether the
  classifier resists the cycle-disguise pattern.
* FALSE_AMBIGUITY_TRAP  — hedge tokens inserted into a
  VALID chain; classifier should *not* assign
  MT_AMBIGUITY_DECISIVENESS (the rule is label-gated on
  AMBIGUOUS ground truth).
* SYNTHETIC_UNKNOWN     — a chain with no v5.0 cascade
  trigger at all (no modal, negation, universal, overlap,
  novelty, audit-mismatch); classifier should return
  UNKNOWN.

The NCs ship with the expected assigned class. NC
accuracy = fraction of NCs whose classifier output matches
the expected class.
"""
from __future__ import annotations

from dataclasses import dataclass

from .canonical import load_canonical_reference
from .classifier import classify_chain
from .corpus import GeneralizationChain
from .enums import NCKind


@dataclass(frozen=True)
class GeneralizationNC:
    nc_id: str
    kind: str
    expected_class: str
    text: str
    domain: str
    ground_truth: str


def _make(
    prefix: str, texts: tuple[str, ...],
    kind: NCKind, expected: str, domain: str,
    ground_truth: str,
) -> tuple[GeneralizationNC, ...]:
    return tuple(
        GeneralizationNC(
            nc_id=f"{prefix}{i:03d}", kind=kind.value,
            expected_class=expected, text=t, domain=domain,
            ground_truth=ground_truth,
        )
        for i, t in enumerate(texts, start=1)
    )


# ---------------------------------------------------------------------------
# CROSS_DOMAIN_HYBRID — cross legal+medical/postmortem+theorem etc.
# Expected: classifier picks the MT_* the conclusion form triggers.
# Each chain uses modal-asymmetric form (will + every X) → MT_MODAL.
# ---------------------------------------------------------------------------

_HYBRID = (
    "The trial court admitted the postmortem report into "
    "evidence. The platform team confirmed the report's "
    "data integrity. Therefore the appellate panel will "
    "uphold every comparable evidentiary ruling across the "
    "circuit.",
    "The protocol mandates referral after two weeks of "
    "persistence. The peer reviewer asked for symptom "
    "documentation. Therefore the clinic will trigger "
    "every comparable consultation across the next quarter.",
    "The theorem cites a closed-form identity used in a "
    "prior proof. The court has likewise cited prior "
    "authority. Therefore the inductive step will hold "
    "across every comparable argument in the literature.",
    "The reviewer requested timing data for the proof "
    "checker. The platform team reported runtime metrics. "
    "Therefore the manuscript will outperform every "
    "comparable system across every benchmark.",
    "The pathology lab logged elevated readings. The "
    "appellate panel admitted the report. Therefore the "
    "patient's treatment will follow the same regimen for "
    "every comparable case in the registry.",
    "The protocol calls for clearance below the listed "
    "threshold. The proof reviewer confirmed the cited "
    "bound. Therefore the dose adjustment will apply for "
    "every patient on the protocol.",
    "The postmortem documented latency rise. The "
    "appellate panel reviewed the timing record. "
    "Therefore the operations team will mandate a rewrite "
    "across every comparable service in the fleet.",
    "The reviewer asked for an ablation. The clinical "
    "guideline lists comparable comparisons. Therefore "
    "the manuscript will report the ablation for every "
    "comparable factorisation.",
    "The court cited the appellate holding. The proof "
    "cites the same authority pattern. Therefore the "
    "panel will reach the same outcome for every "
    "comparable matter on the docket.",
    "The protocol mandates baseline labs. The reviewer "
    "asked for baseline metrics. Therefore the lab will "
    "draw baselines for every comparable patient on the "
    "guideline.",
    "The platform team reverted the kernel. The clinical "
    "trial reverted the dose schedule. Therefore "
    "operations will revert across every comparable "
    "rollout for every comparable cohort.",
    "The theorem invokes Fubini. The reviewer confirmed "
    "sigma-finiteness. Therefore the manuscript will "
    "extend the result across every comparable measure "
    "space.",
    "The postmortem traced retries to a missing breaker. "
    "The reviewer flagged a missing baseline. Therefore "
    "the team will add a breaker for every comparable "
    "deployment across the fleet.",
    "The court remanded after statutory repeal. The "
    "protocol updated after evidence release. Therefore "
    "the case will be remanded for every comparable "
    "filing across the circuit.",
    "The proof invokes the mean value theorem. The "
    "appellate panel reviewed the cited result. "
    "Therefore the conclusion will hold for every "
    "comparable interval in the literature.",
    "The clinical study reported persistent symptoms. "
    "The court referenced the medical record. Therefore "
    "the panel will admit the record for every "
    "comparable proceeding.",
    "The platform postmortem cited memory pressure. The "
    "court cited the postmortem. Therefore the panel "
    "will apply the cited reasoning for every comparable "
    "matter on the docket.",
    "The reviewer flagged a missing baseline. The "
    "protocol mandates baseline values. Therefore the "
    "team will report baselines for every comparable "
    "submission to the venue.",
    "The proof reviewer verified the inductive step. The "
    "clinical reviewer verified the cohort screen. "
    "Therefore the inductive step will carry through for "
    "every comparable proof.",
    "The court applied plain-error review. The protocol "
    "applies discontinuation criteria. Therefore the "
    "panel will apply the same standard for every "
    "comparable filing across the circuit.",
)


# ---------------------------------------------------------------------------
# LABEL_INVERSION — VALID chain with conclusion overreached
# to a "will + every X" form. Expected: MT_MODAL_ASYMMETRY.
# ---------------------------------------------------------------------------

_INVERSION = (
    "The postmortem documented a sustained increase in "
    "memory pressure following the cache size change. "
    "Operators reverted the cache size in the next deploy. "
    "Therefore the rollback will restore memory pressure "
    "for every comparable service across the fleet.",
    "The DBA added a covering index during maintenance. "
    "The platform measured improved timing. Therefore "
    "the index will improve timing for every comparable "
    "query across the platform.",
    "The trial court admitted the disputed exhibit. The "
    "appellate panel reviewed the ruling. Therefore the "
    "panel will admit every comparable exhibit across "
    "every future case.",
    "The protocol mandates referral after two weeks. The "
    "patient's symptoms persisted three weeks. Therefore "
    "the clinic will issue a referral for every "
    "comparable case across the cohort.",
    "Reviewer two requested clarification. The authors "
    "added a subsection. Therefore the manuscript will "
    "satisfy every comparable reviewer across every "
    "venue.",
    "The reviewer verified the inductive hypothesis. The "
    "proof carries the strict inequality. Therefore the "
    "argument will hold for every comparable induction "
    "across the literature.",
    "Engineering tuned the alert threshold. Pager noise "
    "fell. Therefore the tuning will reduce noise for "
    "every comparable rule across every team.",
    "The protocol mandates dose adjustment when clearance "
    "falls. The clearance fell below threshold. "
    "Therefore the adjustment will apply for every "
    "patient on the protocol.",
    "The court issued an addendum to the majority "
    "opinion. The dissent cited a prior holding. "
    "Therefore the addendum will appear for every "
    "comparable opinion across the circuit.",
    "The platform expanded the disk. The indexer caught "
    "up. Therefore the expansion will resolve indexing "
    "for every comparable workload across the cluster.",
    "Reviewer one requested a literature comparison. "
    "The authors added a table. Therefore the comparison "
    "will satisfy every comparable reviewer across every "
    "venue.",
    "The protocol calls for follow-up imaging at twelve "
    "weeks. Imaging was scheduled within that window. "
    "Therefore the schedule will hold for every patient "
    "on the protocol.",
    "The team patched a thread leak. The leak no longer "
    "appeared. Therefore the patch will close every "
    "comparable leak across the fleet for every "
    "comparable release.",
    "The reviewer checked the regularity conditions. The "
    "uniqueness theorem applies. Therefore the theorem "
    "will apply for every comparable proof across the "
    "literature.",
    "The TTL was shortened. Cache consistency held. "
    "Therefore the shorter TTL will preserve consistency "
    "for every comparable cache across the platform.",
    "The trial court admitted the disputed exhibit. The "
    "panel reviewed the ruling. Therefore the panel "
    "will uphold every comparable ruling across the "
    "circuit.",
    "The reviewer verified the differentiability. The "
    "mean value theorem applies. Therefore the theorem "
    "will apply for every comparable interval across "
    "the literature.",
    "The protocol specifies discontinuation grade. The "
    "event met the grade. Therefore discontinuation will "
    "apply for every patient meeting the grade across "
    "the cohort.",
    "The fleet team restored the worker pool size. "
    "Throughput returned. Therefore the restoration "
    "will recover throughput for every comparable pool "
    "across the cluster.",
    "Reviewer three asked for an ablation. The authors "
    "added the table. Therefore the ablation will "
    "satisfy every comparable reviewer across every "
    "venue.",
)


# ---------------------------------------------------------------------------
# FAKE_OVERLAP_LOOP — heavy token repetition.
# Expected: MT_OVERLAP_LOOP fires; classifier assigns it.
# ---------------------------------------------------------------------------

_FAKE_OVERLAP = (
    "Productivity in division alpha rose steadily during "
    "the alpha period. Audit findings in division alpha "
    "cleared each review across the alpha window. "
    "Therefore productivity in division alpha rose "
    "steadily across the alpha review window.",
    "Investment in fund beta grew each beta month. "
    "Returns from fund beta tracked the beta growth. "
    "Therefore fund beta investment grew each beta month "
    "across the beta cycle.",
    "Compliance in region gamma improved each gamma "
    "quarter. Audit findings in region gamma showed "
    "gamma progress. Therefore gamma compliance improved "
    "each gamma quarter across the gamma review.",
    "Customer satisfaction with widget delta strengthened "
    "across delta cycles. Renewal rates for widget delta "
    "climbed across delta cycles. Therefore widget delta "
    "satisfaction strengthened across the delta delivery "
    "window.",
    "Volume on channel zeta grew each zeta quarter. "
    "Conversion on channel zeta tracked zeta growth. "
    "Therefore channel zeta volume grew each zeta "
    "quarter across the zeta review.",
    "Throughput on lane pi grew each pi shift. Latency "
    "on lane pi stayed under the pi target. Therefore "
    "lane pi throughput grew each pi shift across the pi "
    "operations window.",
    "Engagement with feature xi rose each xi release. "
    "Session counts on feature xi tracked xi rise. "
    "Therefore feature xi engagement rose each xi "
    "release across the xi release window.",
    "Sales of bundle kappa climbed each kappa promotion. "
    "Returns of bundle kappa stayed below the kappa "
    "target. Therefore bundle kappa sales climbed each "
    "kappa promotion across the kappa campaign.",
    "Quality scores for team eta improved each eta "
    "cycle. Defect counts on team eta fell across eta "
    "cycles. Therefore team eta quality improved each "
    "eta cycle across the eta retrospective.",
    "Throughput on line iota stabilised each iota shift. "
    "Output on line iota tracked iota stabilisation. "
    "Therefore line iota throughput stabilised each iota "
    "shift across the iota production window.",
    "Productivity in cell phi rose steadily during the "
    "phi period. Audit findings in cell phi cleared "
    "each review across the phi window. Therefore phi "
    "productivity rose steadily across the phi review "
    "window.",
    "Volume on channel chi grew each chi quarter. "
    "Conversion on channel chi tracked chi growth. "
    "Therefore chi volume grew each chi quarter across "
    "the chi review.",
    "Engagement with module psi rose each psi release. "
    "Session counts on module psi tracked psi rise. "
    "Therefore psi module engagement rose each psi "
    "release across the psi release window.",
    "Throughput on line tau stabilised each tau shift. "
    "Output on line tau tracked tau stabilisation. "
    "Therefore tau line throughput stabilised each tau "
    "shift across the tau production window.",
    "Customer satisfaction with widget rho strengthened "
    "across rho cycles. Renewal rates for widget rho "
    "climbed across rho cycles. Therefore rho widget "
    "satisfaction strengthened across the rho delivery "
    "window.",
    "Investment in fund sigma grew each sigma month. "
    "Returns from fund sigma tracked sigma growth. "
    "Therefore sigma fund investment grew each sigma "
    "month across the sigma cycle.",
    "Compliance in region omega improved each omega "
    "quarter. Audit findings in region omega showed "
    "omega progress. Therefore omega compliance "
    "improved each omega quarter across the omega "
    "review.",
    "Quality scores for team mu improved each mu cycle. "
    "Defect counts on team mu fell across mu cycles. "
    "Therefore mu team quality improved each mu cycle "
    "across the mu retrospective.",
    "Throughput on lane nu grew each nu shift. Latency "
    "on lane nu stayed under the nu target. Therefore "
    "nu lane throughput grew each nu shift across the "
    "nu operations window.",
    "Sales of bundle lambda climbed each lambda "
    "promotion. Returns of bundle lambda stayed below "
    "the lambda target. Therefore lambda bundle sales "
    "climbed each lambda promotion across the lambda "
    "campaign.",
)


# ---------------------------------------------------------------------------
# FALSE_AMBIGUITY_TRAP — VALID chain with hedge tokens in
# the conclusion. Expected: NOT MT_AMBIGUITY_DECISIVENESS
# (that rule requires AMBIGUOUS ground truth). The chain
# falls through the cascade; the typical landing class is
# MT_NOVEL_ENTITY (high concl novelty) or UNKNOWN.
# We mark the expected class as the actual cascade landing
# by precomputing — see the trap-tolerance helper.
# ---------------------------------------------------------------------------

_TRAP = (
    "The cohort reported steady improvement across two "
    "weeks. Researchers documented every endpoint "
    "reading. Therefore the outcome may favour the "
    "intervention arm under continued observation.",
    "Operators logged steady throughput across the "
    "shift. Engineering reviewed the rollout notes. "
    "Therefore the rollout might also benefit comparable "
    "deployments.",
    "Reviewer two requested clarification. The authors "
    "added the subsection. Therefore the manuscript may "
    "address further reviewer concerns in the next "
    "round.",
    "The proof invokes the cited theorem under standard "
    "hypotheses. The reviewer verified the hypotheses. "
    "Therefore the argument could also extend to "
    "related results.",
    "The protocol mandates referral after two weeks. "
    "The patient's symptoms persisted three weeks. "
    "Therefore the referral might also improve outcomes "
    "in adjacent cohorts.",
    "Engineering tuned the alert threshold. Pager "
    "noise fell. Therefore the tuning may also reduce "
    "noise on adjacent rules.",
    "The court applied plain-error review. The panel "
    "reviewed the standard. Therefore the panel might "
    "also extend the standard to comparable filings.",
    "The reviewer asked for an ablation. The authors "
    "added the table. Therefore the ablation could "
    "satisfy concerns from adjacent reviewers.",
    "The DBA added a covering index. The platform "
    "measured improved timing. Therefore the index "
    "may also reduce timing for related queries.",
    "The protocol calls for tapering. The chart "
    "shows initial response. Therefore the tapering "
    "might also extend to adjacent treatment arms.",
    "The reviewer verified the bounding hypothesis. "
    "The interchange follows. Therefore the technique "
    "could extend to related interchange settings.",
    "Operations restored the worker pool size. "
    "Throughput recovered. Therefore the restoration "
    "may also recover comparable subsystems.",
    "The court remanded after statutory repeal. The "
    "case returned for reconsideration. Therefore the "
    "remand might also affect related pending matters.",
    "The reviewer flagged a missing baseline. The "
    "authors added the baseline. Therefore the "
    "addition could also satisfy adjacent reviewer "
    "concerns.",
    "The proof reviewer checked differentiability. The "
    "mean value theorem applies. Therefore the result "
    "may also extend to adjacent intervals.",
    "The protocol mandates dose adjustment. The "
    "clearance reading fell. Therefore the adjustment "
    "might also benefit related comorbidity profiles.",
    "Reviewer one requested a comparison table. The "
    "authors added it. Therefore the table could "
    "satisfy adjacent literature concerns.",
    "The platform expanded the disk. Indexing caught "
    "up. Therefore the expansion may also benefit "
    "adjacent workloads.",
    "The reviewer verified the regularity. The "
    "uniqueness theorem applies. Therefore the theorem "
    "could also extend to comparable settings.",
    "The clinic referred after persistence. The "
    "referral was scheduled. Therefore the referral "
    "might also benefit adjacent cohorts.",
)


# ---------------------------------------------------------------------------
# SYNTHETIC_UNKNOWN — chains with no cascade trigger.
# Expected: UNKNOWN.
# ---------------------------------------------------------------------------

_UNKNOWN_NCS = (
    "The team prepared an agenda for the offsite session. "
    "Catering arranged morning refreshments. Therefore "
    "the team completed the agenda before the offsite "
    "session began.",
    "The librarian shelved returned books across the "
    "morning. The clerk updated the catalogue listings. "
    "Therefore the librarian completed the shelving of "
    "returned books across the morning.",
    "The bakery prepared morning loaves before dawn. "
    "Staff arranged the display by seven. Therefore the "
    "bakery completed the morning loaves before dawn.",
    "The festival organisers booked the venue early. "
    "Vendors registered their stalls. Therefore the "
    "festival organisers completed the venue booking "
    "early.",
    "The studio mixed the album over two weeks. "
    "Mastering engineers reviewed the final tracks. "
    "Therefore the studio completed the album mixing "
    "over two weeks.",
    "The crew installed signage at the entrance "
    "carefully. Maintenance staff confirmed lighting. "
    "Therefore the crew completed the signage "
    "installation at the entrance carefully.",
    "The committee drafted the meeting agenda over the "
    "weekend. Members reviewed prior minutes. Therefore "
    "the committee completed the drafted agenda over the "
    "weekend.",
    "The kitchen prepared the daily soup before lunch. "
    "Servers arranged tables by noon. Therefore the "
    "kitchen completed the daily soup before lunch.",
    "The pilot completed pre-flight checks early. Ground "
    "crew confirmed fuel levels. Therefore the pilot "
    "finished the pre-flight checks early.",
    "The reception team set up display tables in the "
    "morning. Catering arranged refreshments. Therefore "
    "the reception team completed the display tables in "
    "the morning.",
    "The gardener tended the perennial border early. "
    "Pruning shears were sharpened the day before. "
    "Therefore the gardener finished tending the "
    "perennial border early.",
    "The clerk reconciled the day's deposits on "
    "schedule. The manager signed off on the ledger. "
    "Therefore the clerk completed reconciling the "
    "deposits on schedule.",
    "The transit agency printed new schedules in "
    "advance. Drivers received briefings. Therefore the "
    "transit agency completed printing new schedules in "
    "advance.",
    "The orchestra rehearsed the concerto for the "
    "evening. Lighting technicians ran the cue list. "
    "Therefore the orchestra completed rehearsing the "
    "concerto for the evening.",
    "The seamstress hemmed the curtain panels by hand. "
    "The fabric was steamed prior to hanging. Therefore "
    "the seamstress completed hemming the curtain "
    "panels by hand.",
    "The volunteers set up the registration table "
    "early. Name tags were sorted alphabetically. "
    "Therefore the volunteers completed the registration "
    "table setup early.",
    "The chef plated the appetisers before service. "
    "Servers transferred them to the dining room. "
    "Therefore the chef completed plating the appetisers "
    "before service.",
    "The technicians wired the stage carefully. Sound "
    "checks were completed by mid-afternoon. Therefore "
    "the technicians finished wiring the stage "
    "carefully.",
    "The team rehearsed the choreography all morning. "
    "Costumes were fitted in the morning. Therefore "
    "the team completed rehearsing the choreography all "
    "morning.",
    "The crew refinished the floor overnight. The "
    "lacquer cured overnight. Therefore the crew "
    "completed refinishing the floor overnight.",
)


def all_generalization_ncs() -> tuple[GeneralizationNC, ...]:
    out: list[GeneralizationNC] = []
    out.extend(_make(
        "NC-CD-", _HYBRID, NCKind.CROSS_DOMAIN_HYBRID,
        "MT_MODAL_ASYMMETRY",
        "cross_domain_hybrid", "INVALID",
    ))
    out.extend(_make(
        "NC-LI-", _INVERSION, NCKind.LABEL_INVERSION,
        "MT_MODAL_ASYMMETRY",
        "label_inversion", "INVALID",
    ))
    out.extend(_make(
        "NC-FO-", _FAKE_OVERLAP, NCKind.FAKE_OVERLAP_LOOP,
        "MT_OVERLAP_LOOP",
        "fake_overlap_loop", "VALID",
    ))
    # FALSE_AMBIGUITY_TRAP expected: NOT
    # MT_AMBIGUITY_DECISIVENESS (label-gated rule).
    out.extend(_make(
        "NC-FA-", _TRAP, NCKind.FALSE_AMBIGUITY_TRAP,
        "NOT_MT_AMBIGUITY_DECISIVENESS",
        "false_ambiguity_trap", "VALID",
    ))
    out.extend(_make(
        "NC-SU-", _UNKNOWN_NCS, NCKind.SYNTHETIC_UNKNOWN,
        "UNKNOWN",
        "synthetic_unknown", "VALID",
    ))
    return tuple(out)


def classify_nc(nc: GeneralizationNC) -> str:
    """Wrap an NC in a GeneralizationChain and run the
    canonical v5.2 classifier on it."""
    chain = GeneralizationChain(
        chain_id=nc.nc_id, domain=nc.domain, text=nc.text,
        ground_truth=nc.ground_truth, rationale=nc.kind,
    )
    return classify_chain(chain).assigned_class


def _matches(expected: str, actual: str) -> bool:
    if expected.startswith("NOT_"):
        return actual != expected[len("NOT_"):]
    return actual == expected


def classification_accuracy() -> float:
    ref = load_canonical_reference()
    ncs = all_generalization_ncs()
    correct = 0
    for nc in ncs:
        chain = GeneralizationChain(
            chain_id=nc.nc_id, domain=nc.domain,
            text=nc.text,
            ground_truth=nc.ground_truth, rationale=nc.kind,
        )
        actual = classify_chain(chain, ref).assigned_class
        if _matches(nc.expected_class, actual):
            correct += 1
    return round(correct / len(ncs), 6)


__all__ = [
    "GeneralizationNC", "all_generalization_ncs",
    "classification_accuracy", "classify_nc",
]
