from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from bson import ObjectId
from enum import Enum

# DexKo-specific enums
class DexKoDepartment(str, Enum):
    ENGINEERING = "Engineering"
    MANUFACTURING = "Manufacturing"
    SALES = "Sales"
    MARKETING = "Marketing"
    FINANCE = "Finance"
    HR = "Human Resources"
    IT = "IT"
    OPERATIONS = "Operations"
    SUPPLY_CHAIN = "Supply Chain"
    OTHER = "Other"

class IdeaStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"

class SubsectionDocument(BaseModel):
    subsection_heading: str
    subsection_definition: str

class SectionDocument(BaseModel):
    section_heading: str
    section_purpose: str
    subsections: List[SubsectionDocument]

class ConversationEntryDocument(BaseModel):
    section: str
    subsection: str
    question: str
    answer: str

class DexKoUserContext(BaseModel):
    user_id: str = Field(..., description="DexKo employee ID")
    department: DexKoDepartment = Field(..., description="DexKo department")
    role: str = Field(..., description="Employee role/title")
    location: str = Field(..., description="DexKo location/office")
    language: str = Field("en", description="Preferred language (en/de)")

class MetadataDocument(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    total_questions_asked: int = 0
    completion_time_minutes: Optional[float] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class IdeaDocument(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    session_id: str
    title: str
    original_idea: str
    rephrased_idea: str
    sections: List[SectionDocument]
    drafts: Dict[str, str]
    conversation_history: List[ConversationEntryDocument]
    metadata: MetadataDocument
    dexko_context: Optional[DexKoUserContext] = Field(None, description="DexKo user context")
    evaluation_score: Optional[float] = Field(None, description="Automated evaluation score (0-100)")
    reviewer_feedback: Optional[str] = Field(None, description="Reviewer comments")
    ai_score: Optional[int] = Field(None, description="AI-generated score (0-100)")
    ai_feedback: Optional[str] = Field(None, description="AI-generated feedback")
    ai_strengths: Optional[List[str]] = Field(None, description="AI-identified strengths")
    ai_improvements: Optional[List[str]] = Field(None, description="AI-identified improvements")
    status: IdeaStatus = Field(IdeaStatus.SUBMITTED, description="Idea workflow status")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }
