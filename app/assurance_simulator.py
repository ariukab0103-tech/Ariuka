"""
C3: Assurance Readiness Simulator

Interactive mock audit walkthrough based on ISSA 5000 limited assurance procedures.
For each in-scope criterion, generates:
- What the auditor will ask (inquiry)
- What evidence you need to show (inspection/documentation)
- Analytical procedures the auditor will perform
- Your current readiness status based on scores

ISSA 5000 Limited Assurance Procedures:
1. Inquiry — Questions to management and personnel
2. Analytical procedures — Data comparison, trend analysis, reasonableness checks
3. Inspection — Review of documents and records
4. Observation — Watch processes in action (noted but not simulated)
5. Recalculation — Verify mathematical accuracy
"""

from app.ssbj_criteria import SSBJ_CRITERIA, LIMITED_ASSURANCE_CRITERIA

# ---------------------------------------------------------------------------
# Mock audit questions for SSBJ in-scope criteria
# Each entry maps to ISSA 5000 procedure types
# ---------------------------------------------------------------------------
_SSBJ_AUDIT_ITEMS = {
    "GOV-01": {
        "auditor_intro": "The auditor will verify that a governance body with sustainability oversight actually exists and functions.",
        "inquiry": [
            "Which board committee or individual has formal responsibility for sustainability oversight?",
            "When was this mandate established and how often does the committee meet?",
            "Can you describe the reporting line from sustainability management to the board?",
        ],
        "documents_needed": [
            "Board committee charter or terms of reference mentioning sustainability",
            "Board resolution establishing sustainability oversight",
            "Organizational chart showing governance structure",
        ],
        "analytical": "The auditor will compare your governance structure against IFRS S1 para 26 requirements and check for consistency with your corporate governance report filed with TSE.",
        "red_flags": [
            "No formal committee charter mentioning sustainability",
            "Sustainability oversight added informally without board resolution",
            "Committee has not met in the past 12 months",
        ],
    },
    "GOV-02": {
        "auditor_intro": "The auditor will verify that governance responsibilities are formally documented in policies.",
        "inquiry": [
            "Where in your governance policies is sustainability oversight explicitly referenced?",
            "When was the policy last reviewed and approved by the board?",
            "How do you ensure the policy is communicated to relevant personnel?",
        ],
        "documents_needed": [
            "Corporate governance policy or board charter with sustainability language",
            "Board approval minutes for the policy",
            "Evidence of policy communication (e.g., intranet publication, training)",
        ],
        "analytical": "The auditor will cross-reference your governance policy with IFRS S1 requirements and verify the language matches your actual governance practices.",
        "red_flags": [
            "Generic sustainability language with no specific responsibilities defined",
            "Policy exists but was never formally approved",
            "Policy references outdated standards (e.g., TCFD without SSBJ/ISSB update)",
        ],
    },
    "GOV-04": {
        "auditor_intro": "The auditor will verify that management actively monitors sustainability risks and reports to the board.",
        "inquiry": [
            "Who in management is specifically responsible for sustainability data and reporting?",
            "How does management report sustainability matters to the governance body?",
            "How frequently are sustainability reports provided to the board?",
            "What controls and procedures does management use to monitor sustainability risks?",
        ],
        "documents_needed": [
            "Management role descriptions with sustainability responsibilities",
            "RACI matrix or responsibility assignment document",
            "Samples of management reports to the board on sustainability",
            "Meeting agendas and minutes showing sustainability discussions",
        ],
        "analytical": "The auditor will verify that management reporting is regular and substantive — not just a one-time mention. They will check frequency, depth, and whether the board took any action based on reports.",
        "red_flags": [
            "No named individual responsible for sustainability data",
            "Sustainability appears in board agenda only once per year",
            "Management reports are generic with no entity-specific data",
        ],
    },
    "GOV-05": {
        "auditor_intro": "The auditor will verify that climate risks are actively considered in management decision-making.",
        "inquiry": [
            "Can you give a specific example of a business decision where climate risk was considered?",
            "How are climate factors incorporated into capital investment approvals?",
            "Is there an internal carbon price or climate screening in your investment process?",
        ],
        "documents_needed": [
            "Investment approval template or checklist showing climate criteria",
            "Meeting minutes where climate was discussed in a business decision",
            "Capital expenditure review documents with climate assessment",
        ],
        "analytical": "The auditor will look for evidence that climate integration is systematic (embedded in processes) rather than ad-hoc (mentioned once). They will sample recent investment decisions.",
        "red_flags": [
            "No evidence of climate in any investment decision",
            "Climate mentioned only in sustainability report, not in actual decision processes",
            "Climate assessment exists but is always marked 'not applicable'",
        ],
    },
    "RSK-01": {
        "auditor_intro": "The auditor will verify you have a documented, repeatable process for identifying sustainability risks.",
        "inquiry": [
            "Describe your process for identifying sustainability-related risks and opportunities.",
            "Who participates in the risk identification process?",
            "How often is risk identification performed?",
            "What sources of information do you use to identify emerging risks?",
        ],
        "documents_needed": [
            "Risk identification methodology document",
            "Workshop attendance records or participant list",
            "Risk register output from the most recent identification exercise",
            "Evidence of external scanning (industry reports, regulatory updates reviewed)",
        ],
        "analytical": "The auditor will assess whether the methodology is documented and consistently applied. They will compare the risk register against known industry risks to test completeness.",
        "red_flags": [
            "No written methodology — risks identified ad-hoc",
            "Risk register has not been updated in over 12 months",
            "Obvious industry risks (e.g., physical climate risk for coastal facilities) missing",
        ],
    },
    "RSK-02": {
        "auditor_intro": "The auditor will verify you have criteria for assessing and prioritizing sustainability risks.",
        "inquiry": [
            "What criteria do you use to assess likelihood and impact of sustainability risks?",
            "How do you prioritize sustainability risks relative to other business risks?",
            "Who is assigned as owner for each identified risk?",
            "How do you monitor risks between assessment cycles?",
        ],
        "documents_needed": [
            "Risk assessment criteria (likelihood/impact matrix)",
            "Risk register with scores and risk owners",
            "Evidence of monitoring activities (status updates, KRIs)",
        ],
        "analytical": "The auditor will test whether risk scores are consistent with the criteria. They may challenge outlier scores (e.g., a high-carbon company rating transition risk as 'low').",
        "red_flags": [
            "No documented assessment criteria — scores assigned subjectively",
            "All risks rated the same (no differentiation)",
            "No risk owners assigned",
        ],
    },
    "RSK-03": {
        "auditor_intro": "The auditor will verify sustainability risks are integrated into your enterprise risk management, not siloed.",
        "inquiry": [
            "How does your sustainability risk register connect to the enterprise risk register?",
            "Is sustainability reported alongside other risk categories to the board?",
            "Does your ERM policy explicitly reference sustainability risks?",
        ],
        "documents_needed": [
            "ERM policy or framework document showing sustainability integration",
            "Combined risk report to board including sustainability risks",
            "Evidence that sustainability risks are discussed in ERM committee meetings",
        ],
        "analytical": "The auditor will compare the sustainability risk register with the ERM register. They expect to see the same risks in both, with consistent scoring.",
        "red_flags": [
            "Sustainability risks managed in separate silo with no ERM linkage",
            "ERM policy makes no mention of sustainability or climate",
            "Board sees sustainability risks in a separate report from other risks",
        ],
    },
    "RSK-04": {
        "auditor_intro": "The auditor will verify you have identified and categorized both physical and transition climate risks.",
        "inquiry": [
            "What physical climate risks (acute and chronic) have you identified?",
            "What transition risks (policy, technology, market, reputation) apply to your business?",
            "How did you assess each risk — qualitative, semi-quantitative, or quantitative?",
            "What is the geographic scope of your physical risk assessment?",
        ],
        "documents_needed": [
            "Climate risk assessment report with physical and transition categories",
            "Physical risk screening results (if available — e.g., flood maps, heat stress data)",
            "Transition risk analysis (policy landscape, technology disruption assessment)",
        ],
        "analytical": "The auditor will check that both physical AND transition risks are covered. They will assess whether the geographic scope matches your operational footprint.",
        "red_flags": [
            "Only transition risks identified — physical risks ignored",
            "Physical risk assessment limited to headquarters, not covering all facilities",
            "No distinction between acute (typhoons, floods) and chronic (sea level, heat) risks",
        ],
    },
    "RSK-05": {
        "auditor_intro": "The auditor will examine your internal controls over sustainability data — this is THE critical item for limited assurance.",
        "inquiry": [
            "Who is responsible for collecting, calculating, and reporting GHG data?",
            "Describe your maker-checker process for GHG calculations.",
            "How do you ensure all emission sources are captured (completeness)?",
            "What happens when an error is discovered in reported data?",
            "How are source documents (invoices, meter readings) retained?",
        ],
        "documents_needed": [
            "Data collection procedures document (step-by-step)",
            "RACI matrix for GHG reporting roles",
            "Sample calculation with reviewer sign-off",
            "Error log or correction records",
            "Source document samples (fuel invoices, electricity bills)",
            "Reconciliation between source data and reported figures",
        ],
        "analytical": "The auditor will select sample emission sources and trace data from source documents through calculations to the final reported figure (walkthrough test). They will recalculate selected items.",
        "red_flags": [
            "One person does everything — no segregation of duties",
            "No written procedures — calculation done 'from experience'",
            "Source documents not retained or organized",
            "No reconciliation between activity data and financial records",
            "Errors found but no correction log maintained",
        ],
    },
    "MET-01": {
        "auditor_intro": "The auditor will verify your Scope 1 emissions calculation — methodology, data, and completeness.",
        "inquiry": [
            "What methodology do you use for Scope 1 calculations (GHG Protocol, etc.)?",
            "How do you identify all direct emission sources?",
            "What emission factors do you use and where do they come from?",
            "How do you handle estimation when measured data is unavailable?",
        ],
        "documents_needed": [
            "Scope 1 calculation methodology document",
            "Complete list of emission sources (fuel combustion, process, fugitive, mobile)",
            "Emission factors with source references and publication dates",
            "Activity data with source documents (fuel invoices, meter readings)",
            "Calculation spreadsheet with reviewer sign-off",
        ],
        "analytical": "The auditor will: (1) Test completeness by comparing emission sources to your facility/asset register, (2) Recalculate selected items, (3) Compare year-over-year and to industry benchmarks for reasonableness, (4) Verify emission factors against published sources.",
        "red_flags": [
            "Emission sources list does not match facility register (missing sites)",
            "Emission factors are outdated or from unrecognized sources",
            "Significant year-over-year change with no explanation",
            "No source documents for activity data (estimates only)",
        ],
    },
    "MET-02": {
        "auditor_intro": "The auditor will verify your Scope 2 emissions — both location-based and market-based methods.",
        "inquiry": [
            "Do you report both location-based and market-based Scope 2?",
            "Which grid emission factors do you use for location-based calculation?",
            "Do you have any contractual instruments (green certificates, PPAs) for market-based?",
            "How do you ensure all purchased energy is captured?",
        ],
        "documents_needed": [
            "Scope 2 calculation for both methods (or location-based only if Year 1)",
            "Grid emission factors with source reference (MOE Japan area-specific)",
            "Electricity bills for all facilities",
            "Green energy certificates or PPA contracts (if applicable)",
            "Reconciliation of energy consumption to financial records",
        ],
        "analytical": "The auditor will: (1) Cross-check electricity consumption against utility invoices, (2) Verify grid emission factors match the correct geographic area, (3) Test that all facilities are included by comparing to your facility list.",
        "red_flags": [
            "Only reporting one method (SSBJ requires both eventually)",
            "Using national average emission factor instead of area-specific",
            "Some facility electricity not captured (e.g., leased space)",
            "Market-based claims without valid contractual instruments",
        ],
    },
    "MET-07": {
        "auditor_intro": "The auditor will assess the quality and reliability of your sustainability data processes.",
        "inquiry": [
            "How do you validate data at the point of entry?",
            "What reconciliation procedures do you perform before reporting?",
            "How do you track and correct errors?",
            "Can you trace any reported figure back to its source document?",
        ],
        "documents_needed": [
            "Data flow diagram (source → collection → calculation → reporting)",
            "Validation rules or reasonableness checks documentation",
            "Reconciliation checklist or evidence",
            "Error log with correction records",
            "Data lineage documentation for at least one metric",
        ],
        "analytical": "The auditor will test the data trail end-to-end: pick a reported number and trace it backwards through each step to the source document. They will also check for anomalies in the data.",
        "red_flags": [
            "No data flow diagram — unclear how data moves through the system",
            "No validation rules — data accepted without checks",
            "Cannot trace a reported figure back to source within a reasonable time",
            "No error correction process — mistakes discovered but not logged",
        ],
    },
}

# ---------------------------------------------------------------------------
# Mock audit questions for LA-specific criteria (internal controls)
# ---------------------------------------------------------------------------
_LA_AUDIT_ITEMS = {
    "LA-01": {
        "auditor_intro": "The auditor will verify your organizational boundary is clearly defined and appropriate.",
        "inquiry": [
            "What consolidation approach do you use — operational control or equity share?",
            "Which entities are included and excluded from your GHG boundary?",
            "Does your GHG boundary align with your financial reporting boundary?",
        ],
        "documents_needed": [
            "Organizational boundary document listing all included/excluded entities",
            "Justification for any exclusions",
            "Comparison to financial reporting consolidation scope",
        ],
        "analytical": "The auditor will compare your GHG boundary to your list of subsidiaries in the annual securities report (有価証券報告書) to identify any gaps.",
        "red_flags": [
            "Boundary not documented — just assumed to be 'the company'",
            "Significant subsidiaries excluded without justification",
            "Boundary inconsistent with financial reporting scope",
        ],
    },
    "LA-02": {
        "auditor_intro": "The auditor will verify you have identified ALL Scope 1 and Scope 2 emission sources.",
        "inquiry": [
            "How do you ensure your emission source inventory is complete?",
            "When was the inventory last reviewed for completeness?",
            "How do you handle new facilities, equipment changes, or divestments?",
        ],
        "documents_needed": [
            "Complete emission source inventory list",
            "Cross-reference to asset register or facility list",
            "Evidence of annual completeness review",
        ],
        "analytical": "The auditor will compare your source inventory to your fixed asset register and facility list. Missing sources indicate a completeness gap.",
        "red_flags": [
            "Inventory not cross-checked against asset register",
            "Refrigerant/fugitive emissions not included",
            "Company vehicles not included in Scope 1",
        ],
    },
    "LA-03": {
        "auditor_intro": "The auditor will examine your calculation methodology and verify it is appropriate.",
        "inquiry": [
            "Is your calculation methodology documented in a manual or procedure?",
            "Which GWP values do you use (IPCC AR5 or AR6)?",
            "How do you select and update emission factors?",
        ],
        "documents_needed": [
            "Written calculation manual or methodology document",
            "Emission factor database with sources and version dates",
            "GWP values used with IPCC source reference",
        ],
        "analytical": "The auditor will verify emission factors against published sources and check that GWP values are consistently applied.",
        "red_flags": [
            "No written methodology — calculations done differently each year",
            "Emission factors from unknown or outdated sources",
            "Inconsistent GWP values (mixing AR4 and AR5)",
        ],
    },
    "LA-05": {
        "auditor_intro": "The auditor will verify that an independent review of calculations occurs before disclosure.",
        "inquiry": [
            "Who reviews GHG calculations before they are finalized?",
            "Is the reviewer independent from the preparer (segregation of duties)?",
            "How is the review documented — is there a sign-off?",
        ],
        "documents_needed": [
            "Calculation file with reviewer sign-off and date",
            "Evidence that reviewer is different from preparer",
            "Review checklist or comments (if any)",
        ],
        "analytical": "The auditor will check the sign-off trail and verify the reviewer has appropriate qualifications. Same person preparing and reviewing is a control failure.",
        "red_flags": [
            "Same person prepares and reviews (no maker-checker)",
            "Review sign-off exists but reviewer cannot explain what they checked",
            "No date on review — unclear when it was performed",
        ],
    },
    "LA-07": {
        "auditor_intro": "The auditor will test whether your documentation is sufficient to reconstruct reported figures.",
        "inquiry": [
            "How long do you retain source documents?",
            "Where are calculation files and supporting documents stored?",
            "Can you show me the audit trail for a specific reported number?",
        ],
        "documents_needed": [
            "Document retention policy",
            "Organized filing system (physical or digital)",
            "Ability to produce source documents for any reported figure on request",
        ],
        "analytical": "The auditor will select a random emission source and ask you to produce the complete trail: source document → activity data → calculation → reported figure. Response time matters.",
        "red_flags": [
            "Source documents stored on personal drives with no backup",
            "Cannot locate documents for prior-year figures",
            "No version control — unclear which spreadsheet version was used for reporting",
        ],
    },
    "LA-10": {
        "auditor_intro": "The auditor will request a formal management representation letter — this is standard under ISSA 5000.",
        "inquiry": [
            "Is management prepared to sign a representation letter confirming the completeness and accuracy of GHG data?",
            "Who has the authority to sign management representations?",
            "Are you aware of any uncorrected misstatements or omissions?",
        ],
        "documents_needed": [
            "Draft management representation letter template",
            "Identification of appropriate signatory (CFO, CEO, or equivalent)",
        ],
        "analytical": "The auditor will provide a template or request specific confirmations. Refusal to sign or extensive qualifications is a significant issue.",
        "red_flags": [
            "No one in management is willing to sign representations",
            "Management cannot confirm completeness of emission sources",
            "Known errors exist that have not been corrected",
        ],
    },
}


def _score_to_readiness(score):
    """Convert maturity score to readiness assessment."""
    if score is None:
        return {"level": "unknown", "label": "Not Assessed", "badge": "secondary",
                "message": "This criterion has not been scored. Complete the assessment first."}
    if score >= 4:
        return {"level": "ready", "label": "Assurance Ready", "badge": "success",
                "message": "Your processes appear mature enough for limited assurance. Focus on maintaining documentation."}
    if score == 3:
        return {"level": "borderline", "label": "Borderline", "badge": "warning",
                "message": "Minimum threshold met, but auditor may find gaps in documentation or consistency. Review the red flags below."}
    if score == 2:
        return {"level": "at_risk", "label": "At Risk", "badge": "danger",
                "message": "Below threshold. Basic processes exist but are likely insufficient for assurance. Prioritize the documents needed."}
    return {"level": "not_ready", "label": "Not Ready", "badge": "danger",
            "message": "Significant work needed. Start with the minimum documents listed and establish basic processes."}


def generate_simulation(assessment, responses):
    """
    Generate a mock audit walkthrough for all in-scope items.

    Returns:
        dict with:
        - ssbj_items: list of in-scope SSBJ criteria with audit simulation
        - la_items: list of LA criteria with audit simulation
        - readiness_summary: overall readiness statistics
    """
    ssbj_items = []
    la_items = []
    readiness_counts = {"ready": 0, "borderline": 0, "at_risk": 0, "not_ready": 0, "unknown": 0}

    # SSBJ in-scope criteria
    for c in SSBJ_CRITERIA:
        if c["la_scope"] != "in_scope":
            continue
        if c["id"] not in _SSBJ_AUDIT_ITEMS:
            continue

        audit = _SSBJ_AUDIT_ITEMS[c["id"]]
        resp = responses.get(c["id"])
        score = resp.score if resp and resp.score is not None else None
        evidence = (resp.evidence or "") if resp else ""
        readiness = _score_to_readiness(score)
        readiness_counts[readiness["level"]] += 1

        # Check evidence against documents needed
        evidence_lower = evidence.lower()
        doc_status = []
        for doc in audit["documents_needed"]:
            # Simple keyword matching to indicate if evidence mentions relevant docs
            keywords = [w.lower() for w in doc.split() if len(w) > 4]
            has_mention = any(kw in evidence_lower for kw in keywords[:3])
            doc_status.append({"document": doc, "mentioned": has_mention})

        ssbj_items.append({
            "id": c["id"],
            "pillar": c["pillar"],
            "category": c["category"],
            "requirement": c["requirement"],
            "score": score,
            "evidence": evidence,
            "readiness": readiness,
            "auditor_intro": audit["auditor_intro"],
            "inquiry": audit["inquiry"],
            "documents_needed": doc_status,
            "analytical": audit["analytical"],
            "red_flags": audit["red_flags"],
            "internal_controls": c.get("internal_controls", ""),
        })

    # LA-specific criteria (selected key items)
    for c in LIMITED_ASSURANCE_CRITERIA:
        if c["id"] not in _LA_AUDIT_ITEMS:
            continue
        audit = _LA_AUDIT_ITEMS[c["id"]]
        la_items.append({
            "id": c["id"],
            "category": c["category"],
            "requirement": c["requirement"],
            "obligation": c["obligation"],
            "auditor_intro": audit["auditor_intro"],
            "inquiry": audit["inquiry"],
            "documents_needed": [{"document": d, "mentioned": False} for d in audit["documents_needed"]],
            "analytical": audit["analytical"],
            "red_flags": audit["red_flags"],
        })

    total = sum(readiness_counts.values())
    readiness_summary = {
        "total": total,
        "ready": readiness_counts["ready"],
        "borderline": readiness_counts["borderline"],
        "at_risk": readiness_counts["at_risk"],
        "not_ready": readiness_counts["not_ready"],
        "unknown": readiness_counts["unknown"],
        "ready_pct": round(readiness_counts["ready"] / total * 100) if total else 0,
        "pass_pct": round((readiness_counts["ready"] + readiness_counts["borderline"]) / total * 100) if total else 0,
    }

    return {
        "ssbj_items": ssbj_items,
        "la_items": la_items,
        "readiness_summary": readiness_summary,
    }
