"""
The Strategist Agent - Finds MISSING and NEGOTIABLE points.
Psychology: Negotiator, compares against best practices and legal requirements.
"""

import logging
from typing import List
from pathlib import Path
from app.agents.base import BaseAgent
from app.models.schemas import ReviewPoint
from app.services.llm_service import llm_service
from app.services.council import council_aggregator
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class StrategistAgent(BaseAgent):
    """Agent focused on finding missing clauses and negotiable terms."""
    
    def __init__(self):
        super().__init__("strategist")
        self.reference_playbook = self._load_playbook()
    
    def _load_playbook(self) -> str:
        """Load reference playbook for comparison."""
        playbook_path = Path("data/reference_playbooks/employee_contract.txt")
        if playbook_path.exists():
            return playbook_path.read_text(encoding="utf-8")
        else:
            logger.warning("Reference playbook not found, using default checklist")
            return """
EMPLOYEE CONTRACT CHECKLIST:
- Job title and responsibilities
- Compensation and payment schedule
- Working hours and overtime policy
- Leave policy (sick, casual, earned)
- Probation period terms
- Notice period for termination
- Benefits (health insurance, PF, gratuity)
- Equipment/work-from-home stipend
- Confidentiality terms (reasonable scope)
- Intellectual property ownership
- Non-compete (reasonable duration and geography)
- Dispute resolution mechanism
- Compliance with Indian Labour Laws
"""
    
    def get_system_prompt(self) -> str:
        """System prompt defining the Strategist's psychology."""
        return f"""You are a STRATEGIC NEGOTIATION EXPERT who reviews contracts for missing protections and weak terms that can be improved.

Your mission: Ensure the employee gets the best possible terms and all legally required protections.

Psychology: You think like a skilled negotiator. You compare what's written against industry best practices and legal requirements.

Reference Checklist (Employee Should Have):
{self.reference_playbook}

Focus areas:
1. MISSING: Essential clauses not present in contract (required by law or best practice)
2. NEGOTIABLE: Weak terms that could be improved (e.g., short notice period, low benefits)

Output in JSON format:
[
    {{
        "category": "MISSING",
        "quote": null,
        "advice": "specific clause that should be added"
    }},
    {{
        "category": "NEGOTIABLE",
        "quote": "weak clause from contract",
        "advice": "how to negotiate this better"
    }}
]

Compare the contract against BOTH:
1. The reference checklist above
2. Indian Labour Law requirements

Be practical. Focus on impactful missing items and truly negotiable points."""
    
    def get_analysis_prompt(self, contract_text: str, legal_context: str = "") -> str:
        """Build analysis prompt with RAG context."""
        prompt = f"{legal_context}\n\n" if legal_context else ""
        prompt += f"""Analyze this contract for MISSING clauses and NEGOTIABLE terms:

CONTRACT:
{contract_text}

Compare against the reference checklist and Indian Labour Law.
Output ONLY the JSON array. No other text."""
        return prompt
    
    async def analyze(self, contract_text: str, contract_type: str = "employment") -> List[ReviewPoint]:
        """Analyze contract using council of LLMs."""
        logger.info(f"Strategist analyzing {contract_type} contract")
        
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
        
        logger.info(
            f"Strategist found {len(consensus_points)} "
            f"missing/negotiable points via council consensus"
        )
        return consensus_points


# Global instance
strategist_agent = StrategistAgent()
