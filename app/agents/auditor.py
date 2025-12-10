"""
The Auditor Agent - Finds GOOD points and validates compliance.
Psychology: Compliance officer, identifies strengths and legal compliance.
"""

import logging
from typing import List
from app.agents.base import BaseAgent
from app.models.schemas import ReviewPoint
from app.services.llm_service import llm_service
from app.services.council import council_aggregator
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class AuditorAgent(BaseAgent):
    """Agent focused on identifying good clauses and compliance validation."""
    
    def __init__(self):
        super().__init__("auditor")
    
    def get_system_prompt(self) -> str:
        """System prompt defining the Auditor's psychology."""
        return """You are a COMPLIANCE AUDITOR who identifies GOOD points and validates legal compliance in contracts.

Your mission: Recognize employee-friendly clauses and confirm legal compliance.

Psychology: You focus on what's working well. You validate that the contract follows Indian Labour Law.

Focus areas:
- Employee-friendly clauses (good notice period, fair compensation, benefits)
- Compliance with statutory requirements (PF, ESI, gratuity, minimum wage)
- Clear and fair terms
- Proper leave policies
- Reasonable working hours
- Good intellectual property terms
- Fair confidentiality scope
- Proper dispute resolution

Output in JSON format:
[
    {
        "category": "GOOD",
        "quote": "exact quote from contract showing good practice",
        "advice": "why this is good / what it protects"
    }
]

If you find no good points (rare), return empty array: []

Be balanced. Only include genuinely good clauses. Don't force positives."""
    
    def get_analysis_prompt(self, contract_text: str, legal_context: str = "") -> str:
        """Build analysis prompt with RAG context."""
        prompt = f"{legal_context}\n\n" if legal_context else ""
        prompt += f"""Analyze this contract for GOOD points and compliance validations:

CONTRACT:
{contract_text}

Identify employee-friendly clauses and legal compliance.
Output ONLY the JSON array. No other text."""
        return prompt
    
    async def analyze(self, contract_text: str, contract_type: str = "employment") -> List[ReviewPoint]:
        """Analyze contract using council of LLMs."""
        logger.info(f"Auditor analyzing {contract_type} contract")
        
        # Retrieve relevant legal context
        legal_context = rag_service.retrieve_for_clause(contract_text[:2000])
        
        # Get prompts
        system_prompt = self.get_system_prompt()
        analysis_prompt = self.get_analysis_prompt(contract_text, legal_context)
        
        # Query council
        llm_responses = await llm_service.generate_parallel(
            prompt=analysis_prompt,
            system_prompt=system_prompt
        )
        
        # Build consensus
        consensus_points = council_aggregator.build_consensus(
            llm_responses=llm_responses,
            agent_source=self.agent_name
        )
        
        logger.info(f"Auditor found {len(consensus_points)} good points via council consensus")
        return consensus_points


# Global instance
auditor_agent = AuditorAgent()
