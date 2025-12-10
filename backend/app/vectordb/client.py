"""
Pinecone vector database client for legal document embeddings.
"""

import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import openai
import cohere
from app.config import settings

logger = logging.getLogger(__name__)


class PineconeClient:
    """Client for interacting with Pinecone vector database."""
    
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        
        # Initialize embedding clients
        self.use_cohere = settings.use_cohere_embeddings or not settings.openai_api_key
        
        if self.use_cohere:
            if not settings.cohere_api_key:
                raise ValueError("Cohere API key required when use_cohere_embeddings=True")
            self.cohere_client = cohere.Client(settings.cohere_api_key)
            self.embedding_dimension = 1024  # Cohere embed-english-v3.0
            logger.info("Using Cohere for embeddings (FREE tier available)")
        else:
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            self.embedding_dimension = 1536  # OpenAI text-embedding-3-small
            logger.info("Using OpenAI for embeddings")
        
        self._index = None
    
    def _get_index(self):
        """Get or create Pinecone index with correct dimensions."""
        if self._index is not None:
            return self._index
        
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
            
            if self.index_name not in index_names:
                logger.info(
                    f"Creating Pinecone index: {self.index_name} "
                    f"(dimension: {self.embedding_dimension})"
                )
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.pinecone_environment
                    )
                )
                logger.info(f"✅ Index {self.index_name} created successfully")
            else:
                # Check if existing index has correct dimensions
                index_desc = self.pc.describe_index(self.index_name)
                existing_dim = index_desc.dimension
                
                if existing_dim != self.embedding_dimension:
                    logger.error(
                        f"⚠️  DIMENSION MISMATCH: Index has {existing_dim} dimensions, "
                        f"but {self.embedding_dimension} expected for current embedding model.\n"
                        f"To fix: Run 'python recreate_index.py' to recreate the index."
                    )
                    raise ValueError(
                        f"Pinecone index dimension mismatch: {existing_dim} != {self.embedding_dimension}. "
                        "Run recreate_index.py to fix."
                    )
            
            self._index = self.pc.Index(self.index_name)
            return self._index
        except Exception as e:
            logger.error(f"Failed to get/create Pinecone index: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using configured provider."""
        try:
            if self.use_cohere:
                # Cohere embeddings (FREE tier: 1000 embeds/month, then pay-as-you-go)
                response = self.cohere_client.embed(
                    texts=[text],
                    model="embed-english-v3.0",
                    input_type="search_document"  # For indexing documents
                )
                return response.embeddings[0]
            else:
                # OpenAI embeddings (requires credits)
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
        except Exception as e:
            # Try fallback to Cohere if OpenAI fails
            if not self.use_cohere and settings.cohere_api_key:
                logger.warning(f"OpenAI embedding failed, trying Cohere fallback: {e}")
                try:
                    if not hasattr(self, 'cohere_client'):
                        self.cohere_client = cohere.Client(settings.cohere_api_key)
                    response = self.cohere_client.embed(
                        texts=[text],
                        model="embed-english-v3.0",
                        input_type="search_document"
                    )
                    logger.info("✅ Cohere fallback successful")
                    return response.embeddings[0]
                except Exception as cohere_error:
                    logger.error(f"Cohere fallback also failed: {cohere_error}")
            
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def upsert_documents(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = "default",
        batch_size: int = 20,  # Smaller batches to avoid rate limits
        delay_between_batches: float = 1.0  # 1 second delay between batches
    ) -> Dict[str, Any]:
        """
        Upsert documents to Pinecone index with rate limiting protection.
        
        Args:
            documents: List of dicts with 'id', 'text', and 'metadata'
            namespace: Pinecone namespace (e.g., 'labour_law', 'contracts')
            batch_size: Number of documents to process per batch (default: 20)
            delay_between_batches: Seconds to wait between batches (default: 1.0)
        
        Returns:
            Status dict with upsert count
        """
        import time
        import asyncio
        
        try:
            index = self._get_index()
            total_upserted = 0
            total_docs = len(documents)
            
            logger.info(f"Starting embedding for {total_docs} documents in batches of {batch_size}")
            
            # Process documents in batches
            for batch_num, i in enumerate(range(0, total_docs, batch_size)):
                batch_docs = documents[i:i + batch_size]
                vectors = []
                
                # Generate embeddings for batch with retry logic
                for doc_idx, doc in enumerate(batch_docs):
                    retry_count = 0
                    max_retries = 3
                    
                    while retry_count < max_retries:
                        try:
                            embedding = self.generate_embedding(doc["text"])
                            vectors.append({
                                "id": doc["id"],
                                "values": embedding,
                                "metadata": {
                                    **doc.get("metadata", {}),
                                    "text": doc["text"][:1000]  # Store first 1000 chars
                                }
                            })
                            break  # Success, exit retry loop
                        except Exception as e:
                            error_str = str(e).lower()
                            if "rate" in error_str or "429" in error_str or "quota" in error_str:
                                retry_count += 1
                                if retry_count < max_retries:
                                    wait_time = 2 ** retry_count  # Exponential backoff
                                    logger.warning(
                                        f"Rate limit hit on doc {i + doc_idx + 1}/{total_docs}. "
                                        f"Retrying in {wait_time}s... (attempt {retry_count}/{max_retries})"
                                    )
                                    time.sleep(wait_time)
                                else:
                                    logger.error(f"Failed to embed doc after {max_retries} retries: {e}")
                                    raise
                            else:
                                logger.error(f"Embedding error: {e}")
                                raise
                
                # Upsert batch to Pinecone
                if vectors:
                    try:
                        result = index.upsert(vectors=vectors, namespace=namespace)
                        total_upserted += result.upserted_count
                        logger.info(
                            f"Batch {batch_num + 1}/{(total_docs + batch_size - 1) // batch_size}: "
                            f"Upserted {result.upserted_count} vectors "
                            f"({total_upserted}/{total_docs} total)"
                        )
                    except Exception as e:
                        logger.error(f"Failed to upsert batch {batch_num + 1}: {e}")
                        raise
                
                # Delay between batches to avoid rate limits (except for last batch)
                if i + batch_size < total_docs:
                    logger.info(f"Waiting {delay_between_batches}s before next batch...")
                    time.sleep(delay_between_batches)
            
            logger.info(f"✅ Successfully upserted {total_upserted} vectors to namespace '{namespace}'")
            return {"upserted_count": total_upserted, "namespace": namespace}
        except Exception as e:
            logger.error(f"Failed to upsert documents: {e}")
            raise
    
    def query(
        self,
        query_text: str,
        top_k: int = 3,
        namespace: str = "default",
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone index for similar documents.
        
        Args:
            query_text: Text to search for
            top_k: Number of results to return
            namespace: Pinecone namespace to search
            filter_metadata: Optional metadata filters
        
        Returns:
            List of matching documents with scores
        """
        try:
            index = self._get_index()
            query_embedding = self.generate_embedding(query_text)
            
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                filter=filter_metadata,
                include_metadata=True
            )
            
            documents = []
            for match in results.matches:
                documents.append({
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "metadata": match.metadata
                })
            
            logger.info(f"Found {len(documents)} matches for query in namespace '{namespace}'")
            return documents
        except Exception as e:
            logger.error(f"Failed to query Pinecone: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            index = self._get_index()
            stats = index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}
    
    def delete_namespace(self, namespace: str) -> bool:
        """Delete all vectors in a namespace."""
        try:
            index = self._get_index()
            index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted all vectors in namespace '{namespace}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete namespace: {e}")
            return False


# Global instance
pinecone_client = PineconeClient()
