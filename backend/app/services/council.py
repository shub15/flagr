"""
Council aggregator for building consensus from multiple LLM responses.
"""

import logging
import json
from typing import List, Dict, Any
from collections import Counter
from app.models.schemas import ReviewPoint, ReviewCategory
from app.config import settings

logger = logging.getLogger(__name__)


class CouncilAggregator:
    """Aggregates multiple LLM responses to reach consensus."""
    
    def __init__(self, consensus_threshold: float = None):
        self.threshold = consensus_threshold or settings.council_consensus_threshold
    
    def parse_llm_response(self, response: Dict[str, Any]) -> List[ReviewPoint]:
        """
        Parse LLM response into ReviewPoint objects.
        Expected JSON format from LLM:
        [
            {
                "category": "CRITICAL",
                "quote": "...",
                "advice": "..."
            }
        ]
        """
        if not response.get("success"):
            return []
        
        try:
            content = response["content"]
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            points = []
            for item in data:
                try:
                    point = ReviewPoint(
                        category=ReviewCategory(item["category"]),
                        quote=item.get("quote"),
                        advice=item["advice"],
                        agent_source=response["provider"],
                        confidence=1.0  # Will be updated by consensus
                    )
                    points.append(point)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse review point: {e}")
                    continue
            
            return points
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return []
    
    def deduplicate_by_similarity(self, points: List[ReviewPoint]) -> List[ReviewPoint]:
        """
        Deduplicate similar points based on quote and advice text similarity.
        Simple implementation using exact matching and substring matching.
        For production, consider using embedding-based similarity.
        """
        if not points:
            return []
        
        unique_points = []
        seen_combinations = set()
        
        for point in points:
            # Create a normalized key for deduplication
            key = (
                point.category.value,
                (point.quote or "").lower().strip()[:100],  # First 100 chars
                point.advice.lower().strip()[:100]
            )
            
            if key not in seen_combinations:
                seen_combinations.add(key)
                unique_points.append(point)
        
        return unique_points
    
    def build_consensus(
        self,
        llm_responses: List[Dict[str, Any]],
        agent_source: str
    ) -> List[ReviewPoint]:
        """
        Build consensus from multiple LLM responses.
        
        Algorithm:
        1. Parse all LLM responses into ReviewPoint objects
        2. Group similar points
        3. Keep points agreed upon by ≥ threshold of providers
        4. Calculate confidence based on agreement level
        """
        # Parse all responses
        all_points = []
        for response in llm_responses:
            points = self.parse_llm_response(response)
            all_points.extend(points)
        
        if not all_points:
            logger.warning(f"No valid points found from council for {agent_source}")
            return []
        
        # Group by category and deduplicate
        categorized = {}
        for point in all_points:
            if point.category not in categorized:
                categorized[point.category] = []
            categorized[point.category].append(point)
        
        # Build consensus points
        consensus_points = []
        total_providers = len([r for r in llm_responses if r.get("success")])
        
        if total_providers == 0:
            return []
        
        for category, points in categorized.items():
            # Deduplicate within category
            unique_points = self.deduplicate_by_similarity(points)
            
            # Count how many providers mentioned each point
            for point in unique_points:
                # Count similar points (simple version: exact match on first 50 chars of advice)
                similar_count = sum(
                    1 for p in points
                    if p.advice[:50].lower() == point.advice[:50].lower()
                )
                
                # Calculate confidence as agreement ratio
                confidence = similar_count / total_providers
                
                # Only include if meets threshold (or if only 1-2 providers available)
                if confidence >= self.threshold or total_providers <= 2:
                    point.confidence = round(confidence, 2)
                    point.agent_source = agent_source
                    consensus_points.append(point)
                else:
                    logger.debug(
                        f"Point '{point.advice[:50]}...' below threshold "
                        f"({confidence:.2f} < {self.threshold})"
                    )
        
        logger.info(
            f"Council consensus for {agent_source}: "
            f"{len(consensus_points)} points from {len(all_points)} raw findings"
        )
        
        return consensus_points
    
    def aggregate_by_voting(
        self,
        llm_responses: List[Dict[str, Any]],
        agent_source: str
    ) -> List[ReviewPoint]:
        """
        Alternative aggregation: simple voting mechanism.
        Each unique finding gets a vote, highest votes win.
        """
        all_findings = []
        
        for response in llm_responses:
            points = self.parse_llm_response(response)
            all_findings.extend(points)
        
        if not all_findings:
            return []
        
        # Vote by advice text (simplified)
        advice_votes = Counter(p.advice for p in all_findings)
        
        # Keep top findings
        consensus = []
        for finding in all_findings:
            votes = advice_votes[finding.advice]
            if votes >= len(llm_responses) * self.threshold:
                finding.confidence = votes / len(llm_responses)
                finding.agent_source = agent_source
                if finding not in consensus:  # Avoid duplicates
                    consensus.append(finding)
        
        return consensus


# Global instance
council_aggregator = CouncilAggregator()
