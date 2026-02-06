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
  - "in_scope" = directly subject to limited assurance (Scope 1 & 2 and their controls)
  - "supporting" = needed to support assurance-ready disclosures
  - "not_in_initial_scope" = not in initial limited assurance scope (may expand later)
- la_priority: "essential" / "important" / "nice_to_have" for minimum viable compliance
- internal_controls: Specific internal controls needed for limited assurance (if applicable)
- guidance: Guidance on what good practice looks like
- assurance_focus: What a limited assurance reviewer would look for

Sources:
- FSA Roadmap on Sustainability Disclosure and Assurance (Nov 2025)
- SSBJ Standards (March 2025)
- ISAE 3000 / ISAE 3410 / ISSA 5000 requirements

Limited Assurance Scope (FSA Roadmap):
- Initially focused on Scope 1 and Scope 2 GHG emissions only
- Mandatory assurance starts one year AFTER mandatory disclosure
- Assurance scope may expand after the third year
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
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Disclose the governance body(ies) or individual(s) responsible for oversight of sustainability-related risks and opportunities.",
        "internal_controls": "",
        "guidance": "Identify specific board committees or members with sustainability oversight. Document their mandate, authority, and reporting lines.",
        "assurance_focus": "Evidence of formal board mandate, committee terms of reference, and documented oversight activities.",
        "minimum_action": "Designate one existing board committee (e.g., Risk Committee) as responsible for sustainability oversight. Add one line to their terms of reference: 'oversight of sustainability-related risks and opportunities.' Minute this decision.",
        "best_practice": "Dedicated Sustainability Committee with named chair, quarterly meetings, formal terms of reference, direct reporting to full board, and documented agenda items. Peers like Toyota and Sony have standalone ESG committees with published charters.",
    },
    {
        "id": "GOV-02",
        "pillar": "Governance",
        "category": "Board Oversight",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Describe how the governance body's responsibilities are reflected in terms of reference, board mandates, and related policies.",
        "internal_controls": "",
        "guidance": "Ensure board charters and corporate governance policies explicitly reference sustainability oversight.",
        "assurance_focus": "Documented policies and terms of reference that explicitly include sustainability.",
        "minimum_action": "Add sustainability oversight language to existing board committee charter or corporate governance policy. One paragraph is sufficient. Have the board formally approve the revised document.",
        "best_practice": "Standalone sustainability governance policy linked to corporate governance code, annual policy review cycle, published in integrated report. Leading companies cross-reference SSBJ requirements in their governance framework.",
    },
    {
        "id": "GOV-03",
        "pillar": "Governance",
        "category": "Board Competence",
        "standard": "General (S1)",
        "obligation": "recommended",
        "la_scope": "not_in_initial_scope",
        "la_priority": "nice_to_have",
        "requirement": "Describe how the governance body ensures appropriate skills and competencies are available to oversee sustainability strategies.",
        "internal_controls": "",
        "guidance": "Document board member qualifications related to sustainability. Consider training programs.",
        "assurance_focus": "Board skills matrix, training records.",
        "minimum_action": "Not required for minimum compliance (SHOULD, not SHALL). If desired: arrange one sustainability briefing session for the board and note it in minutes.",
        "best_practice": "Board skills matrix including ESG competencies, annual sustainability training for all directors, external sustainability advisor retained, competency gaps assessed yearly.",
    },
    {
        "id": "GOV-04",
        "pillar": "Governance",
        "category": "Management Role",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Describe management's role in governance processes, controls, and procedures used to monitor and oversee sustainability-related risks and opportunities.",
        "internal_controls": "",
        "guidance": "Define management roles with sustainability responsibilities. Establish clear reporting to the board.",
        "assurance_focus": "Organizational charts, role descriptions, evidence of management reporting to board.",
        "minimum_action": "Assign sustainability data responsibility to an existing manager (e.g., Environmental Affairs or IR). Document their role in a brief memo and establish a reporting line to the board committee.",
        "best_practice": "Dedicated Chief Sustainability Officer or equivalent, cross-functional sustainability working group, documented RACI matrix, quarterly management reports to board with KPIs.",
    },
    {
        "id": "GOV-05",
        "pillar": "Governance",
        "category": "Climate Governance",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Disclose how climate-related risks and opportunities are factored into management's decision-making.",
        "internal_controls": "",
        "guidance": "Document how climate factors influence capital allocation and strategic decisions.",
        "assurance_focus": "Evidence of climate considerations in management meeting minutes and investment decisions.",
        "minimum_action": "Add a climate risk checklist item to existing capital investment approval process. Minute at least one management discussion where climate was considered in a business decision.",
        "best_practice": "Systematic climate integration in all major investment decisions, internal carbon pricing applied to CAPEX, climate risk dashboard reviewed monthly by management, shadow carbon price in financial planning.",
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
        "requirement": "Disclose sustainability-related risks and opportunities that could reasonably be expected to affect the entity's prospects.",
        "internal_controls": "",
        "guidance": "Assess risks across short, medium, and long-term horizons. Consider both financial and operational impacts.",
        "assurance_focus": "Documented risk register, methodology, time horizons applied.",
        "minimum_action": "Create a simple sustainability risk register listing 5-10 key risks and opportunities. For each, note the time horizon (short/medium/long-term) and potential impact (high/medium/low). One workshop is enough.",
        "best_practice": "Comprehensive risk register integrated with ERM, quantified financial impacts, regular stakeholder engagement to identify emerging risks, quarterly review cycle, published materiality matrix.",
    },
    {
        "id": "STR-02",
        "pillar": "Strategy",
        "category": "Business Model Impact",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "important",
        "requirement": "Describe the current and anticipated effects of sustainability-related risks and opportunities on the entity's business model and value chain.",
        "internal_controls": "",
        "guidance": "Map risks to specific business model elements. Assess value chain dependencies.",
        "assurance_focus": "Value chain mapping, business model impact assessment.",
        "minimum_action": "Write a 1-2 page narrative describing how your top 3 sustainability risks affect your business model. Include a simple value chain diagram showing where risks concentrate.",
        "best_practice": "Detailed value chain mapping with dependency analysis, quantified supply chain exposure, regular supplier engagement on sustainability, dynamic assessment updated annually.",
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
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Describe the processes used to identify sustainability-related risks and opportunities.",
        "internal_controls": "",
        "guidance": "Establish a formal risk identification process including environmental scanning and materiality assessment.",
        "assurance_focus": "Documented risk identification methodology, evidence of regular execution.",
        "minimum_action": "Conduct one formal risk identification workshop. Document the process used (who participated, what was considered, how risks were identified). Keep the output as your risk register.",
        "best_practice": "Annual structured risk identification with stakeholder engagement, emerging risk scanning, integration with materiality assessment, dynamic risk register with regular updates.",
    },
    {
        "id": "RSK-02",
        "pillar": "Risk Management",
        "category": "Risk Assessment",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Describe the processes used to assess, prioritize, and monitor sustainability-related risks.",
        "internal_controls": "",
        "guidance": "Use consistent criteria for assessing likelihood and impact. Establish monitoring and escalation.",
        "assurance_focus": "Risk assessment criteria, risk registers, monitoring evidence.",
        "minimum_action": "Add likelihood/impact scoring to your risk register (simple 3x3 matrix is sufficient). Document how you prioritize risks. Assign an owner to each top risk.",
        "best_practice": "Quantified risk assessment with defined criteria, risk dashboard with KRIs, regular monitoring reports to management, automated alerts for threshold breaches.",
    },
    {
        "id": "RSK-03",
        "pillar": "Risk Management",
        "category": "Risk Integration",
        "standard": "General (S1)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "nice_to_have",
        "requirement": "Describe how sustainability risk management processes are integrated into overall risk management.",
        "internal_controls": "",
        "guidance": "Integrate sustainability risks into the enterprise risk management (ERM) framework.",
        "assurance_focus": "ERM framework showing sustainability integration.",
        "minimum_action": "Add sustainability as a risk category in your existing ERM framework. One paragraph in ERM policy describing integration is sufficient for minimum compliance.",
        "best_practice": "Full integration of sustainability risks into ERM with unified risk appetite statement, cross-functional risk committee, combined reporting to board.",
    },
    {
        "id": "RSK-04",
        "pillar": "Risk Management",
        "category": "Climate Risk",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "supporting",
        "la_priority": "important",
        "requirement": "Describe how climate-related risks are identified, assessed, and managed, including physical and transition risks.",
        "internal_controls": "",
        "guidance": "Cover both physical risks (acute/chronic) and transition risks (policy, technology, market, reputation).",
        "assurance_focus": "Climate risk assessment documentation, physical and transition risk categorization.",
        "minimum_action": "List your climate risks in two categories: physical (acute + chronic) and transition (policy, technology, market, reputation). Assess each as high/medium/low. Document in 1-2 pages.",
        "best_practice": "Quantified climate risk assessment using TCFD framework, physical risk modeling (flood, heat stress), transition risk analysis with financial impacts, mitigation strategies per risk.",
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
    },
    {
        "id": "MET-03",
        "pillar": "Metrics & Targets",
        "category": "GHG Scope 3",
        "standard": "Climate (S2)",
        "obligation": "mandatory",
        "la_scope": "not_in_initial_scope",
        "la_priority": "important",
        "requirement": "Disclose absolute gross Scope 3 greenhouse gas emissions and the categories included.",
        "internal_controls": "",
        "guidance": "Identify material Scope 3 categories. Use recognized estimation methodologies. Disclose data sources and assumptions.",
        "assurance_focus": "Category relevance assessment, calculation methodologies, data sources, assumptions.",
        "minimum_action": "Not in initial LA scope. For minimum compliance: identify which of the 15 Scope 3 categories are material to your business. Calculate at least the top 2-3 categories using industry averages. SSBJ provides a relief period for first-year reporting.",
        "best_practice": "All 15 categories assessed, material categories calculated with primary data where possible, supplier engagement program, annual improvement in data quality, science-based targeting for Scope 3.",
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
    },
]


LIMITED_ASSURANCE_CRITERIA = [
    # =========================================================================
    # INTERNAL CONTROLS REQUIRED FOR LIMITED ASSURANCE
    # Based on ISAE 3000 / ISAE 3410 / ISSA 5000 requirements
    # Focused on MINIMUM requirements for Scope 1 & 2 assurance
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
        "guidance": "Management representation letter confirming: responsibility for GHG data, completeness of emission sources, accuracy of calculations, and disclosure of all known errors.",
        "internal_controls": "Annual management representation letter template. Sign-off by appropriate management level.",
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
