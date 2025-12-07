import logging
from typing import Dict, Any, List, Optional
import asyncio
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
import re

logger = logging.getLogger(__name__)

class ContractTemplateService:
    """Service for generating contracts using AI/LLM capabilities"""
    
    def __init__(self):
        # Initialize LLM for contract generation - try multiple API key environment variables
        openai_key = os.getenv("OPENAI_API_KEY")
        gpt4o_key = os.getenv("GPT_4O_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not any([openai_key, gpt4o_key, groq_key]):
            logger.warning("No API key found. AI features will be disabled. Set OPENAI_API_KEY, GPT_4O_API_KEY, or GROQ_API_KEY environment variable.")
            self.llm = None
        else:
            # Try Azure OpenAI first if available
            if gpt4o_key and azure_endpoint:
                try:
                    # Extract deployment name from endpoint
                    deployment_match = re.search(r'/deployments/([^/]+)/', azure_endpoint)
                    deployment_name = deployment_match.group(1) if deployment_match else "gpt-4o"
                    
                    # Use LangChain's AzureChatOpenAI
                    self.llm = AzureChatOpenAI(
                        azure_deployment=deployment_name,
                        openai_api_version="2025-01-01-preview",
                        azure_endpoint=azure_endpoint.split('/openai/deployments/')[0] if '/openai/deployments/' in azure_endpoint else azure_endpoint,
                        openai_api_key=gpt4o_key,
                        temperature=0.3
                    )
                    logger.info(f"Azure OpenAI model initialized: {deployment_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Azure OpenAI, falling back to standard OpenAI: {e}")
                    # Fallback to standard OpenAI
                    if openai_key:
                        self.llm = ChatOpenAI(
                            model_name="gpt-4",
                            temperature=0.3,
                            openai_api_key=openai_key
                        )
                        logger.info("Standard OpenAI model initialized: gpt-4")
                    else:
                        self.llm = None
            elif openai_key:
                # Use standard OpenAI
                self.llm = ChatOpenAI(
                    model_name="gpt-4",
                    temperature=0.3,
                    openai_api_key=openai_key
                )
                logger.info("Standard OpenAI model initialized: gpt-4")
            else:
                logger.warning("No valid API configuration found. AI features will be disabled.")
                self.llm = None
    
    async def generate_indian_law_contract(self, extracted_data: Dict[str, Any], contract_type: str = "", jurisdiction: str = "india") -> Dict[str, Any]:
        """
        Generate a formatted contract according to Indian law using AI
        """
        try:
            logger.info(f"Generating Indian law contract using AI for type: {contract_type}")
            
            # Use AI to generate contract based on extracted data
            contract_content = await self._generate_contract_with_ai(extracted_data, contract_type, jurisdiction)
            
            # Parse the AI-generated contract into sections
            sections = await self._parse_contract_into_sections(contract_content)
            
            generated_contract = {
                "title": self._extract_title_from_content(contract_content, contract_type),
                "description": extracted_data.get("summary", ""),
                "sections": sections,
                "drafts": self._create_drafts_from_sections(sections),
                "metadata": {
                    "source": "ai_generated",
                    "contract_type": contract_type,
                    "jurisdiction": jurisdiction,
                    "ai_generated": True
                }
            }
            
            logger.info(f"Successfully generated Indian law contract with {len(sections)} sections using AI")
            return generated_contract
            
        except Exception as e:
            logger.error(f"Error generating Indian law contract with AI: {e}")
            # Fallback to basic template
            return await self._generate_fallback_contract(extracted_data, contract_type)
    
    async def generate_from_template(self, template: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a contract from a template using AI to adapt it with user data
        """
        try:
            logger.info(f"Generating contract from template using AI: {template.get('contract_type', 'unknown')}")
            
            # Use AI to adapt the template with user data
            adapted_contract = await self._adapt_template_with_ai(template, user_data)
            
            generated_contract = {
                "title": user_data.get("title", adapted_contract.get("title", "Generated Contract")),
                "description": user_data.get("description", template.get("description", "")),
                "sections": adapted_contract.get("sections", []),
                "drafts": adapted_contract.get("drafts", {}),
                "metadata": {
                    "source": "template_ai",
                    "template_id": template.get("template_id"),
                    "contract_type": template.get("contract_type"),
                    "ai_adapted": True
                }
            }
            
            logger.info(f"Successfully generated contract from template with AI adaptation")
            return generated_contract
            
        except Exception as e:
            logger.error(f"Error generating contract from template with AI: {e}")
            raise
    
    async def analyze_sample_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to analyze a sample contract template and extract its structure and patterns
        """
        if not self.llm:
            logger.warning("AI model not available, returning original template data")
            return template_data
            
        try:
            logger.info("Analyzing sample contract template with AI")
            
            sample_content = template_data.get("sample_content", "")
            contract_type = template_data.get("contract_type", "")
            
            # Use AI to analyze the template structure
            analysis_prompt = f"""
            Analyze the following contract template and provide a structured analysis:

            Contract Type: {contract_type}
            Template Content: {sample_content[:4000]}  # Limit content for token efficiency

            Please analyze:
            1. Key sections and their structure
            2. Common clauses and legal language patterns
            3. Formatting and styling patterns
            4. Key variables and placeholders
            5. Legal compliance aspects for Indian law

            Provide the analysis in a structured JSON format.
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a legal document analyst specializing in Indian contract law."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse AI response to extract analysis
            ai_analysis = self._parse_ai_analysis(response.content)
            
            # Enhance template data with AI analysis
            enhanced_template = {
                **template_data,
                "ai_analysis": ai_analysis,
                "structure_analysis": ai_analysis.get("sections", []),
                "legal_patterns": ai_analysis.get("legal_patterns", []),
                "compliance_notes": ai_analysis.get("compliance_notes", [])
            }
            
            logger.info("Successfully analyzed template with AI")
            return enhanced_template
            
        except Exception as e:
            logger.error(f"Error analyzing template with AI: {e}")
            return template_data  # Return original data if analysis fails
    
    async def _generate_contract_with_ai(self, extracted_data: Dict[str, Any], contract_type: str, jurisdiction: str) -> str:
        """Use AI to generate professional Indian contract content based on extracted data"""
        if not self.llm:
            logger.warning("AI model not available, using fallback contract generation")
            return f"""
            AGREEMENT

            This Agreement is made between {', '.join(extracted_data.get('parties', ['Party A', 'Party B']))}.

            TERMS AND CONDITIONS

            Standard terms and conditions apply as per Indian Contract Act, 1872.

            This is a fallback contract generated without AI assistance. Please configure an API key for enhanced contract generation.
            """
        
        # Check if we have raw_text from uploaded document and use it as base
        raw_text = extracted_data.get("raw_text", "")
        user_responses = extracted_data.get("missing_data_responses", {})
        
        if raw_text:
            # Use the uploaded document content as base and create professional Indian contract
            prompt = f"""
            You are a professional legal document drafter specializing in Indian contract law. Your task is to create a complete, professional legal contract document that looks like it was drafted by a qualified Indian lawyer.

            ORIGINAL DOCUMENT CONTENT (for reference):
            {raw_text[:4000]}

            USER-PROVIDED ADDITIONAL INFORMATION:
            {user_responses}

            Contract Type: {contract_type}
            Jurisdiction: {jurisdiction}

            CRITICAL REQUIREMENTS FOR PROFESSIONAL INDIAN LEGAL DOCUMENT:
            1. Create a COMPLETE, PROFESSIONAL legal contract document that looks like it was drafted by an Indian lawyer
            2. Use proper legal language, clauses, and formatting as per Indian legal standards
            3. Include standard legal sections appropriate for this contract type under Indian law
            4. Incorporate ALL user-provided information seamlessly into the appropriate sections
            5. Add standard legal clauses (confidentiality, termination, governing law, etc.) as per Indian Contract Act, 1872
            6. Use proper section headings in ALL CAPS with proper legal formatting
            7. Format as a proper legal document with numbered clauses and sub-clauses
            8. Include recitals, definitions, operative clauses, and signature blocks
            9. Ensure the document is legally sound and professional for Indian jurisdiction
            10. Use proper legal terminology and standard contract language used in Indian legal practice
            11. Include proper date format, consideration clauses, and execution details
            12. Make it look like a professionally drafted legal document, not plain text

            STANDARD LEGAL SECTIONS TO INCLUDE (format properly):
            - TITLE AND PARTIES (with proper legal names and addresses)
            - RECITALS (WHEREAS clauses explaining the background)
            - DEFINITIONS (clear definitions of key terms)
            - TERMS AND CONDITIONS (numbered clauses with proper legal language)
            - PAYMENT TERMS (if applicable, with proper consideration clauses)
            - OBLIGATIONS AND RESPONSIBILITIES (detailed obligations of each party)
            - TERMINATION (proper termination clauses with notice periods)
            - CONFIDENTIALITY (if applicable)
            - GOVERNING LAW AND JURISDICTION (specifically mention Indian law and courts)
            - DISPUTE RESOLUTION (mention arbitration or court jurisdiction as per Indian law)
            - MISCELLANEOUS (severability, entire agreement, notices, etc.)
            - SIGNATURE BLOCKS (with proper execution format)

            IMPORTANT: Generate a complete, ready-to-use legal document that looks professional and includes all necessary legal clauses for Indian jurisdiction. Do NOT use predefined templates - create a unique professional document based on the provided information.

            Generate the complete professional Indian legal contract:
            """
            
            system_message = "You are a professional legal document drafter specializing in Indian contract law. Create complete, professional legal contracts that look like they were drafted by qualified Indian lawyers. ALWAYS generate contracts as plain text with proper legal formatting, never as JSON or any other structured format."
        else:
            # Generate new professional Indian contract from scratch
            prompt = f"""
            Generate a professional contract document according to Indian law that looks like it was drafted by a qualified Indian lawyer.

            Contract Type: {contract_type}
            Jurisdiction: {jurisdiction}
            
            Extracted Information:
            - Parties: {extracted_data.get('parties', ['Party A', 'Party B'])}
            - Key Terms: {[term.get('term', '') for term in extracted_data.get('key_terms', [])][:5]}
            - Payment Terms: {extracted_data.get('payment_terms', {}).get('terms', 'To be determined')}
            - Duration: {extracted_data.get('duration', {}).get('duration', 'Not specified')}
            - Termination Clauses: {extracted_data.get('termination_clauses', [])}
            - Summary: {extracted_data.get('summary', '')}
            - User Provided Information: {user_responses}

            CRITICAL REQUIREMENTS FOR PROFESSIONAL INDIAN LEGAL DOCUMENT:
            1. Create a COMPLETE, PROFESSIONAL legal contract document suitable for Indian legal context
            2. Include all standard sections with proper legal formatting as per Indian legal practice
            3. Ensure compliance with Indian Contract Act, 1872 and other relevant Indian laws
            4. Use professional legal language and terminology used by Indian lawyers
            5. Include appropriate placeholders for specific details with proper legal formatting
            6. Structure the document with clear section headings in ALL CAPS
            7. Use numbered clauses and sub-clauses with proper legal numbering
            8. Include standard legal boilerplate clauses for Indian contracts
            9. Make the document look professionally drafted, not like plain text
            10. Include proper execution format with signature blocks

            STANDARD SECTIONS TO INCLUDE:
            - TITLE AND PARTIES
            - RECITALS (WHEREAS clauses)
            - DEFINITIONS
            - TERMS AND CONDITIONS (numbered)
            - PAYMENT TERMS
            - OBLIGATIONS
            - TERMINATION
            - CONFIDENTIALITY
            - GOVERNING LAW AND JURISDICTION (specify Indian law)
            - DISPUTE RESOLUTION
            - MISCELLANEOUS
            - SIGNATURES

            IMPORTANT: Generate the complete professional Indian legal contract as plain text with proper legal formatting. Do NOT use predefined templates - create a unique professional document.
            """
            
            system_message = "You are a professional legal document drafter specializing in Indian contract law. Create complete, professional legal contracts that look like they were drafted by qualified Indian lawyers. ALWAYS generate contracts as plain text with proper legal formatting, never as JSON or any other structured format."
        
        response = await self.llm.ainvoke([
            SystemMessage(content=system_message),
            HumanMessage(content=prompt)
        ])
        
        # Ensure the content is plain text, not JSON
        content = response.content
        if content.strip().startswith('{') or content.strip().startswith('['):
            logger.warning("AI generated JSON instead of plain text, using fallback")
            if raw_text:
                # Fallback: use original document with user inputs appended
                fallback_content = raw_text + "\n\nADDITIONAL INFORMATION PROVIDED BY USER:\n"
                for field, value in user_responses.items():
                    fallback_content += f"\n{field}: {value}"
                return fallback_content
            else:
                return f"""
                CONTRACT AGREEMENT

                This Agreement is made between {', '.join(extracted_data.get('parties', ['Party A', 'Party B']))}.

                TERMS AND CONDITIONS

                Standard terms and conditions apply as per Indian Contract Act, 1872.

                USER PROVIDED INFORMATION:
                {user_responses}

                This contract was generated with fallback content due to AI response format issues.
                """
        
        return content
    
    async def _adapt_template_with_ai(self, template: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to adapt a template with user-specific data"""
        if not self.llm:
            logger.warning("AI model not available, using fallback template adaptation")
            # Return basic adapted template without AI
            basic_sections = [
                {
                    "heading": "AGREEMENT",
                    "content": f"This Agreement is adapted from template: {template.get('contract_type', 'Unknown')}",
                    "type": "parties"
                },
                {
                    "heading": "TERMS AND CONDITIONS", 
                    "content": "Standard terms and conditions apply as per Indian Contract Act, 1872.",
                    "type": "terms"
                }
            ]
            return {
                "title": f"Adapted {template.get('contract_type', 'Contract')}",
                "sections": basic_sections,
                "drafts": self._create_drafts_from_sections(basic_sections)
            }
        
        template_content = template.get("sample_content", "")[:3000]  # Limit for token efficiency
        
        prompt = f"""
        Adapt the following contract template with the user-provided data:

        Original Template (Contract Type: {template.get('contract_type', 'Unknown')}):
        {template_content}

        User Data to Incorporate:
        {user_data}

        Requirements:
        1. Maintain the original template's structure and legal validity
        2. Replace placeholders with actual user data
        3. Ensure the contract remains compliant with Indian law
        4. Keep the professional tone and legal language
        5. Generate the complete adapted contract

        Provide the adapted contract document:
        """
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are a legal document specialist who adapts contract templates with user-specific information while maintaining legal compliance."),
            HumanMessage(content=prompt)
        ])
        
        # Parse the adapted contract
        adapted_content = response.content
        sections = await self._parse_contract_into_sections(adapted_content)
        
        return {
            "title": self._extract_title_from_content(adapted_content, template.get("contract_type", "")),
            "sections": sections,
            "drafts": self._create_drafts_from_sections(sections)
        }
    
    async def _parse_contract_into_sections(self, contract_content: str) -> List[Dict[str, Any]]:
        """Parse contract content into structured sections - use robust parsing to avoid JSON output"""
        logger.info("Parsing contract content into sections using robust method")
        
        # First, try to parse using the robust method that preserves plain text
        sections = self._parse_contract_sections_robust(contract_content)
        
        # If we get sections with JSON-like content, fall back to basic extraction
        has_json_content = False
        for section in sections:
            content = section.get("content", "")
            if isinstance(content, dict) or (isinstance(content, str) and content.strip().startswith('{')):
                has_json_content = True
                break
        
        if has_json_content:
            logger.warning("Detected JSON-like content in sections, using basic extraction")
            return self._extract_sections_basic(contract_content)
        
        return sections
    
    def _parse_contract_sections_robust(self, content: str) -> List[Dict[str, Any]]:
        """Robustly parse contract content into sections - ensures plain text output"""
        sections = []
        
        # Common section headings in contracts
        common_headings = [
            "PARTIES", "RECITALS", "DEFINITIONS", "TERMS AND CONDITIONS", 
            "PAYMENT TERMS", "OBLIGATIONS", "TERMINATION", "JURISDICTION",
            "MISCELLANEOUS", "GOVERNING LAW", "CONFIDENTIALITY", "INDEMNIFICATION",
            "LIMITATION OF LIABILITY", "FORCE MAJEURE", "NOTICES", "ENTIRE AGREEMENT",
            "SEVERABILITY", "WAIVER", "ASSIGNMENT", "DISPUTE RESOLUTION"
        ]
        
        # Split content by common section patterns
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section heading (uppercase, bold, or numbered)
            is_heading = False
            heading_text = line.upper()
            
            # Check for common headings
            for heading in common_headings:
                if heading in heading_text:
                    is_heading = True
                    break
            
            # Check for numbered sections (like "1.", "2.", etc.)
            if re.match(r'^\d+\.\s+[A-Z]', line):
                is_heading = True
            
            # Check for bold/underlined sections (common in contracts)
            if line.isupper() and len(line) > 5 and len(line) < 100:
                is_heading = True
            
            if is_heading:
                # Save previous section if exists
                if current_section and current_content:
                    sections.append({
                        "heading": current_section,
                        "content": '\n'.join(current_content).strip(),
                        "type": self._classify_section_type(current_section)
                    })
                
                # Start new section
                current_section = line
                current_content = []
            else:
                # Add content to current section
                if current_section:
                    current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections.append({
                "heading": current_section,
                "content": '\n'.join(current_content).strip(),
                "type": self._classify_section_type(current_section)
            })
        
        # If no sections found, create a single section with all content
        if not sections:
            sections.append({
                "heading": "CONTRACT AGREEMENT",
                "content": content.strip(),
                "type": "general"
            })
        
        return sections
    
    def _parse_ai_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI analysis response into structured data"""
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        # or use structured output from the LLM
        
        analysis = {
            "sections": [],
            "legal_patterns": [],
            "compliance_notes": [],
            "key_variables": []
        }
        
        # Basic parsing logic - extract sections and patterns
        lines = ai_response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('##') or line.startswith('**'):
                if current_section:
                    analysis["sections"].append(current_section)
                current_section = {"heading": line.replace('##', '').replace('**', '').strip(), "content": ""}
            elif current_section and line:
                current_section["content"] += line + " "
        
        if current_section:
            analysis["sections"].append(current_section)
        
        return analysis
    
    def _parse_sections_from_ai_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse sections from AI response"""
        sections = []
        lines = ai_response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            # Detect section headers (common patterns in contracts)
            if (line.isupper() or 
                line.startswith('ARTICLE') or 
                line.startswith('SECTION') or
                line.startswith('CLAUSE') or
                any(line.lower().startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.'])):
                
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "heading": line,
                    "content": "",
                    "type": self._classify_section_type(line)
                }
            elif current_section and line:
                current_section["content"] += line + "\n"
        
        if current_section:
            sections.append(current_section)
        
        return sections if sections else self._extract_sections_basic(ai_response)
    
    def _extract_sections_basic(self, content: str) -> List[Dict[str, Any]]:
        """Basic fallback section extraction"""
        lines = content.split('\n')
        sections = []
        current_section = {"heading": "Contract Agreement", "content": "", "type": "general"}
        
        for line in lines:
            if line.strip():
                current_section["content"] += line + "\n"
        
        if current_section["content"]:
            sections.append(current_section)
        
        return sections
    
    def _classify_section_type(self, heading: str) -> str:
        """Classify section type based on heading"""
        heading_lower = heading.lower()
        
        if any(keyword in heading_lower for keyword in ['party', 'between']):
            return "parties"
        elif any(keyword in heading_lower for keyword in ['recital', 'whereas']):
            return "recitals"
        elif any(keyword in heading_lower for keyword in ['term', 'condition']):
            return "terms"
        elif any(keyword in heading_lower for keyword in ['obligation', 'duty', 'responsibility']):
            return "obligations"
        elif any(keyword in heading_lower for keyword in ['payment', 'fee', 'compensation']):
            return "payment"
        elif any(keyword in heading_lower for keyword in ['termination', 'expiration']):
            return "termination"
        elif any(keyword in heading_lower for keyword in ['jurisdiction', 'governing law']):
            return "jurisdiction"
        elif any(keyword in heading_lower for keyword in ['signature', 'witness']):
            return "signatures"
        else:
            return "general"
    
    def _extract_title_from_content(self, content: str, contract_type: str) -> str:
        """Extract title from contract content"""
        lines = content.split('\n')
        for line in lines:
            if line.strip() and len(line.strip()) < 100:  # Reasonable title length
                if any(keyword in line.lower() for keyword in ['agreement', 'contract', 'deed']):
                    return line.strip()
        
        # Fallback titles based on contract type
        type_titles = {
            "land_agreement": "Land Agreement",
            "employment_contract": "Employment Agreement", 
            "service_agreement": "Service Agreement",
            "nda": "Non-Disclosure Agreement",
            "partnership_agreement": "Partnership Agreement",
            "lease_agreement": "Lease Agreement"
        }
        
        return type_titles.get(contract_type, "Contract Agreement")
    
    def _create_drafts_from_sections(self, sections: List[Dict[str, Any]]) -> Dict[str, str]:
        """Create draft content from sections"""
        drafts = {}
        for i, section in enumerate(sections):
            section_key = section.get("heading", f"Section_{i+1}")
            drafts[section_key] = section.get("content", "")
        return drafts
    
    async def _generate_fallback_contract(self, extracted_data: Dict[str, Any], contract_type: str) -> Dict[str, Any]:
        """Generate a basic fallback contract when AI generation fails"""
        logger.warning("Using fallback contract generation")
        
        basic_sections = [
            {
                "heading": "AGREEMENT",
                "content": f"This Agreement is made between {', '.join(extracted_data.get('parties', ['Party A', 'Party B']))}.",
                "type": "parties"
            },
            {
                "heading": "TERMS AND CONDITIONS", 
                "content": "Standard terms and conditions apply as per Indian Contract Act, 1872.",
                "type": "terms"
            }
        ]
        
        return {
            "title": f"{contract_type.replace('_', ' ').title()} Agreement",
            "sections": basic_sections,
            "drafts": self._create_drafts_from_sections(basic_sections),
            "metadata": {"source": "fallback", "ai_generated": False}
        }
    
    async def analyze_missing_data(self, extracted_data: Dict[str, Any], contract_type: str = "", reference_template: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze extracted data to identify missing information and generate questions
        Uses AI to analyze the raw content without predefined templates
        """
        if not self.llm:
            logger.warning("AI model not available, cannot perform AI-driven analysis")
            return {
                "missing_data": [],
                "first_question": "What additional information do you have about this contract?",
                "available_data": {}
            }
            
        try:
            logger.info("Analyzing missing data using AI-driven analysis")
            
            # Get the raw text content for AI analysis
            raw_text = extracted_data.get("raw_text", "")
            if not raw_text:
                logger.warning("No raw text available for AI analysis")
                return {
                    "missing_data": [],
                    "first_question": "What additional information do you have about this contract?",
                    "available_data": {}
                }
            
            prompt = f"""
            You are an expert legal contract analyst. Analyze the following contract document content and identify ONLY the most critical missing information needed to create a complete, legally binding contract according to Indian law.

            CONTRACT DOCUMENT CONTENT:
            {raw_text[:6000]}  # Limit content for token efficiency

            IMPORTANT INSTRUCTIONS:
            1. FIRST, analyze what type of contract this is (employment, lease, service, partnership, etc.)
            2. THEN, identify ONLY the information that is TRULY MISSING from the document
            3. Do NOT identify information that is already clearly present in the document
            4. Focus on the TOP 5 most important missing fields only
            5. Consider what information is essential for contract validity and enforceability under Indian law
            6. Be very selective - only identify critical missing information

            For each missing item, provide:
            - field: specific field name (e.g., "party_names", "contract_duration", "payment_amount")
            - description: clear description of what's missing
            - reason: why this information is legally required
            - priority: high/medium/low (high = essential for contract validity)
            - question: specific question to ask the user to get this information

            IMPORTANT: If the document already contains comprehensive information and nothing critical is missing, return an empty missing_data array.

            Provide your analysis in this exact JSON format:
            {{
                "contract_type": "detected_contract_type_here",
                "missing_data": [
                    {{
                        "field": "party_names",
                        "description": "Full legal names of all parties",
                        "reason": "Required to identify the contracting parties",
                        "priority": "high",
                        "question": "What are the full legal names of all parties involved in this contract?"
                    }},
                    {{
                        "field": "contract_duration",
                        "description": "Start and end dates of the contract",
                        "reason": "Required to define the contract term",
                        "priority": "high", 
                        "question": "What is the start date and duration of this contract?"
                    }}
                ],
                "first_question": "What are the full legal names of all parties involved in this contract?",
                "analysis_summary": "Brief summary of what was found in the document and what's missing"
            }}
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a meticulous legal contract analyst. Analyze contract documents and identify ONLY truly missing information. Be selective and accurate."),
                HumanMessage(content=prompt)
            ])
            
            # Parse the AI response as JSON with better error handling
            try:
                import json
                # Try to extract JSON from the response if it's wrapped in other text
                content = response.content.strip()
                
                # Look for JSON pattern in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    analysis = json.loads(json_str)
                    logger.info(f"AI-driven missing data analysis completed: {len(analysis.get('missing_data', []))} items identified")
                    return analysis
                else:
                    # If no JSON found, try to parse the entire response
                    analysis = json.loads(content)
                    logger.info(f"AI-driven missing data analysis completed: {len(analysis.get('missing_data', []))} items identified")
                    return analysis
            except json.JSONDecodeError as e:
                logger.warning(f"AI response not in JSON format: {e}, using fallback")
                logger.debug(f"AI response content: {response.content[:500]}...")
                return {
                    "contract_type": "unknown",
                    "missing_data": [],
                    "first_question": "What additional information do you have about this contract?",
                    "analysis_summary": "AI analysis failed to parse response"
                }
            
        except Exception as e:
            logger.error(f"Error analyzing missing data with AI: {e}")
            return {
                "contract_type": "unknown",
                "missing_data": [],
                "first_question": "What additional information do you have about this contract?",
                "analysis_summary": "AI analysis failed due to error"
            }
    
    def _get_comprehensive_missing_data_analysis(self, extracted_data: Dict[str, Any], contract_type: str) -> Dict[str, Any]:
        """Fallback method when AI is not available - returns minimal missing data"""
        logger.warning("Using fallback missing data analysis - AI model not available")
        return {
            "contract_type": "unknown",
            "missing_data": [],
            "first_question": "What additional information do you have about this contract?",
            "analysis_summary": "AI analysis not available - using fallback"
        }

    async def extract_info_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract structured contract information from user-provided text
        """
        if not self.llm:
            logger.warning("AI model not available, cannot extract structured information from text")
            return {}
            
        try:
            logger.info(f"Extracting structured contract information from user text: {len(text)} characters")
            
            prompt = f"""
            You are a legal document analyst. Extract structured contract information from the following user-provided text.

            USER TEXT:
            {text[:3000]}  # Limit for token efficiency

            Extract the following information if mentioned in the text:
            1. Parties involved (names, roles)
            2. Contract duration, start/end dates
            3. Payment terms, amounts, schedules
            4. Key obligations and responsibilities
            5. Termination conditions
            6. Jurisdiction or governing law
            7. Any other key contract terms

            Return the extracted information in this JSON format:
            {{
                "parties": ["Party Name 1", "Party Name 2"],
                "duration": {{
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD",
                    "duration": "description"
                }},
                "payment_terms": {{
                    "amount": "amount",
                    "currency": "currency",
                    "schedule": "payment schedule"
                }},
                "obligations": ["obligation 1", "obligation 2"],
                "key_terms": ["term 1", "term 2"],
                "termination_clauses": ["clause 1", "clause 2"],
                "jurisdiction": "jurisdiction"
            }}

            Only include fields that are explicitly mentioned in the text. If a field is not mentioned, omit it from the response.
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a legal document analyst. Extract structured contract information from user text. Return only valid JSON."),
                HumanMessage(content=prompt)
            ])
            
            # Parse the response with better error handling
            try:
                import json
                # Try to extract JSON from the response if it's wrapped in other text
                content = response.content.strip()
                
                # Look for JSON pattern in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    extracted_info = json.loads(json_str)
                    logger.info(f"Successfully extracted structured information from user text")
                    return extracted_info
                else:
                    # If no JSON found, try to parse the entire response
                    extracted_info = json.loads(content)
                    logger.info(f"Successfully extracted structured information from user text")
                    return extracted_info
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI response as JSON for text extraction: {e}")
                logger.debug(f"AI response content: {response.content[:500]}...")
                
                # CRITICAL FIX: If JSON parsing fails, create a basic structure from the text
                # This ensures the system doesn't fail completely when AI returns non-JSON
                logger.info("Creating fallback extracted data from text input")
                fallback_data = {
                    "parties": [],
                    "key_terms": [],
                    "obligations": [],
                    "payment_terms": {},
                    "raw_text": text,  # Store the original text as raw_text
                    "summary": f"Contract information extracted from user text: {text[:200]}...",
                    "source": "text_input_fallback"
                }
                
                # Try to extract basic information using simple text parsing
                if "party" in text.lower() or "between" in text.lower():
                    fallback_data["parties"] = ["Party A", "Party B"]
                
                if "payment" in text.lower() or "amount" in text.lower() or "price" in text.lower():
                    fallback_data["payment_terms"] = {"terms": "Payment terms mentioned in text"}
                
                if "duration" in text.lower() or "term" in text.lower() or "period" in text.lower():
                    fallback_data["duration"] = {"duration": "Contract duration mentioned in text"}
                
                logger.info(f"Created fallback extracted data with {len(fallback_data.get('parties', []))} parties")
                return fallback_data
                
        except Exception as e:
            logger.error(f"Error extracting information from text: {e}")
            
            # CRITICAL FIX: Always return at least basic structure to prevent system failure
            fallback_data = {
                "parties": [],
                "key_terms": [],
                "obligations": [],
                "payment_terms": {},
                "raw_text": text,
                "summary": f"Contract information from user text (extraction failed: {str(e)})",
                "source": "text_input_error_fallback"
            }
            return fallback_data
