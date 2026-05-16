"""Aufgabe 10 — 100 NC fixtures for taxonomy classifier
accuracy."""
from __future__ import annotations

from dataclasses import dataclass

from .feature_extraction import extract_features
from .corpus import TransferChain
from .taxonomy import TaxonomyClass, classify_sample_features


@dataclass(frozen=True)
class TransferNC:
    nc_id: str
    text: str
    expected_class: str
    family: str


def _make(prefix: str, texts: tuple[str, ...],
          expected: str, family: str) -> tuple[TransferNC, ...]:
    return tuple(
        TransferNC(
            nc_id=f"{prefix}{i:03d}", text=t,
            expected_class=expected, family=family,
        )
        for i, t in enumerate(texts, start=1)
    )


# ---------------------------------------------------------------------------
# Modal asymmetry — premise past, conclusion modal/categorical
# ---------------------------------------------------------------------------

_MA = (
    "Operators logged steady throughput across the shift. "
    "Engineering reviewed the rollout notes before noon. "
    "Therefore the team cannot meet the deadline next week.",
    "The cohort reported steady improvement across two weeks. "
    "Researchers documented every endpoint reading. "
    "Therefore the cohort will dominate every comparable trial.",
    "The reactor stabilised after the schedule change. "
    "Operators reviewed every shift log carefully. "
    "Therefore the reactor will dominate baseline throughput "
    "for a decade.",
    "The audit cleared every recorded checkpoint last quarter. "
    "Inspectors signed off on every line. "
    "Therefore the system cannot fail the next compliance "
    "review.",
    "The pilot reported steady satisfaction across two trials. "
    "Coaches reviewed each session's notes. "
    "Therefore the rollout will dominate every other launch.",
    "The clinic logged steady throughput across the week. "
    "Reception staff reviewed the protocol with care. "
    "Therefore the clinic cannot fail to meet next quarter's "
    "target.",
    "The platform logged steady uptime across the month. "
    "Engineers reviewed each deploy with care. "
    "Therefore the platform will dominate the segment for "
    "a decade.",
    "The team reviewed every incident from the rollout. "
    "Operators logged each step in the runbook. "
    "Therefore the team cannot encounter a repeat incident.",
    "The protocol stabilised every measured run. "
    "Engineers documented each rollout window. "
    "Therefore the protocol will dominate every comparable "
    "deployment.",
    "The cohort reported steady gains across two months. "
    "Coaches logged each weekly measurement. "
    "Therefore the cohort will dominate the next compared "
    "group.",
    "The clinic stabilised throughput across the autumn. "
    "Staff reviewed each shift handover. "
    "Therefore the clinic cannot miss its winter target.",
    "The system stabilised after the recent migration. "
    "Operators reviewed each rollout step. "
    "Therefore the system will dominate the next year of "
    "availability metrics.",
    "The audit cleared the entire scope last cycle. "
    "Inspectors reviewed each finding in detail. "
    "Therefore the audit cannot detect issues at the next "
    "cycle.",
    "The protocol cleared every gate during the rollout. "
    "Engineers reviewed each measured run. "
    "Therefore the protocol will dominate every comparable "
    "pilot.",
    "The depot logged steady inbound volume across the week. "
    "Dispatchers reviewed each routing sheet. "
    "Therefore the depot cannot miss the holiday window.",
    "The branch reported steady deposits across the month. "
    "Tellers reviewed each ledger entry. "
    "Therefore the branch will dominate every comparable "
    "branch in the region.",
    "The fleet logged steady fuel use across the quarter. "
    "Mechanics reviewed each maintenance log. "
    "Therefore the fleet cannot exceed budget next year.",
    "The factory stabilised throughput across the rotation. "
    "Operators reviewed each shift report. "
    "Therefore the factory will dominate the regional output "
    "benchmark.",
    "The library logged steady circulation across the term. "
    "Staff reviewed each catalogue update. "
    "Therefore the library cannot fall behind the readership "
    "target.",
    "The studio reported steady attendance across the season. "
    "Coaches reviewed each scheduling sheet. "
    "Therefore the studio will dominate every comparable "
    "studio in the city.",
)


# ---------------------------------------------------------------------------
# Negation asymmetry — conclusion uses rare-negation tokens
# ---------------------------------------------------------------------------

_NA = (
    "Reports cleared every checkpoint in the quarterly review. "
    "Inspectors signed off on each line. "
    "Therefore the secondary scenario is excluded by the "
    "review summary.",
    "Audit logs cleared each entry in the inspection. "
    "Operators confirmed every published step. "
    "Therefore the rollback path is excluded by the current "
    "operational record.",
    "Test runs covered the documented surface. "
    "Operators confirmed the test outcomes. "
    "Therefore the regression path is excluded by the test "
    "report on file.",
    "Compliance staff reviewed every record. "
    "Each finding cleared the published threshold. "
    "Therefore the compliance gap is denied by the latest "
    "review notes.",
    "Reviewers verified every entry on the docket. "
    "Each entry matched the published template. "
    "Therefore the docketing error is excluded by the review "
    "summary.",
    "Engineers covered every modelled scenario. "
    "Tests passed for each scenario in the matrix. "
    "Therefore the failure scenario is excluded by the test "
    "matrix.",
    "Auditors confirmed the published submission window. "
    "Each filing matched the window. "
    "Therefore the missed-window scenario is denied by the "
    "submission record.",
    "Operators reviewed each shift handover. "
    "Each handover cleared the published checklist. "
    "Therefore the handover gap is excluded by the published "
    "checklist.",
    "Reviewers checked every cited reference. "
    "Each reference cleared the required citation format. "
    "Therefore the missing-citation scenario is denied by the "
    "reference review.",
    "Inspectors covered the entire safety surface. "
    "Each subsystem cleared the test plan. "
    "Therefore the subsystem failure is excluded by the test "
    "plan summary.",
    "Reviewers checked each ledger entry in the audit. "
    "Each entry cleared the published threshold. "
    "Therefore the ledger discrepancy is excluded by the "
    "audit report.",
    "Operators tested every documented configuration. "
    "Each configuration cleared the deployment checklist. "
    "Therefore the configuration drift is excluded by the "
    "rollout summary.",
    "Inspectors reviewed every safety filing in the quarter. "
    "Each filing cleared the regulator's threshold. "
    "Therefore the missed-filing scenario is denied by the "
    "filing record.",
    "Engineers covered every test point in the matrix. "
    "Each test point cleared the documented gate. "
    "Therefore the latent fault is excluded by the test "
    "matrix summary.",
    "Reviewers verified every closing entry in the period. "
    "Each entry matched the audited template. "
    "Therefore the misposting scenario is denied by the "
    "ledger review.",
    "Operators inspected every alert in the queue. "
    "Each alert cleared the documented escalation step. "
    "Therefore the escalation gap is excluded by the queue "
    "review.",
    "Reviewers checked every published claim. "
    "Each claim cleared the citation requirement. "
    "Therefore the uncited-claim scenario is excluded by the "
    "review summary.",
)


# ---------------------------------------------------------------------------
# Universal leap — conclusion uses multi-word universal phrases
# ---------------------------------------------------------------------------

_UL = (
    "Two regions piloted the new feature. "
    "Engagement rose modestly in both regions. "
    "Therefore the feature works for every market in the "
    "country.",
    "Two clinics piloted the new triage protocol. "
    "Wait times fell in both clinics. "
    "Therefore the protocol works across every clinic in "
    "the network.",
    "Three teams piloted the new training programme. "
    "Incident reports fell across the teams. "
    "Therefore the programme works for every team in the "
    "organisation.",
    "Two districts piloted the new curriculum. "
    "Standardised scores rose in both districts. "
    "Therefore the curriculum works across every district "
    "in the state.",
    "Two warehouses piloted the new packaging. "
    "Damage counts fell in both warehouses. "
    "Therefore the packaging works across every warehouse "
    "in the network.",
    "Two studios piloted the new fitness programme. "
    "Attendance rose in both studios. "
    "Therefore the programme works across every studio in "
    "the chain.",
    "Two helpdesks piloted the new triage script. "
    "Resolution times fell in both helpdesks. "
    "Therefore the script works for every helpdesk in the "
    "department.",
    "Two offices piloted the new intake form. "
    "Wait times fell in both offices. "
    "Therefore the form works for every office across the "
    "agency.",
    "Two plants piloted the new maintenance protocol. "
    "Downtime fell in both plants. "
    "Therefore the protocol works across every plant in "
    "the company.",
    "Two regions tested the new survey programme. "
    "Response rates climbed in both regions. "
    "Therefore the programme works for every market across "
    "the country.",
    "Two libraries trialled the new lending policy. "
    "Member returns rose in both libraries. "
    "Therefore the policy works across every library in "
    "the system.",
    "Two depots adopted the new dispatch script. "
    "Routing accuracy improved at both depots. "
    "Therefore the script works for every depot across "
    "the network.",
    "Two boroughs trialled the new permit form. "
    "Application throughput rose in both boroughs. "
    "Therefore the form works across every borough in "
    "the city.",
    "Two pilot wards trialled the new staffing model. "
    "Patient throughput rose in both wards. "
    "Therefore the model works for every ward across "
    "the hospital.",
    "Two campuses trialled the new tutoring scheme. "
    "Pass rates climbed at both campuses. "
    "Therefore the scheme works across every campus in "
    "the university.",
    "Two depots adopted the new packaging guide. "
    "Damage counts fell at both depots. "
    "Therefore the guide works across every depot in "
    "the chain.",
)


# ---------------------------------------------------------------------------
# Overlap loop — bidirectional cycle pattern
# ---------------------------------------------------------------------------

_OL = (
    "Productivity in division alpha rose steadily. "
    "Audit findings in division alpha cleared each review. "
    "Therefore productivity in division alpha rose steadily "
    "across the alpha period.",
    "Investment in fund beta grew each month. "
    "Returns from fund beta tracked the beta growth. "
    "Therefore fund beta investment grew each month across "
    "the beta cycle.",
    "Compliance in region gamma improved each quarter. "
    "Audit findings in region gamma showed gamma progress. "
    "Therefore gamma compliance improved each quarter across "
    "the gamma review.",
    "Customer satisfaction with widget delta strengthened. "
    "Renewal rates for widget delta climbed across delta "
    "cycles. "
    "Therefore widget delta satisfaction strengthened across "
    "the delta delivery window.",
    "Traffic to portal epsilon rose during the cycle. "
    "Engagement on portal epsilon climbed alongside the "
    "epsilon weekly cadence. "
    "Therefore portal epsilon traffic rose during the cycle "
    "across the epsilon campaign window.",
    "Volume on channel zeta grew each quarter. "
    "Conversion on channel zeta tracked the zeta growth. "
    "Therefore channel zeta volume grew each quarter across "
    "the zeta review.",
    "Quality scores for team eta improved each cycle. "
    "Defect counts on team eta fell across eta cycles. "
    "Therefore team eta quality improved each cycle across "
    "the eta retrospective.",
    "Engagement with module theta rose each release. "
    "Repeat sessions on module theta tracked the theta rise. "
    "Therefore module theta engagement rose each release "
    "across the theta release train.",
    "Throughput on line iota stabilised each shift. "
    "Output on line iota tracked the iota stabilisation. "
    "Therefore line iota throughput stabilised each shift "
    "across the iota production window.",
    "Sales of bundle kappa climbed each promotion. "
    "Returns of bundle kappa stayed below the kappa target. "
    "Therefore bundle kappa sales climbed each promotion "
    "across the kappa campaign.",
    "Capacity at depot lambda grew each cycle. "
    "Utilisation at depot lambda tracked the lambda growth. "
    "Therefore depot lambda capacity grew each cycle across "
    "the lambda planning window.",
    "Subscription to service mu rose each quarter. "
    "Retention on service mu tracked the mu quarterly rise. "
    "Therefore service mu subscription rose each quarter "
    "across the mu retention window.",
    "Output at line nu stabilised each shift. "
    "Yield on line nu tracked the nu stabilisation. "
    "Therefore line nu output stabilised each shift across "
    "the nu production window.",
    "Engagement with feature xi rose each release. "
    "Session counts on feature xi tracked the xi rise. "
    "Therefore feature xi engagement rose each release "
    "across the xi release window.",
    "Bookings for tour omicron climbed each season. "
    "Reviews of tour omicron tracked the omicron climb. "
    "Therefore tour omicron bookings climbed each season "
    "across the omicron review window.",
    "Throughput on lane pi grew each shift. "
    "Latency on lane pi stayed under the pi target. "
    "Therefore lane pi throughput grew each shift across "
    "the pi operations window.",
)


# ---------------------------------------------------------------------------
# Novel entity — high concl novelty
# ---------------------------------------------------------------------------

_NE = (
    "The autumn harvest produced abundant grain. "
    "Storage facilities remained dry throughout the season. "
    "Therefore the village hosted an architectural prize "
    "ceremony.",
    "The hiking club walked twenty trails in the spring. "
    "Their boots wore out at a typical rate. "
    "Therefore municipal libraries opened earlier on "
    "Sundays.",
    "The bridge survey measured deflection regularly. "
    "Maintenance teams inspected the trusses on schedule. "
    "Therefore the soup of the day featured wild mushrooms.",
    "Members of the orchestra rehearsed for six weeks. "
    "Their instruments were tuned to concert pitch. "
    "Therefore industrial output in the next county rose.",
    "Beekeepers logged steady production through summer. "
    "Their hives were sheltered from prevailing winds. "
    "Therefore the chess club held its tournament outdoors.",
    "Field crews completed the survey on schedule. "
    "Reports were filed in the project archive. "
    "Therefore the festival organisers selected a new venue.",
    "The transit agency added one bus on a route. "
    "Operators logged the schedule change. "
    "Therefore the literary society held its annual gala.",
    "The library updated its digital catalogue. "
    "Patrons noted the longer access window. "
    "Therefore the wildlife reserve announced new trails.",
    "The maintenance team patched the network outage. "
    "Operations logged the resolution in the queue. "
    "Therefore the symphony released its season programme.",
    "The committee reviewed the draft proposal. "
    "Members submitted written comments. "
    "Therefore the baking competition added new categories.",
    "The painters refreshed the corridor walls last spring. "
    "Their estimates matched the supervisor's projection. "
    "Therefore the philharmonic toured the southern provinces.",
    "The crew patched the roadway over two evenings. "
    "Traffic returned to typical patterns. "
    "Therefore the zoological society opened a new aviary.",
    "Volunteers planted seedlings throughout the park. "
    "Each row matched the planting schedule. "
    "Therefore the rowing club hosted an alumni reunion.",
    "Inspectors logged hull readings during the survey. "
    "Each reading matched the typical baseline. "
    "Therefore the literary press launched a new imprint.",
    "Stage crews rehearsed the lighting for two evenings. "
    "Each cue matched the published cue sheet. "
    "Therefore the cycling federation announced a winter race.",
    "Custodians cleaned the assembly hall over the weekend. "
    "Each task matched the cleaning roster. "
    "Therefore the philatelic society scheduled a "
    "biannual expo.",
)


# ---------------------------------------------------------------------------
# Ambiguity decisiveness — hedge-token conclusion
# ---------------------------------------------------------------------------

_AD = (
    "The pilot reduced wait times in two clinics. "
    "Patient satisfaction climbed in both clinics. "
    "Therefore the protocol may also benefit longer-stay "
    "patients in the future.",
    "Output rose during the afternoon shift. "
    "Material costs were stable across the shift. "
    "Therefore the schedule might also improve evening "
    "throughput.",
    "The system stabilised after the migration. "
    "Operators reviewed each rollout step. "
    "Therefore the migration could also benefit related "
    "systems.",
    "The cohort reported steady gains. "
    "Coaches logged each measurement. "
    "Therefore the cohort might also see continued gains.",
    "The clinic logged steady throughput. "
    "Staff reviewed the protocol carefully. "
    "Therefore the clinic may also exceed next quarter's "
    "target.",
    "The platform logged steady uptime. "
    "Engineers reviewed each deploy. "
    "Therefore the platform could also benefit comparable "
    "deployments.",
    "The team reviewed every incident. "
    "Operators logged each remediation. "
    "Therefore the team may also avoid future incidents.",
    "The protocol stabilised across runs. "
    "Engineers documented each window. "
    "Therefore the protocol might also work in adjacent "
    "deployments.",
    "The cohort reported gains. "
    "Researchers logged each endpoint. "
    "Therefore the protocol could also generalise to a "
    "broader population.",
    "The clinic cleared every audit point. "
    "Staff reviewed each finding. "
    "Therefore the clinic may also benefit from continued "
    "review cycles.",
    "The depot logged steady inbound volume. "
    "Dispatchers reviewed each routing sheet. "
    "Therefore the depot may also handle peak-season volume.",
    "The branch reported steady deposits. "
    "Tellers reviewed each ledger entry. "
    "Therefore the branch might also exceed regional "
    "benchmarks.",
    "The fleet logged steady fuel use. "
    "Mechanics reviewed each maintenance log. "
    "Therefore the fleet could also stay within next year's "
    "budget.",
    "The factory stabilised throughput. "
    "Operators reviewed each shift report. "
    "Therefore the factory may also meet the regional output "
    "benchmark.",
    "The library logged steady circulation. "
    "Staff reviewed each catalogue update. "
    "Therefore the library might also achieve its readership "
    "target.",
    "The studio reported steady attendance. "
    "Coaches reviewed each scheduling sheet. "
    "Therefore the studio could also surpass comparable "
    "studios.",
)


def all_transfer_ncs() -> tuple[TransferNC, ...]:
    return (
        _make(
            "NC-MA-", _MA,
            TaxonomyClass.MT_MODAL_ASYMMETRY.value,
            "modal_asymmetry",
        )
        + _make(
            "NC-NA-", _NA,
            TaxonomyClass.MT_NEGATION_ASYMMETRY.value,
            "negation_asymmetry",
        )
        + _make(
            "NC-UL-", _UL,
            TaxonomyClass.MT_UNIVERSAL_LEAP.value,
            "universal_leap",
        )
        + _make(
            "NC-OL-", _OL,
            TaxonomyClass.MT_OVERLAP_LOOP.value,
            "overlap_loop",
        )
        + _make(
            "NC-NE-", _NE,
            TaxonomyClass.MT_NOVEL_ENTITY.value,
            "novel_entity",
        )
        + _make(
            "NC-AD-", _AD,
            TaxonomyClass.MT_AMBIGUITY_DECISIVENESS.value,
            "ambiguity_decisiveness",
        )
    )


def classify_nc(nc: TransferNC) -> str:
    """Classify an NC through the same per-sample pipeline
    the taxonomy uses on real failures. The NC is wrapped
    in a TransferChain with INVALID ground-truth (since the
    chains demonstrate failures) for feature extraction.
    """
    chain = TransferChain(
        chain_id=nc.nc_id, domain="nc", text=nc.text,
        ground_truth=(
            "AMBIGUOUS"
            if nc.expected_class == (
                "MT_AMBIGUITY_DECISIVENESS"
            )
            else "INVALID"
        ),
        rationale=nc.family,
    )
    sample = extract_features(chain)
    return classify_sample_features(sample.features)


def classification_accuracy() -> float:
    ncs = all_transfer_ncs()
    correct = sum(
        1 for nc in ncs
        if classify_nc(nc) == nc.expected_class
    )
    return round(correct / len(ncs), 6)


__all__ = [
    "TransferNC", "all_transfer_ncs",
    "classification_accuracy", "classify_nc",
]
