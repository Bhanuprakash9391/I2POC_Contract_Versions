from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from fastapi import FastAPI, Query, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
from langgraph.types import Command
from graph_app import graph_app, GraphState
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import tempfile
import shutil
import re
from langchain.schema import HumanMessage, SystemMessage

# MongoDB integration imports
from database import Database, get_ideas_collection
from idea_service import IdeaService
from models import IdeaStatus
from ai_contract_categorization_service import ai_contract_categorization_service
from ai_contract_scoring_service import ai_contract_scoring_service
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Import new services for document processing
from document_processing_service import DocumentProcessingService
from contract_template_service import ContractTemplateService
from contract_generation_service import ContractGenerationService

# Import logging configuration
from logging_config import loggers, log_contract_creation, log_database_operation, log_upload_process, log_catalog_operation, log_ai_operation


logger = logging.getLogger(__name__)

# Lifespan event handler for database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await Database.connect_db()
    # Initialize the global service instance
    global idea_service
    collection = await get_ideas_collection()
    idea_service = IdeaService(collection)
    logger.info("🚀 Application startup complete")
    logger.info("💾 Idea service initialized")

    yield

    # Shutdown
    await Database.close_db()
    logger.info("👋 Application shutdown complete")

app = FastAPI(
    title="AI Idea to Contract Generation API",
    lifespan=lifespan
)

# Add global service instance
idea_service = None

# Add CORS middleware with settings that match frontend requirements
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
    expose_headers=["Content-Type"], 
)

# Session storage
sessions = {}
is_structuring_phase = False


class QueryRequest(BaseModel):
    session_id: str
    query: str
    is_interrupt: bool
    idea_structuring: Dict[str, Any] # 3 keys: idea, title, all_sections

class ChatResponse(BaseModel):
    session_id: str
    type: str
    action: str
    section: Optional[str] = None
    subsection: Optional[str] = None
    question: Optional[str] = None
    reason: Optional[str] = None
    draft: Optional[str] = None
    idea: Optional[str] = None
    title: Optional[str] = None
    all_sections: Optional[List[Dict[str, Any]]] = None
    final_state: Optional[Dict[str, Any]] = None
    # final_draft: Optional[List[Dict[str, str]]] = None

@app.post("/apcontract/chat")
async def chat(request_data: QueryRequest):
    global is_structuring_phase
    
    if not request_data.session_id or request_data.session_id not in sessions:
        session_id = str(uuid.uuid4())

        config = {
            "configurable": {
                "thread_id": session_id
            },
            "recursion_limit": 100
        }

        minimal_state = GraphState(
            idea = "",
            title = "",
            sections=[],
            current_section="",
            current_subsections=[],
            current_section_draft=None,
            conversation_history=[],
            question_asked_for_current_section = 0,
            question_generator_output= None,
            progress={},
            all_drafts={},
            document_generated=False
        )
        # Store the session
        sessions[session_id] = {
            "config": config,
            "state": minimal_state,
        }

        # Don't save initial idea to database automatically
        # Idea will only be saved when user explicitly clicks "Save to Catalog"
        logger.info(f"🆕 Session created for idea: {session_id}")
    else:
        session_id = request_data.session_id

    if request_data.is_interrupt == False:
        state = sessions[session_id]["state"]
        state.idea = request_data.query
        sessions[session_id]["state"] = state

        # Don't save idea to database automatically
        # Idea will only be saved when user explicitly clicks "Save to Catalog"
        logger.info(f"🆕 Idea updated in session: {session_id}")

        return await process_graph_streaming(session_id, None)

    elif request_data.is_interrupt == True:
        if is_structuring_phase:
            is_structuring_phase = False
            return await process_graph_streaming(session_id, request_data.idea_structuring)
        else:
            return await process_graph_streaming(session_id, request_data.query)

async def process_graph_streaming(session_id: str, interrupt_response=None):
    return StreamingResponse(
        process_graph(session_id, interrupt_response),
        media_type="text/event-stream"
    )

async def process_graph(session_id: str, interrupt_response=None):
    session = sessions[session_id]
    global is_structuring_phase
    try:
        if interrupt_response:
            print(f"Resuming execution from interrupt with response: {interrupt_response}")
            resume_cmd = Command(
                resume=interrupt_response
            )

            input_to_stream = resume_cmd

        else:
            print(f"Starting from starting")
            input_to_stream = session["state"]
            
        async for event in graph_app.astream_events(
            input = input_to_stream,
            config=session["config"],
            version="v2"
        ):
            print(f"Event generated")

            if event["event"] == "on_chain_start":
                input_data = event.get("data", {}).get("input")

                if isinstance(input_data, GraphState):
                    sessions[session_id]["state"] = input_data
                    print("✅ Updated session state from on_chain_start")

                    # Don't save state to database automatically
                    # Idea will only be saved when user explicitly clicks "Save to Catalog"
                    print(f"🆕 State updated in session: {session_id}")
            
            if event["event"] == "on_chain_end":
                event_data = event.get("data", {})
                output = event_data.get("output")
                input_data = event_data.get("input")

                # Check if output indicates the final node execution
                if output == "__end__":
                    # Try to update session state if input is GraphState
                    if isinstance(input_data, GraphState):
                        sessions[session_id]["state"] = input_data
                        final_state = input_data

                    elif isinstance(input_data, dict):
                        try:
                            final_state = GraphState(**input_data)
                            sessions[session_id]["state"] = final_state
                        except Exception as e:
                            print(f"⚠️ Couldn't deserialize input_data into GraphState: {e}")
                            final_state = None

                    else:
                        final_state = None

                    print("🎉 All sections complete. Document is ready.")

                    # Save completed document to database
                    if final_state:
                        try:
                            print(f"💾 Attempting to save completed document for session {session_id}")
                            print(f"📝 Final state all_drafts: {final_state.all_drafts}")
                            await idea_service.mark_completed(session_id, final_state.all_drafts)
                            logger.info(f"📄 Document completed and saved for session {session_id}")
                        except Exception as e:
                            logger.error(f"❌ Failed to save completed document: {e}")
                            print(f"🔥 Database save error details: {e}")
                            # Continue with response even if DB save fails

                    # Yield structured finalization response
                    custom_payload = ChatResponse(
                        session_id=session_id,
                        action="generate_document",
                        type = "end",
                        # final_draft = final_state.all_drafts,
                        final_state = jsonable_encoder(final_state) if final_state else {}
                    )
                    yield f"data: {custom_payload.model_dump_json()}\n\n"
                    return

            if event["event"] == "on_chain_stream" and "__interrupt__" in event["data"]["chunk"]:
                
                print(f"Interrupt detected")
                # Store the interrupt details
                interrupt_obj = event["data"]["chunk"]["__interrupt__"][0]
                if hasattr(interrupt_obj, "value"):
                    interrupt_value = interrupt_obj.value
                    print(f"Interrupt value: {interrupt_value}")
                    action = interrupt_value.get("action")
                    print(f"action: {action}")
                    
                current_state = sessions[session_id]["state"]

                if action == "get_structure_review":
                    is_structuring_phase = True
                    custom_payload = ChatResponse(
                        session_id=session_id,
                        type="interrupt",
                        action=action,
                        idea = interrupt_value.get("idea"),
                        title = interrupt_value.get("title"),
                        all_sections = interrupt_value.get("all_sections"),
                        # state = jsonable_encoder(current_state) if current_state else {}
                    )
                    yield f"data: {custom_payload.model_dump_json()}\n\n"
                    return
                
                elif action == "get_question_response":
                    custom_payload = ChatResponse(
                        session_id=session_id,
                        type="interrupt",
                        action=action,
                        section=interrupt_value.get("section"),
                        subsection=interrupt_value.get("subsection"),
                        question=interrupt_value.get("question"),
                        reason=interrupt_value.get("reason"),
                        draft=current_state.current_section_draft.draft if current_state.current_section_draft else "No draft content available",
                        all_sections = current_state.sections,
                        idea = current_state.idea,
                        title = current_state.title
                        # state = jsonable_encoder(current_state) if current_state else {}
                    )
                    yield f"data: {custom_payload.model_dump_json()}\n\n"
                    return
                
                elif action == "get_reviewed_section_draft":
                    custom_payload = ChatResponse(
                            session_id=session_id,
                            type="interrupt",
                            action=action,
                            section=interrupt_value.get("section"),
                            draft=interrupt_value.get("draft"),
                            idea = current_state.idea,
                            title = current_state.title
                            # state = jsonable_encoder(current_state) if current_state else {}
                        )
                    yield f"data: {custom_payload.model_dump_json()}\n\n"
                    return
                
    except Exception as e:
        # This is a real error
        sessions[session_id]["error"] = str(e)
        logger.error(f"Error in process_graph for session {session_id}: {e}")
        # Yield an error response instead of raising exception
        error_payload = ChatResponse(
            session_id=session_id,
            type="error",
            action="error",
            question=f"An error occurred: {str(e)}"
        )
        yield f"data: {error_payload.model_dump_json()}\n\n"

# MongoDB API endpoints
@app.get("/apcontract/contracts")
async def get_all_contracts(limit: int = Query(50, description="Number of contracts to retrieve")):
    """Get all saved contracts"""
    try:
        if idea_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        ideas = await idea_service.get_all_ideas(limit)
        return {"ideas": [idea.dict() for idea in ideas]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/contracts")
async def create_contract(contract_data: dict):
    """Create a new contract and automatically score it with AI"""
    try:
        if idea_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        session_id = str(uuid.uuid4())
        
        # Create a simplified contract document for direct save
        drafts_to_save = contract_data.get("drafts", {}) or contract_data.get("all_drafts", {})
        
        # Convert sections to proper format if provided
        sections_data = []
        if contract_data.get("sections"):
            sections_data = idea_service._convert_sections_to_database_format(contract_data["sections"])
        
        contract_doc_data = {
            "session_id": session_id,
            "title": contract_data.get("title", "Untitled Contract"),
            "original_idea": contract_data.get("idea", ""),
            "rephrased_idea": contract_data.get("idea", ""),
            "sections": sections_data,
            "drafts": drafts_to_save,  # Save the actual draft content
            "all_drafts": drafts_to_save,  # Save to both fields for compatibility
            "conversation_history": [],
            "metadata": contract_data.get("metadata", {}),
            "dexko_context": {
                "user_id": "anonymous",
                "department": contract_data.get("metadata", {}).get("department", "General"),
                "role": "Employee",
                "location": "Unknown",
                "language": "en"
            },
            "status": IdeaStatus.SUBMITTED
        }
        
        # Add metadata fields if they exist
        metadata = contract_data.get("metadata", {})
        if metadata:
            contract_doc_data["metadata"] = {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_questions_asked": 0,
                "submitted_by": metadata.get("submitted_by", "User"),
                "department": metadata.get("department", "General"),
                "is_poc_document": metadata.get("is_poc_document", True),
                "sections_count": metadata.get("sections_count", 0)
            }
        
        # Save the contract first
        await idea_service.save_or_update_idea(session_id, contract_doc_data)
        
        # Automatically score the contract with AI
        try:
            logger.info(f"🤖 Auto-scoring new contract: {session_id} - {contract_data.get('title', 'Untitled Contract')}")
            
            # Convert contract data for AI scoring
            contract_for_scoring = {
                "session_id": session_id,
                "title": contract_data.get("title", "Untitled Contract"),
                "department": metadata.get("department", "General") if metadata else "General",
                "original_idea": contract_data.get("idea", ""),
                "rephrased_idea": contract_data.get("idea", ""),
                "drafts": drafts_to_save,
                "all_drafts": drafts_to_save,
                "metadata": contract_doc_data.get("metadata", {})
            }
            
            # Score using AI
            score_result = await ai_contract_scoring_service.score_contract(contract_for_scoring)
            
            # Update the contract with AI score
            update_data = {
                "ai_score": score_result["score"],
                "ai_feedback": score_result["feedback"],
                "ai_strengths": score_result["strengths"],
                "ai_improvements": score_result["improvements"],
                "ai_risk_level": score_result["risk_level"]
            }
            
            # Update metadata
            if contract_doc_data.get("metadata"):
                metadata = contract_doc_data["metadata"]
                metadata["ai_scored_at"] = datetime.utcnow()
                metadata["auto_scored"] = True
                update_data["metadata"] = metadata
            
            await idea_service.save_or_update_idea(session_id, update_data)
            logger.info(f"✅ Auto-scored contract {session_id}: {score_result['score']}/100")
            
        except Exception as scoring_error:
            logger.error(f"❌ Auto-scoring failed for contract {session_id}: {scoring_error}")
            # Continue even if scoring fails - contract is still saved
        
        return {"message": "Contract created and auto-scored successfully", "session_id": session_id}
    except Exception as e:
        print(f"❌ Error creating contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/apcontract/contracts/{session_id}")
async def get_contract_by_session(session_id: str):
    """Get contract by session ID"""
    try:
        if idea_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        idea = await idea_service.get_idea_by_session(session_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        return idea.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/update-contract-status")
async def update_contract_status(request_data: dict):
    """Update contract status and evaluation score"""
    try:
        if idea_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        session_id = request_data.get("session_id")
        status = request_data.get("status")
        evaluation_score = request_data.get("evaluation_score")
        reviewer_feedback = request_data.get("reviewer_feedback")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Get the existing idea
        existing_idea = await idea_service.get_idea_by_session(session_id)
        if not existing_idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        # Prepare update data
        update_data = {}
        
        if status:
            update_data["status"] = status
        
        # Handle metadata properly - convert to dict if needed
        if existing_idea.metadata:
            if hasattr(existing_idea.metadata, 'dict'):
                metadata = existing_idea.metadata.dict()
            else:
                metadata = dict(existing_idea.metadata)
        else:
            metadata = {}
        
        # Update metadata with evaluation data
        metadata["updated_at"] = datetime.utcnow()
        
        if evaluation_score is not None:
            metadata["evaluation_score"] = evaluation_score
            # Also save at root level for easier access
            update_data["evaluation_score"] = evaluation_score
        
        if reviewer_feedback:
            metadata["reviewer_feedback"] = reviewer_feedback
            # Also save at root level for easier access
            update_data["reviewer_feedback"] = reviewer_feedback
        
        update_data["metadata"] = metadata
        
        # Update the idea in database
        await idea_service.save_or_update_idea(session_id, update_data)
        
        return {
            "message": "Idea status updated successfully",
            "session_id": session_id,
            "status": status,
            "evaluation_score": evaluation_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating idea status: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# Contract Review API endpoints
@app.post("/apcontract/categorize-contracts")
async def categorize_contracts(request_data: dict):
    """Categorize all contracts using AI"""
    try:
        if idea_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        ideas = await idea_service.get_all_ideas(100)  # Get all contracts
        categorized_contracts = {}
        
        for idea in ideas:
            # Convert idea to dict for processing
            idea_dict = idea.dict()
            
            # Categorize using AI
            category_result = await ai_contract_categorization_service.categorize_contract(idea_dict)
            
            # Store in categorized structure
            primary_category = category_result["primary_category"]
            if primary_category not in categorized_contracts:
                categorized_contracts[primary_category] = []
            
            categorized_contracts[primary_category].append({
                "id": idea.session_id,
                "title": idea.title,
                "department": idea.metadata.get("department", "General") if idea.metadata else "General",
                "evaluation_score": idea.metadata.get("evaluation_score") if idea.metadata else None,
                "status": idea.status,
                "ai_category": category_result
            })
        
        return {"categorized_contracts": categorized_contracts}
        
    except Exception as e:
        logger.error(f"Error categorizing contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/score-all-contracts")
async def score_all_contracts():
    """Score all contracts using AI - only score contracts that haven't been scored yet"""
    try:
        if idea_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        ideas = await idea_service.get_all_ideas(100)  # Get all contracts
        scored_count = 0
        already_scored_count = 0
        error_count = 0
        
        logger.info(f"🔍 Starting AI scoring for {len(ideas)} total contracts")
        
        for idea in ideas:
            try:
                # Check if contract already has an AI score
                if idea.ai_score is not None:
                    already_scored_count += 1
                    logger.info(f"Contract {idea.session_id} already has AI score: {idea.ai_score} - skipping")
                    continue
                
                logger.info(f"🎯 Scoring contract: {idea.session_id} - {idea.title}")
                
                # Convert idea to dict for processing
                idea_dict = idea.dict()
                
                # Score using AI
                score_result = await ai_contract_scoring_service.score_contract(idea_dict)
                
                # Update the idea with AI score
                update_data = {
                    "ai_score": score_result["score"],
                    "ai_feedback": score_result["feedback"],
                    "ai_strengths": score_result["strengths"],
                    "ai_improvements": score_result["improvements"],
                    "ai_risk_level": score_result["risk_level"]
                }
                
                # Update metadata
                if idea.metadata:
                    if hasattr(idea.metadata, 'dict'):
                        metadata = idea.metadata.dict()
                    else:
                        metadata = dict(idea.metadata)
                else:
                    metadata = {}
                
                metadata["ai_scored_at"] = datetime.utcnow()
                update_data["metadata"] = metadata
                
                await idea_service.save_or_update_idea(idea.session_id, update_data)
                scored_count += 1
                logger.info(f"✅ Scored contract {idea.session_id}: {score_result['score']}/100")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error scoring contract {idea.session_id}: {e}")
                logger.error(f"Contract details - Title: {idea.title}, Status: {idea.status}")
                continue
        
        logger.info(f"📊 AI scoring summary: {scored_count} scored, {already_scored_count} already scored, {error_count} errors")
        
        return {
            "message": f"AI scoring completed. Scored {scored_count} new contracts, {already_scored_count} contracts already had scores, {error_count} errors.",
            "scored_count": scored_count,
            "already_scored_count": already_scored_count,
            "error_count": error_count,
            "total_contracts": len(ideas)
        }
        
    except Exception as e:
        logger.error(f"Error scoring all contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/force-score-contracts")
async def force_score_contracts():
    """Force score all contracts using AI - even if they already have scores (for testing)"""
    try:
        if idea_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        ideas = await idea_service.get_all_ideas(100)  # Get all contracts
        scored_count = 0
        error_count = 0
        
        logger.info(f"🔍 Starting FORCE AI scoring for {len(ideas)} total contracts")
        
        for idea in ideas:
            try:
                logger.info(f"🎯 Force scoring contract: {idea.session_id} - {idea.title}")
                
                # Convert idea to dict for processing
                idea_dict = idea.dict()
                
                # Score using AI
                score_result = await ai_contract_scoring_service.score_contract(idea_dict)
                
                # Update the idea with AI score
                update_data = {
                    "ai_score": score_result["score"],
                    "ai_feedback": score_result["feedback"],
                    "ai_strengths": score_result["strengths"],
                    "ai_improvements": score_result["improvements"],
                    "ai_risk_level": score_result["risk_level"]
                }
                
                # Update metadata
                if idea.metadata:
                    if hasattr(idea.metadata, 'dict'):
                        metadata = idea.metadata.dict()
                    else:
                        metadata = dict(idea.metadata)
                else:
                    metadata = {}
                
                metadata["ai_scored_at"] = datetime.utcnow()
                metadata["force_scored"] = True
                update_data["metadata"] = metadata
                
                await idea_service.save_or_update_idea(idea.session_id, update_data)
                scored_count += 1
                logger.info(f"✅ Force scored contract {idea.session_id}: {score_result['score']}/100")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error force scoring contract {idea.session_id}: {e}")
                logger.error(f"Contract details - Title: {idea.title}, Status: {idea.status}")
                continue
        
        logger.info(f"📊 FORCE AI scoring summary: {scored_count} scored, {error_count} errors")
        
        return {
            "message": f"FORCE AI scoring completed. Scored {scored_count} contracts, {error_count} errors.",
            "scored_count": scored_count,
            "error_count": error_count,
            "total_contracts": len(ideas)
        }
        
    except Exception as e:
        logger.error(f"Error force scoring all contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        collection = await get_ideas_collection()
        await collection.find_one({})  # Simple query to test connection
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }


# New API endpoints for file upload and document processing
@app.post("/apcontract/upload-sample-contract")
async def upload_sample_contract(
    file: UploadFile = File(...)
):
    """Upload a sample contract template for future reference"""
    try:
        # Validate file type
        allowed_extensions = {'.docx', '.doc', '.pdf', '.txt'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process the document to extract structure and content using AI
            document_service = DocumentProcessingService()
            template_data = await document_service.process_sample_contract(
                temp_file_path, 
                "",  # Empty contract_type - AI will auto-detect
                ""   # Empty description
            )
            
            # Use AI to further analyze the template for better understanding
            template_service = ContractTemplateService()
            enhanced_template = await template_service.analyze_sample_template(template_data)
            
            # Save template to database
            template_id = str(uuid.uuid4())
            enhanced_template["template_id"] = template_id
            enhanced_template["uploaded_at"] = datetime.utcnow()
            
            # Store in database (you might want to create a separate collection for templates)
            await idea_service.save_template(enhanced_template)
            
            return {
                "message": "Sample contract uploaded and analyzed successfully with AI",
                "template_id": template_id,
                "contract_type": enhanced_template.get("contract_type", "auto_detected"),
                "structure": enhanced_template.get("structure", {}),
                "sections_count": len(enhanced_template.get("sections", [])),
                "ai_analyzed": enhanced_template.get("metadata", {}).get("ai_analyzed", False),
                "structure_analysis": enhanced_template.get("structure_analysis", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing sample contract: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process sample contract: {str(e)}")
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}")
                
    except Exception as e:
        logger.error(f"Error uploading sample contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/process-contract-document")
async def process_contract_document(
    file: UploadFile = File(...),
    contract_type: str = Form(""),
    jurisdiction: str = Form("india")
):
    """Process a complete contract document and generate formatted contract according to Indian law"""
    try:
        # Validate file type
        allowed_extensions = {'.docx', '.doc', '.pdf', '.txt'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process the document to extract information
            document_service = DocumentProcessingService()
            extracted_data = await document_service.extract_contract_data(temp_file_path)
            
            # Generate formatted contract according to Indian law
            template_service = ContractTemplateService()
            formatted_contract = await template_service.generate_indian_law_contract(
                extracted_data, 
                contract_type,
                jurisdiction
            )
            
            # Create a new contract in the database
            session_id = str(uuid.uuid4())
            contract_data = {
                "session_id": session_id,
                "title": formatted_contract.get("title", "Generated Contract"),
                "original_idea": extracted_data.get("summary", ""),
                "rephrased_idea": extracted_data.get("summary", ""),
                "sections": formatted_contract.get("sections", []),
                "drafts": formatted_contract.get("drafts", {}),
                "all_drafts": formatted_contract.get("drafts", {}),
                "conversation_history": [],
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "total_questions_asked": 0,
                    "submitted_by": "document_upload",
                    "department": "Legal",
                    "is_poc_document": True,
                    "sections_count": len(formatted_contract.get("sections", [])),
                    "source": "document_upload",
                    "jurisdiction": jurisdiction
                },
                "dexko_context": {
                    "user_id": "document_upload",
                    "department": "Legal",
                    "role": "System",
                    "location": "India",
                    "language": "en"
                },
                "status": IdeaStatus.SUBMITTED
            }
            
            # Save the contract
            await idea_service.save_or_update_idea(session_id, contract_data)
            
            # Auto-score the contract
            try:
                score_result = await ai_contract_scoring_service.score_contract(contract_data)
                update_data = {
                    "ai_score": score_result["score"],
                    "ai_feedback": score_result["feedback"],
                    "ai_strengths": score_result["strengths"],
                    "ai_improvements": score_result["improvements"],
                    "ai_risk_level": score_result["risk_level"]
                }
                await idea_service.save_or_update_idea(session_id, update_data)
            except Exception as scoring_error:
                logger.error(f"Auto-scoring failed for uploaded contract: {scoring_error}")
            
            return {
                "message": "Contract processed and generated successfully",
                "session_id": session_id,
                "title": formatted_contract.get("title", "Generated Contract"),
                "sections_count": len(formatted_contract.get("sections", [])),
                "ai_score": score_result["score"] if 'score_result' in locals() else None
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error processing contract document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/apcontract/templates")
async def get_available_templates():
    """Get available contract templates"""
    try:
        if idea_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        templates = await idea_service.get_all_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/generate-from-template")
async def generate_contract_from_template(request_data: dict):
    """Generate a contract using a specific template and user data"""
    try:
        template_id = request_data.get("template_id")
        user_data = request_data.get("user_data", {})
        
        if not template_id:
            raise HTTPException(status_code=400, detail="template_id is required")
        
        # Get template from database
        template = await idea_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Generate contract using template
        template_service = ContractTemplateService()
        generated_contract = await template_service.generate_from_template(template, user_data)
        
        # Save the generated contract
        session_id = str(uuid.uuid4())
        contract_data = {
            "session_id": session_id,
            "title": generated_contract.get("title", "Template-Based Contract"),
            "original_idea": generated_contract.get("description", ""),
            "rephrased_idea": generated_contract.get("description", ""),
            "sections": generated_contract.get("sections", []),
            "drafts": generated_contract.get("drafts", {}),
            "all_drafts": generated_contract.get("drafts", {}),
            "conversation_history": [],
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_questions_asked": 0,
                "submitted_by": "template_generation",
                "department": "Legal",
                "is_poc_document": True,
                "sections_count": len(generated_contract.get("sections", [])),
                "source": "template",
                "template_id": template_id
            },
            "dexko_context": {
                "user_id": "template_generation",
                "department": "Legal",
                "role": "System",
                "location": "India",
                "language": "en"
            },
            "status": IdeaStatus.SUBMITTED
        }
        
        await idea_service.save_or_update_idea(session_id, contract_data)
        
        return {
            "message": "Contract generated from template successfully",
            "session_id": session_id,
            "title": generated_contract.get("title", "Template-Based Contract")
        }
        
    except Exception as e:
        logger.error(f"Error generating contract from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/generate-contract-with-questions")
async def generate_contract_with_questions(
    file: UploadFile = File(None),
    contract_type: str = Form(""),
    description: str = Form(""),
    reference_template_id: str = Form(""),
    additional_info: str = Form("")
):
    """Generate a contract with interactive questions based on uploaded content and/or user text input"""
    try:
        extracted_data = {}
        
        # Handle file upload if provided
        if file and file.filename:
            # Validate file type
            allowed_extensions = {'.docx', '.doc', '.pdf', '.txt'}
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
                )
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Process the document to extract information
                document_service = DocumentProcessingService()
                extracted_data = await document_service.extract_contract_data(temp_file_path)
                
                # DEBUG: Log the extracted data to verify raw_text is present
                log_ai_operation("EXTRACTED_DATA_DEBUG", "new_session", {
                    "has_raw_text": 'raw_text' in extracted_data,
                    "raw_text_length": len(extracted_data.get('raw_text', '')),
                    "extracted_fields": list(extracted_data.keys()),
                    "file_path": temp_file_path,
                    "file_exists": os.path.exists(temp_file_path)
                })
                
                log_upload_process(file.filename, "new_session", extracted_data)
                
                # CRITICAL: Ensure raw_text is preserved in the initial state
                if 'raw_text' not in extracted_data:
                    logger.error("CRITICAL: raw_text not found in extracted_data after document processing")
                    raise HTTPException(status_code=500, detail="Failed to extract content from uploaded document")
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # Handle text input if provided (can be used independently or with file)
        if additional_info and additional_info.strip():
            logger.info(f"Processing user text input: {len(additional_info)} characters")
            
            # Use AI to extract structured information from the text
            template_service = ContractTemplateService()
            text_extracted_data = await template_service.extract_info_from_text(additional_info)
            
            if text_extracted_data:
                # If we have both file and text data, merge them
                if extracted_data:
                    # Merge parties
                    if text_extracted_data.get('parties'):
                        if 'parties' not in extracted_data:
                            extracted_data['parties'] = []
                        extracted_data['parties'].extend(text_extracted_data['parties'])
                    
                    # Merge key terms
                    if text_extracted_data.get('key_terms'):
                        if 'key_terms' not in extracted_data:
                            extracted_data['key_terms'] = []
                        extracted_data['key_terms'].extend(text_extracted_data['key_terms'])
                    
                    # Merge obligations
                    if text_extracted_data.get('obligations'):
                        if 'obligations' not in extracted_data:
                            extracted_data['obligations'] = []
                        extracted_data['obligations'].extend(text_extracted_data['obligations'])
                    
                    # Merge payment terms
                    if text_extracted_data.get('payment_terms'):
                        if 'payment_terms' not in extracted_data:
                            extracted_data['payment_terms'] = {}
                        extracted_data['payment_terms'].update(text_extracted_data['payment_terms'])
                    
                    logger.info("Successfully merged file data with text input data")
                else:
                    # If only text input, use it as the main data source
                    extracted_data = text_extracted_data
                    logger.info("Using text input as primary data source")
                
                # CRITICAL: For text input, we need to store the raw text as 'raw_text' 
                # so it can be analyzed for missing data just like document upload
                extracted_data['raw_text'] = additional_info
                extracted_data['additional_info'] = additional_info
                extracted_data['source'] = 'text_input' if not file else 'file_and_text'
                
                logger.info(f"Text input processed - raw_text length: {len(additional_info)}")
            else:
                logger.warning("Failed to extract structured information from text input")
        
        # If no file and no text, return error
        if not extracted_data:
            raise HTTPException(
                status_code=400, 
                detail="Please provide either a document file or contract information in the text box"
            )
        
        # Use the new ContractGenerationService
        contract_generation_service = ContractGenerationService(idea_service)
        return await contract_generation_service.generate_contract_with_questions(
            extracted_data=extracted_data,
            contract_type=contract_type,
            reference_template_id=reference_template_id,
            additional_info=additional_info,
            file=file
        )
        
    except Exception as e:
        logger.error(f"Error generating contract with questions: {e}")
        log_upload_process(file.filename if file else "text_input", "ERROR", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

class QuestionRequest(BaseModel):
    session_id: str

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

class SubmitAllMissingDataRequest(BaseModel):
    session_id: str
    missing_data_responses: Dict[str, str]

@app.post("/apcontract/get-next-question")
async def get_next_question(request_data: QuestionRequest):
    """Get the next question for interactive contract generation"""
    try:
        session_id = request_data.session_id
        
        # Get the session data
        idea = await idea_service.get_idea_by_session(session_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Session not found")
        
        interactive_data = getattr(idea, 'interactive_data', {})
        missing_data = interactive_data.get('missing_data', [])
        
        if not missing_data:
            # No more questions - generate final contract
            template_service = ContractTemplateService()
            extracted_data = interactive_data.get('extracted_data', {})
            reference_template = interactive_data.get('reference_template')
            contract_type = interactive_data.get('contract_type', '')
            
            final_contract = await template_service.generate_indian_law_contract(
                extracted_data, 
                contract_type,
                "india"
            )
            
            # Update session with final contract
            interactive_data['generated_contract'] = final_contract
            interactive_data['status'] = 'completed'
            
            await idea_service.save_or_update_idea(session_id, {
                "interactive_data": interactive_data,
                "drafts": final_contract.get("drafts", {}),
                "all_drafts": final_contract.get("drafts", {}),
                "sections": final_contract.get("sections", []),
                "status": IdeaStatus.COMPLETED
            })
            
            return {
                "type": "end",
                "final_contract": final_contract,
                "message": "Contract generation completed successfully"
            }
        
        # Get the next missing data item
        next_item = missing_data[0]
        question = f"Please provide the {next_item.get('field', 'missing information')}: {next_item.get('description', '')}"
        
        return {
            "type": "interrupt",
            "action": "get_question_response",
            "question": question,
            "reason": next_item.get('reason', 'This information is required for the contract'),
            "current_field": next_item.get('field'),
            "remaining_questions": len(missing_data) - 1
        }
        
    except Exception as e:
        logger.error(f"Error getting next question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/submit-answer")
async def submit_answer(request_data: AnswerRequest):
    """Submit answer to current question and get next question or final contract"""
    try:
        session_id = request_data.session_id
        answer = request_data.answer
        
        # Get the session data
        idea = await idea_service.get_idea_by_session(session_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Session not found")
        
        interactive_data = getattr(idea, 'interactive_data', {})
        missing_data = interactive_data.get('missing_data', [])
        extracted_data = interactive_data.get('extracted_data', {})
        
        if not missing_data:
            raise HTTPException(status_code=400, detail="No current question to answer")
        
        # Process the answer - update extracted data with the answer
        current_field = missing_data[0].get('field')
        if current_field:
            # Update the extracted data with the answer
            if 'missing_data_responses' not in extracted_data:
                extracted_data['missing_data_responses'] = {}
            extracted_data['missing_data_responses'][current_field] = answer
        
        # Remove the answered question
        missing_data = missing_data[1:]
        interactive_data['missing_data'] = missing_data
        interactive_data['extracted_data'] = extracted_data
        
        # Update conversation history
        conversation_history = interactive_data.get('conversation_history', [])
        conversation_history.append({
            "role": "user",
            "content": answer,
            "timestamp": datetime.utcnow()
        })
        interactive_data['conversation_history'] = conversation_history
        
        # Update session
        await idea_service.save_or_update_idea(session_id, {
            "interactive_data": interactive_data
        })
        
        if not missing_data:
            # No more questions - generate final contract
            template_service = ContractTemplateService()
            reference_template = interactive_data.get('reference_template')
            contract_type = interactive_data.get('contract_type', '')
            
            final_contract = await template_service.generate_indian_law_contract(
                extracted_data, 
                contract_type,
                "india"
            )
            
            # Update session with final contract
            interactive_data['generated_contract'] = final_contract
            interactive_data['status'] = 'completed'
            
            await idea_service.save_or_update_idea(session_id, {
                "interactive_data": interactive_data,
                "drafts": final_contract.get("drafts", {}),
                "all_drafts": final_contract.get("drafts", {}),
                "sections": final_contract.get("sections", []),
                "status": IdeaStatus.COMPLETED
            })
            
            return {
                "type": "end",
                "final_contract": final_contract,
                "message": "Contract generation completed successfully"
            }
        else:
            # Get next question
            next_item = missing_data[0]
            question = f"Please provide the {next_item.get('field', 'missing information')}: {next_item.get('description', '')}"
            
            # Update conversation history with next question
            conversation_history.append({
                "role": "assistant",
                "content": question,
                "timestamp": datetime.utcnow()
            })
            interactive_data['conversation_history'] = conversation_history
            
            await idea_service.save_or_update_idea(session_id, {
                "interactive_data": interactive_data
            })
            
            return {
                "type": "interrupt",
                "action": "get_question_response",
                "question": question,
                "reason": next_item.get('reason', 'This information is required for the contract'),
                "current_field": next_item.get('field'),
                "remaining_questions": len(missing_data) - 1
            }
        
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/submit-all-missing-data")
async def submit_all_missing_data(request_data: SubmitAllMissingDataRequest):
    """Submit all missing data at once and generate final contract"""
    try:
        # Use the new ContractGenerationService
        contract_generation_service = ContractGenerationService(idea_service)
        return await contract_generation_service.submit_all_missing_data(
            session_id=request_data.session_id,
            missing_data_responses=request_data.missing_data_responses
        )
        
    except Exception as e:
        logger.error(f"Error submitting all missing data: {e}")
        log_catalog_operation("ERROR", request_data.session_id, f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apcontract/save-contract")
async def save_contract(request_data: dict):
    """Save the final contract to the catalog - UPDATE existing session, don't create duplicate"""
    try:
        session_id = request_data.get("session_id")
        contract_data = request_data.get("contract")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Get the existing session - this should already exist from the contract generation process
        idea = await idea_service.get_idea_by_session(session_id)
        if not idea:
            logger.warning(f"Session {session_id} not found, creating new entry")
            # If session doesn't exist, create it (fallback scenario)
            contract_title = contract_data.get("title", "Generated Contract")
            contract_doc_data = {
                "session_id": session_id,
                "title": contract_title,
                "original_idea": contract_data.get("description", ""),
                "rephrased_idea": contract_data.get("description", ""),
                "sections": idea_service._convert_sections_to_database_format(contract_data.get("sections", [])),
                "drafts": contract_data.get("drafts", {}),
                "all_drafts": contract_data.get("drafts", {}),
                "conversation_history": [],
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "total_questions_asked": 0,
                    "submitted_by": "save_contract",
                    "department": "Legal",
                    "is_poc_document": True,
                    "sections_count": len(contract_data.get("sections", [])),
                    "source": "manual_save"
                },
                "dexko_context": {
                    "user_id": "save_contract",
                    "department": "Legal",
                    "role": "System",
                    "location": "India",
                    "language": "en"
                },
                "status": IdeaStatus.COMPLETED
            }
            await idea_service.save_or_update_idea(session_id, contract_doc_data)
            logger.info(f"✅ Contract created and saved to catalog: {contract_title} (Session: {session_id})")
        else:
            # UPDATE existing session - don't create duplicate
            contract_title = contract_data.get("title") or idea.title or "Generated Contract"
            
            # Convert sections to proper format if provided
            sections_data = []
            if contract_data.get("sections"):
                sections_data = idea_service._convert_sections_to_database_format(contract_data["sections"])
            
            # Update the existing contract - don't create new one
            update_data = {
                "title": contract_title,
                "status": IdeaStatus.COMPLETED,
                "drafts": contract_data.get("drafts", {}),
                "all_drafts": contract_data.get("drafts", {}),
                "sections": sections_data
            }
            
            # Update metadata with the final title
            if idea.metadata:
                if hasattr(idea.metadata, 'dict'):
                    metadata = idea.metadata.dict()
                else:
                    metadata = dict(idea.metadata)
            else:
                metadata = {}
            
            metadata["updated_at"] = datetime.utcnow()
            metadata["final_title"] = contract_title
            update_data["metadata"] = metadata
            
            # CRITICAL: Update existing session, don't create new one
            await idea_service.save_or_update_idea(session_id, update_data)
            
            logger.info(f"✅ Contract updated in catalog: {contract_title} (Session: {session_id})")
        
        return {
            "message": f"Contract '{contract_title}' saved to catalog successfully",
            "session_id": session_id,
            "title": contract_title
        }
        
    except Exception as e:
        logger.error(f"Error saving contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _create_final_contract_from_uploaded_document(raw_text: str, enhanced_extracted_data: Dict[str, Any], contract_type: str) -> Dict[str, Any]:
    """Create final contract by combining uploaded document content with user inputs and proper legal formatting"""
    try:
        logger.info("Creating professional legal contract from uploaded document with user inputs")
        
        # Use AI to create a professional legal document
        template_service = ContractTemplateService()
        
        # If AI is available, use it to create a proper legal document
        if template_service.llm:
            # Extract key information for the AI
            user_responses = enhanced_extracted_data.get('missing_data_responses', {})
            parties = enhanced_extracted_data.get('parties', [])
            key_terms = enhanced_extracted_data.get('key_terms', [])
            payment_terms = enhanced_extracted_data.get('payment_terms', {})
            duration = enhanced_extracted_data.get('duration', {})
            
            prompt = f"""
            You are a professional legal document drafter specializing in {contract_type if contract_type else "contract"} agreements. 
            
            ORIGINAL DOCUMENT CONTENT (for reference):
            {raw_text[:3000]}
            
            USER-PROVIDED INFORMATION TO INCORPORATE:
            {user_responses}
            
            Contract Type: {contract_type}
            
            CRITICAL REQUIREMENTS FOR PROFESSIONAL LEGAL DOCUMENT:
            1. Create a COMPLETE, PROFESSIONAL legal contract document
            2. Use proper legal language, clauses, and formatting
            3. Include standard legal sections appropriate for this contract type
            4. Incorporate ALL user-provided information seamlessly
            5. Add standard legal clauses (confidentiality, termination, governing law, etc.)
            6. Use proper section headings in ALL CAPS
            7. Format as a proper legal document with numbered clauses
            8. Include recitals, definitions, operative clauses, and signature blocks
            9. Ensure the document is legally sound and professional
            10. Use proper legal terminology and standard contract language
            
            STANDARD LEGAL SECTIONS TO INCLUDE:
            - TITLE AND PARTIES
            - RECITALS (WHEREAS clauses)
            - DEFINITIONS
            - TERMS AND CONDITIONS
            - PAYMENT TERMS (if applicable)
            - TERMINATION
            - CONFIDENTIALITY
            - GOVERNING LAW AND JURISDICTION
            - MISCELLANEOUS (severability, entire agreement, etc.)
            - SIGNATURE BLOCKS
            
            IMPORTANT: Generate a complete, ready-to-use legal document that looks professional and includes all necessary legal clauses.
            
            Generate the complete professional legal contract:
            """
            
            response = await template_service.llm.ainvoke([
                SystemMessage(content="""You are a professional legal document drafter. Your task is to create complete, professional legal contracts that:
                - Use proper legal language and formatting
                - Include standard legal clauses and sections
                - Are ready for immediate use
                - Look professional and legally sound
                - Incorporate all provided user information
                - Follow standard contract structure with proper headings
                - Include necessary legal boilerplate
                - Use numbered clauses and proper legal terminology
                - Ensure the document is comprehensive and complete"""),
                HumanMessage(content=prompt)
            ])
            
            professional_content = response.content
            
            # Ensure the content is plain text, not JSON
            if professional_content.strip().startswith('{') or professional_content.strip().startswith('['):
                logger.warning("AI generated JSON instead of plain text, using enhanced fallback")
                # Enhanced fallback with proper legal structure
                professional_content = _create_enhanced_legal_document(raw_text, enhanced_extracted_data, contract_type)
            
            # Parse the professional content into sections
            sections = _parse_contract_sections_robust(professional_content)
            
            # Create drafts from sections
            drafts = {}
            for section in sections:
                if section.get('heading') and section.get('content'):
                    drafts[section['heading']] = section['content']
            
            final_contract = {
                "title": _extract_professional_title(enhanced_extracted_data, contract_type),
                "description": f"Professional {contract_type if contract_type else 'Legal'} Agreement",
                "sections": sections,
                "drafts": drafts,
                "metadata": {
                    "source": "professional_legal_document",
                    "contract_type": contract_type,
                    "jurisdiction": "india",
                    "ai_enhanced": True,
                    "professional_format": True,
                    "original_document_used": True
                }
            }
        else:
            # Enhanced fallback with proper legal structure
            professional_content = _create_enhanced_legal_document(raw_text, enhanced_extracted_data, contract_type)
            sections = _parse_contract_sections_robust(professional_content)
            
            # Create drafts from sections
            drafts = {}
            for section in sections:
                if section.get('heading') and section.get('content'):
                    drafts[section['heading']] = section['content']
            
            final_contract = {
                "title": _extract_professional_title(enhanced_extracted_data, contract_type),
                "description": f"Professional {contract_type if contract_type else 'Legal'} Agreement",
                "sections": sections,
                "drafts": drafts,
                "metadata": {
                    "source": "professional_legal_document",
                    "contract_type": contract_type,
                    "jurisdiction": "india",
                    "professional_format": True,
                    "original_document_used": True
                }
            }
        
        logger.info(f"Successfully created professional legal contract with {len(final_contract.get('sections', []))} sections")
        return final_contract
        
    except Exception as e:
        logger.error(f"Error creating professional legal contract: {e}")
        # Fallback to standard contract generation
        template_service = ContractTemplateService()
        return await template_service.generate_indian_law_contract(
            enhanced_extracted_data, 
            contract_type,
            "india"
        )

def _create_enhanced_legal_document(raw_text: str, enhanced_extracted_data: Dict[str, Any], contract_type: str) -> str:
    """Create an enhanced legal document with proper formatting and clauses"""
    user_responses = enhanced_extracted_data.get('missing_data_responses', {})
    parties = enhanced_extracted_data.get('parties', [])
    
    # Build professional legal document
    document_parts = []
    
    # Title
    title = _extract_professional_title(enhanced_extracted_data, contract_type)
    document_parts.append(f"{title.upper()}")
    document_parts.append("=" * len(title))
    document_parts.append("")
    
    # Parties section
    document_parts.append("PARTIES")
    document_parts.append("-" * 50)
    if parties:
        for i, party in enumerate(parties, 1):
            document_parts.append(f"{i}. {party}")
    else:
        document_parts.append("Party A: [Name and Address]")
        document_parts.append("Party B: [Name and Address]")
    document_parts.append("")
    
    # Recitals
    document_parts.append("RECITALS")
    document_parts.append("-" * 50)
    document_parts.append("WHEREAS, the Parties desire to enter into this Agreement;")
    document_parts.append("WHEREAS, the Parties have agreed to the terms and conditions set forth herein;")
    document_parts.append("WHEREAS, this Agreement is made in accordance with applicable laws;")
    document_parts.append("")
    
    # Definitions
    document_parts.append("DEFINITIONS")
    document_parts.append("-" * 50)
    document_parts.append("1. 'Agreement' means this contract and all schedules and exhibits attached hereto.")
    document_parts.append("2. 'Parties' means the signatories to this Agreement.")
    document_parts.append("3. 'Effective Date' means the date this Agreement becomes effective.")
    document_parts.append("")
    
    # Terms and Conditions
    document_parts.append("TERMS AND CONDITIONS")
    document_parts.append("-" * 50)
    
    # Incorporate user responses
    for field, value in user_responses.items():
        if field.lower() in ['duration', 'term']:
            document_parts.append(f"1. TERM: This Agreement shall be effective from the Effective Date and shall continue for a period of {value}.")
        elif field.lower() in ['payment', 'consideration']:
            document_parts.append(f"2. CONSIDERATION: {value}")
        elif field.lower() in ['obligations', 'duties']:
            document_parts.append(f"3. OBLIGATIONS: {value}")
        else:
            document_parts.append(f"4. {field.upper()}: {value}")
    
    # Standard legal clauses
    document_parts.append("")
    document_parts.append("5. CONFIDENTIALITY: The Parties agree to maintain the confidentiality of all proprietary information disclosed during the term of this Agreement.")
    document_parts.append("")
    document_parts.append("6. TERMINATION: This Agreement may be terminated by either Party upon thirty (30) days written notice to the other Party.")
    document_parts.append("")
    document_parts.append("7. GOVERNING LAW: This Agreement shall be governed by and construed in accordance with the laws of India.")
    document_parts.append("")
    document_parts.append("8. JURISDICTION: The courts in [City], India shall have exclusive jurisdiction over any disputes arising from this Agreement.")
    document_parts.append("")
    document_parts.append("9. ENTIRE AGREEMENT: This Agreement constitutes the entire understanding between the Parties and supersedes all prior agreements.")
    document_parts.append("")
    document_parts.append("10. SEVERABILITY: If any provision of this Agreement is found to be invalid, the remaining provisions shall remain in full force and effect.")
    document_parts.append("")
    document_parts.append("11. WAIVER: The failure to exercise any right under this Agreement shall not constitute a waiver of such right.")
    document_parts.append("")
    document_parts.append("12. NOTICES: All notices under this Agreement shall be in writing and delivered to the addresses specified above.")
    document_parts.append("")
    
    # Signature blocks
    document_parts.append("IN WITNESS WHEREOF, the Parties have executed this Agreement as of the date first above written.")
    document_parts.append("")
    document_parts.append("PARTY A:")
    document_parts.append("")
    document_parts.append("_________________________")
    document_parts.append("Name: ___________________")
    document_parts.append("Title: __________________")
    document_parts.append("Date: ___________________")
    document_parts.append("")
    document_parts.append("PARTY B:")
    document_parts.append("")
    document_parts.append("_________________________")
    document_parts.append("Name: ___________________")
    document_parts.append("Title: __________________")
    document_parts.append("Date: ___________________")
    
    return "\n".join(document_parts)

def _extract_professional_title(enhanced_extracted_data: Dict[str, Any], contract_type: str) -> str:
    """Extract or generate a professional contract title"""
    if contract_type and contract_type.strip():
        contract_type_clean = contract_type.replace('_', ' ').title()
        return f"{contract_type_clean} Agreement"
    
    # Try to extract from user responses
    user_responses = enhanced_extracted_data.get('missing_data_responses', {})
    for field, value in user_responses.items():
        if field.lower() in ['contract_type', 'agreement_type']:
            return f"{value.title()} Agreement"
    
    # Final fallback
    return "Professional Legal Agreement"

def _parse_contract_sections_robust(content: str) -> List[Dict[str, str]]:
    """Robustly parse contract content into sections"""
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
                    "type": "section"
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
            "type": "section"
        })
    
    # If no sections found, create a single section with all content
    if not sections:
        sections.append({
            "heading": "CONTRACT AGREEMENT",
            "content": content.strip(),
            "type": "general"
        })
    
    return sections

def _extract_title_from_content(content: str, contract_type: str) -> str:
    """Extract title from contract content with proper naming convention"""
    # First, try to use contract type for proper naming
    if contract_type and contract_type.strip():
        # Convert contract_type to proper title format
        contract_type_clean = contract_type.replace('_', ' ').title()
        return f"{contract_type_clean} Agreement"
    
    # If no contract type, look for actual contract title in content
    lines = content.split('\n')
    
    # Look for title in first few lines - skip generic lines
    for i, line in enumerate(lines[:10]):
        line = line.strip()
        if line and len(line) > 10 and len(line) < 200:
            # Check if line looks like a real contract title (not generic text)
            if (not line.isupper() and 
                len(line.split()) < 20 and
                not any(generic in line.lower() for generic in [
                    'this document contains', 'dummy', 'sample', 'test', 
                    'fictional', 'demonstration', 'prepared for'
                ]) and
                any(keyword in line.lower() for keyword in [
                    'agreement', 'contract', 'deed', 'lease', 'employment',
                    'service', 'partnership', 'nda', 'confidentiality'
                ])):
                return line
    
    # Final fallback
    return "Generated Contract Agreement"

app.mount("/contract-gen", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
