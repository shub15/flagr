"""
Orchestrator service - implements fan-out/fan-in parallel execution.
Coordinates all agents to review contracts.
"""

import logging
import asyncio
from typing import List, Optional
from app.models.schemas import ContractReviewResult
from app.agents import skeptic_agent, strategist_agent, auditor_agent
from app.agents.referee import RefereeAgent
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ContractOrchestrator:
    """
    Orchestrates the parallel multi-agent contract review process.
    
    Architecture:
    - Level 1 (Fan-Out): Run 3 agents in parallel (Skeptic, Strategist, Auditor)
    - Level 2 (Within each agent): Run 3 LLMs in parallel (council)
    - Fan-In: Referee aggregates all findings with LLM-based summary
    
    Total parallelism: 9 LLM calls + 3 RAG retrievals + 1 Gemini summary
    """
    
    def __init__(self):
        self.skeptic = skeptic_agent
        self.strategist = strategist_agent
        self.auditor = auditor_agent
        # Instantiate Referee with LLM service for contextual summary generation
        self.referee = RefereeAgent(llm_service=llm_service)
    
    async def review_contract(
        self, 
        contract_text: str, 
        contract_type: str = "employment",
        context: Optional[str] = None
    ) -> ContractReviewResult:
        """
        Execute full contract review with parallel multi-agent processing.
        
        Args:
            contract_text: Full contract text
            contract_type: Type of contract
            context: Optional additional context about the contract
        
        Returns:
            ContractReviewResult with aggregated findings and safety score
        """
        logger.info(
            f"Starting contract review orchestration "
            f"(type: {contract_type}, length: {len(contract_text)} chars, "
            f"context: {'provided' if context else 'none'})"
        )
        
        # Level 1: Fan-Out - Run all agents in parallel
        logger.info("Fan-Out: Launching all agents in parallel...")
        
        agent_tasks = [
            self.skeptic.analyze(contract_text, contract_type, context),
            self.strategist.analyze(contract_text, contract_type, context),
            self.auditor.analyze(contract_text, contract_type, context)
        ]
        
        try:
            # Execute all agents in parallel
            # Each agent returns (consensus_points, raw_llm_responses)
            results = await asyncio.gather(
                *agent_tasks,
                return_exceptions=False
            )
            
            # Unpack results
            skeptic_points, skeptic_llm_responses = results[0]
            strategist_points, strategist_llm_responses = results[1]
            auditor_points, auditor_llm_responses = results[2]
            
            logger.info(
                f"Agent results: "
                f"Skeptic={len(skeptic_points)}, "
                f"Strategist={len(strategist_points)}, "
                f"Auditor={len(auditor_points)}"
            )
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise
        
        # Fan-In: Referee aggregates all findings (now async for LLM summary)
        logger.info("Fan-In: Referee aggregating all findings...")
        
        result = await self.referee.aggregate(
            skeptic_points=skeptic_points,
            strategist_points=strategist_points,
            auditor_points=auditor_points
        )
        
        # Attach LLM transparency data to result
        result.llm_transparency = {
            "skeptic": skeptic_llm_responses,
            "strategist": strategist_llm_responses,
            "auditor": auditor_llm_responses
        }
        
        logger.info(
            f"Contract review completed: "
            f"Review ID={result.review_id}, "
            f"Safety Score={result.safety_score}/100, "
            f"Total Findings={result.total_findings}"
        )
        
        return result
    
    async def health_check(self) -> dict:
        """Check if all components are operational."""
        health = {
            "orchestrator": "healthy",
            "agents": {
                "skeptic": "ready",
                "strategist": "ready",
                "auditor": "ready",
                "referee": "ready"
            }
        }
        
        # Could add actual health checks here (e.g., test LLM connectivity)
        return health


# Global instance
orchestrator = ContractOrchestrator()
