"""
Project Execution Checklist Generator

Generates a structured, phase-by-phase checklist for companies that received the
SSBJ gap analysis report. Bridges the gap between "here's your assessment" and
"here's your project plan" by auto-generating:

1. Phase-by-phase task checklist with concrete deliverables
2. Evidence & documentation tracker (what the auditor will request)
3. Resource & budget indicators per phase
4. Assurance preparation milestones with gate reviews
5. Year 2+ forward-look for deferred items

All data is derived from existing assessment scores, RACI assignments,
roadmap phases, and relief advisor outputs.
"""

from datetime import date
from app.ssbj_criteria import SSBJ_CRITERIA


# Evidence artifacts the auditor will request per criterion (ISSA 5000 / ISAE 3410)
_EVIDENCE_MAP = {
    "GOV-01": [
        {"document": "Board/committee charter (terms of reference) with sustainability mandate", "format": "PDF/Word"},
        {"document": "Board meeting minutes showing sustainability agenda items", "format": "PDF"},
        {"document": "Committee membership list with appointment dates", "format": "PDF/Excel"},
    ],
    "GOV-02": [
        {"document": "Management role descriptions (data owner, reviewer, approver)", "format": "PDF/Word"},
        {"document": "Organizational chart showing sustainability reporting lines", "format": "PDF"},
        {"document": "Sign-off authorization matrix for sustainability data", "format": "Excel"},
    ],
    "GOV-03": [
        {"document": "Board skills matrix with ESG/sustainability competencies", "format": "Excel"},
        {"document": "Training records for sustainability-related sessions", "format": "PDF"},
    ],
    "GOV-04": [
        {"document": "Board meeting minutes discussing sustainability in strategy", "format": "PDF"},
        {"document": "Strategic planning documents referencing climate/sustainability risks", "format": "PDF/Word"},
    ],
    "GOV-05": [
        {"document": "Board resolution on climate target-setting / approval of targets", "format": "PDF"},
        {"document": "Target oversight framework document", "format": "PDF/Word"},
    ],
    "STR-01": [
        {"document": "Time horizon definitions (short/medium/long-term)", "format": "Word/PDF"},
        {"document": "Climate/sustainability risk register", "format": "Excel"},
        {"document": "Value chain assessment boundary document", "format": "Word/PDF"},
        {"document": "Hotspot identification analysis", "format": "Excel/PDF"},
    ],
    "STR-02": [
        {"document": "Value chain map (upstream to downstream)", "format": "Diagram/PDF"},
        {"document": "Assessment boundary disclosure (included/excluded and why)", "format": "Word/PDF"},
        {"document": "Business model impact assessment", "format": "Word/PDF"},
    ],
    "STR-03": [
        {"document": "Financial effects analysis (position, performance, cash flows)", "format": "Word/PDF"},
        {"document": "Quantification methodology (or explanation of why qualitative)", "format": "Word/PDF"},
    ],
    "STR-04": [
        {"document": "Scenario selection rationale and source citations", "format": "Word/PDF"},
        {"document": "Assumptions and parameters per scenario", "format": "Excel/Word"},
        {"document": "Strategy feedback narrative (how analysis informed strategy)", "format": "Word/PDF"},
        {"document": "Resilience assessment conclusion", "format": "Word/PDF"},
    ],
    "STR-05": [
        {"document": "Transition plan document (even if directional)", "format": "Word/PDF"},
        {"document": "Board approval of transition commitments", "format": "PDF"},
    ],
    "STR-06": [
        {"document": "Resilience assessment (climate resilience covered under STR-04)", "format": "Word/PDF"},
    ],
    "STR-07": [
        {"document": "Mapping table: sustainability disclosures to financial statement line items", "format": "Excel"},
    ],
    "RSK-01": [
        {"document": "Risk identification methodology document", "format": "Word/PDF"},
        {"document": "Climate risk register (physical + transition)", "format": "Excel"},
    ],
    "RSK-02": [
        {"document": "Risk assessment criteria and scoring methodology", "format": "Word/PDF"},
        {"document": "Risk assessment results with prioritization", "format": "Excel"},
    ],
    "RSK-03": [
        {"document": "Risk response strategies per identified risk", "format": "Word/PDF"},
        {"document": "Mitigation action plan with timelines", "format": "Excel"},
    ],
    "RSK-04": [
        {"document": "ERM framework showing climate risk integration", "format": "Word/PDF"},
        {"document": "Cross-reference: sustainability risk register to enterprise risk register", "format": "Excel"},
    ],
    "RSK-05": [
        {"document": "Internal controls framework document (data governance)", "format": "Word/PDF"},
        {"document": "Data collection procedures (step-by-step)", "format": "Word/PDF"},
        {"document": "Maker-checker review log (who reviewed, when, sign-off)", "format": "Excel"},
        {"document": "Data reconciliation checklist", "format": "Excel"},
        {"document": "Audit trail (data change log)", "format": "Excel/System"},
    ],
    "MET-01": [
        {"document": "Scope 1 emission source inventory (all facilities)", "format": "Excel"},
        {"document": "Calculation methodology document (emission factors, sources)", "format": "Word/PDF"},
        {"document": "Activity data (fuel invoices, meter readings)", "format": "Original + Excel"},
        {"document": "Calculation spreadsheet with review sign-off", "format": "Excel"},
        {"document": "Emission factor sources and version documentation", "format": "PDF/Excel"},
    ],
    "MET-02": [
        {"document": "Scope 2 facility electricity consumption data", "format": "Excel + invoices"},
        {"document": "Grid emission factors with area-specific sources", "format": "Excel"},
        {"document": "Location-based calculation spreadsheet", "format": "Excel"},
        {"document": "Market-based calculation (if green energy purchased)", "format": "Excel"},
    ],
    "MET-03": [
        {"document": "Scope 3 category materiality assessment (all 15 categories)", "format": "Excel"},
        {"document": "Supplier engagement plan and correspondence", "format": "Word/PDF"},
        {"document": "Data collection plan per category", "format": "Excel"},
    ],
    "MET-04": [
        {"document": "Climate targets with base year, target year, methodology", "format": "Word/PDF"},
        {"document": "Board approval of targets", "format": "PDF"},
    ],
    "MET-05": [
        {"document": "Industry-specific metrics disclosure (if applicable)", "format": "Word/PDF"},
    ],
    "MET-06": [
        {"document": "Climate-related financial amounts or size information", "format": "Word/PDF"},
    ],
    "MET-07": [
        {"document": "Data governance policy", "format": "Word/PDF"},
        {"document": "Data flow diagram (source to disclosure)", "format": "Diagram/PDF"},
        {"document": "Validation rules and procedures", "format": "Word/PDF"},
        {"document": "Error log and correction records", "format": "Excel"},
        {"document": "Completeness check records", "format": "Excel"},
    ],
    "MET-08": [
        {"document": "GHG intensity calculation and denominator selection rationale", "format": "Excel"},
    ],
    "MET-09": [
        {"document": "Remuneration policy referencing climate/sustainability metrics", "format": "PDF"},
        {"document": "Board resolution on climate-linked remuneration", "format": "PDF"},
    ],
}

# Resource/effort indicators per criterion for gap closure
_EFFORT_MAP = {
    "GOV-01": {"effort_days": "3-5", "skills": ["Board secretary", "ESG lead"], "external": False},
    "GOV-02": {"effort_days": "3-5", "skills": ["ESG lead", "HR"], "external": False},
    "GOV-03": {"effort_days": "2-3", "skills": ["HR", "ESG lead"], "external": False},
    "GOV-04": {"effort_days": "3-5", "skills": ["Board secretary", "Strategy"], "external": False},
    "GOV-05": {"effort_days": "3-5", "skills": ["Board secretary", "ESG lead"], "external": False},
    "STR-01": {"effort_days": "10-20", "skills": ["Risk management", "ESG lead", "Operations"], "external": True},
    "STR-02": {"effort_days": "10-20", "skills": ["ESG lead", "Operations", "Procurement"], "external": True},
    "STR-03": {"effort_days": "10-15", "skills": ["Finance", "ESG lead"], "external": True},
    "STR-04": {"effort_days": "15-25", "skills": ["ESG lead", "Risk management", "External consultant"], "external": True},
    "STR-05": {"effort_days": "10-15", "skills": ["ESG lead", "Strategy", "Operations"], "external": True},
    "STR-06": {"effort_days": "5-10", "skills": ["ESG lead", "Risk management"], "external": False},
    "STR-07": {"effort_days": "5-10", "skills": ["Finance", "ESG lead", "IR"], "external": False},
    "RSK-01": {"effort_days": "5-10", "skills": ["Risk management", "ESG lead"], "external": False},
    "RSK-02": {"effort_days": "5-10", "skills": ["Risk management", "ESG lead"], "external": False},
    "RSK-03": {"effort_days": "5-10", "skills": ["Risk management", "ESG lead", "Operations"], "external": False},
    "RSK-04": {"effort_days": "5-10", "skills": ["Risk management", "ESG lead"], "external": False},
    "RSK-05": {"effort_days": "15-30", "skills": ["Finance/Accounting", "IT", "ESG lead"], "external": True},
    "MET-01": {"effort_days": "15-25", "skills": ["Operations", "ESG lead", "External verifier"], "external": True},
    "MET-02": {"effort_days": "10-15", "skills": ["Operations", "ESG lead", "Facilities"], "external": True},
    "MET-03": {"effort_days": "20-40", "skills": ["Procurement", "ESG lead", "External consultant"], "external": True},
    "MET-04": {"effort_days": "5-10", "skills": ["ESG lead", "Board secretary"], "external": False},
    "MET-05": {"effort_days": "3-5", "skills": ["ESG lead", "IR"], "external": False},
    "MET-06": {"effort_days": "5-10", "skills": ["Finance", "ESG lead"], "external": False},
    "MET-07": {"effort_days": "15-25", "skills": ["Finance/Accounting", "IT", "ESG lead"], "external": True},
    "MET-08": {"effort_days": "3-5", "skills": ["ESG lead", "Finance"], "external": False},
    "MET-09": {"effort_days": "5-10", "skills": ["HR", "Board secretary", "Legal"], "external": False},
}

# Budget categories
_BUDGET_CATEGORIES = {
    "internal_fte": "Internal staff time",
    "ghg_software": "GHG calculation software / tools",
    "external_consultant": "External ESG consultant",
    "assurance_fees": "Assurance engagement fees",
    "training": "Staff training & capacity building",
    "data_systems": "Data management systems",
    "supplier_engagement": "Supplier engagement program",
}


def _classify_phase(criterion, score, relief_applicable, la_scope, months_remaining):
    """Determine which roadmap phase a criterion's gap closure belongs to."""
    if score is None:
        return 1  # Unscored = start immediately

    if la_scope == "in_scope" and score < 3:
        # LA-critical gaps: front-load
        if months_remaining <= 12:
            return 1
        return 2

    if score == 0:
        return 1  # Not started = immediate
    elif score == 1:
        if la_scope == "in_scope":
            return 2
        return 3
    elif score == 2:
        if la_scope == "in_scope":
            return 3
        return 4
    else:
        # Score 3+ but could improve
        return 5

    return 3  # fallback


def generate_checklist(assessment, responses, roadmap_data=None, raci_data=None, relief_data=None):
    """
    Generate a project execution checklist from assessment data.

    Args:
        assessment: Assessment model instance
        responses: dict of {criterion_id: Response}
        roadmap_data: dict from generate_roadmap() (optional, generated if None)
        raci_data: dict from generate_raci() (optional, generated if None)
        relief_data: dict from generate_relief_plan() (optional, generated if None)

    Returns dict with:
        - phases: list of phase dicts with tasks, evidence, resources
        - evidence_tracker: list of all evidence items with status
        - budget_summary: estimated budget categories
        - gate_reviews: list of milestone gates
        - year2_prep: deferred items requiring Year 1 groundwork
        - summary: overall stats
    """
    criteria_map = {c["id"]: c for c in SSBJ_CRITERIA}

    # Generate dependent data if not provided
    if roadmap_data is None:
        from app.roadmap import generate_roadmap
        scored = [r for r in responses.values() if r.score is not None]
        if scored:
            roadmap_data = generate_roadmap(assessment, list(scored))

    if raci_data is None:
        from app.raci import generate_raci
        raci_data = generate_raci(assessment, responses)

    if relief_data is None:
        from app.relief_advisor import generate_relief_plan
        relief_data = generate_relief_plan(assessment, responses)

    months_remaining = roadmap_data["months_remaining"] if roadmap_data else 18

    # Build RACI lookup: criterion_id -> {dept_code: role}
    raci_lookup = {}
    if raci_data:
        for row in raci_data.get("criteria", []):
            raci_lookup[row["id"]] = row.get("dept_roles", {})

    # Relief lookup
    relief_lookup = {}
    if relief_data:
        for item in relief_data.get("relief_items", []):
            relief_lookup[item["criterion_id"]] = item

    # --- Build per-criterion task items ---
    all_tasks = []
    total_effort_min = 0
    total_effort_max = 0
    needs_external = False

    for c in SSBJ_CRITERIA:
        cid = c["id"]
        resp = responses.get(cid)
        score = resp.score if resp and resp.score is not None else None
        evidence_text = (resp.evidence or "") if resp else ""

        is_gap = score is not None and score < 3
        is_unscored = score is None
        target_score = 3 if c["la_scope"] == "in_scope" else 3

        # Phase assignment
        phase_num = _classify_phase(
            c, score,
            cid in relief_lookup and relief_lookup[cid].get("applicable"),
            c["la_scope"],
            months_remaining,
        )

        # Evidence items
        evidence_items = []
        for ev in _EVIDENCE_MAP.get(cid, []):
            # Check if evidence text mentions key words from the document name
            doc_keywords = ev["document"].lower().split()[:3]
            mentioned = any(kw in evidence_text.lower() for kw in doc_keywords if len(kw) > 3)
            evidence_items.append({
                "document": ev["document"],
                "format": ev["format"],
                "status": "likely_exists" if mentioned and score and score >= 3 else (
                    "in_progress" if mentioned else "not_started"
                ),
            })

        # RACI for this criterion
        raci_roles = raci_lookup.get(cid, {})
        responsible = [code for code, role in raci_roles.items() if role == "R"]
        accountable = [code for code, role in raci_roles.items() if role == "A"]

        # Effort
        effort = _EFFORT_MAP.get(cid, {"effort_days": "5-10", "skills": [], "external": False})
        if is_gap or is_unscored:
            parts = effort["effort_days"].split("-")
            total_effort_min += int(parts[0])
            total_effort_max += int(parts[1]) if len(parts) > 1 else int(parts[0])
            if effort["external"]:
                needs_external = True

        # Relief info
        relief_info = relief_lookup.get(cid)
        can_defer = relief_info and relief_info.get("is_deferral") and relief_info.get("applicable")
        can_simplify = relief_info and relief_info.get("applicable") and not relief_info.get("is_deferral")

        task = {
            "criterion_id": cid,
            "pillar": c["pillar"],
            "category": c["category"],
            "standard": c["standard"],
            "obligation": c["obligation"],
            "la_scope": c["la_scope"],
            "la_priority": c.get("la_priority", ""),
            "score": score,
            "target_score": target_score,
            "is_gap": is_gap,
            "is_unscored": is_unscored,
            "phase": phase_num,
            "deliverable": c.get("minimum_action", ""),
            "evidence_items": evidence_items,
            "responsible": responsible,
            "accountable": accountable,
            "effort_days": effort["effort_days"],
            "skills_needed": effort["skills"],
            "external_help": effort["external"],
            "can_defer": can_defer,
            "can_simplify": can_simplify,
            "relief_note": relief_info["relief"] if relief_info and relief_info.get("applicable") else None,
            "year2_req": relief_info["year2_requirement"] if relief_info else None,
        }
        all_tasks.append(task)

    # --- Group tasks into phases ---
    phase_defs = [
        {"number": 1, "title": "Immediate Actions", "subtitle": "Weeks 1-4: Foundation & critical gaps",
         "icon": "bi-lightning", "color": "danger"},
        {"number": 2, "title": "Governance & Controls Setup", "subtitle": "Months 1-3: Policies, roles, frameworks",
         "icon": "bi-building", "color": "primary"},
        {"number": 3, "title": "Data & Process Build", "subtitle": "Months 3-6: Systems, calculations, evidence",
         "icon": "bi-gear", "color": "warning"},
        {"number": 4, "title": "Dry Run & Review", "subtitle": "Months 6-9: Internal review, mock audit prep",
         "icon": "bi-clipboard-check", "color": "info"},
        {"number": 5, "title": "Polish & Assurance Prep", "subtitle": "Months 9-12: Final prep, auditor engagement",
         "icon": "bi-shield-check", "color": "success"},
    ]

    phases = []
    for pdef in phase_defs:
        phase_tasks = [t for t in all_tasks if t["phase"] == pdef["number"]]
        gap_tasks = [t for t in phase_tasks if t["is_gap"] or t["is_unscored"]]
        ok_tasks = [t for t in phase_tasks if not t["is_gap"] and not t["is_unscored"]]

        phase_effort_min = sum(int(t["effort_days"].split("-")[0]) for t in gap_tasks)
        parts_max = [t["effort_days"].split("-") for t in gap_tasks]
        phase_effort_max = sum(int(p[1]) if len(p) > 1 else int(p[0]) for p in parts_max)

        phases.append({
            **pdef,
            "tasks": phase_tasks,
            "gap_tasks": gap_tasks,
            "ok_tasks": ok_tasks,
            "task_count": len(phase_tasks),
            "gap_count": len(gap_tasks),
            "effort_range": f"{phase_effort_min}-{phase_effort_max}" if gap_tasks else "0",
        })

    # --- Evidence tracker (flat list across all criteria) ---
    evidence_tracker = []
    for task in all_tasks:
        for ev in task["evidence_items"]:
            evidence_tracker.append({
                "criterion_id": task["criterion_id"],
                "pillar": task["pillar"],
                "category": task["category"],
                "la_scope": task["la_scope"],
                "document": ev["document"],
                "format": ev["format"],
                "status": ev["status"],
                "phase": task["phase"],
                "responsible": task["responsible"],
            })

    # --- Budget summary ---
    gap_count = sum(1 for t in all_tasks if t["is_gap"])
    la_gap_count = sum(1 for t in all_tasks if t["is_gap"] and t["la_scope"] == "in_scope")
    external_items = sum(1 for t in all_tasks if t["is_gap"] and t["external_help"])

    budget_items = []
    budget_items.append({
        "category": "Internal staff time",
        "estimate": f"{total_effort_min}-{total_effort_max} person-days",
        "note": f"Across {gap_count} gap items. Assumes dedicated project team.",
    })
    if external_items > 0:
        budget_items.append({
            "category": "External ESG consultant",
            "estimate": "¥5M-¥15M",
            "note": f"{external_items} items may need external expertise (scenario analysis, GHG calculation, value chain mapping).",
        })
    budget_items.append({
        "category": "Assurance engagement fees",
        "estimate": "¥5M-¥30M+",
        "note": "Limited assurance for Scope 1 & 2, Governance, Risk Management. Varies by company size and complexity.",
    })
    if any(t["is_gap"] and t["criterion_id"] in ("MET-01", "MET-02", "MET-07", "RSK-05") for t in all_tasks):
        budget_items.append({
            "category": "GHG calculation software / data systems",
            "estimate": "¥1M-¥10M/year",
            "note": "Consider: Zeroboard, Persefoni, booost, or enhanced spreadsheet approach for Year 1.",
        })
    budget_items.append({
        "category": "Training & capacity building",
        "estimate": "¥0.5M-¥2M",
        "note": "Board sustainability briefing, GHG accounting training, ISSA 5000 awareness.",
    })

    # --- Gate reviews (milestone checkpoints) ---
    gate_reviews = [
        {
            "gate": "G1: Project Kickoff",
            "timing": "Week 1",
            "criteria": "Budget approved, project team assigned, gap analysis reviewed by management",
            "owner": "Project Sponsor",
            "phase": 1,
        },
        {
            "gate": "G2: Governance Ready",
            "timing": "Month 3",
            "criteria": "Board charter amended, management roles assigned, sustainability committee established",
            "owner": "ESG Lead / Board Secretary",
            "phase": 2,
        },
        {
            "gate": "G3: Data Collection Complete",
            "timing": "Month 6",
            "criteria": "Scope 1 & 2 data collected for all sites, internal controls documented, data quality checks in place",
            "owner": "ESG Lead / Data Owner",
            "phase": 3,
        },
        {
            "gate": "G4: Dry Run Complete",
            "timing": "Month 9",
            "criteria": "Draft disclosure complete, internal review passed, evidence binders organized",
            "owner": "ESG Lead",
            "phase": 4,
        },
        {
            "gate": "G5: Assurance Ready",
            "timing": "Month 12",
            "criteria": "Assurance provider selected, pre-engagement review complete, all LA-scope items at score 3+",
            "owner": "Project Sponsor",
            "phase": 5,
        },
    ]

    # --- Year 2+ preparation items ---
    year2_prep = []
    for task in all_tasks:
        if task["can_defer"]:
            year2_prep.append({
                "criterion_id": task["criterion_id"],
                "category": task["category"],
                "relief_note": task["relief_note"],
                "year2_req": task["year2_req"],
                "year1_action": "Begin groundwork even though calculation can be deferred. Year 2 auditors will ask what you did in Year 1.",
            })

    # Items not deferred but need Year 2 expansion
    for item in relief_data.get("relief_items", []) if relief_data else []:
        if not item.get("is_deferral") and item.get("applicable") and item.get("year2_requirement"):
            if not any(y["criterion_id"] == item["criterion_id"] for y in year2_prep):
                year2_prep.append({
                    "criterion_id": item["criterion_id"],
                    "category": item["category"],
                    "relief_note": item["relief"],
                    "year2_req": item["year2_requirement"],
                    "year1_action": f"Year 1 simplified approach: {item['what_you_must_do']}",
                })

    # --- Summary stats ---
    summary = {
        "total_criteria": len(SSBJ_CRITERIA),
        "total_gaps": gap_count,
        "la_gaps": la_gap_count,
        "total_evidence_items": len(evidence_tracker),
        "evidence_not_started": sum(1 for e in evidence_tracker if e["status"] == "not_started"),
        "evidence_in_progress": sum(1 for e in evidence_tracker if e["status"] == "in_progress"),
        "evidence_likely_exists": sum(1 for e in evidence_tracker if e["status"] == "likely_exists"),
        "total_effort_range": f"{total_effort_min}-{total_effort_max}",
        "needs_external_help": needs_external,
        "external_items_count": external_items,
        "year2_deferred_count": len([y for y in year2_prep if "deferred" in (y.get("relief_note") or "").lower()]),
        "year2_expansion_count": len(year2_prep),
        "months_remaining": months_remaining,
        "gate_count": len(gate_reviews),
    }

    return {
        "phases": phases,
        "evidence_tracker": evidence_tracker,
        "budget_summary": budget_items,
        "gate_reviews": gate_reviews,
        "year2_prep": year2_prep,
        "summary": summary,
    }
