"""Agents package initialization."""

from app.agents.skeptic import skeptic_agent
from app.agents.strategist import strategist_agent
from app.agents.auditor import auditor_agent
from app.agents.referee import referee_agent

__all__ = [
    "skeptic_agent",
    "strategist_agent",
    "auditor_agent",
    "referee_agent"
]
