"""
Auto-Assessment Analyzer

Extracts text from uploaded documents and automatically scores each SSBJ
criterion based on keyword/concept matching against the document content.

Scoring logic:
- Scans all uploaded documents for keywords relevant to each criterion
- Assigns maturity scores (0-5) based on depth of coverage
- Provides evidence excerpts showing which parts of documents matched
"""

import os
import csv
import io
import re

from app.ssbj_criteria import SSBJ_CRITERIA


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_file(filepath):
    """Extract text content from a file based on its extension."""
    ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""

    try:
        if ext == "pdf":
            return _extract_pdf(filepath)
        elif ext == "docx":
            return _extract_docx(filepath)
        elif ext in ("xlsx", "xls"):
            return _extract_xlsx(filepath)
        elif ext == "csv":
            return _extract_csv(filepath)
        elif ext == "txt":
            return _extract_txt(filepath)
        else:
            return ""
    except Exception:
        return ""


def _extract_pdf(filepath):
    from PyPDF2 import PdfReader
    reader = PdfReader(filepath)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _extract_docx(filepath):
    from docx import Document
    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_xlsx(filepath):
    from openpyxl import load_workbook
    wb = load_workbook(filepath, read_only=True, data_only=True)
    parts = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None]
            if cells:
                parts.append(" | ".join(cells))
    wb.close()
    return "\n".join(parts)


def _extract_csv(filepath):
    parts = []
    with open(filepath, "r", errors="replace") as f:
        reader = csv.reader(f)
        for row in reader:
            parts.append(" | ".join(row))
    return "\n".join(parts)


def _extract_txt(filepath):
    with open(filepath, "r", errors="replace") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Criterion keyword definitions
# ---------------------------------------------------------------------------

# Each criterion maps to keyword groups at different maturity levels.
# level_keywords[level] = list of keywords/phrases.
# Score = highest level where at least one keyword matches.
# If no keywords match at all, score = 0.

CRITERION_KEYWORDS = {
    "GOV-01": {
        1: ["sustainability", "ESG", "oversight", "governance"],
        2: ["board", "committee", "responsible", "sustainability committee"],
        3: ["terms of reference", "mandate", "charter", "board oversight", "sustainability oversight", "reporting line"],
        4: ["regular review", "quarterly", "annual review", "monitoring", "KPI", "performance review"],
        5: ["continuous improvement", "leading practice", "integrated governance", "assurance-ready"],
    },
    "GOV-02": {
        1: ["policy", "governance", "sustainability"],
        2: ["board mandate", "corporate governance", "terms of reference"],
        3: ["sustainability policy", "governance policy", "board charter", "committee charter", "explicit reference"],
        4: ["policy review", "annual update", "policy monitoring", "compliance check"],
        5: ["integrated policy framework", "best practice", "continuous improvement"],
    },
    "GOV-03": {
        1: ["skills", "competence", "training"],
        2: ["sustainability knowledge", "board training", "expertise"],
        3: ["skills matrix", "training program", "competency framework", "sustainability expertise"],
        4: ["regular training", "competency assessment", "external advisor", "specialist"],
        5: ["continuous learning", "certified", "leading expertise"],
    },
    "GOV-04": {
        1: ["management", "role", "sustainability"],
        2: ["management responsibility", "reporting", "sustainability manager"],
        3: ["management role", "organizational chart", "reporting structure", "data owner", "role description"],
        4: ["management KPI", "performance monitoring", "regular reporting", "management review"],
        5: ["integrated management", "cross-functional", "embedded sustainability"],
    },
    "GOV-05": {
        1: ["climate", "risk", "decision"],
        2: ["climate risk", "climate factor", "investment decision"],
        3: ["climate consideration", "capital allocation", "strategic decision", "meeting minutes", "climate governance"],
        4: ["climate integration", "systematic consideration", "decision framework", "regular assessment"],
        5: ["fully integrated", "climate-aligned", "leading practice"],
    },
    "STR-01": {
        1: ["risk", "opportunity", "sustainability"],
        2: ["sustainability risk", "risk assessment", "opportunity identification"],
        3: ["risk register", "time horizon", "short-term", "medium-term", "long-term", "financial impact", "operational impact"],
        4: ["regular assessment", "risk monitoring", "quantified impact", "scenario"],
        5: ["comprehensive risk framework", "integrated risk", "dynamic assessment"],
    },
    "STR-02": {
        1: ["business model", "value chain"],
        2: ["impact assessment", "value chain risk", "business model impact"],
        3: ["value chain mapping", "dependency analysis", "business model assessment", "supply chain"],
        4: ["regular review", "dynamic assessment", "quantified dependency"],
        5: ["integrated value chain", "resilient business model"],
    },
    "STR-03": {
        1: ["financial", "impact", "sustainability"],
        2: ["financial impact", "cost", "revenue"],
        3: ["financial position", "cash flow", "balance sheet", "income statement", "quantified financial impact"],
        4: ["financial scenario", "stress test", "sensitivity analysis", "financial planning"],
        5: ["fully quantified", "integrated financial planning", "forward-looking financial"],
    },
    "STR-04": {
        1: ["climate", "scenario"],
        2: ["scenario analysis", "climate scenario", "1.5", "2 degree"],
        3: ["climate scenario analysis", "resilience assessment", "RCP", "SSP", "IEA", "NGFS", "transition scenario", "physical scenario"],
        4: ["multiple scenarios", "quantified impact", "strategic implication", "time horizon"],
        5: ["comprehensive scenario", "integrated planning", "dynamic scenario"],
    },
    "STR-05": {
        1: ["transition", "plan", "climate"],
        2: ["transition plan", "decarbonization", "net zero"],
        3: ["transition plan", "milestone", "target", "capital expenditure", "timeline", "roadmap"],
        4: ["progress tracking", "annual review", "board approved", "investment plan"],
        5: ["science-based", "SBTi", "verified", "comprehensive transition"],
    },
    "STR-06": {
        1: ["resilience", "strategy"],
        2: ["strategy resilience", "business resilience"],
        3: ["resilience assessment", "adaptability", "vulnerability", "stress test"],
        4: ["dynamic resilience", "regular reassessment", "adaptation plan"],
        5: ["fully resilient", "adaptive strategy"],
    },
    "RSK-01": {
        1: ["risk", "identification", "sustainability"],
        2: ["risk process", "risk identification", "environmental scan"],
        3: ["formal risk identification", "materiality assessment", "documented process", "risk methodology"],
        4: ["regular execution", "annual review", "stakeholder engagement", "comprehensive scan"],
        5: ["dynamic risk identification", "emerging risk", "leading practice"],
    },
    "RSK-02": {
        1: ["risk", "assessment", "monitor"],
        2: ["risk assessment", "risk prioritization", "risk monitoring"],
        3: ["risk register", "likelihood", "impact", "risk criteria", "escalation", "risk matrix"],
        4: ["regular monitoring", "risk dashboard", "KRI", "key risk indicator"],
        5: ["predictive risk", "advanced analytics", "continuous monitoring"],
    },
    "RSK-03": {
        1: ["risk management", "integration"],
        2: ["enterprise risk", "ERM", "integrated risk"],
        3: ["ERM framework", "sustainability integration", "risk appetite", "risk tolerance"],
        4: ["integrated reporting", "cross-functional", "unified framework"],
        5: ["fully integrated ERM", "leading practice"],
    },
    "RSK-04": {
        1: ["climate risk", "physical risk", "transition risk"],
        2: ["climate risk assessment", "physical risk assessment", "transition risk assessment"],
        3: ["physical risk", "transition risk", "acute", "chronic", "policy risk", "technology risk", "market risk", "reputation risk", "TCFD"],
        4: ["quantified climate risk", "regular assessment", "mitigation plan"],
        5: ["comprehensive climate risk", "integrated climate risk management"],
    },
    "RSK-05": {
        1: ["control", "data", "internal"],
        2: ["internal control", "data collection", "data quality"],
        3: ["data owner", "data collection procedure", "maker-checker", "audit trail", "reconciliation", "access control", "segregation of duties"],
        4: ["control testing", "regular review", "control monitoring", "automated control", "data validation"],
        5: ["integrated control framework", "continuous monitoring", "assurance-ready"],
    },
    "MET-01": {
        1: ["emission", "GHG", "scope 1", "greenhouse"],
        2: ["scope 1 emission", "direct emission", "GHG calculation"],
        3: ["scope 1", "direct emission", "fuel combustion", "process emission", "fugitive emission", "mobile source",
            "GHG protocol", "emission factor", "calculation methodology", "activity data", "tCO2", "CO2e"],
        4: ["verified", "third-party", "complete inventory", "regular review", "reconciliation", "sign-off"],
        5: ["assured", "continuous monitoring", "real-time", "leading methodology"],
    },
    "MET-02": {
        1: ["emission", "scope 2", "electricity", "energy"],
        2: ["scope 2 emission", "indirect emission", "purchased electricity"],
        3: ["scope 2", "location-based", "market-based", "grid emission factor", "electricity consumption",
            "utility", "energy consumption", "kWh", "MWh", "tCO2", "CO2e"],
        4: ["both approaches", "verified data", "reconciliation", "utility invoice", "regular review"],
        5: ["assured", "renewable energy certificate", "comprehensive scope 2"],
    },
    "MET-03": {
        1: ["scope 3", "value chain", "indirect"],
        2: ["scope 3 category", "upstream", "downstream", "value chain emission"],
        3: ["scope 3 category", "material category", "estimation methodology", "purchased goods", "transportation",
            "business travel", "employee commuting", "data source", "assumption"],
        4: ["comprehensive scope 3", "supplier engagement", "regular update", "data quality improvement"],
        5: ["verified scope 3", "science-based", "full value chain"],
    },
    "MET-04": {
        1: ["target", "reduction", "climate"],
        2: ["GHG target", "reduction target", "base year"],
        3: ["GHG reduction target", "base year", "target year", "milestone", "interim target", "absolute target", "intensity target"],
        4: ["progress tracking", "annual reporting", "on track", "SBTi"],
        5: ["science-based target", "net zero", "verified target"],
    },
    "MET-05": {
        1: ["industry", "metric", "sector"],
        2: ["industry metric", "sector metric", "SASB"],
        3: ["industry-specific", "SASB standard", "sector disclosure", "material metric"],
        4: ["comprehensive sector", "benchmarking", "peer comparison"],
        5: ["leading sector disclosure", "comprehensive SASB"],
    },
    "MET-06": {
        1: ["cross-industry", "carbon price", "climate metric"],
        2: ["transition risk amount", "physical risk amount", "carbon price"],
        3: ["internal carbon price", "capital deployment", "climate opportunity", "climate-related metric"],
        4: ["quantified cross-industry", "systematic measurement"],
        5: ["comprehensive cross-industry disclosure"],
    },
    "MET-07": {
        1: ["data", "quality", "accuracy"],
        2: ["data quality", "data accuracy", "data completeness"],
        3: ["data governance", "validation rule", "reconciliation", "error tracking", "data lineage", "completeness check", "data standard"],
        4: ["automated validation", "regular audit", "data quality KPI", "continuous improvement"],
        5: ["integrated data governance", "real-time validation", "leading data practice"],
    },
}


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def _find_excerpts(text, keywords, max_excerpts=3):
    """Find text excerpts around keyword matches."""
    excerpts = []
    text_lower = text.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        pos = text_lower.find(kw_lower)
        if pos != -1:
            start = max(0, pos - 80)
            end = min(len(text), pos + len(kw) + 80)
            snippet = text[start:end].strip()
            snippet = re.sub(r'\s+', ' ', snippet)
            if snippet and snippet not in excerpts:
                excerpts.append(f"...{snippet}...")
            if len(excerpts) >= max_excerpts:
                break
    return excerpts


def score_criterion(criterion_id, combined_text):
    """
    Score a single criterion against the combined document text.

    Returns (score, evidence_text, notes).
    """
    keywords_by_level = CRITERION_KEYWORDS.get(criterion_id, {})
    if not keywords_by_level:
        return (0, "", "No auto-assessment keywords defined for this criterion.")

    text_lower = combined_text.lower()
    best_level = 0
    all_matched = []
    all_excerpts = []

    for level in sorted(keywords_by_level.keys()):
        kws = keywords_by_level[level]
        matched = [kw for kw in kws if kw.lower() in text_lower]
        if matched:
            best_level = level
            all_matched.extend(matched)
            excerpts = _find_excerpts(combined_text, matched, max_excerpts=2)
            all_excerpts.extend(excerpts)

    if best_level == 0:
        return (0, "", "No relevant content found in uploaded documents.")

    # Find the criterion for context
    criterion = None
    for c in SSBJ_CRITERIA:
        if c["id"] == criterion_id:
            criterion = c
            break

    unique_matched = list(dict.fromkeys(all_matched))
    evidence = f"[Auto-assessed] Keywords found: {', '.join(unique_matched[:10])}"
    if all_excerpts:
        unique_excerpts = list(dict.fromkeys(all_excerpts))
        evidence += "\n\nRelevant excerpts:\n" + "\n".join(unique_excerpts[:4])

    notes = f"[Auto-assessed] Maturity level {best_level} based on document analysis."
    if criterion:
        notes += f"\nGuidance: {criterion['guidance']}"

    return (best_level, evidence, notes)


def auto_assess_all(combined_text):
    """
    Run auto-assessment on all SSBJ criteria.

    Returns dict: {criterion_id: (score, evidence, notes)}
    """
    results = {}
    for criterion in SSBJ_CRITERIA:
        cid = criterion["id"]
        score, evidence, notes = score_criterion(cid, combined_text)
        results[cid] = (score, evidence, notes)
    return results
