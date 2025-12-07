import os
from typing import Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ContractCategory(BaseModel):
    """Model for AI-generated contract categorization"""
    primary_category: str = Field(description="Primary category for the contract")
    secondary_category: str = Field(description="Secondary category for the contract")
    reasoning: str = Field(description="Detailed reasoning for the categorization")
    confidence_score: int = Field(description="Confidence score from 0-100")
    key_themes: list[str] = Field(description="Key legal themes identified in the contract")
    recommended_sections: list[str] = Field(description="Recommended contract sections for this type")
    legal_formatting_guidelines: str = Field(description="Specific formatting guidelines for this contract type")

class AIContractCategorizationService:
    def __init__(self):
        # Get Azure OpenAI configuration from environment
        self.api_key = os.getenv("GPT_4O_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not self.api_key or not self.azure_endpoint:
            logger.warning("⚠️ Azure OpenAI configuration not found - categorization service will use fallback")
            self.llm = None
            return
        
        # Configure Azure OpenAI LLM
        base_endpoint = self.azure_endpoint.split("/openai/deployments/")[0]
        self.llm = AzureChatOpenAI(
            model="gpt-4o",
            api_key=self.api_key,
            azure_endpoint=base_endpoint,
            azure_deployment="gpt-4o",
            api_version="2025-01-01-preview",
            temperature=0.2
        )
        
        # Create categorization prompt for contracts
        self.categorization_prompt = ChatPromptTemplate.from_template("""
You are an expert legal analyst specializing in contract review and categorization. Your task is to categorize legal contracts into appropriate categories based on their content, legal themes, and business context.

**Contract Details:**
- Title: {title}
- Department: {department}
- Contract Content: {content}

**Available Contract Categories:**
1. **Commercial_Contracts**: Sales agreements, purchase orders, distribution agreements, vendor contracts
2. **Employment_Contracts**: Employment agreements, contractor agreements, non-disclosure agreements, non-compete agreements
3. **Real_Estate_Contracts**: Lease agreements, property purchase agreements, rental contracts, land use agreements
4. **Service_Agreements**: Service contracts, consulting agreements, maintenance contracts, SLA agreements
5. **Partnership_Contracts**: Joint venture agreements, partnership agreements, collaboration agreements
6. **Intellectual_Property**: Licensing agreements, IP transfer agreements, trademark agreements, patent licenses
7. **Compliance_Regulatory**: Regulatory compliance agreements, government contracts, compliance documentation
8. **Financial_Contracts**: Loan agreements, financing contracts, investment agreements, payment terms

**Instructions:**
- Analyze the contract content thoroughly
- Assign a primary category (most relevant)
- Assign a secondary category (second most relevant)
- Provide detailed legal reasoning for your categorization
- Give a confidence score (0-100) based on how well the contract fits the categories
- Identify 3-5 key legal themes present in the contract
- Recommend 5-8 essential contract sections for this specific contract type
- Provide specific formatting guidelines for this contract type (e.g., standard legal clauses, required disclosures, signature blocks)
- Be objective and legally-focused
- Consider the business context and legal implications

**Response Format (JSON):**
{{
    "primary_category": "Commercial_Contracts",
    "secondary_category": "Service_Agreements",
    "reasoning": "This contract establishes a vendor relationship with specific service level agreements and payment terms, which aligns with Commercial_Contracts. The secondary category of Service_Agreements reflects the detailed service obligations and performance metrics.",
    "confidence_score": 85,
    "key_themes": ["Service level agreements", "Payment terms", "Performance metrics", "Termination clauses"],
    "recommended_sections": ["Parties and Recitals", "Definitions", "Services and Deliverables", "Payment Terms", "Term and Termination", "Representations and Warranties", "Liability and Indemnification", "Governing Law"],
    "legal_formatting_guidelines": "Use standard commercial contract format with recitals, defined terms, and numbered articles. Include signature blocks for both parties. Use formal legal language with defined terms in quotes on first use."
}}
""")
        
        self.parser = JsonOutputParser(pydantic_object=ContractCategory)

    async def categorize_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize a contract using AI and return category analysis"""
        try:
            logger.info(f"🔍 AI categorizing contract: {contract_data.get('title', 'Untitled')}")
            
            # Check if LLM is available
            if self.llm is None:
                logger.warning("⚠️ Azure OpenAI not configured - using fallback categorization")
                return self._get_fallback_categorization()
            
            # Prepare input for the LLM
            content = self._prepare_contract_content(contract_data)
            
            # Create the chain
            chain = self.categorization_prompt | self.llm | self.parser
            
            # Invoke the chain
            result = await chain.ainvoke({
                "title": contract_data.get("title", "Untitled Contract"),
                "department": contract_data.get("department", "Legal"),
                "content": content
            })
            
            logger.info(f"✅ AI categorized contract: {result['primary_category']} (confidence: {result['confidence_score']}%)")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI contract categorization failed: {e}")
            return self._get_fallback_categorization()

    def _prepare_contract_content(self, contract_data: Dict[str, Any]) -> str:
        """Prepare the contract content for AI categorization"""
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
        
        # Add summary if available
        if contract_data.get("summary"):
            content_parts.append(f"Summary: {contract_data['summary']}")
        
        return "\n".join(content_parts) if content_parts else "No detailed contract content available for categorization."

    def _get_fallback_categorization(self) -> Dict[str, Any]:
        """Return a fallback categorization when AI categorization is unavailable"""
        return {
            "primary_category": "Commercial_Contracts",
            "secondary_category": "Service_Agreements",
            "reasoning": "Unable to generate AI categorization at this time. Azure OpenAI configuration may be missing.",
            "confidence_score": 50,
            "key_themes": ["General legal agreement"],
            "recommended_sections": ["Parties and Recitals", "Definitions", "Services and Deliverables", "Payment Terms", "Term and Termination"],
            "legal_formatting_guidelines": "Use standard legal contract format with formal language and defined terms."
        }

# Global instance
ai_contract_categorization_service = AIContractCategorizationService()
