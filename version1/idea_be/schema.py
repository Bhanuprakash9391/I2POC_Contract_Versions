from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

# MongoDB integration imports
from models import IdeaDocument, MetadataDocument, DexKoUserContext, DexKoDepartment, IdeaStatus

class QuestionOutput(BaseModel):
    section: str = Field(..., description="The section for which the question is generated")
    subsection: str = Field(..., description="The subsection the question targets")
    question: str = Field(..., description="The question to elicit missing information")
    reason: str = Field(..., description="Why this question was generated")

class ConversationEntry(BaseModel):
    section: str = Field(..., description="The section of the conversation")
    subsection: str = Field(..., description="The subsection of the conversation")
    question: str = Field(..., description="The question asked")
    answer: str = Field(..., description="The user's answer to the question")

class DraftOutput(BaseModel):
    section: str = Field(..., description="The section for which the draft is generated")
    draft: str = Field(..., description="The generated draft content")

# Subsection Definition
class Subsection(BaseModel):
    subsection_heading: str = Field(..., description="The name of the subsection")
    subsection_definition: str = Field(..., description="The definition or purpose of the subsection")
    
class OptionalQuestionOutput(BaseModel):
    question: Optional[QuestionOutput] = Field(
        None,
        description="The generated question to elicit missing information",
    )

class IdeaStructuringOutput(BaseModel):
    rephrased_idea: str = Field(..., description="Refined version of the original idea")
    title_1: str = Field(..., description="A professional title based on the refined idea")

class GraphState(BaseModel):
    idea: Optional[str] = None # store the user's idea
    title: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None  # List of {name, purpose} for all sections
    current_section: Optional[str] = None
    current_subsections: List[Subsection] = Field(default_factory=list)
    current_section_draft: Optional[DraftOutput] = None
    conversation_history: List[ConversationEntry] = Field(default_factory=list)
    question_asked_for_current_section: int = 0
    question_generator_output: Optional[QuestionOutput] = None
    progress: Dict[str, str] = Field(default_factory=dict) # e.g., {"Problem Definition": "In Progress"}
    all_drafts: Dict[str, str] = Field(default_factory=dict)
    document_generated: bool = False
    # Contract type information
    contract_type: Optional[str] = Field(None, description="Type of contract being generated")
    formatting_guidelines: Optional[str] = Field(None, description="Formatting guidelines for this contract type")
    # DexKo-specific fields
    dexko_user_context: Optional[DexKoUserContext] = Field(None, description="DexKo user context for personalization")
    target_department: Optional[DexKoDepartment] = Field(None, description="Target DexKo department for the idea")
    # AI review fields
    review_iterations: int = Field(0, description="Number of review iterations completed")
    ai_score: Optional[int] = Field(None, description="AI evaluation score")
    ai_feedback: Optional[str] = Field(None, description="AI feedback on the contract")
    ai_strengths: List[str] = Field(default_factory=list, description="AI-identified strengths")
    ai_improvements: List[str] = Field(default_factory=list, description="AI-identified improvements needed")
    ai_risk_level: Optional[str] = Field(None, description="AI-assessed risk level")
    improved_document: Optional[str] = Field(None, description="Improved document content after AI review")
