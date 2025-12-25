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
    
    async def generate_clause_comparisons(
        self,
        original_contract: str,
        critical_points: List[ReviewPoint],
        missing_points: List[ReviewPoint],
        negotiable_points: List[ReviewPoint],
        refinement_mode: str = "balanced"
    ) -> List[dict]:
        """
        Generate clause-by-clause comparison for interactive refinement.
        
        Returns list of original vs improved clauses with reasoning.
        Each item contains: change_id, category, original, improved, reasoning.
        """
        import uuid
        
        comparisons = []
        
        # Process critical points - must fix
        for point in critical_points:
            change_id = f"change_{str(uuid.uuid4())[:8]}"
            comparisons.append({
                "change_id": change_id,
                "category": "CRITICAL",
                "original_clause": point.quote if point.quote else None,
                "improved_clause": await self._generate_improvement(point, original_contract, "CRITICAL", refinement_mode),
                "reasoning": point.advice,
                "affected_issue": point.advice[:100]
            })
        
        # Process missing points - add new clauses
        for point in missing_points:
            change_id = f"change_{str(uuid.uuid4())[:8]}"
            comparisons.append({
                "change_id": change_id,
                "category": "MISSING",
                "original_clause": None,  # Missing clause
                "improved_clause": await self._generate_improvement(point, original_contract, "MISSING", refinement_mode),
                "reasoning": point.advice,
                "affected_issue": point.advice[:100]
            })
        
        # Process negotiable points - suggested improvements
        for point in negotiable_points[:10]:  # Limit to avoid overwhelming
            change_id = f"change_{str(uuid.uuid4())[:8]}"
            comparisons.append({
                "change_id": change_id,
                "category": "NEGOTIABLE",
                "original_clause": point.quote if point.quote else None,
                "improved_clause": await self._generate_improvement(point, original_contract, "NEGOTIABLE", refinement_mode),
                "reasoning": point.advice,
                "affected_issue": point.advice[:100]
            })
        
        logger.info(f"Generated {len(comparisons)} clause comparisons")
        return comparisons
    
    async def _generate_improvement(self, point: ReviewPoint, original_contract: str, category: str, mode: str) -> str:
        """Generate improved clause text for a specific issue."""
        prompt = f"""Given this issue in an employment contract:

ISSUE TYPE: {category}
PROBLEM: {point.advice}
ORIGINAL CLAUSE: {point.quote if point.quote else "(Missing from contract)"}

Generate a brief, improved clause (2-3 sentences max) that addresses this issue.
Mode: {mode}

IMPROVED CLAUSE:"""
        
        try:
            result = await self.llm_service.gemini_referee.generate(prompt=prompt)
            if result["success"]:
                return result["content"].strip()
        except:
            pass
        
        # Fallback: use the advice as the improvement
        return point.advice
    
    async def apply_selected_changes(
        self,
        original_contract: str,
        all_comparisons: List[dict],
        accepted_change_ids: List[str]
    ) -> str:
        """
        Apply only user-accepted changes to generate customized refined contract.
        """
        # Filter to accepted changes only
        accepted_changes = [c for c in all_comparisons if c["change_id"] in accepted_change_ids]
        
        if not accepted_changes:
            return original_contract
        
        # Build summary of accepted changes
        critical = [c for c in accepted_changes if c["category"] == "CRITICAL"]
        missing = [c for c in accepted_changes if c["category"] == "MISSING"]
        negotiable = [c for c in accepted_changes if c["category"] == "NEGOTIABLE"]
        
        critical_text = "\n".join([f"- {c['improved_clause']}" for c in critical])
        missing_text = "\n".join([f"- {c['improved_clause']}" for c in missing])
        negotiable_text = "\n".join([f"- {c['improved_clause']}" for c in negotiable])
        
        prompt = f"""You are refining an employment contract with ONLY the changes the user accepted.

ORIGINAL CONTRACT:
{original_contract}

USER-ACCEPTED CRITICAL FIXES ({len(critical)}):
{critical_text if critical_text else "None"}

USER-ACCEPTED MISSING CLAUSES ({len(missing)}):
{missing_text if missing_text else "None"}

USER-ACCEPTED IMPROVEMENTS ({len(negotiable)}):
{negotiable_text if negotiable_text else "None"}

TASK: Generate a refined contract that:
1. Applies ONLY the user-accepted changes above
2. Keeps everything else from the original contract unchanged
3. Maintains professional legal formatting
4. Integrates changes naturally into the contract structure

Output ONLY the refined contract text, no explanations.

REFINED CONTRACT:"""
        
        try:
            result = await self.llm_service.gemini_referee.generate(prompt=prompt)
            if result["success"]:
                refined = result["content"].strip()
                if refined.startswith("```"):
                    lines = refined.split("\n")
                    refined = "\n".join(lines[1:-1]) if len(lines) > 2 else refined
                logger.info(f"Applied {len(accepted_changes)} user-accepted changes")
                return refined
        except Exception as e:
            logger.error(f"Failed to apply changes: {e}")
        
        # Fallback: append changes to original
        return original_contract + "\n\n=== ACCEPTED IMPROVEMENTS ===\n" + critical_text + missing_text + negotiable_text


# Global instance
contract_refinement_service = ContractRefinementService()
