"""
Base agent interface for contract review agents.
"""

from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import ReviewPoint


class BaseAgent(ABC):
    """Abstract base class for all review agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
    
    @abstractmethod
    async def analyze(self, contract_text: str, contract_type: str = "employment") -> List[ReviewPoint]:
        """
        Analyze contract and return findings.
        
        Args:
            contract_text: Full contract text
            contract_type: Type of contract (employment, freelance, etc.)
        
        Returns:
            List of ReviewPoint objects
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent's psychology."""
        pass
    
    @abstractmethod
    def get_analysis_prompt(self, contract_text: str, legal_context: str = "") -> str:
        """
        Build the analysis prompt for the contract.
        
        Args:
            contract_text: Contract to analyze
            legal_context: Retrieved legal context from RAG
        
        Returns:
            Formatted prompt string
        """
        pass
