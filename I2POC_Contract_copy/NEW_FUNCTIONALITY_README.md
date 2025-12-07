# New Contract Document Upload & Processing Functionality

## Overview

This enhancement adds two powerful new capabilities to the contract generation platform:

1. **Sample Contract Template Upload**: Users can upload sample contract documents to create templates for future use
2. **Automatic Contract Generation**: Users can upload complete contract documents and the system will automatically generate formatted contracts according to Indian law

## New Backend Services

### 1. ContractTemplateService (`contract_template_service.py`)

This service provides AI-powered contract generation capabilities:

- **`generate_indian_law_contract()`**: Generates formatted contracts according to Indian law using AI
- **`generate_from_template()`**: Adapts existing templates with user-specific data
- **`analyze_sample_template()`**: Uses AI to analyze uploaded contract templates and extract structure/patterns

### 2. DocumentProcessingService (`document_processing_service.py`)

This service handles document processing and information extraction:

- **`process_sample_contract()`**: Processes uploaded sample contracts to extract structure and format
- **`extract_contract_data()`**: Extracts comprehensive contract information from uploaded documents
- **AI-powered analysis**: Uses GPT-4 to analyze contract structure and extract key information

## New API Endpoints

### 1. Upload Sample Contract Template
```
POST /apcontract/upload-sample-contract
```
- **Purpose**: Upload a sample contract to create a template
- **Parameters**: 
  - `file`: Contract document (DOCX, DOC, PDF, TXT)
  - `contract_type`: Type of contract (land_agreement, employment_contract, etc.)
  - `description`: Optional description
- **Response**: Template ID, structure analysis, section count

### 2. Process Contract Document
```
POST /apcontract/process-contract-document
```
- **Purpose**: Upload a complete contract document and generate formatted contract
- **Parameters**:
  - `file`: Contract document (DOCX, DOC, PDF, TXT)
  - `contract_type`: Type of contract
  - `jurisdiction`: Legal jurisdiction (default: "india")
- **Response**: Session ID, generated contract details, AI score

### 3. Get Available Templates
```
GET /apcontract/templates
```
- **Purpose**: Retrieve all available contract templates
- **Response**: List of templates with metadata

### 4. Generate Contract from Template
```
POST /apcontract/generate-from-template
```
- **Purpose**: Generate a contract using a specific template and user data
- **Parameters**:
  - `template_id`: ID of the template to use
  - `user_data`: User-specific information to populate the template
- **Response**: Session ID, generated contract details

## Frontend Components

### FileUploadSection Component (`FileUploadSection.jsx`)

A new React component that provides:

- **File Upload Interface**: Drag-and-drop file selection with validation
- **Contract Type Selection**: Dropdown for selecting contract type with auto-detection
- **Dual Functionality**: 
  - **Upload as Template**: Save document as template for future use
  - **Generate Contract**: Process document and create formatted contract
- **Real-time Feedback**: Success/error messages with detailed results

## Key Features

### 1. AI-Powered Document Analysis
- Uses GPT-4 to analyze contract structure and extract key information
- Identifies sections, parties, obligations, payment terms, etc.
- Ensures compliance with Indian contract law

### 2. Automatic Contract Generation
- Extracts information from uploaded documents
- Generates professionally formatted contracts
- Applies Indian legal standards and formatting
- Auto-scores generated contracts with AI

### 3. Template Management
- Store and reuse contract templates
- AI analysis of template structure and patterns
- Template-based contract generation with user data

### 4. File Format Support
- **DOCX/DOC**: Microsoft Word documents
- **PDF**: Portable Document Format
- **TXT**: Plain text documents

## Usage Examples

### Example 1: Upload Land Agreement Template
1. Navigate to "Upload Documents" section
2. Select a land agreement document
3. Choose "Land Agreement" as contract type
4. Click "Upload as Template"
5. System analyzes structure and saves as template

### Example 2: Generate Contract from Document
1. Navigate to "Upload Documents" section
2. Select a complete contract document
3. Choose appropriate contract type
4. Click "Generate Contract"
5. System processes document and creates formatted contract
6. Contract is automatically saved to catalog with AI score

## Integration with Existing System

- **Maintains all existing functionality**: Chat-based contract generation remains unchanged
- **Seamless navigation**: New "Upload Documents" option in main navigation
- **Database integration**: Generated contracts saved to existing MongoDB collections
- **AI scoring**: All generated contracts automatically scored using existing AI scoring service

## Technical Implementation

### Dependencies Added
- **PyPDF2**: PDF document processing
- **python-docx**: Word document processing

### AI Integration
- **LangChain**: For structured AI interactions
- **GPT-4**: For contract analysis and generation
- **Custom prompts**: Tailored for Indian legal context

### Error Handling
- Graceful fallbacks when AI analysis fails
- Comprehensive error messages for users
- File type validation and size limits

## Benefits

1. **Time Savings**: Automates contract generation from existing documents
2. **Consistency**: Ensures all contracts follow Indian legal standards
3. **Template Reuse**: Build library of approved contract templates
4. **AI Quality Assurance**: Automatic scoring and feedback on generated contracts
5. **User-Friendly**: Simple file upload interface with clear instructions

## Future Enhancements

1. **Batch Processing**: Upload multiple documents at once
2. **Template Customization**: Edit and customize saved templates
3. **Advanced AI Analysis**: More sophisticated legal compliance checking
4. **Multi-language Support**: Support for contracts in different languages
5. **Integration with Legal Databases**: Cross-reference with legal precedents
