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
    contract_text = Column(Text, nullable=False)
    contract_type = Column(String(50), default="employment")
    safety_score = Column(Integer, nullable=False)
    total_findings = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    review_points = relationship("ReviewPointDB", back_populates="review", cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="review", cascade="all, delete-orphan")


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
