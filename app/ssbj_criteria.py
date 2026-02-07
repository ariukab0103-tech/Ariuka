"""
SSBJ Gap Analysis Criteria

Based on:
- SSBJ Application Standard (適用基準)
- SSBJ Standard No.1 - General Disclosures (一般開示基準) aligned with IFRS S1
- SSBJ Standard No.2 - Climate-related Disclosures (気候関連開示基準) aligned with IFRS S2

Each criterion has:
- id: Unique identifier
- pillar: One of Governance, Strategy, Risk Management, Metrics & Targets
- category: Sub-category within the pillar
- standard: Which SSBJ standard it falls under
- requirement: Description of the requirement
- obligation: "mandatory" (SHALL - required by SSBJ), "recommended" (SHOULD - expected
  practice), or "interpretive" (entity judgment on how to comply)
- la_scope: Whether this item is in scope for initial limited assurance
  - "in_scope" = directly subject to limited assurance (first 2 years: Scope 1 & 2,
    Governance, and Risk Management per FSA July 2025 roadmap)
  - "supporting" = needed to support assurance-ready disclosures
  - "not_in_initial_scope" = not in initial limited assurance scope (may expand from year 3)
- la_priority: "essential" / "important" / "nice_to_have" for minimum viable compliance
- internal_controls: Specific internal controls needed for limited assurance (if applicable)
- guidance: Guidance on what good practice looks like
- assurance_focus: What a limited assurance reviewer would look for

Sources:
- FSA Roadmap on Sustainability Disclosure and Assurance (July 2025, updated Nov 2025)
- FSA Working Group Report (December 2025)
- SSBJ Standards (March 2025)
- ISSA 5000 (IAASB, approved Sep 2024, published Nov 2024, effective Dec 2026)
- ISAE 3000 / ISAE 3410 (legacy standards, being replaced by ISSA 5000)

Limited Assurance Scope (FSA Roadmap, July 2025):
- First 2 years: Scope 1 & 2 GHG emissions, Governance, and Risk Management
- From 3rd year onwards: scope expansion under consideration (full SSBJ disclosures)
- Mandatory assurance starts one year AFTER mandatory disclosure
- Assurance level: limited assurance only (reasonable assurance NOT being considered)
- Assurance standard: ISSA 5000 (JICPA drafting aligned domestic practice guideline)
- Assurance providers: registration system under discussion (not limited to audit firms)
"""

MATURITY_LEVELS = {
    0: {"label": "Not Started", "description": "No action taken on this requirement."},
    1: {
        "label": "Initial / Ad-hoc",
        "description": "Some awareness but no formal processes. Activities are ad-hoc and reactive.",
    },
    2: {
        "label": "Developing",
        "description": "Basic processes exist but are inconsistent. Some documentation in place.",
    },
    3: {
        "label": "Defined",
        "description": "Formal processes documented and consistently applied. Clear ownership assigned.",
    },
    4: {
        "label": "Managed",
        "description": "Processes are monitored and measured. Regular review and improvement cycles.",
    },
    5: {
        "label": "Optimized",
        "description": "Continuous improvement embedded. Leading practice with robust controls and assurance-ready.",
    },
}

# Obligation labels for display
OBLIGATION_LABELS = {
    "mandatory": {"label": "Mandatory (SHALL)", "badge": "danger", "description": "Required by SSBJ standards. Entity shall disclose this information."},
    "recommended": {"label": "Recommended (SHOULD)", "badge": "warning", "description": "Expected practice per SSBJ. Not strictly required but strongly expected."},
    "interpretive": {"label": "Interpretive", "badge": "secondary", "description": "Entity has discretion on how and whether to disclose based on materiality and circumstances."},
}

LA_SCOPE_LABELS = {
    "in_scope": {"label": "In LA Scope", "badge": "danger", "description": "Directly subject to initial limited assurance (Scope 1 & 2 and supporting controls)."},
    "supporting": {"label": "LA Supporting", "badge": "warning", "description": "Supports assurance readiness but not directly assured in initial phase."},
    "not_in_initial_scope": {"label": "Not in Initial LA", "badge": "secondary", "description": "Not in initial limited assurance scope. May be added in future phases."},
}

LA_PRIORITY_LABELS = {
    "essential": {"label": "Essential", "badge": "danger", "description": "Must have for minimum limited assurance readiness."},
    "important": {"label": "Important", "badge": "warning", "description": "Should have for robust compliance."},
    "nice_to_have": {"label": "Nice to Have", "badge": "info", "description": "Enhances quality but not strictly needed for minimum compliance."},
}


SSBJ_CRITERIA = [
    # =========================================================================
    # GOVERNANCE
    # =========================================================================
    {
        "id": "GOV-01",
        "pillar": "Governance",
        "category": "Board Oversight",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Disclose the governance body(ies) or individual(s) responsible for oversight of sustainability-related risks and opportunities.",
        "internal_controls": "",
        "guidance": "Identify specific board committees or members with sustainability oversight. Document their mandate, authority, and reporting lines.",
        "assurance_focus": "Evidence of formal board mandate, committee terms of reference, and documented oversight activities.",
        "minimum_action": "Designate one existing board committee (e.g., Risk Committee) as responsible for sustainability oversight. Add one line to their terms of reference: 'oversight of sustainability-related risks and opportunities.' Minute this decision.",
        "best_practice": "Dedicated Sustainability Committee with named chair, quarterly meetings, formal terms of reference, direct reporting to full board, and documented agenda items. Peers like Toyota and Sony have standalone ESG committees with published charters.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/", "label": "IFRS S1 Standard", "title": "IFRS S1 General Requirements for Sustainability-related Disclosures", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.jpx.co.jp/english/equities/listing/cg/tvdivq0000008jdy-att/nlsgeu000006gevo.pdf", "label": "JPX CG Code", "title": "Japan Corporate Governance Code - ESG Oversight", "type": "compliance", "for_scores": [0, 1, 2]},
            {"url": "https://www.wbcsd.org/Programs/Redefining-Value/ISSB/Resources/Preparing-for-ISSB", "label": "WBCSD Getting Started", "title": "WBCSD Guide - How to Set Up Board Sustainability Oversight", "type": "compliance", "for_scores": [0, 1]},
            {"url": "https://global.toyota/en/sustainability/esg/governance/", "label": "Toyota ESG Governance", "title": "Toyota ESG Committee Structure (Peer Example)", "type": "best_practice", "for_scores": [3, 4, 5]},
            {"url": "https://www.diligent.com/resources/blog/esg-board-oversight", "label": "ESG Board Best Practice", "title": "Leading Practices in Board ESG Oversight", "type": "best_practice", "for_scores": [4, 5]},
        ],
    },
    {
        "id": "GOV-02",
        "pillar": "Governance",
        "category": "Board Oversight",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Describe how the governance body's responsibilities are reflected in terms of reference, board mandates, and related policies.",
        "internal_controls": "",
        "guidance": "Ensure board charters and corporate governance policies explicitly reference sustainability oversight.",
        "assurance_focus": "Documented policies and terms of reference that explicitly include sustainability.",
        "minimum_action": "Add sustainability oversight language to existing board committee charter or corporate governance policy. One paragraph is sufficient. Have the board formally approve the revised document.",
        "best_practice": "Standalone sustainability governance policy linked to corporate governance code, annual policy review cycle, published in integrated report. Leading companies cross-reference SSBJ requirements in their governance framework.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/", "label": "IFRS S1 Standard", "title": "IFRS S1 Governance Disclosure Requirements", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.jpx.co.jp/english/equities/listing/cg/tvdivq0000008jdy-att/nlsgeu000006gevo.pdf", "label": "JPX CG Code Template", "title": "Japan CG Code - Board Charter Template Reference", "type": "compliance", "for_scores": [0, 1, 2]},
            {"url": "https://www.wbcsd.org/Programs/Redefining-Value/ISSB/Resources/Preparing-for-ISSB", "label": "WBCSD ISSB Guide", "title": "WBCSD Guide to Preparing for ISSB Standards", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "GOV-03",
        "pillar": "Governance",
        "category": "Board Competence",
        "standard": "General (S1)",
        "obligation": "recommended",
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Describe how the governance body ensures appropriate skills and competencies are available to oversee sustainability strategies.",
        "internal_controls": "",
        "guidance": "Document board member qualifications related to sustainability. Consider training programs.",
        "assurance_focus": "Board skills matrix, training records.",
        "minimum_action": "Not required for minimum compliance (SHOULD, not SHALL). If desired: arrange one sustainability briefing session for the board and note it in minutes.",
        "best_practice": "Board skills matrix including ESG competencies, annual sustainability training for all directors, external sustainability advisor retained, competency gaps assessed yearly.",
        "references": [
            {"url": "https://www.weforum.org/publications/esg-board-governance-guidance/", "label": "WEF ESG Board Guide", "title": "WEF Principles for Board Governance of ESG", "type": "best_practice", "for_scores": [0, 1, 2, 3, 4, 5]},
        ],
    },
    {
        "id": "GOV-04",
        "pillar": "Governance",
        "category": "Management Role",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Describe management's role in governance processes, controls, and procedures used to monitor and oversee sustainability-related risks and opportunities.",
        "internal_controls": "",
        "guidance": "Define management roles with sustainability responsibilities. Establish clear reporting to the board.",
        "assurance_focus": "Organizational charts, role descriptions, evidence of management reporting to board.",
        "minimum_action": "Assign sustainability data responsibility to an existing manager (e.g., Environmental Affairs or IR). Document their role in a brief memo and establish a reporting line to the board committee.",
        "best_practice": "Dedicated Chief Sustainability Officer or equivalent, cross-functional sustainability working group, documented RACI matrix, quarterly management reports to board with KPIs.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/", "label": "IFRS S1 Standard", "title": "IFRS S1 Management Role Requirements", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://hbr.org/2022/03/the-role-of-the-chief-sustainability-officer", "label": "HBR: CSO Role", "title": "Harvard Business Review - The Role of the Chief Sustainability Officer", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "GOV-05",
        "pillar": "Governance",
        "category": "Climate Governance",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Disclose how climate-related risks and opportunities are factored into management's decision-making.",
        "internal_controls": "",
        "guidance": "Document how climate factors influence capital allocation and strategic decisions.",
        "assurance_focus": "Evidence of climate considerations in management meeting minutes and investment decisions.",
        "minimum_action": "Add a climate risk checklist item to existing capital investment approval process. Minute at least one management discussion where climate was considered in a business decision.",
        "best_practice": "Systematic climate integration in all major investment decisions, internal carbon pricing applied to CAPEX, climate risk dashboard reviewed monthly by management, shadow carbon price in financial planning.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/", "label": "IFRS S2 Standard", "title": "IFRS S2 Climate-related Disclosures", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.cdp.net/en/guidance/guidance-for-companies", "label": "CDP Guidance", "title": "CDP Climate Governance and Internal Carbon Pricing Guide", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    # =========================================================================
    # STRATEGY
    # =========================================================================
    {
        "id": "STR-01",
        "pillar": "Strategy",
        "category": "Risks & Opportunities",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Disclose sustainability-related risks and opportunities that could reasonably be expected to affect the entity's prospects, including those arising across the entity's entire value chain (IFRS S1 para 28-35).",
        "internal_controls": "",
        "guidance": "Assess risks across short, medium, and long-term horizons. Consider both financial and operational impacts. MUST cover the entire value chain — upstream suppliers, own operations, and downstream customers/end-of-life.",
        "assurance_focus": "Documented risk register, methodology, time horizons applied, evidence of value chain consideration.",
        "minimum_action": "Create a sustainability risk register listing key risks and opportunities across your ENTIRE value chain (upstream supply, own operations, downstream distribution/use). For each, note time horizon (short/medium/long-term), potential impact (high/medium/low), and where in the value chain it occurs. SSBJ/IFRS S1 explicitly requires value chain coverage.",
        "best_practice": "Comprehensive risk register integrated with ERM, quantified financial impacts, value chain mapping with dependency analysis, regular stakeholder engagement including suppliers and customers, quarterly review cycle, published materiality matrix.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/", "label": "IFRS S1 Standard", "title": "IFRS S1 Risks & Opportunities Disclosure", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.tcfdhub.org/resource/tcfd-knowledge-hub-risk-management/", "label": "TCFD Risk Guide", "title": "TCFD Knowledge Hub - Risk Management Resources", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "STR-02",
        "pillar": "Strategy",
        "category": "Business Model Impact",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "important",
        "requirement": "Describe the current and anticipated effects of sustainability-related risks and opportunities on the entity's business model and ENTIRE value chain — from raw material sourcing through production, distribution, use, and end-of-life (IFRS S1 para 32-33).",
        "internal_controls": "",
        "guidance": "Map the ENTIRE value chain: upstream (suppliers, raw materials), own operations, and downstream (distribution, customers, end-of-life). Identify where sustainability risks concentrate and how they affect the business model. This is mandatory — not just a nice-to-have.",
        "assurance_focus": "Complete value chain mapping, business model impact assessment, dependency analysis across upstream and downstream.",
        "minimum_action": "Map your ENTIRE value chain from upstream to downstream. For each stage (raw material sourcing → manufacturing → distribution → customer use → end-of-life), identify sustainability-related dependencies and vulnerabilities. Describe how your top risks affect each stage. SSBJ requires the full value chain, not just direct operations.",
        "best_practice": "Detailed value chain mapping with quantified dependency analysis, regular supplier and customer engagement on sustainability, annual reassessment, integration with procurement and sales strategy, published value chain risk heat map.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/", "label": "IFRS S1 Standard", "title": "IFRS S1 Strategy & Business Model Disclosure", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.sasb.org/standards/materiality-finder/", "label": "SASB Materiality", "title": "SASB Materiality Finder - Industry Value Chain Risks", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "STR-03",
        "pillar": "Strategy",
        "category": "Financial Impact",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "nice_to_have",
        "requirement": "Describe the current and anticipated effects on the entity's financial position, performance, and cash flows.",
        "internal_controls": "",
        "guidance": "Quantify financial impacts where possible. Connect sustainability risks to financial statement line items.",
        "assurance_focus": "Financial impact methodology, assumptions, connection to financial planning.",
        "minimum_action": "Provide qualitative discussion of how sustainability risks may affect financial performance. Quantification can be phased in over time per SSBJ proportionality provisions.",
        "best_practice": "Quantified financial impact analysis connected to specific P&L and balance sheet items, scenario-based financial projections, integration with medium-term business plan.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/", "label": "IFRS S1 Standard", "title": "IFRS S1 Financial Effects Disclosure", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.cdsb.net/what-we-do/reporting-guidance", "label": "CDSB Guidance", "title": "CDSB Framework - Connecting Sustainability to Financial Reporting", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "STR-04",
        "pillar": "Strategy",
        "category": "Climate Scenario Analysis",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "important",
        "requirement": "Describe climate-related scenario analysis, including scenarios used and the resilience of the entity's strategy.",
        "internal_controls": "",
        "guidance": "Use at least two scenarios including one consistent with 1.5°C. Document assumptions and time horizons.",
        "assurance_focus": "Scenario selection rationale, methodology documentation.",
        "minimum_action": "Use two off-the-shelf scenarios (e.g., IEA NZE 2050 for transition, IPCC RCP 8.5 for physical). Write a qualitative narrative on how your strategy holds up under each. SSBJ allows proportionality.",
        "best_practice": "Multiple quantified scenarios (IEA, NGFS), sector-specific modeling, financial impact quantification per scenario, board-reviewed resilience conclusions, annual update cycle.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/", "label": "IFRS S2 Standard", "title": "IFRS S2 Scenario Analysis Requirements", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.iea.org/reports/world-energy-outlook-2024", "label": "IEA WEO Scenarios", "title": "IEA World Energy Outlook - NZE & STEPS Scenarios", "type": "best_practice", "for_scores": [3, 4, 5]},
            {"url": "https://www.ngfs.net/ngfs-scenarios-portal/", "label": "NGFS Scenarios", "title": "NGFS Climate Scenarios for Central Banks & Supervisors", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "STR-05",
        "pillar": "Strategy",
        "category": "Transition Plan",
        "standard": "Climate (S2)",
        "obligation": "interpretive",
        "la_scope": "not_in_initial_scope",
        "la_priority": "nice_to_have",
        "requirement": "Disclose the entity's climate-related transition plan, if the entity has one, including targets and actions.",
        "internal_controls": "",
        "guidance": "If a transition plan exists, document milestones, capital expenditure plans, and timelines.",
        "assurance_focus": "Documented transition plan, evidence of board approval, progress tracking.",
        "minimum_action": "Not required for minimum compliance (interpretive). If you have any decarbonization plans, simply disclose them. If not, state that a plan is under development.",
        "best_practice": "Board-approved transition plan with milestones, CAPEX allocation, SBTi-validated targets, annual progress reporting, third-party verification of progress.",
        "references": [
            {"url": "https://sciencebasedtargets.org/resources/files/SBTi-Corporate-Manual.pdf", "label": "SBTi Manual", "title": "Science Based Targets Initiative - Corporate Manual", "type": "best_practice", "for_scores": [3, 4, 5]},
            {"url": "https://transitiontaskforce.net/", "label": "TPT Framework", "title": "Transition Plan Taskforce - Disclosure Framework", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "STR-06",
        "pillar": "Strategy",
        "category": "Strategy Resilience",
        "standard": "General (S1)",
        "obligation": "recommended",
        "la_scope": "not_in_initial_scope",
        "la_priority": "nice_to_have",
        "requirement": "Describe the resilience of the entity's strategy and business model to sustainability-related risks.",
        "internal_controls": "",
        "guidance": "Assess adaptability of business model under different scenarios. Identify key vulnerabilities.",
        "assurance_focus": "Documented resilience assessment.",
        "minimum_action": "Not required for minimum compliance (SHOULD, not SHALL). A brief qualitative statement on strategy resilience is sufficient if you choose to address it.",
        "best_practice": "Comprehensive resilience assessment linked to scenario analysis, adaptation strategies with timelines, regular board review of strategy resilience.",
        "references": [
            {"url": "https://www.tcfdhub.org/", "label": "TCFD Hub", "title": "TCFD Knowledge Hub - Strategy Resilience Resources", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    # =========================================================================
    # RISK MANAGEMENT
    # =========================================================================
    {
        "id": "RSK-01",
        "pillar": "Risk Management",
        "category": "Risk Identification",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Describe the processes used to identify sustainability-related risks and opportunities.",
        "internal_controls": "",
        "guidance": "Establish a formal risk identification process including environmental scanning and materiality assessment.",
        "assurance_focus": "Documented risk identification methodology, evidence of regular execution.",
        "minimum_action": "Conduct one formal risk identification workshop. Document the process used (who participated, what was considered, how risks were identified). Keep the output as your risk register.",
        "best_practice": "Annual structured risk identification with stakeholder engagement, emerging risk scanning, integration with materiality assessment, dynamic risk register with regular updates.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/", "label": "IFRS S1 Standard", "title": "IFRS S1 Risk Management Process Disclosure", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.iso.org/iso-31000-risk-management.html", "label": "ISO 31000", "title": "ISO 31000 Risk Management Framework", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "RSK-02",
        "pillar": "Risk Management",
        "category": "Risk Assessment",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Describe the processes used to assess, prioritize, and monitor sustainability-related risks.",
        "internal_controls": "",
        "guidance": "Use consistent criteria for assessing likelihood and impact. Establish monitoring and escalation.",
        "assurance_focus": "Risk assessment criteria, risk registers, monitoring evidence.",
        "minimum_action": "Add likelihood/impact scoring to your risk register (simple 3x3 matrix is sufficient). Document how you prioritize risks. Assign an owner to each top risk.",
        "best_practice": "Quantified risk assessment with defined criteria, risk dashboard with KRIs, regular monitoring reports to management, automated alerts for threshold breaches.",
        "references": [
            {"url": "https://www.coso.org/guidance-on-enterprise-risk-management", "label": "COSO ERM", "title": "COSO Enterprise Risk Management Framework", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "RSK-03",
        "pillar": "Risk Management",
        "category": "Risk Integration",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Describe how sustainability risk management processes are integrated into overall risk management.",
        "internal_controls": "",
        "guidance": "Integrate sustainability risks into the enterprise risk management (ERM) framework.",
        "assurance_focus": "ERM framework showing sustainability integration.",
        "minimum_action": "Add sustainability as a risk category in your existing ERM framework. One paragraph in ERM policy describing integration is sufficient for minimum compliance.",
        "best_practice": "Full integration of sustainability risks into ERM with unified risk appetite statement, cross-functional risk committee, combined reporting to board.",
        "references": [
            {"url": "https://www.coso.org/guidance-on-enterprise-risk-management", "label": "COSO ERM", "title": "COSO ERM - Integrating Sustainability Risks", "type": "all", "for_scores": [0, 1, 2, 3, 4, 5]},
        ],
    },
    {
        "id": "RSK-04",
        "pillar": "Risk Management",
        "category": "Climate Risk",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Describe how climate-related risks are identified, assessed, and managed, including physical and transition risks.",
        "internal_controls": "",
        "guidance": "Cover both physical risks (acute/chronic) and transition risks (policy, technology, market, reputation).",
        "assurance_focus": "Climate risk assessment documentation, physical and transition risk categorization.",
        "minimum_action": "List your climate risks in two categories: physical (acute + chronic) and transition (policy, technology, market, reputation). Assess each as high/medium/low. Document in 1-2 pages.",
        "best_practice": "Quantified climate risk assessment using TCFD framework, physical risk modeling (flood, heat stress), transition risk analysis with financial impacts, mitigation strategies per risk.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/", "label": "IFRS S2 Standard", "title": "IFRS S2 Climate Risk Identification & Assessment", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.tcfdhub.org/resource/tcfd-knowledge-hub-risk-management/", "label": "TCFD Risk Guide", "title": "TCFD Risk Management Resources", "type": "best_practice", "for_scores": [3, 4, 5]},
            {"url": "https://www.unepfi.org/climate-change/tcfd/", "label": "UNEP FI TCFD", "title": "UNEP FI - TCFD Implementation for Financial Institutions", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "RSK-05",
        "pillar": "Risk Management",
        "category": "Internal Controls",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Establish internal controls over sustainability-related data collection, processing, and reporting.",
        "internal_controls": "ESSENTIAL FOR LIMITED ASSURANCE: (1) Assign data owners for each emission source. (2) Document data collection procedures step-by-step. (3) Implement maker-checker review for calculations. (4) Maintain audit trail of all data changes. (5) Perform regular reconciliation of source data to reported figures. (6) Implement access controls on data systems.",
        "guidance": "Design controls comparable to financial reporting controls. Include data validation, reconciliation, and review procedures.",
        "assurance_focus": "Documented control framework, control testing evidence, data quality procedures, segregation of duties.",
        "minimum_action": "CRITICAL FOR ASSURANCE: (1) Assign a data owner for GHG data. (2) Write a 1-page data collection procedure. (3) Implement maker-checker: one person calculates, another reviews. (4) Keep all source documents (invoices, meter readings). (5) Create a simple reconciliation checklist. This is the bare minimum an auditor needs to see.",
        "best_practice": "Full internal control framework comparable to financial reporting (SOX-like), automated data validation, continuous monitoring, segregation of duties matrix, regular control testing by internal audit, error tracking with root cause analysis.",
        "references": [
            {"url": "https://www.iaasb.org/publications/international-standard-assurance-engagements-isae-3410-assurance-engagements-greenhouse-gas-statements", "label": "ISAE 3410", "title": "ISAE 3410 - Assurance on GHG Statements (Internal Control Requirements)", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.coso.org/guidance-on-internal-control", "label": "COSO ICIF", "title": "COSO Internal Control - Integrated Framework", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    # =========================================================================
    # METRICS & TARGETS
    # =========================================================================
    {
        "id": "MET-01",
        "pillar": "Metrics & Targets",
        "category": "GHG Scope 1",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Disclose absolute gross Scope 1 greenhouse gas emissions.",
        "internal_controls": "ESSENTIAL FOR LIMITED ASSURANCE: (1) Complete inventory of all direct emission sources (fuel combustion, process, fugitive, mobile). (2) Documented calculation methodology (GHG Protocol preferred). (3) Verified activity data from meters, invoices, or logs. (4) Documented emission factors with sources and version dates. (5) Calculation review and sign-off by qualified person. (6) Reconciliation of activity data to financial records where applicable.",
        "guidance": "Measure using GHG Protocol or equivalent. Include all material sources. Use appropriate emission factors.",
        "assurance_focus": "Emission calculation methodology, source data, emission factors, completeness of boundary, data quality checks.",
        "minimum_action": "CRITICAL FOR ASSURANCE: (1) List ALL direct emission sources (boilers, vehicles, refrigerants, etc.). (2) Write a calculation procedure: activity data x emission factor = tCO2e. (3) Use government-published emission factors (MOE Japan or DEFRA). (4) Collect activity data from fuel invoices. (5) Have someone review the calculation. (6) Keep all source documents.",
        "best_practice": "Complete GHG inventory per GHG Protocol, third-party verified data, real-time monitoring systems, automated calculation tools, emission factors reviewed annually, continuous improvement of data quality.",
        "references": [
            {"url": "https://ghgprotocol.org/corporate-standard", "label": "GHG Protocol", "title": "GHG Protocol Corporate Standard - Scope 1 Calculation Guide", "type": "all", "for_scores": [0, 1, 2, 3, 4, 5]},
            {"url": "https://www.env.go.jp/earth/ondanka/santeiho/index.html", "label": "MOE Japan EFs", "title": "Japan MOE Emission Factors Database (排出係数一覧)", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/", "label": "IFRS S2 Standard", "title": "IFRS S2 GHG Emissions Disclosure Requirements", "type": "compliance", "for_scores": [0, 1, 2, 3]},
        ],
    },
    {
        "id": "MET-02",
        "pillar": "Metrics & Targets",
        "category": "GHG Scope 2",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Disclose absolute gross Scope 2 greenhouse gas emissions (location-based and, if applicable, market-based).",
        "internal_controls": "ESSENTIAL FOR LIMITED ASSURANCE: (1) Complete inventory of all purchased electricity, heat, steam, cooling. (2) Location-based calculation using grid emission factors. (3) Market-based calculation if applicable (contractual instruments). (4) Verified energy consumption data from utility invoices. (5) Documented grid emission factors with sources. (6) Review and sign-off by qualified person.",
        "guidance": "Report both location-based and market-based. Use appropriate grid emission factors.",
        "assurance_focus": "Both calculation approaches, grid factors, energy consumption data evidence.",
        "minimum_action": "CRITICAL FOR ASSURANCE: (1) Collect electricity bills for ALL facilities. (2) Calculate location-based: kWh x grid emission factor (use Japan's area-specific factors from MOE). (3) If you buy green electricity, also calculate market-based. (4) SSBJ requires BOTH methods. (5) Have someone review. (6) Keep utility invoices.",
        "best_practice": "Automated utility data collection, both location and market-based reported, renewable energy tracking with certificates, monthly monitoring, reconciliation to financial records, third-party verification.",
        "references": [
            {"url": "https://ghgprotocol.org/scope_2_guidance", "label": "GHG Protocol Scope 2", "title": "GHG Protocol Scope 2 Guidance - Location vs Market-Based", "type": "all", "for_scores": [0, 1, 2, 3, 4, 5]},
            {"url": "https://www.env.go.jp/earth/ondanka/santeiho/index.html", "label": "MOE Japan EFs", "title": "Japan MOE Grid Emission Factors by Area", "type": "compliance", "for_scores": [0, 1, 2, 3]},
        ],
    },
    {
        "id": "MET-03",
        "pillar": "Metrics & Targets",
        "category": "GHG Scope 3",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "important",
        "requirement": "Disclose absolute gross Scope 3 greenhouse gas emissions, broken down by all 15 GHG Protocol categories. This is MANDATORY under SSBJ/IFRS S2 para 29(a)(vi) even though not in initial limited assurance scope.",
        "internal_controls": "",
        "guidance": "SSBJ requires disclosure of ALL 15 Scope 3 categories with breakdown — not just 'material' ones. Use GHG Protocol Corporate Value Chain (Scope 3) Standard. Estimation is acceptable where direct data unavailable. Disclose data sources, assumptions, and measurement approach.",
        "assurance_focus": "Category coverage assessment, calculation methodologies per category, data sources, estimation assumptions, value chain boundary.",
        "minimum_action": "Not in initial LA scope but IS mandatory for disclosure. (1) Assess all 15 Scope 3 categories for your business. (2) Calculate emissions for each applicable category — use estimation methods (spend-based, industry averages) where primary data is unavailable. (3) Disclose which categories are included and your measurement approach. SSBJ provides first-year transition relief allowing delay, but you must plan for full coverage. Engage with key suppliers early for data collection.",
        "best_practice": "All 15 categories calculated with increasing use of primary (supplier-specific) data, formal supplier engagement program, annual data quality improvement plan, science-based Scope 3 targets, integration with procurement strategy.",
        "references": [
            {"url": "https://ghgprotocol.org/corporate-value-chain-scope-3-standard", "label": "GHG Protocol Scope 3", "title": "GHG Protocol Scope 3 Standard - Category Guide", "type": "all", "for_scores": [0, 1, 2, 3, 4, 5]},
            {"url": "https://www.cdp.net/en/guidance/guidance-for-companies", "label": "CDP Supply Chain", "title": "CDP Supply Chain Reporting Guidance", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "MET-04",
        "pillar": "Metrics & Targets",
        "category": "Climate Targets",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "important",
        "requirement": "Disclose climate-related targets including GHG reduction targets, base year, target year, and milestones.",
        "internal_controls": "",
        "guidance": "Set credible targets. Define clear base years and milestones. Report progress annually.",
        "assurance_focus": "Target-setting methodology, base year data, progress tracking.",
        "minimum_action": "Set at least one GHG reduction target. Define: base year, target year, whether absolute or intensity, and scope covered (at least Scope 1+2). Even a modest target is better than none for compliance.",
        "best_practice": "SBTi-validated science-based targets for 1.5°C alignment, near-term and long-term targets, interim milestones, annual progress tracking with variance analysis, net-zero commitment with roadmap.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/", "label": "IFRS S2 Standard", "title": "IFRS S2 Climate Target Disclosure Requirements", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://sciencebasedtargets.org/", "label": "SBTi", "title": "Science Based Targets Initiative - Target Setting", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "MET-05",
        "pillar": "Metrics & Targets",
        "category": "Industry Metrics",
        "standard": "Climate (S2)",
        "obligation": "interpretive",
        "la_scope": "not_in_initial_scope",
        "la_priority": "nice_to_have",
        "requirement": "Disclose industry-specific metrics relevant to the entity's sector, considering SASB standards as reference.",
        "internal_controls": "",
        "guidance": "Consider SASB industry standards as guidance. Disclosure depends on entity's assessment of relevance.",
        "assurance_focus": "Industry metric selection rationale if disclosed.",
        "minimum_action": "Not required for minimum compliance (interpretive). If desired: check SASB standards for your industry and select 1-2 relevant metrics to disclose.",
        "best_practice": "Full SASB industry standard disclosure, peer benchmarking, metrics integrated into management reporting, trend analysis over 3+ years.",
        "references": [
            {"url": "https://www.sasb.org/standards/", "label": "SASB Standards", "title": "SASB Industry-Specific Sustainability Standards", "type": "all", "for_scores": [0, 1, 2, 3, 4, 5]},
        ],
    },
    {
        "id": "MET-06",
        "pillar": "Metrics & Targets",
        "category": "Cross-Industry Metrics",
        "standard": "Climate (S2)",
        "obligation": "interpretive",
        "la_scope": "not_in_initial_scope",
        "la_priority": "nice_to_have",
        "requirement": "Consider disclosing cross-industry climate metrics: transition risk amount, physical risk amount, climate opportunities amount, capital deployment, internal carbon price.",
        "internal_controls": "",
        "guidance": "SSBJ deliberated whether these should be mandatory. Currently subject to entity judgment on materiality.",
        "assurance_focus": "Methodology and data sources if disclosed.",
        "minimum_action": "Not required for minimum compliance (interpretive). If desired: start with internal carbon price — even a simple estimate helps demonstrate climate integration in decision-making.",
        "best_practice": "Internal carbon price applied to all CAPEX decisions, quantified transition and physical risk amounts, climate opportunity revenue tracking, capital deployment aligned to Paris goals.",
        "references": [
            {"url": "https://www.cdp.net/en/climate/carbon-pricing", "label": "CDP Carbon Pricing", "title": "CDP Internal Carbon Pricing Guide", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "MET-07",
        "pillar": "Metrics & Targets",
        "category": "Data Quality",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "in_scope",
        "la_priority": "essential",
        "requirement": "Ensure the quality, completeness, and accuracy of sustainability data used for disclosure.",
        "internal_controls": "ESSENTIAL FOR LIMITED ASSURANCE: (1) Data governance policy defining roles, responsibilities, and standards. (2) Validation rules at data entry points. (3) Reconciliation between source systems and reporting. (4) Error tracking and correction log. (5) Data completeness checks before reporting. (6) Documented data lineage from source to disclosure.",
        "guidance": "Implement data quality management comparable to financial reporting. Establish data governance and validation.",
        "assurance_focus": "Data governance framework, validation procedures, reconciliation evidence, data lineage.",
        "minimum_action": "CRITICAL FOR ASSURANCE: (1) Create a data flow diagram: where does data come from, who enters it, who checks it. (2) Add basic validation (e.g., compare this year to last year — flag if >20% change). (3) Keep a simple error log. (4) Do a completeness check before reporting (all sites reported?).",
        "best_practice": "Formal data governance policy, automated validation rules, real-time data quality dashboards, documented data lineage from source to disclosure, regular data quality audits, continuous improvement program.",
        "references": [
            {"url": "https://www.iaasb.org/publications/international-standard-assurance-engagements-isae-3410-assurance-engagements-greenhouse-gas-statements", "label": "ISAE 3410", "title": "ISAE 3410 - Data Quality Requirements for GHG Assurance", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://ghgprotocol.org/corporate-standard", "label": "GHG Protocol", "title": "GHG Protocol - Data Quality Management", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "MET-08",
        "pillar": "Metrics & Targets",
        "category": "GHG Emissions Intensity",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "important",
        "requirement": "Disclose GHG emissions intensity — emissions per unit of physical or economic output (IFRS S2 para 29(b)). Required for Scope 1+2 combined, and separately for Scope 3 if disclosed.",
        "internal_controls": "",
        "guidance": "Calculate emissions intensity using a denominator appropriate to your industry (e.g., tCO2e per million JPY revenue, per unit produced, per employee, per square meter). Must be consistent year-over-year.",
        "assurance_focus": "Intensity ratio calculation, denominator selection rationale, consistency of methodology.",
        "minimum_action": "Calculate GHG intensity for Scope 1+2 combined using revenue as denominator (tCO2e / ¥ billion revenue). This is a mandatory metric under SSBJ/IFRS S2. Choose a denominator relevant to your industry and apply consistently.",
        "best_practice": "Multiple intensity metrics (revenue-based and physical-based), year-over-year trend analysis, peer benchmarking, sector-specific denominators, intensity targets alongside absolute targets.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/", "label": "IFRS S2 Standard", "title": "IFRS S2 para 29(b) - GHG Emissions Intensity Requirements", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://ghgprotocol.org/corporate-standard", "label": "GHG Protocol", "title": "GHG Protocol - Emissions Intensity Guidance", "type": "best_practice", "for_scores": [3, 4, 5]},
        ],
    },
    {
        "id": "MET-09",
        "pillar": "Metrics & Targets",
        "category": "Climate-related Remuneration",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "nice_to_have",
        "requirement": "Disclose whether and how climate-related considerations are factored into executive remuneration, including the percentage of remuneration linked to climate targets (IFRS S2 para 29(g)).",
        "internal_controls": "",
        "guidance": "Disclose whether any executive compensation is linked to climate/sustainability performance. If yes, describe what metrics are used, what percentage of compensation is affected, and how performance is assessed.",
        "assurance_focus": "Compensation policy documentation, climate KPI linkage, board approval of remuneration structure.",
        "minimum_action": "Disclose whether executive remuneration is linked to climate targets. If not currently linked, state this clearly. If linked, describe the metrics used and percentage of compensation affected. SSBJ/IFRS S2 requires this disclosure.",
        "best_practice": "Explicit climate KPIs in executive compensation (e.g., GHG reduction targets, energy efficiency), percentage of variable compensation linked to sustainability metrics, board-approved targets, annual assessment with external verification.",
        "references": [
            {"url": "https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/", "label": "IFRS S2 Standard", "title": "IFRS S2 para 29(g) - Climate-related Remuneration Disclosure", "type": "compliance", "for_scores": [0, 1, 2, 3]},
            {"url": "https://www.jpx.co.jp/english/equities/listing/cg/tvdivq0000008jdy-att/nlsgeu000006gevo.pdf", "label": "JPX CG Code", "title": "Japan Corporate Governance Code - Executive Compensation", "type": "compliance", "for_scores": [0, 1, 2]},
        ],
    },
]


LIMITED_ASSURANCE_CRITERIA = [
    # =========================================================================
    # INTERNAL CONTROLS REQUIRED FOR LIMITED ASSURANCE
    # Based on ISSA 5000 (replacing ISAE 3000 / ISAE 3410)
    # FSA Roadmap (July 2025): First 2 years scope covers:
    #   - Scope 1 & 2 GHG emissions (LA-01 to LA-10)
    #   - Governance disclosures (LA-11 to LA-13)
    #   - Risk Management disclosures (LA-14 to LA-16)
    # From 3rd year: scope expansion to full SSBJ disclosures under consideration
    # =========================================================================
    {
        "id": "LA-01",
        "category": "Organizational Boundary",
        "obligation": "essential",
        "requirement": "Clearly define the organizational boundary for GHG reporting (operational control or equity share approach).",
        "guidance": "Document which entities/facilities are included. Use GHG Protocol guidance on consolidation approach. Ensure boundary aligns with financial reporting where possible.",
        "internal_controls": "Maintain a list of all consolidated entities with in/out boundary justification.",
    },
    {
        "id": "LA-02",
        "category": "Emission Source Inventory",
        "obligation": "essential",
        "requirement": "Maintain a complete inventory of all Scope 1 and Scope 2 emission sources.",
        "guidance": "List every facility, equipment, and process that generates direct (Scope 1) or indirect energy (Scope 2) emissions. Review annually for completeness.",
        "internal_controls": "Annual completeness review. Cross-check against asset register, facility list, and utility accounts.",
    },
    {
        "id": "LA-03",
        "category": "Calculation Methodology",
        "obligation": "essential",
        "requirement": "Document the GHG calculation methodology, including formulas, emission factors, and GWP values used.",
        "guidance": "Use GHG Protocol as primary methodology. Document specific emission factors with sources and publication dates. State GWP values (IPCC AR5 or AR6).",
        "internal_controls": "Written calculation manual. Version-controlled emission factor database.",
    },
    {
        "id": "LA-04",
        "category": "Activity Data Controls",
        "obligation": "essential",
        "requirement": "Implement controls over the collection, recording, and completeness of activity data (fuel, energy, etc.).",
        "guidance": "Activity data should be traceable to source documents (invoices, meter readings, delivery records). Implement regular reconciliation between source data and calculation inputs.",
        "internal_controls": "Monthly data collection procedure. Source document retention. Reconciliation of reported data to invoices/meters.",
    },
    {
        "id": "LA-05",
        "category": "Calculation Review",
        "obligation": "essential",
        "requirement": "Implement a review and approval process for GHG calculations before disclosure.",
        "guidance": "Independent review of calculations by a person other than the preparer (maker-checker). Document the review with sign-off and date.",
        "internal_controls": "Maker-checker process. Documented review sign-off. Qualified reviewer assigned.",
    },
    {
        "id": "LA-06",
        "category": "Data Quality & Error Correction",
        "obligation": "essential",
        "requirement": "Establish procedures for identifying, tracking, and correcting data errors.",
        "guidance": "Define materiality thresholds for errors. Maintain an error log. Implement reasonableness checks (year-over-year comparison, intensity ratios).",
        "internal_controls": "Error log. Reasonableness checks (YoY variance analysis). Defined correction and restatement procedure.",
    },
    {
        "id": "LA-07",
        "category": "Documentation & Audit Trail",
        "obligation": "essential",
        "requirement": "Maintain sufficient documentation to support all reported GHG figures and enable third-party verification.",
        "guidance": "Retain source documents, calculation spreadsheets, assumptions, and approvals for at least the assurance period. Ensure an auditor could reconstruct figures from source data.",
        "internal_controls": "Document retention policy (minimum 5 years). Organized file structure. Version control on calculation files.",
    },
    {
        "id": "LA-08",
        "category": "Roles & Responsibilities",
        "obligation": "essential",
        "requirement": "Assign clear roles and responsibilities for GHG data collection, calculation, review, and reporting.",
        "guidance": "Document who is responsible for each step: data collection at site level, consolidation, calculation, review, and final approval. Ensure segregation between preparer and reviewer.",
        "internal_controls": "RACI matrix for GHG reporting process. Named individuals with sign-off authority.",
    },
    {
        "id": "LA-09",
        "category": "Consistency & Restatement",
        "obligation": "important",
        "requirement": "Apply methodologies consistently across reporting periods. Document and disclose any changes.",
        "guidance": "If methodology, boundary, or emission factors change, document the reason and restate prior year if material.",
        "internal_controls": "Methodology change log. Restatement policy with materiality threshold.",
    },
    {
        "id": "LA-10",
        "category": "Management Representations",
        "obligation": "essential",
        "requirement": "Management provides written representations on completeness and accuracy of GHG data.",
        "guidance": "Management representation letter confirming: responsibility for GHG data, completeness of emission sources, accuracy of calculations, and disclosure of all known errors. Under ISSA 5000, management must also confirm responsibility for the sustainability information and the internal controls over it.",
        "internal_controls": "Annual management representation letter template. Sign-off by appropriate management level.",
    },
    # =========================================================================
    # GOVERNANCE ASSURANCE READINESS (in scope from year 1)
    # FSA Roadmap: Governance disclosures are in initial LA scope
    # Assurance provider will inquire about governance processes per IFRS S1 para 26-27
    # =========================================================================
    {
        "id": "LA-11",
        "category": "Governance Oversight Documentation",
        "obligation": "essential",
        "requirement": "Document the governance body(ies) or individual(s) responsible for sustainability oversight, including their mandate and authority.",
        "guidance": "Maintain formal records showing: (1) Which body/individual has sustainability oversight responsibility, (2) Terms of reference or mandate explicitly referencing sustainability, (3) Role descriptions and reporting lines. Under ISSA 5000 limited assurance, the practitioner will inquire about governance processes and inspect supporting documentation.",
        "internal_controls": "Formal board/committee charter with sustainability mandate. Governance structure chart. Annual review of terms of reference.",
    },
    {
        "id": "LA-12",
        "category": "Governance Reporting Evidence",
        "obligation": "essential",
        "requirement": "Maintain evidence of regular governance body engagement with sustainability matters: meeting minutes, briefing materials, and decision records.",
        "guidance": "Assurance providers will seek evidence that governance oversight is not just documented on paper but actually functioning. Maintain: (1) Board/committee meeting minutes showing sustainability agenda items, (2) Briefing materials provided to the governance body, (3) Records of frequency of sustainability briefings (IFRS S1 requires disclosure of how often the body is informed), (4) Evidence of decisions or actions taken.",
        "internal_controls": "Minimum quarterly sustainability agenda items in relevant board/committee meetings. Minutes retained for assurance period. Briefing materials archived.",
    },
    {
        "id": "LA-13",
        "category": "Management Role Documentation",
        "obligation": "essential",
        "requirement": "Document management's role in monitoring and overseeing sustainability-related risks and opportunities, including designated personnel and reporting to governance body.",
        "guidance": "Clearly document: (1) Named management personnel responsible for sustainability data and reporting, (2) Their specific responsibilities and authority, (3) How management reports to the governance body on sustainability matters, (4) Evidence of management's sustainability monitoring activities. This supports IFRS S1 para 27 requirements on management's role.",
        "internal_controls": "RACI matrix or role description for sustainability management. Evidence of management reporting to board (reports, memos, dashboards).",
    },
    # =========================================================================
    # RISK MANAGEMENT ASSURANCE READINESS (in scope from year 1)
    # FSA Roadmap: Risk Management disclosures are in initial LA scope
    # Assurance provider will inquire about risk processes per IFRS S1 para 43
    # =========================================================================
    {
        "id": "LA-14",
        "category": "Risk Process Documentation",
        "obligation": "essential",
        "requirement": "Document the processes used to identify, assess, and prioritize sustainability-related risks and opportunities.",
        "guidance": "Maintain documentation showing: (1) How sustainability risks are identified (methodology, inputs, data sources), (2) How risks are assessed (likelihood/impact criteria, scoring methodology), (3) How risks are prioritized relative to other business risks, (4) How risks are monitored over time. Under ISSA 5000 limited assurance, the practitioner will inquire about these processes and review supporting documentation.",
        "internal_controls": "Written risk identification and assessment methodology. Risk register with documented assessment criteria. Annual review cycle.",
    },
    {
        "id": "LA-15",
        "category": "Risk Assessment Records",
        "obligation": "essential",
        "requirement": "Maintain records of risk assessments performed, including inputs, parameters, scope, outcomes, and risk owners.",
        "guidance": "For each assessment cycle, retain: (1) Risk register with identified risks and opportunities, (2) Assessment scores/ratings with supporting rationale, (3) Named risk owners, (4) Monitoring status and actions taken, (5) Changes from prior period assessments. IFRS S1 para 43 requires disclosure of how processes have changed from the prior year.",
        "internal_controls": "Dated risk register. Version history showing changes. Risk owner sign-off. Year-over-year comparison documentation.",
    },
    {
        "id": "LA-16",
        "category": "Risk Integration Evidence",
        "obligation": "essential",
        "requirement": "Document how sustainability risk management processes are integrated into the entity's overall risk management framework.",
        "guidance": "The assurance provider will look for evidence that sustainability risks are not managed in isolation. Document: (1) How sustainability risks feed into enterprise risk management (ERM), (2) Whether sustainability risks are reported alongside other business risks, (3) Integration points between sustainability risk processes and existing risk governance. IFRS S1 para 43 explicitly requires this disclosure.",
        "internal_controls": "ERM framework document showing sustainability integration. Combined risk reporting to board. Cross-reference between sustainability risk register and ERM risk register.",
    },
]


def get_criteria_by_pillar():
    """Group SSBJ criteria by pillar."""
    pillars = {}
    for c in SSBJ_CRITERIA:
        pillar = c["pillar"]
        if pillar not in pillars:
            pillars[pillar] = []
        pillars[pillar].append(c)
    return pillars


def get_criteria_by_standard():
    """Group SSBJ criteria by standard."""
    standards = {}
    for c in SSBJ_CRITERIA:
        std = c["standard"]
        if std not in standards:
            standards[std] = []
        standards[std].append(c)
    return standards


def get_criterion_by_id(criterion_id):
    """Look up a single criterion by ID."""
    for c in SSBJ_CRITERIA:
        if c["id"] == criterion_id:
            return c
    for c in LIMITED_ASSURANCE_CRITERIA:
        if c["id"] == criterion_id:
            return c
    return None
