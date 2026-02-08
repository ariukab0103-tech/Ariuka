"""
B3: Transitional Relief Advisor

Dynamically determines which SSBJ transitional reliefs apply to a specific
assessment based on:
- Fiscal year and reporting timeline
- Current maturity scores
- LA scope status (in_scope, supporting, not_in_initial_scope)
- SSBJ standard classification (No.1 General vs No.2 Climate)

Provides prioritized, actionable recommendations on what can be deferred,
simplified, or must be addressed immediately.

Key transition relief sources:
- IFRS S1 Appendix E (general transition provisions)
- SSBJ Application Standard No.3 (Japan-specific implementation)
- SSBJ Schedule of Differences vs ISSB (jurisdiction-specific alternatives)
"""

import re
from datetime import date

from app.ssbj_criteria import SSBJ_CRITERIA


# Extended relief details with conditions and recommendations
_RELIEF_DETAILS = {
    "STR-01": {
        "relief": "Proportionality relief: value chain risk/opportunity assessment can use qualitative analysis in first year.",
        "what_you_can_defer": "Full quantitative value chain risk analysis",
        "what_you_must_do": "Qualitative assessment covering upstream, own operations, and downstream",
        "year2_requirement": "Move to semi-quantitative or quantitative value chain analysis",
    },
    "STR-02": {
        "relief": "Entity need not assess entire value chain in first year if data is not available without undue cost or effort.",
        "what_you_can_defer": "Complete upstream/downstream data collection from all value chain partners",
        "what_you_must_do": "Map your value chain and assess data availability. Document which parts you could not assess and why.",
        "year2_requirement": "Progressively expand value chain coverage with supplier engagement",
    },
    "STR-04": {
        "relief": "Qualitative scenario analysis is acceptable in first year.",
        "what_you_can_defer": "Quantitative scenario modeling and financial impact calculations",
        "what_you_must_do": "Select at least two climate scenarios (e.g., IEA NZE, IPCC RCP 8.5) and write qualitative narrative",
        "year2_requirement": "Begin quantifying financial impacts under each scenario",
    },
    "STR-05": {
        "relief": "First-year transition plan disclosure can be high-level directional commitments.",
        "what_you_can_defer": "Detailed milestones, CAPEX allocation, specific technology pathways",
        "what_you_must_do": "State directional commitment (e.g., 'working toward net-zero') or state plan is under development",
        "year2_requirement": "Develop concrete transition plan with targets and milestones",
    },
    "MET-01": {
        "relief": "First-year Scope 1 may use simplified calculation methodology. Note: 'simplified' means methodology sophistication, NOT reduced evidence quality.",
        "what_you_can_defer": "Full GHG Protocol alignment with facility-level granularity",
        "what_you_must_do": "Calculate total Scope 1 using available data. Document methodology, emission factors, and keep ALL source documents. The auditor WILL recalculate and verify data even with simplified methodology.",
        "year2_requirement": "Align fully with GHG Protocol Corporate Standard",
    },
    "MET-02": {
        "relief": "First-year Scope 2 location-based calculation is sufficient. If you purchase renewable energy, report both methods from Year 1 to avoid cherry-picking perception.",
        "what_you_can_defer": "Market-based Scope 2 calculation (only if no green energy contracts)",
        "what_you_must_do": "Calculate location-based Scope 2 using area-specific grid emission factors. Keep utility invoices for all facilities.",
        "year2_requirement": "Add market-based Scope 2 calculation alongside location-based",
    },
    "MET-03": {
        "relief": "Scope 3 CALCULATION may be deferred in first reporting year.",
        "what_you_can_defer": "Scope 3 emissions calculations and quantified disclosures",
        "what_you_must_do": "Assess all 15 categories for materiality, begin supplier engagement, document data collection plan. Year 2 auditors will ask what you did in Year 1 to prepare.",
        "year2_requirement": "Disclose all 15 Scope 3 categories with calculations (estimates acceptable)",
    },
    "MET-04": {
        "relief": "Comparative information for targets is NOT required in first reporting year.",
        "what_you_can_defer": "Year-over-year target progress comparison",
        "what_you_must_do": "Set and disclose climate targets with base year and target year",
        "year2_requirement": "Provide comparative data showing progress against targets",
    },
    "MET-05": {
        "relief": "Comparative information for progress tracking is NOT required in first reporting year.",
        "what_you_can_defer": "Historical trend data and year-over-year comparisons",
        "what_you_must_do": "Disclose current-year industry metrics if applicable",
        "year2_requirement": "Provide comparative information from Year 1 as baseline",
    },
    "MET-07": {
        "relief": "Detailed carbon credit methodology can be simplified in first year.",
        "what_you_can_defer": "Detailed credit retirement and vintage tracking methodology",
        "what_you_must_do": "Basic disclosure of data quality approach (validation rules, review process)",
        "year2_requirement": "Full data governance framework with documented lineage",
    },
    "MET-08": {
        "relief": "GHG intensity calculation can use simplified denominators in first year.",
        "what_you_can_defer": "Multiple intensity metrics and sector-specific denominators",
        "what_you_must_do": "Calculate at least one intensity metric (e.g., tCO2e per revenue)",
        "year2_requirement": "Consistent intensity metrics with year-over-year comparison",
    },
}

# Japan-specific alternatives
_JAPAN_ALTERNATIVES = {
    "GOV-01": {
        "alternative": "Leverage existing Japan CG Code Principle 2-3 compliance",
        "action": "Reference your existing corporate governance report. If ESG oversight is already documented there, cross-reference it in SSBJ disclosures.",
        "benefit": "Avoid duplicating governance documentation — reuse what you already file with TSE.",
    },
    "STR-03": {
        "alternative": "Two-stage disclosure (二段階開示): qualitative first, quantitative later",
        "action": "Disclose qualitative financial effects in Year 1. Quantify impacts progressively in subsequent years.",
        "benefit": "Reduces Year 1 burden significantly — no need for complex financial impact modeling immediately.",
    },
    "STR-04": {
        "alternative": "Qualitative scenario analysis accepted by SSBJ",
        "action": "Use narrative-based scenario analysis describing physical and transition risk impacts qualitatively.",
        "benefit": "No need for expensive quantitative climate modeling tools in Year 1.",
    },
    "MET-02": {
        "alternative": "Both location-based and market-based Scope 2 methods explicitly accepted",
        "action": "If you purchase renewable energy certificates (J-Credits, non-fossil certificates), report market-based alongside location-based.",
        "benefit": "Companies with green power purchases can show lower market-based emissions.",
    },
    "MET-03": {
        "alternative": "Proportionality relief for Scope 3 data quality",
        "action": "Use industry averages and spend-based estimates where primary supplier data is unavailable. State 'not material' for non-applicable categories.",
        "benefit": "Significantly reduces data collection burden — no need for perfect supplier-specific data in early years.",
    },
    "MET-04": {
        "alternative": "Two-stage disclosure for targets: qualitative then quantitative",
        "action": "Set qualitative directional targets in Year 1 (e.g., 'reduce emissions'). Quantify from Year 2.",
        "benefit": "Gives time to develop credible quantified targets (potentially SBTi-aligned).",
    },
    "STR-07": {
        "alternative": "Cross-reference securities report (有価証券報告書)",
        "action": "Create a mapping table between sustainability disclosures and specific line items in your annual securities report.",
        "benefit": "FSA encourages this approach — demonstrates connectivity without complex new analysis.",
    },
    "STR-05": {
        "alternative": "Transition plan: qualitative directional statement accepted",
        "action": "State directional commitment (e.g., 'pursuing carbon neutrality') with high-level timeline. Detailed plan can follow in Year 2.",
        "benefit": "No need for detailed CAPEX allocation or technology pathway analysis in Year 1.",
    },
    "MET-06": {
        "alternative": "Information on size (規模に関する情報) instead of monetary amounts",
        "action": "Describe climate-related risk/opportunity exposure by size or proportion (e.g., '% of assets in flood zones', '% revenue from carbon-intensive products') instead of quantitative JPY amounts.",
        "benefit": "SSBJ Schedule of Differences explicitly allows this. Avoids complex financial impact quantification that most companies are not yet ready for.",
    },
    "STR-06": {
        "alternative": "Information on size (規模に関する情報) for physical/transition risk assets",
        "action": "Use qualitative size descriptions for physical risk exposure (e.g., 'X% of manufacturing capacity in high-risk regions') instead of quantified monetary values.",
        "benefit": "SSBJ-specific concession vs ISSB — significantly reduces analytical burden for early disclosures.",
    },
    "RSK-03": {
        "alternative": "Leverage existing ERM framework for climate risk integration",
        "action": "If your ERM already identifies climate risks, cross-reference and extend the existing register rather than building a separate climate risk framework.",
        "benefit": "Demonstrates integration without creating parallel risk systems.",
    },
}

# Criteria that have NO transitional relief for DISCLOSURE — must be disclosed from Year 1
# NOTE: Assurance for these items starts one year AFTER first disclosure (Year 2),
# giving companies a grace period to mature processes before auditor examination.
# Under climate-only Year 1 option, GOV/RSK items are required only to the extent
# they relate to climate-related risks and opportunities (not all sustainability topics).
_NO_RELIEF_ITEMS = {
    "GOV-01": {
        "reason": "Governance oversight: board/committee responsibility for climate-related risks must be disclosed from Year 1.",
        "note": "Under climate-only Year 1, only climate-related governance oversight required — not all sustainability topics.",
        "assurance_note": "Assurance examination begins Year 2 — use Year 1 to establish and document processes.",
    },
    "GOV-02": {
        "reason": "Management roles: climate-related data ownership and sign-off must be disclosed from Year 1.",
        "note": "Under climate-only Year 1, only roles related to climate risk/opportunity management required.",
        "assurance_note": "Assurance examination begins Year 2 — Year 1 is an opportunity to refine role definitions.",
    },
    "GOV-03": {
        "reason": "Board skills: assess climate-related competence. Supporting criterion (SHOULD, not SHALL).",
        "note": "Not a mandatory disclosure item but expected by assurance providers as supporting evidence.",
        "assurance_note": "Good practice to document before assurance begins in Year 2.",
    },
    "GOV-04": {
        "reason": "Strategy integration: board must consider climate-related matters in strategic decisions.",
        "note": "Under climate-only Year 1, focus on how climate risks/opportunities influence strategy.",
        "assurance_note": "Assurance examination begins Year 2 — document board discussion minutes from Year 1.",
    },
    "GOV-05": {
        "reason": "Target oversight: board must oversee climate target-setting process.",
        "note": "Under climate-only Year 1, limited to climate-related targets (GHG reduction, etc.).",
        "assurance_note": "Assurance examination begins Year 2 — establish oversight framework during Year 1.",
    },
    "RSK-01": {
        "reason": "Risk identification: document climate risk identification process from Year 1.",
        "note": "Under climate-only Year 1, focus on climate-specific physical and transition risks.",
        "assurance_note": "Assurance begins Year 2 — use Year 1 to test and refine identification methodology.",
    },
    "RSK-02": {
        "reason": "Risk assessment: methodology for prioritizing climate risks must be disclosed from Year 1.",
        "note": "Under climate-only Year 1, assessment methodology required for climate risks only.",
        "assurance_note": "Assurance begins Year 2 — document assessment criteria and evidence trail during Year 1.",
    },
    "RSK-03": {
        "reason": "Risk mitigation: document climate risk response strategy from Year 1.",
        "note": "Under climate-only Year 1, mitigation strategies required for climate-related risks only.",
        "assurance_note": "Assurance begins Year 2 — establish and document response strategies during Year 1.",
    },
    "RSK-04": {
        "reason": "ERM integration: demonstrate climate risk is part of overall risk management.",
        "note": "Under climate-only Year 1, show climate risk integration into existing ERM framework.",
        "assurance_note": "Assurance begins Year 2 — map climate risks into ERM register during Year 1.",
    },
}

# RSK-05 (Internal Controls) is NOT a standalone SSBJ disclosure item.
# It is implicitly needed for producing assurable data but the FSA roadmap
# does not prescribe it as a separate disclosure requirement.
# We track it separately to avoid misleading users.
_RSK05_NOTE = {
    "reason": "Internal controls over sustainability data — not a standalone SSBJ disclosure item.",
    "note": "The FSA roadmap does not prescribe internal controls as a separate disclosure requirement. "
            "However, robust controls are implicitly needed to produce data that can withstand assurance examination.",
    "assurance_note": "Controls must be in place by Year 2 when assurance begins. Year 1 disclosure does not require separate internal control disclosure.",
}


def _parse_compliance_year(fiscal_year_str):
    """Extract the compliance year from fiscal_year string like 'FY2026 (ending March 2027)'."""
    m = re.search(r"ending\s+\w+\s+(20\d{2})", fiscal_year_str)
    if m:
        return int(m.group(1))
    m2 = re.search(r"FY(20\d{2})", fiscal_year_str)
    if m2:
        return int(m2.group(1)) + 1  # FY2026 ends in 2027
    return 2027  # default


def generate_relief_plan(assessment, responses):
    """
    Generate a personalized transitional relief plan.

    Args:
        assessment: Assessment model instance
        responses: dict of {criterion_id: Response}

    Returns:
        dict with:
        - relief_items: list of applicable relief items with recommendations
        - summary: dict with counts and key metrics
        - japan_items: list of Japan-specific alternatives
    """
    compliance_year = _parse_compliance_year(assessment.fiscal_year)
    fy_end_month = getattr(assessment, "fy_end_month", 3) or 3

    # Determine if this is Year 1 or later
    today = date.today()
    if fy_end_month != 3:
        if fy_end_month < 3:
            adjusted_year = compliance_year
        else:
            adjusted_year = compliance_year - 1
    else:
        adjusted_year = compliance_year

    # First reporting FY end date
    import calendar
    fy_end_day = calendar.monthrange(adjusted_year, fy_end_month)[1]
    first_fy_end = date(adjusted_year, fy_end_month, fy_end_day)

    # Is this the first reporting year?
    is_first_year = today <= first_fy_end
    months_to_deadline = max(0, (first_fy_end.year - today.year) * 12 + first_fy_end.month - today.month)

    relief_items = []
    total_deferred = 0
    total_simplified = 0
    critical_now = 0

    for c in SSBJ_CRITERIA:
        if c["id"] not in _RELIEF_DETAILS:
            continue

        detail = _RELIEF_DETAILS[c["id"]]
        resp = responses.get(c["id"])
        score = resp.score if resp and resp.score is not None else None

        # Determine applicability
        if is_first_year:
            applicable = True
            status = "available"
        else:
            applicable = False
            status = "expired"

        # Determine urgency based on score and LA scope
        if c["la_scope"] == "in_scope" and (score is None or score < 3):
            urgency = "critical"
            critical_now += 1
        elif c["obligation"] == "mandatory" and (score is None or score < 2):
            urgency = "high"
        else:
            urgency = "normal"

        # Is this a full deferral or simplification?
        is_deferral = c["id"] == "MET-03"  # Only Scope 3 can be fully deferred
        if is_deferral and applicable:
            total_deferred += 1
        elif applicable:
            total_simplified += 1

        item = {
            "criterion_id": c["id"],
            "pillar": c["pillar"],
            "category": c["category"],
            "obligation": c["obligation"],
            "la_scope": c["la_scope"],
            "score": score,
            "applicable": applicable,
            "status": status,
            "urgency": urgency,
            "is_deferral": is_deferral,
            "relief": detail["relief"],
            "what_you_can_defer": detail["what_you_can_defer"],
            "what_you_must_do": detail["what_you_must_do"],
            "year2_requirement": detail["year2_requirement"],
        }
        relief_items.append(item)

    # No-relief items (GOV + RSK — disclosure required from Year 1,
    # but assurance starts Year 2, giving a grace period)
    no_relief_items = []
    for c in SSBJ_CRITERIA:
        if c["id"] not in _NO_RELIEF_ITEMS:
            continue
        detail = _NO_RELIEF_ITEMS[c["id"]]
        resp = responses.get(c["id"])
        score = resp.score if resp and resp.score is not None else None
        at_risk = score is not None and score < 3
        no_relief_items.append({
            "criterion_id": c["id"],
            "pillar": c["pillar"],
            "category": c["category"],
            "la_scope": c["la_scope"],
            "score": score,
            "at_risk": at_risk,
            "reason": detail["reason"],
            "climate_only_note": detail["note"],
            "assurance_note": detail["assurance_note"],
        })

    # RSK-05 — not a standalone disclosure item, tracked separately
    rsk05_criterion = next((c for c in SSBJ_CRITERIA if c["id"] == "RSK-05"), None)
    rsk05_item = None
    if rsk05_criterion:
        resp = responses.get("RSK-05")
        score = resp.score if resp and resp.score is not None else None
        rsk05_item = {
            "criterion_id": "RSK-05",
            "pillar": rsk05_criterion["pillar"],
            "category": rsk05_criterion["category"],
            "la_scope": rsk05_criterion["la_scope"],
            "score": score,
            "at_risk": score is not None and score < 3,
            "reason": _RSK05_NOTE["reason"],
            "note": _RSK05_NOTE["note"],
            "assurance_note": _RSK05_NOTE["assurance_note"],
        }

    # Japan-specific alternatives (always applicable)
    japan_items = []
    for c in SSBJ_CRITERIA:
        if c["id"] not in _JAPAN_ALTERNATIVES:
            continue
        alt = _JAPAN_ALTERNATIVES[c["id"]]
        resp = responses.get(c["id"])
        score = resp.score if resp and resp.score is not None else None

        japan_items.append({
            "criterion_id": c["id"],
            "pillar": c["pillar"],
            "category": c["category"],
            "score": score,
            "alternative": alt["alternative"],
            "action": alt["action"],
            "benefit": alt["benefit"],
        })

    # Climate-only Year 1 analysis (SSBJ No.2 focus)
    # Under SSBJ transition provisions, companies may focus on climate (S2)
    # disclosures in Year 1 and expand to general (S1) in Year 2.
    s1_criteria = [c for c in SSBJ_CRITERIA if c.get("standard") == "General (S1)"]
    s2_criteria = [c for c in SSBJ_CRITERIA if c.get("standard") == "Climate (S2)"]
    s1_count = len(s1_criteria)
    s2_count = len(s2_criteria)

    # Count S2 gaps (climate items that need work)
    s2_gaps = 0
    s1_gaps = 0
    for c in SSBJ_CRITERIA:
        resp = responses.get(c["id"])
        if resp and resp.score is not None and resp.score < 3:
            if c.get("standard") == "Climate (S2)":
                s2_gaps += 1
            else:
                s1_gaps += 1

    # S1 items that are NOT in initial LA scope (can potentially defer)
    s1_deferrable = [c for c in s1_criteria
                     if c["la_scope"] != "in_scope"]
    # S1 items IN LA scope (cannot defer even in climate-only mode)
    s1_la_scope = [c for c in s1_criteria
                   if c["la_scope"] == "in_scope"]

    climate_only_option = {
        "available": is_first_year,
        "s1_total": s1_count,
        "s2_total": s2_count,
        "s1_gaps": s1_gaps,
        "s2_gaps": s2_gaps,
        "s1_deferrable_count": len(s1_deferrable),
        "s1_la_scope_count": len(s1_la_scope),
        "s1_deferrable": [{"id": c["id"], "category": c["category"]} for c in s1_deferrable],
        "s1_la_scope": [{"id": c["id"], "category": c["category"]} for c in s1_la_scope],
        "note": (
            "SSBJ transition provisions allow climate-focused (SSBJ No.2) disclosure in Year 1. "
            f"However, {len(s1_la_scope)} General (S1) criteria are in initial LA scope "
            "(Governance + Risk Management) and CANNOT be deferred regardless."
        ),
    }

    summary = {
        "is_first_year": is_first_year,
        "months_to_deadline": months_to_deadline,
        "first_fy_end": first_fy_end.strftime("%B %Y"),
        "total_relief_available": len([r for r in relief_items if r["applicable"]]),
        "total_deferred": total_deferred,
        "total_simplified": total_simplified,
        "critical_now": critical_now,
        "japan_alternatives": len(japan_items),
        "no_relief_count": len(no_relief_items),
        "no_relief_at_risk": len([n for n in no_relief_items if n["at_risk"]]),
    }

    return {
        "relief_items": relief_items,
        "no_relief_items": no_relief_items,
        "rsk05_item": rsk05_item,
        "summary": summary,
        "japan_items": japan_items,
        "climate_only_option": climate_only_option,
    }
