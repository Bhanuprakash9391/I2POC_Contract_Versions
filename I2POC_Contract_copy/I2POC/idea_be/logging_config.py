import logging
import os
from datetime import datetime
import sys

def setup_logging():
    """Setup comprehensive logging for the application"""
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{logs_dir}/app_{timestamp}.log"
    
    # Configure logging - set higher level to reduce noise from third-party libraries
    logging.basicConfig(
        level=logging.INFO,  # Changed from DEBUG to INFO to reduce noise
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create specific loggers for different components
    loggers = {
        'app': logging.getLogger('app'),
        'database': logging.getLogger('database'),
        'contract': logging.getLogger('contract'),
        'upload': logging.getLogger('upload'),
        'catalog': logging.getLogger('catalog'),
        'ai': logging.getLogger('ai')
    }
    
    # Set levels for specific loggers - keep DEBUG for our app but reduce third-party noise
    for logger in loggers.values():
        logger.setLevel(logging.DEBUG)
    
    # Reduce noise from third-party libraries
    logging.getLogger('watchfiles').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    logging.getLogger('langgraph').setLevel(logging.WARNING)
    
    return loggers

# Global loggers instance
loggers = setup_logging()

def log_contract_creation(session_id, title, source, details=None):
    """Log contract creation with details"""
    loggers['contract'].info(f"📄 Contract Created - Session: {session_id}, Title: {title}, Source: {source}")
    if details:
        loggers['contract'].debug(f"Contract Details: {details}")

def log_database_operation(operation, collection, document_id, details=None):
    """Log database operations"""
    loggers['database'].info(f"💾 Database {operation} - Collection: {collection}, ID: {document_id}")
    if details:
        loggers['database'].debug(f"Operation Details: {details}")

def log_upload_process(filename, session_id, extracted_data=None):
    """Log file upload process"""
    loggers['upload'].info(f"📤 File Upload - File: {filename}, Session: {session_id}")
    if extracted_data:
        loggers['upload'].debug(f"Extracted Data Summary: {extracted_data.get('summary', 'No summary')}")
        loggers['upload'].debug(f"Parties: {extracted_data.get('parties', [])}")
        loggers['upload'].debug(f"Key Terms Count: {len(extracted_data.get('key_terms', []))}")

def log_catalog_operation(operation, session_id, details=None):
    """Log catalog operations"""
    loggers['catalog'].info(f"📚 Catalog {operation} - Session: {session_id}")
    if details:
        loggers['catalog'].debug(f"Catalog Details: {details}")

def log_ai_operation(operation, session_id, details=None):
    """Log AI operations"""
    loggers['ai'].info(f"🤖 AI {operation} - Session: {session_id}")
    if details:
        loggers['ai'].debug(f"AI Details: {details}")
