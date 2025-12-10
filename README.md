# Legal Advisor Backend

A parallel multi-agent system for intelligent contract review using FastAPI, implementing a "fan-out, fan-in" architecture with specialized AI agents.

## 🏗️ Architecture

- **Multi-LLM Council Pattern**: Each agent runs multiple LLMs (OpenAI GPT, Google Gemini, Grok) in parallel and aggregates via consensus
- **RAG Integration**: Pinecone vector database with Indian Labour Law embeddings for legal context retrieval
- **Parallel Execution**: 9 LLM calls (3 agents × 3 LLMs) + 3 RAG retrievals per contract review

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL (or SQLite for development)
- API Keys:
  - OpenAI API Key
  - Google Gemini API Key
  - Grok (xAI) API Key
  - Pinecone API Key

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python -m app.database.session

# Run the server
uvicorn app.main:app --reload
```

## 📁 Project Structure

```
legal-advisor/
├── app/
│   ├── agents/          # Specialized review agents
│   ├── api/             # FastAPI endpoints
│   ├── database/        # Database setup
│   ├── models/          # Pydantic & SQLAlchemy models
│   ├── services/        # Business logic & orchestration
│   └── vectordb/        # Pinecone client
├── data/
│   ├── legal_docs/      # Indian Labour Law PDFs
│   └── reference_playbooks/
└── requirements.txt
```

## 🎯 API Endpoints

### Contract Review
- `POST /api/review` - Submit contract document for multi-agent review
  - **File Upload**: Accepts PDF, DOCX, or images
  - Automatic text extraction (PDF, DOCX, Gemini Vision for images)
  - Returns comprehensive analysis with safety score
- `GET /api/reviews/{review_id}` - Retrieve past review

### Feedback (RLHF)
- `POST /api/feedback` - Submit user feedback for learning loop

### Legal Document Management
- `POST /api/legal-docs/upload` - Upload legal documents (PDF, DOCX, Images)
  - Supported formats: `.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`
  - Extracts text and stores in vector database for RAG
- `GET /api/legal-docs/status` - Check vector DB status

### Export
- `POST /api/reviews/{review_id}/export/docx` - Export as Word redline
- `POST /api/reviews/{review_id}/export/pdf` - Export as PDF summary report

### System
- `GET /api/health` - Health check

## 🧪 Testing

```bash
# Run tests
pytest

# Test individual components
python -m pytest tests/test_agents.py
python -m pytest tests/test_council.py
```

## 📝 License

MIT
