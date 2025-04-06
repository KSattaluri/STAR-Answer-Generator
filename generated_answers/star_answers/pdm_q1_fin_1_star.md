# Situation

In my role as a Product Manager for the Retail Banking Mobile App at [Previous Bank Name], I was responsible for optimizing key user journeys to drive customer acquisition and engagement. During Q3 of last year, we observed that while the overall number of users starting the new checking account opening process in the app was healthy, the final conversion rate (from application start to account funded) was consistently falling short of our quarterly target by about 15%. Our primary KPI was this end-to-end conversion rate. Initial funnel analysis using Amplitude revealed a particularly sharp drop-off – approximately 35% – occurring specifically at the 'Identity Verification' step, significantly higher than industry benchmarks or our own web platform's performance for the same step. This indicated a critical friction point within the mobile experience that needed immediate attention.

# Task

My primary task was to diagnose the root cause of the high drop-off rate at the mobile 'Identity Verification' stage and improve the step's completion rate, ultimately aiming to increase the overall checking account opening conversion rate by at least 10% within the next quarter (Q4). This involved leading a cross-functional team to analyze user behavior, formulate data-backed hypotheses, design and execute A/B tests, and implement the most effective solution. Success would be measured by the increase in the 'Identity Verification' step completion rate and the subsequent impact on the overall funnel conversion KPI.

# Action

1.  **Deep Dive Analysis:** I initiated a deep dive collaborating closely with our Data Analyst.
    *   We used Amplitude to segment users dropping off at the ID verification step by device type, OS version, time of day, and previous behavior within the app.
    *   I personally reviewed session recordings (using FullStory) for users who failed this step, observing struggles with aligning their ID card, unclear feedback messages, and multiple failed attempts before abandoning the process.
    *   I wrote SQL queries against our backend application logs database to analyze specific error codes returned during the ID verification process. This revealed a high incidence of errors related to "poor image quality" and intermittent API timeout errors from our third-party identity verification vendor, especially during peak usage hours.

2.  **Hypothesis Formulation:** Based on the combined quantitative data (Amplitude funnel, SQL error logs) and qualitative insights (session recordings), we formulated two primary hypotheses:
    *   *Hypothesis 1:* Improving the user interface (UI) for ID document capture with clearer instructions, real-time feedback, and potentially auto-capture functionality would reduce image quality errors and increase successful submissions.
    *   *Hypothesis 2:* Providing clearer user feedback during the API call to the verification vendor, potentially including a progress indicator or managing expectations about processing time, would reduce abandonment due to perceived slowness or timeouts.

3.  **Experiment Design & Execution:**
    *   Focusing on Hypothesis 1 first due to its direct link to the most frequent error code ("poor image quality") and feasibility, I worked with our UX Designer to design a new ID capture interface (Variation B). This variation included an overlaid guide, real-time edge detection feedback (changing border color), explicit tips for lighting, and an auto-capture feature once the ID was correctly aligned. The existing interface served as the Control (Variation A).
    *   I collaborated with the Mobile Engineering Lead to scope the implementation effort for Variation B within our native iOS and Android apps. We planned to use our A/B testing platform (Firebase A/B Testing) to split traffic.
    *   We defined the primary metric as the completion rate of the 'Identity Verification' step (users successfully submitting verifiable images). Secondary metrics included the overall funnel conversion rate, time spent on the step, number of capture attempts per user, and the specific rate of "poor image quality" errors logged via SQL.
    *   We configured the A/B test to run for three weeks, targeting 50% of new users entering the account opening flow, ensuring we reached statistical significance (95% confidence level).
    *   Simultaneously, I initiated discussions with Engineering regarding Hypothesis 2, asking them to investigate potential optimizations for the API call handling and latency monitoring, preparing for a potential follow-up experiment.

4.  **Monitoring & Analysis:** During the three-week experiment, I monitored the results daily via Firebase and Amplitude dashboards. We held brief daily stand-ups with Engineering to ensure the test was running smoothly and check for any unintended technical side effects. After the test concluded, I worked with the Data Analyst to perform a rigorous statistical analysis of the results.

# Result

The A/B test yielded conclusive, positive results:
*   **Variation B (New UI) demonstrated a statistically significant 18% increase in the completion rate for the 'Identity Verification' step compared to the Control group (Variation A).** The confidence level was well above 95%.
*   The occurrence of "poor image quality" errors, tracked via our backend logs (SQL), decreased by 30% for users in the Variation B group.
*   Secondary metrics also showed positive trends: the average number of capture attempts decreased, and crucially, **the overall end-to-end checking account opening conversion rate saw an uplift of 11% for users exposed to Variation B.**
*   Based on this clear, data-driven evidence, I made the decision to roll out Variation B to 100% of our mobile user base.
*   I presented these findings, the analysis, and the rollout decision to key stakeholders, including the Head of Retail Banking and Marketing leadership, highlighting the direct positive impact on our core acquisition KPI.
*   The successful rollout directly contributed to exceeding our revised Q4 target for new mobile checking account openings. This data-driven approach not only fixed a critical friction point but also reinforced the value of continuous analysis and experimentation within the product development lifecycle. We subsequently prioritized further work on optimizing the API interaction based on the initial SQL findings and the success of this first experiment.