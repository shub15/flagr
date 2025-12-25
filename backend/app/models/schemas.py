"""
Pydantic schemas for Legal Advisor API.
Defines strict data contracts between agents and the API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class ReviewCategory(str, Enum):
    """Categories for contract review findings."""
    CRITICAL = "CRITICAL"
    GOOD = "GOOD"
    NEGOTIABLE = "NEGOTIABLE"
    MISSING = "MISSING"


class ReviewPoint(BaseModel):
    """Atomic unit of a contract review finding."""
    category: ReviewCategory
    quote: Optional[str] = Field(
        None,
        description="Evidence from contract (required except for MISSING)"
    )
    advice: str = Field(..., description="Actionable recommendation")
    agent_source: str = Field(..., description="Which agent found this (skeptic/strategist/auditor)")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score from council consensus"
    )
    legal_reference: Optional[str] = Field(
        None,
        description="Relevant Indian Labour Law reference from RAG"
    )


class ContractReviewRequest(BaseModel):
    """Request schema for contract review."""
    contract_text: str = Field(..., min_length=100, description="Full contract text")
    contract_type: str = Field(
        default="employment",
        description="Type of contract (employment, freelance, etc.)"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context (e.g., 'Senior SDE at startup', 'Intern role')"
    )


class ContractReviewResult(BaseModel):
    """Final aggregated review result."""
    review_id: str
    safety_score: int = Field(..., ge=0, le=100, description="Overall safety score (0-100)")
    
    # Executive Summary
    summary: Optional[str] = Field(None, description="2-3 sentence executive summary")
    recommendation: Optional[str] = Field(None, description="SIGN, NEGOTIATE, or REJECT")
    
    # Detailed findings
    critical_points: List[ReviewPoint] = Field(default_factory=list)
    good_points: List[ReviewPoint] = Field(default_factory=list)
    negotiable_points: List[ReviewPoint] = Field(default_factory=list)
    missing_points: List[ReviewPoint] = Field(default_factory=list)
    total_findings: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Annotated PDF fields
    annotated_pdf_url: Optional[str] = Field(
        None,
        description="URL/path to download the annotated PDF with highlights"
    )
    annotation_map: Optional[dict] = Field(
        None,
        description="Map of point IDs to review data for interactive PDF"
    )
    annotation_stats: Optional[dict] = Field(
        None,
        description="Statistics about PDF annotations (highlights added, points found, etc.)"
    )
    llm_transparency: Optional[Dict[str, List[Dict]]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "review_id": "rev_123456",
                "safety_score": 65,
                "summary": "Contract has 3 critical issues and 5 missing clauses. Recommend negotiating before signing.",
                "recommendation": "NEGOTIATE",
                "critical_points": [
                    {
                        "category": "CRITICAL",
                        "quote": "Employer may terminate without notice",
                        "advice": "Request minimum 30-day notice period",
                        "agent_source": "skeptic",
                        "confidence": 0.95
                    }
                ],
                "good_points": [],
                "negotiable_points": [],
                "missing_points": [],
                "total_findings": 1,
                "annotated_pdf_url": "/api/reviews/rev_123456/annotated-pdf"
            }
        }


class FeedbackRequest(BaseModel):
    """User feedback for learning loop (RLHF-lite)."""
    review_id: str
    point_index: int = Field(..., description="Index of the review point")
    point_category: ReviewCategory
    action: str = Field(..., description="accepted, dismissed, or modified")
    user_comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response for feedback submission."""
    success: bool
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    services: dict


class VectorDBStatus(BaseModel):
    """Vector database status."""
    index_name: str
    total_documents: int
    total_chunks: int
    embedding_dimension: int
    available: bool


class ContractQuestionRequest(BaseModel):
    """Request to ask a question about a contract."""
    question: str = Field(
        ..., 
        min_length=5, 
        max_length=500, 
        description="Question about the contract"
    )


class ContractQuote(BaseModel):
    """Supporting quote from contract."""
    text: str = Field(..., description="Relevant excerpt from contract")
    confidence: float = Field(..., ge=0, le=1, description="Relevance confidence")


class ContractAnswerResponse(BaseModel):
    """Response to contract question."""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="AI-generated answer")
    supporting_quotes: List[ContractQuote] = Field(
        default_factory=list,
        description="Relevant quotes from contract"
    )
    confidence: float = Field(..., ge=0, le=1, description="Answer confidence")
    answerable: bool = Field(..., description="Whether question can be answered from contract")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the notice period?",
                "answer": "The notice period is one week for both parties.",
                "supporting_quotes": [
                    {
                        "text": "Internship can be terminated by either parties with at least one week notice.",
                        "confidence": 0.98
                    }
                ],
                "confidence": 0.95,
                "answerable": True
            }
        }


class LLMResponse(BaseModel):
    """Individual LLM response from council."""
    provider: str = Field(..., description="LLM provider (openai/groq/mistral)")
    model: str = Field(..., description="Model name")
    raw_response: str = Field(..., description="Full LLM output")
    findings: List[dict] = Field(default_factory=list, description="Raw findings as dicts")
    confidence: float = Field(..., description="Response confidence")
    response_time_ms: int = Field(..., description="Response time in milliseconds")


class AgentCouncilResponse(BaseModel):
    """Council responses for a single agent."""
    agent_name: str = Field(..., description="Agent name (skeptic/strategist/auditor)")
    llm_responses: List[LLMResponse] = Field(..., description="Individual LLM responses")
    summary: str = Field(..., description="Summary of council's consensus")
    total_findings: int = Field(..., description="Total findings before deduplication")
    final_findings: int = Field(..., description="Findings after deduplication")


class CouncilTransparencyResponse(BaseModel):
    """Complete transparency view of all council responses."""
    review_id: str
    agents: List[AgentCouncilResponse] = Field(..., description="All agent councils")
    
    class Config:
        json_schema_extra = {
            "example": {
                "review_id": "rev_abc123",
                "agents": [
                    {
                        "agent_name": "skeptic",
                        "llm_responses": [
                            {
                                "provider": "groq",
                                "model": "llama-3.1-70b-versatile",
                                "raw_response": "[{...}]",
                                "findings": [],
                                "confidence": 0.95,
                                "response_time_ms": 1234
                            }
                        ],
                        "summary": "3 LLMs responded. llama-3.1-70b: 4 findings. gpt-4: 5 findings.",
                        "total_findings": 12,
                        "final_findings": 6
                    }
                ]
            }
        }

