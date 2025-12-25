"""
Interactive Refinement API Endpoints.

Allows users to preview refinement suggestions clause-by-clause,
provide feedback (accept/ignore), and export customized refined contracts.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import uuid

from app.models.schemas import (
    RefinementPreviewResponse,
    ClauseComparison,
    RefinementFeedbackRequest,
    CustomRefinedContractResponse,
    ReviewPoint,
    ReviewCategory
)
from app.models.database import ContractReview, RefinementSugg

estion, RefinementFeedback, ReviewPointDB
from app.models.user import User
from app.database.session import get_db
from app.auth.dependencies import get_current_active_user
from app.services.contract_refinement import contract_refinement_service

logger = logging.getLogger(__name__)


async def get_refinement_preview(
    review_id: str,
    mode: str = "balanced",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> RefinementPreviewResponse:
    """
    Preview clause-by-clause refinement suggestions.
    
    Generates suggestions once, stores in database for reuse (saves LLM tokens!).
    Users can review multiple times without regeneration cost.
    """
    # Get review
    review = db.query(ContractReview).filter(
        ContractReview.review_id == review_id,
        ContractReview.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail=f"Review not found: {review_id}")
    
    #Check if suggestions already generated for this mode
    existing_suggestions = db.query(RefinementSuggestion).filter(
        RefinementSuggestion.review_id == review.id,
        RefinementSuggestion.refinement_mode == mode
    ).all()
    
    if existing_suggestions:
        # Return cached suggestions (FREE!)
        logger.info(f"Returning cached suggestions for {review_id} (mode={mode})")
        changes = [
            ClauseComparison(
                change_id=s.change_id,
                category=s.category,
                original_clause=s.original_clause,
                improved_clause=s.improved_clause,
                reasoning=s.reasoning,
                affected_issue=s.affected_issue
            )
            for s in existing_suggestions
        ]
        
        return RefinementPreviewResponse(
            review_id=review_id,
            total_changes=len(changes),
            changes=changes,
            summary=f"{len(changes)} improvements suggested",
            mode=mode
        )
    
    # Generate new suggestions (uses LLM tokens)
    logger.info(f"Generating new refinement suggestions for {review_id} (mode={mode})")
    
    # Reconstruct review points
    points_by_category = {"CRITICAL": [], "MISSING": [], "NEGOTIABLE": []}
    for db_point in review.review_points:
        point = ReviewPoint(
            category=ReviewCategory[db_point.category.name],
            quote=db_point.quote,
            advice=db_point.advice,
            agent_source=db_point.agent_source,
            confidence=db_point.confidence,
            legal_reference=db_point.legal_reference
        )
        points_by_category[db_point.category.name].append(point)
    
    # Generate clause comparisons
    comparisons = await contract_refinement_service.generate_clause_comparisons(
        original_contract=review.contract_text,
        critical_points=points_by_category["CRITICAL"],
        missing_points=points_by_category["MISSING"],
        negotiable_points=points_by_category["NEGOTIABLE"],
        refinement_mode=mode
    )
    
    # Save to database for reuse
    for comp in comparisons:
        db_suggestion = RefinementSuggestion(
            review_id=review.id,
            change_id=comp["change_id"],
            category=comp["category"],
            original_clause=comp["original_clause"],
            improved_clause=comp["improved_clause"],
            reasoning=comp["reasoning"],
            affected_issue=comp["affected_issue"],
            refinement_mode=mode
        )
        db.add(db_suggestion)
    
    db.commit()
    logger.info(f"Saved {len(comparisons)} suggestions to database")
    
    # Return response
    changes = [ClauseComparison(**c) for c in comparisons]
    return RefinementPreviewResponse(
        review_id=review_id,
        total_changes=len(changes),
        changes=changes,
        summary=f"{len(changes)} improvements: {len([c for c in changes if c.category=='CRITICAL'])} critical, {len([c for c in changes if c.category=='MISSING'])} missing, {len([c for c in changes if c.category=='NEGOTIABLE'])} negotiable",
        mode=mode
    )


async def refine_with_user_feedback(
    review_id: str,
    request: RefinementFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate refined contract with only user-accepted changes.
    
    Saves user feedback to database and applies selective refinements.
    """
    # Get review
    review = db.query(ContractReview).filter(
        ContractReview.review_id == review_id,
        ContractReview.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail=f"Review not found: {review_id}")
    
    # Get suggestions for this mode
    suggestions = db.query(RefinementSuggestion).filter(
        RefinementSuggestion.review_id == review.id,
        RefinementSuggestion.refinement_mode == request.refinement_mode
    ).all()
    
    if not suggestions:
        raise HTTPException(status_code=404, detail="No refinement suggestions found. Generate preview first.")
    
    # Save user feedback
    for feedback_item in request.feedback:
        suggestion = next((s for s in suggestions if s.change_id == feedback_item.change_id), None)
        if suggestion:
            # Check if feedback already exists
            existing = db.query(RefinementFeedback).filter(
                RefinementFeedback.suggestion_id == suggestion.id,
                RefinementFeedback.user_id == current_user.id
            ).first()
            
            if existing:
                existing.action = feedback_item.action
            else:
                db_feedback = RefinementFeedback(
                    suggestion_id=suggestion.id,
                    user_id=current_user.id,
                    action=feedback_item.action
                )
                db.add(db_feedback)
    
    db.commit()
    
    # Get accepted change IDs
    accepted_ids = [f.change_id for f in request.feedback if f.action == "accept"]
    ignored_ids = [f.change_id for f in request.feedback if f.action == "ignore"]
    
    logger.info(f"User accepted {len(accepted_ids)}, ignored {len(ignored_ids)} changes")
    
    # Convert suggestions to dict format for service
    all_comparisons = [{
        "change_id": s.change_id,
        "category": s.category,
        "original_clause": s.original_clause,
        "improved_clause": s.improved_clause,
        "reasoning": s.reasoning,
        "affected_issue": s.affected_issue
    } for s in suggestions]
    
    # Generate custom refined contract
    refined_contract = await contract_refinement_service.apply_selected_changes(
        original_contract=review.contract_text,
        all_comparisons=all_comparisons,
        accepted_change_ids=accepted_ids
    )
    
    return CustomRefinedContractResponse(
        review_id=review_id,
        accepted_changes=len(accepted_ids),
        ignored_changes=len(ignored_ids),
        refined_contract=refined_contract,
        pdf_url=None  # Could generate PDF here if needed
    )
