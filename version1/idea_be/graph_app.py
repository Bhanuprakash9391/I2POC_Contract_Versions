from langgraph.types import interrupt
from langgraph.graph import END, StateGraph
import re
from difflib import SequenceMatcher


from prompt_templates import idea_structuring_prompt, question_generator_prompt_template, draft_generator_prompt_template
from schema import IdeaStructuringOutput, GraphState, Subsection, OptionalQuestionOutput, ConversationEntry, DraftOutput
from constants import SECTIONS, IDEA_STRUCTURING_NODE, IDEA_STRUCTURING_REVIEW_NODE, INITALIZE_STATE_NODE, SECTION_SELECTOR_NODE, CRITIC_QUESTION_NODE, MAX_QUESTIONS_PER_SECTION, USER_INPUT_DRAFT_GENERATOR_NODE, SECTION_REVIEW_NODE, FINAL_REVIEW_NODE
from config import llm, memory
from ai_contract_categorization_service import ai_contract_categorization_service
from ai_contract_scoring_service import ai_contract_scoring_service

def is_question_similar(new_question: str, existing_questions: list, similarity_threshold: float = 0.7) -> bool:
    """
    Check if a new question is too similar to existing questions.
    Uses string similarity comparison to detect similar phrasing.
    """
    if not existing_questions:
        return False
    
    # Normalize the new question
    new_question_normalized = re.sub(r'[^\w\s]', '', new_question.lower()).strip()
    
    for existing_question in existing_questions:
        # Normalize existing question
        existing_normalized = re.sub(r'[^\w\s]', '', existing_question.lower()).strip()
        
        # Calculate similarity ratio
        similarity = SequenceMatcher(None, new_question_normalized, existing_normalized).ratio()
        
        if similarity > similarity_threshold:
            print(f"⚠️ Question similarity detected: {similarity:.2f}")
            print(f"   New: {new_question}")
            print(f"   Existing: {existing_question}")
            return True
    
    return False

async def idea_structuring_helper_node(idea: str) -> tuple[str, str]:
    try:
        messages = idea_structuring_prompt.format_messages(idea=idea)

        structured_llm = llm.with_structured_output(IdeaStructuringOutput, method="json_mode")
        result = await structured_llm.ainvoke(messages)

        print("\n=== REPHRASED IDEA ===")
        print(result.rephrased_idea)
        print("=== TITLE ===")
        print(result.title_1)

        return result.rephrased_idea, result.title_1

    except Exception as e:
        print(f"❌ Error in rephrasing and title generation: {e}")
        return idea, ""
    
async def idea_structuring_node(state: GraphState) -> GraphState:
    print("\n=== IDEA STRUCTURING ===")
    
    # Validate input
    if not state.idea or state.idea.strip() == "":
        print("⚠️ No idea provided - using default structure")
        state.idea = "Please provide a contract idea or description"
        state.title = "Contract Document"
        state.contract_type = "Commercial_Contracts"
        state.formatting_guidelines = "Use standard legal contract format with formal language and defined terms."
        state.sections = [
            {"section_heading": section["section_heading"], "section_purpose": section["section_purpose"], "subsections": section["subsections"]}
            for section in SECTIONS
        ]
        return state
    
    idea, title = await idea_structuring_helper_node(state.idea)
    
    # Determine contract type using AI categorization
    try:
        contract_data = {
            "title": title,
            "original_idea": state.idea,
            "rephrased_idea": idea,
            "department": "Legal"  # Default department
        }
        categorization_result = await ai_contract_categorization_service.categorize_contract(contract_data)
        
        state.contract_type = categorization_result["primary_category"]
        state.formatting_guidelines = categorization_result["legal_formatting_guidelines"]
        
        print(f"📋 Contract Type Identified: {state.contract_type}")
        print(f"📝 Formatting Guidelines: {state.formatting_guidelines}")
        
        # Use recommended sections from AI categorization if available
        if categorization_result.get("recommended_sections"):
            sections = []
            for i, section_name in enumerate(categorization_result["recommended_sections"]):
                sections.append({
                    "section_heading": section_name,
                    "section_purpose": f"Standard {section_name} section for {state.contract_type}",
                    "subsections": [
                        {"subsection_heading": "Details", "subsection_definition": f"Provide specific details for {section_name}"}
                    ]
                })
        else:
            # Fallback to default sections
            sections = [
                {"section_heading": section["section_heading"], "section_purpose": section["section_purpose"], "subsections": section["subsections"]}
                for section in SECTIONS
            ]
    except Exception as e:
        print(f"⚠️ Contract categorization failed, using default sections: {e}")
        sections = [
            {"section_heading": section["section_heading"], "section_purpose": section["section_purpose"], "subsections": section["subsections"]}
            for section in SECTIONS
        ]
        state.contract_type = "Commercial_Contracts"
        state.formatting_guidelines = "Use standard legal contract format with formal language and defined terms."

    state.idea = idea
    state.title = title
    state.sections = sections

    return state
async def idea_structuring_review_node(state: GraphState) -> GraphState:
    print("\n=== IDEA STRUCTURING REVIEW ===")
    
    user_response = interrupt({
        "action": "get_structure_review",
        "idea": state.idea,
        "title": state.title,
        "all_sections": state.sections
    })
    print(f"\n=== USER RESPONSE ===\n{user_response}")
    state.idea = user_response["idea"]
    state.title = user_response["title"]
    state.sections = user_response["all_sections"]

    return state
    
async def intiliaze_graph_state(state: GraphState,) -> GraphState:
    print("\n=== INITIALIZING GRAPH STATE ===")
    sections = state.sections
    print(f"\n=== SECTIONS ===\n{sections}")
    # Set progress and drafts for each section
    state.progress = {section["section_heading"]: "Not Started" for section in sections}
    state.all_drafts = {section["section_heading"]: "" for section in sections}

    # Set first section and its subsections
    first_section_data = sections[0]
    state.current_section = first_section_data["section_heading"]
    state.current_subsections = [
        Subsection(subsection_heading=sub["subsection_heading"], subsection_definition=sub["subsection_definition"])
        for sub in first_section_data["subsections"]
    ]

    return state

async def section_selector_node(state: GraphState) -> GraphState:
    print("\n=== SECTION SELECTOR ===")
    
    current_section_name = state.current_section
    
    current_idx = next(i for i, section in enumerate(state.sections) 
                      if section["section_heading"] == current_section_name)
    next_idx = current_idx + 1

    if next_idx >= len(state.sections):
        # Document completion case
        print(f"\n🎉 All sections complete! Document ready for finalization.")
        state.current_section = None
        state.current_subsections = []
        state.current_section_draft = None
        return state
        
    elif state.progress[current_section_name] == "Complete":
        # Transition to next section
        next_section = state.sections[next_idx]
        print(f"\nTransitioning from {current_section_name} to {next_section['section_heading']}")
        state.current_section = next_section["section_heading"]
        state.current_subsections = [
            Subsection(subsection_heading=sub["subsection_heading"], subsection_definition=sub["subsection_definition"])
            for sub in next_section["subsections"]
        ]
        state.current_section_draft = None
        state.question_generator_output = None
        state.progress[next_section["section_heading"]] = "In Progress"
    
    elif state.progress[current_section_name] == "Not Started":
        state.progress[current_section_name] = "In Progress"
        state.current_section_draft = None
        state.question_generator_output = None
    
    return state

def determine_next_node_after_section_selector(state: GraphState) -> str:
    if state.current_section is None:
        print("📄 All sections done — moving to FINAL REVIEW")
        return FINAL_REVIEW_NODE
    
    print(f"➡️ Starting next section: {state.current_section}")
    return CRITIC_QUESTION_NODE

async def critic_and_question_generator_node(state: GraphState) -> GraphState:
    print(f"====CRITIC AND QUESTION GENERATOR====")
    
    if state.progress.get(state.current_section) == "Not Started":
        state.progress[state.current_section] = "In Progress"

    # Extract inputs from state
    current_section_name = state.current_section
    current_section_draft = state.current_section_draft.draft if state.current_section_draft else "No draft generated yet."

    # Prepare subsection data for prompt
    subsections_with_definitions = [
        {"subsection_heading": sub.subsection_heading, "subsection_definition": sub.subsection_definition}
        for sub in state.current_subsections
    ]

    subsections_str="\n".join(f"- {sub['subsection_heading']}: {sub['subsection_definition']}" for sub in subsections_with_definitions)

    user_idea = state.idea

    # Format conversation history for prompt
    conversation_history_str = "No conversation history yet."
    if state.conversation_history:
        conversation_history_str = "\n".join(
            f"Section: {entry.section}, Subsection: {entry.subsection}\n"
            f"Question: {entry.question}\nAnswer: {entry.answer}\n"
            for entry in state.conversation_history
            if entry.section == current_section_name
        )

    # Find section purpose from state.sections
    section_purpose = next(
        section["section_purpose"] for section in state.sections 
        if section["section_heading"] == current_section_name
    )

    # Create structured LLM
    structured_llm = llm.with_structured_output(
        OptionalQuestionOutput,
        method = "json_mode"
        )
    
    # Format prompt with inputs
    prompt = question_generator_prompt_template.format(
        section_name = current_section_name,
        section_purpose = section_purpose,
        subsections_str = subsections_str,
        user_idea=user_idea,
        current_section_draft=current_section_draft,
        conversation_history=conversation_history_str,
    )

    try:
        response = await structured_llm.ainvoke(prompt)
        print(f"\nCritic and question generated:\n{response}")

        state.question_generator_output = response.question if response and response.question else None
    
        return state
            
    except Exception as e:
        print(f"Error in question_generator_node: {str(e)}")
        state.question_generator_output = None
        return state
    
async def determine_next_node_after_critic(state: GraphState) -> str:
    current_section_name = state.current_section
    question = state.question_generator_output

    if question is None:
        print(f"✅ No more questions needed — moving to REVIEW")
        return SECTION_REVIEW_NODE
        
    if question.section != current_section_name:
        print(f"⚠️ Section mismatch in question — retrying...")
        return CRITIC_QUESTION_NODE
    
    if question.subsection not in [s.subsection_heading for s in state.current_subsections]:
        print(f"⚠️ Invalid subsection: {question.subsection} — retrying...")
        return CRITIC_QUESTION_NODE
    
    # Check for question similarity
    existing_questions = [
        entry.question for entry in state.conversation_history 
        if entry.section == current_section_name and entry.subsection == question.subsection
    ]
    
    if is_question_similar(question.question, existing_questions):
        print(f"⚠️ Question too similar to existing questions — retrying...")
        return CRITIC_QUESTION_NODE
    
    print(f"➡️ Comprehensive question generated — moving to USER_INPUT_DRAFT_GENERATOR_NODE")
    return USER_INPUT_DRAFT_GENERATOR_NODE

async def user_input_draft_generator_node(state: GraphState) -> GraphState:
    print("\n=== USER INPUT NODE ===\n")
    
    current_section_name = state.current_section

    # Get user input
    user_response = interrupt({
        "action": "get_question_response",
        "section": current_section_name,
        "subsection": state.question_generator_output.subsection,
        "question": state.question_generator_output.question,
        "reason": state.question_generator_output.reason
    }).strip()

    # Create ConversationEntry
    conversation_entry = ConversationEntry(
        section=current_section_name,
        subsection=state.question_generator_output.subsection,
        question=state.question_generator_output.question,
        answer=user_response
    )
    
    # Append to conversation_history
    state.conversation_history.append(conversation_entry)

    print(f"User input processed:\n{user_response}")

    print("\n=== DRAFT GENERATION STARTED ===\n")

    # Find section purpose from new_state.sections
    section_purpose = next(
        section["section_purpose"] for section in state.sections 
        if section["section_heading"] == current_section_name
    )
    
    subsection_name = state.question_generator_output.subsection
    subsection_definition = next(sub.subsection_definition for sub in state.current_subsections 
                                if sub.subsection_heading == subsection_name)
    
    # Create structured LLM with JSON mode
    structured_llm = llm.with_structured_output(
        DraftOutput,
        method="json_mode"
    )
    
    # Format prompt with inputs
    prompt = draft_generator_prompt_template.format(
        section_name=current_section_name,
        section_purpose=section_purpose,
        current_section_draft=(state.current_section_draft.draft 
            if state.current_section_draft 
            else "No existing draft"),
        subsection_name=subsection_name,
        subsection_definition=subsection_definition,
        question_answer_pair=(
            f"Q: {conversation_entry.question}\n"
            f"A: {conversation_entry.answer}"
        ),
        contract_type=state.contract_type or "Commercial_Contracts",
        formatting_guidelines=state.formatting_guidelines or "Use standard legal contract format with formal language and defined terms."
    )
    
    try:
        
        draft_output = await structured_llm.ainvoke(prompt)
        print(f"Draft generated: {draft_output.draft}")
        
        state.current_section_draft = draft_output
        state.question_generator_output = None
        
        return state
    
    except Exception as e:
        print(f"Draft generation failed: {str(e)} - this should trigger critic again")
        state.question_generator_output = None

        return state
    
def determine_next_node_after_user_input(state: GraphState) -> str:
    if state.current_section_draft is None:
        print("❌ Draft generation failed — moving to review to avoid infinite loop")
        return SECTION_REVIEW_NODE
    
    # After one comprehensive question, always move to review
    print("✅ Comprehensive question answered — moving to REVIEW")
    return SECTION_REVIEW_NODE

async def section_review_node(state: GraphState) -> GraphState:
    print("\n=== SECTION REVIEW NODE ===\n")

    current_section_name = state.current_section
    section_purpose = next(s["section_purpose"] for s in state.sections if s["section_heading"] == current_section_name)
    current_draft = state.current_section_draft.draft if state.current_section_draft else "No draft content available"
    subsections_str = "\n".join(f"- {sub.subsection_heading}: {sub.subsection_definition}" for sub in state.current_subsections)

    # === 1. Show to user and get decision ===
    print(f"\n=== REVIEW FOR SECTION: {current_section_name} ===")

    reviewed_draft = interrupt(
            {
                "action": "get_reviewed_section_draft",
                "section": current_section_name,
                "draft": current_draft
            }
        )
    
    state.current_section_draft.draft = reviewed_draft
    state.progress[current_section_name] = "Complete"
    state.all_drafts[current_section_name] = state.current_section_draft.draft

    print(f"Succesfully updated the draft")
    return state

async def final_review_node(state: GraphState) -> GraphState:
    print("\n=== FINAL REVIEW NODE ===\n")
    
    # Combine all drafts into a complete document
    complete_document = f"# {state.title}\n\n"
    for section_name, draft_content in state.all_drafts.items():
        if draft_content and draft_content.strip():
            complete_document += f"## {section_name}\n{draft_content}\n\n"
    
    print(f"📄 Complete document assembled with {len(state.all_drafts)} sections")
    
    # Initialize iteration counter if not exists
    if not hasattr(state, 'review_iterations'):
        state.review_iterations = 0
    
    # Use AI scoring service to review the complete document
    try:
        contract_data = {
            "title": state.title,
            "original_idea": state.idea,
            "rephrased_idea": state.idea,
            "drafts": state.all_drafts,
            "department": "Legal"
        }
        
        # Get AI score and feedback
        score_result = await ai_contract_scoring_service.score_contract(contract_data)
        
        print(f"🎯 AI Review Score: {score_result['score']}/100")
        print(f"📝 AI Feedback: {score_result['feedback']}")
        
        # Store AI review results in state
        state.ai_score = score_result["score"]
        state.ai_feedback = score_result["feedback"]
        state.ai_strengths = score_result["strengths"]
        state.ai_improvements = score_result["improvements"]
        state.ai_risk_level = score_result["risk_level"]
        
        # Check if document needs improvement or max iterations reached
        if score_result["score"] >= 80 or state.review_iterations >= 2:  # Max 3 iterations (0, 1, 2)
            print("🎉 Document finalized!")
            state.document_generated = True
            return state
        else:
            state.review_iterations += 1
            print(f"🔄 Iteration {state.review_iterations + 1}/3: Improving document based on AI feedback...")
            
            # Use AI feedback to improve the document
            improvement_prompt = f"""
            Based on the following AI feedback, please improve this {state.contract_type} contract document:
            
            **AI Score**: {score_result['score']}/100
            **AI Feedback**: {score_result['feedback']}
            **Strengths**: {', '.join(score_result['strengths'])}
            **Improvements Needed**: {', '.join(score_result['improvements'])}
            
            **Current Document**:
            {complete_document}
            
            Please provide an improved version that addresses the specific improvements mentioned while maintaining the strengths.
            Focus on legal clarity, proper formatting, and addressing the identified weaknesses.
            Return only the improved document content without additional commentary.
            """
            
            # Get improved version from AI
            improved_document = await llm.ainvoke(improvement_prompt)
            
            # Store the improved version
            state.improved_document = improved_document.content
            state.document_generated = True
            
            print(f"✅ Document improved (iteration {state.review_iterations + 1}/3)")
            return state
            
    except Exception as e:
        print(f"❌ Error in final review: {e}")
        # If AI review fails, still mark as complete
        state.document_generated = True
        return state

def determine_next_node_after_final_review(state: GraphState) -> str:
    if state.document_generated:
        print("🎉 Final document completed successfully!")
        return END
    else:
        print("🔄 Document needs further refinement")
        return FINAL_REVIEW_NODE
    
workflow = StateGraph(GraphState)
workflow.add_node(IDEA_STRUCTURING_NODE, idea_structuring_node)
workflow.add_node(IDEA_STRUCTURING_REVIEW_NODE, idea_structuring_review_node)
workflow.add_node(INITALIZE_STATE_NODE, intiliaze_graph_state)
workflow.add_node(SECTION_SELECTOR_NODE, section_selector_node)
workflow.add_node(CRITIC_QUESTION_NODE, critic_and_question_generator_node)
workflow.add_node(USER_INPUT_DRAFT_GENERATOR_NODE, user_input_draft_generator_node)
workflow.add_node(SECTION_REVIEW_NODE, section_review_node)
workflow.add_node(FINAL_REVIEW_NODE, final_review_node)

workflow.set_entry_point(IDEA_STRUCTURING_NODE)

workflow.add_edge(IDEA_STRUCTURING_NODE, IDEA_STRUCTURING_REVIEW_NODE)
workflow.add_edge(IDEA_STRUCTURING_REVIEW_NODE, INITALIZE_STATE_NODE)
workflow.add_edge(INITALIZE_STATE_NODE, SECTION_SELECTOR_NODE)
workflow.add_edge(SECTION_REVIEW_NODE, SECTION_SELECTOR_NODE)

workflow.add_conditional_edges(
    SECTION_SELECTOR_NODE,
    determine_next_node_after_section_selector,
    {
        CRITIC_QUESTION_NODE: CRITIC_QUESTION_NODE,
        FINAL_REVIEW_NODE: FINAL_REVIEW_NODE
    }
)

workflow.add_conditional_edges(
    FINAL_REVIEW_NODE,
    determine_next_node_after_final_review,
    {
        FINAL_REVIEW_NODE: FINAL_REVIEW_NODE,
        END: END
    }
)

workflow.add_conditional_edges(
    CRITIC_QUESTION_NODE,
    determine_next_node_after_critic,
    {
        CRITIC_QUESTION_NODE: CRITIC_QUESTION_NODE,
        USER_INPUT_DRAFT_GENERATOR_NODE: USER_INPUT_DRAFT_GENERATOR_NODE,
        SECTION_REVIEW_NODE: SECTION_REVIEW_NODE
    }
)

workflow.add_conditional_edges(
    USER_INPUT_DRAFT_GENERATOR_NODE,
    determine_next_node_after_user_input,
    {
        CRITIC_QUESTION_NODE: CRITIC_QUESTION_NODE,
        SECTION_REVIEW_NODE: SECTION_REVIEW_NODE
    }
)


graph_app = workflow.compile(checkpointer=memory)
