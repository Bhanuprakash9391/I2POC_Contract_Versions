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
                    return session_id
                else:
                    # Update failed, try to create new idea instead
                    logger.info(f"🔄 Update failed, creating new idea for session {session_id}")
                    idea_data["session_id"] = session_id
                    return await self.save_idea(idea_data)
            else:
                # Create new idea
                idea_data["session_id"] = session_id
                return await self.save_idea(idea_data)
        except Exception as e:
            logger.warning(f"⚠️ Save/update failed for session {session_id}: {e}")
            # Fallback to creating new idea
            try:
                idea_data["session_id"] = session_id
                return await self.save_idea(idea_data)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback save also failed: {fallback_error}")
                # Return session_id anyway to avoid breaking the flow
                return session_id

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
                try:
                    # Convert sections to proper format if needed
                    if doc.get("sections"):
                        doc["sections"] = self._convert_sections_to_database_format(doc["sections"])
                    
                    # Convert conversation_history to proper format if needed
                    if doc.get("conversation_history"):
                        doc["conversation_history"] = self._convert_conversation_history(doc["conversation_history"])
                    
                    # Preserve interactive_data if it exists
                    if "interactive_data" in doc:
                        # Ensure interactive_data is preserved as-is
                        doc["interactive_data"] = doc["interactive_data"]
                    
                    return IdeaDocument(**doc)
                except Exception as conversion_error:
                    logger.warning(f"⚠️ Failed to convert document {session_id}: {conversion_error}")
                    # Try to create a minimal valid document
                    try:
                        # Create a basic document with default sections
                        minimal_doc = {
                            "session_id": doc.get("session_id", ""),
                            "title": doc.get("title", "Untitled Contract"),
                            "original_idea": doc.get("original_idea", ""),
                            "rephrased_idea": doc.get("rephrased_idea", ""),
                            "sections": self._convert_sections_to_database_format(doc.get("sections", [])),
                            "drafts": doc.get("drafts", {}),
                            "all_drafts": doc.get("all_drafts", {}),
                            "conversation_history": self._convert_conversation_history(doc.get("conversation_history", [])),
                            "metadata": doc.get("metadata", {}),
                            "dexko_context": doc.get("dexko_context", {}),
                            "status": doc.get("status", "submitted"),
                            "interactive_data": doc.get("interactive_data", None)
                        }
                        return IdeaDocument(**minimal_doc)
                    except Exception as fallback_error:
                        logger.error(f"❌ Failed to create fallback document for {session_id}: {fallback_error}")
                        return None
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
            
            # Convert documents to handle old data structure
            converted_ideas = []
            for doc in docs:
                try:
                    # Convert sections to proper format if needed
                    if doc.get("sections"):
                        doc["sections"] = self._convert_sections_to_database_format(doc["sections"])
                    
                    # Convert conversation_history to proper format if needed
                    if doc.get("conversation_history"):
                        doc["conversation_history"] = self._convert_conversation_history(doc["conversation_history"])
                    
                    converted_ideas.append(IdeaDocument(**doc))
                except Exception as conversion_error:
                    logger.warning(f"⚠️ Failed to convert document {doc.get('session_id', 'unknown')}: {conversion_error}")
                    # Try to create a minimal valid document
                    try:
                        # Create a basic document with default sections
                        minimal_doc = {
                            "session_id": doc.get("session_id", ""),
                            "title": doc.get("title", "Untitled Contract"),
                            "original_idea": doc.get("original_idea", ""),
                            "rephrased_idea": doc.get("rephrased_idea", ""),
                            "sections": self._convert_sections_to_database_format(doc.get("sections", [])),
                            "drafts": doc.get("drafts", {}),
                            "all_drafts": doc.get("all_drafts", {}),
                            "conversation_history": self._convert_conversation_history(doc.get("conversation_history", [])),
                            "metadata": doc.get("metadata", {}),
                            "dexko_context": doc.get("dexko_context", {}),
                            "status": doc.get("status", "submitted")
                        }
                        converted_ideas.append(IdeaDocument(**minimal_doc))
                    except Exception as fallback_error:
                        logger.error(f"❌ Failed to create fallback document: {fallback_error}")
                        continue
            
            return converted_ideas
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
        
        # Convert sections to proper format for database model
        sections = self._convert_sections_to_database_format(graph_state_data.get("sections", []))
        
        return IdeaDocument(
            session_id=graph_state_data.get("session_id", ""),
            title=graph_state_data.get("title", ""),
            original_idea=graph_state_data.get("idea", ""),
            rephrased_idea=graph_state_data.get("idea", ""),  # Could be different
            sections=sections,
            drafts=graph_state_data.get("all_drafts", {}),
            conversation_history=graph_state_data.get("conversation_history", []),
            metadata=MetadataDocument(
                total_questions_asked=len(graph_state_data.get("conversation_history", []))
            ),
            dexko_context=dexko_context,
            status=IdeaStatus.SUBMITTED
        )
    
    def _convert_sections_to_database_format(self, sections: list) -> list:
        """Convert contract sections to database-compatible format"""
        from models import SectionDocument, SubsectionDocument
        
        converted_sections = []
        
        for section in sections:
            # Handle different section formats
            if isinstance(section, dict):
                # Check if it's already in database format
                if 'section_heading' in section and 'section_purpose' in section and 'subsections' in section:
                    # Already in correct format, use as-is
                    converted_sections.append(section)
                else:
                    # Contract format: {"heading": "...", "content": "...", "type": "..."}
                    section_heading = section.get("heading", section.get("section_heading", "Contract Section"))
                    section_content = section.get("content", section.get("subsection_definition", ""))
                    section_type = section.get("type", "general")
                    
                    # Create a single subsection with the content
                    subsection = SubsectionDocument(
                        subsection_heading="Main Content",
                        subsection_definition=section_content
                    )
                    
                    # Create section with purpose based on type
                    section_purpose = f"{section_type.title()} section for contract"
                    
                    converted_section = SectionDocument(
                        section_heading=section_heading,
                        section_purpose=section_purpose,
                        subsections=[subsection]
                    )
                    # Convert to dictionary for MongoDB storage
                    converted_sections.append(converted_section.dict())
            elif isinstance(section, SectionDocument):
                # Convert SectionDocument to dictionary
                converted_sections.append(section.dict())
            else:
                # If it's already in the correct format, use as-is
                converted_sections.append(section)
        
        # If no sections were converted, create a default one
        if not converted_sections:
            default_subsection = SubsectionDocument(
                subsection_heading="Contract Agreement",
                subsection_definition="This is a generated contract document."
            )
            default_section = SectionDocument(
                section_heading="Contract Agreement",
                section_purpose="Main contract document",
                subsections=[default_subsection]
            )
            converted_sections.append(default_section.dict())
        
        return converted_sections

    def _convert_conversation_history(self, conversation_history: list) -> list:
        """Convert conversation history to proper format"""
        from models import ConversationEntryDocument
        
        converted_history = []
        
        for entry in conversation_history:
            if isinstance(entry, dict):
                # Check if it's already in the correct format
                if 'section' in entry and 'subsection' in entry and 'question' in entry and 'answer' in entry:
                    # Already in correct format, use as-is
                    converted_history.append(entry)
                else:
                    # Handle different conversation entry formats
                    section = entry.get("section", entry.get("role", "general"))
                    subsection = entry.get("subsection", "main")
                    question = entry.get("question", entry.get("content", ""))
                    answer = entry.get("answer", entry.get("response", ""))
                    
                    # Create proper conversation entry
                    conversation_entry = ConversationEntryDocument(
                        section=section,
                        subsection=subsection,
                        question=question,
                        answer=answer
                    )
                    converted_history.append(conversation_entry.dict())
            elif isinstance(entry, ConversationEntryDocument):
                # Convert ConversationEntryDocument to dictionary
                converted_history.append(entry.dict())
            else:
                # If it's already in the correct format, use as-is
                converted_history.append(entry)
        
        return converted_history

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

        # Interactive data field for contract generation
        if idea_data.get("interactive_data") is not None:
            update_data["interactive_data"] = idea_data["interactive_data"]

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

    async def save_template(self, template_data: dict) -> str:
        """Save a contract template to the database"""
        try:
            # Add template-specific metadata
            template_data["type"] = "contract_template"
            template_data["created_at"] = datetime.utcnow()
            template_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(template_data)
            logger.info(f"✅ Contract template saved with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Failed to save contract template: {e}")
            raise

    async def get_template_by_id(self, template_id: str) -> Optional[dict]:
        """Retrieve a contract template by ID"""
        try:
            from bson import ObjectId
            doc = await self.collection.find_one({"_id": ObjectId(template_id), "type": "contract_template"})
            if doc:
                # Convert ObjectId to string for JSON serialization
                doc["_id"] = str(doc["_id"])
                return doc
            return None
        except Exception as e:
            logger.error(f"❌ Failed to retrieve template {template_id}: {e}")
            raise

    async def get_all_templates(self) -> List[dict]:
        """Get all contract templates"""
        try:
            cursor = self.collection.find({"type": "contract_template"}).sort("created_at", -1)
            docs = await cursor.to_list(length=100)  # Limit to 100 templates
            # Convert ObjectId to string for JSON serialization
            for doc in docs:
                doc["_id"] = str(doc["_id"])
            return docs
        except Exception as e:
            logger.error(f"❌ Failed to retrieve templates: {e}")
            return []
