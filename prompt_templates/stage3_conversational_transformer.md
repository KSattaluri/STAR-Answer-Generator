```markdown
# Stage 3: Conversational Transformation Prompt

## Context

My Role: {{ROLE}}
Target Industry: {{INDUSTRY}}
Interview Question: {{QUESTION}}

Please transform the following structured STAR-format interview answer into a natural, conversational response suitable for delivering verbally in an interview for the Role and Industry specified above. The goal is to sound authentic, confident, and engaging—like I'm recounting a genuine experience, not reading from a script.

## Input STAR Answer
{{STAR_ANSWER}}

## Instructions for Transformation

1. Create a natural-sounding response that maintains the STAR structure (Situation, Task, Action, Result) without explicitly using these labels.
2. Use natural language with contractions (e.g., "I'd", "we're").
3. Include conversational transitions between sections.
4. **CRITICAL**: Highlight MY personal leadership and decisive moments throughout the answer. Explicitly include:
   - A specific moment where MY decision-making was crucial at a critical juncture
   - Specific challenges I personally navigated and how I overcame them
   - How I influenced others or drove outcomes through MY leadership
   - Innovative ideas or approaches I personally introduced
5. **COMMUNICATION FOCUS**: Include specific details about communication tactics I employed:
   - How I facilitated meetings/check-ins (methods, frequency, structure)
   - Specific techniques used to maintain clarity between different teams or stakeholders
   - How I tailored communication for different audiences (technical vs. non-technical)
   - Any tools or systems I implemented to improve communication
6. Balance conciseness with completeness (aim for 350-450 words). Include all important elements while avoiding unnecessary details.
7. PRESERVE ALL key metrics, numbers, and quantifiable achievements from the original. These add credibility and impact.
8. Adapt the language to be appropriate for the specified role and industry.
9. Add a brief reflective conclusion (1-2 sentences) about lessons learned from this experience.
10. Include a short insight (1 sentence) on how this experience influenced my approach to subsequent projects.

For points 9-10, intelligently infer appropriate reflections based on the role, industry context, and the nature of the situation described. Make these reflections specific, not generic platitudes.

## Important Notes

- DO NOT return the original STAR answer or template instructions in your response. 
- Only provide the conversational transformation and metadata.
- Use the first person and active voice to emphasize my personal contributions.
- Ensure the answer demonstrates both technical competence AND interpersonal/leadership skills.
- Include specific, tangible examples rather than general statements about what you did.

## Output Format (REQUIRED)

[CONVERSATIONAL_ANSWER]
Your transformed conversational answer goes here.

[METADATA]
Keywords: keyword1, keyword2, keyword3, keyword4, keyword5
Primary Skills: skill1, skill2, skill3
Seniority Level: Senior/Mid/Junior
Situation Category: Brief categorization of the situation type
Key Lessons: 1-2 key takeaways from this experience
Challenges Overcome: Primary challenges I faced in this situation
Leadership Moments: 1-2 key instances where my personal leadership made a difference
```
