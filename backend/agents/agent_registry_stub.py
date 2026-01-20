"""
AgentRegistryStub - In-memory agent registry for development/testing

Tracks which agents are registered, their capabilities, and health status.

Key Features:
- In-memory agent tracking (Python dict)
- Heartbeat tracking (last_heartbeat timestamp)
- Agent discovery (find agents by type or capability)
- Health monitoring (detect dead agents)

When to use:
- Local development (no Redis installed)
- Unit testing
- Early Phase 3 development (before infrastructure ready)

Migration path:
When Developer B builds real infrastructure, replace:
```python
# Before (stub)
from agents.agent_registry_stub import AgentRegistryStub
registry = AgentRegistryStub()

# After (real Redis)
from agents.agent_registry import AgentRegistry
registry = AgentRegistry(redis_client)
```
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


class AgentRegistryStub:
    """
    In-memory agent registry (no Redis required).
    
    Stores agent metadata:
    - agent_id, agent_type, priority
    - capabilities (what this agent can do)
    - registered_at, last_heartbeat
    - status (active, idle, dead)
    - metrics (tasks completed, failed, etc.)
    """
    
    def __init__(self, heartbeat_timeout_seconds: int = 90):
        """
        Initialize agent registry.
        
        Args:
            heartbeat_timeout_seconds: After this many seconds without heartbeat,
                                       agent is considered dead
        """
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_timeout = timedelta(seconds=heartbeat_timeout_seconds)
        self._lock = asyncio.Lock()
        
        logger.info(f"AgentRegistryStub initialized (heartbeat_timeout={heartbeat_timeout_seconds}s)")
    
    async def register(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[Dict[str, Any]],
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an agent with the registry.
        
        Args:
            agent_id: Unique agent identifier (e.g., "obs_1")
            agent_type: Agent type (e.g., "observation", "requirements")
            capabilities: List of capabilities (from agent.capabilities)
            priority: Agent priority (1-10, higher = more important)
            metadata: Additional metadata (version, config, etc.)
        
        Returns:
            True if registered successfully, False if already registered
        
        Example:
            await registry.register(
                agent_id="obs_1",
                agent_type="observation",
                capabilities=[{"name": "code_analysis", "version": "1.0.0"}],
                priority=7
            )
        """
        async with self._lock:
            if agent_id in self.agents:
                logger.warning(f"Agent {agent_id} already registered")
                return False
            
            now = datetime.utcnow()
            self.agents[agent_id] = {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
                "priority": priority,
                "registered_at": now,
                "last_heartbeat": now,
                "status": "active",
                "metadata": metadata or {},
            }
            
            logger.info(f"Registered agent {agent_id} (type: {agent_type}, priority: {priority})")
            return True
    
    async def deregister(self, agent_id: str) -> bool:
        """
        Deregister an agent (graceful shutdown).
        
        Args:
            agent_id: Agent to deregister
        
        Returns:
            True if deregistered, False if not found
        
        Example:
            await registry.deregister("obs_1")
        """
        async with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not registered")
                return False
            
            del self.agents[agent_id]
            logger.info(f"Deregistered agent {agent_id}")
            return True
    
    async def heartbeat(
        self,
        agent_id: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update agent heartbeat (agent is still alive).
        
        Heartbeats should be sent every 30-60 seconds.
        If no heartbeat received for >90 seconds, agent is considered dead.
        
        Args:
            agent_id: Agent sending heartbeat
            metrics: Optional metrics (tasks completed, etc.)
        
        Returns:
            True if heartbeat recorded, False if agent not registered
        
        Example:
            await registry.heartbeat("obs_1", metrics={
                "tasks_completed": 10,
                "tasks_failed": 1,
                "active_tasks": 2
            })
        """
        async with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"Heartbeat from unregistered agent {agent_id}")
                return False
            
            self.agents[agent_id]["last_heartbeat"] = datetime.utcnow()
            self.agents[agent_id]["status"] = "active"
            
            if metrics:
                self.agents[agent_id]["metrics"] = metrics
            
            logger.debug(f"Heartbeat from agent {agent_id}")
            return True
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent information by ID.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Agent info dict or None if not found
        
        Example:
            agent = await registry.get_agent("obs_1")
            if agent:
                print(f"Agent type: {agent['agent_type']}")
                print(f"Last heartbeat: {agent['last_heartbeat']}")
        """
        async with self._lock:
            agent = self.agents.get(agent_id)
            if agent:
                # Check if agent is dead (no heartbeat)
                if self._is_agent_dead(agent):
                    agent["status"] = "dead"
            return agent
    
    async def get_agents_by_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """
        Get all agents of a specific type.
        
        Args:
            agent_type: Agent type to filter (e.g., "observation")
        
        Returns:
            List of agent info dicts
        
        Example:
            observation_agents = await registry.get_agents_by_type("observation")
            print(f"Found {len(observation_agents)} observation agents")
        """
        async with self._lock:
            agents = [
                agent for agent in self.agents.values()
                if agent["agent_type"] == agent_type
            ]
            
            # Update status for dead agents
            for agent in agents:
                if self._is_agent_dead(agent):
                    agent["status"] = "dead"
            
            return agents
    
    async def get_agents_by_capability(
        self,
        capability_name: str
    ) -> List[Dict[str, Any]]:
        """
        Find agents that have a specific capability.
        
        Used for task routing: "Which agents can handle code_analysis?"
        
        Args:
            capability_name: Capability to search for
        
        Returns:
            List of agents that have this capability
        
        Example:
            agents = await registry.get_agents_by_capability("code_analysis")
            for agent in agents:
                print(f"Agent {agent['agent_id']} can analyze code")
        """
        async with self._lock:
            matching_agents = []
            
            for agent in self.agents.values():
                # Check if agent has this capability
                capabilities = agent.get("capabilities", [])
                for cap in capabilities:
                    if cap.get("name") == capability_name:
                        if not self._is_agent_dead(agent):
                            matching_agents.append(agent)
                        break
            
            return matching_agents
    
    async def get_all_agents(
        self,
        include_dead: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all registered agents.
        
        Args:
            include_dead: If True, include agents that haven't sent heartbeat
        
        Returns:
            List of all agent info dicts
        
        Example:
            all_agents = await registry.get_all_agents()
            print(f"Total agents: {len(all_agents)}")
        """
        async with self._lock:
            agents = list(self.agents.values())
            
            # Update status
            for agent in agents:
                if self._is_agent_dead(agent):
                    agent["status"] = "dead"
            
            # Filter dead agents if requested
            if not include_dead:
                agents = [a for a in agents if a["status"] != "dead"]
            
            return agents
    
    async def get_healthy_agents_count(self) -> int:
        """
        Get count of healthy (non-dead) agents.
        
        Returns:
            Number of agents that sent heartbeat recently
        """
        async with self._lock:
            healthy_count = sum(
                1 for agent in self.agents.values()
                if not self._is_agent_dead(agent)
            )
            return healthy_count
    
    async def cleanup_dead_agents(self) -> int:
        """
        Remove agents that haven't sent heartbeat in a long time.
        
        Returns:
            Number of dead agents removed
        
        Example:
            # Run periodically to clean up dead agents
            removed = await registry.cleanup_dead_agents()
            print(f"Cleaned up {removed} dead agents")
        """
        async with self._lock:
            dead_agents = [
                agent_id for agent_id, agent in self.agents.items()
                if self._is_agent_dead(agent)
            ]
            
            for agent_id in dead_agents:
                del self.agents[agent_id]
                logger.info(f"Cleaned up dead agent {agent_id}")
            
            return len(dead_agents)
    
    def _is_agent_dead(self, agent: Dict[str, Any]) -> bool:
        """
        Check if agent is dead (no heartbeat for >90 seconds).
        
        Args:
            agent: Agent info dict
        
        Returns:
            True if agent is dead
        """
        last_heartbeat = agent.get("last_heartbeat")
        if not last_heartbeat:
            return True
        
        time_since_heartbeat = datetime.utcnow() - last_heartbeat
        return time_since_heartbeat > self.heartbeat_timeout
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with:
            - total_agents: Total registered agents
            - healthy_agents: Agents with recent heartbeat
            - dead_agents: Agents without recent heartbeat
            - agents_by_type: Count by agent type
            - agents_by_status: Count by status
        """
        async with self._lock:
            total = len(self.agents)
            healthy = sum(1 for a in self.agents.values() if not self._is_agent_dead(a))
            dead = total - healthy
            
            agents_by_type = {}
            for agent in self.agents.values():
                agent_type = agent["agent_type"]
                agents_by_type[agent_type] = agents_by_type.get(agent_type, 0) + 1
            
            return {
                "total_agents": total,
                "healthy_agents": healthy,
                "dead_agents": dead,
                "agents_by_type": agents_by_type,
                "heartbeat_timeout_seconds": self.heartbeat_timeout.total_seconds(),
            }
    
    def __repr__(self) -> str:
        healthy = sum(1 for a in self.agents.values() if not self._is_agent_dead(a))
        return f"AgentRegistryStub(total={len(self.agents)}, healthy={healthy})"
