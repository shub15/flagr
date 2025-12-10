"""
FastAPI application entry point for Legal Advisor backend.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.database.session import init_db
from app import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting Legal Advisor Backend...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Legal Advisor Backend...")


# Create FastAPI application
app = FastAPI(
    title="Legal Advisor API",
    description="""
    Multi-Agent Contract Review System with RAG
    
    Features:
    - 3 Specialized Agents (Skeptic, Strategist, Auditor)
    - Multi-LLM Council (OpenAI, Gemini, Grok)
    - RAG with Indian Labour Law (Pinecone)
    - Parallel Execution (9 LLM calls per review)
    - Safety Scoring & Conflict Resolution
    - RLHF Learning Loop
    """,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Legal Advisor API - Multi-Agent Contract Review System",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
