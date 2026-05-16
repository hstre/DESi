"""Aufgabe 4 — new v5.2 evaluation corpus.

Five adjacent domains:

* D1 ``postmortem_engineering``   (adjacent to v5.0 technical
                                   incident reports)
* D2 ``appellate_legal``          (adjacent to v5.0 legal
                                   case summaries)
* D3 ``clinical_protocols``       (adjacent to v5.0 medical
                                   guidelines)
* D4 ``peer_review_rebuttal``     (adjacent to v5.0
                                   scientific peer reviews)
* D5 ``theorem_review``           (adjacent to v5.0
                                   mathematical proof
                                   sketches)

Each domain contributes at least one hundred chains
(roughly twenty-five base chains expanded with four framing
variants). The corpus is balanced across VALID / INVALID /
AMBIGUOUS within ±20% of the mean. No v5.0 corpus chain is
reused.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import GeneralizationDomain


@dataclass(frozen=True)
class GeneralizationChain:
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
# D1 postmortem_engineering
# ---------------------------------------------------------------------------

_D1_VALID: tuple[tuple[str, str], ...] = (
    ("The postmortem documented a sustained increase in "
     "memory pressure following the cache size change. "
     "Operators reverted the cache size in the next "
     "deploy. Therefore the revert restored memory pressure "
     "to the prior baseline.",
     "revert correlates with restored memory pressure"),
    ("The incident review found a thread leak in the "
     "service after the upgrade. The team applied a "
     "targeted patch within the same window. Therefore "
     "the regression no longer appeared in subsequent "
     "diagnostic runs.",
     "patch correlates with leak closure"),
    ("The review surfaced a slow query introduced by the "
     "schema migration. The DBA added a covering index "
     "during the maintenance window. Therefore p99 "
     "response timing improved across the next sampling "
     "epoch.",
     "index correlates with latency drop"),
    ("Pager noise rose after the new alert rule shipped. "
     "Engineering tuned the threshold to a higher value. "
     "Therefore on-call interrupt volume fell during the "
     "subsequent rotation.",
     "threshold tuning reduced noise"),
    ("The postmortem identified a stale cache as the "
     "source of inconsistent reads. The team shortened "
     "the TTL on the affected key. Therefore consistency "
     "metrics held within tolerance through the next "
     "observation window.",
     "shorter TTL eliminated inconsistency"),
    ("The review traced a request retry storm to a missing "
     "circuit breaker. The team added a circuit breaker "
     "in the next deploy. Therefore amplification events "
     "stayed below the alarm threshold during the "
     "validation interval.",
     "circuit breaker limited retries"),
    ("Throughput dropped after the worker pool size was "
     "halved. The platform team restored the original "
     "pool size. Therefore the previous performance "
     "envelope returned within the validation interval.",
     "pool restoration returned throughput"),
    ("Background indexing fell behind after the disk "
     "saturated. Operators expanded the disk and resumed "
     "the indexer. Therefore queue backlog returned to "
     "its prior baseline within the monitored window.",
     "disk expansion enabled indexer catch-up"),
    ("The postmortem traced response failures to a "
     "stalled background job. Engineering restarted the "
     "scheduler and replayed the queue. Therefore "
     "downstream availability returned to its prior "
     "envelope within the observed interval.",
     "replay drained queue"),
)

_D1_INVALID: tuple[tuple[str, str], ...] = (
    ("The postmortem documented a memory-pressure spike "
     "during the deploy. Operators reverted the cache "
     "change in the next deploy. Therefore for every "
     "service deployed that week the team will issue a "
     "permanent rewrite.",
     "no support for permanent rewrite"),
    ("The review surfaced a slow query after the schema "
     "migration. The DBA added a covering index. Therefore "
     "the schema migration will produce a latency "
     "regression for every comparable service.",
     "single-cause overreach"),
    ("Pager noise rose after the new alert rule shipped. "
     "Engineering tuned the threshold. Therefore for "
     "every alert rule the company ships from now on the "
     "tuning will produce no noise at any threshold.",
     "every-rule overreach"),
    ("The team patched a thread leak during the incident. "
     "Therefore the engineering organisation cannot ever "
     "experience a thread leak again across every future "
     "release window.",
     "absolute future claim unsupported"),
    ("The postmortem identified a stale cache. The TTL "
     "was shortened. Therefore the cache layer will be "
     "removed from every service across the platform "
     "without further audit, and any objection is denied "
     "by the team's prior writeup.",
     "removal claim unsupported"),
    ("Throughput dropped after halving the worker pool. "
     "The pool size was restored. Therefore the recovery "
     "will prove the original sizing decision was a "
     "deliberate act of sabotage across every audit "
     "review.",
     "no support for sabotage attribution"),
    ("Background indexing fell behind during disk "
     "saturation. The disk was expanded. Therefore the "
     "operations team's storage strategy will be named "
     "the singular cause for every incident logged that "
     "quarter.",
     "no single-cause warrant"),
    ("Retry storms surfaced from a missing circuit "
     "breaker. A breaker was added. Therefore the "
     "addition will prove the team's earlier risk "
     "assessment was uniformly negligent across every "
     "comparable review.",
     "no support for negligence verdict"),
    ("The scheduler was restarted after the stalled "
     "background job. Therefore the engineering "
     "organisation will be judged incompetent in "
     "scheduler design across every future review.",
     "no support for competence claim"),
)

_D1_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("The postmortem documented a memory-pressure spike "
     "after the cache size change. Operators reverted "
     "the change. Therefore the cache change may have "
     "contributed to the memory pressure observed in the "
     "incident.",
     "hedged contributing cause"),
    ("The review found a thread leak after the upgrade. "
     "A patch was applied. Therefore the upgrade might "
     "have introduced the leak, though other factors "
     "could also be responsible.",
     "hedged cause attribution"),
    ("The postmortem traced a slow query to the migration. "
     "The DBA added an index. Therefore the migration "
     "could be one of several contributors to the "
     "observed latency regression.",
     "non-unique contributor"),
    ("Pager noise increased after the alert rule shipped. "
     "Thresholds were tuned. Therefore the rule may "
     "require periodic tuning across teams in similar "
     "environments.",
     "hedged generalisation"),
    ("Throughput fell after halving the worker pool. The "
     "pool was restored. Therefore the original pool "
     "size might have been near the safe lower bound.",
     "hedged safe-bound claim"),
    ("The postmortem found a stale cache caused "
     "inconsistent reads. The TTL was shortened. "
     "Therefore shorter TTLs could reduce inconsistency "
     "but may increase backend load.",
     "trade-off acknowledged"),
    ("The team added a circuit breaker after retry storms. "
     "Therefore the breaker may have helped under the "
     "observed traffic shape, though heavier traffic "
     "could still produce storms.",
     "load-dependent hedge"),
    ("Background indexing recovered after disk expansion. "
     "Therefore additional capacity may delay future "
     "saturation but cannot guarantee that no future "
     "incident will occur.",
     "no certainty hedge"),
    ("The scheduler restart drained the queue in the "
     "observed window. Therefore the restart may have "
     "helped under the observed load, though heavier "
     "workloads could still stall the scheduler.",
     "hedged load-dependent recovery"),
)


# ---------------------------------------------------------------------------
# D2 appellate_legal
# ---------------------------------------------------------------------------

_D2_VALID: tuple[tuple[str, str], ...] = (
    ("The trial court admitted the disputed exhibit over "
     "objection. The appellate panel reviewed the "
     "evidentiary ruling under the abuse-of-discretion "
     "standard. Therefore the appellate panel applied the "
     "standard the rule of evidence prescribes.",
     "standard application warranted"),
    ("The plaintiff preserved the constitutional issue at "
     "trial. The appellate court reviewed the issue de "
     "novo. Therefore the de novo review followed from "
     "the preservation of the constitutional question.",
     "preservation triggers de novo"),
    ("The opinion below relied on a statute later "
     "repealed. The appellate court remanded for "
     "reconsideration under the current statute. "
     "Therefore the remand follows from the change in "
     "governing law.",
     "remand follows from statutory change"),
    ("The record showed a procedural default at the "
     "objection stage. The appellate panel applied "
     "plain-error review. Therefore preservation "
     "doctrine governed the standard of analysis on "
     "appeal.",
     "default triggers plain-error"),
    ("The appellate court applied the contemporaneous "
     "interpretive canon to the disputed statutory term. "
     "The lower court had applied a later interpretation. "
     "Therefore the contemporaneous canon governed the "
     "reading of the term in the case under review.",
     "canon governs reading"),
    ("The party requested oral argument on a question of "
     "first impression. The appellate court granted "
     "argument and circulated focus letters. Therefore "
     "the focus-letter process followed the court's "
     "standing rules for first-impression cases.",
     "process follows standing rules"),
    ("Counsel moved for rehearing en banc within the "
     "filing window. The court granted the motion under "
     "its discretionary rule. Therefore the grant of "
     "rehearing followed the discretionary criteria.",
     "discretionary grant supported"),
    ("The appellate panel found the lower court's record "
     "incomplete on a material point. The panel "
     "remanded for supplementation. Therefore the remand "
     "followed from the identified incompleteness.",
     "remand follows from incompleteness"),
    ("The dissenting opinion cited a prior holding the "
     "majority did not address. The majority opinion "
     "issued an addendum responding to the citation. "
     "Therefore the responsive supplement clarified the "
     "court's treatment of the earlier authority.",
     "addendum addressed citation"),
)

_D2_INVALID: tuple[tuple[str, str], ...] = (
    ("The trial court admitted the disputed exhibit. The "
     "appellate panel reviewed under abuse-of-discretion. "
     "Therefore for every evidentiary ruling in every "
     "future case the courts will apply the same "
     "standard.",
     "single-case overreach"),
    ("The appellate court remanded after the statute was "
     "repealed. Therefore across every remand in the "
     "jurisdiction's history the prior outcome will be "
     "retroactively vacated.",
     "no warrant for retroactive vacatur"),
    ("The court applied plain-error review after a "
     "procedural default. Therefore the trial counsel "
     "will be found to have committed malpractice for "
     "every comparable filing in the future.",
     "no warrant for malpractice"),
    ("The contemporaneous interpretive canon governed "
     "the disputed term. Therefore across every prior "
     "decision interpreting that term the holding will "
     "be overruled by operation of law.",
     "no automatic overruling"),
    ("The court granted oral argument in a "
     "first-impression case. Therefore for every party "
     "in every case the court will grant oral argument "
     "on demand.",
     "no entitlement claim"),
    ("Counsel won rehearing en banc. Therefore counsel "
     "will be shown to have engaged in improper ex parte "
     "contact across every comparable matter on the "
     "docket.",
     "no warrant for impropriety"),
    ("The panel found the record incomplete. Therefore "
     "the entire docket of the lower court will be "
     "reviewed for record integrity across every matter "
     "filed in the same period.",
     "no warrant for docket-wide review"),
    ("The de novo review followed a preserved "
     "constitutional issue. Therefore for every party "
     "that raises a constitutional issue the court will "
     "grant de novo review across every other claim.",
     "no spillover entitlement"),
    ("The majority issued an addendum responding to a "
     "cited dissenting authority. Therefore for every "
     "dissenting citation the court will require an "
     "addendum from every majority opinion in every "
     "court.",
     "no warrant for universal addendum rule"),
)

_D2_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("The trial court admitted the disputed exhibit. The "
     "appellate panel applied abuse-of-discretion review. "
     "Therefore the standard may have produced a "
     "different result under a stricter review level.",
     "hedged counterfactual"),
    ("The appellate court remanded after the statute "
     "was repealed. Therefore the remand might also "
     "affect related claims pending in similar matters.",
     "hedged spillover"),
    ("The court applied plain-error review after the "
     "default. Therefore the standard could shift the "
     "outcome compared with full review.",
     "hedged outcome shift"),
    ("The contemporaneous canon governed the term. "
     "Therefore similar terms in adjacent statutes "
     "could attract the same canon in future cases.",
     "hedged extension"),
    ("Oral argument was granted on the first-impression "
     "question. Therefore the panel may set persuasive "
     "guidance for adjacent open questions.",
     "hedged guidance forecast"),
    ("Counsel obtained rehearing en banc. Therefore the "
     "court may reconsider the prior panel's reasoning "
     "without necessarily reversing it.",
     "reconsideration not equal to reversal"),
    ("The panel found the record incomplete. Therefore "
     "supplementation could clarify the disputed point "
     "though it may not resolve it.",
     "hedged resolution"),
    ("The de novo review followed preservation. Therefore "
     "the appellate court might reach a different "
     "conclusion than the trial court.",
     "hedged divergence"),
    ("The majority addendum responded to the dissent's "
     "citation. Therefore subsequent panels may consider "
     "the addendum reasoning, though weight could vary "
     "across courts.",
     "hedged weight variation"),
)


# ---------------------------------------------------------------------------
# D3 clinical_protocols
# ---------------------------------------------------------------------------

_D3_VALID: tuple[tuple[str, str], ...] = (
    ("The clinical protocol specified initiating therapy "
     "after two consecutive elevated readings. The "
     "patient's chart shows three consecutive elevated "
     "readings. Therefore the chart satisfies the "
     "protocol's initiation criterion.",
     "criterion satisfied"),
    ("The protocol mandates referral when symptoms persist "
     "beyond two weeks. The patient's symptom log "
     "spans three weeks of persistence. Therefore the "
     "documented duration meets the published threshold "
     "for onward consultation.",
     "referral triggered"),
    ("The protocol requires documenting allergy history "
     "before initial dosing. The clinician documented "
     "the history in the intake note. Therefore the "
     "intake documentation satisfied the protocol's "
     "pre-dosing requirement.",
     "pre-dosing requirement met"),
    ("The treatment guideline specifies tapering over "
     "four weeks when initial response is observed. The "
     "patient's chart shows initial response at week "
     "two. Therefore the documented improvement satisfies "
     "the published threshold for dose reduction.",
     "tapering schedule triggered"),
    ("The protocol calls for follow-up imaging at "
     "twelve weeks post-procedure. The follow-up imaging "
     "was scheduled within that window. Therefore the "
     "patient's care plan satisfies the published "
     "scheduling rule for surveillance review.",
     "follow-up window observed"),
    ("The protocol requires baseline laboratory values "
     "before adjustment. Baseline values were drawn at "
     "the visit preceding the adjustment. Therefore the "
     "draw satisfied the baseline requirement.",
     "baseline requirement met"),
    ("The guideline lists three contraindications for "
     "the agent. The patient's record reflects none of "
     "the listed contraindications. Therefore the agent "
     "is not contraindicated in this patient's case.",
     "contraindications absent"),
    ("The protocol specifies discontinuation when an "
     "adverse event of the listed grade occurs. The "
     "adverse-event report documents an event of that "
     "grade. Therefore the documented finding satisfies "
     "the published threshold for stopping the agent.",
     "discontinuation criterion met"),
    ("The protocol mandates dose adjustment when renal "
     "clearance falls below the listed threshold. The "
     "patient's clearance reading was below the "
     "threshold. Therefore the reading triggers the "
     "dose-adjustment requirement under the protocol.",
     "adjustment triggered by clearance"),
)

_D3_INVALID: tuple[tuple[str, str], ...] = (
    ("The protocol specifies initiating therapy after two "
     "elevated readings. The chart shows three. Therefore "
     "every patient on the cohort will respond identically "
     "to therapy across every comparable arm.",
     "no warrant for uniform response"),
    ("The protocol mandates referral after two weeks of "
     "persistence. The patient's symptoms persisted "
     "three weeks. Therefore for every clinic in the "
     "network the operations team will double its "
     "referral capacity.",
     "no warrant for capacity claim"),
    ("Allergy history was documented before initial "
     "dosing. Therefore the intake form will capture "
     "every relevant adverse reaction history for every "
     "patient in the population.",
     "no warrant for completeness"),
    ("The guideline specifies tapering over four weeks. "
     "Therefore across every adjustment in clinical "
     "practice the clinician will apply the same "
     "four-week tapering window.",
     "no warrant for uniform tapering"),
    ("Follow-up imaging was scheduled at twelve weeks. "
     "Therefore the imaging suite will double its "
     "capacity to accommodate every patient on the "
     "guideline.",
     "no warrant for capacity doubling"),
    ("Baseline values were drawn before adjustment. "
     "Therefore the laboratory's testing volume will "
     "increase across every department.",
     "no warrant for department-wide change"),
    ("The patient lacked listed contraindications. "
     "Therefore the agent will be uniformly safe across "
     "every patient in the population and the "
     "contraindication list will be retired.",
     "no warrant for retiring contraindications"),
    ("The adverse event met the discontinuation "
     "criterion. Therefore the agent will be withdrawn "
     "from every market in the region.",
     "no warrant for market withdrawal"),
    ("The clearance reading triggered the dose "
     "adjustment. Therefore every patient on the agent "
     "will immediately have their dose halved regardless "
     "of clearance.",
     "no warrant for uniform halving"),
)

_D3_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("The protocol specifies initiating therapy after "
     "two elevated readings. The chart shows three. "
     "Therefore initiation may have been timely, though "
     "the protocol allows clinical judgement on "
     "borderline cases.",
     "hedged borderline judgement"),
    ("The patient's symptoms persisted three weeks. The "
     "protocol mandates referral after two. Therefore "
     "the referral might also be appropriate slightly "
     "earlier depending on severity.",
     "hedged earlier referral"),
    ("Allergy history was documented at intake. Therefore "
     "the documentation may be sufficient, though "
     "additional history could surface in later visits.",
     "hedged completeness"),
    ("The protocol calls for four-week tapering after "
     "initial response. Therefore tapering could be "
     "extended in patients with delayed clearance "
     "metrics.",
     "hedged extension"),
    ("Follow-up imaging was scheduled at twelve weeks. "
     "Therefore the imaging may capture the expected "
     "change, though anatomic variation could shift the "
     "interpretation.",
     "hedged interpretation"),
    ("Baseline labs were drawn before adjustment. "
     "Therefore the baseline may be representative, "
     "though within-day variability could affect the "
     "reading.",
     "hedged representativeness"),
    ("The contraindications listed are absent from the "
     "record. Therefore the agent might be appropriate, "
     "though comorbidity considerations could modify "
     "the choice.",
     "hedged appropriateness"),
    ("The adverse event meets the discontinuation grade. "
     "Therefore discontinuation may be indicated, though "
     "the clinician could weigh alternative regimens "
     "with comparable risk profiles.",
     "hedged discontinuation"),
    ("The clearance reading fell below the listed "
     "threshold. Therefore dose adjustment may be "
     "appropriate, though the clinician could consider "
     "rechecking with a fasting sample.",
     "hedged recheck"),
)


# ---------------------------------------------------------------------------
# D4 peer_review_rebuttal
# ---------------------------------------------------------------------------

_D4_VALID: tuple[tuple[str, str], ...] = (
    ("Reviewer two requested clarification of the "
     "preprocessing pipeline. The authors added a "
     "subsection describing each step. Therefore the "
     "manuscript now exposes the pipeline detail the "
     "report flagged as insufficient.",
     "rebuttal addresses request"),
    ("Reviewer one identified a missing baseline. The "
     "authors added the baseline in a revised table. "
     "Therefore the manuscript now reports the comparator "
     "the report flagged as omitted.",
     "table supplies missing baseline"),
    ("Reviewer three asked for an ablation of the "
     "attention layer. The authors included a new "
     "ablation table in the appendix. Therefore the "
     "manuscript now exposes the layer-isolation result "
     "the report had asked for.",
     "appendix addresses ablation"),
    ("Reviewer two raised a question about evaluation "
     "metrics. The authors added per-metric definitions "
     "to the methodology section. Therefore the "
     "manuscript now exposes the formal scoring detail "
     "the report had flagged as missing.",
     "definitions answer clarification"),
    ("Reviewer one requested a literature comparison. "
     "The authors added a comparison table citing five "
     "prior works. Therefore the manuscript now "
     "situates its contribution within the published "
     "context the report had flagged as missing.",
     "table addresses comparison"),
    ("Reviewer three flagged a missing standard "
     "deviation. The revision added standard deviations "
     "to every reported number. Therefore the manuscript "
     "now exposes the dispersion estimates the report "
     "had asked for.",
     "values supplied"),
    ("Reviewer two questioned a claim's generalisation. "
     "The authors qualified the assertion and added "
     "boundary conditions. Therefore the manuscript now "
     "circumscribes the assertion within the limits the "
     "report had flagged.",
     "qualification narrows scope"),
    ("Reviewer one asked for runtime measurements. The "
     "authors added a benchmark table with timing "
     "results. Therefore the manuscript now exposes the "
     "execution-cost data the report had asked for.",
     "benchmark provides timing"),
    ("Reviewer two requested a confusion matrix at the "
     "evaluation split. The authors added the matrix "
     "in the appendix. Therefore the manuscript now "
     "exposes the per-class error breakdown the report "
     "had asked for.",
     "appendix addresses request"),
)

_D4_INVALID: tuple[tuple[str, str], ...] = (
    ("Reviewer two requested preprocessing clarification. "
     "The authors added the description. Therefore for "
     "every reviewer of every future submission the "
     "description will be found sufficient.",
     "no warrant for uniform sufficiency"),
    ("The authors added a missing baseline. Therefore "
     "the field will be shown to have neglected "
     "baselines as a category across every venue for "
     "the past decade.",
     "no warrant for decadal claim"),
    ("The authors added an ablation table. Therefore for "
     "every paper without ablations the venue will issue "
     "a retraction.",
     "no warrant for mass retraction"),
    ("Per-metric definitions were added. Therefore "
     "across every metric debate in the literature the "
     "definitions will settle the question.",
     "no warrant for universal settlement"),
    ("The literature comparison table was added. "
     "Therefore the authors' approach will be superior "
     "to every cited prior work in every downstream "
     "task.",
     "no warrant for universal superiority"),
    ("Standard deviations were added. Therefore the "
     "results will be beyond methodological critique "
     "across every venue and for every reviewer.",
     "no warrant for immunity"),
    ("The scope qualification was added. Therefore the "
     "qualification will prove that for every prior "
     "unqualified claim in the field the authors were "
     "intentionally misleading.",
     "no warrant for intent claim"),
    ("Runtime measurements were added. Therefore the "
     "approach will run faster than every method across "
     "every deployment environment.",
     "no warrant for universal speed"),
    ("The confusion matrix was added. Therefore for "
     "every future submission the venue will require a "
     "confusion matrix at every reported split without "
     "exception.",
     "no warrant for universal requirement"),
)

_D4_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("Reviewer two requested preprocessing clarification. "
     "The authors added a description. Therefore the "
     "addition may satisfy reviewer two's request, "
     "though additional detail could be requested in a "
     "future round.",
     "hedged sufficiency"),
    ("The missing baseline was added. Therefore the "
     "baseline might be sufficient, though additional "
     "comparison points could strengthen the table.",
     "hedged completeness"),
    ("The ablation table was added. Therefore the "
     "ablation may answer reviewer three's question, "
     "though further factorisation could be explored.",
     "hedged further analysis"),
    ("Per-metric definitions were added. Therefore the "
     "definitions could clarify the metric debate, "
     "though edge cases may remain.",
     "hedged remaining ambiguity"),
    ("The literature comparison was added. Therefore the "
     "comparison may be representative, though selection "
     "bias could affect the chosen cohort.",
     "hedged selection-bias"),
    ("Standard deviations were added. Therefore the "
     "values might enable more meaningful comparison, "
     "though the underlying distributional assumptions "
     "could warrant scrutiny.",
     "hedged distributional caveat"),
    ("A scope qualification was added. Therefore the "
     "qualification may narrow the claim appropriately, "
     "though boundary cases could still attract review.",
     "hedged boundary handling"),
    ("Runtime measurements were added. Therefore the "
     "measurements could enable runtime comparison, "
     "though hardware variability may complicate "
     "interpretation.",
     "hedged variability"),
    ("The confusion matrix was added at the evaluation "
     "split. Therefore the matrix may clarify the error "
     "distribution, though additional splits could "
     "reveal complementary patterns.",
     "hedged complementary insight"),
)


# ---------------------------------------------------------------------------
# D5 theorem_review
# ---------------------------------------------------------------------------

_D5_VALID: tuple[tuple[str, str], ...] = (
    ("The submitted proof invokes the dominated "
     "convergence theorem on a sequence bounded by an "
     "integrable function. The reviewer verified the "
     "bounding assumption on the supporting line. "
     "Therefore the interchange of limit and integral "
     "carries through under the checked assumption.",
     "hypothesis supports invocation"),
    ("The proof relies on a closed-form identity proved "
     "in an earlier lemma. The reviewer confirmed the "
     "earlier statement matches the present usage. "
     "Therefore the cited equality carries through "
     "where the argument requires it.",
     "lemma supplies identity"),
    ("The induction step uses a strict inequality at the "
     "inductive hypothesis. The reviewer confirmed the "
     "antecedent carries the same strictness. Therefore "
     "the recurrence advances under a premise the panel "
     "has independently verified.",
     "inductive hypothesis verified"),
    ("The proof appeals to a uniqueness theorem under "
     "specific regularity conditions. The reviewer "
     "checked the listed hypotheses on the prior page. "
     "Therefore the appeal to the cited theorem stands "
     "on assumptions the panel has confirmed.",
     "regularity supports appeal"),
    ("The argument substitutes a series expansion valid "
     "on a specified disk. The reviewer checked that the "
     "substitution remains inside the disk. Therefore "
     "the substitution respects the convergence "
     "constraint of the expansion.",
     "substitution respects constraint"),
    ("The proof invokes Fubini's theorem on a product of "
     "sigma-finite measure spaces. The reviewer "
     "confirmed sigma-finiteness on each factor. "
     "Therefore the invocation of Fubini follows from "
     "the verified sigma-finiteness conditions.",
     "Fubini follows from sigma-finiteness"),
    ("The proof uses a fixed-point theorem under "
     "continuity assumptions. The reviewer verified the "
     "mapping behaves smoothly on the relevant compact "
     "set. Therefore the existence claim stands on a "
     "hypothesis the panel has confirmed.",
     "fixed point follows from continuity"),
    ("The induction base case is checked at n equals "
     "two. The reviewer confirmed the initial "
     "computation. Therefore the recurrence advances "
     "from the smallest index forward as written.",
     "base case supports induction"),
    ("The proof invokes the mean value theorem on a "
     "function shown differentiable on the open "
     "interval. The reviewer confirmed smoothness across "
     "the relevant domain. Therefore the cited theorem "
     "applies under hypotheses the panel has confirmed.",
     "MVT applies as verified"),
)

_D5_INVALID: tuple[tuple[str, str], ...] = (
    ("The proof invokes dominated convergence with a "
     "bounding function. Therefore for every interchange "
     "of limit and integral in the wider literature the "
     "same bound will provide automatic justification.",
     "no warrant for universal justification"),
    ("A closed-form identity is reused from a prior "
     "lemma. Therefore for every prior lemma in the "
     "journal the authors will reuse the statement, and "
     "the re-verification requirement is withheld by the "
     "editors.",
     "no warrant for blanket reuse"),
    ("The induction step uses a strict inequality. "
     "Therefore across every induction in the field the "
     "argument will be replaced by a single "
     "strict-inequality step.",
     "no warrant for replacement"),
    ("Regularity conditions are checked for a uniqueness "
     "appeal. Therefore the uniqueness theorem will hold "
     "across every related setting regardless of "
     "regularity.",
     "no warrant for unconditional uniqueness"),
    ("A series substitution remains in the convergence "
     "disk. Therefore for every series substitution in "
     "the next chapter the argument will hold "
     "unconditionally.",
     "no warrant for unconditional validity"),
    ("Fubini is invoked on a sigma-finite product. "
     "Therefore the interchange of integrals will hold "
     "across every measure space regardless of "
     "finiteness.",
     "no warrant for general interchange"),
    ("The fixed-point appeal uses continuity. Therefore "
     "for every fixed-point claim in the field the "
     "argument will follow, and additional verification "
     "is withheld by the editors.",
     "no warrant for blanket fixed-point claim"),
    ("The induction base case is checked at n equals "
     "two. Therefore across every induction in the "
     "literature the base case will be omitted.",
     "no warrant for omission"),
    ("The mean value theorem is applied to a "
     "differentiable function. Therefore for every "
     "differentiability claim in the literature the "
     "argument will follow, and verification is denied "
     "by the editors.",
     "no warrant for blanket follow"),
)

_D5_AMBIGUOUS: tuple[tuple[str, str], ...] = (
    ("Dominated convergence is invoked with a bounding "
     "function. Therefore the reviewer's check may "
     "extend to similar interchange arguments in the "
     "same paper.",
     "hedged extension"),
    ("A closed-form identity is reused from a prior "
     "lemma. Therefore the reuse might be acceptable, "
     "though stating the identity inline could improve "
     "readability.",
     "hedged readability"),
    ("The induction step uses a strict inequality. "
     "Therefore the strictness could remove an edge "
     "case but might restrict the result's reach.",
     "hedged trade-off"),
    ("Regularity conditions are checked for a uniqueness "
     "appeal. Therefore the appeal may extend to "
     "slightly weaker conditions in follow-up work.",
     "hedged extension"),
    ("A series substitution remains in the convergence "
     "disk. Therefore the substitution might still be "
     "valid near the disk boundary under additional "
     "care.",
     "hedged boundary care"),
    ("Fubini is invoked on a sigma-finite product. "
     "Therefore the conclusion may carry over to "
     "complete measures with additional hypotheses.",
     "hedged completion"),
    ("A fixed-point theorem is applied with continuity. "
     "Therefore the conclusion might also hold under "
     "weaker continuity assumptions with extra work.",
     "hedged weaker continuity"),
    ("The induction base case is checked at n equals "
     "two. Therefore the proof could be tightened by "
     "checking the case at n equals one if needed.",
     "hedged optional tightening"),
    ("The mean value theorem is applied on the open "
     "interval. Therefore the conclusion may extend to "
     "the closed interval given additional boundary "
     "behaviour analysis.",
     "hedged boundary extension"),
)


# ---------------------------------------------------------------------------
# Framing variants — repeat each base chain with prefixes
# ---------------------------------------------------------------------------


_PREFIXES: tuple[str, ...] = (
    "",
    "Note: ",
    "From the record: ",
    "Summary: ",
)


def _expand(
    base: tuple[tuple[str, str], ...], domain: str,
    label: str, prefix_letter: str,
) -> list[GeneralizationChain]:
    out: list[GeneralizationChain] = []
    for i, (text, rationale) in enumerate(base, start=1):
        for j, p in enumerate(_PREFIXES, start=1):
            out.append(GeneralizationChain(
                chain_id=(
                    f"GEN-{prefix_letter}{label}-"
                    f"{i:02d}-v{j}"
                ),
                domain=domain, text=p + text,
                ground_truth=label, rationale=rationale,
            ))
    return out


def all_chains() -> tuple[GeneralizationChain, ...]:
    out: list[GeneralizationChain] = []
    out.extend(_expand(
        _D1_VALID,
        GeneralizationDomain.D1_POSTMORTEM_ENGINEERING.value,
        "VALID", "1",
    ))
    out.extend(_expand(
        _D1_INVALID,
        GeneralizationDomain.D1_POSTMORTEM_ENGINEERING.value,
        "INVALID", "1",
    ))
    out.extend(_expand(
        _D1_AMBIGUOUS,
        GeneralizationDomain.D1_POSTMORTEM_ENGINEERING.value,
        "AMBIGUOUS", "1",
    ))
    out.extend(_expand(
        _D2_VALID,
        GeneralizationDomain.D2_APPELLATE_LEGAL.value,
        "VALID", "2",
    ))
    out.extend(_expand(
        _D2_INVALID,
        GeneralizationDomain.D2_APPELLATE_LEGAL.value,
        "INVALID", "2",
    ))
    out.extend(_expand(
        _D2_AMBIGUOUS,
        GeneralizationDomain.D2_APPELLATE_LEGAL.value,
        "AMBIGUOUS", "2",
    ))
    out.extend(_expand(
        _D3_VALID,
        GeneralizationDomain.D3_CLINICAL_PROTOCOLS.value,
        "VALID", "3",
    ))
    out.extend(_expand(
        _D3_INVALID,
        GeneralizationDomain.D3_CLINICAL_PROTOCOLS.value,
        "INVALID", "3",
    ))
    out.extend(_expand(
        _D3_AMBIGUOUS,
        GeneralizationDomain.D3_CLINICAL_PROTOCOLS.value,
        "AMBIGUOUS", "3",
    ))
    out.extend(_expand(
        _D4_VALID,
        GeneralizationDomain.D4_PEER_REVIEW_REBUTTAL.value,
        "VALID", "4",
    ))
    out.extend(_expand(
        _D4_INVALID,
        GeneralizationDomain.D4_PEER_REVIEW_REBUTTAL.value,
        "INVALID", "4",
    ))
    out.extend(_expand(
        _D4_AMBIGUOUS,
        GeneralizationDomain.D4_PEER_REVIEW_REBUTTAL.value,
        "AMBIGUOUS", "4",
    ))
    out.extend(_expand(
        _D5_VALID,
        GeneralizationDomain.D5_THEOREM_REVIEW.value,
        "VALID", "5",
    ))
    out.extend(_expand(
        _D5_INVALID,
        GeneralizationDomain.D5_THEOREM_REVIEW.value,
        "INVALID", "5",
    ))
    out.extend(_expand(
        _D5_AMBIGUOUS,
        GeneralizationDomain.D5_THEOREM_REVIEW.value,
        "AMBIGUOUS", "5",
    ))
    return tuple(out)


__all__ = [
    "GeneralizationChain", "all_chains",
]
