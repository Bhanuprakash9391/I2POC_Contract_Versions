from motor.motor_asyncio import AsyncIOMotorCollection
from models import IdeaDocument, MetadataDocument, DexKoUserContext, IdeaStatus, DexKoDepartment
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class IdeaService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def save_idea(self, idea_data: dict) -> str:
        """Save a new idea document"""
        try:
            # Convert GraphState to IdeaDocument format
            idea_doc = self._convert_to_document(idea_data)

            result = await self.collection.insert_one(idea_doc.dict(by_alias=True))
            logger.info(f"✅ Idea saved with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Failed to save idea: {e}")
            raise

    async def save_or_update_idea(self, session_id: str, idea_data: dict) -> str:
        """Save new idea or update existing one by session_id"""
        try:
            # Check if idea already exists
            existing_idea = await self.get_idea_by_session(session_id)

            if existing_idea:
                # Update existing idea
                update_data = self._prepare_update_data(idea_data)
                success = await self.update_idea(session_id, update_data)
                if success:
                    logger.info(f"✅ Idea updated for session {session_id}")
                    return str(existing_idea.id)
                else:
                    logger.error(f"❌ Failed to update idea for session {session_id}")
                    raise Exception("Failed to update existing idea")
            else:
                # Create new idea
                idea_data["session_id"] = session_id
                return await self.save_idea(idea_data)
        except Exception as e:
            logger.error(f"❌ Failed to save/update idea for session {session_id}: {e}")
            raise

    async def update_idea(self, session_id: str, update_data: dict) -> bool:
        """Update existing idea by session_id"""
        try:
            # Handle metadata separately to avoid dot notation issues
            metadata_update = {}
            regular_updates = {}
            
            for key, value in update_data.items():
                if key.startswith("metadata."):
                    # Extract the metadata field name
                    metadata_field = key.replace("metadata.", "")
                    metadata_update[metadata_field] = value
                else:
                    regular_updates[key] = value
            
            # If we have metadata updates, handle them properly
            if metadata_update:
                # Get existing metadata first
                existing_idea = await self.get_idea_by_session(session_id)
                if existing_idea and existing_idea.metadata:
                    if hasattr(existing_idea.metadata, 'dict'):
                        existing_metadata = existing_idea.metadata.dict()
                    else:
                        existing_metadata = dict(existing_idea.metadata)
                else:
                    existing_metadata = {}
                
                # Merge with new metadata updates
                merged_metadata = {**existing_metadata, **metadata_update}
                regular_updates["metadata"] = merged_metadata
            
            # Always update the updated_at timestamp
            if "metadata" in regular_updates:
                regular_updates["metadata"]["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"session_id": session_id},
                {"$set": regular_updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to update idea {session_id}: {e}")
            raise

    async def get_idea_by_session(self, session_id: str) -> Optional[IdeaDocument]:
        """Retrieve idea by session_id"""
        try:
            doc = await self.collection.find_one({"session_id": session_id})
            if doc:
                return IdeaDocument(**doc)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to retrieve idea {session_id}: {e}")
            raise

    async def mark_completed(self, session_id: str, final_drafts: dict) -> bool:
        """Mark idea as completed with final drafts"""
        try:
            completion_time = await self._calculate_completion_time(session_id)

            # Get the existing idea first to preserve existing metadata
            existing_idea = await self.get_idea_by_session(session_id)
            if not existing_idea:
                logger.error(f"❌ Idea not found for session {session_id}")
                return False

            # Prepare metadata properly
            if existing_idea.metadata:
                if hasattr(existing_idea.metadata, 'dict'):
                    metadata = existing_idea.metadata.dict()
                else:
                    metadata = dict(existing_idea.metadata)
            else:
                metadata = {}

            # Update metadata fields
            metadata["updated_at"] = datetime.utcnow()
            metadata["completion_time_minutes"] = completion_time

            update_data = {
                "drafts": final_drafts,
                "all_drafts": final_drafts,
                "status": "completed",
                "metadata": metadata
            }

            return await self.update_idea(session_id, update_data)
        except Exception as e:
            logger.error(f"❌ Failed to mark idea {session_id} as completed: {e}")
            raise

    async def get_all_ideas(self, limit: int = 50) -> List[IdeaDocument]:
        """Get all ideas with pagination"""
        try:
            cursor = self.collection.find().sort("metadata.created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [IdeaDocument(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"❌ Failed to retrieve ideas: {e}")
            raise

    def _convert_to_document(self, graph_state_data: dict) -> IdeaDocument:
        """Convert GraphState data to IdeaDocument"""
        # Create default DexKo user context if not provided
        dexko_context = graph_state_data.get("dexko_user_context")
        if not dexko_context:
            dexko_context = DexKoUserContext(
                user_id="anonymous",
                department=DexKoDepartment.OTHER,
                role="Employee",
                location="Unknown",
                language="en"
            )
        
        return IdeaDocument(
            session_id=graph_state_data.get("session_id", ""),
            title=graph_state_data.get("title", ""),
            original_idea=graph_state_data.get("idea", ""),
            rephrased_idea=graph_state_data.get("idea", ""),  # Could be different
            sections=graph_state_data.get("sections", []),
            drafts=graph_state_data.get("all_drafts", {}),
            conversation_history=graph_state_data.get("conversation_history", []),
            metadata=MetadataDocument(
                total_questions_asked=len(graph_state_data.get("conversation_history", []))
            ),
            dexko_context=dexko_context,
            status=IdeaStatus.SUBMITTED
        )

    def _prepare_update_data(self, idea_data: dict) -> dict:
        """Prepare data for updating existing idea"""
        update_data = {}

        # Only update fields that are provided and not empty
        if idea_data.get("idea"):
            update_data["original_idea"] = idea_data["idea"]
            update_data["rephrased_idea"] = idea_data["idea"]

        if idea_data.get("title"):
            update_data["title"] = idea_data["title"]

        if idea_data.get("sections"):
            update_data["sections"] = idea_data["sections"]

        drafts_to_save = idea_data.get("drafts") or idea_data.get("all_drafts")
        if drafts_to_save:
            update_data["drafts"] = drafts_to_save
            update_data["all_drafts"] = drafts_to_save

        if idea_data.get("conversation_history"):
            update_data["conversation_history"] = idea_data["conversation_history"]
            update_data["metadata.total_questions_asked"] = len(idea_data["conversation_history"])

        if idea_data.get("status"):
            update_data["status"] = idea_data["status"]

        # DexKo-specific fields
        if idea_data.get("dexko_user_context"):
            update_data["dexko_context"] = idea_data["dexko_user_context"]

        if idea_data.get("evaluation_score"):
            update_data["evaluation_score"] = idea_data["evaluation_score"]

        if idea_data.get("reviewer_feedback"):
            update_data["reviewer_feedback"] = idea_data["reviewer_feedback"]

        # AI Scoring fields
        if idea_data.get("ai_score") is not None:
            update_data["ai_score"] = idea_data["ai_score"]

        if idea_data.get("ai_feedback"):
            update_data["ai_feedback"] = idea_data["ai_feedback"]

        if idea_data.get("ai_strengths"):
            update_data["ai_strengths"] = idea_data["ai_strengths"]

        if idea_data.get("ai_improvements"):
            update_data["ai_improvements"] = idea_data["ai_improvements"]

        return update_data

    async def _calculate_completion_time(self, session_id: str) -> float:
        """Calculate total time spent on idea completion"""
        # Implementation would track start time vs completion time
        return 0.0  # Placeholder
