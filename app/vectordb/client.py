"""
Pinecone vector database client for legal document embeddings.
"""

import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import openai
from app.config import settings

logger = logging.getLogger(__name__)


class PineconeClient:
    """Client for interacting with Pinecone vector database."""
    
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.embedding_dimension = 1536  # OpenAI text-embedding-3-small
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self._index = None
    
    def _get_index(self):
        """Get or create Pinecone index."""
        if self._index is not None:
            return self._index
        
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
            
            if self.index_name not in index_names:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.pinecone_environment
                    )
                )
                logger.info(f"Index {self.index_name} created successfully")
            
            self._index = self.pc.Index(self.index_name)
            return self._index
        except Exception as e:
            logger.error(f"Failed to get/create Pinecone index: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def upsert_documents(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Upsert documents to Pinecone index.
        
        Args:
            documents: List of dicts with 'id', 'text', and 'metadata'
            namespace: Pinecone namespace (e.g., 'labour_law', 'contracts')
        
        Returns:
            Status dict with upsert count
        """
        try:
            index = self._get_index()
            vectors = []
            
            for doc in documents:
                embedding = self.generate_embedding(doc["text"])
                vectors.append({
                    "id": doc["id"],
                    "values": embedding,
                    "metadata": {
                        **doc.get("metadata", {}),
                        "text": doc["text"][:1000]  # Store first 1000 chars in metadata
                    }
                })
            
            # Upsert in batches of 100
            batch_size = 100
            total_upserted = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                result = index.upsert(vectors=batch, namespace=namespace)
                total_upserted += result.upserted_count
            
            logger.info(f"Upserted {total_upserted} vectors to namespace '{namespace}'")
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
