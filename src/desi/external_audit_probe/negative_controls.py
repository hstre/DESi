"""Aufgabe 9 — 50 synthetic external false-support fixtures.

Each fixture is a three-sentence ``A. B. Therefore C.`` chain
hand-authored to exhibit exactly one closed
``ExternalAuditFailure`` mode. The classifier accuracy on this
set must reach ``>= 0.95`` (Aufgabe 10).

The minimum of one fixture per class is satisfied with margin:
five fixtures per class for the eight surface-bearing classes,
plus five ``SEMANTIC_NON_SEQUITUR`` fixtures and a small
``UNKNOWN`` cohort for the catch-all.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import ExternalAuditFailure


@dataclass(frozen=True)
class FailureFixture:
    nc_id: str
    text: str
    expected_class: str
    rationale: str


_FIXTURES: tuple[tuple[str, str, str, str], ...] = (
    # ---- HIDDEN_NEGATION ---------------------------------------
    (
        "NC-HN-001",
        "Animals in the high-dose arm gained weight steadily. "
        "Their food intake doubled within the first month. "
        "Therefore the test compound was excluded from further "
        "trials.",
        ExternalAuditFailure.HIDDEN_NEGATION.value,
        "hidden negation via 'was excluded from'",
    ),
    (
        "NC-HN-002",
        "Patients in the trial reported substantial relief. "
        "Inflammatory markers fell back to normal ranges. "
        "Therefore the regimen rules out a non-inflammatory "
        "aetiology.",
        ExternalAuditFailure.HIDDEN_NEGATION.value,
        "hidden negation via 'rules out'",
    ),
    (
        "NC-HN-003",
        "The reactor temperature held steady throughout the run. "
        "Yield exceeded the historical baseline. "
        "Therefore the cooling failure is excluded by the data.",
        ExternalAuditFailure.HIDDEN_NEGATION.value,
        "hidden negation via 'is excluded by'",
    ),
    (
        "NC-HN-004",
        "The exam scores rose across cohorts year over year. "
        "Teacher ratings improved in parallel. "
        "Therefore the legacy curriculum is forgotten.",
        ExternalAuditFailure.HIDDEN_NEGATION.value,
        "hidden negation via 'is forgotten'",
    ),
    (
        "NC-HN-005",
        "Sensor readings logged a steady upward trend. "
        "Calibration was checked twice each week. "
        "Therefore the prior diagnosis can be safely deferred.",
        ExternalAuditFailure.HIDDEN_NEGATION.value,
        "hidden negation via 'safely deferred'",
    ),
    # ---- QUANTIFIER_DRIFT --------------------------------------
    (
        "NC-QD-001",
        "Three patients in the pilot study showed improvement. "
        "Follow-up at six months confirmed the trend. "
        "Therefore the treatment guaranteed remission for the "
        "entire cohort.",
        ExternalAuditFailure.QUANTIFIER_DRIFT.value,
        "drift via 'guaranteed' + 'entire'",
    ),
    (
        "NC-QD-002",
        "Two regional clinics piloted the intake form. "
        "Wait times fell modestly in both clinics. "
        "Therefore the form alone resolved the queueing problem "
        "single-handedly.",
        ExternalAuditFailure.QUANTIFIER_DRIFT.value,
        "drift via 'alone' + 'single-handedly'",
    ),
    (
        "NC-QD-003",
        "The compliance team ran a focused audit last quarter. "
        "Findings were within tolerance for the audited units. "
        "Therefore compliance holds conclusively across every "
        "department for the entire fiscal year.",
        ExternalAuditFailure.QUANTIFIER_DRIFT.value,
        "drift via 'conclusively' + 'every' + 'entire'",
    ),
    (
        "NC-QD-004",
        "Survey respondents in two cities preferred the new "
        "layout. Response rates were comparable across the cities. "
        "Therefore the layout will dominate user preferences "
        "ever after.",
        ExternalAuditFailure.QUANTIFIER_DRIFT.value,
        "drift via 'ever' (universal future)",
    ),
    (
        "NC-QD-005",
        "Output rose during the trial shift. "
        "Material costs were stable through the shift. "
        "Therefore the new schedule is solely responsible for "
        "the entire productivity gain.",
        ExternalAuditFailure.QUANTIFIER_DRIFT.value,
        "drift via 'solely' + 'entire'",
    ),
    # ---- AUTHORITY_CONTAMINATION -------------------------------
    (
        "NC-AC-001",
        "Internal reports tracked operational throughput weekly. "
        "Output stabilised across the second month. "
        "Therefore the procedure is validated by industry "
        "consensus.",
        ExternalAuditFailure.AUTHORITY_CONTAMINATION.value,
        "authority via 'validated'",
    ),
    (
        "NC-AC-002",
        "Survey data tracked retention through three quarters. "
        "Attendance held above prior baselines. "
        "Therefore the retention claim is confirmed by senior "
        "leadership review.",
        ExternalAuditFailure.AUTHORITY_CONTAMINATION.value,
        "authority via 'confirmed by'",
    ),
    (
        "NC-AC-003",
        "Field measurements ran daily for two weeks. "
        "Readings clustered within the expected band. "
        "Therefore the methodology is certified for site-wide "
        "deployment.",
        ExternalAuditFailure.AUTHORITY_CONTAMINATION.value,
        "authority via 'certified'",
    ),
    (
        "NC-AC-004",
        "Throughput counters logged stable performance. "
        "Maintenance windows were observed without incident. "
        "Therefore the new protocol is endorsed across the "
        "operations division.",
        ExternalAuditFailure.AUTHORITY_CONTAMINATION.value,
        "authority via 'endorsed'",
    ),
    (
        "NC-AC-005",
        "The procurement team logged supplier deliveries. "
        "Receipts were filed and counter-signed. "
        "Therefore vendor compliance is established by the "
        "documented record.",
        ExternalAuditFailure.AUTHORITY_CONTAMINATION.value,
        "authority via 'established'",
    ),
    # ---- METAPHOR_CONTAMINATION --------------------------------
    (
        "NC-MC-001",
        "Output recovered after the maintenance window. "
        "Operators logged steady throughput thereafter. "
        "Therefore the production line behaves like a perfectly "
        "wound clock.",
        ExternalAuditFailure.METAPHOR_CONTAMINATION.value,
        "metaphor via 'like a'",
    ),
    (
        "NC-MC-002",
        "Engagement counts ticked upward through the quarter. "
        "Repeat visits trended in the same direction. "
        "Therefore loosely speaking the platform is now its own "
        "tide.",
        ExternalAuditFailure.METAPHOR_CONTAMINATION.value,
        "metaphor via 'loosely speaking'",
    ),
    (
        "NC-MC-003",
        "Defect reports declined across three releases. "
        "Code coverage measurements rose in parallel. "
        "Therefore the codebase reads as if it were polished "
        "marble.",
        ExternalAuditFailure.METAPHOR_CONTAMINATION.value,
        "metaphor via 'as if'",
    ),
    (
        "NC-MC-004",
        "Helpdesk tickets ticked downward each month. "
        "Resolution times stayed within service targets. "
        "Therefore the support model is in a sense a perpetual "
        "garden in bloom.",
        ExternalAuditFailure.METAPHOR_CONTAMINATION.value,
        "metaphor via 'in a sense'",
    ),
    (
        "NC-MC-005",
        "Throughput numbers met the seasonal target. "
        "Downtime windows were short and planned. "
        "Therefore the workflow runs metaphorically as an "
        "uninterrupted river.",
        ExternalAuditFailure.METAPHOR_CONTAMINATION.value,
        "metaphor via 'metaphorically'",
    ),
    # ---- TOOL_CONTAMINATION ------------------------------------
    (
        "NC-TC-001",
        "Sales rose by twelve percent during the launch quarter. "
        "Refund volume held below eight percent during the same "
        "period. "
        "Therefore profit grew by twenty percent across the "
        "quarter.",
        ExternalAuditFailure.TOOL_CONTAMINATION.value,
        "tool: arithmetic in premise and conclusion (percent)",
    ),
    (
        "NC-TC-002",
        "Sensor A logged ninety degrees during the test. "
        "Sensor B logged eighty-five degrees during the test. "
        "Therefore the average reading was eighty-eight degrees "
        "in the test.",
        ExternalAuditFailure.TOOL_CONTAMINATION.value,
        "tool: degrees in premise and conclusion",
    ),
    (
        "NC-TC-003",
        "The runner covered five kilometres in the morning. "
        "She added three kilometres in the afternoon. "
        "Therefore she covered eight kilometres in total during "
        "the day.",
        ExternalAuditFailure.TOOL_CONTAMINATION.value,
        "tool: kilometres in premise and conclusion",
    ),
    (
        "NC-TC-004",
        "The first sample weighed forty milligrams on the scale. "
        "The second sample weighed sixty milligrams on the same "
        "scale. "
        "Therefore the combined mass was one hundred milligrams "
        "on the scale.",
        ExternalAuditFailure.TOOL_CONTAMINATION.value,
        "tool: milligrams in premise and conclusion",
    ),
    (
        "NC-TC-005",
        "The first batch logged fifty milligrams of impurity. "
        "The second batch logged thirty milligrams of impurity. "
        "Therefore the combined impurity reading came to eighty "
        "milligrams overall.",
        ExternalAuditFailure.TOOL_CONTAMINATION.value,
        "tool: milligram arithmetic (cross-loaded)",
    ),
    # ---- CYCLE_DISGUISE ---------------------------------------
    (
        "NC-CY-001",
        "Productivity in division alpha climbed steadily. "
        "Output across division alpha exceeded targets monthly. "
        "Therefore productivity rose in division alpha across "
        "the period.",
        ExternalAuditFailure.CYCLE_DISGUISE.value,
        "cycle: 'productivity' + 'alpha' in conclusion and "
        "multiple premises",
    ),
    (
        "NC-CY-002",
        "Investment in fund beta climbed through the quarter. "
        "Returns from fund beta tracked the climb in fund beta. "
        "Therefore fund beta saw climbing investment across the "
        "period.",
        ExternalAuditFailure.CYCLE_DISGUISE.value,
        "cycle: 'fund beta' overlaps conclusion and premises",
    ),
    (
        "NC-CY-003",
        "Compliance in region gamma improved each month. "
        "Audit findings in region gamma showed steady progress. "
        "Therefore compliance in region gamma improved "
        "throughout the period.",
        ExternalAuditFailure.CYCLE_DISGUISE.value,
        "cycle: 'gamma' shared between conclusion and premises",
    ),
    (
        "NC-CY-004",
        "Customer satisfaction with widget delta strengthened. "
        "Renewal rates for widget delta exceeded prior baselines. "
        "Therefore widget delta delighted customers throughout "
        "the period.",
        ExternalAuditFailure.CYCLE_DISGUISE.value,
        "cycle: 'widget delta' loops to conclusion",
    ),
    (
        "NC-CY-005",
        "Traffic to portal epsilon rose each week. "
        "Engagement on portal epsilon climbed alongside the "
        "traffic. "
        "Therefore portal epsilon flourished throughout the "
        "campaign window.",
        ExternalAuditFailure.CYCLE_DISGUISE.value,
        "cycle: 'portal epsilon' loops",
    ),
    # ---- FRAME_SWITCH -----------------------------------------
    (
        "NC-FS-001",
        "Quarterly revenue grew by a healthy margin. "
        "Operating costs stayed within plan during the quarter. "
        "Therefore the venture will dominate its market within "
        "the decade.",
        ExternalAuditFailure.FRAME_SWITCH.value,
        "frame switch: empirical premises -> future prediction",
    ),
    (
        "NC-FS-002",
        "Pilot users tried the feature for two weeks. "
        "Their reported satisfaction was modest but positive. "
        "Therefore the feature will dominate the user base "
        "across the coming product cycle.",
        ExternalAuditFailure.FRAME_SWITCH.value,
        "frame switch: empirical -> 'will dominate' future",
    ),
    (
        "NC-FS-003",
        "Survey scores improved in two districts. "
        "Stakeholder feedback echoed the survey findings. "
        "Therefore the policy will extend its benefits "
        "indefinitely going forward.",
        ExternalAuditFailure.FRAME_SWITCH.value,
        "frame switch: 'will extend' future certainty",
    ),
    (
        "NC-FS-004",
        "Engagement counts rose for the new feature. "
        "Crash reports declined during the trial. "
        "Therefore the feature will fail by the next major "
        "release.",
        ExternalAuditFailure.FRAME_SWITCH.value,
        "frame switch: 'will fail by'",
    ),
    (
        "NC-FS-005",
        "Initial retention exceeded targets in the cohort. "
        "Renewal numbers rose in parallel. "
        "Therefore subscriptions will renew across the next "
        "product generation without operator review.",
        ExternalAuditFailure.FRAME_SWITCH.value,
        "frame switch: 'will renew' future certainty",
    ),
    # ---- EXTRACTION_COLLAPSE ----------------------------------
    # These fixtures present only one parsable premise sentence
    # to PremiseExtractor (the second 'sentence' is a continuation
    # clause that does not parse as a separate premise).
    (
        "NC-EX-001",
        "Output rose across the morning shift in the assembly "
        "bay although several factors contributed in subtle "
        "ways throughout the shift. "
        "Therefore productivity climbed throughout the bay.",
        ExternalAuditFailure.EXTRACTION_COLLAPSE.value,
        "single complex sentence followed by conclusion",
    ),
    (
        "NC-EX-002",
        "Sales numbers climbed during the campaign across "
        "regions which had been previously underperforming for "
        "two consecutive quarters in the prior fiscal year. "
        "Therefore the campaign succeeded across the regions.",
        ExternalAuditFailure.EXTRACTION_COLLAPSE.value,
        "single complex sentence -> conclusion",
    ),
    (
        "NC-EX-003",
        "Throughput numbers stabilised after the new operating "
        "protocol was introduced across the affected lines on "
        "the morning shift. "
        "Therefore protocol adoption stabilised throughput.",
        ExternalAuditFailure.EXTRACTION_COLLAPSE.value,
        "single complex sentence -> conclusion",
    ),
    (
        "NC-EX-004",
        "Telemetry from the new sensors recorded a steady upward "
        "trend across the affected production windows during "
        "the trial. "
        "Therefore the sensors confirmed the upward trend.",
        ExternalAuditFailure.EXTRACTION_COLLAPSE.value,
        "single complex sentence -> conclusion",
    ),
    (
        "NC-EX-005",
        "Customer service metrics held above the published "
        "service-level agreement throughout the reporting "
        "period under review by the operations team. "
        "Therefore the service agreement was honoured.",
        ExternalAuditFailure.EXTRACTION_COLLAPSE.value,
        "single complex sentence -> conclusion",
    ),
    # ---- SEMANTIC_NON_SEQUITUR --------------------------------
    (
        "NC-SN-001",
        "The autumn harvest produced abundant grain. "
        "Storage facilities remained dry throughout the season. "
        "Therefore the village will host an architectural prize "
        "next year.",
        ExternalAuditFailure.SEMANTIC_NON_SEQUITUR.value,
        "surface clean; conclusion unrelated to premises",
    ),
    (
        "NC-SN-002",
        "The hiking club walked twenty trails in the spring. "
        "Their boots wore out at a typical rate. "
        "Therefore municipal libraries opened earlier on Sundays.",
        ExternalAuditFailure.SEMANTIC_NON_SEQUITUR.value,
        "surface clean; total non-sequitur",
    ),
    (
        "NC-SN-003",
        "The bridge survey measured deflection regularly. "
        "Maintenance teams inspected the trusses on schedule. "
        "Therefore the soup of the day featured wild mushrooms.",
        ExternalAuditFailure.SEMANTIC_NON_SEQUITUR.value,
        "surface clean; unrelated conclusion",
    ),
    (
        "NC-SN-004",
        "Members of the orchestra rehearsed for six weeks. "
        "Their instruments were tuned to concert pitch. "
        "Therefore industrial output in the next county rose.",
        ExternalAuditFailure.SEMANTIC_NON_SEQUITUR.value,
        "surface clean; unrelated empirical claim",
    ),
    (
        "NC-SN-005",
        "Beekeepers logged steady production through summer. "
        "Their hives were sheltered from prevailing winds. "
        "Therefore the chess club held its tournament outdoors.",
        ExternalAuditFailure.SEMANTIC_NON_SEQUITUR.value,
        "surface clean; unrelated conclusion",
    ),
    # ---- UNKNOWN ----------------------------------------------
    # These chains audit as supported but exhibit no recognisable
    # failure pattern: premises and conclusion share *no* content
    # tokens at all, and no marker bucket fires.
    (
        "NC-UN-001",
        "Rivers flow through valleys in measured cadence. "
        "Birds wheel above the canopy in patterns of three. "
        "Therefore.",
        ExternalAuditFailure.UNKNOWN.value,
        "missing conclusion content tokens",
    ),
    (
        "NC-UN-002",
        "Walls bear weight in measured silence. "
        "Roofs shelter rooms from rain at appointed hours. "
        "Therefore.",
        ExternalAuditFailure.UNKNOWN.value,
        "missing conclusion content tokens",
    ),
    (
        "NC-UN-003",
        "Pebbles line the shoreline in cool air. "
        "Tides recede before sunrise at the appointed turn. "
        "Therefore.",
        ExternalAuditFailure.UNKNOWN.value,
        "missing conclusion content tokens",
    ),
    (
        "NC-UN-004",
        "Bells ring across the courtyard at first light. "
        "Doors open to greet the morning in unison. "
        "Therefore.",
        ExternalAuditFailure.UNKNOWN.value,
        "missing conclusion content tokens",
    ),
    (
        "NC-UN-005",
        "Lanterns hang above the river at festival. "
        "Songs carry the procession through the streets. "
        "Therefore.",
        ExternalAuditFailure.UNKNOWN.value,
        "missing conclusion content tokens",
    ),
)


def all_failure_fixtures() -> tuple[FailureFixture, ...]:
    out: list[FailureFixture] = []
    for nc_id, text, expected_class, rationale in _FIXTURES:
        out.append(FailureFixture(
            nc_id=nc_id, text=text,
            expected_class=expected_class,
            rationale=rationale,
        ))
    return tuple(out)


__all__ = ["FailureFixture", "all_failure_fixtures"]
