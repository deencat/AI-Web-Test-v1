"""
Phase 3: Multi-Agent Test Generation System
Agents Package - Contains all agent implementations
"""

from .base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult
from .observation_agent import ObservationAgent

__all__ = [
    "BaseAgent",
    "AgentCapability", 
    "TaskContext",
    "TaskResult",
    "ObservationAgent",
]
