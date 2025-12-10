"""
The Skeptic Agent - Finds CRITICAL risks in contracts.
Psychology: Paranoid, focuses on worst-case scenarios.
"""

import logging
from typing import List
from app.agents.base import BaseAgent
from app.models.schemas import ReviewPoint
from app.services.llm_service import llm_service
from app.services.council import council_aggregator
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class SkepticAgent(BaseAgent):
    """Agent focused on identifying critical risks and red flags."""
    
    def __init__(self):
        super().__init__("skeptic")
    
    def get_system_prompt(self) -> str:
        """System prompt defining the Skeptic's psychology."""
        return """You are a PARANOID contract lawyer who ONLY focuses on finding CRITICAL RISKS and dangerous clauses.

Your mission: Protect the employee from potentially harmful contract terms.

Psychology: You assume the worst. Every clause is suspicious until proven safe.

Focus areas:
- Termination clauses without notice
- Non-compete restrictions that limit future employment
- Intellectual property assignments beyond work scope
- Liability clauses favoring employer
- Missing employee protections required by Indian Labour Law
- Wage/payment terms below legal minimum
- Unreasonable working hours or conditions
- Confidentiality clauses that are overly broad

Output ONLY in JSON format:
[
    {
        "category": "CRITICAL",
        "quote": "exact quote from contract",
        "advice": "specific actionable advice to mitigate this risk"
    }
]

If you find no critical risks, return an empty array: []

Be specific. Quote exact problematic text. Provide concrete solutions."""
    
    def get_analysis_prompt(self, contract_text: str, legal_context: str = "") -> str:
        """Build analysis prompt with RAG context."""
        prompt = f"{legal_context}\n\n" if legal_context else ""
        prompt += f"""Analyze this contract for CRITICAL RISKS ONLY:

CONTRACT:
{contract_text}

Remember: Output ONLY the JSON array of critical findings. No other text."""
        return prompt
    
    async def analyze(self, contract_text: str, contract_type: str = "employment") -> List[ReviewPoint]:
        """Analyze contract using council of LLMs."""
        logger.info(f"Skeptic analyzing {contract_type} contract ({len(contract_text)} chars)")
        
        # Retrieve relevant legal context
        legal_context = rag_service.retrieve_for_clause(contract_text[:2000])  # First 2000 chars
        
        # Get system prompt and analysis prompt
        system_prompt = self.get_system_prompt()
        analysis_prompt = self.get_analysis_prompt(contract_text, legal_context)
        
        # Query council (all LLMs in parallel)
        llm_responses = await llm_service.generate_parallel(
            prompt=analysis_prompt,
            system_prompt=system_prompt
        )
        
        # Build consensus from council responses
        consensus_points = council_aggregator.build_consensus(
            llm_responses=llm_responses,
            agent_source=self.agent_name
        )
        
        logger.info(f"Skeptic found {len(consensus_points)} critical risks via council consensus")
        return consensus_points


# Global instance
skeptic_agent = SkepticAgent()
