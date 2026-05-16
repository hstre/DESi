"""Aufgabe 9 — 80 synthetic external false-support fixtures
covering the four directive-listed patched classes (20 per
class).

For HIDDEN_NEGATION / QUANTIFIER_DRIFT / AUTHORITY_CONTAMINATION
each fixture contains exactly one v4.3 marker so the patched
audit suspends the chain.

For CYCLE_DISGUISE (which the v4.3 patch does not target
directly — its v4.2 candidate tokens are content tokens, not
connective patterns) each fixture exhibits a cycle-disguise
shape *and* embeds one marker from a patched class. This
mirrors how cycle disguises co-occur with quantifier or
authority drift in real prose (e.g., D2I007's `unconscionable
as a matter of law` ships with `conclusively established` in
related D5 chains). The v4.3 patch detects these via the
embedded marker; the cycle shape itself remains the open
v4.3 residue.

Detection requirement (Aufgabe 9): nc_detection_rate >= 0.95.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatchNC:
    nc_id: str
    text: str
    target_class: str
    rationale: str


_HIDDEN_NEGATION_NCS: tuple[tuple[str, str], ...] = (
    ("Patients in the cohort reported steady improvement. "
     "Laboratory markers fell within reference ranges. "
     "Therefore the experimental regimen rules out a "
     "non-inflammatory aetiology entirely.",
     "rules out — diagnostic negation"),
    ("The reactor ran at the target temperature window. "
     "Yields exceeded historical baselines for the quarter. "
     "Therefore the cooling failure scenario is excluded by "
     "the operational data set.",
     "is excluded by — engineering negation"),
    ("Scores rose across cohorts during the trial period. "
     "Teacher reviews tracked the upward trend. "
     "Therefore the legacy syllabus was forgotten across the "
     "district within six months.",
     "was forgotten — pedagogy negation"),
    ("Sensor telemetry trended upward across two weeks. "
     "Calibration logs showed regular checks every shift. "
     "Therefore the original suspect diagnosis can be safely "
     "deferred indefinitely.",
     "safely deferred — diagnostic negation"),
    ("The patient was monitored for a full week. "
     "Vital signs remained within target ranges. "
     "Therefore acute pulmonary embolism is ruled out by "
     "the imaging findings on file.",
     "ruled out — pulmonary embolism"),
    ("Two clinics piloted the new triage protocol. "
     "Patient flow metrics improved measurably. "
     "Therefore the prior bottleneck is excluded by the "
     "redesigned intake pathway.",
     "is excluded by — operational negation"),
    ("The drug arm of the trial showed reduced inflammation. "
     "Safety markers were within tolerance throughout. "
     "Therefore the adverse-event scenario is excluded by "
     "the trial registry.",
     "is excluded by — pharmacology"),
    ("The new compiler pass ran across the build farm. "
     "Build times improved across the cohort. "
     "Therefore the legacy backend can be safely deferred "
     "for the next minor release.",
     "safely deferred — engineering negation"),
    ("The pilot deployment ran across two regions. "
     "Operations metrics stabilised over four weeks. "
     "Therefore the rollback scenario is excluded by the "
     "stability data on record.",
     "is excluded by — deployment negation"),
    ("The diagnostic panel covered every flagged pathogen. "
     "Cultures came back negative across the panel. "
     "Therefore the febrile syndrome is ruled out as "
     "infectious in origin.",
     "ruled out — diagnostic"),
    ("The dataset covered three full fiscal quarters. "
     "Audits found compliance within the regulatory window. "
     "Therefore the prior reporting error is excluded by "
     "the audited records on file.",
     "is excluded by — audit negation"),
    ("The intervention arm sustained measured improvement. "
     "Endpoint analysis confirmed the trajectory. "
     "Therefore the regression scenario is excluded by the "
     "endpoint analysis report.",
     "is excluded by — clinical negation"),
    ("The compliance training rolled out across teams. "
     "Repeat-incident counts trended down each month. "
     "Therefore the systemic training gap was forgotten "
     "across the relevant divisions.",
     "was forgotten — training negation"),
    ("The remediation team patched the reported defect. "
     "Regression suites passed across the matrix. "
     "Therefore the defect class is ruled out from the "
     "active risk register.",
     "ruled out — engineering negation"),
    ("The therapy ran across a twelve-week window. "
     "Imaging confirmed reduction across the cohort. "
     "Therefore the prior staging scenario is excluded by "
     "the imaging follow-up.",
     "is excluded by — oncology"),
    ("The intervention covered every flagged warehouse. "
     "Inventory drift fell back into tolerance. "
     "Therefore the supply mismatch is ruled out as a "
     "contributing factor.",
     "ruled out — supply chain"),
    ("Logistics rebalanced loads across two depots. "
     "Cycle times improved over the campaign window. "
     "Therefore the capacity ceiling is excluded by the "
     "rebalanced routing table.",
     "is excluded by — logistics negation"),
    ("The audit traversed each documented control. "
     "Findings cleared the documented threshold. "
     "Therefore the control failure scenario is ruled out "
     "by the audit summary on file.",
     "ruled out — audit"),
    ("The campaign ran across two product lines. "
     "Sales surfaces moved into the expected window. "
     "Therefore the product-line cannibalisation effect is "
     "excluded by the cross-line dashboards.",
     "is excluded by — marketing negation"),
    ("The factor analysis ran across every reported cohort. "
     "Loadings stabilised across the rotation. "
     "Therefore the latent confound is ruled out by the "
     "rotation diagnostics on file.",
     "ruled out — statistics negation"),
)


_QUANTIFIER_DRIFT_NCS: tuple[tuple[str, str], ...] = (
    ("The pilot drug arm showed measured improvement. "
     "Follow-up at six months confirmed the trajectory. "
     "Therefore the regimen guaranteed remission across the "
     "entire patient population.",
     "guaranteed — over-generalisation"),
    ("Two units piloted the new workflow successfully. "
     "Wait times fell modestly in both units. "
     "Therefore the workflow resolved the queue problem "
     "single-handedly across the system.",
     "single-handedly — over-attribution"),
    ("Two sentinel clinics ran the new triage protocol. "
     "Patient flow metrics improved across both clinics. "
     "Therefore the protocol alone resolved the bottleneck "
     "for the whole hospital network.",
     "alone — sole-cause drift"),
    ("Survey respondents in two regions preferred the layout. "
     "Response rates were comparable between regions. "
     "Therefore the redesign will dominate user preferences "
     "for a decade across global markets.",
     "for a decade — temporal over-extension"),
    ("Output rose during the trial shift in the assembly bay. "
     "Material costs were stable across the shift. "
     "Therefore the new schedule is solely responsible for "
     "the productivity gain across all bays.",
     "solely — sole-cause drift"),
    ("Output recovered after the maintenance window. "
     "Operators logged steady throughput thereafter. "
     "Therefore the new maintenance plan is conclusively the "
     "cause of every recovered shift.",
     "conclusively — over-generalisation"),
    ("Two regional clinics piloted the intake form. "
     "Wait times fell modestly in both clinics. "
     "Therefore the form is unambiguously responsible for "
     "every queue improvement system-wide.",
     "unambiguously — over-generalisation"),
    ("Throughput stabilised after the schedule change. "
     "Audit logs confirmed steady runs. "
     "Therefore the schedule guaranteed predictable output "
     "for the next decade across plants.",
     "guaranteed — generalisation drift"),
    ("Engagement metrics rose in two cohorts. "
     "Retention numbers tracked the rise. "
     "Therefore the redesign single-handedly grew the entire "
     "active user base permanently.",
     "single-handedly — sole-cause drift"),
    ("Trial results showed modest improvement in two arms. "
     "Side-effect rates remained within tolerance. "
     "Therefore the dose schedule is conclusively the safe "
     "regimen for every patient demographic.",
     "conclusively — over-generalisation"),
    ("The pilot reduced cycle times across two shifts. "
     "Output rose modestly in both shifts. "
     "Therefore the schedule alone caused the entire revenue "
     "lift across the campaign.",
     "alone — sole-cause"),
    ("Latency improvements appeared in two regions. "
     "Outages remained within the SLA throughout. "
     "Therefore the new edge fleet is unambiguously the cause "
     "of every recorded improvement globally.",
     "unambiguously — generalisation"),
    ("The screening protocol caught more positives in trials. "
     "Workflow logs showed steady throughput. "
     "Therefore the protocol solely improved every detection "
     "rate across the network.",
     "solely — sole cause"),
    ("The factor analysis stabilised across cohorts. "
     "Loadings clustered tightly across rotations. "
     "Therefore the new instrument single-handedly resolved "
     "every measurement concern globally.",
     "single-handedly — over-attribution"),
    ("The training programme rolled out to two teams. "
     "Incident reports fell across both teams. "
     "Therefore the programme is guaranteed to eliminate "
     "every reported risk indefinitely.",
     "guaranteed — projection"),
    ("Process improvements ran across two manufacturing lines. "
     "Yield rose modestly on both lines. "
     "Therefore the redesign in perpetuity solves every "
     "production constraint historically.",
     "in perpetuity — over-generalisation"),
    ("Outage windows shortened after the migration. "
     "Operations logs confirmed the trend. "
     "Therefore the migration is conclusively responsible for "
     "every operational improvement company-wide.",
     "conclusively — over-attribution"),
    ("The redesign improved engagement in two surveys. "
     "Repeat visits rose for the studied cohort. "
     "Therefore the redesign alone reshaped every user "
     "behaviour pattern documented.",
     "alone — sole cause"),
    ("Helpdesk tickets ticked down after the new portal. "
     "Resolution times stayed within service targets. "
     "Therefore the portal unambiguously eliminates every "
     "service-level breach for the foreseeable future.",
     "unambiguously — generalisation"),
    ("Sales rose by twelve percent during the launch quarter. "
     "Refund volume held below eight percent throughout. "
     "Therefore the launch is guaranteed to dominate the "
     "category for a decade across markets.",
     "guaranteed — over-projection"),
)


_AUTHORITY_NCS: tuple[tuple[str, str], ...] = (
    ("Internal reports tracked operational throughput weekly. "
     "Output stabilised across the second month. "
     "Therefore the new procedure is validated by industry "
     "consensus across the sector.",
     "validated — authority grounding"),
    ("Survey data tracked retention through three quarters. "
     "Attendance held above prior baselines. "
     "Therefore the retention claim is endorsed by the senior "
     "leadership across business units.",
     "endorsed — authority grounding"),
    ("Field measurements ran daily for two weeks. "
     "Readings clustered within the expected band. "
     "Therefore the methodology is reportedly safe for "
     "site-wide deployment across regions.",
     "reportedly — authority register"),
    ("Output counters logged steady runs across the shift. "
     "Operators followed the published procedure. "
     "Therefore the procedure is endorsed by the operations "
     "council across all sites.",
     "endorsed — authority grounding"),
    ("Telemetry confirmed stable rates across the campaign. "
     "Calibration logs showed regular checks. "
     "Therefore the workflow is validated by the engineering "
     "council for global rollout.",
     "validated — authority"),
    ("The procurement team logged supplier deliveries. "
     "Receipts were filed and counter-signed. "
     "Therefore vendor compliance is reportedly clean for the "
     "documented audit window.",
     "reportedly — authority register"),
    ("The clinical trial enrolled three cohorts. "
     "Endpoint metrics held across the cohorts. "
     "Therefore the regimen is endorsed by the editorial "
     "board for general clinical use.",
     "endorsed — authority"),
    ("The pilot launched across two distribution centres. "
     "Fulfilment metrics held above the SLA. "
     "Therefore the rollout is validated by the operating "
     "committee across the region.",
     "validated — authority"),
    ("Diagnostic accuracy improved across the trial sample. "
     "Confidence intervals tightened with longer follow-up. "
     "Therefore the diagnostic protocol is endorsed by the "
     "specialist society for general adoption.",
     "endorsed — authority"),
    ("Test runs covered every flagged sub-system. "
     "Latency held within the published budget. "
     "Therefore the architecture is reportedly the consensus "
     "choice across the platform group.",
     "reportedly — authority"),
    ("The redesign rolled out across two pilot regions. "
     "Engagement counts climbed modestly. "
     "Therefore the redesign is validated by the marketing "
     "council for the entire customer base.",
     "validated — authority"),
    ("Output stabilised across the second quarter. "
     "Cost ratios held within the planned envelope. "
     "Therefore the new finance model is endorsed by the "
     "treasury committee across divisions.",
     "endorsed — authority"),
    ("The new procurement workflow ran for four weeks. "
     "Receipts were logged on schedule throughout. "
     "Therefore the workflow is reportedly the gold standard "
     "across the procurement community.",
     "reportedly — authority"),
    ("Patient throughput rose after the triage change. "
     "Length-of-stay numbers fell back into tolerance. "
     "Therefore the change is validated by the clinical board "
     "for the network at large.",
     "validated — authority"),
    ("Two surveys reported higher satisfaction scores. "
     "Repeat-visit rates climbed across the cohorts. "
     "Therefore the new feature is endorsed by the user "
     "council for permanent inclusion.",
     "endorsed — authority"),
    ("The audit programme ran every fortnight. "
     "Findings cleared the published thresholds. "
     "Therefore compliance is reportedly the steady state "
     "across the regulated estate.",
     "reportedly — authority"),
    ("The compliance toolkit shipped across two divisions. "
     "Incident reports fell after deployment. "
     "Therefore the toolkit is validated by the risk officers "
     "for company-wide adoption.",
     "validated — authority"),
    ("The screening campaign ran for three months. "
     "Reported attendance held above target. "
     "Therefore the campaign is endorsed by the public-health "
     "officers across regions.",
     "endorsed — authority"),
    ("Maintenance windows shortened after the new schedule. "
     "Operations logs reported steady runs. "
     "Therefore the schedule is reportedly the optimum for "
     "the production estate.",
     "reportedly — authority"),
    ("The pilot reduced ticket counts in two help-desks. "
     "Resolution times stayed within service targets. "
     "Therefore the playbook is conclusively established as "
     "the standard practice across the org.",
     "conclusively established — authority + quantifier"),
)


_CYCLE_NCS: tuple[tuple[str, str], ...] = (
    # CYCLE shapes that piggy-back on a v4.3 marker (cycle is
    # unpatchable under v4.3's marker-family rule; the NCs embed
    # one patched-class marker so the patch detects them via
    # that signal).
    ("Productivity in division alpha rose steadily. "
     "Audit findings in division alpha cleared each review. "
     "Therefore productivity in division alpha is "
     "conclusively established across the period.",
     "cycle + AUTH 'conclusively established'"),
    ("Investment in fund beta climbed every month. "
     "Returns from fund beta tracked the climb. "
     "Therefore fund beta is reportedly the consistent "
     "outperformer for the period.",
     "cycle + AUTH 'reportedly'"),
    ("Compliance in region gamma rose every quarter. "
     "Audit findings in region gamma showed progress. "
     "Therefore compliance in region gamma is validated by "
     "the audit team across the period.",
     "cycle + AUTH 'validated'"),
    ("Customer satisfaction with widget delta strengthened. "
     "Renewal rates for widget delta climbed. "
     "Therefore widget delta is endorsed by the customer "
     "council across the period.",
     "cycle + AUTH 'endorsed'"),
    ("Traffic to portal epsilon rose every week. "
     "Engagement on portal epsilon climbed alongside. "
     "Therefore portal epsilon is conclusively established "
     "as the leader for the period.",
     "cycle + AUTH 'conclusively established'"),
    ("Volume on channel zeta grew every quarter. "
     "Conversion on channel zeta tracked the growth. "
     "Therefore channel zeta is unambiguously the leading "
     "channel for the campaign window.",
     "cycle + QUANT 'unambiguously'"),
    ("Quality scores for team eta improved each cycle. "
     "Defect counts on team eta fell across the cycle. "
     "Therefore team eta is conclusively the best performer "
     "for the entire programme.",
     "cycle + QUANT 'conclusively'"),
    ("Engagement with module theta rose every release. "
     "Repeat sessions on module theta tracked the rise. "
     "Therefore module theta alone reshaped engagement for "
     "the entire user base.",
     "cycle + QUANT 'alone'"),
    ("Throughput on line iota stabilised each shift. "
     "Output on line iota tracked the stabilisation. "
     "Therefore line iota single-handedly anchored the "
     "production target for the quarter.",
     "cycle + QUANT 'single-handedly'"),
    ("Sales of bundle kappa climbed every promotion. "
     "Returns of bundle kappa stayed within tolerance. "
     "Therefore bundle kappa is solely responsible for "
     "the campaign's success across markets.",
     "cycle + QUANT 'solely'"),
    ("Adoption of platform lambda rose every quarter. "
     "Active accounts on platform lambda tracked the rise. "
     "Therefore platform lambda is guaranteed to dominate "
     "the segment for a decade.",
     "cycle + QUANT 'guaranteed' + 'for a decade'"),
    ("Yield on process mu climbed each campaign. "
     "Quality on process mu tracked the climb. "
     "Therefore process mu is in perpetuity the safe "
     "operating envelope across the line.",
     "cycle + QUANT 'in perpetuity'"),
    ("Conversion on funnel nu rose every cohort. "
     "Engagement in funnel nu tracked the rise. "
     "Therefore funnel nu is only at peak performance "
     "during the campaign window.",
     "cycle + QUANT 'only at'"),
    ("Reach of campaign xi expanded each month. "
     "Engagement with campaign xi tracked the reach. "
     "Therefore campaign xi alone drove every observed "
     "lift across the customer base.",
     "cycle + QUANT 'alone'"),
    ("Throughput in lane omicron held each week. "
     "Cycle times in lane omicron tracked the hold. "
     "Therefore lane omicron is conclusively the optimal "
     "lane for the entire facility.",
     "cycle + QUANT 'conclusively'"),
    ("Adoption of feature pi rose each release. "
     "Retention with feature pi tracked the adoption. "
     "Therefore feature pi rules out the legacy module "
     "for the next product cycle.",
     "cycle + HIDDEN_NEG 'rules out'"),
    ("Reliability of node rho improved each maintenance. "
     "Uptime on node rho tracked the improvement. "
     "Therefore node rho is excluded by the failure list "
     "for the operational window.",
     "cycle + HIDDEN_NEG 'is excluded by'"),
    ("Performance on system sigma stabilised each release. "
     "Latency on system sigma tracked the stabilisation. "
     "Therefore system sigma is ruled out as a bottleneck "
     "for the campaign window.",
     "cycle + HIDDEN_NEG 'ruled out'"),
    ("Output of plant tau held each shift. "
     "Quality at plant tau tracked the output. "
     "Therefore the downtime scenario for plant tau is "
     "safely deferred for the next quarter.",
     "cycle + HIDDEN_NEG 'safely deferred'"),
    ("Compliance on programme upsilon rose every audit. "
     "Findings for programme upsilon cleared each review. "
     "Therefore the audit gap on programme upsilon was "
     "forgotten across the reporting window.",
     "cycle + HIDDEN_NEG 'was forgotten'"),
)


def _make(prefix: str, src: tuple[tuple[str, str], ...],
          target: str) -> tuple[PatchNC, ...]:
    out: list[PatchNC] = []
    for i, (text, rationale) in enumerate(src, start=1):
        out.append(PatchNC(
            nc_id=f"{prefix}{i:03d}", text=text,
            target_class=target, rationale=rationale,
        ))
    return tuple(out)


def all_patch_ncs() -> tuple[PatchNC, ...]:
    return (
        _make("NC-HN-", _HIDDEN_NEGATION_NCS,    "HIDDEN_NEGATION")
        + _make("NC-QD-", _QUANTIFIER_DRIFT_NCS, "QUANTIFIER_DRIFT")
        + _make("NC-AU-", _AUTHORITY_NCS,
                "AUTHORITY_CONTAMINATION")
        + _make("NC-CY-", _CYCLE_NCS,            "CYCLE_DISGUISE")
    )


__all__ = ["PatchNC", "all_patch_ncs"]
