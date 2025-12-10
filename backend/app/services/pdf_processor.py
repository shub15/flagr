"""
PDF processing pipeline for extracting and chunking legal documents.
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
import PyPDF2
import pdfplumber
from app.vectordb.embeddings import chunk_text
from app.config import settings

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processes PDF files for vectorization."""
    
    def __init__(self):
        self.chunk_size = settings.rag_chunk_size
        self.chunk_overlap = settings.rag_chunk_overlap
    
    def extract_text_with_pages_pypdf2(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF with page numbers using PyPDF2."""
        try:
            pages = []
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()
                    if text.strip():
                        pages.append({
                            "page": page_num,
                            "text": text,
                            "total_pages": len(reader.pages)
                        })
            return pages
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed for {pdf_path}: {e}")
            return []
    
    def extract_text_with_pages_pdfplumber(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF with page numbers using pdfplumber (more accurate)."""
        try:
            pages = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        pages.append({
                            "page": page_num,
                            "text": page_text,
                            "total_pages": len(pdf.pages)
                        })
            return pages
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for {pdf_path}: {e}")
            return []
    
    def extract_text_with_pages(self, pdf_path: str, method: str = "pdfplumber") -> List[Dict[str, Any]]:
        """
        Extract text from PDF with page tracking.
        
        Args:
            pdf_path: Path to PDF file
            method: Extraction method ("pdfplumber" or "pypdf2")
        
        Returns:
            List of dicts with page, text, total_pages
        """
        if method == "pdfplumber":
            pages = self.extract_text_with_pages_pdfplumber(pdf_path)
            if not pages:
                logger.info("pdfplumber failed, trying PyPDF2")
                pages = self.extract_text_with_pages_pypdf2(pdf_path)
        else:
            pages = self.extract_text_with_pages_pypdf2(pdf_path)
        
        total_chars = sum(len(p["text"]) for p in pages)
        logger.info(f"Extracted {total_chars} characters from {len(pages)} pages in {pdf_path}")
        return pages
    
    def process_pdf(self, pdf_path: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Process a PDF file into chunks ready for vectorization with page tracking.
        
        Args:
            pdf_path: Path to PDF file
            metadata: Additional metadata to attach to chunks
        
        Returns:
            List of document chunks with metadata including page numbers
        """
        # Extract text with page information
        pages = self.extract_text_with_pages(pdf_path)
        
        if not pages:
            logger.warning(f"No text extracted from {pdf_path}")
            return []
        
        file_name = Path(pdf_path).name
        documents = []
        chunk_id = 0
        
        # Process each page
        for page_info in pages:
            page_num = page_info["page"]
            page_text = page_info["text"]
            
            # Chunk the page text
            page_chunks = chunk_text(page_text, self.chunk_size, self.chunk_overlap)
            
            for chunk in page_chunks:
                doc = {
                    "id": f"{file_name}_page{page_num}_chunk_{chunk_id}",
                    "text": chunk,
                    "metadata": {
                        "document_name": file_name,
                        "page_number": page_num,
                        "total_pages": page_info["total_pages"],
                        "chunk_id": chunk_id,
                        "source": "pdf",
                        **(metadata or {})
                    }
                }
                documents.append(doc)
                chunk_id += 1
        
        logger.info(f"Processed {pdf_path} into {len(documents)} chunks from {len(pages)} pages")
        return documents
    
    def process_directory(self, directory: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Process all PDF files in a directory.
        
        Args:
            directory: Path to directory containing PDFs
            metadata: Additional metadata for all documents
        
        Returns:
            List of all document chunks
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory}")
            return []
        
        all_documents = []
        pdf_files = list(dir_path.glob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        for pdf_file in pdf_files:
            try:
                documents = self.process_pdf(str(pdf_file), metadata)
                all_documents.extend(documents)
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
        
        logger.info(f"Processed {len(pdf_files)} PDFs into {len(all_documents)} total chunks")
        return all_documents


# Global instance
pdf_processor = PDFProcessor()
