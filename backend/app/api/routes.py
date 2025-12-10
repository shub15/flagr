"""
FastAPI routes for Legal Advisor API.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import tempfile

from app.models.schemas import (
    ContractReviewRequest,
    ContractReviewResult,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    VectorDBStatus
)
from app.models.database import ContractReview, ReviewPointDB, UserFeedback, ReviewCategoryDB
from app.models.user import User
from app.database.session import get_db
from app.auth.dependencies import get_current_active_user
from app.services.orchestrator import orchestrator
from app.services.pdf_processor import pdf_processor
from app.services.docx_processor import docx_processor
from app.services.image_processor import image_processor
from app.services.export_service import export_service
from app.vectordb.client import pinecone_client
from app import __version__

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["legal-advisor"])


@router.post("/review", response_model=ContractReviewResult, status_code=status.HTTP_200_OK)
async def review_contract(
    file: UploadFile = File(...),
    contract_type: str = "employment",
    context: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ContractReviewResult:
    """
    Submit a contract document for multi-agent review.
    
    **Authentication required** - Include JWT token in Authorization header.
    
    Accepts file uploads (PDF, DOCX, or images) and automatically extracts text.
    Supported formats: .pdf, .docx, .png, .jpg, .jpeg, .tif, .tiff, .bmp, .webp
    
    Triggers the orchestrator which:
    - Runs 3 agents in parallel (Skeptic, Strategist, Auditor)
    - Each agent queries council of LLMs
    - Retrieves relevant legal context from Pinecone
    - Aggregates findings via Referee
    """
    try:
        filename = file.filename.lower()
        
        # Determine file type
        if filename.endswith('.pdf'):
            file_type = "pdf"
        elif filename.endswith('.docx'):
            file_type = "docx"
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp')):
            file_type = "image"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Supported: PDF, DOCX, PNG, JPG, JPEG, TIF, TIFF, BMP, WEBP"
            )
        
        logger.info(f"Received contract review request (type: {contract_type}, file: {file.filename})")
        
        # Save uploaded file temporarily
        temp_dir = Path("data/temp_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file_path = temp_dir / file.filename
        
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text based on file type
        contract_text = ""
        
        if file_type == "pdf":
            # Extract text from PDF pages
            pages = pdf_processor.extract_text_with_pages(str(temp_file_path))
            contract_text = "\n\n".join(page["text"] for page in pages)
            logger.info(f"Extracted {len(contract_text)} chars from PDF ({len(pages)} pages)")
            
        elif file_type == "docx":
            # Extract text from DOCX
            paragraphs = docx_processor.extract_text_from_docx(str(temp_file_path))
            contract_text = "\n\n".join(p["text"] for p in paragraphs)
            logger.info(f"Extracted {len(contract_text)} chars from DOCX ({len(paragraphs)} paragraphs)")
            
        else:  # image
            # Extract text using Gemini Vision
            contract_text = image_processor.extract_text_from_image(str(temp_file_path))
            logger.info(f"Extracted {len(contract_text)} chars from image via Gemini Vision")
        
        # Clean up temp file (but keep PDF for annotation)
        pdf_file_for_annotation = None
        if file_type == "pdf":
            # Keep the PDF file for annotation
            pdf_file_for_annotation = temp_file_path
        else:
            # Delete non-PDF temp files
            temp_file_path.unlink()
        
        if not contract_text or len(contract_text) < 50:
            if pdf_file_for_annotation:
                pdf_file_for_annotation.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract meaningful text from {file_type.upper()}. File may be empty or corrupted."
            )
        
        # Execute orchestrator
        result = await orchestrator.review_contract(
            contract_text=contract_text,
            contract_type=contract_type,
            context=context
        )
        
        # Generate annotated PDF if input was PDF
        if pdf_file_for_annotation:
            try:
                from app.services.pdf_annotator import pdf_annotator
                
                # Create annotated PDF directory
                annotated_dir = Path("data/annotated_pdfs")
                annotated_dir.mkdir(parents=True, exist_ok=True)
                
                annotated_pdf_path = annotated_dir / f"{result.review_id}_annotated.pdf"
                
                # Get all points with quotes for annotation
                all_review_points = (
                    result.critical_points +
                    result.good_points +
                    result.negotiable_points +
                    result.missing_points
                )
                
                # Annotate PDF
                annotation_stats = pdf_annotator.annotate_pdf(
                    input_pdf_path=str(pdf_file_for_annotation),
                    output_pdf_path=str(annotated_pdf_path),
                    review_points=all_review_points
                )
                
                # Create annotation map
                annotation_map = pdf_annotator.create_annotation_map(all_review_points)
                
                # Add to result
                result.annotated_pdf_url = f"/api/reviews/{result.review_id}/annotated-pdf"
                result.annotation_map = annotation_map
                result.annotation_stats = annotation_stats
                
                logger.info(f"Annotated PDF created: {annotation_stats['highlights_added']} highlights")
                
            except Exception as e:
                logger.error(f"PDF annotation failed (continuing without it): {e}")
                # Continue without annotated PDF
            finally:
                # Clean up original uploaded PDF
                if pdf_file_for_annotation.exists():
                    pdf_file_for_annotation.unlink()
        
        # Save to database
        db_review = ContractReview(
            review_id=result.review_id,
            user_id=current_user.id,  # Link review to user
            contract_text=contract_text,
            contract_type=contract_type,
            safety_score=result.safety_score,
            total_findings=result.total_findings
        )
        db.add(db_review)
        db.flush()
        
        # Save review points
        all_points = (
            result.critical_points +
            result.good_points +
            result.negotiable_points +
            result.missing_points
        )
        
        for point in all_points:
            db_point = ReviewPointDB(
                review_id=db_review.id,
                category=ReviewCategoryDB[point.category.value],
                quote=point.quote,
                advice=point.advice,
                agent_source=point.agent_source,
                confidence=point.confidence,
                legal_reference=point.legal_reference
            )
            db.add(db_point)
        
        db.commit()
        
        logger.info(f"Contract review completed: {result.review_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contract review failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contract review failed: {str(e)}"
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
) -> FeedbackResponse:
    """
    Submit user feedback for a review point (RLHF learning loop).
    """
    try:
        # Find the review
        review = db.query(ContractReview).filter(
            ContractReview.review_id == feedback.review_id
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {feedback.review_id}"
            )
        
        # Get review points
        review_points = db.query(ReviewPointDB).filter(
            ReviewPointDB.review_id == review.id
        ).all()
        
        if feedback.point_index >= len(review_points):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid point index"
            )
        
        point = review_points[feedback.point_index]
        
        # Save feedback
        db_feedback = UserFeedback(
            review_id=review.id,
            review_point_id=point.id,
            action=feedback.action,
            user_comment=feedback.user_comment
        )
        db.add(db_feedback)
        db.commit()
        
        logger.info(f"Feedback recorded for review {feedback.review_id}")
        
        return FeedbackResponse(
            success=True,
            message="Feedback recorded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}"
        )


@router.post("/legal-docs/upload", status_code=status.HTTP_201_CREATED)
async def upload_legal_document(
    file: UploadFile = File(...),
    namespace: str = "labour_law"
) -> dict:
    """
    Upload legal documents (PDF, DOCX, or images) for vectorization.
    Supports: .pdf, .docx, .png, .jpg, .jpeg, .tif, .tiff
    """
    try:
        filename = file.filename.lower()
        
        # Determine file type
        if filename.endswith('.pdf'):
            file_type = "pdf"
        elif filename.endswith('.docx'):
            file_type = "docx"
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')):
            file_type = "image"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Supported: PDF, DOCX, PNG, JPG, JPEG, TIF, TIFF"
            )
        
        # Save uploaded file temporarily
        upload_dir = Path("data/legal_docs")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Uploaded {file_type.upper()}: {file.filename}")
        
        # Process based on file type
        if file_type == "pdf":
            documents = pdf_processor.process_pdf(
                str(file_path),
                metadata={"category": "indian_labour_law"}
            )
        elif file_type == "docx":
            documents = docx_processor.process_docx(
                str(file_path),
                metadata={"category": "indian_labour_law"}
            )
        else:  # image
            documents = image_processor.process_image(
                str(file_path),
                metadata={"category": "indian_labour_law"}
            )
        
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text from {file_type.upper()}"
            )
        
        # Upload to Pinecone
        result = pinecone_client.upsert_documents(documents, namespace=namespace)
        
        logger.info(f"Vectorized {result['upserted_count']} chunks from {file.filename}")
        
        return {
            "filename": file.filename,
            "file_type": file_type,
            "chunks_created": len(documents),
            "chunks_uploaded": result["upserted_count"],
            "namespace": namespace
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.get("/legal-docs/status", response_model=VectorDBStatus)
async def get_vectordb_status() -> VectorDBStatus:
    """Check Pinecone vector database status."""
    try:
        stats = pinecone_client.get_stats()
        
        # Extract namespace info
        namespaces = stats.get("namespaces", {})
        labour_law_ns = namespaces.get("labour_law", {})
        
        return VectorDBStatus(
            index_name=pinecone_client.index_name,
            total_documents=len(namespaces),
            total_chunks=stats.get("total_vector_count", 0),
            embedding_dimension=stats.get("dimension", 1536),
            available=stats.get("total_vector_count", 0) > 0
        )
    except Exception as e:
        logger.error(f"Failed to get vector DB status: {e}")
        return VectorDBStatus(
            index_name=pinecone_client.index_name,
            total_documents=0,
            total_chunks=0,
            embedding_dimension=1536,
            available=False
        )


@router.get("/reviews")
async def get_all_reviews(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Get all contract reviews for the authenticated user.
    
    **Authentication required** - Include JWT token in Authorization header.
    
    Returns a list of reviews with metadata and finding counts.
    """
    try:
        # Fetch all reviews for the current user, ordered by most recent first
        reviews = db.query(ContractReview).filter(
            ContractReview.user_id == current_user.id
        ).order_by(ContractReview.created_at.desc()).all()
        
        # Format response with summary information
        result = []
        for review in reviews:
            # Count findings by category
            critical_count = sum(1 for p in review.review_points if p.category == ReviewCategoryDB.CRITICAL)
            good_count = sum(1 for p in review.review_points if p.category == ReviewCategoryDB.GOOD)
            negotiable_count = sum(1 for p in review.review_points if p.category == ReviewCategoryDB.NEGOTIABLE)
            missing_count = sum(1 for p in review.review_points if p.category == ReviewCategoryDB.MISSING)
            
            result.append({
                "review_id": review.review_id,
                "contract_type": review.contract_type,
                "safety_score": review.safety_score,
                "total_findings": review.total_findings,
                "critical_count": critical_count,
                "good_count": good_count,
                "negotiable_count": negotiable_count,
                "missing_count": missing_count,
                "created_at": review.created_at.isoformat()
            })
        
        logger.info(f"Retrieved {len(result)} reviews for user {current_user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to fetch reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reviews: {str(e)}"
        )


@router.get("/reviews/{review_id}", response_model=ContractReviewResult)
async def get_review(review_id: str, db: Session = Depends(get_db)) -> ContractReviewResult:
    """Retrieve a past contract review."""
    review = db.query(ContractReview).filter(
        ContractReview.review_id == review_id
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review not found: {review_id}"
        )
    
    # Reconstruct ReviewPoints from database
    from app.models.schemas import ReviewPoint, ReviewCategory
    
    points_by_category = {
        "CRITICAL": [],
        "GOOD": [],
        "NEGOTIABLE": [],
        "MISSING": []
    }
    
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
    
    return ContractReviewResult(
        review_id=review.review_id,
        safety_score=review.safety_score,
        critical_points=points_by_category["CRITICAL"],
        good_points=points_by_category["GOOD"],
        negotiable_points=points_by_category["NEGOTIABLE"],
        missing_points=points_by_category["MISSING"],
        total_findings=review.total_findings,
        created_at=review.created_at
    )


@router.get("/reviews/{review_id}/annotated-pdf")
async def get_annotated_pdf(review_id: str) -> FileResponse:
    """
    Download the annotated PDF with color-coded highlights.
    
    Highlights are clickable and show the corresponding review point.
    - RED highlights = CRITICAL issues
    - ORANGE highlights = NEGOTIABLE terms
    - GREEN highlights = GOOD points
    """
    try:
        annotated_pdf_path = Path("data/annotated_pdfs") / f"{review_id}_annotated.pdf"
        
        if not annotated_pdf_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Annotated PDF not found for review: {review_id}. Only PDF uploads generate annotated PDFs."
            )
        
        return FileResponse(
            path=str(annotated_pdf_path),
            filename=f"{review_id}_annotated.pdf",
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={review_id}_annotated.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve annotated PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve annotated PDF: {str(e)}"
        )


@router.get("/reviews/{review_id}/export/docx")
async def export_review_word(
    review_id: str,
    mode: str = "balanced",
    db: Session = Depends(get_db)
):
    """
    Export contract review as Word document with redline markup.
    """
    try:
        # Get review from database
        review = db.query(ContractReview).filter(
            ContractReview.review_id == review_id
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {review_id}"
            )
        
        # Reconstruct ReviewResult
        from app.models.schemas import ReviewPoint, ReviewCategory
        
        points_by_category = {
            "CRITICAL": [],
            "GOOD": [],
            "NEGOTIABLE": [],
            "MISSING": []
        }
        
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
        
        review_result = ContractReviewResult(
            review_id=review.review_id,
            safety_score=review.safety_score,
            critical_points=points_by_category["CRITICAL"],
            good_points=points_by_category["GOOD"],
            negotiable_points=points_by_category["NEGOTIABLE"],
            missing_points=points_by_category["MISSING"],
            total_findings=review.total_findings,
            created_at=review.created_at
        )
        
        # Generate refined contract using LLM
        from app.services.contract_refinement import contract_refinement_service
        
        refined_contract = await contract_refinement_service.refine_contract(
            original_contract=review.contract_text,
            critical_points=review_result.critical_points,
            missing_points=review_result.missing_points,
            negotiable_points=review_result.negotiable_points,
            safety_score=review.safety_score,
            refinement_mode=mode
        )
        
        # Generate Word document with refined contract
        output_dir = Path("data/exports")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{review_id}_refined.docx"
        
        export_service.generate_refined_contract_docx(
            refined_contract=refined_contract,
            safety_score=review.safety_score,
            review_id=review.review_id,
            output_path=str(output_path)
        )
        
        logger.info(f"Generated refined contract DOCX for review {review_id}")
        
        return FileResponse(
            path=str(output_path),
            filename=f"{review_id}_refined.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Word export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Word export failed: {str(e)}"
        )


@router.get("/reviews/{review_id}/export/pdf")
async def export_review_pdf(
    review_id: str,
    mode: str = "balanced",
    db: Session = Depends(get_db)
):
    """
    Export refined contract as PDF.
    
    Args:
        mode: Refinement mode - 'balanced' (fair to both) or 'unilateral' (employee-favoring)
    """
    try:
        # Get review from database
        review = db.query(ContractReview).filter(
            ContractReview.review_id == review_id
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {review_id}"
            )
        
        # Reconstruct ReviewResult
        from app.models.schemas import ReviewPoint, ReviewCategory
        
        points_by_category = {
            "CRITICAL": [],
            "GOOD": [],
            "NEGOTIABLE": [],
            "MISSING": []
        }
        
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
        
        review_result = ContractReviewResult(
            review_id=review.review_id,
            safety_score=review.safety_score,
            critical_points=points_by_category["CRITICAL"],
            good_points=points_by_category["GOOD"],
            negotiable_points=points_by_category["NEGOTIABLE"],
            missing_points=points_by_category["MISSING"],
            total_findings=review.total_findings,
            created_at=review.created_at
        )

        # Generate refined contract using LLM
        from app.services.contract_refinement import contract_refinement_service
        
        refined_contract = await contract_refinement_service.refine_contract(
            original_contract=review.contract_text,
            critical_points=review_result.critical_points,
            missing_points=review_result.missing_points,
            negotiable_points=review_result.negotiable_points,
            safety_score=review.safety_score,
            refinement_mode=mode
        )
        
        # Generate PDF with refined contract
        output_dir = Path("data/exports")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{review_id}_refined.pdf"
        
        export_service.generate_refined_contract_pdf(
            refined_contract=refined_contract,
            safety_score=review.safety_score,
            review_id=review.review_id,
            output_path=str(output_path)
        )
        
        logger.info(f"Generated refined contract PDF for review {review_id}")
        
        # Return PDF with inline disposition to open in browser
        from fastapi.responses import Response
        
        with open(output_path, 'rb') as f:
            pdf_content = f.read()
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{review_id}_refined.pdf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF export failed: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    orchestrator_health = await orchestrator.health_check()
    
    # Check vector DB
    try:
        stats = pinecone_client.get_stats()
        vectordb_status = "healthy" if stats else "unavailable"
    except:
        vectordb_status = "unavailable"
    
    return HealthResponse(
        status="healthy",
        version=__version__,
        services={
            "orchestrator": orchestrator_health["orchestrator"],
            "agents": orchestrator_health["agents"],
            "vectordb": vectordb_status
        }
    )
