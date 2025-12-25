"""
SQLAlchemy database models for persistence and learning loop.
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class ReviewCategoryDB(enum.Enum):
    """Database enum for review categories."""
    CRITICAL = "CRITICAL"
    GOOD = "GOOD"
    NEGOTIABLE = "NEGOTIABLE"
    MISSING = "MISSING"


class ContractReview(Base):
    """Stores submitted contracts and review results."""
    __tablename__ = "contract_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for backward compatibility
    contract_text = Column(Text, nullable=False)
    contract_type = Column(String(50), default="employment")
    safety_score = Column(Integer, nullable=False)
    total_findings = Column(Integer, default=0)
    
    # Executive summary fields
    summary = Column(Text, nullable=True)
    recommendation = Column(String(20), nullable=True)  # SIGN, NEGOTIATE, or REJECT
    
    # Annotated PDF fields
    annotated_pdf_url = Column(String(500), nullable=True)
    annotation_map = Column(Text, nullable=True)  # JSON stored as text
    annotation_stats = Column(Text, nullable=True)  # JSON stored as text
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    review_points = relationship("ReviewPointDB", back_populates="review", cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="review", cascade="all, delete-orphan")
    llm_responses = relationship("AgentLLMResponse", back_populates="review", cascade="all, delete-orphan")
    refinement_suggestions = relationship("RefinementSuggestion", back_populates="review", cascade="all, delete-orphan")


class ReviewPointDB(Base):
    """Individual findings from agents."""
    __tablename__ = "review_points"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("contract_reviews.id"), nullable=False)
    category = Column(SQLEnum(ReviewCategoryDB), nullable=False, index=True)
    quote = Column(Text, nullable=True)
    advice = Column(Text, nullable=False)
    agent_source = Column(String(50), nullable=False)
    confidence = Column(Float, default=1.0)
    legal_reference = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    review = relationship("ContractReview", back_populates="review_points")
    feedbacks = relationship("UserFeedback", back_populates="review_point")


class UserFeedback(Base):
    """Tracks user feedback for RLHF learning loop."""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("contract_reviews.id"), nullable=False)
    review_point_id = Column(Integer, ForeignKey("review_points.id"), nullable=False)
    action = Column(String(20), nullable=False)  # accepted, dismissed, modified
    user_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    review = relationship("ContractReview", back_populates="feedbacks")
    review_point = relationship("ReviewPointDB", back_populates="feedbacks")
    
    # For RLHF analysis: track which advice gets accepted/dismissed
    # Example query: SELECT advice, COUNT(*) FROM user_feedback WHERE action='accepted' GROUP BY advice


class AgentLLMResponse(Base):
    """Individual LLM response from council for transparency."""
    __tablename__ = "agent_llm_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("contract_reviews.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)  # skeptic, strategist, auditor
    llm_provider = Column(String(50), nullable=False)  # openai, groq, mistral  
    llm_model = Column(String(100), nullable=False)  # gpt-4, llama-3.1-70b, etc
    raw_response = Column(Text, nullable=False)  # Full LLM JSON output
    parsed_findings = Column(Text, nullable=True)  # JSON array of findings
    confidence = Column(Float, default=1.0)
    response_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    review = relationship("ContractReview", back_populates="llm_responses")


class RefinementSuggestion(Base):
    """Stores individual refinement suggestions for a review."""
    __tablename__ = "refinement_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("contract_reviews.id"), nullable=False)
    change_id = Column(String(50), unique=True, index=True, nullable=False)  # UUID
    category = Column(String(20), nullable=False)  # CRITICAL/MISSING/NEGOTIABLE
    original_clause = Column(Text, nullable=True)  # Null for missing clauses
    improved_clause = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    affected_issue = Column(Text, nullable=True)  # Related review point
    refinement_mode = Column(String(20), default="balanced")  # balanced/unilateral
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    review = relationship("ContractReview", back_populates="refinement_suggestions")
    feedback = relationship("RefinementFeedback", back_populates="suggestion", cascade="all, delete-orphan")


class RefinementFeedback(Base):
    """Stores user feedback on refinement suggestions."""
    __tablename__ = "refinement_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    suggestion_id = Column(Integer, ForeignKey("refinement_suggestions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(10), nullable=False)  # 'accept' or 'ignore'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    suggestion = relationship("RefinementSuggestion", back_populates="feedback")
    user = relationship("User")
