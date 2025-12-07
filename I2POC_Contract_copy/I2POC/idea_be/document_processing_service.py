import os
import tempfile
import logging
from typing import Dict, Any, List
import asyncio
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import re

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Service for processing uploaded contract documents and extracting information using AI"""
    
    def __init__(self):
        self.supported_formats = ['.docx', '.doc', '.pdf', '.txt']
        # Initialize LLM for document analysis - try multiple API key environment variables
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
                        temperature=0.1
                    )
                    logger.info(f"Azure OpenAI model initialized: {deployment_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Azure OpenAI, falling back to standard OpenAI: {e}")
                    # Fallback to standard OpenAI
                    if openai_key:
                        self.llm = ChatOpenAI(
                            model_name="gpt-4",
                            temperature=0.1,
                            openai_api_key=openai_key
                        )
                        logger.info("Standard OpenAI model initialized: gpt-4")
                    else:
                        self.llm = None
            elif openai_key:
                # Use standard OpenAI
                self.llm = ChatOpenAI(
                    model_name="gpt-4",
                    temperature=0.1,
                    openai_api_key=openai_key
                )
                logger.info("Standard OpenAI model initialized: gpt-4")
            else:
                logger.warning("No valid API configuration found. AI features will be disabled.")
                self.llm = None
    
    async def process_sample_contract(self, file_path: str, contract_type: str, description: str = "") -> Dict[str, Any]:
        """
        Process a sample contract to extract structure and format for template creation using AI
        """
        try:
            logger.info(f"Processing sample contract: {file_path}, type: {contract_type}")
            
            # Extract file extension
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Extract text content based on file type
            text_content = await self._extract_text_from_file(file_path, file_extension)
            
            # Auto-detect contract type if not provided using AI
            if not contract_type:
                contract_type = await self._detect_contract_type_with_ai(text_content)
            
            # Use AI for comprehensive analysis including structure and document type
            try:
                ai_analysis = await self._analyze_contract_with_ai(text_content, contract_type)
                use_ai = True
            except Exception as ai_error:
                logger.warning(f"AI analysis failed, using basic processing: {ai_error}")
                ai_analysis = {}
                use_ai = False
            
            # Use AI analysis if successful, otherwise use basic structure
            if use_ai and ai_analysis:
                structure = ai_analysis.get("structure", {})
                sections = ai_analysis.get("sections", [])
                key_information = ai_analysis.get("key_information", {})
                # Update contract type with AI-detected type if available
                detected_type = ai_analysis.get("detected_contract_type")
                if detected_type:
                    contract_type = detected_type
            else:
                structure = await self._analyze_contract_structure(text_content)
                sections = structure.get("sections", [])
                key_information = await self._extract_key_information(text_content, contract_type)
            
            template_data = {
                "contract_type": contract_type,
                "description": description,
                "file_path": file_path,
                "file_extension": file_extension,
                "structure": structure,
                "sections": sections,
                "key_information": key_information,
                "sample_content": text_content[:5000],  # Store first 5000 chars as sample
                "total_sections": len(sections),
                "ai_analysis": ai_analysis.get("analysis", {}) if use_ai else {"method": "basic_processing"},
                "metadata": {
                    "word_count": len(text_content.split()),
                    "section_count": len(sections),
                    "has_signature_block": "signature" in text_content.lower(),
                    "has_parties_section": any(keyword in text_content.lower() for keyword in ["party", "parties", "between"]),
                    "ai_analyzed": use_ai
                }
            }
            
            logger.info(f"Successfully processed sample contract with {len(sections)} sections (AI: {use_ai})")
            return template_data
            
        except Exception as e:
            logger.error(f"Error processing sample contract: {e}")
            # Fallback to basic processing
            return await self._process_sample_contract_basic(file_path, contract_type, description)
    
    async def _process_sample_contract_basic(self, file_path: str, contract_type: str, description: str) -> Dict[str, Any]:
        """Basic fallback processing without AI"""
        file_extension = os.path.splitext(file_path)[1].lower()
        text_content = await self._extract_text_from_file(file_path, file_extension)
        structure = await self._analyze_contract_structure(text_content)
        key_info = await self._extract_key_information(text_content, contract_type)
        
        return {
            "contract_type": contract_type,
            "description": description,
            "file_path": file_path,
            "file_extension": file_extension,
            "structure": structure,
            "sections": structure.get("sections", []),
            "key_information": key_info,
            "sample_content": text_content[:5000],
            "total_sections": len(structure.get("sections", [])),
            "metadata": {
                "word_count": len(text_content.split()),
                "section_count": len(structure.get("sections", [])),
                "has_signature_block": "signature" in text_content.lower(),
                "has_parties_section": any(keyword in text_content.lower() for keyword in ["party", "parties", "between"]),
                "ai_analyzed": False
            }
        }
    
    async def extract_contract_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extract contract data from uploaded document - ONLY extract raw text
        Let LLM decide what's missing for complete contract
        """
        try:
            logger.info(f"Extracting contract data from: {file_path}")
            
            file_extension = os.path.splitext(file_path)[1].lower()
            logger.info(f"File extension: {file_extension}")
            
            # Extract ONLY raw text - no predefined fields
            raw_text = await self._extract_text_from_file(file_path, file_extension)
            logger.info(f"Extracted raw text length: {len(raw_text)}")
            
            # Return only raw text - let LLM analyze what's missing
            extracted_data = {
                "raw_text": raw_text,
                "summary": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
            }
            
            logger.info(f"Successfully extracted raw text only - no predefined fields")
            logger.info(f"Raw text length: {len(extracted_data.get('raw_text', ''))}")
            logger.info(f"Extracted data keys: {list(extracted_data.keys())}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting contract data: {e}")
            raise
    
    async def _extract_text_from_file(self, file_path: str, file_extension: str) -> str:
        """Extract text content from different file formats"""
        try:
            logger.info(f"Extracting text from file: {file_path}, extension: {file_extension}")
            
            if file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"TXT file extracted, length: {len(content)}")
                    return content
            
            elif file_extension == '.pdf':
                # For PDF processing, we would use PyPDF2 or similar
                # This is a simplified version
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = ""
                        for i, page in enumerate(pdf_reader.pages):
                            page_text = page.extract_text()
                            text += page_text
                            logger.info(f"PDF page {i+1} extracted, length: {len(page_text)}")
                        logger.info(f"Total PDF text extracted, length: {len(text)}")
                        return text
                except ImportError:
                    logger.warning("PyPDF2 not available, using fallback PDF text extraction")
                    return f"PDF content from {file_path} - install PyPDF2 for proper extraction"
                except Exception as pdf_error:
                    logger.error(f"PDF extraction error: {pdf_error}")
                    return f"Error extracting PDF: {str(pdf_error)}"
            
            elif file_extension in ['.docx', '.doc']:
                # For Word documents, we would use python-docx
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    logger.info(f"DOCX file extracted, length: {len(text)}")
                    return text
                except ImportError:
                    logger.warning("python-docx not available, using fallback DOCX text extraction")
                    return f"Word document content from {file_path} - install python-docx for proper extraction"
                except Exception as docx_error:
                    logger.error(f"DOCX extraction error: {docx_error}")
                    return f"Error extracting DOCX: {str(docx_error)}"
            
            else:
                error_msg = f"Unsupported file format: {file_extension}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
        except Exception as e:
            logger.error(f"Error extracting text from file: {e}")
            return f"Error extracting text: {str(e)}"
    
    async def _analyze_contract_structure(self, text_content: str) -> Dict[str, Any]:
        """Analyze contract structure and identify sections"""
        lines = text_content.split('\n')
        sections = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect section headers (typically in uppercase, numbered, or have specific patterns)
            if (line.isupper() or 
                line.startswith('ARTICLE') or 
                line.startswith('SECTION') or
                line.startswith('CLAUSE') or
                any(line.lower().startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.'])):
                
                if current_section:
                    sections.append(current_section)
                
                current_section = {
                    "heading": line,
                    "content": "",
                    "subsections": []
                }
            elif current_section:
                current_section["content"] += line + "\n"
        
        if current_section:
            sections.append(current_section)
        
        return {
            "sections": sections,
            "total_sections": len(sections),
            "estimated_complexity": "High" if len(sections) > 10 else "Medium" if len(sections) > 5 else "Low"
        }
    
    async def _generate_summary(self, text_content: str) -> str:
        """Generate a summary of the contract content"""
        # This would typically use an AI model for summarization
        # For now, return first 200 characters as a simple summary
        return text_content[:200] + "..." if len(text_content) > 200 else text_content
    
    async def _extract_parties(self, text_content: str) -> List[str]:
        """Extract parties involved in the contract"""
        # Simple pattern matching for party names
        parties = []
        lines = text_content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['between', 'party', 'parties']):
                # Extract potential party names
                if 'between' in line_lower:
                    parties.extend(self._extract_names_from_line(line))
        
        return list(set(parties)) if parties else []
    
    async def _extract_key_terms(self, text_content: str) -> List[Dict[str, str]]:
        """Extract key terms and definitions"""
        key_terms = []
        lines = text_content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['shall', 'must', 'will', 'agree', 'obligation']):
                key_terms.append({
                    "term": line[:50] + "..." if len(line) > 50 else line,
                    "type": "obligation"
                })
        
        return key_terms[:10]  # Return top 10 terms
    
    async def _extract_obligations(self, text_content: str) -> List[str]:
        """Extract obligations from contract"""
        obligations = []
        lines = text_content.split('\n')
        
        for line in lines:
            if 'shall' in line.lower() or 'must' in line.lower():
                obligations.append(line.strip())
        
        return obligations[:5]  # Return top 5 obligations
    
    async def _extract_payment_terms(self, text_content: str) -> Dict[str, Any]:
        """Extract payment terms"""
        payment_keywords = ['payment', 'fee', 'price', 'amount', 'consideration', 'compensation']
        lines = text_content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in payment_keywords):
                return {
                    "terms": line.strip(),
                    "currency": self._extract_currency(line),
                    "amount": self._extract_amount(line)
                }
        
        return {}
    
    async def _extract_duration(self, text_content: str) -> Dict[str, str]:
        """Extract contract duration"""
        duration_keywords = ['term', 'duration', 'period', 'validity']
        lines = text_content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in duration_keywords):
                return {
                    "duration": line.strip(),
                    "start_date": "",
                    "end_date": ""
                }
        
        return {}
    
    async def _extract_termination_clauses(self, text_content: str) -> List[str]:
        """Extract termination clauses"""
        termination_keywords = ['termination', 'terminate', 'end', 'expire']
        clauses = []
        lines = text_content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in termination_keywords):
                clauses.append(line.strip())
        
        return clauses[:3]  # Return top 3 clauses
    
    async def _extract_jurisdiction(self, text_content: str) -> str:
        """Extract jurisdiction information"""
        jurisdiction_keywords = ['jurisdiction', 'governing law', 'laws of', 'courts of']
        lines = text_content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in jurisdiction_keywords):
                if 'india' in line.lower():
                    return "India"
                elif 'delhi' in line.lower():
                    return "Delhi, India"
        
        return ""  # No default jurisdiction
    
    def _extract_names_from_line(self, line: str) -> List[str]:
        """Extract potential party names from a line"""
        # Simple name extraction - in real implementation, use more sophisticated NLP
        words = line.split()
        names = []
        for i, word in enumerate(words):
            if word.isupper() and len(word) > 2:
                names.append(word)
        return names
    
    def _extract_currency(self, line: str) -> str:
        """Extract currency from line"""
        currencies = ['INR', 'USD', 'EUR', 'GBP']
        for currency in currencies:
            if currency in line:
                return currency
        return ""  # No default currency
    
    def _extract_amount(self, line: str) -> str:
        """Extract amount from line"""
        # Simple amount extraction
        import re
        amounts = re.findall(r'[\d,]+\.?\d*', line)
        return amounts[0] if amounts else "Not specified"
    
    async def _detect_contract_type_with_ai(self, text_content: str) -> str:
        """Use AI to detect contract type from document content"""
        if not self.llm:
            logger.warning("AI model not available, using basic contract type detection")
            return await self._detect_contract_type_basic(text_content)
        
        try:
            prompt = f"""
            Analyze the following contract document and determine its type:

            Document Content: {text_content[:3000]}

            Please identify the type of contract from these categories:
            - land_agreement (land, property, real estate agreements)
            - employment_contract (employment, employee agreements)
            - service_agreement (service, consulting agreements)
            - nda (non-disclosure, confidentiality agreements)
            - partnership_agreement (partnership, joint venture agreements)
            - lease_agreement (lease, rental, tenancy agreements)
            - general (other types of contracts)

            Return only the contract type as a single word from the categories above.
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a legal document analyst. Identify the type of contract from the document content."),
                HumanMessage(content=prompt)
            ])
            
            detected_type = response.content.strip().lower()
            logger.info(f"AI detected contract type: {detected_type}")
            return detected_type
            
        except Exception as e:
            logger.error(f"Error detecting contract type with AI: {e}")
            # Fallback to basic detection
            return await self._detect_contract_type_basic(text_content)
    
    async def _detect_contract_type_basic(self, text_content: str) -> str:
        """Basic contract type detection using keyword matching"""
        text_lower = text_content.lower()
        
        if any(keyword in text_lower for keyword in ['land', 'property', 'real estate', 'plot']):
            return "land_agreement"
        elif any(keyword in text_lower for keyword in ['employment', 'employee', 'employer', 'salary']):
            return "employment_contract"
        elif any(keyword in text_lower for keyword in ['service', 'consulting', 'professional services']):
            return "service_agreement"
        elif any(keyword in text_lower for keyword in ['nda', 'non-disclosure', 'confidentiality']):
            return "nda"
        elif any(keyword in text_lower for keyword in ['partnership', 'partner', 'joint venture']):
            return "partnership_agreement"
        elif any(keyword in text_lower for keyword in ['lease', 'rent', 'tenancy', 'landlord']):
            return "lease_agreement"
        else:
            return "general"
    
    async def _extract_key_information(self, text_content: str, contract_type: str) -> Dict[str, Any]:
        """Extract key information from contract content"""
        key_info = {
            "parties": await self._extract_parties(text_content),
            "payment_terms": await self._extract_payment_terms(text_content),
            "duration": await self._extract_duration(text_content),
            "jurisdiction": await self._extract_jurisdiction(text_content),
            "key_terms": await self._extract_key_terms(text_content),
            "obligations": await self._extract_obligations(text_content),
            "termination_clauses": await self._extract_termination_clauses(text_content)
        }
        
        return key_info
    
    async def _analyze_contract_with_ai(self, text_content: str, contract_type: str) -> Dict[str, Any]:
        """Use AI to analyze contract structure and extract key information"""
        if not self.llm:
            logger.warning("AI model not available, using basic contract analysis")
            return {
                "structure": await self._analyze_contract_structure(text_content),
                "sections": [],
                "key_information": {},
                "analysis": {"error": "AI model not available, using basic extraction"}
            }
        
        try:
            prompt = f"""
            Analyze the following contract document and extract structured information:

            Document Content: {text_content[:4000]}  # Limit for token efficiency

            Please provide a comprehensive analysis including:
            1. Document structure with sections and subsections
            2. Key parties involved
            3. Main obligations and responsibilities
            4. Payment terms and financial details
            5. Duration and termination clauses
            6. Jurisdiction and governing law
            7. Key legal terms and definitions
            8. Compliance with Indian contract law
            9. Detected contract type (land_agreement, employment_contract, service_agreement, nda, partnership_agreement, lease_agreement, general)

            Provide the analysis in a structured JSON format with the following sections:
            - structure: overall document structure
            - sections: detailed section breakdown
            - key_information: extracted key data points
            - analysis: comprehensive analysis notes
            - detected_contract_type: the detected contract type
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a legal document analyst specializing in Indian contract law. Extract structured information from contract documents."),
                HumanMessage(content=prompt)
            ])
            
            # Parse the AI response to extract structured data
            ai_analysis = self._parse_ai_contract_analysis(response.content)
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing contract with AI: {e}")
            # Return basic structure if AI analysis fails
            return {
                "structure": await self._analyze_contract_structure(text_content),
                "sections": [],
                "key_information": {},
                "analysis": {"error": "AI analysis failed, using basic extraction"}
            }
    
    def _parse_ai_contract_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI analysis response into structured data"""
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        # or use structured output from the LLM
        
        analysis = {
            "structure": {},
            "sections": [],
            "key_information": {},
            "analysis": {},
            "detected_contract_type": "general"
        }
        
        # Basic parsing logic - extract sections and key information
        lines = ai_response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            # Detect section headers
            if (line.isupper() or 
                line.startswith('##') or 
                line.startswith('**') or
                any(line.lower().startswith(prefix) for prefix in ['section', 'article', 'clause'])):
                
                if current_section:
                    analysis["sections"].append(current_section)
                
                current_section = {
                    "heading": line.replace('##', '').replace('**', '').strip(),
                    "content": "",
                    "type": self._classify_section_type(line)
                }
            elif current_section and line:
                current_section["content"] += line + " "
        
        if current_section:
            analysis["sections"].append(current_section)
        
        # Extract key information patterns
        analysis["key_information"] = self._extract_key_info_from_ai_response(ai_response)
        analysis["analysis"] = {"summary": "AI analysis completed"}
        
        # Try to detect contract type from AI response
        if 'land' in ai_response.lower() or 'property' in ai_response.lower():
            analysis["detected_contract_type"] = "land_agreement"
        elif 'employment' in ai_response.lower():
            analysis["detected_contract_type"] = "employment_contract"
        elif 'service' in ai_response.lower():
            analysis["detected_contract_type"] = "service_agreement"
        elif 'nda' in ai_response.lower() or 'confidential' in ai_response.lower():
            analysis["detected_contract_type"] = "nda"
        elif 'partnership' in ai_response.lower():
            analysis["detected_contract_type"] = "partnership_agreement"
        elif 'lease' in ai_response.lower() or 'rent' in ai_response.lower():
            analysis["detected_contract_type"] = "lease_agreement"
        
        return analysis
    
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
    
    def _extract_key_info_from_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Extract key information from AI response"""
        key_info = {}
        
        # No predefined content - only extract what's actually in the AI response
        return key_info
