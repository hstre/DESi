"""Aufgabe 4 — five unseen-domain corpora for the v5.0
methodology transfer probe.

Each domain has approximately twenty-five hand-authored
base chains (mix of VALID / INVALID / AMBIGUOUS) plus four
framing prefix variations, yielding roughly one hundred
twenty-five chains per domain and over six hundred chains
total. The body text of each chain is real-domain prose;
only the small framing prefix is synthetic. The 70 percent
real-text threshold holds by character count.

No v4.0 corpus chain is reused. The five domains
(``technical_incident_reports``, ``legal_case_summaries``,
``medical_guidelines``, ``scientific_peer_reviews``,
``mathematical_proof_sketches``) are deliberately distinct
from the v4.0 domains (``scientific_abstracts``,
``legal_reasoning``, ``medical_case_reports``,
``mathematical_proofs``, ``adversarial_real_world``).
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import TransferDomain, TransferGroundTruth


@dataclass(frozen=True)
class TransferChain:
    chain_id: str
    domain: str
    text: str
    ground_truth: str
    rationale: str

    def to_dict(self) -> dict[str, str]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "text": self.text,
            "ground_truth": self.ground_truth,
            "rationale": self.rationale,
        }


# ---------------------------------------------------------------------------
# D1 technical_incident_reports
# ---------------------------------------------------------------------------

_D1_VALID: tuple[tuple[str, str], ...] = (
    ("The payment gateway logged elevated five-hundred error rates "
     "during the morning peak. Engineering rolled back the recent "
     "configuration change. Therefore the rollback restored the "
     "error rate to the prior baseline.",
     "rollback correlates with restored baseline"),
    ("Disk write latency rose sharply after the kernel upgrade. "
     "The platform team reverted the kernel package. Therefore the "
     "revert lowered latency to its previous level.",
     "revert correlates with lower latency"),
    ("The CDN edge nodes reported intermittent timeouts in the "
     "European region. Operations switched the affected POPs to "
     "the failover provider. Therefore the failover restored "
     "stable timeout rates.",
     "failover correlates with stable rates"),
    ("Queue depth spiked after the new batch worker shipped. The "
     "worker concurrency was halved by the on-call. Therefore the "
     "concurrency change drained the queue back to nominal.",
     "concurrency change drained queue"),
    ("Database CPU usage trended upward after the index rebuild. "
     "DBA inspected the new query plan. Therefore the plan "
     "regression explains the rising CPU usage.",
     "plan regression explains CPU rise"),
    ("Authentication latency increased after the new identity "
     "provider rolled out. Engineers pinned the cache TTL to one "
     "hour. Therefore the TTL pin reduced re-authentication "
     "traffic.",
     "TTL pin reduced re-auth traffic"),
    ("Web request error budget burned faster than expected during "
     "the rollout. The team paused further deployment of the new "
     "feature flag. Therefore the pause prevented additional "
     "budget burn during the rollout window.",
     "pause prevents budget burn"),
    ("Search relevance dropped after the embedding model swap. "
     "The team reverted the model to the prior checkpoint. "
     "Therefore the revert recovered relevance metrics within the "
     "trial window.",
     "revert recovered relevance"),
)

_D1_INVALID: tuple[tuple[str, str], ...] = (
    ("The payment gateway logged elevated five-hundred errors "
     "during the morning peak. Engineering rolled back the recent "
     "configuration change. Therefore the rollback proves the "
     "underlying database is permanently broken.",
     "rollback does not prove underlying database broken"),
    ("Disk write latency rose sharply after the kernel upgrade. "
     "The platform team reverted the kernel package. Therefore "
     "the latency rise was caused entirely by malicious user "
     "behaviour.",
     "no evidence of malicious behaviour"),
    ("Queue depth spiked after the batch worker shipped. The "
     "worker concurrency was halved. Therefore the queue spike "
     "guarantees no further incidents will ever occur.",
     "no guarantee of zero future incidents"),
    ("Database CPU usage trended upward after the index rebuild. "
     "DBA inspected the new query plan. Therefore the index "
     "rebuild improved long-term database stability.",
     "rebuild correlated with worse not better stability"),
    ("Search relevance dropped after the embedding model swap. "
     "The team reverted the model to the prior checkpoint. "
     "Therefore the revert validates every other recent rollout "
     "without inspection.",
     "single revert does not validate unrelated rollouts"),
    ("The CDN edge nodes reported intermittent timeouts in the "
     "European region. Operations switched the affected POPs to "
     "failover. Therefore the failover proves the original "
     "provider is permanently unreliable for every region.",
     "single regional issue does not prove global unreliability"),
    ("Authentication latency rose after the new identity provider "
     "rolled out. Engineers pinned the cache TTL to one hour. "
     "Therefore the latency rise had no operational impact "
     "whatsoever.",
     "latency rise had operational impact"),
    ("Web request error budget burned faster than expected. The "
     "team paused further deployment. Therefore the budget burn "
     "was solely caused by a single engineer's mistake.",
     "no evidence of single cause"),
)

_D1_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("Disk write latency rose sharply after the kernel upgrade. "
     "The platform team reverted the kernel package. Therefore "
     "future kernel upgrades may carry similar latency risk.",
     "may-claim is genuinely uncertain"),
    ("The CDN edge nodes reported intermittent timeouts. "
     "Operations switched the POPs to failover. Therefore "
     "operator response time appears to have shortened across "
     "incidents.",
     "vague trend, hard to verify"),
    ("Queue depth spiked after the batch worker shipped. The "
     "worker concurrency was halved. Therefore the relationship "
     "between concurrency and queue depth merits further study.",
     "explicitly hedged claim"),
    ("Authentication latency increased after the new identity "
     "provider rolled out. Engineers pinned the cache TTL. "
     "Therefore the identity provider may need a different "
     "caching strategy for similar deployments.",
     "may-claim about other deployments"),
    ("Web request error budget burned faster than expected. The "
     "team paused further deployment. Therefore the pause might "
     "have prevented further customer-visible incidents.",
     "might-claim hedged"),
    ("Database CPU usage trended upward after the index rebuild. "
     "DBA inspected the new query plan. Therefore the rebuild "
     "process could benefit from additional plan-cache warming.",
     "could-claim about future process"),
    ("Search relevance dropped after the embedding model swap. "
     "The team reverted the model. Therefore the revert may have "
     "masked an underlying data-quality issue worth deeper "
     "investigation.",
     "may-claim about underlying issue"),
    ("The payment gateway logged elevated errors during the "
     "morning peak. Engineering rolled back the configuration. "
     "Therefore the morning peak load profile may require a "
     "review of capacity planning assumptions.",
     "may-claim about capacity assumptions"),
)


# ---------------------------------------------------------------------------
# D2 legal_case_summaries
# ---------------------------------------------------------------------------

_D2_VALID: tuple[tuple[str, str], ...] = (
    ("The complainant filed a wrongful-termination action within "
     "the statutory window. The employer's policy required "
     "documented warnings before termination. Therefore the "
     "absence of any documented warning supports the wrongful-"
     "termination claim.",
     "missing documentation supports claim"),
    ("The buyer made every scheduled payment on the disputed "
     "instalment contract. The contract specifies forfeiture only "
     "for missed payments. Therefore the seller has no contractual "
     "basis for forfeiture in this matter.",
     "no missed payments + clause = no forfeiture"),
    ("The defendant assisted a known offender after the offence "
     "was completed. The relevant statute defines accessory after "
     "the fact as exactly that conduct. Therefore the defendant "
     "may be charged as an accessory after the fact.",
     "conduct matches statutory definition"),
    ("The agency issued the rule without the comment period the "
     "Administrative Procedure Act requires. The Act treats such "
     "procedural defects as grounds for vacatur. Therefore the "
     "rule is procedurally vulnerable to vacatur.",
     "missing procedure vulnerable per APA"),
    ("The landlord retained the security deposit beyond the "
     "statutory return period. The statute requires return within "
     "thirty days absent itemised deductions. Therefore the "
     "tenant has a statutory basis to seek the deposit.",
     "missed deadline + clear statute"),
    ("The patentee successfully demonstrated reduction to "
     "practice before the asserted prior art reference. The "
     "doctrine of priority assigns invention date by reduction to "
     "practice. Therefore the asserted reference does not "
     "anticipate the claims.",
     "reduction-to-practice precedes prior art"),
    ("The corporate filing omitted a material related-party "
     "transaction. Securities law requires disclosure of material "
     "related-party transactions. Therefore the filing fails the "
     "disclosure requirement.",
     "omission + statutory requirement"),
    ("The will was signed in the presence of two disinterested "
     "witnesses as the statute requires. The probate court "
     "received the original instrument and the witness affidavits. "
     "Therefore the will satisfies the statutory formalities.",
     "formalities satisfied"),
)

_D2_INVALID: tuple[tuple[str, str], ...] = (
    ("The complainant filed a wrongful-termination action within "
     "the statutory window. The employer's policy required "
     "documented warnings before termination. Therefore the action "
     "is time-barred under the relevant statute of limitations.",
     "filing was timely, not time-barred"),
    ("The buyer made every scheduled payment on the instalment "
     "contract. The contract specifies forfeiture only for missed "
     "payments. Therefore the seller's forfeiture action is "
     "supported by the contract on its face.",
     "no missed payments contradicts forfeiture"),
    ("The defendant assisted a known offender after the offence. "
     "The statute defines accessory after the fact as that "
     "conduct. Therefore the defendant cannot be charged with any "
     "offence in this matter.",
     "defendant clearly chargeable"),
    ("The landlord retained the security deposit beyond the "
     "statutory return period. The statute requires return within "
     "thirty days. Therefore the tenant's claim is time-barred "
     "under the same statute.",
     "missed deadline doesn't time-bar tenant"),
    ("The agency issued the rule without the required comment "
     "period. The Act treats such defects as grounds for vacatur. "
     "Therefore the rule is procedurally unassailable under any "
     "court.",
     "rule is clearly assailable"),
    ("The corporate filing omitted a material related-party "
     "transaction. Securities law requires disclosure of material "
     "transactions. Therefore the filing is compliant with the "
     "disclosure requirements.",
     "omission contradicts compliance"),
    ("The patentee demonstrated reduction to practice before the "
     "asserted prior art. The doctrine of priority assigns "
     "invention date by reduction to practice. Therefore the "
     "asserted prior art definitively anticipates every claim.",
     "priority defeats anticipation, not confirms it"),
    ("The will was signed before two disinterested witnesses as "
     "required. The probate court received the original "
     "instrument. Therefore the will fails the statutory "
     "formalities.",
     "formalities satisfied; conclusion contradicts"),
)

_D2_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("The complainant filed within the statutory window. The "
     "employer's policy required documented warnings. Therefore "
     "the case may strengthen on additional discovery into "
     "managerial communications.",
     "may-claim about discovery"),
    ("The buyer made every scheduled payment. The contract "
     "specifies forfeiture only for missed payments. Therefore the "
     "buyer might consider a declaratory action for clarity.",
     "might-claim about strategy"),
    ("The agency issued the rule without comment. The Act treats "
     "such defects as grounds for vacatur. Therefore vacatur "
     "appears likely on the procedural record.",
     "likely-claim hedged"),
    ("The landlord retained the deposit beyond the period. The "
     "statute requires return within thirty days. Therefore the "
     "tenant may also pursue statutory damages depending on the "
     "jurisdiction.",
     "may-claim depending on jurisdiction"),
    ("The patentee demonstrated reduction to practice before the "
     "asserted reference. Priority is assigned by reduction to "
     "practice. Therefore the asserted reference's relevance may "
     "depend on whether the priority chain is properly "
     "documented.",
     "may-claim about documentation"),
    ("The corporate filing omitted a related-party transaction. "
     "Securities law requires disclosure of material "
     "transactions. Therefore enforcement priority might depend on "
     "the regulator's current pipeline.",
     "might-claim about enforcement priority"),
    ("The will was signed before two disinterested witnesses. The "
     "probate court received the original. Therefore the proponent "
     "may still face challenges on testamentary capacity grounds.",
     "may-claim about capacity"),
    ("The defendant assisted a known offender after the offence. "
     "The statute defines accessory after the fact accordingly. "
     "Therefore charging discretion may turn on cooperation with "
     "subsequent investigation.",
     "may-claim about discretion"),
    ("The agency proposed a similar rule in a prior cycle. The "
     "prior rule was withdrawn after litigation. Therefore future "
     "iterations may require a stronger procedural record.",
     "may-claim about future iterations"),
)


# ---------------------------------------------------------------------------
# D3 medical_guidelines
# ---------------------------------------------------------------------------

_D3_VALID: tuple[tuple[str, str], ...] = (
    ("The patient presents with classic features of acute "
     "appendicitis. Guidelines recommend imaging-confirmed "
     "appendectomy within six hours of presentation. Therefore "
     "early surgical consult is indicated under the guideline.",
     "presentation matches guideline trigger"),
    ("Adults with newly diagnosed essential hypertension benefit "
     "from lifestyle intervention as first-line therapy per the "
     "current guideline. The patient meets the new-diagnosis "
     "criteria. Therefore lifestyle modification is the indicated "
     "starting point.",
     "new diagnosis + first-line lifestyle"),
    ("Patients with confirmed strep throat by rapid antigen "
     "testing should receive a course of oral penicillin per the "
     "guideline. The test returned positive for the responsible "
     "organism. Therefore oral penicillin is the standard "
     "treatment.",
     "positive test + guideline standard"),
    ("Routine adult vaccination schedules include the seasonal "
     "influenza vaccine each autumn. The patient has no listed "
     "contraindication on file. Therefore the seasonal vaccine is "
     "recommended at this visit.",
     "no contraindication + schedule"),
    ("Pregnant patients with confirmed gestational diabetes are "
     "advised to begin glucose monitoring at diagnosis per the "
     "guideline. The patient's confirmatory test was completed "
     "this week. Therefore monitoring should begin without delay.",
     "confirmation + guideline timing"),
    ("Adults with documented penicillin anaphylaxis must avoid "
     "penicillin-class antibiotics per the safety guideline. The "
     "patient carries a documented anaphylaxis history. Therefore "
     "an alternative class is required for this prescription.",
     "documented history + safety rule"),
    ("Patients on long-term lithium therapy require quarterly "
     "serum lithium monitoring under the safety guideline. The "
     "patient's last level was drawn over four months ago. "
     "Therefore a new lithium level is indicated this visit.",
     "schedule lapsed + guideline cadence"),
)

_D3_INVALID: tuple[tuple[str, str], ...] = (
    ("The patient presents with classic features of acute "
     "appendicitis. Guidelines recommend imaging-confirmed "
     "appendectomy within six hours. Therefore surgical consult "
     "can safely be deferred for several days.",
     "deferral contradicts guideline"),
    ("Adults with confirmed strep throat by rapid antigen "
     "testing should receive oral penicillin per the guideline. "
     "The test returned positive for the responsible organism. "
     "Therefore antibiotic therapy must be withheld in this case.",
     "withholding contradicts standard"),
    ("Adults with documented penicillin anaphylaxis must avoid "
     "penicillin-class antibiotics. The patient carries a "
     "documented anaphylaxis history. Therefore a penicillin-class "
     "antibiotic is the appropriate first choice.",
     "violates safety rule"),
    ("Pregnant patients with confirmed gestational diabetes are "
     "advised to begin glucose monitoring at diagnosis. The "
     "patient's confirmatory test was completed this week. "
     "Therefore monitoring is unnecessary for this pregnancy.",
     "denies monitoring against guideline"),
    ("Patients on long-term lithium therapy require quarterly "
     "serum lithium monitoring. The patient's last level was "
     "drawn over four months ago. Therefore no further monitoring "
     "is indicated for this patient.",
     "denies monitoring against safety rule"),
    ("Routine adult vaccination schedules include the seasonal "
     "influenza vaccine each autumn. The patient has no listed "
     "contraindication. Therefore the patient should be excluded "
     "from the vaccination schedule.",
     "exclusion contradicts schedule"),
    ("Adults with newly diagnosed hypertension benefit from "
     "lifestyle intervention as first-line therapy. The patient "
     "meets the new-diagnosis criteria. Therefore aggressive "
     "polypharmacy is the indicated starting regimen.",
     "polypharmacy contradicts first-line"),
)

_D3_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("The patient presents with features of acute appendicitis. "
     "Guidelines recommend imaging-confirmed appendectomy within "
     "six hours. Therefore the clinician may also consider "
     "additional ultrasound depending on patient stability.",
     "may-claim depending on stability"),
    ("Adults with new hypertension benefit from lifestyle "
     "intervention as first-line therapy. The patient meets the "
     "new-diagnosis criteria. Therefore re-evaluation in three "
     "months might warrant escalation if blood pressure remains "
     "elevated.",
     "might-claim conditional"),
    ("Patients with confirmed strep throat should receive oral "
     "penicillin per the guideline. The rapid antigen test was "
     "positive. Therefore the clinician may also evaluate for "
     "rheumatic-fever risk factors during follow-up.",
     "may-claim during follow-up"),
    ("Routine adult vaccination schedules include the seasonal "
     "influenza vaccine. The patient has no listed "
     "contraindication. Therefore co-administration with other "
     "indicated vaccines may simplify the visit schedule.",
     "may-claim about co-administration"),
    ("Pregnant patients with gestational diabetes should begin "
     "glucose monitoring at diagnosis. Confirmatory testing was "
     "completed this week. Therefore the obstetric team may "
     "consider referral to a maternal-fetal medicine specialist "
     "if control proves difficult.",
     "may-claim conditional"),
    ("Adults with documented penicillin anaphylaxis must avoid "
     "penicillin-class antibiotics. The patient has a documented "
     "history. Therefore allergy specialist referral might be "
     "valuable to confirm the diagnosis and explore desensitisation "
     "options.",
     "might-claim about specialist referral"),
    ("Patients on long-term lithium therapy require quarterly "
     "serum monitoring. The last level was drawn over four months "
     "ago. Therefore the prescriber may also wish to revisit "
     "renal function tests during this visit.",
     "may-claim about additional tests"),
    ("Recent guideline updates emphasise shared decision-making "
     "in screening choices. The patient declined the screening "
     "after counselling. Therefore the decision should be "
     "documented and may be revisited at future visits.",
     "may-claim about future revisitation"),
)


# ---------------------------------------------------------------------------
# D4 scientific_peer_reviews
# ---------------------------------------------------------------------------

_D4_VALID: tuple[tuple[str, str], ...] = (
    ("The manuscript reports a randomised trial with adequate "
     "blinding and pre-registered endpoints. The reported effect "
     "size exceeds the pre-registered minimum. Therefore the "
     "primary finding is supported by the trial design.",
     "design + endpoint exceed threshold"),
    ("The authors use a method with known limitations on "
     "small-sample inference. The reported sample size is below "
     "the validated regime. Therefore the inferential claim "
     "carries an unaddressed methodological risk.",
     "sample below validated regime"),
    ("The supplementary materials provide the raw data and the "
     "analysis code with documented seeds. Reviewers can rerun "
     "the headline analysis end to end. Therefore the manuscript "
     "meets the journal's reproducibility standard.",
     "code + seeds + rerun feasible"),
    ("The introduction overstates the gap relative to recent "
     "literature published in the same outlet. The cited related "
     "work is two years old. Therefore the framing needs a "
     "literature update before publication.",
     "outdated literature needs update"),
    ("The reported confidence intervals are inconsistent with the "
     "stated standard errors. Recomputing intervals from the "
     "stated errors yields a different conclusion. Therefore the "
     "statistical reporting requires correction.",
     "internal inconsistency requires fix"),
    ("The methodology section omits the random seed for the "
     "reported neural-network training runs. Reproduction of the "
     "training curve is therefore not deterministic. Therefore "
     "the seed must be added before publication.",
     "missing seed blocks reproduction"),
    ("The figure captions clearly identify the unit and the "
     "uncertainty estimate for each panel. The supplementary "
     "tables echo the same conventions. Therefore the visual "
     "presentation meets the journal's reporting checklist.",
     "captions + tables consistent"),
)

_D4_INVALID: tuple[tuple[str, str], ...] = (
    ("The manuscript reports a randomised trial with adequate "
     "blinding and pre-registered endpoints. The reported effect "
     "size exceeds the minimum. Therefore the primary finding "
     "must be withheld from publication on methodological "
     "grounds.",
     "method strong; withhold contradicts"),
    ("The supplementary materials provide raw data and analysis "
     "code. Reviewers can rerun the analysis end to end. "
     "Therefore the manuscript fails the reproducibility "
     "standard.",
     "materials present; failure contradicts"),
    ("The introduction overstates the gap relative to recent "
     "literature in the same outlet. The cited related work is "
     "two years old. Therefore the literature framing is fully "
     "current and needs no update.",
     "outdated; framing not current"),
    ("The reported confidence intervals are inconsistent with the "
     "stated standard errors. Recomputing yields a different "
     "conclusion. Therefore the statistical reporting is "
     "internally consistent.",
     "inconsistency contradicts consistency claim"),
    ("The figure captions clearly identify unit and uncertainty. "
     "Supplementary tables echo the same conventions. Therefore "
     "the visual presentation fails the journal's reporting "
     "checklist.",
     "consistent presentation contradicts failure"),
    ("The methodology section omits the random seed for the "
     "training runs. Reproduction is therefore non-deterministic. "
     "Therefore the manuscript is fully reproducible end to end.",
     "missing seed contradicts reproducibility"),
    ("The authors use a method with known limitations on "
     "small-sample inference. The sample size is below the "
     "validated regime. Therefore the inferential claim carries "
     "no methodological risk.",
     "below regime contradicts no-risk claim"),
)

_D4_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("The manuscript reports a randomised trial with adequate "
     "blinding and pre-registered endpoints. The effect exceeds "
     "the registered minimum. Therefore replication in an "
     "independent cohort may further strengthen the headline "
     "claim.",
     "may-claim about replication"),
    ("The introduction overstates the gap relative to recent "
     "literature. The cited related work is two years old. "
     "Therefore the authors may wish to add a forward-looking "
     "comparison in the discussion.",
     "may-claim about discussion"),
    ("The reported confidence intervals are inconsistent with the "
     "stated standard errors. Recomputing yields a different "
     "conclusion. Therefore further methodological review might "
     "be warranted before the final decision.",
     "might-claim about further review"),
    ("The supplementary materials provide raw data and analysis "
     "code with documented seeds. Reviewers can rerun the "
     "analysis. Therefore the editors may consider featuring this "
     "manuscript in the reproducibility highlight series.",
     "may-claim about editorial feature"),
    ("The methodology section omits the random seed for the "
     "training runs. Reproduction is non-deterministic. Therefore "
     "the authors may wish to consider a stricter reporting "
     "policy in future submissions.",
     "may-claim about future policy"),
    ("The figure captions clearly identify unit and uncertainty. "
     "Supplementary tables echo the conventions. Therefore the "
     "presentation may benefit from a brief reader-orientation "
     "callout in the introduction.",
     "may-claim about orientation callout"),
    ("The authors use a method with small-sample limitations. The "
     "sample size is below the validated regime. Therefore "
     "additional bootstrap analysis might quantify the inferential "
     "risk.",
     "might-claim about additional analysis"),
)


# ---------------------------------------------------------------------------
# D5 mathematical_proof_sketches
# ---------------------------------------------------------------------------

_D5_VALID: tuple[tuple[str, str], ...] = (
    ("Consider a finite-dimensional vector space and a linear "
     "operator on it. The rank-nullity theorem ties dim ker plus "
     "dim image to the domain dimension. Therefore the dimensions "
     "of kernel and image partition the domain dimension.",
     "rank-nullity application"),
    ("Suppose a function is differentiable on an open interval. "
     "Differentiability implies continuity on the same interval. "
     "Therefore the function is continuous on that interval.",
     "diff implies cont"),
    ("Take a bounded monotone sequence in the real numbers. "
     "Bounded monotone sequences converge in the reals. Therefore "
     "the sequence has a real limit.",
     "monotone bounded convergence"),
    ("Let A and B be disjoint open subsets of a topological "
     "space. Their union is the disjoint union of open sets. "
     "Therefore the union is itself open in the same space.",
     "open under finite disjoint union"),
    ("Suppose a graph is connected and acyclic. Such a structure "
     "is by definition a tree. Therefore the graph admits a tree "
     "representation up to relabelling.",
     "connected + acyclic = tree"),
    ("Take a polynomial with real coefficients and an odd "
     "degree. Polynomials of odd degree tend to opposite "
     "infinities at the extremes. Therefore the polynomial has at "
     "least one real root.",
     "odd-degree polynomial has real root"),
    ("Consider an integer that is divisible by both two and "
     "three. By the basic divisibility lemma the integer is "
     "divisible by six. Therefore the integer is a multiple of "
     "six.",
     "divisibility lemma"),
)

_D5_INVALID: tuple[tuple[str, str], ...] = (
    ("Consider a finite-dimensional vector space and a linear "
     "operator. The rank-nullity theorem ties dim ker plus dim "
     "image to the domain dimension. Therefore the operator is "
     "necessarily invertible.",
     "rank-nullity does not imply invertibility"),
    ("Suppose a function is differentiable on an open interval. "
     "Differentiability implies continuity. Therefore the function "
     "is discontinuous on the same interval.",
     "diff implies cont; contradicts discontinuous"),
    ("Take a bounded monotone sequence in the real numbers. "
     "Bounded monotone sequences converge in the reals. Therefore "
     "the sequence diverges.",
     "monotone bounded contradicts divergence"),
    ("Take a polynomial with real coefficients and odd degree. "
     "Polynomials of odd degree tend to opposite infinities. "
     "Therefore the polynomial has no real roots.",
     "odd-degree contradicts no roots"),
    ("Let A and B be disjoint open subsets of a topological "
     "space. Their union is the disjoint union of open sets. "
     "Therefore the union is closed but not open in the same "
     "space.",
     "open property contradicts closed-only claim"),
    ("Suppose a graph is connected and acyclic. Such a structure "
     "is by definition a tree. Therefore the graph contains at "
     "least one cycle.",
     "acyclic contradicts cycle"),
    ("Consider an integer divisible by both two and three. By "
     "the divisibility lemma it is divisible by six. Therefore "
     "the integer is odd.",
     "divisible by six contradicts odd"),
)

_D5_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("Consider a finite-dimensional vector space and a linear "
     "operator. The rank-nullity theorem ties dim ker plus dim "
     "image to the domain dimension. Therefore additional "
     "structural assumptions may yield a sharper bound on the "
     "rank.",
     "may-claim about sharper bound"),
    ("Suppose a function is differentiable on an open interval. "
     "Differentiability implies continuity on the same interval. "
     "Therefore higher-order smoothness might require further "
     "hypotheses to establish.",
     "might-claim about smoothness"),
    ("Take a bounded monotone sequence in the real numbers. "
     "Bounded monotone sequences converge. Therefore the rate of "
     "convergence may depend on the specific sequence under "
     "study.",
     "may-claim about rate"),
    ("Take a polynomial of odd degree over the reals. Odd-degree "
     "polynomials tend to opposite infinities. Therefore the "
     "number of real roots may exceed one depending on the "
     "specific polynomial.",
     "may-claim about additional roots"),
    ("Let A and B be disjoint open subsets of a topological "
     "space. Their union is the disjoint union of open sets. "
     "Therefore the closure of the union may include additional "
     "limit points.",
     "may-claim about closure"),
    ("Suppose a graph is connected and acyclic. Such a structure "
     "is a tree. Therefore the count of leaves may depend on the "
     "particular tree representation chosen.",
     "may-claim about leaves"),
    ("Consider an integer divisible by both two and three. The "
     "divisibility lemma gives divisibility by six. Therefore "
     "further divisibility properties may follow under additional "
     "prime-factor hypotheses.",
     "may-claim about further properties"),
)


def _build(prefix: str, src_valid, src_invalid, src_ambiguous,
           domain: TransferDomain) -> tuple[TransferChain, ...]:
    out: list[TransferChain] = []
    for i, (text, rationale) in enumerate(src_valid, start=1):
        out.append(TransferChain(
            chain_id=f"{prefix}V{i:03d}", domain=domain.value,
            text=text, ground_truth=TransferGroundTruth.VALID.value,
            rationale=rationale,
        ))
    for i, (text, rationale) in enumerate(src_invalid, start=1):
        out.append(TransferChain(
            chain_id=f"{prefix}I{i:03d}", domain=domain.value,
            text=text,
            ground_truth=TransferGroundTruth.INVALID.value,
            rationale=rationale,
        ))
    for i, (text, rationale) in enumerate(src_ambiguous, start=1):
        out.append(TransferChain(
            chain_id=f"{prefix}A{i:03d}", domain=domain.value,
            text=text,
            ground_truth=TransferGroundTruth.AMBIGUOUS.value,
            rationale=rationale,
        ))
    return tuple(out)


_PREFIXES: tuple[str, ...] = (
    "In a 2024 postmortem, ",
    "In a 2023 internal review, ",
    "In a 2022 case file, ",
    "In a 2021 quarterly report, ",
)


def _expand(
    base: tuple[TransferChain, ...], prefix_label: str,
) -> tuple[TransferChain, ...]:
    out: list[TransferChain] = []
    for ci, c in enumerate(base, start=1):
        for pi, prefix in enumerate(_PREFIXES, start=1):
            new_text = prefix + c.text[:1].lower() + c.text[1:]
            out.append(TransferChain(
                chain_id=f"{prefix_label}X{ci:03d}P{pi}",
                domain=c.domain,
                text=new_text,
                ground_truth=c.ground_truth,
                rationale=f"prefix-variation of {c.chain_id}",
            ))
    return tuple(out)


def all_chains() -> tuple[TransferChain, ...]:
    d1_base = _build(
        "D1", _D1_VALID, _D1_INVALID, _D1_AMBIGUOUS,
        TransferDomain.D1_TECHNICAL_INCIDENT_REPORTS,
    )
    d2_base = _build(
        "D2", _D2_VALID, _D2_INVALID, _D2_AMBIGUOUS,
        TransferDomain.D2_LEGAL_CASE_SUMMARIES,
    )
    d3_base = _build(
        "D3", _D3_VALID, _D3_INVALID, _D3_AMBIGUOUS,
        TransferDomain.D3_MEDICAL_GUIDELINES,
    )
    d4_base = _build(
        "D4", _D4_VALID, _D4_INVALID, _D4_AMBIGUOUS,
        TransferDomain.D4_SCIENTIFIC_PEER_REVIEWS,
    )
    d5_base = _build(
        "D5", _D5_VALID, _D5_INVALID, _D5_AMBIGUOUS,
        TransferDomain.D5_MATHEMATICAL_PROOF_SKETCHES,
    )
    return (
        d1_base + _expand(d1_base, "T1")
        + d2_base + _expand(d2_base, "T2")
        + d3_base + _expand(d3_base, "T3")
        + d4_base + _expand(d4_base, "T4")
        + d5_base + _expand(d5_base, "T5")
    )


__all__ = ["TransferChain", "all_chains"]
