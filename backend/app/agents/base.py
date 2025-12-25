"""
Base agent interface for contract review agents.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.schemas import ReviewPoint


class BaseAgent(ABC):
    """Abstract base class for all review agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
    
    @abstractmethod
    async def analyze(
        self, 
        contract_text: str, 
        contract_type: str = "employment",
        context: Optional[str] = None
    ) -> tuple[List[ReviewPoint], List[dict]]:
        """
        Analyze contract and return findings + raw LLM responses.
        
        Args:
            contract_text: Full contract text
            contract_type: Type of contract (employment, freelance, etc.)
            context: Optional additional context about the contract
        
        Returns:
            Tuple of (consensus_findings, raw_llm_responses)
            - consensus_findings: List of ReviewPoint objects after deduplication
            - raw_llm_responses: List of dicts with provider, model, raw_response, etc.
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent's psychology."""
        pass
    
    @abstractmethod
    def get_analysis_prompt(
        self, 
        contract_text: str, 
        legal_context: str = "",
        user_context: Optional[str] = None
    ) -> str:
        """
        Build the analysis prompt for the contract.
        
        Args:
            contract_text: Contract to analyze
            legal_context: Retrieved legal context from RAG
            user_context: Optional user-provided context
        
        Returns:
            Formatted prompt string
        """
        pass
