# Overrule Legal Advisor

## Introduction

Overrule is a parallel multi-agent system for intelligent contract review, designed to help legal professionals and individuals analyze contracts with speed and precision.

**Key Features:**
- **Multi-Agent Review:** Utilizes a "council" of AI agents (running on OpenAI, Google Gemini, and Grok) to provide diverse perspectives.
- **RAG Integration:** Leverages Pinecone vector database with legal document embeddings (e.g., Indian Labour Law) for context-aware analysis.
- **Smart Interface:** A modern, React-based frontend for uploading contracts, viewing agent insights, and managing reviews.
- **Dynamic Analysis:** Automated text extraction and risk scoring.

## How to Run

### Prerequisites
- **Node.js** (v16+ recommended)
- **Python** (v3.10+)
- **PostgreSQL** or **SQLite** (for local dev)
- **API Keys**: You will need API keys for OpenAI, Google Gemini, Grok (xAI), and Pinecone.

### Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Set up environment variables:
    - Copy `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Open `.env` and add your API keys.

5.  Initialize the database (if required):
    ```bash
    python -m app.database.session
    ```

6.  Start the backend server:
    ```bash
    uvicorn app.main:app --reload
    ```
    The backend API will be available at `http://localhost:8000`.

### Frontend Setup

1.  Open a new terminal and navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Start the development server:
    ```bash
    npm run dev
    ```
    The application will be running at `http://localhost:3000`.

## Presentation and Demo

- **Presentation (PPT):** [Link to Presentation Slides](https://drive.google.com/file/d/1xpf3YnGrQjFOfk-56QBOdbtWK-nytDf1/view?usp=sharing)
- **Demo Video:** [Link to Demo Video](https://youtu.be/bQDLGf5dtyM)

## License

MIT
    