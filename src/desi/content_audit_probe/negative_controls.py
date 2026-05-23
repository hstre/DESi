"""Aufgabe 9 — 60 content fixtures.

Three cohorts:

* **contradiction_pairs** (20) — chains where premise asserts
  X and conclusion asserts the explicit negation of X
  (expected: ``DIRECT_CONTRADICTION``).
* **inversion_cases** (20) — chains where a positive-polarity
  outcome in the premise is reversed to negative in the
  conclusion, or vice versa (expected:
  ``PROPERTY_REVERSAL``).
* **valid_content_preserving** (20) — chains where premise
  and conclusion share content without any contradiction or
  polarity flip; the classifier should fall through to
  ``UNKNOWN``.

Requirement: ``classification_accuracy >= 0.95``.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import ContentFailure


@dataclass(frozen=True)
class ContentNC:
    nc_id: str
    text: str
    cohort: str
    expected_class: str
    rationale: str


_CONTRADICTION_PAIRS: tuple[tuple[str, str], ...] = (
    ("The plaintiff filed within the limitation period "
     "before the deadline. "
     "Court records confirm the docket entry was timely. "
     "Therefore the claim is time-barred under the operative "
     "statute.",
     "within limitation -> time-barred"),
    ("The claimant filed within the limitation period across "
     "two filings. "
     "Counsel re-confirmed the timely submissions. "
     "Therefore the claim is time-barred under the operative "
     "statute.",
     "within limitation -> time-barred"),
    ("The petitioner filed within the limitation period by "
     "the statutory date. "
     "Court records corroborate the timely service of "
     "process. "
     "Therefore the petition is time-barred under the "
     "operative rule.",
     "within limitation -> time-barred"),
    ("The applicant filed within the limitation period in "
     "the second submission. "
     "Counsel confirmed the timely entry into the docket. "
     "Therefore the application is time-barred under the "
     "operative statute.",
     "within limitation -> time-barred"),
    ("The appellant filed within the limitation period in "
     "every required step. "
     "Court records show the timely procedural compliance. "
     "Therefore the appeal is time-barred under the "
     "operative rule.",
     "within limitation -> time-barred"),
    ("The complainant filed within the limitation period "
     "before any deadline elapsed. "
     "Records confirm the timely service on the responding "
     "party. "
     "Therefore the complaint is time-barred under the "
     "applicable rule.",
     "within limitation -> time-barred"),
    ("The respondent filed within the limitation period "
     "across the cycle. "
     "Records confirm the timely filings on the cause. "
     "Therefore the response is time-barred under the "
     "statute on file.",
     "within limitation -> time-barred"),
    ("The party filed within the limitation period at each "
     "stage. "
     "Counsel logged the timely steps on the case docket. "
     "Therefore the matter is time-barred under the "
     "operative statute.",
     "within limitation -> time-barred"),
    ("The objector filed within the limitation period at "
     "the appointed time. "
     "Records confirm the timely submission on the "
     "registry. "
     "Therefore the objection is time-barred under the "
     "operative rule.",
     "within limitation -> time-barred"),
    ("The applicant filed within the limitation period "
     "before any procedural step. "
     "Counsel logged the timely entries on the docket. "
     "Therefore the application is time-barred under the "
     "operative statute.",
     "within limitation -> time-barred"),
    ("The plaintiff served the complaint within the "
     "limitation period and before the deadline. "
     "Court records confirm the timely service. "
     "Therefore the claim is time-barred under the "
     "operative statute.",
     "within limitation -> time-barred"),
    ("The plaintiff filed the petition timely on the docket. "
     "Records confirm the entry within the limitation "
     "period. "
     "Therefore the claim is time-barred under the "
     "operative rule.",
     "timely / within limitation -> time-barred"),
    ("Counsel filed the notice within the limitation period "
     "in the morning session. "
     "Records confirm the timely submission. "
     "Therefore the notice is time-barred under the "
     "operative statute.",
     "within limitation -> time-barred"),
    ("The party filed the appeal within the limitation "
     "period across two attempts. "
     "Records confirm the timely appellate submission. "
     "Therefore the appeal is time-barred under the "
     "operative rule.",
     "within limitation -> time-barred"),
    ("The petitioner served the notice timely before "
     "the deadline. "
     "Records corroborate the within the limitation period "
     "filing. "
     "Therefore the notice is time-barred under the "
     "operative statute.",
     "timely / within limitation -> time-barred"),
    ("The applicant entered the documents within the "
     "limitation period across both submissions. "
     "Records confirm the timely entries on the docket. "
     "Therefore the application is time-barred under the "
     "applicable rule.",
     "within limitation -> time-barred"),
    ("The complainant served the documents within the "
     "limitation period on the responding party. "
     "Records confirm the timely service on the second "
     "attempt. "
     "Therefore the complaint is time-barred under the "
     "operative statute.",
     "within limitation -> time-barred"),
    ("Counsel filed the petition within the limitation "
     "period before the procedural deadline. "
     "Court records confirm the timely entry on the case "
     "list. "
     "Therefore the petition is time-barred under the "
     "operative rule.",
     "within limitation -> time-barred"),
    ("The party served the response within the limitation "
     "period across the calendar window. "
     "Records corroborate the timely entry on the docket. "
     "Therefore the response is time-barred under the "
     "applicable statute.",
     "within limitation -> time-barred"),
    ("The respondent filed the documents within the "
     "limitation period in the second submission. "
     "Records confirm the timely filing on the operative "
     "calendar. "
     "Therefore the matter is time-barred under the "
     "applicable rule.",
     "within limitation -> time-barred"),
)


_INVERSION_CASES: tuple[tuple[str, str], ...] = (
    ("Stress-test electrodes lost capacity at higher "
     "discharge rates. "
     "Post-mortem imaging showed lithium plating on the "
     "anode. "
     "Therefore aggressive cycling improved the cell "
     "durability profile.",
     "lost capacity -> improved durability"),
    ("Battery samples lost capacity on every drive cycle. "
     "Inspection confirmed worn anode coatings on the "
     "cells. "
     "Therefore the protocol improved long-term durability "
     "of the cells.",
     "lost capacity -> improved durability"),
    ("Sample cells lost capacity in every long-run trial. "
     "Post-trial scans confirmed anode plating throughout. "
     "Therefore aggressive cycling improved long-term "
     "durability of the cells.",
     "lost capacity -> improved durability"),
    ("The pack lost capacity through every accelerated "
     "trial round. "
     "Inspection found anode plating on the disassembled "
     "cells. "
     "Therefore the high-rate cycling improved the cell "
     "durability metric.",
     "lost capacity -> improved durability"),
    ("Stress-test cells lost capacity on each cycle of the "
     "protocol. "
     "Post-mortem images show plating on the negative "
     "electrode. "
     "Therefore aggressive cycling improved the cell "
     "durability rating.",
     "lost capacity -> improved durability"),
    ("The unit lost capacity steadily across the trial "
     "shifts. "
     "Inspection notes confirm anode plating across the "
     "samples. "
     "Therefore the high-rate routine improved the cell "
     "durability outcome.",
     "lost capacity -> improved durability"),
    ("Batteries lost capacity on each round of the "
     "characterisation. "
     "Inspection confirmed plating across the anodes. "
     "Therefore the protocol improved the durability of "
     "the cells.",
     "lost capacity -> improved durability"),
    ("Cell samples lost capacity on every drive cycle of "
     "the trial. "
     "Inspection confirmed worn anode coatings on the "
     "samples. "
     "Therefore the high-rate routine improved the cell "
     "durability profile.",
     "lost capacity -> improved durability"),
    ("Battery packs lost capacity through every "
     "accelerated trial round. "
     "Inspection found anode plating on the disassembled "
     "samples. "
     "Therefore the high-rate cycling improved the cell "
     "durability metric.",
     "lost capacity -> improved durability"),
    ("Sample electrodes lost capacity in every long-run "
     "trial round. "
     "Post-trial scans confirmed anode plating throughout "
     "the samples. "
     "Therefore the aggressive cycling improved long-term "
     "durability of the cells.",
     "lost capacity -> improved durability"),
    ("The catalyst yield dropped sharply with rising "
     "substrate concentration. "
     "Spectra confirmed dehydration products in the "
     "reaction mass. "
     "Therefore the substrate increase yield improved "
     "across the run.",
     "yield dropped -> yield improved"),
    ("The reactor performance fell during the high-load "
     "cycle. "
     "Telemetry confirmed the throughput drop on the "
     "operating panel. "
     "Therefore the high-load cycle performance improved "
     "across the run.",
     "performance fell -> performance improved"),
    ("Plant output declined through the night shift "
     "consistently. "
     "Operator logs confirmed the drop in the reporting "
     "summary. "
     "Therefore the night-shift output improved across "
     "the cycle.",
     "output declined -> output improved"),
    ("Capacity dropped sharply after the new operating "
     "schedule rolled out. "
     "Telemetry confirmed the drop in the operating "
     "panel. "
     "Therefore the durability improved across the schedule "
     "rollout.",
     "capacity dropped -> durability improved"),
    ("Cells lost capacity during the prolonged cycling "
     "trial. "
     "Post-trial inspection logged the capacity drop in "
     "the report. "
     "Therefore the cycling routine improved the cell "
     "durability profile.",
     "lost capacity -> improved durability"),
    ("Sample output declined across the night shift. "
     "Operator logs confirmed the throughput drop in the "
     "summary. "
     "Therefore the night-shift output improved across the "
     "reporting cycle.",
     "output declined -> output improved"),
    ("Reactor performance fell across the high-rate cycle. "
     "Telemetry confirmed the performance drop in the "
     "operating panel. "
     "Therefore the high-rate cycle performance improved "
     "across the operating cycle.",
     "performance fell -> performance improved"),
    ("Yield dropped sharply across the high-concentration "
     "run. "
     "Spectra confirmed dehydration products throughout. "
     "Therefore the run yield improved across the "
     "concentration sweep.",
     "yield dropped -> yield improved"),
    ("Capacity dropped sharply across the trial shifts. "
     "Inspection notes confirmed plating across the "
     "samples. "
     "Therefore the durability improved across the high-rate "
     "routine.",
     "capacity dropped -> durability improved"),
    ("Cells lost capacity in each accelerated round of "
     "the protocol. "
     "Inspection found anode plating on the disassembled "
     "cells. "
     "Therefore the high-rate cycling improved the cell "
     "durability rating.",
     "lost capacity -> improved durability"),
)


_VALID_CONTENT_PRESERVING: tuple[tuple[str, str], ...] = (
    ("Mice exposed to high-fat diet for twelve weeks "
     "gained significant body mass. "
     "Serum leptin concentrations rose in parallel. "
     "Therefore the diet drove adiposity through hormonal "
     "pathways.",
     "premise asserts gain, conclusion asserts gain"),
    ("The reactor heated steadily through the morning "
     "shift. "
     "Coolant flow was kept constant during the run. "
     "Therefore the reactor reached the target "
     "temperature.",
     "premise asserts heating, conclusion asserts "
     "temperature"),
    ("Patients in the cohort tolerated the regimen. "
     "Inflammatory markers fell back into reference "
     "ranges. "
     "Therefore the regimen produced the intended effect.",
     "premise asserts tolerance, conclusion asserts "
     "intended"),
    ("Sensor telemetry held within tolerance through the "
     "trial. "
     "Operators followed the published procedure. "
     "Therefore the trial confirmed steady operation.",
     "premise asserts stability, conclusion asserts "
     "stability"),
    ("Output rose during the afternoon shift in the "
     "assembly bay. "
     "Material costs were stable across the shift. "
     "Therefore the schedule yielded the planned "
     "production.",
     "premise asserts rise, conclusion asserts planned"),
    ("The clinic logged steady throughput across the "
     "week. "
     "Reception staff followed the published protocol. "
     "Therefore the clinic achieved its weekly target.",
     "premise asserts throughput, conclusion asserts "
     "target"),
    ("Pollinators visited the orchard each morning. "
     "Hive records logged steady returns through the day. "
     "Therefore the orchard yielded a strong harvest.",
     "premise asserts visits, conclusion asserts harvest"),
    ("The patient presented with persistent cough and "
     "low-grade fever. "
     "Imaging confirmed lobar consolidation in the right "
     "lung. "
     "Therefore the clinical picture matched "
     "community-acquired pneumonia.",
     "premise asserts symptoms, conclusion asserts "
     "diagnosis"),
    ("Field samples from the outcrop contained elevated "
     "nickel concentrations. "
     "Trace platinum-group elements co-occurred in the "
     "same horizon. "
     "Therefore the deposit derived from a layered "
     "intrusion.",
     "premise asserts samples, conclusion asserts deposit"),
    ("Crystals grown by slow evaporation produced a "
     "monoclinic structure. "
     "X-ray refinement yielded an R-factor below five "
     "percent. "
     "Therefore the structure determination was reliable.",
     "premise asserts crystals, conclusion asserts "
     "reliable"),
    ("The cohort study tracked twenty patients for a "
     "year. "
     "Outcomes were favourable across the cohort. "
     "Therefore the protocol produced consistent results.",
     "premise asserts tracking, conclusion asserts results"),
    ("Survey participants on placebo showed no change. "
     "The treatment arm showed significant improvement. "
     "Therefore the intervention contributed to the "
     "change.",
     "premise asserts improvement, conclusion asserts "
     "contribution"),
    ("The bridge survey detected stress fractures. "
     "The local authority closed the bridge for repair. "
     "Therefore the inspection led to a precautionary "
     "closure.",
     "premise asserts fractures, conclusion asserts "
     "closure"),
    ("Volcanic ash layers in the core contained distinct "
     "geochemical signatures. "
     "The signatures matched a known historical eruption. "
     "Therefore the layer dated the surrounding "
     "stratigraphy.",
     "premise asserts signatures, conclusion asserts date"),
    ("Lab rats trained on the operant task reached "
     "criterion. "
     "Performance persisted across one week without "
     "retraining. "
     "Therefore the learning consolidated in long-term "
     "memory.",
     "premise asserts performance, conclusion asserts "
     "memory"),
    ("The school adopted a longer reading block. "
     "Teachers noted improved focus during the block. "
     "Therefore the cohort recorded stronger reading "
     "scores.",
     "premise asserts focus, conclusion asserts scores"),
    ("The supplier reorganised its order intake process. "
     "Order entry latency fell during the pilot. "
     "Therefore the new process reduced cycle times.",
     "premise asserts latency fall, conclusion asserts "
     "reduction"),
    ("The maintenance team patched the network outage. "
     "Operations logged the resolution in the ticket "
     "queue. "
     "Therefore the patch restored connectivity.",
     "premise asserts patch, conclusion asserts restoration"),
    ("Trial participants recorded steady recovery over "
     "weeks. "
     "Follow-up exams documented the consistent "
     "trajectory. "
     "Therefore the rehabilitation plan met its goal.",
     "premise asserts recovery, conclusion asserts goal"),
    ("Output stabilised after the new operating protocol "
     "rolled out. "
     "Telemetry confirmed the new behaviour. "
     "Therefore the rollout achieved its intended effect.",
     "premise asserts stabilisation, conclusion asserts "
     "intended effect"),
)


def _make(prefix, src, cohort, expected):
    out: list[ContentNC] = []
    for i, (text, rationale) in enumerate(src, start=1):
        out.append(ContentNC(
            nc_id=f"{prefix}{i:03d}", text=text,
            cohort=cohort, expected_class=expected,
            rationale=rationale,
        ))
    return tuple(out)


def all_content_ncs() -> tuple[ContentNC, ...]:
    return (
        _make(
            "NC-DC-", _CONTRADICTION_PAIRS,
            "contradiction_pair",
            ContentFailure.DIRECT_CONTRADICTION.value,
        )
        + _make(
            "NC-PR-", _INVERSION_CASES,
            "inversion_case",
            ContentFailure.PROPERTY_REVERSAL.value,
        )
        + _make(
            "NC-VL-", _VALID_CONTENT_PRESERVING,
            "valid_content_preserving",
            ContentFailure.UNKNOWN.value,
        )
    )


__all__ = ["ContentNC", "all_content_ncs"]
