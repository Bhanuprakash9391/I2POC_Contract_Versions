from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
from langgraph.types import Command
from graph_app import graph_app, GraphState
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
import uvicorn

# MongoDB integration imports
from database import Database, get_ideas_collection
from idea_service import IdeaService
from models import IdeaStatus
from ai_contract_categorization_service import ai_contract_categorization_service
from ai_contract_scoring_service import ai_contract_scoring_service
from contextlib import asynccontextmanager
import logging
from datetime import datetime


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

# @app.get("/")
# async def read_root():
#     return {"message": "Welcome to the Root page!"}

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
        
        contract_doc_data = {
            "session_id": session_id,
            "title": contract_data.get("title", "Untitled Contract"),
            "original_idea": contract_data.get("idea", ""),
            "rephrased_idea": contract_data.get("idea", ""),
            "sections": [],
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


app.mount("/contract-gen", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
