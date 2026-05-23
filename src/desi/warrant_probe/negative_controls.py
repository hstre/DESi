"""Aufgabe 9 — 60 synthetic warrant fixtures.

Three directive-listed families, twenty each:

* **missing-bridge** — chains where premise asserts X and
  conclusion asserts ¬X (the v4.6 ``MISSING_BRIDGE_RULE``
  shape).
* **scope-extension** — chains where conclusion broadens the
  scope beyond what premises establish (the ``SCOPE_EXTENSION``
  shape).
* **generalization-leap** — chains where one observation or
  correlation drives a categorical / future-causal claim
  (``SAMPLE_TO_UNIVERSAL`` or ``CORRELATION_TO_CAUSATION``).

Classifier accuracy on this set must reach ``>= 0.95``.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import WarrantFailure


@dataclass(frozen=True)
class WarrantNC:
    nc_id: str
    text: str
    directive_family: str
    expected_class: str
    rationale: str


# ---- missing-bridge (20) -- contradiction pairs --------------

_MISSING_BRIDGE: tuple[tuple[str, str], ...] = (
    ("Stress-test electrodes lost capacity faster at higher "
     "discharge rates. "
     "Post-mortem imaging showed lithium plating on the "
     "anode. "
     "Therefore aggressive cycling improved the cell "
     "durability profile.",
     "premise lost capacity / conclusion improved durability"),
    ("The plaintiff filed within the limitation period "
     "before the deadline. "
     "Court records confirm the docket entry was timely "
     "on the calendar. "
     "Therefore the claim is time-barred under the "
     "operative statute.",
     "premise within limitation / conclusion time-barred"),
    ("The battery lost capacity steadily over the test "
     "cycle. "
     "Imaging confirmed steady plating on the anode "
     "surface throughout. "
     "Therefore aggressive cycling improved durability "
     "across the test.",
     "premise lost capacity / conclusion improved"),
    ("The claimant filed within the limitation period "
     "across two filings. "
     "Counsel re-confirmed the timely submissions on "
     "the docket. "
     "Therefore the claim is time-barred under the "
     "operative statute.",
     "premise within limitation / conclusion time-barred"),
    ("The reactor lost capacity in the towing test under "
     "load. "
     "Post-trial inspection logged the capacity drop in "
     "the report. "
     "Therefore the rating improved across the trial "
     "durability checks.",
     "premise lost capacity / conclusion improved"),
    ("The petitioner filed within the limitation period "
     "by the statutory date. "
     "Court records corroborate the timely service of "
     "process. "
     "Therefore the petition is time-barred under the "
     "operative rule.",
     "premise within limitation / conclusion time-barred"),
    ("Cell samples lost capacity on every drive cycle. "
     "Inspection logged worn coatings on the cell tops. "
     "Therefore the protocol improved their long-term "
     "durability outlook.",
     "premise lost capacity / conclusion improved"),
    ("The applicant filed within the limitation period in "
     "the second submission. "
     "Counsel confirmed the timely entry into the docket. "
     "Therefore the application is time-barred under the "
     "operative statute.",
     "premise within limitation / conclusion time-barred"),
    ("The vehicle lost capacity during the towing trial. "
     "Post-trial logs documented the capacity drop on the "
     "platform. "
     "Therefore the tow rating improved across the trial "
     "phase.",
     "premise lost capacity / conclusion improved"),
    ("The appellant filed within the limitation period in "
     "every required step. "
     "Court records show the timely procedural compliance. "
     "Therefore the appeal is time-barred under the "
     "operative rule.",
     "premise within limitation / conclusion time-barred"),
    ("Stress-test cells lost capacity on each cycle of "
     "the protocol. "
     "Post-mortem images show plating on the negative "
     "electrode. "
     "Therefore aggressive cycling improved the cell "
     "durability rating.",
     "premise lost capacity / conclusion improved"),
    ("The complainant filed within the limitation period "
     "before any deadline elapsed. "
     "Records confirm the timely service on the responding "
     "party. "
     "Therefore the complaint is time-barred under the "
     "applicable rule.",
     "premise within limitation / conclusion time-barred"),
    ("The unit lost capacity steadily across the trial "
     "shifts. "
     "Inspection notes confirm anode plating across the "
     "samples. "
     "Therefore the high-rate routine improved the cell "
     "durability outcome.",
     "premise lost capacity / conclusion improved"),
    ("The respondent filed within the limitation period "
     "across the cycle. "
     "Records confirm the timely filings on the cause. "
     "Therefore the response is time-barred under the "
     "statute on file.",
     "premise within limitation / conclusion time-barred"),
    ("Batteries lost capacity on each round of the "
     "characterisation. "
     "Inspection confirmed plating across the anodes. "
     "Therefore the protocol improved the durability of "
     "the cells.",
     "premise lost capacity / conclusion improved"),
    ("The party filed within the limitation period at each "
     "stage. "
     "Counsel logged the timely steps on the case docket. "
     "Therefore the matter is time-barred under the "
     "operative statute.",
     "premise within limitation / conclusion time-barred"),
    ("The pack lost capacity through every accelerated "
     "trial round. "
     "Inspection found anode plating on the disassembled "
     "cells. "
     "Therefore the high-rate cycling improved the cell "
     "durability metric.",
     "premise lost capacity / conclusion improved"),
    ("The objector filed within the limitation period at "
     "the appointed time. "
     "Records confirm the timely submission on the "
     "registry. "
     "Therefore the objection is time-barred under the "
     "operative rule.",
     "premise within limitation / conclusion time-barred"),
    ("Sample cells lost capacity in every long-run trial. "
     "Post-trial scans confirmed anode plating throughout. "
     "Therefore aggressive cycling improved long-term "
     "durability of the cells.",
     "premise lost capacity / conclusion improved"),
    ("The applicant filed within the limitation period "
     "before any procedural step. "
     "Counsel logged the timely entries on the docket. "
     "Therefore the application is time-barred under the "
     "operative statute.",
     "premise within limitation / conclusion time-barred"),
)


# ---- scope-extension (20) -- universal-scope conclusions ----

_SCOPE_EXTENSION: tuple[tuple[str, str], ...] = (
    ("Pilot users in two regions tried the new flow. "
     "Reported satisfaction was modest but positive in both "
     "regions. "
     "Therefore the flow is the right choice for a person's "
     "needs in every market.",
     "scope hint 'a person's' + 'every market'"),
    ("The cohort study tracked twenty patients for a year. "
     "Outcomes were favourable across the cohort. "
     "Therefore the regimen improves a person's odds for "
     "life.",
     "scope hint 'a person's' + 'for life'"),
    ("The survey sampled two cities. "
     "Response rates were comparable between them. "
     "Therefore the policy works across every city in the "
     "country.",
     "scope hint 'across every'"),
    ("Two clinics piloted the new triage protocol. "
     "Wait times fell modestly in both clinics. "
     "Therefore the protocol works for every patient across "
     "every clinic.",
     "scope hint 'every patient' + 'every clinic'"),
    ("Pilot users tried the feature for two weeks. "
     "Reported satisfaction was modest but positive. "
     "Therefore the feature meets a person's needs across "
     "every market for life.",
     "scope hint 'a person's' + 'every'"),
    ("The intervention ran across three pilot sites. "
     "Endpoint metrics held across all three sites. "
     "Therefore the intervention improves outcomes across "
     "every site in the region.",
     "scope hint 'across every'"),
    ("Two surveys reported elevated satisfaction. "
     "Repeat-visit counts rose in both surveys. "
     "Therefore the feature reshapes a person's experience "
     "for life.",
     "scope hint 'a person's' + 'for life'"),
    ("The screening campaign ran across two districts. "
     "Reported attendance climbed in both districts. "
     "Therefore the campaign meets a person's needs across "
     "every district.",
     "scope hint 'a person's' + 'across every'"),
    ("The pilot reduced wait times in two clinics. "
     "Patient satisfaction climbed in both clinics. "
     "Therefore the protocol works for every clinic across "
     "the network.",
     "scope hint 'every clinic'"),
    ("The training programme rolled out across two cohorts. "
     "Incident reports fell in both cohorts. "
     "Therefore the programme improves outcomes for every "
     "cohort across the organisation.",
     "scope hint 'every cohort'"),
    ("The educational intervention reached two districts. "
     "Standardised scores rose in both districts. "
     "Therefore the intervention raises a person's outcomes "
     "across every district.",
     "scope hint 'a person's' + 'across every'"),
    ("The maintenance protocol ran across two plants. "
     "Downtime metrics fell in both plants. "
     "Therefore the protocol works across every plant in "
     "the company.",
     "scope hint 'across every'"),
    ("The pilot tested the new portal in two regions. "
     "Engagement climbed in both regions. "
     "Therefore the portal works for every market across "
     "the country.",
     "scope hint 'every market'"),
    ("The new menu was piloted in two restaurants. "
     "Sales rose modestly in both venues. "
     "Therefore the menu meets a person's preferences "
     "across every market.",
     "scope hint 'a person's' + 'across every'"),
    ("The exam reform reached two schools. "
     "Pass rates climbed in both schools. "
     "Therefore the reform improves outcomes for every "
     "school in the district.",
     "scope hint 'every school'"),
    ("The new packaging rolled out in two warehouses. "
     "Damage counts fell in both warehouses. "
     "Therefore the packaging works across every warehouse "
     "in the network.",
     "scope hint 'across every'"),
    ("The fitness programme reached two studios. "
     "Attendance rose in both studios. "
     "Therefore the programme improves a person's outcomes "
     "across every studio.",
     "scope hint 'a person's' + 'across every'"),
    ("Two field offices piloted the new intake form. "
     "Wait times fell in both offices. "
     "Therefore the form benefits every office across the "
     "agency for life.",
     "scope hint 'every office' + 'for life'"),
    ("The training videos rolled out across two teams. "
     "Compliance climbed in both teams. "
     "Therefore the videos work for every team across the "
     "organisation.",
     "scope hint 'every team'"),
    ("The new triage script reached two helpdesks. "
     "Resolution times fell in both helpdesks. "
     "Therefore the script benefits a person's resolution "
     "across every helpdesk.",
     "scope hint 'a person's' + 'across every'"),
)


# ---- generalization-leap (20) — sample/correlation -> universal

_GENERALIZATION_LEAP: tuple[tuple[str, str, str], ...] = (
    # SAMPLE_TO_UNIVERSAL — incapacity / character claim
    ("The candidate hesitated during the closing debate. "
     "Analysts noted slower replies in the final segment. "
     "Therefore the candidate cannot withstand the demands "
     "of office.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The athlete missed one optional training session. "
     "Coaches noted brief reduced intensity that week. "
     "Therefore the athlete is unable to compete at the "
     "championship level.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The pilot showed mild fatigue at the late hour. "
     "Cockpit telemetry noted brief response latency. "
     "Therefore the pilot cannot withstand the demands of "
     "long-haul service.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The engineer paused before a hard question. "
     "Reviewers noted brief hesitation in the recording. "
     "Therefore the engineer is not equipped for the "
     "leadership role.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The manager skipped a single optional review. "
     "Reports flagged the absence in the weekly note. "
     "Therefore the manager is incapable of running the "
     "wider programme.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The driver missed one optional drill. "
     "Logs flagged the absence in the weekly report. "
     "Therefore the driver is not fit for long-haul "
     "service.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The candidate hesitated in one rebuttal. "
     "Reviewers noted brief delays in the response. "
     "Therefore the candidate cannot withstand the demands "
     "of high office.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The technician paused before one repair step. "
     "Logs noted brief hesitation in the maintenance "
     "record. "
     "Therefore the technician is not equipped for the "
     "lead role.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The student missed two practice items in a set. "
     "Tutors logged the misses in the weekly review. "
     "Therefore the student is not fit for the advanced "
     "examination tier.",
     "incapacity from limited observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    ("The clinician skipped one optional briefing. "
     "Reports flagged the absence in the weekly summary. "
     "Therefore the clinician is incapable of running the "
     "broader rotation.",
     "incapacity from one observation",
     WarrantFailure.SAMPLE_TO_UNIVERSAL.value),
    # CORRELATION_TO_CAUSATION
    ("A cohort study reported correlation between exercise "
     "and longevity. "
     "Controls were applied for several lifestyle factors. "
     "Therefore exercise will extend a person's lifespan by "
     "a measurable margin.",
     "correlation premise + future-causal conclusion",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("A panel study observed correlation between sleep and "
     "memory outcomes. "
     "The panel tracked participants for two years. "
     "Therefore better sleep will extend a person's recall "
     "abilities for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("A registry study reported correlation between fibre "
     "intake and gut health. "
     "Controls were applied for several lifestyle "
     "variables. "
     "Therefore more fibre will extend a person's gut "
     "health for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("An observational study reported correlation between "
     "social ties and well-being. "
     "Controls were applied across several lifestyle "
     "factors. "
     "Therefore stronger ties will extend a person's "
     "well-being for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("A registry study observed correlation between green "
     "spaces and stress outcomes. "
     "Controls applied for several lifestyle variables. "
     "Therefore more green spaces will extend a person's "
     "stress resilience for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("A long-run cohort study observed correlation between "
     "hydration and cognitive scores. "
     "Controls applied for several lifestyle variables. "
     "Therefore more water will extend a person's cognition "
     "for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("A panel study observed correlation between time "
     "outdoors and mood. "
     "Researchers controlled for several lifestyle "
     "factors. "
     "Therefore more time outdoors will extend a person's "
     "mood improvements for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("A cohort study observed correlation between "
     "meditation and stress markers. "
     "Researchers tracked participants for three years. "
     "Therefore meditation will extend a person's "
     "calmness for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("An observational study reported correlation between "
     "social engagement and longevity. "
     "Controls were applied for several lifestyle "
     "variables. "
     "Therefore engaging socially will extend a person's "
     "lifespan for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
    ("A registry study observed correlation between "
     "regular reading and cognitive scores. "
     "Controls were applied across many lifestyle "
     "factors. "
     "Therefore reading will extend a person's cognition "
     "for life.",
     "correlation + future-causal",
     WarrantFailure.CORRELATION_TO_CAUSATION.value),
)


def _make(prefix: str, src, target: str | None = None,
          family: str = "") -> tuple[WarrantNC, ...]:
    out: list[WarrantNC] = []
    for i, row in enumerate(src, start=1):
        if len(row) == 2:
            text, rationale = row
            expected = target
        else:
            text, rationale, expected = row
        out.append(WarrantNC(
            nc_id=f"{prefix}{i:03d}", text=text,
            directive_family=family,
            expected_class=expected,
            rationale=rationale,
        ))
    return tuple(out)


def all_warrant_ncs() -> tuple[WarrantNC, ...]:
    return (
        _make(
            "NC-MB-", _MISSING_BRIDGE,
            target=WarrantFailure.MISSING_BRIDGE_RULE.value,
            family="missing_bridge",
        )
        + _make(
            "NC-SE-", _SCOPE_EXTENSION,
            target=WarrantFailure.SCOPE_EXTENSION.value,
            family="scope_extension",
        )
        + _make(
            "NC-GL-", _GENERALIZATION_LEAP,
            family="generalization_leap",
        )
    )


__all__ = ["WarrantNC", "all_warrant_ncs"]
