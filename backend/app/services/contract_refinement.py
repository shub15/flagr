"""
Contract Refinement Service - Generates improved contracts based on review findings.
Uses LLM to apply all recommendations and create a better version.
"""

import logging
from typing import List
from app.models.schemas import ReviewPoint, ReviewCategory
from app.models.database import ContractReview
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ContractRefinementService:
    """Generates refined contracts by applying all review recommendations."""
    
    def __init__(self):
        self.llm_service = llm_service
    
    async def refine_contract(
        self,
        original_contract: str,
        critical_points: List[ReviewPoint],
        missing_points: List[ReviewPoint],
        negotiable_points: List[ReviewPoint],
        safety_score: int,
        refinement_mode: str = "balanced"
    ) -> str:
        """
        Generate a refined contract by applying all recommendations.
        
        Returns an improved contract with:
        - Critical issues fixed
        - Missing clauses added
        - Negotiable points improved
        """
        
        # Build recommendations summary
        critical_fixes = "\n".join([f"- FIX: {p.advice}" for p in critical_points[:10]])
        missing_clauses = "\n".join([f"- ADD: {p.advice}" for p in missing_points[:10]])
        improvements = "\n".join([f"- IMPROVE: {p.advice}" for p in negotiable_points[:8]])
        
        # Mode-specific instructions
        if refinement_mode == "unilateral":
            mode_instruction = """
REFINEMENT MODE: UNILATERAL (Employee-Favoring)
- Maximize employee protections and benefits
- Add strong termination safeguards (notice periods, severance)
- Include comprehensive leave policies
- Enforce strict non-compete limits
- Add dispute resolution favorable to employee
- Strengthen intellectual property rights for employee
- Include benefits and compensation protections
"""
        else:  # balanced
            mode_instruction = """
REFINEMENT MODE: BALANCED (Fair to Both Parties)
- Create fair terms for both employer and employee
- Balance flexibility with security
- Reasonable notice periods and termination clauses
- Standard industry practices for leave and benefits
- Mutually reasonable non-compete and IP clauses
- Fair dispute resolution mechanisms
"""
        
        prompt = f"""You are a legal expert tasked with refining an employment contract.

{mode_instruction}

ORIGINAL CONTRACT:
{original_contract}

CRITICAL ISSUES TO FIX ({len(critical_points)} total):
{critical_fixes if critical_fixes else "None"}

MISSING CLAUSES TO ADD ({len(missing_points)} total):
{missing_clauses if missing_clauses else "None"}

NEGOTIABLE IMPROVEMENTS ({len(negotiable_points)} total):
{improvements if improvements else "None"}

TASK:
Generate an improved version of this contract that:
1. Fixes all critical issues according to the refinement mode
2. Adds all missing clauses with appropriate terms
3. Implements negotiable improvements based on the mode
4. Maintains the original structure and professional tone
5. Keeps all good existing clauses
6. Uses proper legal formatting

IMPORTANT:
- Output ONLY the refined contract text
- Do NOT include explanations or commentary
- Maintain professional legal language
- Keep the contract concise and clear
- Add section headings where appropriate
- Apply the {refinement_mode.upper()} mode principles throughout

REFINED CONTRACT:"""
        
        try:
            # Use Gemini for contract generation
            result = await self.llm_service.gemini_referee.generate(
                prompt=prompt,
                system_prompt="You are a legal contract specialist. Generate improved contracts that protect employee rights while maintaining professionalism."
            )
            
            if result["success"]:
                refined_contract = result["content"].strip()
                
                # Clean up any markdown or extra formatting
                if refined_contract.startswith("```"):
                    lines = refined_contract.split("\n")
                    refined_contract = "\n".join(lines[1:-1]) if len(lines) > 2 else refined_contract
                
                logger.info(f"✅ Generated refined contract ({len(refined_contract)} chars)")
                return refined_contract
            else:
                logger.error("LLM failed to generate refined contract")
                return self._generate_fallback_refined_contract(
                    original_contract,
                    critical_points,
                    missing_points,
                    negotiable_points
                )
                
        except Exception as e:
            logger.error(f"Contract refinement failed: {e}")
            return self._generate_fallback_refined_contract(
                original_contract,
                critical_points,
                missing_points,
                negotiable_points
            )
    
    def _generate_fallback_refined_contract(
        self,
        original_contract: str,
        critical_points: List[ReviewPoint],
        missing_points: List[ReviewPoint],
        negotiable_points: List[ReviewPoint]
    ) -> str:
        """Fallback: Append recommendations to original contract if LLM fails."""
        
        refined = f"{original_contract}\n\n"
        refined += "=" * 80 + "\n"
        refined += "RECOMMENDED IMPROVEMENTS TO THIS CONTRACT\n"
        refined += "=" * 80 + "\n\n"
        
        if critical_points:
            refined += "CRITICAL ISSUES TO ADDRESS:\n"
            for i, point in enumerate(critical_points[:10], 1):
                refined += f"{i}. {point.advice}\n"
            refined += "\n"
        
        if missing_points:
            refined += "MISSING CLAUSES TO ADD:\n"
            for i, point in enumerate(missing_points[:10], 1):
                refined += f"{i}. {point.advice}\n"
            refined += "\n"
        
        if negotiable_points:
            refined += "SUGGESTED IMPROVEMENTS:\n"
            for i, point in enumerate(negotiable_points[:8], 1):
                refined += f"{i}. {point.advice}\n"
            refined += "\n"
        
        return refined


# Global instance
contract_refinement_service = ContractRefinementService()
