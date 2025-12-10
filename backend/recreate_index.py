"""
Script to recreate Pinecone index with correct dimensions for Cohere embeddings.

Run this once to fix the dimension mismatch:
    python recreate_index.py

This will:
1. Delete the existing index (if any)
2. Create a new index with 1024 dimensions (for Cohere)
3. You'll need to re-upload your legal documents after this
"""

from pinecone import Pinecone, ServerlessSpec
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_index():
    """Recreate Pinecone index with correct dimensions."""
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index_name = settings.pinecone_index_name
    
    # Check existing indexes
    existing_indexes = pc.list_indexes()
    index_names = [idx.name for idx in existing_indexes]
    
    # Delete existing index if it exists
    if index_name in index_names:
        logger.info(f"⚠️  Deleting existing index: {index_name}")
        pc.delete_index(index_name)
        logger.info("✅ Old index deleted")
    
    # Create new index with 1024 dimensions (for Cohere)
    logger.info(f"Creating new index: {index_name} with 1024 dimensions")
    pc.create_index(
        name=index_name,
        dimension=1024,  # Cohere embed-english-v3.0
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=settings.pinecone_environment
        )
    )
    
    logger.info("✅ New index created successfully!")
    logger.info("📝 Next step: Re-upload your legal documents to the new index")

if __name__ == "__main__":
    try:
        recreate_index()
    except Exception as e:
        logger.error(f"❌ Failed to recreate index: {e}")
        raise
