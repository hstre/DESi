"""Aufgabe 10 — 60 modality fixtures.

Three cohorts:

* **tense_consistent_valid** (20) — chains whose conclusion
  modality matches the premise modality (past→past or
  past→present-descriptive); the v4.7 guard *must not* fire.
* **correlation_leap** (20) — past observational premises +
  modal/future conclusion; the v4.7 guard *must* fire.
* **sample_to_universal_leap** (20) — past observational
  premises + modal/categorical conclusion; the v4.7 guard
  *must* fire.

Requirements:

* ``nc_detection_rate >= 0.95`` (leaps caught),
* ``false_modality_rate <= 0.05`` (consistent chains falsely
  flagged).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModalityNC:
    nc_id: str
    text: str
    is_inconsistent: bool
    cohort: str
    rationale: str


_TENSE_CONSISTENT_VALID: tuple[tuple[str, str], ...] = (
    ("Mice exposed to high-fat diet gained significant body "
     "mass. Serum leptin concentrations rose in parallel. "
     "Therefore the diet drove adiposity through hormonal "
     "pathways.",
     "past + past + past — consistent"),
    ("The reactor heated steadily through the morning shift. "
     "Coolant flow was kept constant during the run. "
     "Therefore the reactor reached the target temperature.",
     "past + past + past — consistent"),
    ("Patients in the cohort tolerated the regimen. "
     "Inflammatory markers fell back into reference ranges. "
     "Therefore the regimen produced the intended effect.",
     "past + past + past — consistent"),
    ("Sensor telemetry held within tolerance through the "
     "trial. Operators followed the published procedure. "
     "Therefore the trial confirmed steady operation.",
     "past + past + past — consistent"),
    ("Output rose during the afternoon shift in the assembly "
     "bay. Material costs were stable across the shift. "
     "Therefore the schedule yielded the planned production.",
     "past + past + past — consistent"),
    ("The clinic logged steady throughput across the week. "
     "Reception staff followed the published protocol. "
     "Therefore the clinic achieved its weekly target.",
     "past + past + past — consistent"),
    ("Pollinators visited the orchard each morning. "
     "Hive records logged steady returns through the day. "
     "Therefore the orchard yielded a strong harvest.",
     "past + past + past — consistent"),
    ("The patient presented with persistent cough and "
     "low-grade fever. Imaging confirmed lobar consolidation "
     "in the right lung. Therefore the clinical picture "
     "matched community-acquired pneumonia.",
     "past + past + past — consistent"),
    ("Field samples from the outcrop contained elevated "
     "nickel concentrations. Trace platinum-group elements "
     "co-occurred in the same horizon. Therefore the deposit "
     "derived from a layered intrusion.",
     "past + past + past — consistent"),
    ("Crystals grown by slow evaporation produced a "
     "monoclinic structure. X-ray refinement yielded an "
     "R-factor below five percent. Therefore the structure "
     "determination was reliable.",
     "past + past + past — consistent"),
    ("The cohort study tracked twenty patients for a year. "
     "Outcomes were favourable across the cohort. "
     "Therefore the protocol produced consistent results.",
     "past + past + past — consistent"),
    ("Survey participants on placebo showed no change. "
     "The treatment arm showed significant improvement. "
     "Therefore the intervention contributed to the change.",
     "past + past + past — consistent"),
    ("The bridge survey detected stress fractures. "
     "The local authority closed the bridge for repair. "
     "Therefore the inspection led to a precautionary "
     "closure.",
     "past + past + past — consistent"),
    ("Volcanic ash layers in the core contained distinct "
     "geochemical signatures. The signatures matched a "
     "known historical eruption. Therefore the layer dated "
     "the surrounding stratigraphy.",
     "past + past + past — consistent"),
    ("Lab rats trained on the operant task reached criterion. "
     "Performance persisted across one week without retraining. "
     "Therefore the learning consolidated in long-term "
     "memory.",
     "past + past + past — consistent"),
    ("The school adopted a longer reading block. "
     "Teachers noted improved focus during the block. "
     "Therefore the cohort recorded stronger reading scores.",
     "past + past + past — consistent"),
    ("The supplier reorganised its order intake process. "
     "Order entry latency fell during the pilot. "
     "Therefore the new process reduced cycle times.",
     "past + past + past — consistent"),
    ("The maintenance team patched the network outage. "
     "Operations logged the resolution in the ticket queue. "
     "Therefore the patch restored connectivity.",
     "past + past + past — consistent"),
    ("Trial participants recorded steady recovery over weeks. "
     "Follow-up exams documented the consistent trajectory. "
     "Therefore the rehabilitation plan met its goal.",
     "past + past + past — consistent"),
    ("Output stabilised after the new operating protocol "
     "rolled out. Telemetry confirmed the new behaviour. "
     "Therefore the rollout achieved its intended effect.",
     "past + past + past — consistent"),
)


_CORRELATION_LEAP: tuple[tuple[str, str], ...] = (
    ("A cohort study reported correlation between exercise "
     "and longevity. Controls were applied for several "
     "lifestyle factors. Therefore exercise will extend a "
     "person's lifespan by a measurable margin.",
     "past + past + modal-future"),
    ("A panel study observed correlation between sleep and "
     "memory outcomes. The panel tracked participants for "
     "two years. Therefore better sleep will extend "
     "a person's recall for life.",
     "past + past + modal-future"),
    ("A registry study reported correlation between fibre "
     "intake and gut health. Controls were applied for "
     "several lifestyle variables. Therefore more fibre "
     "will extend a person's gut health for life.",
     "past + past + modal-future"),
    ("An observational study reported correlation between "
     "social ties and well-being. Controls were applied "
     "across several lifestyle factors. Therefore stronger "
     "ties will extend a person's well-being for life.",
     "past + past + modal-future"),
    ("A registry study observed correlation between green "
     "spaces and stress outcomes. Controls applied for "
     "several lifestyle variables. Therefore more green "
     "spaces will extend a person's stress resilience for "
     "life.",
     "past + past + modal-future"),
    ("A long-run cohort study observed correlation between "
     "hydration and cognitive scores. Controls applied for "
     "several lifestyle variables. Therefore more water "
     "will extend a person's cognition for life.",
     "past + past + modal-future"),
    ("A panel study observed correlation between time "
     "outdoors and mood. Researchers controlled for "
     "several lifestyle factors. Therefore more time "
     "outdoors will extend a person's mood for life.",
     "past + past + modal-future"),
    ("A cohort study observed correlation between meditation "
     "and stress markers. Researchers tracked participants "
     "for three years. Therefore meditation will extend a "
     "person's calmness for life.",
     "past + past + modal-future"),
    ("An observational study reported correlation between "
     "social engagement and longevity. Controls were "
     "applied for several lifestyle variables. Therefore "
     "engaging socially will extend a person's lifespan "
     "for life.",
     "past + past + modal-future"),
    ("A registry study observed correlation between regular "
     "reading and cognitive scores. Controls were applied "
     "across many lifestyle factors. Therefore reading will "
     "extend a person's cognition for life.",
     "past + past + modal-future"),
    ("A cohort study tracked stress markers across years. "
     "Researchers controlled for several lifestyle "
     "variables. Therefore mindfulness will extend a "
     "person's resilience for life.",
     "past + past + modal-future"),
    ("A panel study reported correlation between music "
     "lessons and cognitive scores. Researchers tracked "
     "participants for three years. Therefore lessons will "
     "extend a person's cognition for life.",
     "past + past + modal-future"),
    ("A long-run study observed correlation between cycling "
     "and lung capacity. Researchers tracked participants "
     "for five years. Therefore cycling will extend a "
     "person's lung capacity for life.",
     "past + past + modal-future"),
    ("An observational study reported correlation between "
     "yoga and balance scores. Researchers controlled for "
     "several lifestyle factors. Therefore yoga will extend "
     "a person's balance for life.",
     "past + past + modal-future"),
    ("A registry study tracked physical activity across "
     "regions. Researchers controlled for several lifestyle "
     "variables. Therefore regular activity will extend a "
     "person's longevity for life.",
     "past + past + modal-future"),
    ("A long-run study observed correlation between gardening "
     "and well-being. Researchers tracked participants for "
     "three years. Therefore gardening will extend a "
     "person's well-being for life.",
     "past + past + modal-future"),
    ("A panel study reported correlation between volunteering "
     "and reported happiness. Researchers controlled for "
     "several lifestyle factors. Therefore volunteering will "
     "extend a person's happiness for life.",
     "past + past + modal-future"),
    ("An observational study reported correlation between "
     "tea consumption and cardiovascular outcomes. "
     "Researchers controlled for several lifestyle factors. "
     "Therefore tea will extend a person's cardiovascular "
     "health for life.",
     "past + past + modal-future"),
    ("A registry study observed correlation between bicycle "
     "commuting and mood. Researchers controlled for "
     "several lifestyle factors. Therefore commuting by "
     "bicycle will extend a person's mood for life.",
     "past + past + modal-future"),
    ("A long-run study tracked nature walks and resting "
     "heart rate across years. Researchers controlled for "
     "several lifestyle factors. Therefore nature walks "
     "will extend a person's cardiovascular health for life.",
     "past + past + modal-future"),
)


_SAMPLE_TO_UNIVERSAL_LEAP: tuple[tuple[str, str], ...] = (
    ("The candidate hesitated during the closing debate. "
     "Analysts noted slower replies in the final segment. "
     "Therefore the candidate cannot withstand the demands "
     "of office.",
     "past + past + modal-cannot"),
    ("The athlete missed one optional training session. "
     "Coaches noted brief reduced intensity that week. "
     "Therefore the athlete cannot withstand the demands "
     "of the championship.",
     "past + past + modal-cannot"),
    ("The pilot showed mild fatigue at the late hour. "
     "Cockpit telemetry recorded brief response latency. "
     "Therefore the pilot cannot withstand the demands of "
     "long-haul service.",
     "past + past + modal-cannot"),
    ("The engineer paused before a hard question. "
     "Reviewers noted brief hesitation in the recording. "
     "Therefore the engineer cannot withstand the demands "
     "of the leadership role.",
     "past + past + modal-cannot"),
    ("The manager skipped a single optional review. "
     "Reports flagged the absence in the weekly note. "
     "Therefore the manager cannot withstand the demands "
     "of the broader programme.",
     "past + past + modal-cannot"),
    ("The driver missed one optional drill. "
     "Logs flagged the absence in the weekly report. "
     "Therefore the driver cannot withstand the demands "
     "of long-haul service.",
     "past + past + modal-cannot"),
    ("The technician paused before one repair step. "
     "Logs noted brief hesitation in the maintenance "
     "record. Therefore the technician cannot withstand "
     "the demands of the lead role.",
     "past + past + modal-cannot"),
    ("The student missed two practice items in a set. "
     "Tutors logged the misses in the weekly review. "
     "Therefore the student cannot withstand the demands "
     "of the advanced tier.",
     "past + past + modal-cannot"),
    ("The clinician skipped one optional briefing. "
     "Reports flagged the absence in the weekly summary. "
     "Therefore the clinician cannot withstand the demands "
     "of the broader rotation.",
     "past + past + modal-cannot"),
    ("The instructor paused once during the morning session. "
     "Notes flagged the pause in the session summary. "
     "Therefore the instructor cannot withstand the demands "
     "of the full programme.",
     "past + past + modal-cannot"),
    ("The musician missed one optional rehearsal. "
     "Notes flagged the absence in the weekly review. "
     "Therefore the musician cannot withstand the demands "
     "of the touring season.",
     "past + past + modal-cannot"),
    ("The chef paused before one plating step. "
     "Logs flagged the brief hesitation in the kitchen "
     "record. Therefore the chef cannot withstand the "
     "demands of the head role.",
     "past + past + modal-cannot"),
    ("The analyst missed one optional briefing. "
     "Logs flagged the absence in the weekly summary. "
     "Therefore the analyst cannot withstand the demands "
     "of the broader portfolio.",
     "past + past + modal-cannot"),
    ("The mediator paused once during the morning hearing. "
     "Notes flagged the pause in the session log. "
     "Therefore the mediator cannot withstand the demands "
     "of the full case-load.",
     "past + past + modal-cannot"),
    ("The auditor skipped one optional review. "
     "Notes flagged the absence in the weekly summary. "
     "Therefore the auditor cannot withstand the demands "
     "of the broader engagement.",
     "past + past + modal-cannot"),
    ("The librarian missed one optional outreach session. "
     "Notes flagged the absence in the weekly briefing. "
     "Therefore the librarian cannot withstand the demands "
     "of the broader programme.",
     "past + past + modal-cannot"),
    ("The engineer paused before one design review step. "
     "Logs flagged the brief hesitation in the design "
     "record. Therefore the engineer must abandon the "
     "broader project.",
     "past + past + modal-must"),
    ("The supervisor missed one optional inspection. "
     "Notes flagged the absence in the weekly review. "
     "Therefore the supervisor cannot withstand the "
     "demands of the broader site.",
     "past + past + modal-cannot"),
    ("The candidate hesitated in one rebuttal. "
     "Reviewers noted brief delays in the response. "
     "Therefore the candidate cannot withstand the demands "
     "of high office.",
     "past + past + modal-cannot"),
    ("The negotiator paused once during the morning talks. "
     "Notes flagged the pause in the session log. "
     "Therefore the negotiator cannot withstand the demands "
     "of the broader mandate.",
     "past + past + modal-cannot"),
)


def _make(prefix, src, is_inconsistent, cohort):
    out: list[ModalityNC] = []
    for i, (text, rationale) in enumerate(src, start=1):
        out.append(ModalityNC(
            nc_id=f"{prefix}{i:03d}", text=text,
            is_inconsistent=is_inconsistent, cohort=cohort,
            rationale=rationale,
        ))
    return tuple(out)


def all_modality_ncs() -> tuple[ModalityNC, ...]:
    return (
        _make(
            "NC-TC-", _TENSE_CONSISTENT_VALID,
            False, "tense_consistent_valid",
        )
        + _make(
            "NC-CL-", _CORRELATION_LEAP,
            True, "correlation_leap",
        )
        + _make(
            "NC-SU-", _SAMPLE_TO_UNIVERSAL_LEAP,
            True, "sample_to_universal_leap",
        )
    )


__all__ = ["ModalityNC", "all_modality_ncs"]
