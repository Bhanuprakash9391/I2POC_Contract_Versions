from typing import Dict, Any, List
import logging
import uuid
from datetime import datetime
from fastapi import HTTPException
from contract_template_service import ContractTemplateService
from ai_contract_scoring_service import ai_contract_scoring_service
from idea_service import IdeaService
from models import IdeaStatus
from logging_config import log_ai_operation, log_database_operation, log_catalog_operation

logger = logging.getLogger(__name__)

class ContractGenerationService:
    def __init__(self, idea_service: IdeaService):
        self.idea_service = idea_service
        self.template_service = ContractTemplateService()
    
    async def generate_contract_with_questions(
        self, 
        extracted_data: Dict[str, Any], 
        contract_type: str = "",
        reference_template_id: str = "",
        additional_info: str = "",
        file: Any = None
    ) -> Dict[str, Any]:
        """Generate a contract with interactive questions"""
        try:
            # Get reference template if provided
            reference_template = None
            if reference_template_id:
                reference_template = await self.idea_service.get_template_by_id(reference_template_id)
            
            # Create a new session
            session_id = str(uuid.uuid4())
            
            # Determine title based on input source
            if file and file.filename:
                title = f"Contract from {file.filename}"
            elif additional_info and additional_info.strip():
                title = "Contract from Text Input"
            else:
                title = "Generated Contract"
            
            # Initialize session with extracted data and template
            initial_state = {
                "session_id": session_id,
                "extracted_data": extracted_data,
                "reference_template": reference_template,
                "contract_type": contract_type,
                "additional_info": additional_info,
                "conversation_history": [],
                "missing_data": [],
                "current_question": None,
                "generated_contract": None,
                "status": "initialized"
            }
            
            # Store session in database
            initial_session_data = {
                "session_id": session_id,
                "title": title,
                "original_idea": extracted_data.get("summary", ""),
                "rephrased_idea": extracted_data.get("summary", ""),
                "sections": [],
                "drafts": {},
                "all_drafts": {},
                "conversation_history": [],
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "total_questions_asked": 0,
                    "submitted_by": "document_upload" if file else "text_input",
                    "department": "Legal",
                    "is_poc_document": True,
                    "sections_count": 0,
                    "source": "document_upload_interactive" if file else "text_input",
                    "contract_type": contract_type,
                    "reference_template_id": reference_template_id,
                    "has_additional_info": bool(additional_info and additional_info.strip())
                },
                "dexko_context": {
                    "user_id": "document_upload" if file else "text_input",
                    "department": "Legal",
                    "role": "System",
                    "location": "India",
                    "language": "en"
                },
                "status": IdeaStatus.IN_PROGRESS,
                "interactive_data": initial_state
            }
            
            # Create the initial session
            await self.idea_service.save_or_update_idea(session_id, initial_session_data)
            
            log_catalog_operation("CREATE", session_id, {
                "title": initial_session_data["title"],
                "status": "IN_PROGRESS",
                "source": "document_upload_interactive" if file else "text_input",
                "has_additional_info": bool(additional_info and additional_info.strip())
            })
            
            # Use AI to analyze missing data and generate first question
            analysis_result = await self.template_service.analyze_missing_data(
                extracted_data, 
                contract_type, 
                reference_template
            )
            
            # Update session with analysis
            initial_state["missing_data"] = analysis_result.get("missing_data", [])
            initial_state["current_question"] = analysis_result.get("first_question")
            initial_state["status"] = "awaiting_input"
            
            # Update the session with the analysis results
            await self.idea_service.save_or_update_idea(session_id, {
                "interactive_data": initial_state
            })
            
            log_ai_operation("ANALYZE_MISSING_DATA", session_id, {
                "missing_data_count": len(analysis_result.get("missing_data", [])),
                "has_first_question": bool(analysis_result.get("first_question")),
                "had_additional_info": bool(additional_info and additional_info.strip())
            })
            
            # Check if we have missing data and need to ask questions
            missing_data_count = len(analysis_result.get("missing_data", []))
            
            response_data = {
                "message": "Contract generation session started successfully",
                "session_id": session_id,
                "missing_data_count": missing_data_count,
                "extracted_info": {
                    "parties": extracted_data.get("parties", []),
                    "key_terms": len(extracted_data.get("key_terms", [])),
                    "obligations": len(extracted_data.get("obligations", [])),
                    "payment_terms": extracted_data.get("payment_terms", {})
                }
            }
            
            # Include missing data details so frontend can show input boxes
            if missing_data_count > 0:
                response_data["missing_data"] = analysis_result.get("missing_data", [])
                response_data["first_question"] = analysis_result.get("first_question")
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error generating contract with questions: {e}")
            raise
    
    async def submit_all_missing_data(
        self, 
        session_id: str, 
        missing_data_responses: Dict[str, str]
    ) -> Dict[str, Any]:
        """Submit all missing data at once and generate final contract"""
        try:
            from logging_config import log_contract_creation
            
            log_contract_creation(session_id, "Contract from Upload", "upload_with_questions", {
                "missing_data_responses": missing_data_responses,
                "missing_data_count": len(missing_data_responses)
            })
            
            # Get the session data
            idea = await self.idea_service.get_idea_by_session(session_id)
            if not idea:
                log_catalog_operation("ERROR", session_id, "Session not found")
                raise HTTPException(status_code=404, detail="Session not found")
            
            log_catalog_operation("FOUND", session_id, {
                "current_status": idea.status,
                "title": idea.title,
                "has_interactive_data": hasattr(idea, 'interactive_data')
            })
            
            interactive_data = getattr(idea, 'interactive_data', {})
            extracted_data = interactive_data.get('extracted_data', {})
            
            # Update the extracted data with all responses
            if 'missing_data_responses' not in extracted_data:
                extracted_data['missing_data_responses'] = {}
            
            # Ensure all responses are properly formatted
            for field, answer in missing_data_responses.items():
                if answer and answer.strip():
                    extracted_data['missing_data_responses'][field] = answer.strip()
            
            # Clear missing data since we're submitting all at once
            interactive_data['missing_data'] = []
            interactive_data['extracted_data'] = extracted_data
            
            # Update conversation history
            conversation_history = interactive_data.get('conversation_history', [])
            for field, answer in missing_data_responses.items():
                conversation_history.append({
                    "role": "user",
                    "content": f"{field}: {answer}",
                    "timestamp": datetime.utcnow()
                })
            interactive_data['conversation_history'] = conversation_history
            
            # Update session
            await self.idea_service.save_or_update_idea(session_id, {
                "interactive_data": interactive_data
            })
            
            log_database_operation("UPDATE", "ideas", session_id, "Updated interactive data")
            
            # Generate final contract with user inputs integrated
            reference_template = interactive_data.get('reference_template')
            contract_type = interactive_data.get('contract_type', '')
            
            # Merge user inputs with extracted data for final contract generation
            enhanced_extracted_data = self._enhance_extracted_data(extracted_data)
            
            # CRITICAL: ALWAYS use the original uploaded document content as the base for the final contract
            raw_text = enhanced_extracted_data.get('raw_text', '')
            if not raw_text:
                # If no raw_text, this is a critical error - we should have extracted it
                log_ai_operation("CRITICAL_ERROR", session_id, {
                    "error": "No raw_text found in enhanced_extracted_data",
                    "extracted_fields": list(extracted_data.keys()),
                    "enhanced_fields": list(enhanced_extracted_data.keys())
                })
                raise HTTPException(status_code=500, detail="Failed to extract content from uploaded document")
            
            log_ai_operation("ENHANCE_DOCUMENT", session_id, {
                "has_raw_text": True,
                "raw_text_length": len(raw_text),
                "contract_type": contract_type
            })
            
            # Create a final contract that combines the original document with user inputs
            final_contract = await self.template_service.generate_indian_law_contract(
                enhanced_extracted_data, 
                contract_type,
                "india"
            )
            
            # Update session with final contract
            interactive_data['generated_contract'] = final_contract
            interactive_data['status'] = 'completed'
            
            # Convert sections to proper format for database using the service method
            sections_data = self.idea_service._convert_sections_to_database_format(final_contract.get("sections", []))
            
            log_catalog_operation("COMPLETE", session_id, {
                "sections_count": len(sections_data),
                "drafts_count": len(final_contract.get("drafts", {})),
                "final_title": final_contract.get("title", "Unknown")
            })
            
            # Update the existing session with final contract data - don't create duplicate
            await self.idea_service.save_or_update_idea(session_id, {
                "interactive_data": interactive_data,
                "drafts": final_contract.get("drafts", {}),
                "all_drafts": final_contract.get("drafts", {}),
                "sections": sections_data,
                "status": IdeaStatus.COMPLETED,
                "title": final_contract.get("title", "Generated Contract")
            })
            
            # Auto-score the contract with AI
            await self._auto_score_contract(session_id, final_contract, extracted_data, contract_type)
            
            log_database_operation("FINAL_SAVE", "ideas", session_id, "Contract marked as COMPLETED and AI scored")
            
            return {
                "type": "end",
                "final_contract": final_contract,
                "message": "Contract generation completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error submitting all missing data: {e}")
            log_catalog_operation("ERROR", session_id, f"Exception: {str(e)}")
            raise
    
    def _enhance_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance extracted data with user responses"""
        enhanced_extracted_data = {**extracted_data}  # This should include raw_text
        
        # Add user responses to the extracted data
        if 'missing_data_responses' in extracted_data:
            # Process each user response and integrate it into the appropriate field
            responses = extracted_data['missing_data_responses']
            
            # Map common field names to extracted data structure
            field_mapping = {
                'party_names': 'parties',
                'contract_duration': 'duration',
                'payment_details': 'payment_terms',
                'obligations': 'obligations',
                'termination_conditions': 'termination_clauses',
                'governing_law': 'jurisdiction',
                'job_title': 'key_terms',
                'salary_details': 'payment_terms',
                'property_details': 'key_terms',
                'consideration_amount': 'payment_terms'
            }
            
            for field, response in responses.items():
                if field in field_mapping:
                    target_field = field_mapping[field]
                    
                    if target_field == 'parties':
                        # Parse party names from response
                        if isinstance(response, str):
                            # Split by commas or newlines to get individual parties
                            parties = [party.strip() for party in response.split(',') if party.strip()]
                            if parties:
                                enhanced_extracted_data['parties'] = parties
                    
                    elif target_field == 'duration':
                        enhanced_extracted_data['duration'] = {
                            'duration': response,
                            'user_provided': True
                        }
                    
                    elif target_field == 'payment_terms':
                        if 'payment_terms' not in enhanced_extracted_data:
                            enhanced_extracted_data['payment_terms'] = {}
                        enhanced_extracted_data['payment_terms']['terms'] = response
                        enhanced_extracted_data['payment_terms']['user_provided'] = True
                    
                    elif target_field == 'jurisdiction':
                        enhanced_extracted_data['jurisdiction'] = response
                    
                    # For other fields, add to key_terms or create new field
                    else:
                        if 'key_terms' not in enhanced_extracted_data:
                            enhanced_extracted_data['key_terms'] = []
                        enhanced_extracted_data['key_terms'].append({
                            'term': field,
                            'value': response,
                            'user_provided': True
                        })
        
        # CRITICAL: Ensure raw_text is preserved in enhanced_extracted_data
        if 'raw_text' not in enhanced_extracted_data and 'raw_text' in extracted_data:
            enhanced_extracted_data['raw_text'] = extracted_data['raw_text']
        
        return enhanced_extracted_data
    
    async def _auto_score_contract(self, session_id: str, final_contract: Dict[str, Any], extracted_data: Dict[str, Any], contract_type: str):
        """Auto-score the contract with AI"""
        try:
            logger.info(f"🤖 Auto-scoring uploaded contract: {session_id} - {final_contract.get('title', 'Generated Contract')}")
            
            # Prepare contract data for AI scoring
            contract_for_scoring = {
                "session_id": session_id,
                "title": final_contract.get("title", "Generated Contract"),
                "department": "Legal",  # Default for uploaded contracts
                "original_idea": extracted_data.get("summary", ""),
                "rephrased_idea": extracted_data.get("summary", ""),
                "drafts": final_contract.get("drafts", {}),
                "all_drafts": final_contract.get("drafts", {}),
                "metadata": {
                    "source": "document_upload_interactive",
                    "contract_type": contract_type,
                    "jurisdiction": "india"
                }
            }
            
            # Score using AI
            score_result = await ai_contract_scoring_service.score_contract(contract_for_scoring)
            
            # Update the contract with AI score - also update evaluation_score for frontend compatibility
            update_data = {
                "ai_score": score_result["score"],
                "ai_feedback": score_result["feedback"],
                "ai_strengths": score_result["strengths"],
                "ai_improvements": score_result["improvements"],
                "ai_risk_level": score_result["risk_level"],
                "evaluation_score": score_result["score"]  # Also set evaluation_score for frontend
            }
            
            # Update metadata with AI scoring info
            try:
                idea = await self.idea_service.get_idea_by_session(session_id)
                if idea and idea.metadata:
                    if hasattr(idea.metadata, 'dict'):
                        metadata = idea.metadata.dict()
                    else:
                        metadata = dict(idea.metadata)
                    
                    metadata["ai_scored_at"] = datetime.utcnow()
                    metadata["auto_scored"] = True
                    metadata["evaluation_score"] = score_result["score"]  # Also set in metadata for frontend
                    update_data["metadata"] = metadata
            except Exception as metadata_error:
                logger.warning(f"Could not update metadata for AI scoring: {metadata_error}")
                # Continue without metadata update if it fails
            
            await self.idea_service.save_or_update_idea(session_id, update_data)
            logger.info(f"✅ Auto-scored uploaded contract {session_id}: {score_result['score']}/100")
            
        except Exception as scoring_error:
            logger.error(f"❌ Auto-scoring failed for uploaded contract {session_id}: {scoring_error}")
            # Continue even if scoring fails - contract is still saved
