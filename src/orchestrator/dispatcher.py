"""
Dispatcher Module: Conditional Execution Queue Builder.

Defines the dispatcher that builds execution queues based on use case intent,
including SubAgent specifications, DispatchQueue management, and parallelism detection.

Components:
- SubAgent: Dataclass for individual agent specifications with timing, retries, dependencies
- DispatchQueue: Queue container with parallel group detection
- Dispatcher: Static factory that builds queues from Intent objects
"""
from dataclasses import dataclass
from typing import Optional, List
from src.orchestrator.intent import Intent, UseCase


@dataclass
class SubAgent:
    """Specification for a sub-agent in the orchestration pipeline.

    Attributes:
        name: Agent identifier (e.g., 'ixia-c-deployment')
        sequence: Execution order (0, 1, 2, 3...)
        color: Emoji color for UI representation (🔵, 🟢, 🟡, 🟠)
        can_run_parallel: Whether agent can execute in parallel with others
        depends_on: Optional sequence number of prerequisite agent
        timeout_seconds: Max execution time in seconds
        max_retries: Number of retry attempts on failure
    """

    name: str
    sequence: int
    color: str
    can_run_parallel: bool
    depends_on: Optional[int]
    timeout_seconds: int
    max_retries: int


class DispatchQueue:
    """Queue container for orchestration agents.

    Manages a list of SubAgents and provides methods to detect parallel execution groups.

    Attributes:
        agents: List of SubAgent objects in execution order
    """

    def __init__(self, agents: List[SubAgent]):
        """Initialize queue with agents.

        Args:
            agents: List of SubAgent objects
        """
        self.agents = agents

    def get_parallel_groups(self) -> List[List[SubAgent]]:
        """Detect and group agents that can execute in parallel.

        Groups agents by dependency chain. Agents with no dependency or agents
        that can run parallel without dependencies are grouped together.

        Returns:
            List of agent groups, where each group can execute in parallel.
            Groups are ordered by execution sequence.

        Example:
            Agents with dependencies [None, 0, 1, 1] produce groups:
            [[agent_0], [agent_1], [agent_2, agent_3]]
        """
        if not self.agents:
            return []

        groups = []
        current_group = []

        # Track agents by sequence for dependency lookups
        agents_by_seq = {agent.sequence: agent for agent in self.agents}

        for i, agent in enumerate(self.agents):
            # First agent always starts a new group
            if i == 0:
                current_group = [agent]
                continue

            # Check if agent can be grouped with current group
            # An agent can be grouped if:
            # 1. It can run in parallel, AND
            # 2. Its dependency (if any) is not in the current group
            prev_agent = self.agents[i - 1]
            can_group = False

            if agent.can_run_parallel and prev_agent.can_run_parallel:
                # Both can run parallel - check dependencies
                if agent.depends_on is None or agent.depends_on not in [
                    a.sequence for a in current_group
                ]:
                    can_group = True

            if can_group:
                # Add to current group
                current_group.append(agent)
            else:
                # Start new group
                groups.append(current_group)
                current_group = [agent]

        # Append final group
        if current_group:
            groups.append(current_group)

        return groups


class Dispatcher:
    """Static factory for building execution queues from Intent objects.

    Defines agent configurations and builds DispatchQueues based on use case intent.
    """

    # Static configuration for all agents
    AGENT_CONFIGS = {
        "ixia-c-deployment": {
            "color": "🔵",
            "timeout": 600,
            "max_retries": 3,
            "can_parallel": True,
        },
        "otg-config-generator": {
            "color": "🟢",
            "timeout": 120,
            "max_retries": 2,
            "can_parallel": False,
        },
        "snappi-script-generator": {
            "color": "🟡",
            "timeout": 60,
            "max_retries": 1,
            "can_parallel": False,
        },
        "keng-licensing": {
            "color": "🟠",
            "timeout": 30,
            "max_retries": 1,
            "can_parallel": True,
        },
    }

    @staticmethod
    def build_queue(intent: Intent) -> DispatchQueue:
        """Build execution queue from intent.

        Routes to appropriate queue builder based on use_case.

        Args:
            intent: Intent object specifying use case and requirements

        Returns:
            DispatchQueue with agents configured for the use case

        Raises:
            ValueError: If use case is not supported
        """
        if intent.use_case == UseCase.full_greenfield:
            return Dispatcher._build_full_greenfield_queue(intent)
        elif intent.use_case == UseCase.config_only:
            return Dispatcher._build_config_only_queue(intent)
        elif intent.use_case == UseCase.deployment_only:
            return Dispatcher._build_deployment_only_queue(intent)
        elif intent.use_case == UseCase.script_only:
            return Dispatcher._build_script_only_queue(intent)
        elif intent.use_case == UseCase.licensing_only:
            return Dispatcher._build_licensing_only_queue(intent)
        else:
            raise ValueError(f"Unsupported use case: {intent.use_case}")

    @staticmethod
    def _build_full_greenfield_queue(intent: Intent) -> DispatchQueue:
        """Build queue for full greenfield use case.

        Pipeline: deployment -> config -> script [-> licensing (optional)]

        Args:
            intent: Full greenfield intent

        Returns:
            DispatchQueue with all agents in dependency order
        """
        agents = []
        sequence = 0

        # Step 1: Deployment
        agents.append(
            Dispatcher._create_agent(
                name="ixia-c-deployment",
                sequence=sequence,
                depends_on=None,
            )
        )
        sequence += 1

        # Step 2: Config (depends on deployment)
        agents.append(
            Dispatcher._create_agent(
                name="otg-config-generator",
                sequence=sequence,
                depends_on=0,
            )
        )
        sequence += 1

        # Step 3: Script (depends on config)
        agents.append(
            Dispatcher._create_agent(
                name="snappi-script-generator",
                sequence=sequence,
                depends_on=1,
            )
        )
        sequence += 1

        # Step 4: Licensing (optional, depends on deployment)
        if intent.include_licensing and intent.licensing:
            agents.append(
                Dispatcher._create_agent(
                    name="keng-licensing",
                    sequence=sequence,
                    depends_on=0,  # Can depend on deployment, can run in parallel
                )
            )

        return DispatchQueue(agents=agents)

    @staticmethod
    def _build_config_only_queue(intent: Intent) -> DispatchQueue:
        """Build queue for config_only use case.

        Pipeline: config -> script

        Args:
            intent: Config only intent

        Returns:
            DispatchQueue with config and script agents
        """
        agents = []

        # Step 1: Config (no deployment needed, no dependency)
        agents.append(
            Dispatcher._create_agent(
                name="otg-config-generator",
                sequence=0,
                depends_on=None,
            )
        )

        # Step 2: Script (depends on config)
        agents.append(
            Dispatcher._create_agent(
                name="snappi-script-generator",
                sequence=1,
                depends_on=0,
            )
        )

        return DispatchQueue(agents=agents)

    @staticmethod
    def _build_deployment_only_queue(intent: Intent) -> DispatchQueue:
        """Build queue for deployment_only use case.

        Pipeline: deployment

        Args:
            intent: Deployment only intent

        Returns:
            DispatchQueue with only deployment agent
        """
        agents = [
            Dispatcher._create_agent(
                name="ixia-c-deployment",
                sequence=0,
                depends_on=None,
            )
        ]
        return DispatchQueue(agents=agents)

    @staticmethod
    def _build_script_only_queue(intent: Intent) -> DispatchQueue:
        """Build queue for script_only use case.

        Pipeline: script

        Args:
            intent: Script only intent

        Returns:
            DispatchQueue with only script agent
        """
        agents = [
            Dispatcher._create_agent(
                name="snappi-script-generator",
                sequence=0,
                depends_on=None,
            )
        ]
        return DispatchQueue(agents=agents)

    @staticmethod
    def _build_licensing_only_queue(intent: Intent) -> DispatchQueue:
        """Build queue for licensing_only use case.

        Pipeline: licensing

        Args:
            intent: Licensing only intent

        Returns:
            DispatchQueue with only licensing agent
        """
        agents = [
            Dispatcher._create_agent(
                name="keng-licensing",
                sequence=0,
                depends_on=None,
            )
        ]
        return DispatchQueue(agents=agents)

    @staticmethod
    def _create_agent(
        name: str, sequence: int, depends_on: Optional[int] = None
    ) -> SubAgent:
        """Create a SubAgent from name, sequence, and dependency.

        Retrieves configuration from AGENT_CONFIGS.

        Args:
            name: Agent name (must exist in AGENT_CONFIGS)
            sequence: Execution sequence number
            depends_on: Optional prerequisite agent sequence

        Returns:
            Fully configured SubAgent

        Raises:
            KeyError: If agent name not found in AGENT_CONFIGS
        """
        if name not in Dispatcher.AGENT_CONFIGS:
            raise KeyError(f"Agent '{name}' not found in AGENT_CONFIGS")

        config = Dispatcher.AGENT_CONFIGS[name]

        return SubAgent(
            name=name,
            sequence=sequence,
            color=config["color"],
            can_run_parallel=config["can_parallel"],
            depends_on=depends_on,
            timeout_seconds=config["timeout"],
            max_retries=config["max_retries"],
        )
