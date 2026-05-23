"""Aufgabe 9 — 60 synthetic semantic fixtures.

Three directive-listed families, twenty each:

* **cycle disguises** — token-overlap cycles between conclusion
  and multiple premises (expected: ``BIDIRECTIONAL_CYCLE``).
* **frame switches** — empirical premises driving a conclusion
  that lives in a different evidence frame (expected:
  ``CROSS_DOMAIN_ANALOGY`` / ``UNJUSTIFIED_GENERALIZATION`` /
  ``CONCLUSION_LEAP``).
* **non-sequiturs** — conclusion does not follow from the
  premises (expected: ``SEMANTIC_SCOPE_COLLAPSE`` /
  ``CAUSAL_BRIDGE_MISSING``).

Classifier accuracy on this set must reach ``>= 0.95`` per
directive Aufgabe 10. Each fixture carries the v4.4 class it
expects the classifier to assign.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import ResidualSemanticFailure


@dataclass(frozen=True)
class SemanticNC:
    nc_id: str
    text: str
    directive_family: str
    expected_class: str
    rationale: str


_CYCLE_NCS: tuple[tuple[str, str], ...] = (
    ("Productivity in division alpha rose steadily. "
     "Audit findings in division alpha cleared each review. "
     "Therefore division alpha productivity rose steadily "
     "across the alpha period.",
     "cycle: 'alpha' + 'productivity' + 'rose' across both premises"),
    ("Investment in fund beta grew each month. "
     "Returns from fund beta tracked the growth of fund beta. "
     "Therefore fund beta investment grew each month "
     "throughout the beta cycle.",
     "cycle: 'fund beta' + 'grew' + 'month' span both premises"),
    ("Compliance in region gamma improved each quarter. "
     "Audit findings in region gamma showed progress in gamma. "
     "Therefore gamma compliance improved each quarter "
     "across the gamma review window.",
     "cycle: 'gamma' + 'compliance' + 'quarter' span both"),
    ("Customer satisfaction with widget delta strengthened. "
     "Renewal rates for widget delta climbed across delta cycles. "
     "Therefore widget delta satisfaction strengthened "
     "throughout the delta delivery period.",
     "cycle: 'widget delta' + 'satisfaction'"),
    ("Traffic to portal epsilon rose every week. "
     "Engagement on portal epsilon climbed alongside epsilon "
     "weekly cadence. "
     "Therefore portal epsilon traffic rose every week "
     "throughout the epsilon campaign.",
     "cycle: 'portal epsilon' + 'traffic' + 'rose'"),
    ("Volume on channel zeta grew each quarter. "
     "Conversion on channel zeta tracked the zeta growth. "
     "Therefore channel zeta volume grew each quarter "
     "across the zeta review.",
     "cycle: 'zeta' + 'volume' + 'grew'"),
    ("Quality scores for team eta improved each cycle. "
     "Defect counts on team eta fell across eta cycles. "
     "Therefore team eta quality improved each cycle "
     "across the eta retrospective period.",
     "cycle: 'eta' + 'quality' + 'improved'"),
    ("Engagement with module theta rose each release. "
     "Repeat sessions on module theta tracked the theta rise. "
     "Therefore module theta engagement rose each release "
     "across the theta release train.",
     "cycle: 'theta' + 'engagement' + 'rose'"),
    ("Throughput on line iota stabilised each shift. "
     "Output on line iota tracked the iota stabilisation. "
     "Therefore line iota throughput stabilised each shift "
     "across the iota production window.",
     "cycle: 'iota' + 'throughput' + 'stabilised'"),
    ("Sales of bundle kappa climbed each promotion. "
     "Returns of bundle kappa stayed below the kappa target. "
     "Therefore bundle kappa sales climbed each promotion "
     "across the kappa campaign.",
     "cycle: 'kappa' + 'sales' + 'climbed'"),
    ("Adoption of platform lambda rose each quarter. "
     "Active accounts on platform lambda tracked the lambda rise. "
     "Therefore platform lambda adoption rose each quarter "
     "across the lambda review cycle.",
     "cycle: 'lambda' + 'adoption' + 'rose'"),
    ("Yield on process mu climbed each campaign. "
     "Quality on process mu tracked the mu campaign climb. "
     "Therefore process mu yield climbed each campaign "
     "across the mu production window.",
     "cycle: 'mu' + 'yield' + 'climbed'"),
    ("Conversion on funnel nu rose each cohort. "
     "Engagement in funnel nu tracked the nu cohort rise. "
     "Therefore funnel nu conversion rose each cohort "
     "across the nu campaign window.",
     "cycle: 'nu' + 'conversion' + 'rose'"),
    ("Reach of campaign xi expanded each month. "
     "Engagement with campaign xi tracked the xi monthly reach. "
     "Therefore campaign xi reach expanded each month "
     "across the xi rollout window.",
     "cycle: 'xi' + 'reach' + 'expanded'"),
    ("Throughput in lane omicron held each week. "
     "Cycle times in lane omicron tracked the omicron weekly hold. "
     "Therefore lane omicron throughput held each week "
     "across the omicron review.",
     "cycle: 'omicron' + 'throughput' + 'held'"),
    ("Adoption of feature pi rose each release. "
     "Retention with feature pi tracked the pi release rise. "
     "Therefore feature pi adoption rose each release "
     "across the pi release train.",
     "cycle: 'pi' + 'adoption' + 'rose'"),
    ("Reliability of node rho improved each maintenance. "
     "Uptime on node rho tracked the rho maintenance improvement. "
     "Therefore node rho reliability improved each maintenance "
     "across the rho service window.",
     "cycle: 'rho' + 'reliability' + 'improved'"),
    ("Performance on system sigma stabilised each release. "
     "Latency on system sigma tracked the sigma release stabilisation. "
     "Therefore system sigma performance stabilised each release "
     "across the sigma release plan.",
     "cycle: 'sigma' + 'performance' + 'stabilised'"),
    ("Output of plant tau held each shift. "
     "Quality at plant tau tracked the tau shift hold. "
     "Therefore plant tau output held each shift "
     "across the tau production window.",
     "cycle: 'tau' + 'output' + 'held'"),
    ("Compliance on programme upsilon rose each audit. "
     "Findings for programme upsilon cleared each upsilon review. "
     "Therefore programme upsilon compliance rose each audit "
     "across the upsilon reporting window.",
     "cycle: 'upsilon' + 'compliance' + 'rose'"),
)


_FRAME_SWITCH_NCS: tuple[tuple[str, str, str], ...] = (
    # Future projection -> CONCLUSION_LEAP
    ("Pilot users tried the new flow for two weeks. "
     "Reported satisfaction was modest but positive. "
     "Therefore the flow will dominate the user base over "
     "the next decade.",
     "future-projection -> CONCLUSION_LEAP",
     ResidualSemanticFailure.CONCLUSION_LEAP.value),
    ("Sales improved during the campaign quarter. "
     "Refund volume held below the prior baseline. "
     "Therefore the campaign will fail in the next budget cycle.",
     "future-projection -> CONCLUSION_LEAP",
     ResidualSemanticFailure.CONCLUSION_LEAP.value),
    ("A cohort study reported correlation between exercise "
     "and longevity outcomes. "
     "Controls were applied for several lifestyle factors. "
     "Therefore exercise will extend a person's lifespan "
     "by a measurable margin.",
     "future-projection -> CONCLUSION_LEAP",
     ResidualSemanticFailure.CONCLUSION_LEAP.value),
    ("Engagement rose during the trial window. "
     "Repeat-visit counts climbed alongside engagement. "
     "Therefore the feature will outperform every competitor "
     "over the next decade.",
     "future-projection -> CONCLUSION_LEAP",
     ResidualSemanticFailure.CONCLUSION_LEAP.value),
    ("Early adoption metrics climbed for the new platform. "
     "Press coverage was generally favourable. "
     "Therefore the platform will dominate the market for "
     "a decade across regions.",
     "future-projection -> CONCLUSION_LEAP",
     ResidualSemanticFailure.CONCLUSION_LEAP.value),
    ("The product tested well across pilot regions. "
     "User satisfaction held above the prior baseline. "
     "Therefore the product will rise to category leadership "
     "for years to come.",
     "future-projection -> CONCLUSION_LEAP",
     ResidualSemanticFailure.CONCLUSION_LEAP.value),
    ("The service reduced wait times in pilot clinics. "
     "Patient satisfaction held above prior baselines. "
     "Therefore the service will extend its benefits "
     "for a lifetime in every region.",
     "future-projection -> CONCLUSION_LEAP",
     ResidualSemanticFailure.CONCLUSION_LEAP.value),
    # Incapacity -> UNJUSTIFIED_GENERALIZATION
    ("The speaker hesitated several times during the debate. "
     "Reviewers noted brief pauses in delivery. "
     "Therefore the speaker cannot withstand the demands of "
     "national office.",
     "incapacity -> UNJUSTIFIED_GENERALIZATION",
     ResidualSemanticFailure.UNJUSTIFIED_GENERALIZATION.value),
    ("The athlete missed one training session in the week. "
     "Coaches logged a slight reduction in intensity. "
     "Therefore the athlete is unable to compete at the "
     "championship level.",
     "incapacity -> UNJUSTIFIED_GENERALIZATION",
     ResidualSemanticFailure.UNJUSTIFIED_GENERALIZATION.value),
    ("The candidate appeared briefly tired in the debate. "
     "Analysts noted slower replies in the final hour. "
     "Therefore the candidate cannot withstand the demands "
     "of office.",
     "incapacity -> UNJUSTIFIED_GENERALIZATION",
     ResidualSemanticFailure.UNJUSTIFIED_GENERALIZATION.value),
    ("The engineer paused before answering a hard question. "
     "Reviewers noted a brief hesitation in the recording. "
     "Therefore the engineer is not equipped for leadership "
     "responsibilities.",
     "incapacity -> UNJUSTIFIED_GENERALIZATION",
     ResidualSemanticFailure.UNJUSTIFIED_GENERALIZATION.value),
    ("The manager declined a single optional meeting. "
     "Reports flagged the absence in the weekly summary. "
     "Therefore the manager is incapable of leading the "
     "broader programme.",
     "incapacity -> UNJUSTIFIED_GENERALIZATION",
     ResidualSemanticFailure.UNJUSTIFIED_GENERALIZATION.value),
    ("The pilot showed mild fatigue at the late hour. "
     "Cockpit telemetry noted reduced response latency. "
     "Therefore the pilot cannot withstand the demands of "
     "long-haul service.",
     "incapacity -> UNJUSTIFIED_GENERALIZATION",
     ResidualSemanticFailure.UNJUSTIFIED_GENERALIZATION.value),
    ("The student missed two practice questions in the set. "
     "Tutors logged the misses in the weekly review. "
     "Therefore the student is not fit for the advanced "
     "examination tier.",
     "incapacity -> UNJUSTIFIED_GENERALIZATION",
     ResidualSemanticFailure.UNJUSTIFIED_GENERALIZATION.value),
    # Cross-domain analogy -> CROSS_DOMAIN_ANALOGY
    # (Zero token overlap between conclusion and premises.)
    ("The orchestra rehearsed its programme for six weeks. "
     "Concertmaster reports praised the rehearsal discipline. "
     "Therefore industrial yields rose markedly in the "
     "neighbouring province.",
     "zero-overlap conclusion -> CROSS_DOMAIN_ANALOGY",
     ResidualSemanticFailure.CROSS_DOMAIN_ANALOGY.value),
    ("Beekeepers logged steady production through summer. "
     "Apiary records confirmed sheltered hive placement. "
     "Therefore municipal libraries opened earlier on Sundays.",
     "zero-overlap conclusion -> CROSS_DOMAIN_ANALOGY",
     ResidualSemanticFailure.CROSS_DOMAIN_ANALOGY.value),
    ("The hiking club walked twenty trails in spring. "
     "Equipment records confirmed routine boot wear. "
     "Therefore municipal libraries opened earlier on Sundays.",
     "zero-overlap conclusion -> CROSS_DOMAIN_ANALOGY",
     ResidualSemanticFailure.CROSS_DOMAIN_ANALOGY.value),
    ("The bridge survey measured deflection daily. "
     "Maintenance teams inspected the trusses on schedule. "
     "Therefore the soup of the day featured wild mushrooms.",
     "zero-overlap conclusion -> CROSS_DOMAIN_ANALOGY",
     ResidualSemanticFailure.CROSS_DOMAIN_ANALOGY.value),
    ("Sun exposure rose during the holiday week. "
     "Vitamin records tracked the elevated readings. "
     "Therefore municipal libraries opened earlier on "
     "Sundays.",
     "zero-overlap conclusion -> CROSS_DOMAIN_ANALOGY",
     ResidualSemanticFailure.CROSS_DOMAIN_ANALOGY.value),
    ("The autumn harvest produced abundant grain. "
     "Storage records confirmed dry warehouse conditions. "
     "Therefore the chess club held its tournament outdoors.",
     "zero-overlap conclusion -> CROSS_DOMAIN_ANALOGY",
     ResidualSemanticFailure.CROSS_DOMAIN_ANALOGY.value),
    ("Members of the choir rehearsed for six weeks. "
     "Instruments were tuned to concert pitch. "
     "Therefore industrial output in the next county rose.",
     "zero-overlap conclusion -> CROSS_DOMAIN_ANALOGY",
     ResidualSemanticFailure.CROSS_DOMAIN_ANALOGY.value),
)


_NON_SEQUITUR_NCS: tuple[tuple[str, str, str], ...] = (
    # Scope collapse via explicit contradiction
    ("Stress-test cells lost capacity at higher discharge rates. "
     "Post-mortem imaging showed lithium plating in the cells. "
     "Therefore high-rate operation improved cell durability "
     "across the run.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("The plaintiff filed within the limitation period. "
     "Counsel logged the filing date on the docket. "
     "Therefore the claim is time-barred under the relevant "
     "statute.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("Production remained stable during the operating window. "
     "Audits found no deviation across the window. "
     "Therefore the line will collapse during the next "
     "reporting period.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("The battery lost capacity steadily over the test cycle. "
     "Imaging confirmed steady plating on the anode surface. "
     "Therefore aggressive cycling improved the cell "
     "durability profile.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("The claimant filed within the limitation period before "
     "the deadline. "
     "Records confirm the docket entry was timely. "
     "Therefore the claim is time-barred under the operative "
     "statute.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("Inventory remained stable through the holiday peak. "
     "Audits confirmed steady stock levels across departments. "
     "Therefore inventory will collapse during the next "
     "post-holiday quarter.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("The vehicle lost capacity in the towing test under load. "
     "Post-trial inspection logged the capacity drop. "
     "Therefore the tow rating improved across the trial "
     "phase durability checks.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("The applicant filed within the limitation period across "
     "two filings in the docket. "
     "Counsel re-confirmed the timely submission. "
     "Therefore the claim is time-barred under the operative "
     "statute.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("The reservoir remained stable through the dry season. "
     "Daily measurements confirmed steady levels. "
     "Therefore the water supply will collapse in the next "
     "calendar window.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    ("Battery samples lost capacity on every drive cycle. "
     "Inspection confirmed worn anode coatings on the cells. "
     "Therefore the protocol improved their long-term "
     "durability outlook.",
     "contradiction -> SEMANTIC_SCOPE_COLLAPSE",
     ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value),
    # Causal bridge missing — conclusion shares exactly one
    # content token with a premise but no causal warrant exists
    # and no scope-collapse / generalisation / future-projection
    # marker fires.
    ("The lecture hall booked the keynote speaker. "
     "Attendees registered ahead of the talk. "
     "Therefore the lecture hall floor received a new coat "
     "of paint.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("The library updated its evening hours. "
     "Patrons noted the longer access window. "
     "Therefore the library cafeteria received additional "
     "kitchen equipment.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("Field crews completed the survey on schedule. "
     "Reports were filed in the project archive. "
     "Therefore the project office received new desk lamps.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("The maintenance team patched the network outage. "
     "Operations logged the resolution in the ticketing "
     "queue. "
     "Therefore the network closet received fresh signage.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("The orchestra finalised the programme for the season. "
     "Rehearsal schedules were published to orchestra members. "
     "Therefore the orchestra hall received a new carpet.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("The school updated its bell schedule. "
     "Teachers reviewed the new timing in staff meetings. "
     "Therefore the school office received a new printer.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("The municipal park installed new benches along the "
     "northern path. "
     "Crews finished the installation work in a single shift. "
     "Therefore the municipal park hosted a marathon the "
     "following weekend.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("The clinic published a new visiting schedule. "
     "Receptionists updated the booking system at the clinic. "
     "Therefore the clinic hosted a public lecture on "
     "nutrition.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("The transit agency added one bus on the eastern "
     "corridor. "
     "Operators logged the schedule change in the daily "
     "report. "
     "Therefore the transit office hosted a community "
     "breakfast.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
    ("The hospital renamed a corridor for clarity. "
     "Signage updates were rolled out across the hospital. "
     "Therefore the hospital cafeteria added a salad bar.",
     "missing-bridge -> CAUSAL_BRIDGE_MISSING",
     ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value),
)


def _make_cycle() -> tuple[SemanticNC, ...]:
    out: list[SemanticNC] = []
    for i, (text, rationale) in enumerate(_CYCLE_NCS, start=1):
        out.append(SemanticNC(
            nc_id=f"NC-CY-{i:03d}", text=text,
            directive_family="cycle_disguise",
            expected_class=
                ResidualSemanticFailure.BIDIRECTIONAL_CYCLE.value,
            rationale=rationale,
        ))
    return tuple(out)


def _make_frame_switch() -> tuple[SemanticNC, ...]:
    out: list[SemanticNC] = []
    for i, (text, rationale, expected) in enumerate(
            _FRAME_SWITCH_NCS, start=1,
    ):
        out.append(SemanticNC(
            nc_id=f"NC-FS-{i:03d}", text=text,
            directive_family="frame_switch",
            expected_class=expected,
            rationale=rationale,
        ))
    return tuple(out)


def _make_non_sequitur() -> tuple[SemanticNC, ...]:
    out: list[SemanticNC] = []
    for i, (text, rationale, expected) in enumerate(
            _NON_SEQUITUR_NCS, start=1,
    ):
        out.append(SemanticNC(
            nc_id=f"NC-NS-{i:03d}", text=text,
            directive_family="non_sequitur",
            expected_class=expected,
            rationale=rationale,
        ))
    return tuple(out)


def all_semantic_ncs() -> tuple[SemanticNC, ...]:
    return _make_cycle() + _make_frame_switch() + _make_non_sequitur()


__all__ = ["SemanticNC", "all_semantic_ncs"]
