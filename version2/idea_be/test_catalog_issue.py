import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database, get_ideas_collection
from idea_service import IdeaService
from models import IdeaStatus

async def test_catalog_issue():
    """Test script to identify catalog duplication issues"""
    print("🔍 Testing Catalog Duplication Issue...")
    
    try:
        # Connect to database
        await Database.connect_db()
        collection = await get_ideas_collection()
        idea_service = IdeaService(collection)
        
        # Get all contracts
        ideas = await idea_service.get_all_ideas(100)
        
        print(f"📊 Total contracts in database: {len(ideas)}")
        
        # Analyze duplicates
        session_ids = {}
        duplicates = []
        
        for idea in ideas:
            session_id = idea.session_id
            if session_id in session_ids:
                duplicates.append({
                    'session_id': session_id,
                    'first_title': session_ids[session_id],
                    'duplicate_title': idea.title,
                    'status': idea.status
                })
            else:
                session_ids[session_id] = idea.title
        
        print(f"🔄 Found {len(duplicates)} duplicate session IDs")
        
        if duplicates:
            print("\n📋 Duplicate Contracts:")
            for dup in duplicates:
                print(f"  - Session ID: {dup['session_id']}")
                print(f"    First: {dup['first_title']}")
                print(f"    Duplicate: {dup['duplicate_title']}")
                print(f"    Status: {dup['status']}")
                print()
        
        # Analyze by source
        sources = {}
        for idea in ideas:
            source = idea.metadata.get('source', 'unknown') if idea.metadata else 'unknown'
            if source not in sources:
                sources[source] = []
            sources[source].append({
                'session_id': idea.session_id,
                'title': idea.title,
                'status': idea.status
            })
        
        print("\n📚 Contracts by Source:")
        for source, contracts in sources.items():
            print(f"  - {source}: {len(contracts)} contracts")
            for contract in contracts[:3]:  # Show first 3
                print(f"    * {contract['title']} ({contract['status']})")
            if len(contracts) > 3:
                print(f"    ... and {len(contracts) - 3} more")
        
        # Check for contracts with interactive_data
        interactive_contracts = []
        for idea in ideas:
            if hasattr(idea, 'interactive_data') and idea.interactive_data:
                interactive_contracts.append({
                    'session_id': idea.session_id,
                    'title': idea.title,
                    'status': idea.status,
                    'interactive_status': idea.interactive_data.get('status', 'unknown') if isinstance(idea.interactive_data, dict) else 'unknown'
                })
        
        print(f"\n🤖 Contracts with interactive_data: {len(interactive_contracts)}")
        for contract in interactive_contracts:
            print(f"  - {contract['title']} (Status: {contract['status']}, Interactive: {contract['interactive_status']})")
        
        return {
            'total_contracts': len(ideas),
            'duplicates': duplicates,
            'sources': sources,
            'interactive_contracts': interactive_contracts
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        await Database.close_db()

if __name__ == "__main__":
    result = asyncio.run(test_catalog_issue())
    if result:
        print(f"\n✅ Test completed successfully!")
        print(f"📊 Summary: {result['total_contracts']} total contracts, {len(result['duplicates'])} duplicates")
    else:
        print(f"\n❌ Test failed!")
