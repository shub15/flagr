"""
PDF annotation service for creating interactive highlighted PDFs.
Highlights quotes and adds clickable annotations mapped to review points.
"""

import logging
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
from pathlib import Path
from app.models.schemas import ReviewPoint, ReviewCategory

logger = logging.getLogger(__name__)


class PDFAnnotator:
    """Annotates PDFs with color-coded highlights and clickable links."""
    
    # Color schemes for different categories
    COLORS = {
        ReviewCategory.CRITICAL: (1.0, 0.0, 0.0),      # Red
        ReviewCategory.NEGOTIABLE: (1.0, 0.65, 0.0),   # Orange
        ReviewCategory.GOOD: (0.0, 0.8, 0.0),          # Green
        ReviewCategory.MISSING: (0.5, 0.5, 0.5)        # Gray (not highlighted, just listed)
    }
    
    def __init__(self):
        pass
    
    def find_text_instances(self, doc: fitz.Document, search_text: str) -> List[Dict[str, Any]]:
        """
        Find all instances of text in the PDF.
        
        Returns:
            List of dicts with page number and rectangles
        """
        instances = []
        
        # Clean and normalize search text
        search_text = search_text.strip()
        if len(search_text) < 10:  # Too short to search reliably
            return instances
        
        # Search in each page
        for page_num, page in enumerate(doc):
            # Search for text (case-insensitive)
            text_instances = page.search_for(search_text)
            
            if text_instances:
                for rect in text_instances:
                    instances.append({
                        "page": page_num,
                        "rect": rect
                    })
        
        return instances
    
    def add_highlight_annotation(
        self,
        page: fitz.Page,
        rect: fitz.Rect,
        color: Tuple[float, float, float],
        point_id: str,
        quote: str,
        advice: str
    ):
        """
        Add a highlight annotation with clickable functionality.
        
        Args:
            page: PDF page object
            rect: Rectangle to highlight
            color: RGB color tuple (0-1 range)
            point_id: Unique ID for this review point
            quote: The quoted text
            advice: The advice/finding
        """
        # Add highlight
        highlight = page.add_highlight_annot(rect)
        highlight.set_colors(stroke=color)
        highlight.set_opacity(0.3)
        
        # Add popup note with advice
        info_text = f"Finding ID: {point_id}\n\nQuote:\n{quote}\n\nAdvice:\n{advice}"
        highlight.set_info(
            title=f"Review Point #{point_id}",
            content=info_text
        )
        
        # Update appearance
        highlight.update()
    
    def annotate_pdf(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        review_points: List[ReviewPoint]
    ) -> Dict[str, Any]:
        """
        Create an annotated PDF with highlighted quotes.
        
        Args:
            input_pdf_path: Path to original PDF
            output_pdf_path: Path to save annotated PDF
            review_points: List of review points with quotes
        
        Returns:
            Dict with annotation statistics
        """
        try:
            # Open PDF
            doc = fitz.open(input_pdf_path)
            
            highlights_added = 0
            points_with_highlights = []
            points_without_highlights = []
            
            # Process each review point that has a quote
            for idx, point in enumerate(review_points):
                if not point.quote or point.category == ReviewCategory.MISSING:
                    # MISSING points don't have quotes in the document
                    continue
                
                point_id = f"{point.category.value}_{idx}"
                
                # Find text in PDF
                instances = self.find_text_instances(doc, point.quote)
                
                if instances:
                    # Highlight all instances (usually just one)
                    color = self.COLORS.get(point.category, (0.5, 0.5, 0.5))
                    
                    for instance in instances:
                        page = doc[instance["page"]]
                        
                        self.add_highlight_annotation(
                            page=page,
                            rect=instance["rect"],
                            color=color,
                            point_id=point_id,
                            quote=point.quote,
                            advice=point.advice
                        )
                        
                        highlights_added += 1
                    
                    points_with_highlights.append({
                        "point_id": point_id,
                        "category": point.category.value,
                        "instances": len(instances)
                    })
                else:
                    # Quote not found (might be paraphrased or OCR error)
                    points_without_highlights.append({
                        "point_id": point_id,
                        "category": point.category.value,
                        "quote": point.quote[:100] + "..."
                    })
                    logger.warning(f"Could not find quote in PDF: {point.quote[:50]}...")
            
            # Save annotated PDF
            doc.save(output_pdf_path, garbage=4, deflate=True)
            doc.close()
            
            logger.info(
                f"Annotated PDF created: {highlights_added} highlights added "
                f"({len(points_with_highlights)} points highlighted)"
            )
            
            return {
                "highlights_added": highlights_added,
                "points_highlighted": len(points_with_highlights),
                "points_not_found": len(points_without_highlights),
                "highlight_details": points_with_highlights,
                "not_found_details": points_without_highlights
            }
            
        except Exception as e:
            logger.error(f"PDF annotation failed: {e}")
            raise
    
    def create_annotation_map(self, review_points: List[ReviewPoint]) -> Dict[str, Dict[str, Any]]:
        """
        Create a map of point IDs to review point data for frontend use.
        
        Returns:
            Dict mapping point_id to point data
        """
        annotation_map = {}
        
        for idx, point in enumerate(review_points):
            if point.quote:  # Only points with quotes get IDs
                point_id = f"{point.category.value}_{idx}"
                annotation_map[point_id] = {
                    "category": point.category.value,
                    "quote": point.quote,
                    "advice": point.advice,
                    "agent_source": point.agent_source,
                    "confidence": point.confidence,
                    "legal_reference": point.legal_reference
                }
        
        return annotation_map


# Global instance
pdf_annotator = PDFAnnotator()
