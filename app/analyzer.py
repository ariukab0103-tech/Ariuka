"""
Auto-Assessment Analyzer

Two modes:
1. AI-powered (Claude API): Sends document text + each criterion to Claude for
   contextual analysis with proper understanding of SSBJ requirements.
2. Keyword fallback: Simple keyword matching when no API key is configured.

Text extraction supports PDF, DOCX, XLSX, CSV, TXT.
"""

import os
import csv
import json
import logging
import re

from app.ssbj_criteria import SSBJ_CRITERIA, MATURITY_LEVELS

logger = logging.getLogger(__name__)


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
    except Exception as e:
        logger.warning(f"Failed to extract text from {filepath}: {e}")
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
# AI-powered assessment (Claude API)
# ---------------------------------------------------------------------------

def _get_anthropic_client():
    """Get Anthropic client if API key is configured."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logger.warning(f"Failed to create Anthropic client: {e}")
        return None


def _truncate_text(text, max_chars=80000):
    """Truncate text to fit within API limits while keeping meaningful content."""
    if len(text) <= max_chars:
        return text
    # Keep beginning and end (most reports have summary at start, data at end)
    half = max_chars // 2
    return text[:half] + "\n\n[... content truncated for length ...]\n\n" + text[-half:]


def ai_assess_all(combined_text):
    """
    Use Claude to assess all SSBJ criteria against the document text.

    Sends the document text + all criteria in a single call for efficiency.
    Returns dict: {criterion_id: (score, evidence, notes)}
    """
    client = _get_anthropic_client()
    if not client:
        return None

    truncated = _truncate_text(combined_text)

    # Build criteria descriptions for the prompt
    criteria_list = []
    for c in SSBJ_CRITERIA:
        criteria_list.append(
            f"- {c['id']} ({c['pillar']} / {c['category']}): {c['requirement']}\n"
            f"  Obligation: {c['obligation']} | LA Scope: {c['la_scope']}\n"
            f"  Guidance: {c['guidance']}"
        )
    criteria_text = "\n\n".join(criteria_list)

    maturity_desc = "\n".join(
        f"  {level}: {info['label']} - {info['description']}"
        for level, info in MATURITY_LEVELS.items()
    )

    prompt = f"""You are an expert sustainability auditor specializing in Japanese SSBJ (Sustainability Standards Board of Japan) standards, IFRS S1/S2, and limited assurance under ISAE 3000/3410/ISSA 5000.

## YOUR DEEP EXPERTISE (use this knowledge when scoring)

### SSBJ Standards
- **SSBJ No.1** (General Requirements) aligned with IFRS S1 — requires disclosure of sustainability-related risks and opportunities affecting cash flows, access to finance, or cost of capital. 4 core pillars: Governance, Strategy, Risk Management, Metrics & Targets.
- **SSBJ No.2** (Climate-related Disclosures) aligned with IFRS S2 — specific requirements for climate governance, strategy, risk management, metrics & targets. GHG emissions (Scope 1, 2, 3), climate scenario analysis, transition plans, industry-specific metrics (SASB-based).

### Mandatory vs Recommended vs Interpretive
**Mandatory (SHALL / しなければならない):**
- Governance oversight body disclosure, management role disclosure
- Sustainability risks and opportunities identification
- Financial effects on financial position, performance, cash flows
- GHG emissions (Scope 1, Scope 2 mandatory; Scope 3 with relief period)
- Climate scenario analysis (with proportionality)
- GHG reduction targets with base year, scope, and timeline

**Recommended (SHOULD / すべきである):**
- Skills and competencies of governance body
- Climate consideration in strategic decisions
- Value chain impact analysis
- Industry-specific and cross-industry metrics beyond minimum

**Interpretive (entity discretion):**
- Level of detail in scenario analysis
- Scope 3 methodology selection
- Financial impact quantification approach
- Transition plan detail level

### Limited Assurance Requirements (critical for scoring)
**Standards:** ISAE 3000 (Revised), ISAE 3410, ISSA 5000
**Initial Scope:** Scope 1 & 2 GHG emissions ONLY (NOT Scope 3, NOT qualitative disclosures)
**What limited assurance means:** Negative form conclusion ("nothing has come to our attention..."), primarily analytical procedures and inquiry.

**Essential internal controls for limited assurance (Scope 1 & 2):**
1. Organizational boundary definition — clear documentation of included entities
2. Emission source inventory — complete list of all sources by scope
3. Calculation methodology — documented (GHG Protocol, ISO 14064)
4. Activity data controls — procedures for collecting/verifying fuel, electricity data
5. Emission factor management — documented source and version
6. Maker-checker review — independent review of calculations
7. Audit trail — trace from disclosed numbers to source data
8. Data reconciliation — reconcile to utility bills, fuel invoices, meter readings
9. Error tracking — log of errors found and corrections
10. Management sign-off — formal approval of final GHG figures
11. Segregation of duties — separate data collection, calculation, review, approval
12. Access controls — restricted access to calculation systems
13. Documentation — all policies, procedures, assumptions documented

### GHG Accounting
**Scope 1 (Direct):** Stationary combustion, mobile combustion, process emissions, fugitive emissions. Calculation: Activity data × Emission factor = tCO2e
**Scope 2 (Energy indirect):** Location-based AND market-based methods BOTH required by SSBJ. Data: utility invoices, meter readings.
**Scope 3 (Value chain):** 15 categories, material categories must be identified. Relief period in first year.

### Japanese Regulatory Timeline
- Phase 1 (FY March 2027): Prime Market, ≥¥3T — mandatory
- Phase 2 (FY March 2028): Prime Market, ≥¥1T — mandatory
- Phase 3 (FY March 2029): Prime Market, ≥¥700B — mandatory
- Limited assurance starts ONE YEAR AFTER mandatory disclosure for each phase

## TASK
Analyze the following documents against each SSBJ criterion and assess the organization's maturity level.

MATURITY SCALE:
{maturity_desc}

SCORING GUIDELINES (be strict — apply your SSBJ expertise):
- Score 0: No evidence at all in the documents
- Score 1: Topic is mentioned but no formal process or structure
- Score 2: Some processes exist but incomplete or inconsistent documentation
- Score 3: Formal documented processes with clear ownership (MINIMUM for limited assurance readiness). For GHG criteria, must show: documented methodology, activity data sources, emission factors, calculation procedures, and review process
- Score 4: Monitored, measured processes with regular review cycles. Evidence of maker-checker, reconciliation, management sign-off
- Score 5: Continuous improvement, leading practice, fully assurance-ready. Complete audit trail, segregation of duties, error tracking

SSBJ CRITERIA TO ASSESS:
{criteria_text}

DOCUMENTS TO ANALYZE:
{truncated}

INSTRUCTIONS:
For each criterion, provide your assessment as a JSON array. Each element should have:
- "id": the criterion ID (e.g., "GOV-01")
- "score": integer 0-5
- "evidence": specific quotes or references from the documents that support your score (2-3 sentences)
- "notes": what the organization needs to improve to reach score 3+ for limited assurance readiness (2-3 sentences)

Be strict and objective — apply your deep SSBJ/ISSB/limited assurance expertise:
- Only give high scores when you see clear, specific evidence
- If a document mentions a topic vaguely without specifics, that's score 1-2, not 3+
- For score 3+, you need to see formal processes, specific methodologies, named responsibilities, or concrete data
- For GHG metrics (MET-01, MET-02): score 3+ requires documented calculation methodology, identified emission sources, activity data sources, emission factors with references, and review process
- For internal controls (RSK-05): score 3+ requires at least maker-checker, audit trail, data reconciliation, and segregation of duties
- For governance (GOV-01, GOV-02): score 3+ requires formal board/committee mandate with documented terms of reference
- For mandatory (SHALL) items: assess against SSBJ/IFRS S1/S2 mandatory disclosure requirements specifically
- For limited assurance scope items: assess readiness for ISAE 3000/3410 procedures (can an auditor trace from disclosure to source data?)

Respond ONLY with valid JSON array, no other text. Example format:
[
  {{"id": "GOV-01", "score": 3, "evidence": "The report states...", "notes": "To improve..."}},
  ...
]"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse the response
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle potential markdown code blocks)
        if response_text.startswith("```"):
            # Remove markdown code block markers
            response_text = re.sub(r'^```(?:json)?\s*\n?', '', response_text)
            response_text = re.sub(r'\n?```\s*$', '', response_text)

        results_list = json.loads(response_text)

        results = {}
        for item in results_list:
            cid = item.get("id", "")
            score = int(item.get("score", 0))
            score = max(0, min(5, score))  # Clamp to 0-5
            evidence = f"[AI Assessment] {item.get('evidence', '')}"
            notes = item.get("notes", "")
            results[cid] = (score, evidence, notes)

        return results

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        raise RuntimeError(f"AI returned invalid response. Please try again.") from e
    except Exception as e:
        logger.error(f"AI assessment failed: {e}")
        raise RuntimeError(str(e)) from e


# ---------------------------------------------------------------------------
# Keyword-based fallback assessment
# ---------------------------------------------------------------------------

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


def keyword_assess_all(combined_text):
    """
    Keyword-based fallback assessment for all SSBJ criteria.

    Returns dict: {criterion_id: (score, evidence, notes)}
    """
    results = {}
    text_lower = combined_text.lower()

    for criterion in SSBJ_CRITERIA:
        cid = criterion["id"]
        keywords_by_level = CRITERION_KEYWORDS.get(cid, {})

        if not keywords_by_level:
            results[cid] = (0, "", "No assessment keywords defined for this criterion.")
            continue

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
            results[cid] = (0, "", "No relevant content found in uploaded documents.")
            continue

        unique_matched = list(dict.fromkeys(all_matched))
        evidence = f"[Keyword match] Keywords found: {', '.join(unique_matched[:10])}"
        if all_excerpts:
            unique_excerpts = list(dict.fromkeys(all_excerpts))
            evidence += "\n\nRelevant excerpts:\n" + "\n".join(unique_excerpts[:4])

        notes = f"Maturity level {best_level} based on keyword matching (not AI analysis)."
        notes += f"\nGuidance: {criterion['guidance']}"

        results[cid] = (best_level, evidence, notes)

    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def auto_assess_all(combined_text):
    """
    Run auto-assessment on all SSBJ criteria.

    Tries AI-powered assessment first (if ANTHROPIC_API_KEY is set).
    Falls back to keyword matching ONLY if no API key is configured.
    If AI fails (errors), raises the error so the user sees what went wrong.

    Returns (results_dict, method_used, error_message).
    - results_dict: {criterion_id: (score, evidence, notes)}
    - method_used: "ai" or "keyword"
    - error_message: None if success, or string describing AI failure
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if api_key:
        # API key is set — try AI assessment, report errors clearly
        try:
            ai_results = ai_assess_all(combined_text)
            if ai_results:
                return ai_results, "ai", None
        except RuntimeError as e:
            error_msg = str(e)
            logger.warning(f"AI assessment failed, falling back to keyword: {error_msg}")
            # Fall back to keyword but tell the user AI failed
            keyword_results = keyword_assess_all(combined_text)
            return keyword_results, "keyword", error_msg

    # No API key — use keyword matching
    keyword_results = keyword_assess_all(combined_text)
    return keyword_results, "keyword", None
