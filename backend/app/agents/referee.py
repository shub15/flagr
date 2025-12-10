"""
The Referee Agent - Aggregates, deduplicates, resolves conflicts, and scores.
Uses Gemini LLM to generate contextual executive summaries based on council findings.
"""

import logging
from typing import List, Dict
from collections import defaultdict
from app.models.schemas import ReviewPoint, ReviewCategory, ContractReviewResult
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class RefereeAgent:
    """
    Referee agent that aggregates findings from Skeptic, Strategist, and Auditor.
    Implements "Risk Trumps Benefit" conflict resolution.
    Uses LLM to generate contextual summaries.
    """
    
    def __init__(self, llm_service=None):
        self.agent_name = "referee"
        self.llm_service = llm_service
    
    def deduplicate_points(self, points: List[ReviewPoint]) -> List[ReviewPoint]:
        """
        Deduplicate similar points across agents.
        Simple implementation based on advice similarity.
        """
        if not points:
            return []
        
        unique_points = []
        seen_advice = set()
        
        for point in points:
            # Use first 100 chars of advice as deduplication key
            key = point.advice[:100].lower().strip()
            
            if key not in seen_advice:
                seen_advice.add(key)
                unique_points.append(point)
        
        logger.info(f"Deduplicated {len(points)} points to {len(unique_points)} unique points")
        return unique_points
    
    def resolve_conflicts(self, points: List[ReviewPoint]) -> List[ReviewPoint]:
        """
        Implement "Risk Trumps Benefit" conflict resolution.
        If same clause is marked as both CRITICAL and GOOD, keep as CRITICAL.
        """
        # Group by quote
        quote_groups = defaultdict(list)
        for point in points:
            if point.quote:
                # Normalize quote for grouping
                normalized_quote = point.quote[:100].lower().strip()
                quote_groups[normalized_quote].append(point)
        
        resolved_points = []
        processed_quotes = set()
        
        for point in points:
            if not point.quote:
                # No quote means it's MISSING, can't have conflict
                resolved_points.append(point)
                continue
            
            normalized_quote = point.quote[:100].lower().strip()
            
            if normalized_quote in processed_quotes:
                continue
            
            group = quote_groups[normalized_quote]
            
            if len(group) == 1:
                # No conflict
                resolved_points.append(point)
            else:
                # Check for conflicts
                categories = [p.category for p in group]
                
                # Risk Trumps Benefit logic
                if ReviewCategory.CRITICAL in categories:
                    # Keep CRITICAL, discard GOOD
                    critical_point = next(p for p in group if p.category == ReviewCategory.CRITICAL)
                    resolved_points.append(critical_point)
                    logger.info(f"Conflict resolved: Kept CRITICAL over GOOD for quote '{point.quote[:50]}...'")
                elif ReviewCategory.NEGOTIABLE in categories and ReviewCategory.GOOD in categories:
                    # Keep NEGOTIABLE, discard GOOD (improvement opportunity trumps validation)
                    negotiable_point = next(p for p in group if p.category == ReviewCategory.NEGOTIABLE)
                    resolved_points.append(negotiable_point)
                else:
                    # No semantic conflict, keep all
                    resolved_points.extend(group)
            
            processed_quotes.add(normalized_quote)
        
        return resolved_points
    
    def calculate_safety_score(
        self,
        critical_count: int,
        missing_count: int,
        negotiable_count: int,
        good_count: int
    ) -> int:
        """
        Calculate overall safety score (0-100).
        
        Algorithm:
        - Base score: 50
        - Each CRITICAL: -10 points
        - Each MISSING: -5 points
        - Each NEGOTIABLE: -2 points
        - Each GOOD: +5 points
        - Clamp to 0-100
        """
        score = 50
        score -= critical_count * 10
        score -= missing_count * 5
        score -= negotiable_count * 2
        score += good_count * 5
        
        # Clamp to valid range
        score = max(0, min(100, score))
        
        logger.info(
            f"Safety score: {score}/100 "
            f"(CRITICAL: {critical_count}, MISSING: {missing_count}, "
            f"NEGOTIABLE: {negotiable_count}, GOOD: {good_count})"
        )
        
        return score
    
    def _generate_fallback_summary(
        self,
        safety_score: int,
        critical_count: int,
        missing_count: int,
        negotiable_count: int,
        good_count: int
    ) -> tuple:
        """Fallback summary generation without LLM."""
        
        if safety_score >= 80 and critical_count == 0:
            recommendation = "SIGN"
            summary = f"Contract shows strong protections with {good_count} positive aspects and minimal concerns. Safe to proceed."
        elif safety_score >= 60 and critical_count <= 2:
            recommendation = "NEGOTIATE"
            summary = f"Contract has {critical_count} critical issues and {missing_count} missing clauses. Recommend negotiating these points before signing."
        elif critical_count >= 3:
            recommendation = "REJECT"
            summary = f"Contract presents significant risks with {critical_count} critical issues. Seek legal counsel or reject this offer."
        else:
            recommendation = "NEGOTIATE"
            summary = f"Contract requires improvements. Found {critical_count} critical issues, {missing_count} missing clauses, and {negotiable_count} negotiable points."
        
        return summary, recommendation
    
    async def _generate_summary_with_llm(
        self,
        safety_score: int,
        critical_points: List[ReviewPoint],
        missing_points: List[ReviewPoint],
        negotiable_points: List[ReviewPoint],
        good_points: List[ReviewPoint]
    ) -> tuple:
        """Generate executive summary using Gemini LLM based on actual findings."""
        
        if not self.llm_service:
            # Fallback to simple logic if no LLM
            return self._generate_fallback_summary(
                safety_score,
                len(critical_points),
                len(missing_points),
                len(negotiable_points),
                len(good_points)
            )
        
        # Build concise summary of top findings for LLM
        critical_summary = "\n".join([f"- {p.advice[:150]}" for p in critical_points[:5]]) if critical_points else "None"
        missing_summary = "\n".join([f"- {p.advice[:150]}" for p in missing_points[:5]]) if missing_points else "None"
        
        prompt = f"""You are the Referee in a legal council analyzing an employment contract.

The Skeptic, Strategist, and Auditor agents have completed their analysis:

SAFETY SCORE: {safety_score}/100

TOP CRITICAL ISSUES ({len(critical_points)} total):
{critical_summary}

TOP MISSING CLAUSES ({len(missing_points)} total):
{missing_summary}

NEGOTIABLE POINTS: {len(negotiable_points)}
POSITIVE ASPECTS: {len(good_points)}

Based on these council findings, provide your final verdict:

1. Executive Summary (2-3 sentences max)
2. Recommendation (SIGN, NEGOTIATE, or REJECT)

Guidelines:
- SIGN: Score 80+, no critical issues, safe contract
- NEGOTIATE: Moderate risks, issues can be addressed
- REJECT: Serious risks (3+ critical issues), dangerous contract

Respond ONLY with JSON:
{{"summary": "your summary", "recommendation": "SIGN|NEGOTIATE|REJECT"}}"""
        
        try:
            result = await self.llm_service.gemini_referee.generate(
                prompt=prompt,
                system_prompt="You are a senior legal advisor providing final contract verdicts."
            )
            
            if result["success"]:
                import json
                content = result["content"].strip()
                
                # Clean markdown formatting
                if "```" in content:
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
                
                data = json.loads(content)
                summary = data.get("summary", "").strip()
                recommendation = data.get("recommendation", "NEGOTIATE").strip().upper()
                
                # Validate
                if recommendation not in ["SIGN", "NEGOTIATE", "REJECT"]:
                    recommendation = "NEGOTIATE"
                
                if not summary:
                    raise ValueError("Empty summary")
                
                logger.info(f"✅ Gemini verdict: {recommendation} - \"{summary[:50]}...\"")
                return summary, recommendation
                
        except Exception as e:
            logger.warning(f"Gemini summary failed: {e}, using fallback")
        
        # Fallback
        return self._generate_fallback_summary(
            safety_score,
            len(critical_points),
            len(missing_points),
            len(negotiable_points),
            len(good_points)
        )
    
    async def aggregate(
        self,
        skeptic_points: List[ReviewPoint],
        strategist_points: List[ReviewPoint],
        auditor_points: List[ReviewPoint]
    ) -> ContractReviewResult:
        """
        Aggregate findings from all agents into final result.
        
        Steps:
        1. Combine all points
        2. Deduplicate
        3. Resolve conflicts (Risk Trumps Benefit)
        4. Categorize
        5. Calculate safety score
        6. Generate LLM-based summary
        """
        logger.info("Referee aggregating findings from all agents")
        
        # Combine all points
        all_points = skeptic_points + strategist_points + auditor_points
        logger.info(f"Total raw points from agents: {len(all_points)}")
        
        # Deduplicate
        unique_points = self.deduplicate_points(all_points)
        
        # Resolve conflicts
        resolved_points = self.resolve_conflicts(unique_points)
        
        # Categorize by type
        categorized: Dict[ReviewCategory, List[ReviewPoint]] = {
            ReviewCategory.CRITICAL: [],
            ReviewCategory.GOOD: [],
            ReviewCategory.NEGOTIABLE: [],
            ReviewCategory.MISSING: []
        }
        
        for point in resolved_points:
            categorized[point.category].append(point)
        
        # Calculate safety score
        safety_score = self.calculate_safety_score(
            critical_count=len(categorized[ReviewCategory.CRITICAL]),
            missing_count=len(categorized[ReviewCategory.MISSING]),
            negotiable_count=len(categorized[ReviewCategory.NEGOTIABLE]),
            good_count=len(categorized[ReviewCategory.GOOD])
        )
        
        # Generate LLM-based summary and recommendation
        summary, recommendation = await self._generate_summary_with_llm(
            safety_score=safety_score,
            critical_points=categorized[ReviewCategory.CRITICAL],
            missing_points=categorized[ReviewCategory.MISSING],
            negotiable_points=categorized[ReviewCategory.NEGOTIABLE],
            good_points=categorized[ReviewCategory.GOOD]
        )
        
        # Create result
        result = ContractReviewResult(
            review_id=f"rev_{uuid.uuid4().hex[:12]}",
            safety_score=safety_score,
            summary=summary,
            recommendation=recommendation,
            critical_points=categorized[ReviewCategory.CRITICAL],
            good_points=categorized[ReviewCategory.GOOD],
            negotiable_points=categorized[ReviewCategory.NEGOTIABLE],
            missing_points=categorized[ReviewCategory.MISSING],
            total_findings=len(resolved_points),
            created_at=datetime.utcnow()
        )
        
        logger.info(
            f"Referee completed aggregation: "
            f"Safety Score {safety_score}/100, "
            f"Total Findings: {result.total_findings}, "
            f"Recommendation: {recommendation}"
        )
        
        return result


# Global instance
referee_agent = RefereeAgent()
