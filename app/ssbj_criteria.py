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
- guidance: Guidance on what good practice looks like
- assurance_focus: What a limited assurance reviewer would look for
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


SSBJ_CRITERIA = [
    # =========================================================================
    # GOVERNANCE
    # =========================================================================
    {
        "id": "GOV-01",
        "pillar": "Governance",
        "category": "Board Oversight",
        "standard": "General (S1)",
        "requirement": "Disclose information about the governance body(ies) or individual(s) responsible for oversight of sustainability-related risks and opportunities.",
        "guidance": "Identify specific board committees or members with sustainability oversight responsibilities. Document their mandate, authority, and reporting lines.",
        "assurance_focus": "Evidence of formal board mandate, committee terms of reference, and documented oversight activities.",
    },
    {
        "id": "GOV-02",
        "pillar": "Governance",
        "category": "Board Oversight",
        "standard": "General (S1)",
        "requirement": "Describe how the governance body's responsibilities for sustainability-related risks and opportunities are reflected in terms of reference, board mandates, and other related policies.",
        "guidance": "Ensure board charters, committee mandates, and corporate governance policies explicitly reference sustainability oversight responsibilities.",
        "assurance_focus": "Documented policies and terms of reference that explicitly include sustainability. Evidence of regular review and updates.",
    },
    {
        "id": "GOV-03",
        "pillar": "Governance",
        "category": "Board Competence",
        "standard": "General (S1)",
        "requirement": "Describe how the governance body ensures that appropriate skills and competencies are available to oversee sustainability strategies.",
        "guidance": "Document board member qualifications related to sustainability. Establish training programs for governance bodies on sustainability topics.",
        "assurance_focus": "Board skills matrix, training records, external advisor engagements related to sustainability.",
    },
    {
        "id": "GOV-04",
        "pillar": "Governance",
        "category": "Management Role",
        "standard": "General (S1)",
        "requirement": "Describe management's role in governance processes, controls, and procedures used to monitor, manage, and oversee sustainability-related risks and opportunities.",
        "guidance": "Define management roles with sustainability responsibilities. Establish internal sustainability committees or working groups with clear reporting to the board.",
        "assurance_focus": "Organizational charts, role descriptions, evidence of management reporting to the board on sustainability matters.",
    },
    {
        "id": "GOV-05",
        "pillar": "Governance",
        "category": "Management Role",
        "standard": "Climate (S2)",
        "requirement": "Disclose how climate-related risks and opportunities are factored into management's decision-making, including whether dedicated climate roles or committees exist.",
        "guidance": "Establish climate-specific roles or integrate climate considerations into existing management processes. Document how climate factors influence capital allocation and strategic decisions.",
        "assurance_focus": "Evidence of climate considerations in management meeting minutes, investment decisions, and strategic planning documents.",
    },
    # =========================================================================
    # STRATEGY
    # =========================================================================
    {
        "id": "STR-01",
        "pillar": "Strategy",
        "category": "Risks & Opportunities Identification",
        "standard": "General (S1)",
        "requirement": "Disclose the sustainability-related risks and opportunities that could reasonably be expected to affect the entity's prospects.",
        "guidance": "Conduct a comprehensive assessment of sustainability-related risks and opportunities across short, medium, and long-term horizons. Consider both financial and operational impacts.",
        "assurance_focus": "Documented risk and opportunity register, methodology for identification, and time horizons applied.",
    },
    {
        "id": "STR-02",
        "pillar": "Strategy",
        "category": "Business Model Impact",
        "standard": "General (S1)",
        "requirement": "Describe the current and anticipated effects of sustainability-related risks and opportunities on the entity's business model and value chain.",
        "guidance": "Map sustainability risks and opportunities to specific elements of the business model (inputs, activities, outputs, outcomes). Assess value chain dependencies and impacts.",
        "assurance_focus": "Value chain mapping, documented business model impact assessment, evidence of stakeholder engagement in the assessment.",
    },
    {
        "id": "STR-03",
        "pillar": "Strategy",
        "category": "Financial Impact",
        "standard": "General (S1)",
        "requirement": "Describe the current and anticipated effects of sustainability-related risks and opportunities on the entity's financial position, financial performance, and cash flows.",
        "guidance": "Quantify financial impacts where possible. Use scenario analysis to assess potential future impacts. Connect sustainability risks to financial statement line items.",
        "assurance_focus": "Financial impact quantification methodology, assumptions used, connection to financial planning processes.",
    },
    {
        "id": "STR-04",
        "pillar": "Strategy",
        "category": "Climate Scenario Analysis",
        "standard": "Climate (S2)",
        "requirement": "Describe climate-related scenario analysis, including scenarios used and the resilience of the entity's strategy.",
        "guidance": "Use at least two scenarios including one consistent with 1.5°C. Document assumptions, time horizons, and analytical approach. Assess both physical and transition risks.",
        "assurance_focus": "Scenario selection rationale, methodology documentation, evidence of board/management review of scenario results.",
    },
    {
        "id": "STR-05",
        "pillar": "Strategy",
        "category": "Transition Plan",
        "standard": "Climate (S2)",
        "requirement": "Disclose the entity's climate-related transition plan, including targets and actions to achieve them.",
        "guidance": "Document a credible transition plan with specific milestones, capital expenditure plans, and timelines. Align with the entity's overall strategy and financial planning.",
        "assurance_focus": "Documented transition plan, evidence of board approval, integration with capital budgeting, progress tracking mechanisms.",
    },
    {
        "id": "STR-06",
        "pillar": "Strategy",
        "category": "Strategy Resilience",
        "standard": "General (S1)",
        "requirement": "Describe the resilience of the entity's strategy and business model to sustainability-related risks, considering the entity's capacity to adapt.",
        "guidance": "Assess the adaptability of the business model under different scenarios. Identify key dependencies and vulnerabilities. Document response strategies.",
        "assurance_focus": "Documented resilience assessment, evidence of strategic review incorporating sustainability scenarios.",
    },
    # =========================================================================
    # RISK MANAGEMENT
    # =========================================================================
    {
        "id": "RSK-01",
        "pillar": "Risk Management",
        "category": "Risk Identification Process",
        "standard": "General (S1)",
        "requirement": "Describe the processes used to identify sustainability-related risks and opportunities.",
        "guidance": "Establish a formal process for identifying sustainability risks, including environmental scanning, stakeholder engagement, and materiality assessment. Define roles and frequencies.",
        "assurance_focus": "Documented risk identification methodology, evidence of regular execution, stakeholder engagement records.",
    },
    {
        "id": "RSK-02",
        "pillar": "Risk Management",
        "category": "Risk Assessment Process",
        "standard": "General (S1)",
        "requirement": "Describe the processes used to assess, prioritize, and monitor sustainability-related risks.",
        "guidance": "Use consistent criteria for assessing likelihood and impact. Prioritize risks based on severity. Establish monitoring and escalation procedures.",
        "assurance_focus": "Risk assessment criteria, risk registers with prioritization, evidence of monitoring activities and escalation.",
    },
    {
        "id": "RSK-03",
        "pillar": "Risk Management",
        "category": "Risk Integration",
        "standard": "General (S1)",
        "requirement": "Describe how sustainability-related risk management processes are integrated into the entity's overall risk management.",
        "guidance": "Integrate sustainability risks into the enterprise risk management (ERM) framework. Ensure sustainability risks are considered alongside financial and operational risks.",
        "assurance_focus": "ERM framework documentation showing sustainability integration, evidence of combined risk reporting.",
    },
    {
        "id": "RSK-04",
        "pillar": "Risk Management",
        "category": "Climate Risk Process",
        "standard": "Climate (S2)",
        "requirement": "Describe how climate-related risks are identified, assessed, and managed, including physical and transition risks.",
        "guidance": "Conduct specific climate risk assessments covering both physical risks (acute and chronic) and transition risks (policy, technology, market, reputation). Use recognized frameworks.",
        "assurance_focus": "Climate-specific risk assessment documentation, physical and transition risk categorization, evidence of management response plans.",
    },
    {
        "id": "RSK-05",
        "pillar": "Risk Management",
        "category": "Internal Controls",
        "standard": "General (S1)",
        "requirement": "Establish internal controls over sustainability-related data collection, processing, and reporting.",
        "guidance": "Design and implement controls over sustainability data comparable to financial reporting controls. Include data validation, reconciliation, and review procedures.",
        "assurance_focus": "Documented control framework, evidence of control testing, data quality procedures, segregation of duties.",
    },
    # =========================================================================
    # METRICS & TARGETS
    # =========================================================================
    {
        "id": "MET-01",
        "pillar": "Metrics & Targets",
        "category": "GHG Emissions - Scope 1",
        "standard": "Climate (S2)",
        "requirement": "Disclose absolute gross Scope 1 greenhouse gas emissions.",
        "guidance": "Measure and report Scope 1 emissions using GHG Protocol or equivalent methodology. Include all material emission sources. Use appropriate emission factors.",
        "assurance_focus": "Emission calculation methodology, source data, emission factors used, completeness of boundary, data quality checks.",
    },
    {
        "id": "MET-02",
        "pillar": "Metrics & Targets",
        "category": "GHG Emissions - Scope 2",
        "standard": "Climate (S2)",
        "requirement": "Disclose absolute gross Scope 2 greenhouse gas emissions (location-based and, if applicable, market-based).",
        "guidance": "Report both location-based and market-based Scope 2 emissions. Use appropriate grid emission factors and contractual instruments.",
        "assurance_focus": "Location-based and market-based calculations, grid factors, evidence of energy consumption data, contractual instruments.",
    },
    {
        "id": "MET-03",
        "pillar": "Metrics & Targets",
        "category": "GHG Emissions - Scope 3",
        "standard": "Climate (S2)",
        "requirement": "Disclose absolute gross Scope 3 greenhouse gas emissions and the categories included.",
        "guidance": "Identify material Scope 3 categories. Use recognized estimation methodologies. Disclose data sources, assumptions, and limitations for each category.",
        "assurance_focus": "Category relevance assessment, calculation methodologies by category, data sources, assumptions documentation, year-over-year consistency.",
    },
    {
        "id": "MET-04",
        "pillar": "Metrics & Targets",
        "category": "Climate Targets",
        "standard": "Climate (S2)",
        "requirement": "Disclose climate-related targets including GHG emission reduction targets, base year, target year, and interim milestones.",
        "guidance": "Set science-based or otherwise credible targets. Define clear base years, methodologies, and milestones. Report progress against targets annually.",
        "assurance_focus": "Target-setting methodology, base year data, progress tracking, evidence of board-approved targets.",
    },
    {
        "id": "MET-05",
        "pillar": "Metrics & Targets",
        "category": "Industry Metrics",
        "standard": "Climate (S2)",
        "requirement": "Disclose industry-specific metrics relevant to the entity's sector as applicable.",
        "guidance": "Identify and report sector-specific sustainability metrics. Consider SASB industry standards as guidance for relevant metrics.",
        "assurance_focus": "Industry metric selection rationale, calculation methodology, data sources, comparability with peers.",
    },
    {
        "id": "MET-06",
        "pillar": "Metrics & Targets",
        "category": "Sustainability Metrics",
        "standard": "General (S1)",
        "requirement": "Disclose metrics used to measure and monitor sustainability-related risks and opportunities and performance against targets.",
        "guidance": "Define KPIs for material sustainability topics. Ensure metrics are measurable, comparable, and verifiable. Track and report on progress.",
        "assurance_focus": "KPI definitions, measurement methodology, data collection processes, trend analysis, target progress reporting.",
    },
    {
        "id": "MET-07",
        "pillar": "Metrics & Targets",
        "category": "Data Quality",
        "standard": "General (S1)",
        "requirement": "Ensure the quality, completeness, and accuracy of sustainability data used for disclosure.",
        "guidance": "Implement data quality management processes. Establish data governance, validation rules, and reconciliation procedures for sustainability data.",
        "assurance_focus": "Data governance framework, validation procedures, reconciliation evidence, data lineage documentation, error correction processes.",
    },
]


LIMITED_ASSURANCE_CRITERIA = [
    {
        "id": "LA-01",
        "category": "Engagement Planning",
        "requirement": "Defined scope and subject matter for the limited assurance engagement.",
        "guidance": "Clearly define what disclosures are subject to assurance, the criteria used (SSBJ standards), and the reporting period.",
    },
    {
        "id": "LA-02",
        "category": "Internal Controls",
        "requirement": "Internal controls over sustainability reporting are designed and operating effectively.",
        "guidance": "Document the control environment for sustainability data. Include entity-level controls and process-level controls over data collection and reporting.",
    },
    {
        "id": "LA-03",
        "category": "Data Collection",
        "requirement": "Sustainability data collection processes are systematic, documented, and repeatable.",
        "guidance": "Establish clear data collection procedures, ownership, timelines, and quality checks at each stage of the data pipeline.",
    },
    {
        "id": "LA-04",
        "category": "Evidence & Documentation",
        "requirement": "Sufficient and appropriate evidence exists to support sustainability disclosures.",
        "guidance": "Maintain an audit trail for all reported data. Retain source documents, calculations, assumptions, and approvals for the assurance period.",
    },
    {
        "id": "LA-05",
        "category": "GHG Data Verification",
        "requirement": "GHG emission calculations are accurate, complete, and use appropriate methodologies and emission factors.",
        "guidance": "Verify completeness of emission sources, accuracy of activity data, appropriateness of emission factors, and correctness of calculations.",
    },
    {
        "id": "LA-06",
        "category": "Consistency & Comparability",
        "requirement": "Reporting methodologies are applied consistently across periods and disclosures are comparable.",
        "guidance": "Document and consistently apply measurement methodologies. Disclose and explain any changes in methodology, boundary, or estimation techniques.",
    },
    {
        "id": "LA-07",
        "category": "Third-Party Data",
        "requirement": "Third-party and estimated data used in disclosures is appropriately validated and disclosed.",
        "guidance": "Identify all third-party data sources. Assess reliability, validate key data points, and disclose the extent of estimation and third-party reliance.",
    },
    {
        "id": "LA-08",
        "category": "Management Representations",
        "requirement": "Management provides written representations regarding the completeness and accuracy of sustainability information.",
        "guidance": "Obtain formal management representations covering responsibility for disclosures, completeness of information, and accuracy of data provided.",
    },
    {
        "id": "LA-09",
        "category": "Process Maturity",
        "requirement": "Sustainability reporting processes demonstrate sufficient maturity for limited assurance.",
        "guidance": "Assess whether processes are formalized, consistently applied, and subject to regular review. Limited assurance typically requires at least a 'Defined' maturity level.",
    },
    {
        "id": "LA-10",
        "category": "Disclosure Completeness",
        "requirement": "All required SSBJ disclosures are addressed with sufficient detail and transparency.",
        "guidance": "Cross-reference disclosures against the full SSBJ requirement checklist. Ensure all mandatory items are addressed with appropriate qualitative and quantitative information.",
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
