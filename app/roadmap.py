"""
Backcasting Roadmap Generator for SSBJ Compliance

Generates a phased implementation roadmap working backwards from the target
compliance year, tailored to the entity's actual gap assessment results.

SSBJ Timeline Context:
- Mandatory disclosure begins for prime market companies
- Limited assurance starts ONE YEAR after mandatory disclosure
- Initial limited assurance (first 2 years): Scope 1 & 2, Governance, and Risk Management
- From 3rd year: scope expansion to full SSBJ disclosures under consideration
- Assurance standard: ISSA 5000 (JICPA drafting aligned domestic practice guideline)
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
    - pre_assurance: pre-assurance engagement guidance
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

    # Pre-assurance engagement guidance
    pre_assurance = _generate_pre_assurance_guide(gaps, months_remaining, months_to_assurance, compliance_date)

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
        "pre_assurance": pre_assurance,
    }


def _calculate_phase_schedule(months_remaining):
    """Calculate dynamic phase durations based on available time.

    Returns a list of (start_month, end_month) tuples for phases 1-6.
    Phase 7 (assurance) is always the year after compliance.
    """
    m = max(months_remaining, 3)  # floor at 3 months

    if m >= 24:
        # Comfortable: standard 24-month plan
        return [
            (1, 3), (3, 6), (6, 12), (12, 18), (15, 21), (18, 24),
        ]
    elif m >= 18:
        # Adequate: compress to 18 months
        return [
            (1, 2), (2, 5), (5, 10), (10, 14), (12, 16), (16, m),
        ]
    elif m >= 12:
        # Tight: aggressive compression, overlapping phases
        return [
            (0, 1), (1, 3), (3, 7), (7, 10), (8, 11), (10, m),
        ]
    else:
        # Critical (<12 months): emergency parallel execution
        half = max(2, m // 2)
        q1 = max(1, m // 4)
        q3 = max(4, m * 3 // 4)
        return [
            (0, q1),
            (0, half),         # parallel with phase 1
            (q1, half + 1),
            (half, q3),
            (half + 1, q3 + 1),
            (q3, m),
        ]


def _phase_duration_label(start, end, months_remaining):
    """Format a human-readable duration label from month boundaries."""
    if start == 0 and end <= 1:
        return "Weeks 1-4"
    elif start == 0:
        return f"Months 1-{end}"
    else:
        return f"Months {start}-{end}"


def _generate_phases(compliance_date, assurance_date, today, months_remaining, gaps):
    """Generate implementation phases with specific tasks.

    Phase durations and task urgency adapt dynamically based on months_remaining:
    - Comfortable (24+ mo): standard phased rollout
    - Adequate (18-24 mo): slightly compressed
    - Tight (12-18 mo): aggressive compression, overlapping phases
    - Critical (<12 mo): emergency parallel execution with accelerated tasks
    """
    phases = []

    # Determine urgency for task adjustments
    if months_remaining <= 6:
        urgency = "critical"
    elif months_remaining <= 12:
        urgency = "tight"
    elif months_remaining <= 24:
        urgency = "adequate"
    else:
        urgency = "comfortable"

    # Calculate dynamic phase schedule
    schedule = _calculate_phase_schedule(months_remaining)

    # Phase 1: Foundation & Management Buy-in
    p1_tasks = {
        "management": [
            "Present gap analysis results to executive management / board",
            "Secure budget allocation for SSBJ compliance project",
            "Appoint a Sustainability Disclosure Project Owner (executive sponsor)",
            "Establish cross-functional working group (Finance, Legal, IR, Operations, ESG)",
            "Include assurance engagement fees in budget planning (¥5M-¥30M+ depending on complexity)",
        ],
        "technical": [
            "Complete current gap assessment and baseline scoring",
            "Map existing data sources for GHG emissions (energy bills, fuel records, refrigerant logs)",
            "Inventory existing IT systems that hold sustainability data (ERP, utility management, etc.)",
        ],
        "assurance": [
            "BEGIN NOW: Research potential assurance providers (Big 4, mid-tier firms with ISSA 5000 / ISAE 3410 experience)",
            "Create shortlist of 3-5 providers — check their SSBJ/ISSB experience in Japan",
            "Understand limited assurance scope: Scope 1 & 2 GHG, Governance, and Risk Management (first 2 years)",
            "Review ISSA 5000 requirements at high level (replacing ISAE 3000/3410 from Dec 2026)",
            "Contact providers for informal introduction calls — don't wait until Phase 3",
        ],
    }

    if gaps["la_critical"]:
        p1_tasks["management"].append(
            f"URGENT: Highlight {len(gaps['la_critical'])} limited assurance critical gaps to management — these will be directly examined by auditors"
        )

    # Urgency-specific adjustments for Phase 1
    if urgency == "critical":
        p1_tasks["management"].insert(0,
            "ACCELERATED: Compress foundation activities into weeks, not months — run governance setup in parallel"
        )
        p1_tasks["assurance"].insert(0,
            "IMMEDIATE: Contact assurance providers THIS WEEK — you cannot afford delays"
        )
    elif urgency == "tight":
        p1_tasks["management"].insert(0,
            "COMPRESSED TIMELINE: Complete foundation within 1 month — delegate tasks across team members simultaneously"
        )

    phases.append({
        "number": 1,
        "title": "Foundation & Management Buy-in",
        "subtitle": "Gap analysis, governance setup, project launch",
        "duration": _phase_duration_label(schedule[0][0], schedule[0][1], months_remaining),
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
            "Schedule introductory meetings with shortlisted assurance firms",
            "Discuss assurance scope, timeline, and evidence expectations",
            "Ask about pre-assurance readiness review service (most firms offer this)",
            "Compare fees, team experience, and advisory support during preparation",
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

    # Urgency-specific adjustments for Phase 2
    if urgency == "critical":
        p2_tasks["management"].insert(0,
            "ACCELERATED: Use existing governance structures — add sustainability as standing board agenda item NOW, formalize later"
        )
        p2_tasks["assurance"].insert(0,
            "FAST-TRACK: Skip RFP — approach your current financial auditor or Big 4 firm directly for fastest engagement"
        )
    elif urgency == "tight":
        p2_tasks["assurance"].insert(0,
            "PRIORITY: Send RFP within 2 weeks — provider selection cannot wait"
        )

    phases.append({
        "number": 2,
        "title": "Governance & Policy Framework",
        "subtitle": "Policies, roles, assurance provider selection",
        "duration": _phase_duration_label(schedule[1][0], schedule[1][1], months_remaining),
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
            "IMPORTANT: Select and formally engage assurance provider by month 6-9",
            "Sign engagement letter for pre-assurance readiness review",
            "Pre-engagement planning meeting: agree scope, materiality, evidence requirements",
            "Assurance provider reviews your internal controls design (advisory, not assurance)",
            "Receive feedback on control gaps — adjust processes before dry run",
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

    # Urgency-specific adjustments for Phase 3
    if urgency == "critical":
        p3_tasks["management"].insert(0,
            "ACCELERATED: Focus ONLY on LA-scope items (Scope 1 & 2 GHG, Governance, Risk Management). Defer non-LA disclosures to Year 2"
        )
        p3_tasks["technical"].insert(0,
            "FAST-TRACK: Use spreadsheet-based approach with controls — do NOT start a multi-month IT project"
        )
    elif urgency == "tight":
        p3_tasks["management"].insert(0,
            "COMPRESSED: Prioritize LA-scope items first, then address remaining gaps"
        )

    phases.append({
        "number": 3,
        "title": "Process & System Implementation",
        "subtitle": "IT systems, data collection, internal controls",
        "duration": _phase_duration_label(schedule[2][0], schedule[2][1], months_remaining),
        "icon": "bi-gear",
        "color": "warning",
        "tasks": p3_tasks,
    })

    # Phase 4: Dry Run & Internal Review (Months 12-18)
    p4_tasks = {
        "management": [
            "Management sign-off on draft sustainability disclosure",
            "Board reviews draft disclosure before publication",
            "Assess completeness: all 25 SSBJ criteria covered?",
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
            "Assurance provider conducts readiness assessment (gap-check against ISSA 5000)",
            "Address any findings from readiness assessment",
            "Rehearse management inquiry sessions (auditor will interview key staff)",
        ],
    }

    # Urgency-specific adjustments for Phase 4
    if urgency == "critical":
        p4_tasks["management"].insert(0,
            "ACCELERATED: Combine dry run with actual disclosure preparation — no time for separate cycles"
        )
        p4_tasks["assurance"].insert(0,
            "FAST-TRACK: Provider should be doing readiness review NOW, concurrent with your data preparation"
        )
    elif urgency == "tight":
        p4_tasks["technical"].insert(0,
            "COMPRESSED: Run dry run on partial data if full year not yet available — don't wait for year-end"
        )

    phases.append({
        "number": 4,
        "title": "Dry Run & Internal Review",
        "subtitle": "Trial disclosure, assurance readiness check",
        "duration": _phase_duration_label(schedule[3][0], schedule[3][1], months_remaining),
        "icon": "bi-clipboard-check",
        "color": "success",
        "tasks": p4_tasks,
    })

    # Phase 5: Pre-Assurance Readiness (Months 15-21)
    p5_tasks = {
        "management": [
            "Schedule formal pre-assurance readiness review with your assurance provider",
            "Ensure management understands the assurance process and their role in it",
            "Identify key personnel who will interface with auditors (data owners, reviewers, approvers)",
            "Prepare internal FAQ: what auditors will ask, what evidence they need, common pitfalls",
        ],
        "technical": [
            "Complete mock audit: walk through the full evidence trail as if you are the auditor",
            "Verify all Scope 1 source data is traceable: fuel invoice → activity data → emission factor → tCO2e",
            "Verify all Scope 2 source data is traceable: utility bill → kWh → grid factor → tCO2e",
            "Test internal controls: does maker-checker work? Are reviews documented with dates and signatures?",
            "Prepare organized evidence binders/folders for each in-scope criterion",
            "Run completeness check: all sites, all emission sources, all months accounted for?",
            "GOVERNANCE READINESS: Verify board/committee minutes show sustainability agenda items, terms of reference include sustainability mandate",
            "RISK MANAGEMENT READINESS: Verify risk register is documented, risk assessment methodology is written, ERM integration is evidenced",
        ],
        "assurance": [
            "Assurance provider conducts pre-assurance readiness review (formal or advisory)",
            "Walk-through of data collection, calculation, and reporting processes",
            "Provider identifies control gaps, missing documentation, or methodology issues",
            "Receive written readiness assessment report with specific remediation items",
            "Remediate ALL findings before first disclosure — this is your last chance to fix issues",
            "Confirm engagement terms: timing, team, fees, deliverables for formal assurance",
        ],
    }

    if gaps["la_critical"]:
        p5_tasks["technical"].append(
            f"CRITICAL: Re-assess {len(gaps['la_critical'])} LA-critical items — all must be at score 3+ before assurance"
        )

    # Urgency-specific adjustments for Phase 5
    if urgency == "critical":
        p5_tasks["management"].insert(0,
            "ACCELERATED: Merge pre-assurance with dry run — run both simultaneously with provider support"
        )
        p5_tasks["assurance"].insert(0,
            "FAST-TRACK: Provider readiness review and formal engagement planning happen in parallel"
        )
    elif urgency == "tight":
        p5_tasks["assurance"].insert(0,
            "COMPRESSED: Schedule mock audit immediately after dry run with no gap between phases"
        )

    phases.append({
        "number": 5,
        "title": "Pre-Assurance Readiness",
        "subtitle": "Mock audit, provider readiness review, remediation",
        "duration": _phase_duration_label(schedule[4][0], schedule[4][1], months_remaining),
        "icon": "bi-search",
        "color": "purple",
        "tasks": p5_tasks,
    })

    # Phase 6: First Disclosure (Months 18-24 / Compliance Year)
    p6_tasks = {
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
            "Share final disclosure draft with assurance provider for awareness",
            "Ensure evidence packages are organized and ready for formal engagement",
            "Prepare management representation letter",
            "Confirm assurance engagement start date (typically 1-3 months after disclosure filing)",
        ],
    }

    # Urgency-specific adjustments for Phase 6
    if urgency == "critical":
        p6_tasks["technical"].insert(0,
            "ACCELERATED: Focus on minimum viable disclosure — ensure LA-scope items are complete, address others in amendments"
        )
    elif urgency == "tight":
        p6_tasks["technical"].insert(0,
            "PRIORITY: Finalize LA-scope disclosures first, then complete remaining sections"
        )

    phases.append({
        "number": 6,
        "title": "First Mandatory Disclosure",
        "subtitle": f"Publish SSBJ-compliant disclosure (FY{compliance_date.year})",
        "duration": _phase_duration_label(schedule[5][0], schedule[5][1], months_remaining)
            if urgency in ("critical", "tight") else f"Compliance Year ({compliance_date.year})",
        "icon": "bi-file-earmark-text",
        "color": "danger",
        "tasks": p6_tasks,
    })

    # Phase 7: First Limited Assurance (Year + 1)
    p7_tasks = {
        "management": [
            "Board informed of assurance engagement kickoff and expected timeline",
            "Designate internal liaison team for day-to-day auditor interactions",
            "Prepare for management inquiry sessions (auditor interviews with CFO, data owners, reviewers)",
        ],
        "technical": [
            "Provide complete evidence packages to assurance provider on day one",
            "GHG evidence: source data, calculations, methodology docs, reconciliations, review sign-offs",
            "Governance evidence: board/committee minutes, terms of reference, management role documentation",
            "Risk Management evidence: risk register, assessment methodology, ERM integration documentation",
            "Respond to information requests promptly (target 2-3 business days turnaround)",
            "Support site visits if required by assurance provider",
            "Address any findings or adjustments identified during fieldwork",
            "Track and resolve all auditor queries in a formal tracker",
        ],
        "assurance": [
            "Formal limited assurance engagement begins (ISSA 5000 / JICPA Practice Guideline 5000)",
            "Assurance procedures: inquiry, analytical review, recalculation, limited testing of controls",
            "Scope: Scope 1 & 2 GHG emissions, Governance disclosures, and Risk Management disclosures",
            "GHG procedures: recalculation of emissions, source data testing, emission factor verification",
            "Governance procedures: inquiry on oversight processes, inspection of minutes and charters",
            "Risk Management procedures: inquiry on risk processes, inspection of risk register and methodology",
            "Draft assurance report reviewed by management before finalization",
            "Receive assurance report — target: unqualified (clean) conclusion",
            "Note: IAASB expects modified conclusions may be common in early years — prepare for potential qualifications",
            "Debrief with provider: lessons learned, improvement areas for Year 2",
            "Plan for scope expansion from Year 3 (Strategy, Metrics, Scope 3 — per FSA roadmap)",
        ],
    }

    phases.append({
        "number": 7,
        "title": "First Limited Assurance",
        "subtitle": f"Auditor examines Scope 1 & 2, Governance, Risk Mgmt (FY{assurance_date.year})",
        "duration": f"Assurance Year ({assurance_date.year})",
        "icon": "bi-shield-check",
        "color": "dark",
        "tasks": p7_tasks,
    })

    return phases


def _generate_pre_assurance_guide(gaps, months_remaining, months_to_assurance, compliance_date):
    """Generate pre-assurance engagement guidance based on assessment results."""

    # When to start talking to assurance providers
    if months_remaining > 18:
        engagement_urgency = "recommended"
        engagement_message = (
            "You have adequate time. Start informal conversations with assurance providers now "
            "to understand expectations. Formal engagement by month 6-9 is ideal."
        )
    elif months_remaining > 12:
        engagement_urgency = "important"
        engagement_message = (
            "Timeline is getting tight. Begin assurance provider discussions immediately. "
            "Aim to select a provider within 2-3 months and commission a pre-assurance readiness review."
        )
    else:
        engagement_urgency = "critical"
        engagement_message = (
            "URGENT: You should already be talking to assurance providers. Contact firms immediately "
            "and fast-track a pre-assurance readiness review. Consider engaging your financial auditor "
            "who already knows your organization."
        )

    # Pre-assurance readiness checklist based on gaps
    checklist = []

    # Check LA-critical items
    if gaps["la_critical"]:
        checklist.append({
            "item": f"Close {len(gaps['la_critical'])} limited assurance critical gaps (currently below score 3)",
            "status": "not_ready",
            "priority": "critical",
            "detail": "Auditors will directly examine these items. All must reach score 3 (Defined) minimum.",
        })
    else:
        checklist.append({
            "item": "All LA-scope items meet minimum threshold",
            "status": "ready",
            "priority": "done",
            "detail": "In-scope items are at or above score 3.",
        })

    # Internal controls check
    has_controls_gap = any(
        g["id"] == "RSK-05" for g in gaps.get("risk", [])
    )
    if has_controls_gap:
        checklist.append({
            "item": "Establish internal controls for GHG data (RSK-05 below threshold)",
            "status": "not_ready",
            "priority": "critical",
            "detail": "Auditors REQUIRE documented internal controls: data ownership, maker-checker review, audit trail, reconciliation.",
        })
    else:
        checklist.append({
            "item": "Internal controls framework in place",
            "status": "ready",
            "priority": "done",
            "detail": "Controls are documented. Ensure they are operating effectively.",
        })

    # Data quality check
    has_dq_gap = any(
        g["id"] == "MET-07" for g in gaps.get("metrics", [])
    )
    if has_dq_gap:
        checklist.append({
            "item": "Implement data quality management (MET-07 below threshold)",
            "status": "not_ready",
            "priority": "critical",
            "detail": "Auditors need to see: data flow diagram, validation rules, error log, completeness checks.",
        })
    else:
        checklist.append({
            "item": "Data quality processes documented",
            "status": "ready",
            "priority": "done",
            "detail": "Data governance is in place. Maintain evidence of ongoing quality checks.",
        })

    # Scope 1 & 2 completeness
    has_s1_gap = any(g["id"] == "MET-01" for g in gaps.get("metrics", []))
    has_s2_gap = any(g["id"] == "MET-02" for g in gaps.get("metrics", []))
    if has_s1_gap or has_s2_gap:
        missing = []
        if has_s1_gap:
            missing.append("Scope 1")
        if has_s2_gap:
            missing.append("Scope 2")
        checklist.append({
            "item": f"Complete {' & '.join(missing)} GHG calculation process",
            "status": "not_ready",
            "priority": "critical",
            "detail": "These are the CORE items for limited assurance. Need documented methodology, verified data, and reviewed calculations.",
        })
    else:
        checklist.append({
            "item": "Scope 1 & 2 GHG calculation processes established",
            "status": "ready",
            "priority": "done",
            "detail": "Calculation processes are in place. Ensure audit trail is complete.",
        })

    # Governance readiness (IN SCOPE for initial LA per FSA July 2025 roadmap)
    has_gov_gap = any(g["id"].startswith("GOV-") for g in gaps.get("la_critical", []))
    if has_gov_gap:
        checklist.append({
            "item": "Governance documentation gaps — IN ASSURANCE SCOPE",
            "status": "not_ready",
            "priority": "critical",
            "detail": "Auditors will inquire about governance processes. Need: board/committee mandate, meeting minutes with sustainability agenda, management role documentation.",
        })
    else:
        checklist.append({
            "item": "Governance oversight documented",
            "status": "ready",
            "priority": "done",
            "detail": "Governance processes documented. Ensure board minutes and terms of reference are filed as evidence.",
        })

    # Risk management readiness (IN SCOPE for initial LA per FSA July 2025 roadmap)
    has_rsk_gap = any(g["id"].startswith("RSK-") for g in gaps.get("la_critical", []))
    if has_rsk_gap:
        checklist.append({
            "item": "Risk management documentation gaps — IN ASSURANCE SCOPE",
            "status": "not_ready",
            "priority": "critical",
            "detail": "Auditors will inquire about risk processes. Need: documented risk identification methodology, risk register, ERM integration evidence.",
        })
    else:
        checklist.append({
            "item": "Risk management processes documented",
            "status": "ready",
            "priority": "done",
            "detail": "Risk management processes documented. Ensure risk register and methodology are filed as evidence.",
        })

    # General readiness items
    checklist.extend([
        {
            "item": "Evidence filing system organized for auditor access",
            "status": "pending",
            "priority": "important",
            "detail": "Organize evidence by criterion, year, and source. Auditor should be able to trace any number back to source.",
        },
        {
            "item": "Management representation letter template prepared",
            "status": "pending",
            "priority": "important",
            "detail": "Management must formally represent completeness and accuracy of GHG data, governance processes, and risk management. Prepare template in advance.",
        },
        {
            "item": "Key personnel identified and briefed for auditor inquiries",
            "status": "pending",
            "priority": "important",
            "detail": "Auditors will interview data owners, reviewers, governance body members, and risk owners. Prepare them for typical questions.",
        },
    ])

    # Assurance provider selection criteria
    provider_criteria = [
        {"criterion": "ISSA 5000 certification (or ISAE 3000/3410 experience)", "why": "ISSA 5000 is the new mandatory standard for sustainability assurance (effective Dec 2026)"},
        {"criterion": "Experience with Japanese SSBJ standards", "why": "SSBJ has Japan-specific requirements that differ from global ISSB"},
        {"criterion": "Industry experience in your sector", "why": "Sector-specific emission sources and calculation methods matter"},
        {"criterion": "Pre-assurance advisory service available", "why": "Best practice: provider reviews your readiness BEFORE formal engagement"},
        {"criterion": "Team continuity year-over-year", "why": "Consistent team reduces ramp-up time and builds institutional knowledge"},
        {"criterion": "Relationship with your financial auditor", "why": "If same firm or cooperative firms, evidence sharing is easier"},
    ]

    # Typical engagement timeline
    timeline = [
        {"when": "12-18 months before assurance", "what": "Informal provider conversations, understand requirements"},
        {"when": "9-12 months before assurance", "what": "Send RFP, receive proposals, select provider"},
        {"when": "6-9 months before assurance", "what": "Sign engagement letter, pre-assurance readiness review"},
        {"when": "3-6 months before assurance", "what": "Remediate findings from readiness review, prepare evidence"},
        {"when": "1-3 months before assurance", "what": "Final preparation, mock audit, confirm engagement logistics"},
        {"when": "Assurance period (4-8 weeks)", "what": "Fieldwork: inquiry, testing, recalculation, site visits if needed"},
        {"when": "After fieldwork", "what": "Draft report review, management response, final assurance report issued"},
    ]

    return {
        "engagement_urgency": engagement_urgency,
        "engagement_message": engagement_message,
        "checklist": checklist,
        "provider_criteria": provider_criteria,
        "timeline": timeline,
        "months_to_assurance": months_to_assurance,
    }


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
            f"Phases have been compressed with parallel execution. "
            f"Focus exclusively on LA-scope items. Consider external consultants to supplement internal resources."
        )
    elif urgency == "tight":
        lines.append(
            f"Timeline is tight ({months_remaining} months). Phases have been compressed and some overlap. "
            f"Prioritize limited assurance scope items and begin assurance provider discussions immediately."
        )
    elif urgency == "adequate":
        lines.append(
            f"You have {months_remaining} months — adequate time if you start promptly. "
            f"Phases are slightly compressed. Stay on schedule to avoid last-minute pressure."
        )
    else:
        lines.append(
            f"Comfortable timeline ({months_remaining} months). Standard phased approach with full time allocations. "
            f"Use the extra time for thorough preparation and testing."
        )

    return lines
