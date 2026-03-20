"""
Transport Adapter Layer for Sub-Agent and Skill Invocation.

Provides abstraction for orchestrator to work with sub-agents (skills) through
a unified transport interface. Designed for future SDK migration.

Architecture:
- SubAgentTransport: Abstract base interface for all transports
- SkillTransport: Concrete implementation for Claude Code skills
- Future: SDKTransport for ADK agents

This separation allows the orchestrator to remain agnostic to the underlying
execution platform.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
import time

from src.orchestrator.config import AGENT_CONFIG


@dataclass
class SubAgentResult:
    """
    Result of a sub-agent/skill invocation.

    Attributes:
        status: Execution status ("success" or "error")
        agent_name: Name of the agent/skill that was invoked
        output: Dictionary containing the output from the agent
        error: Optional error message if status is "error"
        duration_seconds: Time taken to execute the agent
    """

    status: str
    agent_name: str
    output: Dict[str, Any]
    error: Optional[str]
    duration_seconds: float


class SubAgentTransport(ABC):
    """
    Abstract base class for sub-agent transport implementations.

    Defines the interface that all transport implementations must follow.
    This allows the orchestrator to work with different execution platforms
    (Claude Code skills, ADK agents, etc.) through a common interface.
    """

    @abstractmethod
    def invoke(
        self,
        agent_name: str,
        context: Dict[str, Any],
        timeout_seconds: int,
    ) -> SubAgentResult:
        """
        Invoke a sub-agent/skill with the given context.

        Args:
            agent_name: Name of the agent/skill to invoke
            context: Input context/parameters for the agent
            timeout_seconds: Maximum time to wait for completion

        Returns:
            SubAgentResult with execution status and output
        """
        pass

    @abstractmethod
    def supports_interactive_confirmation(self) -> bool:
        """
        Check if this transport supports interactive user confirmation.

        Returns:
            True if the transport can prompt for user confirmation,
            False otherwise
        """
        pass

    @abstractmethod
    def get_checkpoint_timeout(self, agent_name: str) -> int:
        """
        Get the checkpoint timeout for a specific agent.

        Checkpoint timeout determines how long the system will wait
        at checkpoint boundaries before timing out.

        Args:
            agent_name: Name of the agent to query

        Returns:
            Timeout in seconds

        Raises:
            ValueError: If agent_name is not found in configuration
        """
        pass


class SkillTransport(SubAgentTransport):
    """
    Transport implementation for Claude Code skills.

    Handles invocation of skills within the Claude Code platform.
    Skills are sub-agents that operate within the interactive Claude Code
    environment, allowing for real-time user confirmation and feedback.

    In production, this would call invoke_skill() from Claude Code SDK.
    For now, returns mock results for testing.
    """

    def __init__(self):
        """Initialize the SkillTransport."""
        pass

    def invoke(
        self,
        agent_name: str,
        context: Dict[str, Any],
        timeout_seconds: int,
    ) -> SubAgentResult:
        """
        Invoke a Claude Code skill.

        Args:
            agent_name: Name of the skill to invoke
            context: Input context/parameters for the skill
            timeout_seconds: Maximum time to wait for completion

        Returns:
            SubAgentResult with execution status and output

        Note:
            Production implementation would call:
            invoke_skill(skill=agent_name, context=context)
        """
        start_time = time.time()

        # Mock invocation for now
        # In production: result = invoke_skill(skill=agent_name, context=context)
        output = {
            "skill": agent_name,
            "context_received": context,
            "status": "completed",
        }

        duration_seconds = time.time() - start_time

        return SubAgentResult(
            status="success",
            agent_name=agent_name,
            output=output,
            error=None,
            duration_seconds=duration_seconds,
        )

    def supports_interactive_confirmation(self) -> bool:
        """
        Claude Code skills support interactive confirmation.

        Returns:
            True - Claude Code is an interactive platform
        """
        return True

    def get_checkpoint_timeout(self, agent_name: str) -> int:
        """
        Get checkpoint timeout from AGENT_CONFIG.

        Args:
            agent_name: Name of the agent to query

        Returns:
            Timeout in seconds from configuration

        Raises:
            ValueError: If agent_name is not in AGENT_CONFIG
        """
        if agent_name not in AGENT_CONFIG:
            raise ValueError(
                f"Agent '{agent_name}' not found in AGENT_CONFIG. "
                f"Available agents: {list(AGENT_CONFIG.keys())}"
            )

        return AGENT_CONFIG[agent_name]["timeout_seconds"]
