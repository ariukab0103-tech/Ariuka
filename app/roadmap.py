"""
Backcasting Roadmap Generator for SSBJ Compliance

Generates a phased implementation roadmap working backwards from the target
compliance year, tailored to the entity's actual gap assessment results.

SSBJ Timeline Context:
- Mandatory disclosure begins for prime market companies
- Limited assurance starts ONE YEAR after mandatory disclosure
- Assurance scope may expand after the third year
- Initial limited assurance covers Scope 1 & 2 GHG only
"""

from datetime import date
from app.ssbj_criteria import SSBJ_CRITERIA


def _extract_year(fiscal_year_str):
    """Extract a 4-digit year from fiscal_year string like '2027', 'FY2027', '2027年3月期'."""
    import re
    match = re.search(r"20\d{2}", str(fiscal_year_str))
    return int(match.group()) if match else None


def _classify_gaps(responses):
    """Classify gaps by area for roadmap task generation."""
    criteria_map = {c["id"]: c for c in SSBJ_CRITERIA}
    gaps = {
        "la_critical": [],      # in_scope, score < 3
        "governance": [],       # GOV-* gaps
        "strategy": [],         # STR-* gaps
        "risk": [],             # RISK-* gaps
        "metrics": [],          # MET-* gaps
        "it_needed": False,     # whether IT systems are recommended
        "total_gaps": 0,
        "total_scored": 0,
        "avg_score": 0,
    }

    scores = []
    for resp in responses:
        if resp.score is None:
            continue
        scores.append(resp.score)
        c = criteria_map.get(resp.criterion_id)
        if not c:
            continue

        if resp.score < 3:
            gaps["total_gaps"] += 1
            gap_info = {
                "id": resp.criterion_id,
                "category": c["category"],
                "score": resp.score,
                "obligation": c["obligation"],
                "la_scope": c["la_scope"],
                "la_priority": c["la_priority"],
                "minimum_action": c.get("minimum_action", ""),
                "pillar": c["pillar"],
            }

            if c["la_scope"] == "in_scope":
                gaps["la_critical"].append(gap_info)

            if c["pillar"] == "Governance":
                gaps["governance"].append(gap_info)
            elif c["pillar"] == "Strategy":
                gaps["strategy"].append(gap_info)
            elif c["pillar"] == "Risk Management":
                gaps["risk"].append(gap_info)
            elif c["pillar"] == "Metrics & Targets":
                gaps["metrics"].append(gap_info)

    # IT systems needed if metrics gaps exist or score < 2 on MET items
    if gaps["metrics"]:
        met_scores = [g["score"] for g in gaps["metrics"]]
        if any(s < 2 for s in met_scores):
            gaps["it_needed"] = True

    gaps["total_scored"] = len(scores)
    gaps["avg_score"] = round(sum(scores) / len(scores), 1) if scores else 0
    return gaps


def generate_roadmap(assessment, responses_list):
    """
    Generate a backcasting roadmap from the compliance year.

    Returns a dict with:
    - compliance_year: target year
    - assurance_year: compliance_year + 1
    - today: current date
    - months_remaining: months until compliance
    - urgency: 'critical' / 'tight' / 'adequate' / 'comfortable'
    - phases: list of phase dicts with tasks
    - summary: overall readiness summary
    """
    compliance_year = _extract_year(assessment.fiscal_year)
    if not compliance_year:
        compliance_year = date.today().year + 2  # default: 2 years from now

    # Compliance date = end of fiscal year (March 31 for Japanese companies)
    compliance_date = date(compliance_year, 3, 31)
    assurance_date = date(compliance_year + 1, 3, 31)
    today = date.today()

    months_remaining = (compliance_date.year - today.year) * 12 + (compliance_date.month - today.month)
    months_to_assurance = months_remaining + 12

    # Urgency level
    if months_remaining <= 6:
        urgency = "critical"
    elif months_remaining <= 12:
        urgency = "tight"
    elif months_remaining <= 24:
        urgency = "adequate"
    else:
        urgency = "comfortable"

    # Classify gaps
    gaps = _classify_gaps(responses_list)

    # Generate phases based on timeline and gaps
    phases = _generate_phases(
        compliance_date, assurance_date, today, months_remaining, gaps
    )

    # Summary
    summary = _generate_summary(gaps, months_remaining, urgency)

    return {
        "compliance_year": compliance_year,
        "compliance_date": compliance_date,
        "assurance_year": compliance_year + 1,
        "assurance_date": assurance_date,
        "today": today,
        "months_remaining": months_remaining,
        "months_to_assurance": months_to_assurance,
        "urgency": urgency,
        "phases": phases,
        "gaps": gaps,
        "summary": summary,
    }


def _generate_phases(compliance_date, assurance_date, today, months_remaining, gaps):
    """Generate implementation phases with specific tasks."""
    phases = []

    # Phase 1: Foundation & Management Buy-in (Now to +3 months)
    p1_tasks = {
        "management": [
            "Present gap analysis results to executive management / board",
            "Secure budget allocation for SSBJ compliance project",
            "Appoint a Sustainability Disclosure Project Owner (executive sponsor)",
            "Establish cross-functional working group (Finance, Legal, IR, Operations, ESG)",
        ],
        "technical": [
            "Complete current gap assessment and baseline scoring",
            "Map existing data sources for GHG emissions (energy bills, fuel records, refrigerant logs)",
            "Inventory existing IT systems that hold sustainability data (ERP, utility management, etc.)",
        ],
        "assurance": [
            "Research potential assurance providers (Big 4, mid-tier firms with ISAE 3000 experience)",
            "Understand limited assurance scope: Scope 1 & 2 GHG only in initial phase",
            "Review ISAE 3000/3410 and ISSA 5000 requirements at high level",
        ],
    }

    if gaps["la_critical"]:
        p1_tasks["management"].append(
            f"URGENT: Highlight {len(gaps['la_critical'])} limited assurance critical gaps to management — these will be directly examined by auditors"
        )

    phases.append({
        "number": 1,
        "title": "Foundation & Management Buy-in",
        "subtitle": "Gap analysis, governance setup, project launch",
        "duration": "Months 1-3",
        "icon": "bi-flag",
        "color": "primary",
        "tasks": p1_tasks,
    })

    # Phase 2: Governance & Policy Framework (Months 3-6)
    p2_tasks = {
        "management": [
            "Board formally designates sustainability oversight committee",
            "Approve sustainability governance policy (or add to existing corporate governance code)",
            "Define management roles: who owns GHG data, who reviews, who signs off",
            "Set up quarterly sustainability reporting to board",
        ],
        "technical": [],
        "assurance": [
            "Send RFP to 2-3 assurance providers for limited assurance engagement",
            "Schedule introductory meeting with shortlisted firms",
            "Discuss assurance scope, timeline, and evidence expectations",
        ],
    }

    if gaps["governance"]:
        for g in gaps["governance"]:
            if g["score"] <= 1:
                p2_tasks["management"].append(
                    f"Fix {g['id']} ({g['category']}): currently score {g['score']} — needs formal documentation"
                )

    # IT assessment
    if gaps["it_needed"]:
        p2_tasks["technical"].extend([
            "Evaluate GHG calculation software options (e.g., Zeroboard, Persefoni, booost, or spreadsheet-based)",
            "Decide build vs. buy: dedicated GHG platform vs. enhanced spreadsheets",
            "Map data flow: source systems → calculation → reporting → disclosure",
        ])
    else:
        p2_tasks["technical"].extend([
            "Document current data collection process for GHG emissions",
            "Create standardized templates for activity data collection from sites/subsidiaries",
            "Define calculation methodology document (emission factors, sources, methodology)",
        ])

    phases.append({
        "number": 2,
        "title": "Governance & Policy Framework",
        "subtitle": "Policies, roles, assurance provider selection",
        "duration": "Months 3-6",
        "icon": "bi-building",
        "color": "info",
        "tasks": p2_tasks,
    })

    # Phase 3: Process & System Implementation (Months 6-12)
    p3_tasks = {
        "management": [
            "Review progress at board level — mid-project checkpoint",
            "Approve internal controls framework for sustainability data",
            "Ensure sustainability KPIs are embedded in management reporting",
        ],
        "technical": [],
        "assurance": [
            "Select and formally engage assurance provider",
            "Pre-engagement planning meeting: agree scope, materiality, evidence requirements",
            "Assurance provider reviews your internal controls design (advisory, not assurance yet)",
        ],
    }

    if gaps["it_needed"]:
        p3_tasks["technical"].extend([
            "Implement GHG calculation tool / build calculation spreadsheets with controls",
            "Set up automated data collection from source systems where possible",
            "Implement data validation rules (range checks, completeness checks, year-on-year comparison)",
            "Create audit trail: who entered data, when, what changed",
            "Test system with prior year data as dry run",
        ])
    else:
        p3_tasks["technical"].extend([
            "Formalize GHG calculation procedures in a written methodology document",
            "Implement calculation review checklist (4-eyes principle)",
            "Set up evidence filing system (organized by criterion, year, source)",
            "Collect and organize prior year activity data as baseline",
        ])

    # Add metrics-specific tasks
    if gaps["metrics"]:
        for g in gaps["metrics"]:
            if g["la_scope"] == "in_scope" and g["score"] < 2:
                p3_tasks["technical"].append(
                    f"CRITICAL: Build process for {g['id']} ({g['category']}) — score {g['score']}, needs formal procedures"
                )

    # Strategy and risk management
    if gaps["strategy"]:
        p3_tasks["management"].append(
            f"Address {len(gaps['strategy'])} strategy disclosure gaps: scenario analysis, transition plans"
        )
    if gaps["risk"]:
        p3_tasks["management"].append(
            f"Address {len(gaps['risk'])} risk management gaps: integrate sustainability into ERM framework"
        )

    phases.append({
        "number": 3,
        "title": "Process & System Implementation",
        "subtitle": "IT systems, data collection, internal controls",
        "duration": "Months 6-12",
        "icon": "bi-gear",
        "color": "warning",
        "tasks": p3_tasks,
    })

    # Phase 4: Dry Run & Internal Review (Months 12-18)
    p4_tasks = {
        "management": [
            "Management sign-off on draft sustainability disclosure",
            "Board reviews draft disclosure before publication",
            "Assess completeness: all 23 SSBJ criteria covered?",
        ],
        "technical": [
            "Complete full GHG inventory calculation (Scope 1 & 2) using actual data",
            "Prepare draft SSBJ-compliant disclosure document",
            "Run internal quality assurance review on all data and disclosures",
            "Document all assumptions, estimation methodologies, and data limitations",
            "Organize evidence files as if auditor is coming tomorrow",
        ],
        "assurance": [
            "Share draft disclosure with assurance provider for informal review",
            "Assurance provider conducts readiness assessment (gap-check against ISAE 3000)",
            "Address any findings from readiness assessment",
            "Rehearse management inquiry sessions (auditor will interview key staff)",
        ],
    }

    phases.append({
        "number": 4,
        "title": "Dry Run & Internal Review",
        "subtitle": "Trial disclosure, assurance readiness check",
        "duration": "Months 12-18",
        "icon": "bi-clipboard-check",
        "color": "success",
        "tasks": p4_tasks,
    })

    # Phase 5: First Disclosure (Months 18-24 / Compliance Year)
    p5_tasks = {
        "management": [
            "Final board approval of sustainability disclosure",
            "CEO/CFO sign-off on disclosed information",
            "Integrate sustainability disclosure into annual securities report (有価証券報告書)",
        ],
        "technical": [
            "Finalize all calculations with year-end actual data",
            "Complete all SSBJ-required disclosures in proper format",
            "Final quality review and cross-reference check against SSBJ criteria",
            "Archive all supporting evidence with complete audit trail",
        ],
        "assurance": [
            "Assurance provider is on standby for post-disclosure engagement",
            "Ensure evidence packages are organized for handoff to auditor",
            "Prepare management representation letter template",
        ],
    }

    phases.append({
        "number": 5,
        "title": "First Mandatory Disclosure",
        "subtitle": f"Publish SSBJ-compliant disclosure (FY{compliance_date.year})",
        "duration": f"Compliance Year ({compliance_date.year})",
        "icon": "bi-file-earmark-text",
        "color": "danger",
        "tasks": p5_tasks,
    })

    # Phase 6: First Limited Assurance (Year + 1)
    p6_tasks = {
        "management": [
            "Board informed of upcoming assurance engagement and timeline",
            "Designate internal liaison team for auditor interactions",
            "Budget for assurance engagement fees",
        ],
        "technical": [
            "Provide complete evidence packages to assurance provider",
            "Respond to information requests and clarification queries",
            "Support site visits if required by assurance provider",
            "Address any findings or adjustments identified during assurance",
        ],
        "assurance": [
            "Formal limited assurance engagement begins (ISAE 3000 / ISSA 5000)",
            "Assurance procedures: inquiry, analytical review, limited testing",
            "Scope: Scope 1 & 2 GHG emissions quantification and disclosure",
            "Receive assurance report — target: unqualified conclusion",
            "Plan for scope expansion in subsequent years",
        ],
    }

    phases.append({
        "number": 6,
        "title": "First Limited Assurance",
        "subtitle": f"Auditor examines Scope 1 & 2 (FY{assurance_date.year})",
        "duration": f"Assurance Year ({assurance_date.year})",
        "icon": "bi-shield-check",
        "color": "dark",
        "tasks": p6_tasks,
    })

    return phases


def _generate_summary(gaps, months_remaining, urgency):
    """Generate an overall readiness summary."""
    lines = []

    if gaps["avg_score"] >= 3:
        lines.append("Overall assessment indicates the entity is approaching assurance readiness.")
    elif gaps["avg_score"] >= 2:
        lines.append("The entity has foundational processes but significant work remains for compliance.")
    else:
        lines.append("The entity is at an early stage. Substantial effort is needed across all pillars.")

    if gaps["la_critical"]:
        lines.append(
            f"{len(gaps['la_critical'])} criteria directly in limited assurance scope are below threshold. "
            f"These are the highest priority — auditors will examine these first."
        )

    lines.append(f"{gaps['total_gaps']} total gaps identified (score below 3 out of {gaps['total_scored']} scored).")

    if gaps["it_needed"]:
        lines.append(
            "IT system investment is recommended: GHG calculation and data management tools "
            "will improve data quality and auditability."
        )
    else:
        lines.append(
            "No major IT investment appears necessary at this time. "
            "Focus on formalizing existing processes and documentation."
        )

    if urgency == "critical":
        lines.append(
            f"TIMELINE CRITICAL: Only {months_remaining} months until compliance. "
            f"Accelerate all phases — consider external consultants to supplement internal resources."
        )
    elif urgency == "tight":
        lines.append(
            f"Timeline is tight ({months_remaining} months). Prioritize limited assurance scope items "
            f"and begin assurance provider discussions immediately."
        )

    return lines
