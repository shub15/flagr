"""
DOCX document processing for contract analysis.
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
from docx import Document
from app.vectordb.embeddings import chunk_text
from app.config import settings

logger = logging.getLogger(__name__)


class DOCXProcessor:
    """Processes DOCX files for vectorization."""
    
    def __init__(self):
        self.chunk_size = settings.rag_chunk_size
        self.chunk_overlap = settings.rag_chunk_overlap
    
    def extract_text_from_docx(self, docx_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from DOCX with paragraph tracking.
        
        Returns:
            List of dicts with paragraph_num, text, is_heading
        """
        try:
            doc = Document(docx_path)
            paragraphs = []
            
            for para_num, paragraph in enumerate(doc.paragraphs, start=1):
                text = paragraph.text.strip()
                if text:
                    # Detect headings based on style
                    is_heading = paragraph.style.name.startswith('Heading')
                    
                    paragraphs.append({
                        "paragraph_num": para_num,
                        "text": text,
                        "is_heading": is_heading,
                        "style": paragraph.style.name
                    })
            
            logger.info(f"Extracted {len(paragraphs)} paragraphs from {docx_path}")
            return paragraphs
            
        except Exception as e:
            logger.error(f"DOCX extraction failed for {docx_path}: {e}")
            return []
    
    def process_docx(self, docx_path: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Process a DOCX file into chunks ready for vectorization.
        
        Args:
            docx_path: Path to DOCX file
            metadata: Additional metadata to attach to chunks
        
        Returns:
            List of document chunks with metadata
        """
        # Extract paragraphs
        paragraphs = self.extract_text_from_docx(docx_path)
        
        if not paragraphs:
            logger.warning(f"No text extracted from {docx_path}")
            return []
        
        # Combine paragraph texts while tracking headings
        full_text = "\n\n".join(p["text"] for p in paragraphs)
        
        # Extract headings for context
        headings = [p["text"] for p in paragraphs if p["is_heading"]]
        
        # Chunk the text
        chunks = chunk_text(full_text, self.chunk_size, self.chunk_overlap)
        
        file_name = Path(docx_path).name
        documents = []
        
        for idx, chunk in enumerate(chunks):
            doc = {
                "id": f"{file_name}_chunk_{idx}",
                "text": chunk,
                "metadata": {
                    "document_name": file_name,
                    "chunk_id": idx,
                    "total_chunks": len(chunks),
                    "source": "docx",
                    "headings": ", ".join(headings[:5]) if headings else "",  # First 5 headings for context
                    **(metadata or {})
                }
            }
            documents.append(doc)
        
        logger.info(f"Processed {docx_path} into {len(documents)} chunks ({len(headings)} headings detected)")
        return documents
    
    def process_directory(self, directory: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Process all DOCX files in a directory.
        
        Args:
            directory: Path to directory containing DOCX files
            metadata: Additional metadata for all documents
        
        Returns:
            List of all document chunks
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory}")
            return []
        
        all_documents = []
        docx_files = list(dir_path.glob("*.docx"))
        
        logger.info(f"Found {len(docx_files)} DOCX files in {directory}")
        
        for docx_file in docx_files:
            # Skip temporary Word files
            if docx_file.name.startswith('~$'):
                continue
                
            try:
                documents = self.process_docx(str(docx_file), metadata)
                all_documents.extend(documents)
            except Exception as e:
                logger.error(f"Failed to process {docx_file}: {e}")
        
        logger.info(f"Processed {len(docx_files)} DOCX files into {len(all_documents)} total chunks")
        return all_documents


# Global instance
docx_processor = DOCXProcessor()
