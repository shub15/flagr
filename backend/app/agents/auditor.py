"""
The Auditor Agent - Finds GOOD points and validates compliance.
Psychology: Compliance officer, identifies strengths and legal compliance.
"""

import logging
from typing import List, Optional
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
- Employee-friendly clauses (generous leave, benefits, flexibility)
- Fair compensation and payment terms
- Reasonable working hours
- Good termination/notice provisions
- Strong confidentiality protections for employee
- Fair IP ownership terms
- Proper compliance with labour laws
- Dispute resolution mechanisms
- Safety and working condition protections

Output ONLY in JSON format:
[
    {
        "category": "GOOD",
        "quote": "exact quote from contract",
        "advice": "why this is beneficial for the employee"
    }
]

If you find no good points, return empty array: []

Be specific. Quote exact beneficial text. Explain the positive impact."""
    
    def get_analysis_prompt(
        self, 
        contract_text: str, 
        legal_context: str = "",
        user_context: Optional[str] = None
    ) -> str:
        """Build analysis prompt with RAG context and user context."""
        prompt = f"{legal_context}\n\n" if legal_context else ""
        
        if user_context:
            prompt += f"""ROLE CONTEXT: {user_context}

Evaluate good points in relation to this specific role and industry standards.

"""
        
        prompt += f"""Analyze this contract for GOOD points and compliance validations:

CONTRACT:
{contract_text}

Identify employee-friendly clauses and legal compliance.
Output ONLY the JSON array. No other text."""
        return prompt
    
    async def analyze(
        self, 
        contract_text: str, 
        contract_type: str = "employment",
        context: Optional[str] = None
    ) -> tuple[List[ReviewPoint], List[dict]]:
        """Analyze contract using council of LLMs."""
        logger.info(
            f"Auditor analyzing {contract_type} contract "
            f"(context: {'provided' if context else 'none'})"
        )
        
        # Retrieve relevant legal context
        legal_context = rag_service.retrieve_for_clause(contract_text[:2000])
        
        # Get prompts
        system_prompt = self.get_system_prompt()
        analysis_prompt = self.get_analysis_prompt(contract_text, legal_context, context)
        
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
        
        # Format raw responses
        raw_responses = []
        for resp in llm_responses:
            if resp.get("success"):
                raw_responses.append({
                    "provider": resp.get("provider", "unknown"),
                    "model": resp.get("model", "unknown"),
                    "raw_response": resp.get("content", ""),
                    "response_time_ms": resp.get("response_time_ms", 0)
                })
        
        logger.info(
            f"Auditor found {len(consensus_points)} good points via council consensus "
            f"({len(raw_responses)} LLM responses)"
        )
        return consensus_points, raw_responses


# Global instance
auditor_agent = AuditorAgent()
