"""
The Referee Agent - Aggregates, deduplicates, resolves conflicts, and scores.
Does not generate new ideas, only synthesizes findings from other agents.
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
    """
    
    def __init__(self):
        self.agent_name = "referee"
    
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
    
    def aggregate(
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
        
        # Create result
        result = ContractReviewResult(
            review_id=f"rev_{uuid.uuid4().hex[:12]}",
            safety_score=safety_score,
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
            f"Total Findings: {result.total_findings}"
        )
        
        return result


# Global instance
referee_agent = RefereeAgent()
