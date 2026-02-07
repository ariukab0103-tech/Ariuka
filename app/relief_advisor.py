"""
B3: Transitional Relief Advisor

Dynamically determines which SSBJ transitional reliefs apply to a specific
assessment based on:
- Fiscal year and reporting timeline
- Current maturity scores
- LA scope status (in_scope, supporting, not_in_initial_scope)

Provides prioritized, actionable recommendations on what can be deferred,
simplified, or must be addressed immediately.
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
        "relief": "First-year Scope 1 may use simplified calculation methodology.",
        "what_you_can_defer": "Full GHG Protocol alignment with facility-level granularity",
        "what_you_must_do": "Calculate total Scope 1 using available data. Document methodology and emission factors used.",
        "year2_requirement": "Align fully with GHG Protocol Corporate Standard",
    },
    "MET-02": {
        "relief": "First-year Scope 2 location-based calculation is sufficient.",
        "what_you_can_defer": "Market-based Scope 2 calculation",
        "what_you_must_do": "Calculate location-based Scope 2 using grid emission factors",
        "year2_requirement": "Add market-based Scope 2 calculation alongside location-based",
    },
    "MET-03": {
        "relief": "Scope 3 disclosure may be DEFERRED entirely in first reporting year.",
        "what_you_can_defer": "ALL Scope 3 calculations and disclosures",
        "what_you_must_do": "Nothing required in Year 1, but recommended: begin supplier data collection and category assessment",
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

    summary = {
        "is_first_year": is_first_year,
        "months_to_deadline": months_to_deadline,
        "first_fy_end": first_fy_end.strftime("%B %Y"),
        "total_relief_available": len([r for r in relief_items if r["applicable"]]),
        "total_deferred": total_deferred,
        "total_simplified": total_simplified,
        "critical_now": critical_now,
        "japan_alternatives": len(japan_items),
    }

    return {
        "relief_items": relief_items,
        "summary": summary,
        "japan_items": japan_items,
    }
