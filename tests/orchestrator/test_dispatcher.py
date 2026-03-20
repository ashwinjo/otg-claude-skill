"""
Tests for Dispatcher & DispatchQueue.

TDD approach: Define expected behavior before implementation.
Tests for conditional dispatch queue building and parallelism detection.
"""
import pytest
from src.orchestrator.dispatcher import (
    SubAgent,
    DispatchQueue,
    Dispatcher,
)
from src.orchestrator.intent import Intent, UseCase


class TestSubAgent:
    """Test SubAgent dataclass structure and properties."""

    def test_subagent_basic_creation(self):
        """SubAgent should create with all required fields."""
        agent = SubAgent(
            name="ixia-c-deployment",
            sequence=0,
            color="🔵",
            can_run_parallel=True,
            depends_on=None,
            timeout_seconds=600,
            max_retries=3,
        )
        assert agent.name == "ixia-c-deployment"
        assert agent.sequence == 0
        assert agent.color == "🔵"
        assert agent.can_run_parallel is True
        assert agent.depends_on is None
        assert agent.timeout_seconds == 600
        assert agent.max_retries == 3

    def test_subagent_with_dependency(self):
        """SubAgent should support depends_on reference to prior sequence."""
        agent = SubAgent(
            name="otg-config-generator",
            sequence=1,
            color="🟢",
            can_run_parallel=False,
            depends_on=0,
            timeout_seconds=120,
            max_retries=2,
        )
        assert agent.depends_on == 0
        assert agent.can_run_parallel is False

    def test_subagent_all_colors(self):
        """SubAgent should support all emoji colors."""
        colors = ["🔵", "🟢", "🟡", "🟠"]
        for i, color in enumerate(colors):
            agent = SubAgent(
                name=f"agent_{i}",
                sequence=i,
                color=color,
                can_run_parallel=True,
                depends_on=None,
                timeout_seconds=60,
                max_retries=1,
            )
            assert agent.color == color


class TestDispatcherAgentConfigs:
    """Test Dispatcher.AGENT_CONFIGS static configuration."""

    def test_dispatcher_has_agent_configs(self):
        """Dispatcher should have AGENT_CONFIGS dict."""
        assert hasattr(Dispatcher, "AGENT_CONFIGS")
        assert isinstance(Dispatcher.AGENT_CONFIGS, dict)

    def test_dispatcher_agent_configs_has_all_agents(self):
        """Dispatcher.AGENT_CONFIGS should include all 4 agents."""
        required_agents = [
            "ixia-c-deployment",
            "otg-config-generator",
            "snappi-script-generator",
            "keng-licensing",
        ]
        for agent_name in required_agents:
            assert agent_name in Dispatcher.AGENT_CONFIGS

    def test_dispatcher_agent_configs_structure(self):
        """Each agent config should have required fields."""
        for agent_name, config in Dispatcher.AGENT_CONFIGS.items():
            assert "color" in config
            assert "timeout" in config
            assert "max_retries" in config
            assert "can_parallel" in config
            assert isinstance(config["color"], str)
            assert isinstance(config["timeout"], int)
            assert isinstance(config["max_retries"], int)
            assert isinstance(config["can_parallel"], bool)

    def test_dispatcher_agent_configs_values(self):
        """Agent configs should have correct timeout and retry values."""
        configs = Dispatcher.AGENT_CONFIGS
        assert configs["ixia-c-deployment"]["timeout"] == 600
        assert configs["ixia-c-deployment"]["max_retries"] == 3
        assert configs["otg-config-generator"]["timeout"] == 120
        assert configs["otg-config-generator"]["max_retries"] == 2
        assert configs["snappi-script-generator"]["timeout"] == 60
        assert configs["snappi-script-generator"]["max_retries"] == 1
        assert configs["keng-licensing"]["timeout"] == 30
        assert configs["keng-licensing"]["max_retries"] == 1

    def test_dispatcher_agent_configs_colors(self):
        """Agent configs should have correct emoji colors."""
        configs = Dispatcher.AGENT_CONFIGS
        assert configs["ixia-c-deployment"]["color"] == "🔵"
        assert configs["otg-config-generator"]["color"] == "🟢"
        assert configs["snappi-script-generator"]["color"] == "🟡"
        assert configs["keng-licensing"]["color"] == "🟠"

    def test_dispatcher_agent_configs_parallelism(self):
        """Agent configs should have correct parallelism settings."""
        configs = Dispatcher.AGENT_CONFIGS
        assert configs["ixia-c-deployment"]["can_parallel"] is True
        assert configs["otg-config-generator"]["can_parallel"] is False
        assert configs["snappi-script-generator"]["can_parallel"] is False
        assert configs["keng-licensing"]["can_parallel"] is True


class TestDispatchQueue:
    """Test DispatchQueue structure and operations."""

    def test_dispatch_queue_basic_creation(self):
        """DispatchQueue should create with list of SubAgents."""
        agents = [
            SubAgent(
                name="ixia-c-deployment",
                sequence=0,
                color="🔵",
                can_run_parallel=True,
                depends_on=None,
                timeout_seconds=600,
                max_retries=3,
            ),
        ]
        queue = DispatchQueue(agents=agents)
        assert len(queue.agents) == 1
        assert queue.agents[0].name == "ixia-c-deployment"

    def test_dispatch_queue_empty(self):
        """DispatchQueue should support empty queue."""
        queue = DispatchQueue(agents=[])
        assert len(queue.agents) == 0

    def test_dispatch_queue_get_parallel_groups(self):
        """DispatchQueue.get_parallel_groups() should group agents by dependency."""
        agents = [
            SubAgent(
                name="ixia-c-deployment",
                sequence=0,
                color="🔵",
                can_run_parallel=True,
                depends_on=None,
                timeout_seconds=600,
                max_retries=3,
            ),
            SubAgent(
                name="otg-config-generator",
                sequence=1,
                color="🟢",
                can_run_parallel=False,
                depends_on=0,
                timeout_seconds=120,
                max_retries=2,
            ),
        ]
        queue = DispatchQueue(agents=agents)
        groups = queue.get_parallel_groups()

        # Should return list of lists (groups)
        assert isinstance(groups, list)
        assert len(groups) == 2  # Two sequential groups
        assert len(groups[0]) == 1  # First group has deployment
        assert len(groups[1]) == 1  # Second group has config

    def test_dispatch_queue_parallel_eligible_agents_grouped(self):
        """DispatchQueue should group agents that can run in parallel."""
        agents = [
            SubAgent(
                name="ixia-c-deployment",
                sequence=0,
                color="🔵",
                can_run_parallel=True,
                depends_on=None,
                timeout_seconds=600,
                max_retries=3,
            ),
            SubAgent(
                name="keng-licensing",
                sequence=1,
                color="🟠",
                can_run_parallel=True,
                depends_on=None,  # Can run in parallel with deployment
                timeout_seconds=30,
                max_retries=1,
            ),
        ]
        queue = DispatchQueue(agents=agents)
        groups = queue.get_parallel_groups()

        # Both agents can run in parallel and have no dependencies
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_dispatch_queue_sequential_agents(self):
        """DispatchQueue should not group sequential-only agents."""
        agents = [
            SubAgent(
                name="otg-config-generator",
                sequence=0,
                color="🟢",
                can_run_parallel=False,
                depends_on=None,
                timeout_seconds=120,
                max_retries=2,
            ),
            SubAgent(
                name="snappi-script-generator",
                sequence=1,
                color="🟡",
                can_run_parallel=False,
                depends_on=0,
                timeout_seconds=60,
                max_retries=1,
            ),
        ]
        queue = DispatchQueue(agents=agents)
        groups = queue.get_parallel_groups()

        # Sequential agents should be in separate groups
        assert len(groups) == 2
        assert groups[0][0].name == "otg-config-generator"
        assert groups[1][0].name == "snappi-script-generator"


class TestDispatcherBuildQueue:
    """Test Dispatcher.build_queue() method for each use case."""

    def _build_full_greenfield_intent(self) -> Intent:
        """Helper to build a full_greenfield intent."""
        return Intent(
            use_case=UseCase.full_greenfield,
            test_scenario={
                "name": "BGP Test",
                "description": "BGP test",
                "protocols": ["BGP"],
                "port_count": 2,
            },
            deployment={
                "method": "docker_compose",
                "deployment_type": "CP+DP",
                "ports": [
                    {"name": "te1", "speed": "100GE"},
                    {"name": "te2", "speed": "100GE"},
                ],
            },
        )

    def _build_config_only_intent(self) -> Intent:
        """Helper to build a config_only intent."""
        return Intent(
            use_case=UseCase.config_only,
            test_scenario={
                "name": "Config Test",
                "description": "Config test",
                "protocols": ["BGP"],
                "port_count": 2,
            },
            infrastructure={
                "controller_url": "localhost:8443",
                "ports": [
                    {"name": "eth1", "location": "te1:5555"},
                    {"name": "eth2", "location": "te2:5556"},
                ],
            },
        )

    def _build_deployment_only_intent(self) -> Intent:
        """Helper to build a deployment_only intent."""
        return Intent(
            use_case=UseCase.deployment_only,
            deployment={
                "method": "docker_compose",
                "deployment_type": "CP+DP",
                "ports": [
                    {"name": "te1", "speed": "100GE"},
                    {"name": "te2", "speed": "100GE"},
                ],
            },
        )

    def _build_script_only_intent(self) -> Intent:
        """Helper to build a script_only intent."""
        return Intent(
            use_case=UseCase.script_only,
            otg_config_path="/path/to/config.json",
            infrastructure={
                "controller_url": "localhost:8443",
                "ports": [{"name": "port1", "location": "ixia_port_1"}],
            },
        )

    def _build_licensing_only_intent(self) -> Intent:
        """Helper to build a licensing_only intent."""
        return Intent(
            use_case=UseCase.licensing_only,
            licensing={
                "port_count": 2,
                "port_speed": "100GE",
                "protocols": ["BGP"],
            },
        )

    def test_dispatcher_build_queue_returns_dispatch_queue(self):
        """build_queue() should return DispatchQueue instance."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        assert isinstance(queue, DispatchQueue)

    def test_dispatcher_queues_agents_for_full_greenfield(self):
        """Full greenfield should queue deployment, config, script, in order."""
        intent = self._build_full_greenfield_intent()
        queue = Dispatcher.build_queue(intent)

        # Should have all 3 agents
        assert len(queue.agents) == 3

        # Check sequence order
        assert queue.agents[0].name == "ixia-c-deployment"
        assert queue.agents[0].sequence == 0

        assert queue.agents[1].name == "otg-config-generator"
        assert queue.agents[1].sequence == 1
        assert queue.agents[1].depends_on == 0

        assert queue.agents[2].name == "snappi-script-generator"
        assert queue.agents[2].sequence == 2
        assert queue.agents[2].depends_on == 1

    def test_dispatcher_queues_agents_for_full_greenfield_with_licensing(self):
        """Full greenfield with licensing should include all 4 agents."""
        intent = self._build_full_greenfield_intent()
        intent.include_licensing = True
        intent.licensing = {
            "port_count": 2,
            "port_speed": "100GE",
            "protocols": ["BGP"],
        }

        queue = Dispatcher.build_queue(intent)
        assert len(queue.agents) == 4

        agent_names = [agent.name for agent in queue.agents]
        assert "ixia-c-deployment" in agent_names
        assert "otg-config-generator" in agent_names
        assert "snappi-script-generator" in agent_names
        assert "keng-licensing" in agent_names

    def test_dispatcher_queues_agents_for_config_only(self):
        """Config only should skip deployment and queue config, script."""
        intent = self._build_config_only_intent()
        queue = Dispatcher.build_queue(intent)

        # Should have 2 agents (config + script)
        assert len(queue.agents) == 2

        # Check order
        assert queue.agents[0].name == "otg-config-generator"
        assert queue.agents[0].sequence == 0
        assert queue.agents[0].depends_on is None

        assert queue.agents[1].name == "snappi-script-generator"
        assert queue.agents[1].sequence == 1
        assert queue.agents[1].depends_on == 0

    def test_dispatcher_queues_agents_for_deployment_only(self):
        """Deployment only should queue only deployment agent."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)

        assert len(queue.agents) == 1
        assert queue.agents[0].name == "ixia-c-deployment"
        assert queue.agents[0].sequence == 0
        assert queue.agents[0].depends_on is None

    def test_dispatcher_queues_agents_for_script_only(self):
        """Script only should queue only script agent."""
        intent = self._build_script_only_intent()
        queue = Dispatcher.build_queue(intent)

        assert len(queue.agents) == 1
        assert queue.agents[0].name == "snappi-script-generator"
        assert queue.agents[0].sequence == 0
        assert queue.agents[0].depends_on is None

    def test_dispatcher_queues_agents_for_licensing_only(self):
        """Licensing only should queue only licensing agent."""
        intent = self._build_licensing_only_intent()
        queue = Dispatcher.build_queue(intent)

        assert len(queue.agents) == 1
        assert queue.agents[0].name == "keng-licensing"
        assert queue.agents[0].sequence == 0
        assert queue.agents[0].depends_on is None

    def test_dispatcher_detects_parallel_group_in_full_greenfield(self):
        """Full greenfield should detect parallelism via get_parallel_groups()."""
        intent = self._build_full_greenfield_intent()
        queue = Dispatcher.build_queue(intent)
        groups = queue.get_parallel_groups()

        # Deployment is sequence 0, config depends on 0, script depends on 1
        # So: [deployment], [config], [script]
        assert len(groups) == 3

    def test_dispatcher_detects_parallel_group_with_licensing(self):
        """Full greenfield with licensing should detect parallel licensing."""
        intent = self._build_full_greenfield_intent()
        intent.include_licensing = True
        intent.licensing = {
            "port_count": 2,
            "port_speed": "100GE",
            "protocols": ["BGP"],
        }

        queue = Dispatcher.build_queue(intent)
        groups = queue.get_parallel_groups()

        # Check that licensing is in a group where it can run in parallel
        licensing_agents = [a for a in queue.agents if a.name == "keng-licensing"]
        assert len(licensing_agents) == 1
        assert licensing_agents[0].can_run_parallel is True

    def test_dispatcher_preserves_agent_config_on_build(self):
        """build_queue() should preserve agent configurations from AGENT_CONFIGS."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)

        agent = queue.agents[0]
        config = Dispatcher.AGENT_CONFIGS[agent.name]

        assert agent.color == config["color"]
        assert agent.timeout_seconds == config["timeout"]
        assert agent.max_retries == config["max_retries"]
        assert agent.can_run_parallel == config["can_parallel"]

    def test_dispatcher_builds_correct_sequences(self):
        """Sequences should be 0, 1, 2, ... in order."""
        intent = self._build_full_greenfield_intent()
        queue = Dispatcher.build_queue(intent)

        for i, agent in enumerate(queue.agents):
            assert agent.sequence == i

    def test_dispatcher_builds_dependencies_correctly(self):
        """Dependencies should reference prior sequences."""
        intent = self._build_full_greenfield_intent()
        queue = Dispatcher.build_queue(intent)

        for i, agent in enumerate(queue.agents):
            if i == 0:
                # First agent has no dependencies
                assert agent.depends_on is None
            else:
                # Later agents depend on the previous one
                assert agent.depends_on == i - 1
