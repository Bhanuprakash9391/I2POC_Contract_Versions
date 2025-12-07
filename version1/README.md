# Version 1 - I2POC Contract (Original)

This is the original version of the I2POC Contract application, a full-stack web application for contract drafting, review, and management.

## Overview

The application consists of:
- **Backend**: Python Flask server with AI-powered contract analysis and generation
- **Frontend**: React-based single-page application with real-time chat interface

## Features

### Backend (idea_be)
- Contract categorization using AI
- Contract scoring and risk assessment
- Graph-based contract visualization
- Database models for contracts, sections, and users
- REST API endpoints for frontend communication
- Integration with OpenAI GPT models for contract analysis

### Frontend (idea_fe)
- Interactive chat interface for contract drafting
- Real-time contract section editing
- Contract catalog with filtering and search
- User authentication and profile management
- Responsive design with Tailwind CSS
- Document export (DOCX, PDF) functionality

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite (with SQLAlchemy ORM)
- **AI Integration**: OpenAI GPT-4, LangChain
- **Visualization**: NetworkX, Plotly
- **API**: RESTful endpoints

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS, CSS modules
- **UI Components**: Custom components with Framer Motion animations
- **State Management**: React Context API
- **HTTP Client**: Axios
- **Build Tool**: Vite

## Project Structure

```
version1/
├── idea_be/                    # Backend server
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration settings
│   ├── constants.py           # Application constants
│   ├── database.py            # Database connection and models
│   ├── models.py              # SQLAlchemy models
│   ├── schema.py              # Pydantic schemas for validation
│   ├── ai_contract_categorization_service.py  # AI categorization
│   ├── ai_contract_scoring_service.py         # AI scoring
│   ├── idea_service.py        # Business logic for ideas/contracts
│   ├── prompt_templates.py    # AI prompt templates
│   ├── graph_app.py           # Graph visualization
│   ├── user_context.py        # User context management
│   ├── clear_database.py      # Database cleanup utility
│   ├── requirements.txt       # Python dependencies
│   ├── static/                # Static assets
│   │   ├── assets/           # Compiled frontend assets
│   │   └── index.html        # Frontend entry point
│   └── .gitignore
├── idea_fe/                    # Frontend application
│   ├── src/
│   │   ├── App.jsx           # Main application component
│   │   ├── main.jsx          # Application entry point
│   │   ├── ChatContext.jsx   # React context for chat
│   │   ├── components/       # React components
│   │   │   ├── DraftChat/   # Contract drafting chat interface
│   │   │   ├── ContractCatalog.jsx
│   │   │   ├── ContractReviewerDashboard.jsx
│   │   │   ├── IdeaCatalog.jsx
│   │   │   ├── InitialChat.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── UserProfile.jsx
│   │   │   └── ui/          # Reusable UI components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── utils/           # Utility functions
│   │   ├── assets/          # Images and SVG assets
│   │   ├── constants.js     # Frontend constants
│   │   └── index.css        # Global styles
│   ├── public/              # Public assets
│   ├── package.json         # Node.js dependencies
│   ├── vite.config.js       # Vite configuration
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   ├── postcss.config.js    # PostCSS configuration
│   ├── eslint.config.js     # ESLint configuration
│   ├── index.html           # HTML entry point
│   └── .gitignore
└── logo.png                  # Application logo
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key

### Backend Setup
1. Navigate to `version1/idea_be/`
2. Create a virtual environment: `python -m venv venv`
3. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set environment variables:
   ```
   export OPENAI_API_KEY=your_api_key_here
   export FLASK_APP=app.py
   export FLASK_ENV=development
   ```
6. Initialize database: `python database.py`
7. Run the server: `python app.py`

### Frontend Setup
1. Navigate to `version1/idea_fe/`
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
4. Open browser to `http://localhost:5173`

## API Documentation

### Key Endpoints
- `GET /api/contracts` - List all contracts
- `POST /api/contracts` - Create new contract
- `GET /api/contracts/{id}` - Get contract details
- `POST /api/contracts/{id}/sections` - Add section to contract
- `POST /api/chat` - AI chat endpoint for contract drafting
- `GET /api/graph/{contract_id}` - Get contract visualization graph

## Deployment

### Backend Deployment
- Can be deployed using Gunicorn: `gunicorn app:app`
- Environment variables required: `OPENAI_API_KEY`, `DATABASE_URL`

### Frontend Deployment
- Build for production: `npm run build`
- Deploy static files to any web server (Nginx, Apache, S3, etc.)

## Limitations
- SQLite database not suitable for high-concurrency production
- No advanced user role management
- Basic error handling
- Limited contract template variety

## Future Enhancements
- Multi-user collaboration
- Advanced contract analytics
- Integration with document signing services
- Mobile application
- Enhanced security features

## License
Proprietary - For internal use only

## Contact
For questions or support, contact the development team.
