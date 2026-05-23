"""Aufgabe 10 — 60 content fixtures.

Three cohorts:

* **contradiction_pair** (20) — chains exhibiting the C1
  pattern (premise X, conclusion ¬X); both guards together
  must fire.
* **polarity_reversal** (20) — chains exhibiting the C2
  pattern (premise asserts X declined, conclusion asserts
  X improved); both guards together must fire.
* **content_preserving** (20) — chains whose premises and
  conclusion share content tokens without contradiction or
  polarity inversion; neither guard may fire.

Requirements:

* ``nc_detection_rate >= 0.95`` (inversion chains caught),
* ``false_inversion_rate <= 0.05`` (consistent chains
  falsely flagged).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InversionNC:
    nc_id: str
    text: str
    is_inversion: bool
    cohort: str
    rationale: str


_CONTRADICTION_PAIR: tuple[tuple[str, str], ...] = (
    ("The plaintiff filed within the limitation period "
     "before the deadline. "
     "Court records confirm the docket entry was timely. "
     "Therefore the claim is time-barred under the statute.",
     "within limitation + is time-barred"),
    ("The claimant filed within the limitation period "
     "across two filings. "
     "Counsel re-confirmed the timely submissions. "
     "Therefore the claim is time-barred under the statute.",
     "within limitation + is time-barred"),
    ("The petitioner filed within the limitation period "
     "by the statutory date. "
     "Court records corroborate the timely service of "
     "process. "
     "Therefore the petition is time-barred under the rule.",
     "within limitation + is time-barred"),
    ("The applicant filed within the limitation period in "
     "the second submission. "
     "Counsel confirmed the timely entry into the docket. "
     "Therefore the application is time-barred under the "
     "statute.",
     "within limitation + is time-barred"),
    ("The appellant filed within the limitation period in "
     "every required step. "
     "Court records show the timely procedural compliance. "
     "Therefore the appeal is time-barred under the rule.",
     "within limitation + is time-barred"),
    ("The complainant filed within the limitation period "
     "before any deadline elapsed. "
     "Records confirm the timely service on the responding "
     "party. "
     "Therefore the complaint is time-barred under the rule.",
     "within limitation + is time-barred"),
    ("The respondent filed within the limitation period "
     "across the cycle. "
     "Records confirm the timely filings on the cause. "
     "Therefore the response is time-barred under the "
     "statute on file.",
     "within limitation + is time-barred"),
    ("The party filed within the limitation period at each "
     "stage. "
     "Counsel logged the timely steps on the case docket. "
     "Therefore the matter is time-barred under the "
     "operative statute.",
     "within limitation + is time-barred"),
    ("The objector filed within the limitation period at "
     "the appointed time. "
     "Records confirm the timely submission on the "
     "registry. "
     "Therefore the objection is time-barred under the "
     "operative rule.",
     "within limitation + is time-barred"),
    ("The applicant filed within the limitation period "
     "before any procedural step. "
     "Counsel logged the timely entries on the docket. "
     "Therefore the application is time-barred under the "
     "operative statute.",
     "within limitation + is time-barred"),
    ("The plaintiff served the complaint within the "
     "limitation period and before the deadline. "
     "Court records confirm the timely service. "
     "Therefore the claim is time-barred under the "
     "operative statute.",
     "within limitation + is time-barred"),
    ("The plaintiff filed the petition timely on the "
     "docket. "
     "Records confirm the entry within the limitation "
     "period. "
     "Therefore the claim is time-barred under the "
     "operative rule.",
     "timely / within limitation + is time-barred"),
    ("Counsel filed the notice within the limitation "
     "period in the morning session. "
     "Records confirm the timely submission. "
     "Therefore the notice is time-barred under the "
     "operative statute.",
     "within limitation + is time-barred"),
    ("The party filed the appeal within the limitation "
     "period across two attempts. "
     "Records confirm the timely appellate submission. "
     "Therefore the appeal is time-barred under the "
     "operative rule.",
     "within limitation + is time-barred"),
    ("The petitioner served the notice timely before "
     "the deadline. "
     "Records corroborate the within the limitation period "
     "filing. "
     "Therefore the notice is time-barred under the "
     "operative statute.",
     "timely / within limitation + is time-barred"),
    ("The applicant entered the documents within the "
     "limitation period across both submissions. "
     "Records confirm the timely entries on the docket. "
     "Therefore the application is time-barred under the "
     "applicable rule.",
     "within limitation + is time-barred"),
    ("The complainant served the documents within the "
     "limitation period on the responding party. "
     "Records confirm the timely service on the second "
     "attempt. "
     "Therefore the complaint is time-barred under the "
     "operative statute.",
     "within limitation + is time-barred"),
    ("Counsel filed the petition within the limitation "
     "period before the procedural deadline. "
     "Court records confirm the timely entry on the case "
     "list. "
     "Therefore the petition is time-barred under the "
     "operative rule.",
     "within limitation + is time-barred"),
    ("The party served the response within the limitation "
     "period across the calendar window. "
     "Records corroborate the timely entry on the docket. "
     "Therefore the response is time-barred under the "
     "applicable statute.",
     "within limitation + is time-barred"),
    ("The respondent filed the documents within the "
     "limitation period in the second submission. "
     "Records confirm the timely filing on the operative "
     "calendar. "
     "Therefore the matter is time-barred under the "
     "applicable rule.",
     "within limitation + is time-barred"),
)


_POLARITY_REVERSAL: tuple[tuple[str, str], ...] = (
    ("Stress-test electrodes lost capacity at higher "
     "discharge rates. "
     "Post-mortem imaging showed lithium plating on the "
     "anode. "
     "Therefore aggressive cycling improved the cell "
     "durability profile.",
     "lost capacity + improved durability"),
    ("Battery samples lost capacity on every drive cycle. "
     "Inspection confirmed worn anode coatings on the "
     "cells. "
     "Therefore the protocol improved long-term durability.",
     "lost capacity + improved"),
    ("Sample cells lost capacity in every long-run trial. "
     "Post-trial scans confirmed anode plating throughout. "
     "Therefore aggressive cycling improved long-term "
     "durability of the cells.",
     "lost capacity + improved"),
    ("The pack lost capacity through every accelerated "
     "trial round. "
     "Inspection found anode plating on the disassembled "
     "cells. "
     "Therefore the high-rate cycling improved the cell "
     "durability metric.",
     "lost capacity + improved"),
    ("Stress-test cells lost capacity on each cycle of the "
     "protocol. "
     "Post-mortem images show plating on the negative "
     "electrode. "
     "Therefore aggressive cycling improved the cell "
     "durability rating.",
     "lost capacity + improved"),
    ("The unit lost capacity steadily across the trial "
     "shifts. "
     "Inspection notes confirm anode plating across the "
     "samples. "
     "Therefore the high-rate routine improved the cell "
     "durability outcome.",
     "lost capacity + improved"),
    ("Batteries lost capacity on each round of the "
     "characterisation. "
     "Inspection confirmed plating across the anodes. "
     "Therefore the protocol improved the durability of "
     "the cells.",
     "lost capacity + improved"),
    ("Cell samples lost capacity on every drive cycle of "
     "the trial. "
     "Inspection confirmed worn anode coatings on the "
     "samples. "
     "Therefore the high-rate routine improved the cell "
     "durability profile.",
     "lost capacity + improved"),
    ("Battery packs lost capacity through every "
     "accelerated trial round. "
     "Inspection found anode plating on the disassembled "
     "samples. "
     "Therefore the high-rate cycling improved the cell "
     "durability metric.",
     "lost capacity + improved"),
    ("Sample electrodes lost capacity in every long-run "
     "trial round. "
     "Post-trial scans confirmed anode plating throughout "
     "the samples. "
     "Therefore the aggressive cycling improved long-term "
     "durability of the cells.",
     "lost capacity + improved"),
    ("The catalyst yield dropped sharply with rising "
     "substrate concentration. "
     "Spectra confirmed dehydration products in the "
     "reaction mass. "
     "Therefore the high-load yield improved across the "
     "run.",
     "yield dropped + yield improved"),
    ("The reactor performance fell during the high-load "
     "cycle. "
     "Telemetry confirmed the throughput drop on the "
     "operating panel. "
     "Therefore the high-load cycle performance improved "
     "across the run.",
     "performance fell + performance improved"),
    ("Plant output declined through the night shift "
     "consistently. "
     "Operator logs confirmed the drop in the reporting "
     "summary. "
     "Therefore the night-shift output improved across "
     "the cycle.",
     "output declined + output improved"),
    ("Capacity dropped sharply after the new operating "
     "schedule rolled out. "
     "Telemetry confirmed the drop in the operating panel. "
     "Therefore the durability improved across the schedule "
     "rollout.",
     "capacity dropped + durability improved"),
    ("Cells lost capacity during the prolonged cycling "
     "trial. "
     "Post-trial inspection logged the capacity drop in "
     "the report. "
     "Therefore the cycling routine improved the cell "
     "durability profile.",
     "lost capacity + improved"),
    ("Sample output declined across the night shift. "
     "Operator logs confirmed the throughput drop in the "
     "summary. "
     "Therefore the night-shift output improved across "
     "the reporting cycle.",
     "output declined + output improved"),
    ("Reactor performance fell across the high-rate cycle. "
     "Telemetry confirmed the performance drop in the "
     "operating panel. "
     "Therefore the high-rate cycle performance improved "
     "across the operating cycle.",
     "performance fell + performance improved"),
    ("Yield dropped sharply across the high-concentration "
     "run. "
     "Spectra confirmed dehydration products throughout. "
     "Therefore the run yield improved across the "
     "concentration sweep.",
     "yield dropped + yield improved"),
    ("Capacity dropped sharply across the trial shifts. "
     "Inspection notes confirmed plating across the "
     "samples. "
     "Therefore the durability improved across the "
     "high-rate routine.",
     "capacity dropped + durability improved"),
    ("Cells lost capacity in each accelerated round of "
     "the protocol. "
     "Inspection found anode plating on the disassembled "
     "cells. "
     "Therefore the high-rate cycling improved the cell "
     "durability rating.",
     "lost capacity + improved"),
)


_CONTENT_PRESERVING: tuple[tuple[str, str], ...] = (
    ("Mice exposed to high-fat diet for twelve weeks gained "
     "significant body mass. "
     "Serum leptin concentrations rose in parallel. "
     "Therefore the diet drove adiposity through hormonal "
     "pathways.",
     "shared tokens, no inversion"),
    ("The reactor heated steadily through the morning "
     "shift. "
     "Coolant flow was kept constant during the run. "
     "Therefore the reactor reached the target "
     "temperature.",
     "shared tokens, no inversion"),
    ("Patients in the cohort tolerated the regimen. "
     "Inflammatory markers fell back into reference "
     "ranges. "
     "Therefore the regimen produced the intended effect.",
     "shared tokens, no inversion"),
    ("Sensor telemetry held within tolerance through the "
     "trial. "
     "Operators followed the published procedure. "
     "Therefore the trial confirmed steady operation.",
     "shared tokens, no inversion"),
    ("Output rose during the afternoon shift in the "
     "assembly bay. "
     "Material costs were stable across the shift. "
     "Therefore the schedule yielded the planned "
     "production.",
     "shared tokens, no inversion"),
    ("The clinic logged steady throughput across the week. "
     "Reception staff followed the published protocol. "
     "Therefore the clinic achieved its weekly target.",
     "shared tokens, no inversion"),
    ("Pollinators visited the orchard each morning. "
     "Hive records logged steady returns through the day. "
     "Therefore the orchard yielded a strong harvest.",
     "shared tokens, no inversion"),
    ("The patient presented with persistent cough and "
     "low-grade fever. "
     "Imaging confirmed lobar consolidation in the right "
     "lung. "
     "Therefore the clinical picture matched "
     "community-acquired pneumonia.",
     "shared tokens, no inversion"),
    ("Field samples from the outcrop contained elevated "
     "nickel concentrations. "
     "Trace platinum-group elements co-occurred in the "
     "same horizon. "
     "Therefore the deposit derived from a layered "
     "intrusion.",
     "shared tokens, no inversion"),
    ("Crystals grown by slow evaporation produced a "
     "monoclinic structure. "
     "X-ray refinement yielded an R-factor below five "
     "percent. "
     "Therefore the structure determination was reliable.",
     "shared tokens, no inversion"),
    ("The cohort study tracked twenty patients for a year. "
     "Outcomes were favourable across the cohort. "
     "Therefore the protocol produced consistent results.",
     "shared tokens, no inversion"),
    ("Survey participants on placebo showed no change. "
     "The treatment arm showed significant improvement. "
     "Therefore the intervention contributed to the "
     "change.",
     "shared tokens, no inversion"),
    ("The bridge survey detected stress fractures. "
     "The local authority closed the bridge for repair. "
     "Therefore the inspection led to a precautionary "
     "closure.",
     "shared tokens, no inversion"),
    ("Volcanic ash layers in the core contained distinct "
     "geochemical signatures. "
     "The signatures matched a known historical eruption. "
     "Therefore the layer dated the surrounding "
     "stratigraphy.",
     "shared tokens, no inversion"),
    ("Lab rats trained on the operant task reached "
     "criterion. "
     "Performance persisted across one week without "
     "retraining. "
     "Therefore the learning consolidated in long-term "
     "memory.",
     "shared tokens, no inversion"),
    ("The school adopted a longer reading block. "
     "Teachers noted improved focus during the block. "
     "Therefore the cohort recorded stronger reading "
     "scores.",
     "shared tokens, 'improved' alone (no polarity pair)"),
    ("The supplier reorganised its order intake process. "
     "Order entry latency fell during the pilot. "
     "Therefore the new process reduced cycle times.",
     "shared tokens, no inversion"),
    ("The maintenance team patched the network outage. "
     "Operations logged the resolution in the ticket "
     "queue. "
     "Therefore the patch restored connectivity.",
     "shared tokens, no inversion"),
    ("Trial participants recorded steady recovery over "
     "weeks. "
     "Follow-up exams documented the consistent "
     "trajectory. "
     "Therefore the rehabilitation plan met its goal.",
     "shared tokens, no inversion"),
    ("Output stabilised after the new operating protocol "
     "rolled out. "
     "Telemetry confirmed the new behaviour. "
     "Therefore the rollout achieved its intended effect.",
     "shared tokens, no inversion"),
)


def _make(prefix, src, is_inversion, cohort):
    out: list[InversionNC] = []
    for i, (text, rationale) in enumerate(src, start=1):
        out.append(InversionNC(
            nc_id=f"{prefix}{i:03d}", text=text,
            is_inversion=is_inversion, cohort=cohort,
            rationale=rationale,
        ))
    return tuple(out)


def all_inversion_ncs() -> tuple[InversionNC, ...]:
    return (
        _make(
            "NC-DC-", _CONTRADICTION_PAIR, True,
            "contradiction_pair",
        )
        + _make(
            "NC-PR-", _POLARITY_REVERSAL, True,
            "polarity_reversal",
        )
        + _make(
            "NC-CP-", _CONTENT_PRESERVING, False,
            "content_preserving",
        )
    )


__all__ = ["InversionNC", "all_inversion_ncs"]
