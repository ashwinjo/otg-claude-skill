"""
Tests for Transport Adapter Layer.

TDD approach: Define expected behavior before implementation.
Tests for the transport abstraction layer that allows the orchestrator to work
with sub-agents and skills.
"""
import pytest
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

from src.orchestrator.transport import (
    SubAgentResult,
    SubAgentTransport,
    SkillTransport,
)


class TestSubAgentResult:
    """Test SubAgentResult dataclass."""

    def test_subagent_result_success(self):
        """Create a successful result."""
        result = SubAgentResult(
            status="success",
            agent_name="test-agent",
            output={"key": "value"},
            error=None,
            duration_seconds=10.5,
        )
        assert result.status == "success"
        assert result.agent_name == "test-agent"
        assert result.output == {"key": "value"}
        assert result.error is None
        assert result.duration_seconds == 10.5

    def test_subagent_result_error(self):
        """Create an error result."""
        result = SubAgentResult(
            status="error",
            agent_name="test-agent",
            output={},
            error="Something went wrong",
            duration_seconds=5.2,
        )
        assert result.status == "error"
        assert result.agent_name == "test-agent"
        assert result.error == "Something went wrong"
        assert result.duration_seconds == 5.2


class TestSubAgentTransportInterface:
    """Test SubAgentTransport abstract interface."""

    def test_transport_interface_defined(self):
        """Verify SubAgentTransport is an abstract base class."""
        # SubAgentTransport should be abstract
        assert issubclass(SubAgentTransport, ABC)

        # Should have required abstract methods
        required_methods = [
            "invoke",
            "supports_interactive_confirmation",
            "get_checkpoint_timeout",
        ]
        for method_name in required_methods:
            assert hasattr(SubAgentTransport, method_name)

    def test_cannot_instantiate_abstract_transport(self):
        """SubAgentTransport should not be instantiable."""
        with pytest.raises(TypeError):
            SubAgentTransport()


class TestSkillTransport:
    """Test SkillTransport concrete implementation."""

    def test_skill_transport_implements_interface(self):
        """SkillTransport should implement SubAgentTransport."""
        assert issubclass(SkillTransport, SubAgentTransport)

    def test_skill_transport_instantiation(self):
        """Create a SkillTransport instance."""
        transport = SkillTransport()
        assert transport is not None

    def test_skill_transport_invocation_success(self):
        """Invoke a skill and get a successful result."""
        transport = SkillTransport()

        result = transport.invoke(
            agent_name="test-skill",
            context={"query": "test query"},
            timeout_seconds=60,
        )

        assert isinstance(result, SubAgentResult)
        assert result.agent_name == "test-skill"
        assert result.status == "success"
        assert isinstance(result.output, dict)
        assert result.duration_seconds >= 0

    def test_skill_transport_invocation_with_complex_context(self):
        """Invoke with complex context data."""
        transport = SkillTransport()

        context = {
            "query": "deploy network",
            "parameters": {"nodes": 5, "protocol": "bgp"},
            "tags": ["automation", "test"],
        }

        result = transport.invoke(
            agent_name="deployment-skill",
            context=context,
            timeout_seconds=120,
        )

        assert result.status == "success"
        assert result.agent_name == "deployment-skill"
        assert result.duration_seconds >= 0

    def test_skill_transport_supports_interactive(self):
        """SkillTransport should support interactive confirmation."""
        transport = SkillTransport()
        assert transport.supports_interactive_confirmation() is True

    def test_skill_transport_get_checkpoint_timeout(self):
        """Get checkpoint timeout for a skill."""
        transport = SkillTransport()

        # Test with known agents from AGENT_CONFIG
        timeout = transport.get_checkpoint_timeout("ixia-c-deployment")
        assert timeout == 600

        timeout = transport.get_checkpoint_timeout("otg-config-generator")
        assert timeout == 120

        timeout = transport.get_checkpoint_timeout("snappi-script-generator")
        assert timeout == 60

        timeout = transport.get_checkpoint_timeout("keng-licensing")
        assert timeout == 30

    def test_skill_transport_get_checkpoint_timeout_unknown_agent(self):
        """Get timeout for unknown agent should raise ValueError."""
        transport = SkillTransport()

        with pytest.raises(ValueError):
            transport.get_checkpoint_timeout("unknown-agent")

    def test_skill_transport_multiple_invocations(self):
        """Invoke multiple skills sequentially."""
        transport = SkillTransport()

        result1 = transport.invoke(
            agent_name="skill-1",
            context={"step": 1},
            timeout_seconds=30,
        )
        assert result1.status == "success"

        result2 = transport.invoke(
            agent_name="skill-2",
            context={"step": 2},
            timeout_seconds=30,
        )
        assert result2.status == "success"

        assert result1.agent_name == "skill-1"
        assert result2.agent_name == "skill-2"
