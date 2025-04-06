# Situation

As the Product Owner for our core Lending Platform—a complex system built on Java microservices, using Kafka for event streaming, deployed on AWS, and integrating with legacy mainframe systems—we were heading into a critical Program Increment (PI) Planning session for the Lending Solutions Agile Release Train (ART). Capacity was known to be constrained, yet we faced three competing, high-priority demands, each championed by influential stakeholders and initially positioned as non-negotiable 'must-haves' for the upcoming PI:

1.  **Mandatory Regulatory Compliance:** A new CFPB reporting requirement had a non-negotiable deadline just six months away (spanning two PIs). Failure to comply carried the risk of substantial daily fines (estimated $50k/day) and significant reputational damage. This was driven by the Regulatory Compliance Officer.
2.  **High-Potential Revenue Feature:** The Sales Director was aggressively pushing for a new automated underwriting feature for Small-to-Medium Business (SMB) loans, projected to generate $5M in new Annual Recurring Revenue (ARR) within the first year. Sales saw this as critical to hitting their annual targets.
3.  **Critical Technical Debt Remediation:** The Enterprise Architect had flagged severe performance bottlenecks and stability risks associated with our aging mainframe integration layer. Recent minor outages were traced back to this layer, and failure to address it threatened platform stability and would significantly hinder future development velocity, including the scalability of the proposed revenue feature.

The Head of Lending Products, our primary Business Sponsor, expected a plan that maximized overall business value while ensuring platform stability and compliance. The Development Team Lead confirmed that delivering the full scope of all three initiatives within the PI's capacity was impossible.

# Task

My primary responsibility was to navigate this complex situation, characterized by conflicting priorities and limited capacity. I needed to perform a rigorous, data-driven assessment of these three critical initiatives, facilitate a difficult but necessary prioritization decision, gain alignment from all key stakeholders (Head of Lending Products, Regulatory Compliance Officer, Sales Director, Enterprise Architect, Dev Team Lead/Scrum Master), and ultimately define a realistic, high-value scope for the PI. This required decisive leadership, strong business acumen, sophisticated prioritization skills, and transparent communication to manage expectations effectively.

# Action

1.  **Data Gathering & Objective Analysis:** I initiated deep dives into each initiative:
    *   **Regulatory:** Met with the Compliance Officer and Legal to confirm the exact deadline, define the Minimum Viable Compliance Product (MVCP), and quantify the financial ($50k/day fine) and reputational risks precisely. Confirmed the deadline was immutable.
    *   **Revenue Feature:** Collaborated with the Sales Director and Finance team to scrutinize the $5M ARR forecast, understand dependencies, define a phased rollout starting with an MVP, and calculate the Cost of Delay using qualitative (market window) and quantitative inputs.
    *   **Technical Debt:** Partnered with the Enterprise Architect and Development Team Lead. We analyzed system logs, incident reports, and performance metrics (e.g., P95 latency for mainframe lookups) to quantify the stability risk (projected increase in outage frequency/duration) and the impact on future development velocity (estimated 20% slowdown). We defined the scope for essential remediation versus a full rewrite.

2.  **Prioritization Framework Implementation:** Recognizing the need for an objective method, I adapted the Weighted Shortest Job First (WSJF) framework. I tailored the components to our specific context:
    *   **User/Business Value:** Included potential revenue ($5M), cost avoidance (fines, reputational repair costs), and operational efficiency gains/risk reduction from tech debt.
    *   **Time Criticality:** Assessed urgency based on the regulatory deadline, market window for the revenue feature, and the escalating risk profile of the tech debt.
    *   **Risk Reduction/Opportunity Enablement:** Quantified the reduction in compliance/stability risk and the degree to which each item enabled future strategic initiatives (e.g., tech debt enabling faster feature delivery).
    *   **Job Size (Effort):** Obtained realistic story point estimates from the Development Team for the MVP/essential scope of each item.
    *   **Strategic Weighting:** Applied a multiplier emphasizing regulatory mandates and platform stability, reflecting directives from the Head of Lending Products and enterprise strategy.

3.  **Stakeholder Engagement & Facilitation:**
    *   Conducted individual sessions with each stakeholder to understand their non-negotiables, minimum viable scope, and underlying concerns.
    *   Convened a cross-functional workshop presenting the collated data, the adapted WSJF model, the inputs gathered, and the resulting scores in a transparent manner. I used visuals like a 2x2 matrix plotting value/risk vs. effort.
    *   Facilitated a structured discussion focused on the *relative* priorities based on the data and agreed framework, acknowledging the importance of all requests but emphasizing the capacity constraint and the need for trade-offs for the overall good of the ART and the business. I framed the tech debt not just as a cost but as an investment in future velocity and stability, directly impacting our ability to deliver *more* revenue features reliably later.

4.  **Decision & Communication:**
    *   The adapted WSJF scoring clearly prioritized the Regulatory Compliance feature (highest Time Criticality and Risk Reduction) followed closely by the critical Technical Debt remediation (high Risk Reduction and Opportunity Enablement, impacting future value). The Revenue Feature, while high value, had lower Time Criticality relative to the others for this specific PI.
    *   I presented this data-driven recommendation to the Head of Lending Products, explaining the rationale, the risks mitigated, and the plan for the deferred item. I highlighted how addressing tech debt now would de-risk and potentially accelerate the revenue feature's future rollout.
    *   After securing their buy-in, I communicated the decision clearly and transparently to all stakeholders in a follow-up meeting. I explicitly addressed the Sales Director's concerns, acknowledging the revenue impact but committing to prioritizing the revenue feature's MVP in the *next* PI, contingent on successful delivery of the current PI scope and demonstrating how the tech debt work would create a more stable foundation for it.

5.  **Backlog Execution:** I worked closely with the Development Team Lead/Scrum Master to refine the User Stories and Enablers for the regulatory and tech debt items, ensuring they were well-understood and ready for PI Planning.

# Result

*   **Successful Prioritization & Delivery:** The PI scope was finalized with the Regulatory Compliance feature and the Technical Debt remediation as the top priorities. Both were successfully delivered within the PI.
*   **Compliance Achieved:** The regulatory reporting feature went live ahead of the deadline, avoiding significant fines (~$1.5M potential fines averted for the first month alone) and reputational damage, satisfying the Compliance Officer.
*   **Improved Stability & Velocity:** The tech debt remediation led to a measurable 35% reduction in related production incidents and a 15% improvement in key API response times within two months post-release, validating the Architect's concerns and enabling faster subsequent development.
*   **Stakeholder Alignment & Trust:** Despite the initial conflict and the difficult trade-off impacting the revenue feature's timeline, the transparent, data-driven approach maintained stakeholder trust. The Sales Director, while initially disappointed, appreciated the clear rationale and the concrete plan for the feature in the following PI. Expectations were managed effectively.
*   **Predictable Execution:** The ART executed the PI predictably, meeting its commitments due to the clear focus and realistic scope.
*   **Demonstrated Leadership:** This process showcased decisive and accountable leadership by navigating ambiguity, making tough, data-backed trade-offs aligned with broader business strategy (compliance and stability first), and ensuring transparent communication, ultimately optimizing value delivery and risk management for the Lending Platform. The revenue feature MVP was subsequently prioritized and delivered successfully in the next PI.