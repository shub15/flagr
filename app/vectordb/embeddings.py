"""
Embedding generation utilities for vector database.
"""

import logging
from typing import List
import tiktoken
from app.vectordb.client import pinecone_client

logger = logging.getLogger(__name__)


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Failed to count tokens: {e}, using char count / 4")
        return len(text) // 4


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """
    Chunk text into smaller segments with overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Target size in tokens
        chunk_overlap: Overlap between chunks in tokens
    
    Returns:
        List of text chunks
    """
    # Simple sentence-based chunking
    sentences = text.replace('\n', ' ').split('. ')
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_tokens = count_tokens(sentence)
        
        if current_tokens + sentence_tokens > chunk_size and current_chunk:
            # Save current chunk
            chunks.append('. '.join(current_chunk) + '.')
            
            # Start new chunk with overlap
            overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
            current_chunk = overlap_sentences + [sentence]
            current_tokens = sum(count_tokens(s) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
    
    # Add remaining chunk
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    logger.info(f"Chunked text into {len(chunks)} segments")
    return chunks


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts."""
    embeddings = []
    for text in texts:
        embedding = pinecone_client.generate_embedding(text)
        embeddings.append(embedding)
    return embeddings
