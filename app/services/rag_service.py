"""
RAG (Retrieval Augmented Generation) service for legal context retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from app.vectordb.client import pinecone_client
from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for retrieving relevant legal context using RAG."""
    
    def __init__(self):
        self.top_k = settings.rag_top_k
        self.namespace = "labour_law"  # Default namespace for Indian Labour Law
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> List[str]:
        """
        Retrieve relevant legal context for a query.
        
        Args:
            query: Contract clause or question
            top_k: Number of results (default from settings)
            namespace: Pinecone namespace (default: labour_law)
        
        Returns:
            List of relevant legal text snippets
        """
        k = top_k or self.top_k
        ns = namespace or self.namespace
        
        try:
            results = pinecone_client.query(
                query_text=query,
                top_k=k,
                namespace=ns
            )
            
            # Extract text from results
            contexts = []
            for result in results:
                if result["score"] > 0.7:  # Only include high-confidence matches
                    text = result["text"]
                    metadata = result["metadata"]
                    
                    # Format with metadata
                    context = f"[{metadata.get('document_name', 'Unknown')}] {text}"
                    contexts.append(context)
            
            logger.info(f"Retrieved {len(contexts)} relevant contexts for query")
            return contexts
        except Exception as e:
            logger.error(f"Failed to retrieve RAG context: {e}")
            return []
    
    def retrieve_for_clause(self, clause: str) -> str:
        """
        Retrieve and format legal context for a specific contract clause.
        
        Args:
            clause: Contract clause text
        
        Returns:
            Formatted context string for injection into LLM prompt
        """
        contexts = self.retrieve(clause)
        
        if not contexts:
            return "No relevant legal context found."
        
        # Format for prompt injection
        formatted = "Relevant Indian Labour Law:\n\n"
        for idx, context in enumerate(contexts, 1):
            formatted += f"{idx}. {context}\n\n"
        
        return formatted.strip()
    
    def retrieve_for_contract(self, contract_text: str) -> Dict[str, List[str]]:
        """
        Retrieve legal context for entire contract (by section).
        
        Args:
            contract_text: Full contract text
        
        Returns:
            Dictionary mapping contract sections to relevant laws
        """
        # Simple section splitting (could be improved with NLP)
        sections = contract_text.split('\n\n')
        
        contract_contexts = {}
        for idx, section in enumerate(sections[:10]):  # Limit to first 10 sections
            if len(section.strip()) < 50:  # Skip short sections
                continue
            
            contexts = self.retrieve(section, top_k=2)
            if contexts:
                contract_contexts[f"section_{idx}"] = contexts
        
        logger.info(f"Retrieved contexts for {len(contract_contexts)} contract sections")
        return contract_contexts
    
    def format_context_for_agent(self, contexts: List[str]) -> str:
        """
        Format retrieved contexts for agent prompt injection.
        
        Args:
            contexts: List of retrieved legal texts
        
        Returns:
            Formatted string for LLM prompt
        """
        if not contexts:
            return ""
        
        formatted = "Given the following relevant Indian Labour Law provisions:\n\n"
        for idx, context in enumerate(contexts, 1):
            formatted += f"{idx}. {context}\n"
        
        formatted += "\nPlease analyze the contract clause considering these legal requirements.\n"
        return formatted


# Global instance
rag_service = RAGService()
