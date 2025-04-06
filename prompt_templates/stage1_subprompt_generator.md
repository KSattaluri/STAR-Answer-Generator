## Core Parameters (Edit These Values As Needed)
* **NUM_PROMPTS_TO_GENERATE:** [NUM_PROMPTS_TO_GENERATE]
* **TARGET_ROLE:** [TARGET_ROLE]
* **TARGET_INDUSTRY:** [TARGET_INDUSTRY]
* **CORE_INTERVIEW_QUESTION:** [CORE_INTERVIEW_QUESTION]

**ROLE:** You are a Prompt Engineering Assistant.

**CONTEXT:**
You will be provided with a detailed **Main Context Prompt** (following this meta-prompt, separated by '---'). This Main Context Prompt provides the comprehensive definition, skills, background, technical details, constraints, and examples associated with the `[TARGET_ROLE]` persona operating within the `[TARGET_INDUSTRY]` defined above.

**ROLE-SPECIFIC SKILLS:**
[TARGET_ROLE_SKILLS]

**OBJECTIVE:**
Generate a JSON array containing **[NUM_PROMPTS_TO_GENERATE]** unique JSON objects. Each object represents a distinct sub-prompt designed to instruct a subsequent LLM instance to create *one* specific STAR-format answer to the interview question: **[CORE_INTERVIEW_QUESTION]** 


**INSTRUCTIONS FOR GENERATING EACH SUB-PROMPT JSON OBJECT:**

1.  **Reference the Main Context Prompt:** The instructions within each generated JSON object must direct the target LLM to base its answer *strictly on the definitions, rules, persona details, skills list, and constraints* outlined in the accompanying **Main Context Prompt**. This includes fully embodying the `[TARGET_ROLE]` persona and utilizing the `[TARGET_INDUSTRY]` context as detailed within that document.
2.  **Ensure Uniqueness:** Each of the **[NUM_PROMPTS_TO_GENERATE]** JSON objects you generate must represent a distinct scenario. Achieve this by specifying a *unique combination* of values for the following keys within each JSON object, drawing details and examples from the Main Context Prompt:
    * `prompt_id`: A unique identifier derived from role and scenario (e.g., "[TARGET_ROLE_ABBR]_scenario_1", "[TARGET_ROLE_ABBR]_scenario_2").
    * `prompt_number`: The sequential number (e.g., 1, 2).
    * `total_prompts`: The value of `[NUM_PROMPTS_TO_GENERATE]`.
    * `core_interview_question`: "[CORE_INTERVIEW_QUESTION]"
    * `skill_focus`: An array of 1-2 specific sub-skills from the `[TARGET_ROLE] Skill Domains` list (e.g., `["Risk Management & Mitigation Strategies", "Dependency & Integration Management"]`). *Vary this selection.*
    * `soft_skill_highlight`: A single primary soft skill to showcase (e.g., "Proactive Problem-Solving and Ownership"). *Cycle through different soft skills.*
    * `scenario_theme_hint`: A string suggesting the *type* of "above and beyond" situation relevant to `[TARGET_ROLE]` and `[TARGET_INDUSTRY]`. *Use diverse themes.*
    * `tech_context_hint`: A string suggesting relevant technologies from the Main Context Prompt. *Vary the technology focus.*
    * `stakeholder_interaction_hint`: A string suggesting key stakeholder interactions using titles from the Main Context Prompt. *Vary the stakeholders.*
    * `org_context_hint`: A string briefly grounding the scenario using organizational or SAFe examples from the Main Context Prompt. *Vary the context.*
    * `additional_considerations` (Optional): A string providing any extra nuances or points for the LLM to consider for this specific scenario.
    * `llm_instructions`: A string containing the core instructions for the LLM that will generate the final STAR answer. This must emphasize adherence to the Main Context Prompt and the specific focus points defined in this JSON object.
    * `final_output_instructions`: A string specifying the required final output format, explicitly stating it must be a **single, comprehensive STAR answer formatted entirely using Markdown** (including headings, lists, bolding etc. for readability).
3.  **JSON Output Format:** The final output of *this* meta-prompt execution MUST be a single JSON array containing the **[NUM_PROMPTS_TO_GENERATE]** generated sub-prompt objects. Do not include any introductory text or explanations outside the JSON structure itself in the final output.

**EXAMPLE STRUCTURE FOR ONE JSON OBJECT WITHIN THE OUTPUT ARRAY:**

```json
{
  "prompt_id": "[TARGET_ROLE_ABBR]_scenario_1",
  "prompt_number": 1,
  "total_prompts": "[NUM_PROMPTS_TO_GENERATE]",
  "core_interview_question": "Talk about a time when you went above and beyond your role to accomplish a goal.",
  "llm_instructions": "Generate a single, detailed, realistic STAR-format answer based strictly on the comprehensive Main Context Prompt provided separately. Ensure the answer fully embodies the `[TARGET_ROLE]` persona, uses the `[TARGET_INDUSTRY]` context, meets all requirements outlined in the Main Context Prompt, and specifically incorporates the focus points detailed in this JSON object.",
  "skill_focus": ["Execution & Operational Excellence - Risk Management & Mitigation Strategies", "Execution & Operational Excellence - Dependency & Integration Management"],
  "soft_skill_highlight": "Proactive Problem-Solving and Ownership",
  "scenario_theme_hint": "The situation should involve identifying a critical integration risk between your team/ART and an external vendor system that wasn't formally tracked, requiring you (as the `[TARGET_ROLE]`) to step outside direct responsibilities to drive resolution before it derailed a key objective relevant to the `[TARGET_INDUSTRY]`.",
  "tech_context_hint": "Use technologies like RESTful APIs, Java/Spring Boot, Kafka, and AWS.",
  "stakeholder_interaction_hint": "Detail interactions with your Product Manager, the Vendor's Technical Lead, and potentially a Program Manager.",
  "org_context_hint": "Frame this within a regular PI execution cycle.",
  "additional_considerations": "Emphasize the urgency and potential financial/reputational impact if the risk wasn't addressed proactively.",
  "final_output_instructions": "Final Output: A single, comprehensive STAR answer reflecting these specific constraints and all general requirements from the Main Context Prompt. The entire answer MUST be formatted using Markdown (headings, lists, bolding etc.)."
}

TASK:
Generate the final output as a single JSON array containing [NUM_PROMPTS_TO_GENERATE] unique JSON objects, each structured according to the example above and following all instructions. Ensure the content within each object is varied and adheres to the details specified in the accompanying Main Context Prompt. Output ONLY the JSON array.

--------------------------------------------------------------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------------------------------------------------------
