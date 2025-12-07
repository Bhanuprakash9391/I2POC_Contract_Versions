from langchain.prompts import ChatPromptTemplate

idea_structuring_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert assistant that helps users clarify their contract ideas and generate specific, descriptive titles."),
    ("user", """
Please perform the following:
1. Rephrase the idea below to make it clearer, more concise, and professional, while preserving the specific legal/business context.
2. Generate one specific, descriptive title that directly reflects the core concept (max 8 words). The title should be concrete and avoid generic phrases like "Generic Contract" or "Legal Document".

Idea:\n{idea}

IMPORTANT: The title must be specific to the actual idea content. For example:
- If the idea is "create contract generation agent", the title should be something like "AI-Powered Contract Generation Agent"
- If the idea is "inventory optimization system", the title should be "Inventory Optimization Service Agreement"
- Avoid generic titles that don't reflect the specific idea

Respond ONLY in the following JSON format:
{{
    "rephrased_idea": "...",
    "title_1": "..." 
}}
""")
])

question_generator_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are a focused question generator for Contract Documents. Analyze the section and generate ONE concise, specific question about the most important missing information."""),

    ("user", """
**Section**: {section_name}
**Purpose**: {section_purpose}
**Subsections**:
{subsections_str}

**User's AI Idea**: {user_idea}
**Current Draft**: {current_section_draft}
**Previous Q&A pertaining to the current section**:
{conversation_history}

INSTRUCTIONS:
1. Identify the SINGLE most important piece of missing information needed to advance this section
2. Generate ONE concise, focused question (max 2-3 sentences)
3. The question should be specific and easy to answer
4. Focus on the most critical information needed right now
5. Avoid asking multiple questions or covering too many topics
6. Return null if the draft is already complete and comprehensive

Return EXACTLY this JSON format if you are generating a question:
{{
    "question": {{
        "section": "<section_name>",
        "subsection": "<subsection which is missing the information>",
        "question": "<your_concise_focused_question>",
        "reason": "<Why this specific information is needed now>"
     }}
}}
If all information is present and the section is complete, you will return the output in the following JSON format:
{{
  "question": null,
}} 
""")
])


draft_generator_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a Draft Generator Agent updating a Contract Document. Focus on legal clarity, business terms, and compliance requirements."),
    ("user", """
You are a Draft Generator Agent updating the draft for the "{section_name}" section of a Contract Document. 
The section's purpose is: {section_purpose}.
The current draft is: {current_section_draft}.
The following question-answer pair pertains to the subsection: {subsection_name} (definition: {subsection_definition}):

Question-Answer Pair: {question_answer_pair}

**Contract Type Context:**
- Contract Type: {contract_type}
- Formatting Guidelines: {formatting_guidelines}

Instructions:
1. Update the current draft by incorporating the provided answer into the relevant subsection.
2. Use formal legal language appropriate for the specified contract type.
3. Follow the formatting guidelines provided for this contract type.
4. Ensure the updated draft maintains proper legal structure and terminology.
5. Include standard legal clauses and provisions as appropriate for the contract type.
6. Use defined terms in quotes on first use and maintain consistency.
7. If the subsection is not yet present in the draft, create a new paragraph for it using proper legal formatting.
8. Return the updated draft in the following JSON format:
   {{
     "section": "<section_name>",
     "draft": "<updated_draft_text>",
   }}
""")
])
