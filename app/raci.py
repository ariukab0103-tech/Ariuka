"""
B1: RACI Generator for SSBJ Gap Assessment

Generates a Responsible / Accountable / Consulted / Informed matrix
based on SSBJ criteria, typical Japanese corporate structures, and
the entity's current assessment scores.

Standard departments mapped:
- Board / Sustainability Committee
- Sustainability / ESG Office
- Finance / Accounting
- Legal / Compliance
- Risk Management
- Operations / Manufacturing
- HR / General Affairs
- IR / Communications
- IT / Systems
- Procurement / Supply Chain
"""

from app.ssbj_criteria import SSBJ_CRITERIA

# Department short codes and full names
DEPARTMENTS = [
    ("board", "Board / Sustainability Committee"),
    ("esg", "Sustainability / ESG Office"),
    ("finance", "Finance / Accounting"),
    ("legal", "Legal / Compliance"),
    ("risk", "Risk Management"),
    ("ops", "Operations / Manufacturing"),
    ("hr", "HR / General Affairs"),
    ("ir", "IR / Communications"),
    ("it", "IT / Systems"),
    ("procurement", "Procurement / Supply Chain"),
]

# RACI mapping per criterion: R=Responsible, A=Accountable, C=Consulted, I=Informed
# Based on typical Japanese listed-company structures
_RACI_MAP = {
    # Governance
    "GOV-01": {"board": "A", "esg": "R", "legal": "C", "ir": "I"},
    "GOV-02": {"board": "A", "esg": "R", "legal": "R", "ir": "I"},
    "GOV-03": {"board": "A", "hr": "R", "esg": "C", "legal": "I"},
    "GOV-04": {"board": "I", "esg": "A", "finance": "C", "risk": "C", "ops": "C"},
    "GOV-05": {"board": "A", "esg": "R", "finance": "C", "risk": "C", "ops": "I"},
    # Strategy
    "STR-01": {"board": "I", "esg": "A", "risk": "R", "ops": "C", "procurement": "C"},
    "STR-02": {"board": "I", "esg": "A", "ops": "R", "procurement": "R", "finance": "C"},
    "STR-03": {"board": "I", "esg": "C", "finance": "R", "ir": "C"},
    "STR-04": {"board": "I", "esg": "R", "risk": "R", "finance": "C", "ops": "C"},
    "STR-05": {"board": "A", "esg": "R", "ops": "C", "finance": "C", "procurement": "C"},
    "STR-06": {"board": "I", "esg": "R", "risk": "C", "finance": "C"},
    "STR-07": {"board": "I", "esg": "C", "finance": "R", "ir": "C"},
    # Risk Management
    "RSK-01": {"board": "I", "risk": "R", "esg": "A", "ops": "C", "legal": "C"},
    "RSK-02": {"board": "I", "risk": "R", "esg": "A", "ops": "C"},
    "RSK-03": {"board": "I", "risk": "A", "esg": "R", "legal": "C"},
    "RSK-04": {"board": "I", "risk": "R", "esg": "A", "ops": "C", "finance": "C"},
    "RSK-05": {"board": "I", "esg": "A", "finance": "R", "it": "R", "ops": "C"},
    # Metrics & Targets
    "MET-01": {"board": "I", "esg": "A", "ops": "R", "finance": "C", "it": "C"},
    "MET-02": {"board": "I", "esg": "A", "ops": "R", "finance": "C", "procurement": "C"},
    "MET-03": {"board": "I", "esg": "A", "procurement": "R", "ops": "R", "finance": "C"},
    "MET-04": {"board": "A", "esg": "R", "ops": "C", "finance": "C"},
    "MET-05": {"board": "I", "esg": "R", "ops": "C", "ir": "C"},
    "MET-06": {"board": "I", "esg": "R", "finance": "R", "ops": "C"},
    "MET-07": {"board": "I", "esg": "A", "finance": "R", "it": "R", "ops": "C"},
    "MET-08": {"board": "I", "esg": "R", "finance": "C", "ops": "C"},
    "MET-09": {"board": "A", "hr": "R", "esg": "C", "legal": "C"},
}


def generate_raci(assessment, responses):
    """
    Generate a RACI matrix for the assessment.

    Args:
        assessment: Assessment model instance
        responses: dict of {criterion_id: Response} for current scores

    Returns:
        dict with:
        - departments: list of (code, name) tuples
        - criteria: list of dicts with criterion info + raci assignments
        - dept_workload: dict of dept_code -> {R: count, A: count, C: count, I: count}
        - priority_actions: list of high-priority items needing attention
    """
    criteria_raci = []
    dept_workload = {code: {"R": 0, "A": 0, "C": 0, "I": 0} for code, _ in DEPARTMENTS}
    priority_actions = []

    for c in SSBJ_CRITERIA:
        raci = _RACI_MAP.get(c["id"], {})
        resp = responses.get(c["id"])
        score = resp.score if resp and resp.score is not None else None

        # Build per-department RACI for this criterion
        dept_roles = {}
        for dept_code, _ in DEPARTMENTS:
            role = raci.get(dept_code, "")
            dept_roles[dept_code] = role
            if role in ("R", "A", "C", "I"):
                dept_workload[dept_code][role] += 1

        row = {
            "id": c["id"],
            "pillar": c["pillar"],
            "category": c["category"],
            "obligation": c["obligation"],
            "la_scope": c["la_scope"],
            "score": score,
            "dept_roles": dept_roles,
        }
        criteria_raci.append(row)

        # Flag priority actions: LA in_scope + score < 3
        if c["la_scope"] == "in_scope" and (score is None or score < 3):
            responsible_depts = [
                name for code, name in DEPARTMENTS if raci.get(code) == "R"
            ]
            accountable_depts = [
                name for code, name in DEPARTMENTS if raci.get(code) == "A"
            ]
            priority_actions.append({
                "criterion_id": c["id"],
                "category": c["category"],
                "score": score,
                "gap": 3 - (score or 0),
                "responsible": responsible_depts,
                "accountable": accountable_depts,
                "obligation": c["obligation"],
            })

    return {
        "departments": DEPARTMENTS,
        "criteria": criteria_raci,
        "dept_workload": dept_workload,
        "priority_actions": priority_actions,
    }
