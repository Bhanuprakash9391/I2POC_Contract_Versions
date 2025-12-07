import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ContractScore(BaseModel):
    """Model for AI-generated contract score and feedback"""
    score: int = Field(description="Score from 0-100")
    feedback: str = Field(description="At least one paragraph of detailed legal feedback about the contract")
    strengths: list[str] = Field(description="Key legal strengths of the contract")
    improvements: list[str] = Field(description="Areas for legal improvement")
    risk_level: str = Field(description="Overall risk level: Low, Medium, High")

class AIContractScoringService:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ DeepSeek API key not found - scoring service will use fallback")
            self.llm = None
            return

        # Configure DeepSeek LLM
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.3
        )
        
        # Create scoring prompt for contracts
        self.scoring_prompt = ChatPromptTemplate.from_template("""
You are an expert legal reviewer specializing in contract analysis and risk assessment. Your task is to evaluate legal contracts and provide a comprehensive score with constructive legal feedback.

**Contract Details:**
- Title: {title}
- Department: {department}
- Contract Content: {content}

**Legal Evaluation Criteria:**
1. **Legal Completeness** (0-25 points): Are all essential legal clauses present and properly defined?
2. **Risk Management** (0-25 points): How well does the contract identify and mitigate legal risks?
3. **Clarity & Precision** (0-25 points): Is the language clear, unambiguous, and legally sound?
4. **Business Alignment** (0-25 points): Does the contract properly reflect the business arrangement and protect interests?

**Instructions:**
- Provide an overall legal quality score from 0-100
- Give AT LEAST ONE PARAGRAPH of detailed legal feedback (minimum 3-4 sentences)
- List 2-3 key legal strengths
- List 2-3 areas for legal improvement
- Assess overall risk level (Low, Medium, High)
- Be constructive and legally-focused
- Provide specific, actionable legal recommendations
- Consider standard legal practices and potential liabilities

**Response Format (JSON):**
{{
    "score": 85,
    "feedback": "This contract demonstrates solid legal structure with clear definitions and obligations. The termination clauses and dispute resolution mechanisms are well-defined, providing adequate protection. However, the liability limitations could be strengthened, and additional indemnification language would enhance risk management. The payment terms are clear but could benefit from more specific late payment penalties.",
    "strengths": ["Clear termination clauses", "Well-defined dispute resolution", "Proper governing law selection"],
    "improvements": ["Strengthen liability limitations", "Add comprehensive indemnification clauses", "Specify late payment penalties"],
    "risk_level": "Medium"
}}
""")
        
        self.parser = JsonOutputParser(pydantic_object=ContractScore)

    async def score_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score a contract using AI and return score with legal feedback"""
        try:
            logger.info(f"🔍 AI scoring contract: {contract_data.get('title', 'Untitled')}")
            
            # Check if LLM is available
            if self.llm is None:
                logger.warning("⚠️ DeepSeek not configured - using fallback scoring")
                return self._get_fallback_score()
            
            # Prepare input for the LLM
            content = self._prepare_contract_content(contract_data)
            
            # Create the chain
            chain = self.scoring_prompt | self.llm | self.parser
            
            # Invoke the chain
            result = await chain.ainvoke({
                "title": contract_data.get("title", "Untitled Contract"),
                "department": contract_data.get("department", "Legal"),
                "content": content
            })
            
            logger.info(f"✅ AI scored contract: {result['score']}/100 (Risk: {result['risk_level']})")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI contract scoring failed: {e}")
            return self._get_fallback_score()

    def _prepare_contract_content(self, contract_data: Dict[str, Any]) -> str:
        """Prepare the contract content for AI legal evaluation"""
        content_parts = []
        
        # Add original idea if available
        if contract_data.get("original_idea"):
            content_parts.append(f"Original Contract Idea: {contract_data['original_idea']}")
        
        # Add draft content if available
        if contract_data.get("drafts"):
            content_parts.append("Contract Document Sections:")
            for section, draft in contract_data["drafts"].items():
                if draft and draft.strip() and draft != "No draft content available":
                    content_parts.append(f"\n## {section}\n{draft}")
        
        # Add rephrased idea if available
        if contract_data.get("rephrased_idea"):
            content_parts.append(f"Rephrased Contract: {contract_data['rephrased_idea']}")
        
        return "\n".join(content_parts) if content_parts else "No detailed contract content available for legal evaluation."

    def _get_fallback_score(self) -> Dict[str, Any]:
        """Return a fallback score when AI scoring is unavailable"""
        return {
            "score": 50,
            "feedback": "Unable to generate AI legal evaluation at this time. DeepSeek API key may be missing.",
            "strengths": ["Contract submitted successfully"],
            "improvements": ["AI legal evaluation service temporarily unavailable"],
            "risk_level": "Medium"
        }

# Global instance
ai_contract_scoring_service = AIContractScoringService()
