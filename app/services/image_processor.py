"""
Image processing with Gemini Vision API for contract OCR.
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
from PIL import Image
import google.generativeai as genai
from app.vectordb.embeddings import chunk_text
from app.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processes images using Gemini Vision API for text extraction."""
    
    def __init__(self):
        self.chunk_size = settings.rag_chunk_size
        self.chunk_overlap = settings.rag_chunk_overlap
        
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key)
        
        # Use Gemini 1.5 Flash for vision (faster and cheaper than Pro)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info("ImageProcessor initialized with Gemini Vision API")
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from image using Gemini Vision API.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Extracted text
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Prepare prompt for OCR
            prompt = """Extract ALL text from this image. This is a legal document (contract, policy, or agreement).

Instructions:
1. Extract every word, clause, and section exactly as written
2. Preserve the structure (headings, paragraphs, numbered lists)
3. Include all fine print and footnotes
4. Do not summarize or paraphrase
5. Output only the extracted text, no explanations

Text:"""
            
            # Generate content with vision
            response = self.model.generate_content([prompt, image])
            
            # Extract text from response
            text = response.text.strip()
            
            logger.info(f"Gemini Vision extracted {len(text)} characters from {image_path}")
            return text
            
        except Exception as e:
            logger.error(f"Gemini Vision OCR failed for {image_path}: {e}")
            return ""
    
    def process_image(self, image_path: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Process an image file into chunks ready for vectorization.
        
        Args:
            image_path: Path to image file
            metadata: Additional metadata to attach to chunks
        
        Returns:
            List of document chunks with metadata
        """
        # Extract text via Gemini Vision
        text = self.extract_text_from_image(image_path)
        
        if not text:
            logger.warning(f"No text extracted from {image_path}")
            return []
        
        # Chunk the text
        chunks = chunk_text(text, self.chunk_size, self.chunk_overlap)
        
        file_name = Path(image_path).name
        documents = []
        
        for idx, chunk in enumerate(chunks):
            doc = {
                "id": f"{file_name}_chunk_{idx}",
                "text": chunk,
                "metadata": {
                    "document_name": file_name,
                    "chunk_id": idx,
                    "total_chunks": len(chunks),
                    "source": "gemini_vision_ocr",
                    **(metadata or {})
                }
            }
            documents.append(doc)
        
        logger.info(f"Processed {image_path} into {len(documents)} chunks via Gemini Vision")
        return documents
    
    def process_directory(
        self,
        directory: str,
        metadata: Dict[str, Any] = None,
        extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process all image files in a directory.
        
        Args:
            directory: Path to directory containing images
            metadata: Additional metadata for all documents
            extensions: Image extensions to process (default: png, jpg, jpeg, tif, tiff)
        
        Returns:
            List of all document chunks
        """
        if extensions is None:
            extensions = ['png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp', 'webp']
        
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory}")
            return []
        
        all_documents = []
        image_files = []
        
        for ext in extensions:
            image_files.extend(dir_path.glob(f"*.{ext}"))
            image_files.extend(dir_path.glob(f"*.{ext.upper()}"))
        
        logger.info(f"Found {len(image_files)} image files in {directory}")
        
        for image_file in image_files:
            try:
                documents = self.process_image(str(image_file), metadata)
                all_documents.extend(documents)
            except Exception as e:
                logger.error(f"Failed to process {image_file}: {e}")
        
        logger.info(f"Processed {len(image_files)} images into {len(all_documents)} total chunks via Gemini Vision")
        return all_documents


# Global instance
image_processor = ImageProcessor()
