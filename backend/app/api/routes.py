"""
FastAPI routes for Legal Advisor API.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
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
    VectorDBStatus,
    ContractQuestionRequest,
    ContractAnswerResponse,
    CouncilTransparencyResponse,
    AgentCouncilResponse,
    LLMResponse,
    ReviewPoint,
    ReviewCategory,
    TranslationRequest,
    TranslationResponse,
    ClauseComparison,
    RefinementPreviewResponse,
    RefinementFeedbackRequest,
    CustomRefinedContractResponse
)
from app.models.database import ContractReview, ReviewPointDB, UserFeedback, ReviewCategoryDB, AgentLLMResponse, RefinementSuggestion, RefinementFeedback
from app.models.user import User
from app.database.session import get_db
from app.auth.dependencies import get_current_active_user
from app.services.orchestrator import orchestrator
from app.services.pdf_processor import pdf_processor
from app.services.docx_processor import docx_processor
from app.services.image_processor import image_processor
from app.services.export_service import export_service
from app.services.redaction_service import process_redaction_pdf, process_redaction_docx
from app.models.schemas import TrelloSyncRequest
from app.services.trello_service import TrelloService
from app.vectordb.client import pinecone_client
from app import __version__
import os
import http.client
import json

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
        import json
        
        db_review = ContractReview(
            review_id=result.review_id,
            user_id=current_user.id,  # Link review to user
            contract_text=contract_text,
            contract_type=contract_type,
            safety_score=result.safety_score,
            total_findings=result.total_findings,
            summary=result.summary,
            recommendation=result.recommendation,
            annotated_pdf_url=result.annotated_pdf_url,
            annotation_map=json.dumps(result.annotation_map) if result.annotation_map else None,
            annotation_stats=json.dumps(result.annotation_stats) if result.annotation_stats else None
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
        
        # Save LLM council responses for transparency
        if hasattr(result, 'llm_transparency') and result.llm_transparency:
            for agent_name, llm_responses in result.llm_transparency.items():
                for llm_resp in llm_responses:
                    # Parse findings for this LLM
                    try:
                        parsed_findings = json.loads(llm_resp.get("raw_response", "[]"))
                        if isinstance(parsed_findings, list):
                            parsed_findings_json = json.dumps(parsed_findings)
                        else:
                            parsed_findings_json = "[]"
                    except json.JSONDecodeError:
                        parsed_findings_json = "[]"
                    
                    db_llm_response = AgentLLMResponse(
                        review_id=db_review.id,
                        agent_name=agent_name,
                        llm_provider=llm_resp.get("provider", "unknown"),
                        llm_model=llm_resp.get("model", "unknown"),
                        raw_response=llm_resp.get("raw_response", ""),
                        parsed_findings=parsed_findings_json,
                        confidence=1.0,  # Default confidence
                        response_time_ms=llm_resp.get("response_time_ms", 0)
                    )
                    db.add(db_llm_response)
        
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
    
    # Parse JSON fields from database
    import json
    annotation_map = json.loads(review.annotation_map) if review.annotation_map else None
    annotation_stats = json.loads(review.annotation_stats) if review.annotation_stats else None
    
    return ContractReviewResult(
        review_id=review.review_id,
        safety_score=review.safety_score,
        summary=review.summary,
        recommendation=review.recommendation,
        critical_points=points_by_category["CRITICAL"],
        good_points=points_by_category["GOOD"],
        negotiable_points=points_by_category["NEGOTIABLE"],
        missing_points=points_by_category["MISSING"],
        total_findings=review.total_findings,
        created_at=review.created_at,
        annotated_pdf_url=review.annotated_pdf_url,
        annotation_map=annotation_map,
        annotation_stats=annotation_stats
    )


@router.post("/reviews/{review_id}/ask", response_model=ContractAnswerResponse)
async def ask_contract_question(
    review_id: str,
    request: ContractQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ContractAnswerResponse:
    """
    Ask a natural language question about a previously reviewed contract.
    
    **Authentication required**
    
    Examples:
    - "What is the notice period?"
    - "Is the vendor liable for delays?"
    - "Can I work remotely?"
    - "What happens if I get terminated?"
    
    Returns:
    - AI-generated answer based on contract text
    - Supporting quotes from the contract
    - Confidence score and answerability flag
    """
    try:
        # Get contract from database
        review = db.query(ContractReview).filter(
            ContractReview.review_id == review_id,
            ContractReview.user_id == current_user.id  # Ensure user owns this review
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {review_id}"
            )
        
        # Answer question using QA service
        from app.services.contract_qa_service import contract_qa_service
        
        answer = await contract_qa_service.answer_question(
            contract_text=review.contract_text,
            question=request.question,
            contract_type=review.contract_type
        )
        
        logger.info(
            f"Answered Q&A for review {review_id}: '{request.question}' "
            f"(answerable={answer.answerable}, confidence={answer.confidence:.2f})"
        )
        
        return answer
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Q&A failed for review {review_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


from app.config import settings

@router.post("/search")
async def search_google(
    query: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search Google using Serper API.
    """
    try:
        search_query = query.get("query")
        if not search_query:
             raise HTTPException(status_code=400, detail="Query is required")

        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({
          "q": search_query
        })
        headers = {
          'X-API-KEY': settings.serper_api_key,
          'Content-Type': 'application/json'
        }
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/reviews/{review_id}/council", response_model=CouncilTransparencyResponse)
async def get_council_responses(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> CouncilTransparencyResponse:
    """
    Get individual LLM responses from the council for transparency.
    
    **Authentication required**
    
    Shows how each LLM model (GPT, Groq models, Mistral) analyzed the contract:
    - Skeptic agent's council responses
    - Strategist agent's council responses  
    - Auditor agent's council responses
    
    Useful for:
    - Understanding AI decision-making process
    - Debugging consensus failures
    - Seeing which models found what issues
    - Comparing model performance
    
    Note: Only available for reviews created after this feature was deployed.
    """
    import json
    
    try:
        # Get review
        review = db.query(ContractReview).filter(
            ContractReview.review_id == review_id,
            ContractReview.user_id == current_user.id
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {review_id}"
            )
        
        # Get all LLM responses for this review
        llm_responses_db = db.query(AgentLLMResponse).filter(
            AgentLLMResponse.review_id == review.id
        ).all()
        
        if not llm_responses_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Council responses not found. This feature is only available for recent reviews."
            )
        
        # Group responses by agent
        agents_data = {}
        for resp in llm_responses_db:
            agent_name = resp.agent_name
            if agent_name not in agents_data:
                agents_data[agent_name] = []
            
            # Parse findings from JSON (keep as raw dicts)
            findings = []
            if resp.parsed_findings:
                try:
                    findings_data = json.loads(resp.parsed_findings)
                    # Keep as dicts - raw LLM responses don't have agent_source field yet
                    if isinstance(findings_data, list):
                        findings = findings_data
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse findings for {resp.id}")
            
            agents_data[agent_name].append(LLMResponse(
                provider=resp.llm_provider,
                model=resp.llm_model,
                raw_response=resp.raw_response,
                findings=findings,
                confidence=resp.confidence,
                response_time_ms=resp.response_time_ms
            ))
        
        # Build agent council responses with summaries
        agent_councils = []
        
        # Get final deduplicated findings for context
        final_points_per_agent = {}
        for db_point in review.review_points:
            agent = db_point.agent_source
            if agent not in final_points_per_agent:
                final_points_per_agent[agent] = 0
            final_points_per_agent[agent] += 1
        
        for agent_name, llm_resps in agents_data.items():
            # Generate summary
            num_llms = len(llm_resps)
            total_findings_before_dedup = sum(len(r.findings) for r in llm_resps)
            final_findings = final_points_per_agent.get(agent_name, 0)
            
            # Build detailed summary
            summary_parts = [
                f"{num_llms} LLM{'s' if num_llms > 1 else ''} responded.",
                f"Total findings before dedup: {total_findings_before_dedup}."
            ]
            
            # Show individual model findings
            for llm_resp in llm_resps:
                summary_parts.append(
                    f"{llm_resp.model}: {len(llm_resp.findings)} finding{'s' if len(llm_resp.findings) != 1 else ''} "
                    f"({llm_resp.response_time_ms}ms)."
                )
            
            summary_parts.append(f"Final after dedup: {final_findings} findings.")
            
            agent_councils.append(AgentCouncilResponse(
                agent_name=agent_name,
                llm_responses=llm_resps,
                summary=" ".join(summary_parts),
                total_findings=total_findings_before_dedup,
                final_findings=final_findings
            ))
        
        # Sort by agent name for consistency
        agent_councils.sort(key=lambda x: x.agent_name)
        
        logger.info(
            f"Retrieved council transparency for review {review_id}: "
            f"{len(agent_councils)} agents, {len(llm_responses_db)} total LLM responses"
        )
        
        return CouncilTransparencyResponse(
            review_id=review_id,
            agents=agent_councils
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get council responses for {review_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve council responses: {str(e)}"
        )


@router.get("/reviews/{review_id}/annotated-pdf")
async def get_annotated_pdf(review_id: str, db: Session = Depends(get_db)) -> FileResponse:
    """
    Download the annotated PDF with color-coded highlights.
    
    **Auto-regenerates** if missing!
    Highlights are clickable and show the corresponding review point.
    - RED highlights = CRITICAL issues
    - ORANGE highlights = NEGOTIABLE terms
    - GREEN highlights = GOOD points
    """
    try:
        annotated_pdf_path = Path("data/annotated_pdfs") / f"{review_id}_annotated.pdf"
        
        if not annotated_pdf_path.exists():
            # Regenerate annotated PDF on-demand
            logger.info(f"Annotated PDF missing for {review_id}, regenerating...")
            
            # Get review from database
            review = db.query(ContractReview).filter(
                ContractReview.review_id == review_id
            ).first()
            
            if not review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Review not found: {review_id}"
                )
            
            # Check if we have contract text (needed for PDF generation)
            if not review.contract_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot generate annotated PDF: Original contract text not found"
                )
            
            # Get all review points for annotation
            all_points_db = review.review_points
            
            if not all_points_db:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot generate annotated PDF: No review points found"
                )
            
            # Convert to ReviewPoint objects
            all_review_points = []
            for db_point in all_points_db:
                point = ReviewPoint(
                    category=ReviewCategory[db_point.category.name],
                    quote=db_point.quote,
                    advice=db_point.advice,
                    agent_source=db_point.agent_source,
                    confidence=db_point.confidence,
                    legal_reference=db_point.legal_reference
                )
                all_review_points.append(point)
            
            # Create temporary PDF from contract text
            temp_dir = Path("data/temp_uploads")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_pdf_path = temp_dir / f"{review_id}_temp.pdf"
            
            # Generate PDF from text using ReportLab
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch
            
            c = canvas.Canvas(str(temp_pdf_path), pagesize=letter)
            width, height = letter
            
            # Write contract text to PDF
            y = height - inch
            for line in review.contract_text.split('\n'):
                if y < inch:  # New page
                    c.showPage()
                    y = height - inch
                c.drawString(inch, y, line[:80])  # Limit line length
                y -= 12
            c.save()
            
            # Create annotated directory
            annotated_dir = Path("data/annotated_pdfs")
            annotated_dir.mkdir(parents=True, exist_ok=True)
            
            # Annotate PDF
            from app.services.pdf_annotator import pdf_annotator
            
            annotation_stats = pdf_annotator.annotate_pdf(
                input_pdf_path=str(temp_pdf_path),
                output_pdf_path=str(annotated_pdf_path),
                review_points=all_review_points
            )
            
            # Clean up temp file
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()
            
            logger.info(f"Regenerated annotated PDF with {annotation_stats['highlights_added']} highlights")
        
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
        logger.error(f"Failed to retrieve/generate annotated PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve annotated PDF: {str(e)}"
        )



@router.get("/reviews/{review_id}/annotated-pdf/redacted")
async def get_redacted_annotated_pdf(review_id: str):
    """
    Download the annotated PDF with sensitive information redacted (black boxes).
    
    This endpoint:
    1. Retrieves the annotated PDF with highlights
    2. Applies redaction to cover Names, Emails, Phone numbers, Organizations
    3. Returns the redacted PDF with both highlights AND black boxes
    
    Perfect for sharing reviewed contracts while protecting sensitive information.
    """
    try:
        annotated_pdf_path = Path("data/annotated_pdfs") / f"{review_id}_annotated.pdf"
        
        if not annotated_pdf_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Annotated PDF not found for review: {review_id}. Only PDF uploads generate annotated PDFs."
            )
        
        # Read the annotated PDF
        with open(annotated_pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Apply redaction
        redacted_stream = process_redaction_pdf(pdf_bytes)
        
        # Return as streaming response
        return StreamingResponse(
            redacted_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={review_id}_annotated_redacted.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create redacted PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create redacted PDF: {str(e)}"
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


@router.get("/reviews/{review_id}/refinement-preview", response_model=RefinementPreviewResponse)
async def get_refinement_preview(
    review_id: str,
    mode: str = "balanced",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> RefinementPreviewResponse:
    """
    Preview clause-by-clause refinement suggestions.
    
    **Saves LLM tokens!** Generates once, stores in database for reuse.
    """
    review = db.query(ContractReview).filter(
        ContractReview.review_id == review_id,
        ContractReview.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail=f"Review not found: {review_id}")
    
    # Check for cached suggestions
    existing = db.query(RefinementSuggestion).filter(
        RefinementSuggestion.review_id == review.id,
        RefinementSuggestion.refinement_mode == mode
    ).all()
    
    if existing:
        logger.info(f"Using cached suggestions ({len(existing)} items)")
        changes = [ClauseComparison(**{"change_id": s.change_id, "category": s.category, "original_clause": s.original_clause, "improved_clause": s.improved_clause, "reasoning": s.reasoning, "affected_issue": s.affected_issue}) for s in existing]
        return RefinementPreviewResponse(review_id=review_id, total_changes=len(changes), changes=changes, summary=f"{len(changes)} improvements", mode=mode)
    
    # Generate new
    from app.services.contract_refinement import contract_refinement_service
    points = {"CRITICAL": [], "MISSING": [], "NEGOTIABLE": [], "GOOD": []}
    for p in review.review_points:
        pt = ReviewPoint(category=ReviewCategory[p.category.name], quote=p.quote, advice=p.advice, agent_source=p.agent_source, confidence=p.confidence, legal_reference=p.legal_reference)
        points[p.category.name].append(pt)
    
    comparisons = await contract_refinement_service.generate_clause_comparisons(
        review.contract_text, points["CRITICAL"], points["MISSING"], points["NEGOTIABLE"], mode
    )
    
    for c in comparisons:
        db.add(RefinementSuggestion(review_id=review.id, change_id=c["change_id"], category=c["category"], original_clause=c["original_clause"], improved_clause=c["improved_clause"], reasoning=c["reasoning"], affected_issue=c["affected_issue"], refinement_mode=mode))
    db.commit()
    
    changes = [ClauseComparison(**c) for c in comparisons]
    return RefinementPreviewResponse(review_id=review_id, total_changes=len(changes), changes=changes, summary=f"{len(changes)} improvements", mode=mode)


@router.post("/reviews/{review_id}/refine-with-feedback", response_model=CustomRefinedContractResponse)
async def refine_with_user_feedback(
    review_id: str,
    request: RefinementFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate custom refined contract with only user-accepted changes.
    """
    review = db.query(ContractReview).filter(
        ContractReview.review_id == review_id,
        ContractReview.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    suggestions = db.query(RefinementSuggestion).filter(
        RefinementSuggestion.review_id == review.id,
        RefinementSuggestion.refinement_mode == request.refinement_mode
    ).all()
    
    if not suggestions:
        raise HTTPException(status_code=404, detail="Generate preview first")
    
    # Save feedback
    for f in request.feedback:
        s = next((s for s in suggestions if s.change_id == f.change_id), None)
        if s:
            existing = db.query(RefinementFeedback).filter(RefinementFeedback.suggestion_id == s.id, RefinementFeedback.user_id == current_user.id).first()
            if existing:
                existing.action = f.action
            else:
                db.add(RefinementFeedback(suggestion_id=s.id, user_id=current_user.id, action=f.action))
    db.commit()
    
    accepted_ids = [f.change_id for f in request.feedback if f.action == "accept"]
    all_comps = [{"change_id": s.change_id, "category": s.category, "original_clause": s.original_clause, "improved_clause": s.improved_clause, "reasoning": s.reasoning, "affected_issue": s.affected_issue} for s in suggestions]
    
    from app.services.contract_refinement import contract_refinement_service
    refined = await contract_refinement_service.apply_selected_changes(review.contract_text, all_comps, accepted_ids)
    
    # Generate PDF for download
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"{review_id}_custom_refined.pdf"
    output_path = output_dir / pdf_filename
    
    # Create PDF from refined contract text
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.units import inch
    
    c = pdf_canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch, "Refined Employment Contract")
    
    # Add metadata
    c.setFont("Helvetica", 10)
    c.drawString(inch, height - inch - 20, f"Accepted Changes: {len(accepted_ids)} | Ignored: {len(request.feedback) - len(accepted_ids)}")
    
    # Write refined contract text
    c.setFont("Helvetica", 11)
    y = height - inch - 60
    for line in refined.split('\n'):
        if y < inch:  # New page
            c.showPage()
            y = height - inch
        # Wrap long lines
        if len(line) > 80:
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line + word) < 80:
                    current_line += word + " "
                else:
                    c.drawString(inch, y, current_line.strip())
                    y -= 14
                    current_line = word + " "
                    if y < inch:
                        c.showPage()
                        y = height - inch
            if current_line:
                c.drawString(inch, y, current_line.strip())
                y -= 14
        else:
            c.drawString(inch, y, line)
            y -= 14
    
    c.save()
    
    pdf_url = f"/api/reviews/{review_id}/custom-refined-pdf"
    logger.info(f"Generated custom refined PDF with {len(accepted_ids)} accepted changes")
    
    return CustomRefinedContractResponse(
        review_id=review_id,
        accepted_changes=len(accepted_ids),
        ignored_changes=len(request.feedback) - len(accepted_ids),
        refined_contract=refined,
        pdf_url=pdf_url
    )


@router.get("/reviews/{review_id}/custom-refined-pdf")
async def get_custom_refined_pdf(review_id: str):
    """Download the custom refined contract PDF."""
    try:
        output_path = Path("data/exports") / f"{review_id}_custom_refined.pdf"
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Custom refined PDF not found. Generate it first via /refine-with-feedback")
        
        return FileResponse(
            path=str(output_path),
            filename=f"{review_id}_custom_refined.pdf",
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{review_id}_custom_refined.pdf"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve custom refined PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate", response_model=TranslationResponse)
async def translate_text_endpoint(
    request: TranslationRequest,
    current_user: User = Depends(get_current_active_user)
) -> TranslationResponse:
    """
    Translate text to the target language using Gemini.
    """
    from app.services.translation_service import translation_service
    
    translated_text = await translation_service.translate_text(request.text, request.target_language)
    
    return TranslationResponse(
        translated_text=translated_text,
        original_text=request.text,
        target_language=request.target_language
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


@router.post("/redact")
async def redact_document(file: UploadFile = File(...)):
    """
    Uploads a file, automatically detects sensitive info (Names, ORGs, Emails),
    redacts it, and returns the file inline.
    """
    try:
        content = await file.read()
        filename = file.filename.lower()
        redacted_stream = None
        media_type = ""

        # Logic to choose processor
        if filename.endswith(".pdf"):
            redacted_stream = process_redaction_pdf(content)
            media_type = "application/pdf"
        elif filename.endswith((".docx", ".doc")):
            redacted_stream = process_redaction_docx(content)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Unsupported file type. Use PDF or DOCX."
            )

        # Return response matching your requested style
        return StreamingResponse(
            redacted_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=redacted_{file.filename}"
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions so FastAPI handles them correctly
        raise
    except Exception as e:
        logger.error(f"Failed to redact document {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to redact document: {str(e)}"
        )
    
@router.post("/integrations/trello/sync")
async def sync_to_trello(
    request: TrelloSyncRequest,
    db: Session = Depends(get_db)
):
    """
    Export Critical and Missing findings to Trello Cards.
    """
    review = db.query(ContractReview).filter(ContractReview.review_id == request.review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    from app.models.schemas import ReviewPoint, ReviewCategory
    all_points = []
    for db_point in review.review_points:
        all_points.append(ReviewPoint(
            category=ReviewCategory[db_point.category.name],
            quote=db_point.quote,
            advice=db_point.advice,
            agent_source=db_point.agent_source,
            confidence=db_point.confidence,
            legal_reference=db_point.legal_reference
        ))

    trello = TrelloService(api_key=request.trello_api_key, token=request.trello_token)

    try:
        count = await trello.sync_findings_to_trello(
            board_id=request.trello_board_id,
            review_points=all_points,
            filters=request.filters
        )

        return {"status": "success", "cards_created": count}
    
    except Exception as e:
        logger.error(f"Trello sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trello sync failed: {str(e)}")