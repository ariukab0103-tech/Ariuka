"""
Executive Summary Generator for Board / Management

Produces a concise, board-ready summary:
- Compliance status at a glance
- Timeline and urgency
- Minimum requirements (what you MUST do)
- Investment Option A: minimal compliance (manual, paper-based)
- Investment Option B: systematic approach (reduce manual work long-term)
- Key risks of non-compliance
"""

from datetime import date
from app.ssbj_criteria import SSBJ_CRITERIA


def generate_executive_summary(assessment, responses_dict, pillar_scores, roadmap_data):
    """
    Generate executive summary data for board/management presentation.

    Args:
        assessment: Assessment model instance
        responses_dict: dict of {criterion_id: Response}
        pillar_scores: dict from assessment.pillar_scores()
        roadmap_data: dict from generate_roadmap() (or None)

    Returns dict with all summary sections.
    """
    criteria_map = {c["id"]: c for c in SSBJ_CRITERIA}

    # ---- Scores & Gaps ----
    scored_responses = [r for r in responses_dict.values() if r.score is not None]
    total_scored = len(scored_responses)
    overall = round(sum(r.score for r in scored_responses) / total_scored, 1) if scored_responses else 0

    gaps = []
    la_gaps = []
    for r in scored_responses:
        c = criteria_map.get(r.criterion_id)
        if not c:
            continue
        if r.score < 3:
            gap_info = {
                "id": r.criterion_id,
                "category": c["category"],
                "score": r.score,
                "pillar": c["pillar"],
                "la_scope": c["la_scope"],
                "minimum_action": c.get("minimum_action", ""),
            }
            gaps.append(gap_info)
            if c["la_scope"] == "in_scope":
                la_gaps.append(gap_info)

    # ---- Timeline (defensive: works even if roadmap_data is None) ----
    if roadmap_data:
        months_remaining = roadmap_data["months_remaining"]
        months_to_assurance = roadmap_data.get("months_to_assurance", months_remaining + 12)
        urgency = roadmap_data.get("disclosure_urgency", roadmap_data["urgency"])
        assurance_urgency = roadmap_data.get("assurance_urgency", urgency)
        compliance_year = roadmap_data["compliance_year"]
    else:
        # Fallback: compute independently from assessment
        from app.roadmap import _extract_year, _urgency_level
        import calendar
        fy_end_month = getattr(assessment, "fy_end_month", 3) or 3
        comp_year = _extract_year(assessment.fiscal_year)
        if not comp_year:
            comp_year = date.today().year + 2
        if fy_end_month != 3:
            adj_year = comp_year if fy_end_month < 3 else comp_year - 1
        else:
            adj_year = comp_year
        fy_end_day = calendar.monthrange(adj_year, fy_end_month)[1]
        comp_date = date(adj_year, fy_end_month, fy_end_day)
        months_remaining = (comp_date.year - date.today().year) * 12 + (comp_date.month - date.today().month)
        months_to_assurance = months_remaining + 12
        compliance_year = comp_year
        urgency = _urgency_level(months_remaining)
        assurance_urgency = _urgency_level(months_to_assurance)

    # ---- Standard classification (SSBJ No.1 General vs No.2 Climate) ----
    s1_gaps = [g for g in gaps if criteria_map.get(g["id"], {}).get("standard") == "General (S1)"]
    s2_gaps = [g for g in gaps if criteria_map.get(g["id"], {}).get("standard") == "Climate (S2)"]
    s1_total = len([c for c in SSBJ_CRITERIA if c.get("standard") == "General (S1)"])
    s2_total = len([c for c in SSBJ_CRITERIA if c.get("standard") == "Climate (S2)"])

    # ---- Compliance readiness verdict ----
    if not gaps:
        verdict = "on_track"
        verdict_label = "On Track"
        verdict_detail = "All criteria meet the minimum maturity level (score 3+). Focus on maintaining and evidencing current practices for assurance."
    elif not la_gaps and len(gaps) <= 5:
        verdict = "minor_gaps"
        verdict_label = "Minor Gaps"
        verdict_detail = f"{len(gaps)} criteria below threshold, but none in limited assurance scope. Address gaps before disclosure but assurance readiness is not at risk."
    elif len(la_gaps) <= 3:
        verdict = "action_needed"
        verdict_label = "Action Needed"
        verdict_detail = f"{len(la_gaps)} criteria in limited assurance scope are below threshold. These will be directly examined by auditors and must be fixed as top priority."
    else:
        verdict = "significant_work"
        verdict_label = "Significant Work Required"
        verdict_detail = f"{len(la_gaps)} limited assurance criteria and {len(gaps)} total criteria are below threshold. A dedicated project team and budget allocation are essential."

    # ---- Minimum requirements (what MUST be done regardless of investment) ----
    minimum_requirements = []

    # Governance
    gov_gaps = [g for g in gaps if g["pillar"] == "Governance"]
    if gov_gaps:
        actions = []
        for g in gov_gaps:
            action = g.get("minimum_action", "")
            if action:
                actions.append(f"{g['id']} (score {g['score']}): {action}")
            else:
                actions.append(f"{g['id']} (score {g['score']})")
        minimum_requirements.append({
            "area": "Governance",
            "icon": "bi-building",
            "what": "Board/committee must formally oversee sustainability disclosure",
            "why": "SSBJ requires disclosed governance processes. Auditors will verify board oversight via minutes and mandates.",
            "gaps": actions,
        })

    # Risk Management
    rsk_gaps = [g for g in gaps if g["pillar"] == "Risk Management"]
    if rsk_gaps:
        actions = []
        for g in rsk_gaps:
            action = g.get("minimum_action", "")
            if action:
                actions.append(f"{g['id']} (score {g['score']}): {action}")
            else:
                actions.append(f"{g['id']} (score {g['score']})")
        minimum_requirements.append({
            "area": "Risk Management",
            "icon": "bi-exclamation-triangle",
            "what": "Document climate risk identification, assessment methodology, and ERM integration",
            "why": "Risk management is in initial limited assurance scope. Auditors will examine your risk processes from Year 1.",
            "gaps": actions,
        })

    # GHG Emissions (Scope 1 & 2)
    met_s1 = next((g for g in gaps if g["id"] == "MET-01"), None)
    met_s2 = next((g for g in gaps if g["id"] == "MET-02"), None)
    if met_s1 or met_s2:
        actions = []
        if met_s1:
            action = met_s1.get("minimum_action", "")
            actions.append(f"Scope 1 (score {met_s1['score']}): {action}" if action else f"Scope 1 (score {met_s1['score']})")
        if met_s2:
            action = met_s2.get("minimum_action", "")
            actions.append(f"Scope 2 (score {met_s2['score']}): {action}" if action else f"Scope 2 (score {met_s2['score']})")
        minimum_requirements.append({
            "area": "GHG Emissions (Scope 1 & 2)",
            "icon": "bi-cloud",
            "what": "Establish complete, auditable GHG calculation",
            "why": "Core limited assurance item. Auditors will recalculate your emissions, test source data, and verify methodology.",
            "gaps": actions,
        })

    # Scope 3 (mandatory but Year 1 relief available)
    met_s3 = next((g for g in gaps if g["id"] == "MET-03"), None)
    if met_s3:
        action = met_s3.get("minimum_action", "")
        minimum_requirements.append({
            "area": "Scope 3 Emissions",
            "icon": "bi-diagram-3",
            "what": "Disclose all 15 Scope 3 categories (Year 1 relief: can use estimates/proxies)",
            "why": "Mandatory under IFRS S2 para 29(a)(vi). Year 1 transition relief allows simplified data, but disclosure is still required.",
            "gaps": [f"MET-03 (score {met_s3['score']}): {action}" if action else f"MET-03 (score {met_s3['score']})"],
        })

    # Strategy gaps
    str_gaps = [g for g in gaps if g["pillar"] == "Strategy"]
    if str_gaps:
        actions = []
        for g in str_gaps:
            action = g.get("minimum_action", "")
            if action:
                actions.append(f"{g['id']} (score {g['score']}): {action}")
            else:
                actions.append(f"{g['id']} (score {g['score']})")
        minimum_requirements.append({
            "area": "Strategy & Value Chain",
            "icon": "bi-signpost-split",
            "what": "Disclose climate-related risks/opportunities, scenario analysis, and value chain impacts",
            "why": "Value chain analysis is mandatory (entire chain, not just direct operations). Scenario analysis required under SSBJ.",
            "gaps": actions,
        })

    # Other metrics gaps
    other_met = [g for g in gaps if g["pillar"] == "Metrics & Targets" and g["id"] not in ("MET-01", "MET-02", "MET-03")]
    if other_met:
        actions = []
        for g in other_met:
            action = g.get("minimum_action", "")
            if action:
                actions.append(f"{g['id']} (score {g['score']}): {action}")
            else:
                actions.append(f"{g['id']} (score {g['score']})")
        minimum_requirements.append({
            "area": "Other Metrics & Targets",
            "icon": "bi-graph-up",
            "what": f"Address {len(other_met)} remaining metrics gaps (intensity, targets, remuneration, etc.)",
            "why": "All SSBJ metrics are mandatory disclosures. GHG intensity (MET-08) and climate remuneration (MET-09) required under IFRS S2.",
            "gaps": actions,
        })

    # Internal controls (always required for assurance)
    met_dq = next((g for g in gaps if g["id"] == "MET-07"), None)
    if met_dq:
        action = met_dq.get("minimum_action", "")
        minimum_requirements.append({
            "area": "Data Quality & Internal Controls",
            "icon": "bi-shield-lock",
            "what": action if action else "Implement maker-checker review, audit trail, data validation for GHG data",
            "why": "Without internal controls, auditors cannot issue an unqualified opinion. This is foundational for assurance.",
            "gaps": [f"MET-07 (score {met_dq['score']})"],
        })

    # ---- Investment estimates ----
    # Option A: Minimal compliance (spreadsheet-based, manual)
    # Option B: Systematic (GHG software, training, advisory)
    # Estimates based on typical Japanese listed company costs

    staff_gap_count = len(gaps)
    has_it_need = any(g["id"] in ("MET-01", "MET-02", "MET-03", "MET-07") and g["score"] < 2 for g in gaps)

    option_a = {
        "name": "Minimum Viable Compliance",
        "subtitle": "Manual processes, spreadsheet-based, minimal external support",
        "approach": [
            "Spreadsheet-based GHG calculations with documented review process",
            "Manual data collection from sites/subsidiaries via templates",
            "Internal staff allocated part-time to sustainability disclosure",
            "Minimal external advisory for methodology validation",
            "Paper-based evidence filing organized by criterion",
        ],
        "investment_items": [],
        "total_range": "",
        "pros": [
            "Lower upfront cost",
            "Can start immediately with existing resources",
            "Suitable if organization has few emission sources / simple operations",
        ],
        "cons": [
            "High ongoing manual effort each reporting cycle",
            "Higher risk of data errors (no automated validation)",
            "Difficult to scale for Scope 3 (15 categories) in Year 2+",
            "Auditor may flag control weaknesses",
            "Key person risk if dedicated staff leave",
        ],
        "best_for": "Smaller organizations, simple operations, or those very close to deadline with no time for system implementation",
    }

    option_b = {
        "name": "Systematic Compliance",
        "subtitle": "GHG software, structured processes, advisory support, long-term efficiency",
        "approach": [
            "Dedicated GHG calculation platform (e.g., Zeroboard, Persefoni, booost, or equivalent)",
            "Automated data collection integrations where possible",
            "External advisory support for methodology and gap remediation",
            "Pre-assurance readiness review by assurance provider",
            "Structured training program for data owners and reviewers",
            "Digital evidence management with audit trail",
        ],
        "investment_items": [],
        "total_range": "",
        "pros": [
            "Significantly reduced manual effort from Year 2 onward",
            "Built-in data validation and audit trail (auditor-friendly)",
            "Scales easily for Scope 3 expansion and assurance scope widening",
            "Lower risk of errors and qualifications",
            "Institutional knowledge embedded in systems, not people",
        ],
        "cons": [
            "Higher upfront investment",
            "Implementation time (3-6 months for platform setup)",
            "Ongoing license fees",
            "Change management required across departments",
        ],
        "best_for": "Organizations with complex operations, multiple sites, or those planning for long-term compliance beyond Year 1",
    }

    # Estimate ranges based on gap severity
    if staff_gap_count <= 5 and not has_it_need:
        # Minor gaps
        option_a["investment_items"] = [
            {"item": "Staff time allocation (part-time, 2-3 people)", "range": "Internal cost"},
            {"item": "External advisory (methodology review)", "range": "¥3M - ¥5M"},
            {"item": "Assurance engagement (limited)", "range": "¥5M - ¥10M"},
        ]
        option_a["total_range"] = "¥8M - ¥15M + internal staff time"
        option_b["investment_items"] = [
            {"item": "GHG platform license (annual)", "range": "¥3M - ¥8M"},
            {"item": "Platform setup & data integration", "range": "¥2M - ¥5M"},
            {"item": "External advisory & training", "range": "¥5M - ¥8M"},
            {"item": "Pre-assurance readiness review", "range": "¥2M - ¥5M"},
            {"item": "Assurance engagement (limited)", "range": "¥5M - ¥10M"},
        ]
        option_b["total_range"] = "¥17M - ¥36M (Year 1), reducing to ¥8M - ¥18M/year ongoing"
    elif staff_gap_count <= 12:
        # Moderate gaps
        option_a["investment_items"] = [
            {"item": "Staff time allocation (part-time, 3-5 people)", "range": "Internal cost"},
            {"item": "External advisory (gap remediation + methodology)", "range": "¥5M - ¥10M"},
            {"item": "Governance/policy documentation support", "range": "¥2M - ¥5M"},
            {"item": "Assurance engagement (limited)", "range": "¥8M - ¥15M"},
        ]
        option_a["total_range"] = "¥15M - ¥30M + internal staff time"
        option_b["investment_items"] = [
            {"item": "GHG platform license (annual)", "range": "¥5M - ¥12M"},
            {"item": "Platform setup, integration & customization", "range": "¥5M - ¥10M"},
            {"item": "External advisory (comprehensive gap remediation)", "range": "¥8M - ¥15M"},
            {"item": "Staff training program", "range": "¥2M - ¥4M"},
            {"item": "Pre-assurance readiness review", "range": "¥3M - ¥5M"},
            {"item": "Assurance engagement (limited)", "range": "¥8M - ¥15M"},
        ]
        option_b["total_range"] = "¥31M - ¥61M (Year 1), reducing to ¥13M - ¥27M/year ongoing"
    else:
        # Significant gaps
        option_a["investment_items"] = [
            {"item": "Dedicated project manager (FTE or contractor)", "range": "¥8M - ¥15M"},
            {"item": "Staff time allocation (part-time, 5-8 people)", "range": "Internal cost"},
            {"item": "External advisory (comprehensive program)", "range": "¥10M - ¥20M"},
            {"item": "Governance & risk management overhaul support", "range": "¥5M - ¥10M"},
            {"item": "Assurance engagement (limited)", "range": "¥10M - ¥20M"},
        ]
        option_a["total_range"] = "¥33M - ¥65M + significant internal staff time"
        option_b["investment_items"] = [
            {"item": "GHG platform license (annual, enterprise)", "range": "¥8M - ¥20M"},
            {"item": "Platform setup, full integration & customization", "range": "¥10M - ¥20M"},
            {"item": "Dedicated project manager", "range": "¥8M - ¥15M"},
            {"item": "External advisory (full program support)", "range": "¥15M - ¥25M"},
            {"item": "Staff training & change management", "range": "¥3M - ¥6M"},
            {"item": "Pre-assurance readiness review", "range": "¥5M - ¥8M"},
            {"item": "Assurance engagement (limited)", "range": "¥10M - ¥20M"},
        ]
        option_b["total_range"] = "¥59M - ¥114M (Year 1), reducing to ¥18M - ¥40M/year ongoing"

    # ---- Risks of non-compliance / delayed action ----
    risks = [
        {
            "risk": "Qualified assurance opinion",
            "impact": "Investor and market confidence impact; signals to investors that disclosure controls are weak",
            "likelihood": "High" if len(la_gaps) > 3 else ("Medium" if la_gaps else "Low"),
        },
        {
            "risk": "Regulatory action by FSA/exchange",
            "impact": "Potential designation review, public disclosure of non-compliance, reputational damage",
            "likelihood": "Medium" if months_remaining and months_remaining < 12 else "Low",
        },
        {
            "risk": "Investor downgrade on ESG ratings",
            "impact": "May affect cost of capital, index inclusion (FTSE, MSCI), and institutional investor engagement",
            "likelihood": "High" if len(gaps) > 10 else "Medium",
        },
        {
            "risk": "Inability to secure assurance provider",
            "impact": "Limited pool of qualified providers; late entrants may face capacity constraints or premium fees",
            "likelihood": "High" if months_remaining and months_remaining < 12 else "Medium",
        },
        {
            "risk": "Scope 3 data gaps compound in Year 2",
            "impact": "Year 1 relief expires; without foundational data collection in Year 1, Year 2 full disclosure becomes very difficult",
            "likelihood": "High" if met_s3 else "Low",
        },
    ]

    # ---- Cross-criterion dependency risks ----
    gap_ids = {g["id"] for g in gaps}
    if "RSK-05" in gap_ids and ("MET-01" in gap_ids or "MET-02" in gap_ids):
        risks.append({
            "risk": "Internal controls gap undermines GHG data reliability",
            "impact": "RSK-05 (internal controls) is weak — auditors will question the reliability of Scope 1 & 2 data even if calculations are correct",
            "likelihood": "High",
        })
    if "MET-07" in gap_ids:
        risks.append({
            "risk": "Data quality gap blocks clean assurance on all metrics",
            "impact": "MET-07 (data quality) is foundational — without it, auditors will likely qualify their opinion on all GHG metrics",
            "likelihood": "High" if any(g["id"] in ("MET-01", "MET-02") and g["score"] < 2 for g in gaps) else "Medium",
        })

    # ---- Key decisions for the board ----
    key_decisions = []

    if verdict in ("action_needed", "significant_work"):
        key_decisions.append({
            "decision": "Approve dedicated budget and project team for SSBJ compliance",
            "deadline": "Immediate",
            "owner": "Board / CFO",
        })

    key_decisions.append({
        "decision": "Select compliance approach: Option A (minimal) or Option B (systematic)",
        "deadline": "Within 1 month",
        "owner": "CFO / ESG Lead",
    })

    if months_remaining and months_remaining <= 18:
        key_decisions.append({
            "decision": "Initiate assurance provider engagement (RFP or direct approach)",
            "deadline": "Within 2 weeks" if months_remaining <= 12 else "Within 2 months",
            "owner": "CFO / Finance",
        })

    key_decisions.append({
        "decision": "Designate sustainability disclosure project owner (executive sponsor)",
        "deadline": "Within 1 month",
        "owner": "Board",
    })

    if gov_gaps:
        key_decisions.append({
            "decision": "Establish board sustainability oversight committee or add to existing committee mandate",
            "deadline": "Within 2 months",
            "owner": "Board Secretary",
        })

    return {
        "overall_score": overall,
        "total_scored": total_scored,
        "total_criteria": len(SSBJ_CRITERIA),
        "total_gaps": len(gaps),
        "la_gaps_count": len(la_gaps),
        "la_gaps": la_gaps,
        "pillar_scores": pillar_scores,
        "months_remaining": months_remaining,
        "months_to_assurance": months_to_assurance,
        "urgency": urgency,
        "assurance_urgency": assurance_urgency,
        "compliance_year": compliance_year,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "verdict_detail": verdict_detail,
        "minimum_requirements": minimum_requirements,
        "option_a": option_a,
        "option_b": option_b,
        "risks": risks,
        "key_decisions": key_decisions,
        # Standard breakdown (SSBJ No.1 vs No.2)
        "standard_breakdown": {
            "s1_total": s1_total,
            "s2_total": s2_total,
            "s1_gaps": len(s1_gaps),
            "s2_gaps": len(s2_gaps),
        },
    }
