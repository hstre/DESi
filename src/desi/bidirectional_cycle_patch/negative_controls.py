"""Aufgabe 10 — 50 structural fixtures.

Two cohorts:

* **cycle**     — 25 chains whose conclusion content tokens
                   overlap with at least two distinct premises
                   and reach the cross-premise overlap threshold
                   (the v4.5 guard *must* fire).
* **non_cycle** — 25 chains that *do* contain repeated content
                   tokens (token-rich) but whose conclusion
                   only links into a single premise, or whose
                   cross-premise overlap stays below threshold
                   (the v4.5 guard *must not* fire).

Requirements:

* ``nc_detection_rate >= 0.95`` (cycles caught),
* ``false_cycle_rate    <= 0.05`` (non-cycles falsely caught).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CycleNC:
    nc_id: str
    text: str
    is_cycle: bool
    rationale: str


# ---- 25 cycle fixtures --------------------------------------
# Each has tokens from at least two distinct premises *and*
# total cross-premise overlap >= 3 (the v4.5 threshold).

_CYCLES: tuple[tuple[str, str], ...] = (
    ("Productivity in division alpha rose steadily. "
     "Audit findings in division alpha cleared each review. "
     "Therefore productivity in division alpha rose across "
     "the alpha review.",
     "alpha + productivity + rose span both premises"),
    ("Investment in fund beta grew each month. "
     "Returns from fund beta tracked the beta growth. "
     "Therefore fund beta investment grew each month "
     "across the beta cycle.",
     "fund beta + grew + month span both"),
    ("Compliance in region gamma improved each quarter. "
     "Audit findings in region gamma showed gamma progress. "
     "Therefore region gamma compliance improved each "
     "quarter across the gamma window.",
     "gamma + compliance + quarter span both"),
    ("Customer satisfaction with widget delta strengthened. "
     "Renewal rates for widget delta climbed across delta "
     "cycles. "
     "Therefore widget delta satisfaction strengthened "
     "across the delta delivery window.",
     "widget delta + satisfaction + strengthened"),
    ("Traffic to portal epsilon rose every week. "
     "Engagement on portal epsilon climbed alongside the "
     "epsilon weekly cadence. "
     "Therefore portal epsilon traffic rose every week "
     "across the epsilon campaign.",
     "portal epsilon + traffic + rose"),
    ("Volume on channel zeta grew each quarter. "
     "Conversion on channel zeta tracked the zeta growth. "
     "Therefore channel zeta volume grew each quarter "
     "across the zeta review.",
     "zeta + volume + grew"),
    ("Quality scores for team eta improved each cycle. "
     "Defect counts on team eta fell across eta cycles. "
     "Therefore team eta quality improved each cycle "
     "across the eta retrospective.",
     "eta + quality + improved"),
    ("Engagement with module theta rose each release. "
     "Repeat sessions on module theta tracked the theta "
     "rise. "
     "Therefore module theta engagement rose each release "
     "across the theta release train.",
     "theta + engagement + rose"),
    ("Throughput on line iota stabilised each shift. "
     "Output on line iota tracked the iota stabilisation. "
     "Therefore line iota throughput stabilised each shift "
     "across the iota production window.",
     "iota + throughput + stabilised"),
    ("Sales of bundle kappa climbed each promotion. "
     "Returns of bundle kappa stayed below the kappa "
     "baseline. "
     "Therefore bundle kappa sales climbed each promotion "
     "across the kappa campaign.",
     "kappa + sales + climbed"),
    ("Adoption of platform lambda rose each quarter. "
     "Active accounts on platform lambda tracked the lambda "
     "rise. "
     "Therefore platform lambda adoption rose each quarter "
     "across the lambda window.",
     "lambda + adoption + rose"),
    ("Yield on process mu climbed each campaign. "
     "Quality on process mu tracked the mu campaign climb. "
     "Therefore process mu yield climbed each campaign "
     "across the mu production window.",
     "mu + yield + climbed"),
    ("Conversion on funnel nu rose each cohort. "
     "Engagement in funnel nu tracked the nu cohort rise. "
     "Therefore funnel nu conversion rose each cohort "
     "across the nu campaign window.",
     "nu + conversion + rose"),
    ("Reach of campaign xi expanded each month. "
     "Engagement with campaign xi tracked the xi monthly "
     "reach. "
     "Therefore campaign xi reach expanded each month "
     "across the xi rollout window.",
     "xi + reach + expanded"),
    ("Throughput in lane omicron held each week. "
     "Cycle times in lane omicron tracked the omicron weekly "
     "hold. "
     "Therefore lane omicron throughput held each week "
     "across the omicron review.",
     "omicron + throughput + held"),
    ("Adoption of feature pi rose each release. "
     "Retention with feature pi tracked the pi release rise. "
     "Therefore feature pi adoption rose each release "
     "across the pi release train.",
     "pi + adoption + rose"),
    ("Reliability of node rho improved each maintenance. "
     "Uptime on node rho tracked the rho maintenance "
     "improvement. "
     "Therefore node rho reliability improved each "
     "maintenance across the rho service window.",
     "rho + reliability + improved"),
    ("Performance on system sigma stabilised each release. "
     "Latency on system sigma tracked the sigma release "
     "stabilisation. "
     "Therefore system sigma performance stabilised each "
     "release across the sigma plan.",
     "sigma + performance + stabilised"),
    ("Output of plant tau held each shift. "
     "Quality at plant tau tracked the tau shift hold. "
     "Therefore plant tau output held each shift across "
     "the tau production window.",
     "tau + output + held"),
    ("Compliance on programme upsilon rose each audit. "
     "Findings for programme upsilon cleared each upsilon "
     "review. "
     "Therefore programme upsilon compliance rose each "
     "audit across the upsilon reporting window.",
     "upsilon + compliance + rose"),
    ("Patronage at gallery phi climbed each season. "
     "Memberships at gallery phi tracked the phi seasonal "
     "climb. "
     "Therefore gallery phi patronage climbed each season "
     "across the phi annual cycle.",
     "phi + patronage + climbed"),
    ("Throughput on conveyor chi steadied each calibration. "
     "Vibration logs on conveyor chi tracked the chi "
     "steadying. "
     "Therefore conveyor chi throughput steadied each "
     "calibration across the chi review.",
     "chi + throughput + steadied"),
    ("Yield in field psi rose each season. "
     "Soil reports on field psi tracked the psi seasonal "
     "rise. "
     "Therefore field psi yield rose each season across the "
     "psi crop window.",
     "psi + yield + rose"),
    ("Quality on bench omega lifted each batch. "
     "Test reports on bench omega tracked the omega batch "
     "lift. "
     "Therefore bench omega quality lifted each batch "
     "across the omega run window.",
     "omega + quality + lifted"),
    ("Reach of newsletter rho2 widened each issue. "
     "Engagement on newsletter rho2 tracked the rho2 issue "
     "widening. "
     "Therefore newsletter rho2 reach widened each issue "
     "across the rho2 publication window.",
     "rho2 + reach + widened"),
)


# ---- 25 non-cycle fixtures (token-rich, but not cycles) ----

_NON_CYCLES: tuple[tuple[str, str], ...] = (
    # Pattern A: conclusion overlaps with exactly one premise
    # (≥3 shared tokens, but all on one side).
    ("Mice exposed to high-fat diet gained body mass. "
     "Calorie intake was monitored daily on the chow. "
     "Therefore the high-fat diet contributed to the body "
     "mass gain.",
     "concl shares 'diet'+'body'+'mass' with p1 only"),
    ("The reactor heated steadily through the morning shift. "
     "Coolant flow was kept constant during the run. "
     "Therefore the reactor heating progressed smoothly "
     "throughout the morning.",
     "concl shares 'reactor'+'heating'+'morning' with p1"),
    ("The clinic logged steady throughput across the week. "
     "Reception staff followed the published protocol. "
     "Therefore the clinic throughput logged steady gains "
     "across the week.",
     "concl shares 'clinic'+'throughput'+'week' with p1"),
    ("Sensor telemetry held stable across the trial window. "
     "Operators followed the published instructions. "
     "Therefore the sensor telemetry held stable across the "
     "trial.",
     "concl shares 'sensor'+'telemetry'+'trial' with p1"),
    ("Output rose during the afternoon shift. "
     "Material costs were stable throughout the shift. "
     "Therefore the afternoon shift saw rising output.",
     "concl shares 'shift'+'output'+'afternoon' across "
     "p1 only"),
    # Pattern B: conclusion shares one token total (not 3+).
    ("Pollinators visited the orchard each morning. "
     "Hive records logged steady returns through the day. "
     "Therefore the orchard yielded a strong harvest.",
     "concl shares 'orchard' with p1 only (one token)"),
    ("The athlete trained at altitude for the season. "
     "Coaches logged steady mileage in the trail diary. "
     "Therefore the athlete improved race times.",
     "concl shares 'athlete' with p1 only"),
    ("The chef seasoned the broth before serving. "
     "Diners commented favourably on the menu. "
     "Therefore the broth tasted balanced to most patrons.",
     "concl shares 'broth' with p1 only"),
    ("The librarian shelved the new acquisitions. "
     "Patrons browsed the recent additions over the week. "
     "Therefore the new acquisitions found an audience.",
     "concl shares 'acquisitions' with p1 + p2"),
    ("The gardener watered the rose beds each morning. "
     "Soil moisture readings stayed in the safe range. "
     "Therefore the rose beds bloomed on schedule.",
     "concl shares 'rose'+'beds' with p1 only"),
    # Pattern C: premises share tokens with each other but the
    # conclusion's content is largely fresh.
    ("The transit agency added two buses on the eastern "
     "corridor. "
     "Operators logged the schedule change in the daily "
     "report. "
     "Commute times fell measurably along the route.",
     "premises share 'agency'+'operators' style tokens; "
     "conclusion talks about commute times instead"),
    ("Researchers calibrated the spectrometer before each "
     "run. "
     "Reagent stocks were checked alongside the calibration. "
     "Signal-to-noise ratios improved across the trial.",
     "concl introduces 'signal-to-noise' fresh"),
    ("The hospital introduced a new hand-hygiene routine. "
     "Compliance with the routine was audited monthly. "
     "Infection counts fell across the wards over the year.",
     "concl says 'infection' fresh"),
    ("The school adopted a longer reading block. "
     "Teachers noted improved focus during the block. "
     "Standardised scores rose modestly the following term.",
     "concl says 'scores' fresh"),
    ("The supplier reorganised its order intake process. "
     "Order entry latency fell measurably during pilots. "
     "Inventory write-downs eased through the next quarter.",
     "concl says 'inventory write-downs' fresh"),
    # Pattern D: legitimate causal chains with conclusion
    # summarising the result (high overlap with ONE premise
    # only).
    ("The bridge inspection found stress fractures in the "
     "south span. "
     "Engineers documented the fractures with photographs. "
     "Therefore the south span requires repair before "
     "reopening.",
     "concl 'south span' overlaps only p1; p2 different"),
    ("The catalyst showed enhanced activity at lower "
     "temperatures. "
     "Reactant turnover was logged each minute on the bench. "
     "Therefore the catalyst is favoured for low-temperature "
     "synthesis.",
     "concl 'catalyst' overlaps only p1"),
    ("The patient presented with persistent cough and "
     "low-grade fever. "
     "Chest imaging confirmed lobar consolidation in the "
     "right lung. "
     "Therefore community-acquired pneumonia is the leading "
     "diagnosis.",
     "concl 'pneumonia' fresh"),
    ("The plaintiff served the formal complaint on the "
     "defendant. "
     "Counsel filed the answer within the prescribed "
     "window. "
     "Therefore the case proceeds to the discovery phase.",
     "concl 'case'+'discovery' fresh"),
    ("The committee reviewed the draft proposal in three "
     "sessions. "
     "Members submitted written comments after the third "
     "session. "
     "Therefore the proposal moves to a vote at the next "
     "meeting.",
     "concl 'proposal'+'vote' overlap minimal"),
    # Pattern E: conclusion contains a NEW domain word that
    # doesn't appear in premises (zero overlap edge case
    # confirming no false-cycle).
    ("Soil cores from the post-burn site contained elevated "
     "charcoal layers. "
     "Pollen counts shifted toward fire-adapted species in "
     "the same horizon. "
     "The ecosystem transitioned after the disturbance.",
     "concl 'ecosystem' fresh"),
    ("Stress-test electrodes lost capacity faster at higher "
     "discharge rates. "
     "Post-mortem imaging showed lithium plating in the "
     "cells. "
     "The high-rate cycling degraded the anode interface.",
     "concl 'anode'+'interface' overlap only p2"),
    ("Stellar parallax measurements placed the target at "
     "forty parsecs. "
     "Independent radial velocity data agreed within "
     "tolerance. "
     "The distance estimate is robust to the choice of "
     "method.",
     "concl 'distance' overlap minimal"),
    ("Field samples from the basaltic outcrop contained "
     "elevated nickel concentrations. "
     "Trace platinum-group elements co-occurred in the same "
     "horizon. "
     "The deposit derived from a layered intrusion.",
     "concl 'deposit'+'intrusion' fresh"),
    ("Stellar parallax measurements placed the target at "
     "forty parsecs in the local arm. "
     "Independent radial velocity data agreed within "
     "tolerance across the survey. "
     "Astrometric calibration shifted the inferred distance "
     "by only a few percent.",
     "concl 'astrometric'+'inferred' fresh"),
)


def all_structural_ncs() -> tuple[CycleNC, ...]:
    out: list[CycleNC] = []
    for i, (text, rationale) in enumerate(_CYCLES, start=1):
        out.append(CycleNC(
            nc_id=f"NC-CY-{i:03d}", text=text,
            is_cycle=True, rationale=rationale,
        ))
    for i, (text, rationale) in enumerate(_NON_CYCLES, start=1):
        out.append(CycleNC(
            nc_id=f"NC-NX-{i:03d}", text=text,
            is_cycle=False, rationale=rationale,
        ))
    return tuple(out)


__all__ = ["CycleNC", "all_structural_ncs"]
