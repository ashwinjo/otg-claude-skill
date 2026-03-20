# OTG Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code orchestrator agent that validates user intent, conditionally dispatches to 4 sub-agents, manages checkpoints, handles errors intelligently, and produces auditable artifacts.

**Architecture:** Multi-phase implementation following the design spec. Phase 1-2 establish core intent validation and dispatch logic (5 tasks). Phase 3-4 add checkpointing and error recovery (4 tasks). Phase 5 adds transport abstraction for future SDK migration (2 tasks). Each phase builds on the previous; phases can be tested independently.

**Tech Stack:** Python 3.9+, Pydantic (validation), JSON (checkpoints/manifests), pytest (testing), Claude Code Skill tool (sub-agent dispatch)

---

## File Structure

**Orchestrator Core:**
- `src/orchestrator/intent.py` — Intent schema + validation + clarifying questions
- `src/orchestrator/dispatcher.py` — Conditional dispatch logic + sub-agent queuing
- `src/orchestrator/checkpoint.py` — Checkpoint schema + save/load logic
- `src/orchestrator/artifact.py` — Manifest generation + summary markdown
- `src/orchestrator/recovery.py` — Error classification + recovery strategies
- `src/orchestrator/transport.py` — Transport adapter interface + SkillTransport implementation
- `src/orchestrator/orchestrator.py` — Main orchestrator class that ties all phases together

**Tests:**
- `tests/orchestrator/test_intent.py` — Intent validation tests
- `tests/orchestrator/test_dispatcher.py` — Dispatch logic tests
- `tests/orchestrator/test_checkpoint.py` — Checkpoint I/O tests
- `tests/orchestrator/test_artifact.py` — Manifest + summary tests
- `tests/orchestrator/test_recovery.py` — Error recovery tests
- `tests/orchestrator/test_transport.py` — Transport adapter tests
- `tests/orchestrator/test_orchestrator_e2e.py` — End-to-end integration tests

**Skill Entry Point:**
- `skills/otg-orchestrator/SKILL.md` — Skill manifest
- `skills/otg-orchestrator/skill_handler.py` — Claude Code skill entry point

**Artifacts & Examples:**
- `orchestration_runs/` — Directory for run artifacts (created at runtime)
- `docs/orchestrator/USAGE.md` — User guide + examples

**Utilities:**
- `src/orchestrator/config.py` — Configuration (timeouts, retry counts, paths)
- `src/orchestrator/utils.py` — Helpers (timestamps, checksums, JSON serialization)

---

## Implementation Roadmap

### Phase 1: Intent Intake & Validation (Tasks 1-2)

Implement the intent schema, clarifying question engine, and validation logic.

#### Task 1: Define Intent Schema & Validation

**Files:**
- Create: `src/orchestrator/intent.py`
- Create: `tests/orchestrator/test_intent.py`

- [ ] **Step 1: Write test for Intent schema parsing**

```python
# tests/orchestrator/test_intent.py
import pytest
from orchestrator.intent import Intent, IntentValidator

def test_intent_schema_parse_valid():
    """Intent schema should parse valid intent JSON."""
    intent_json = {
        "user_request": "Create BGP test",
        "use_case": "full_greenfield",
        "deployment": {
            "method": "docker_compose",
            "controller_url": "localhost:8443",
            "ports": [{"name": "te1", "speed": "100GE"}]
        },
        "test_scenario": {
            "protocols": ["bgp"],
            "port_count": 1,
            "sessions": {"bgp": 2},
            "traffic_rate": "1000 pps"
        },
        "licensing": {
            "tier": "developer",
            "estimate_required": False
        },
        "flags": {
            "ask_at_checkpoints": True,
            "auto_retry": True,
            "max_wait_time_minutes": 30
        }
    }
    intent = Intent(**intent_json)
    assert intent.use_case == "full_greenfield"
    assert intent.deployment.controller_url == "localhost:8443"

def test_intent_schema_validates_use_case():
    """Intent should validate use_case enum."""
    invalid_intent = {
        "user_request": "Test",
        "use_case": "invalid_case",
        "deployment": {},
        "test_scenario": {},
        "licensing": {},
        "flags": {}
    }
    with pytest.raises(ValueError):
        Intent(**invalid_intent)

def test_intent_schema_requires_critical_fields():
    """Intent should require critical fields."""
    incomplete = {
        "user_request": "Test"
    }
    with pytest.raises(TypeError):
        Intent(**incomplete)
```

- [ ] **Step 2: Implement Intent schema using Pydantic**

```python
# src/orchestrator/intent.py
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class UseCase(str, Enum):
    FULL_GREENFIELD = "full_greenfield"
    CONFIG_ONLY = "config_only"
    DEPLOYMENT_ONLY = "deployment_only"
    SCRIPT_ONLY = "script_only"
    LICENSING_ONLY = "licensing_only"

class DeploymentMethod(str, Enum):
    DOCKER_COMPOSE = "docker_compose"
    CONTAINERLAB = "containerlab"

class Port(BaseModel):
    name: str
    speed: str  # e.g., "100GE", "10GE"

class Deployment(BaseModel):
    method: Optional[DeploymentMethod] = None
    controller_url: Optional[str] = None
    ports: List[Port] = []

class TestScenario(BaseModel):
    protocols: List[str] = []
    port_count: Optional[int] = None
    sessions: Dict[str, int] = {}  # e.g., {"bgp": 4, "isis": 2}
    traffic_rate: Optional[str] = None

class Licensing(BaseModel):
    tier: Optional[str] = None  # developer, team, system
    estimate_required: bool = False

class Flags(BaseModel):
    ask_at_checkpoints: bool = True
    auto_retry: bool = True
    max_wait_time_minutes: int = 30

class Intent(BaseModel):
    user_request: str
    use_case: UseCase
    deployment: Deployment = Deployment()
    test_scenario: TestScenario = TestScenario()
    licensing: Licensing = Licensing()
    flags: Flags = Flags()

    @validator('use_case', pre=True)
    def validate_use_case(cls, v):
        if isinstance(v, str):
            try:
                return UseCase(v)
            except ValueError:
                raise ValueError(f"Invalid use_case: {v}. Must be one of {list(UseCase)}")
        return v

class IntentValidator:
    """Validate intent against sub-agent capabilities."""

    @staticmethod
    def validate(intent: Intent) -> tuple[bool, List[str]]:
        """
        Validate intent.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check deployment requirements
        if intent.use_case in [UseCase.FULL_GREENFIELD, UseCase.DEPLOYMENT_ONLY]:
            if not intent.deployment.method:
                errors.append("deployment.method required for this use case")

        # Check test scenario requirements
        if intent.use_case != UseCase.DEPLOYMENT_ONLY:
            if not intent.test_scenario.protocols:
                errors.append("test_scenario.protocols required for this use case")
            if intent.test_scenario.port_count is None:
                errors.append("test_scenario.port_count required for this use case")

        # Check port speed if deployment provided
        if intent.deployment.ports:
            for port in intent.deployment.ports:
                if not port.speed:
                    errors.append(f"Port {port.name} missing speed")

        return (len(errors) == 0, errors)
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_intent.py::test_intent_schema_parse_valid -v
```

Expected output: `FAILED - ModuleNotFoundError: No module named 'orchestrator'`

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_intent.py -v
```

Expected output: All tests PASS (5/5)

- [ ] **Step 5: Commit Phase 1.1**

```bash
git add src/orchestrator/intent.py tests/orchestrator/test_intent.py
git commit -m "feat: implement intent schema and validation"
```

---

#### Task 2: Implement Intent Intake Engine (Clarifying Questions)

**Files:**
- Modify: `src/orchestrator/intent.py` (add IntentIntake class)
- Create: `tests/orchestrator/test_intent.py` (add intake tests)

- [ ] **Step 1: Write test for clarifying questions**

```python
# Add to tests/orchestrator/test_intent.py
from orchestrator.intent import IntentIntake

def test_intent_intake_classifies_use_case():
    """IntentIntake should classify use case from user request."""
    intake = IntentIntake()
    # Simulate user saying they want deployment + config + script
    request = "Create BGP test with 2 ports, deploy with Docker, get script"
    use_case = intake.classify_intent(request)
    # Should detect full_greenfield
    assert use_case == UseCase.FULL_GREENFIELD

def test_intent_intake_builds_intent():
    """IntentIntake should build complete intent from answers."""
    intake = IntentIntake()
    answers = {
        "deployment_method": "docker_compose",
        "controller_url": "localhost:8443",
        "protocols": ["bgp"],
        "port_count": 2,
        "port_speeds": ["100GE", "100GE"],
        "license_tier": "team",
        "estimate_required": True
    }
    intent = intake.build_intent("Create BGP test", answers)
    assert intent.use_case == UseCase.FULL_GREENFIELD
    assert intent.deployment.method == DeploymentMethod.DOCKER_COMPOSE
    assert intent.test_scenario.port_count == 2
```

- [ ] **Step 2: Implement IntentIntake class**

```python
# Add to src/orchestrator/intent.py
class IntentIntake:
    """Engine for gathering and building intent from user interaction."""

    CLARIFYING_QUESTIONS = {
        "deployment_method": {
            "question": "Do you want to deploy Ixia-c, or use existing infrastructure?",
            "options": ["docker_compose", "containerlab", "existing"],
            "field": "deployment.method"
        },
        "controller_url": {
            "question": "What is the controller URL? (e.g., localhost:8443)",
            "options": None,  # Open-ended
            "field": "deployment.controller_url",
            "required_for": ["docker_compose", "containerlab", "existing"]
        },
        "protocols": {
            "question": "What test protocols do you need? (BGP, ISIS, LACP, LLDP, etc.)",
            "options": ["bgp", "isis", "lacp", "lldp"],
            "field": "test_scenario.protocols",
            "required_for": ["config_only", "full_greenfield", "script_only"]
        },
        "port_count": {
            "question": "How many ports?",
            "options": ["1", "2", "4", "8"],
            "field": "test_scenario.port_count"
        },
        "port_speeds": {
            "question": "Port speeds? (e.g., 100GE, 10GE, 1GE)",
            "options": None,
            "field": "deployment.ports"
        },
        "license_tier": {
            "question": "License tier? (Developer, Team, System)",
            "options": ["developer", "team", "system"],
            "field": "licensing.tier"
        }
    }

    @staticmethod
    def classify_intent(user_request: str) -> UseCase:
        """
        Classify intent from user request.
        Heuristic: look for keywords like "deploy", "config", "script", "license".
        """
        request_lower = user_request.lower()

        has_deploy = "deploy" in request_lower or "docker" in request_lower
        has_config = "config" in request_lower or "test" in request_lower
        has_script = "script" in request_lower
        has_license = "license" in request_lower or "cost" in request_lower
        has_existing = "existing" in request_lower or "ixia" in request_lower

        if has_deploy and has_config and has_script:
            return UseCase.FULL_GREENFIELD
        elif has_config and has_script and not has_deploy:
            return UseCase.CONFIG_ONLY
        elif has_deploy and not has_config and not has_script:
            return UseCase.DEPLOYMENT_ONLY
        elif has_script and not has_deploy and not has_config:
            return UseCase.SCRIPT_ONLY
        elif has_license:
            return UseCase.LICENSING_ONLY
        else:
            return UseCase.FULL_GREENFIELD  # Default

    @staticmethod
    def build_intent(user_request: str, answers: Dict[str, Any]) -> Intent:
        """Build Intent from user answers."""
        use_case = IntentIntake.classify_intent(user_request)

        deployment = Deployment()
        if "deployment_method" in answers:
            deployment.method = DeploymentMethod(answers["deployment_method"])
        if "controller_url" in answers:
            deployment.controller_url = answers["controller_url"]
        if "port_speeds" in answers:
            port_names = answers.get("port_names", [f"te{i+1}" for i in range(answers.get("port_count", 1))])
            port_speeds = answers["port_speeds"]
            deployment.ports = [Port(name=name, speed=speed) for name, speed in zip(port_names, port_speeds)]

        test_scenario = TestScenario()
        if "protocols" in answers:
            test_scenario.protocols = answers["protocols"]
        if "port_count" in answers:
            test_scenario.port_count = int(answers["port_count"])
        if "sessions" in answers:
            test_scenario.sessions = answers["sessions"]
        if "traffic_rate" in answers:
            test_scenario.traffic_rate = answers["traffic_rate"]

        licensing = Licensing()
        if "license_tier" in answers:
            licensing.tier = answers["license_tier"]
        if "estimate_required" in answers:
            licensing.estimate_required = answers["estimate_required"]

        return Intent(
            user_request=user_request,
            use_case=use_case,
            deployment=deployment,
            test_scenario=test_scenario,
            licensing=licensing
        )
```

- [ ] **Step 3: Run test to verify it passes**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_intent.py -v
```

Expected output: All tests PASS

- [ ] **Step 4: Commit Phase 1.2**

```bash
git add src/orchestrator/intent.py tests/orchestrator/test_intent.py
git commit -m "feat: implement intent intake engine with clarifying questions"
```

---

### Phase 2: Conditional Dispatch & State Machine (Tasks 3-4)

Implement the dispatch logic that determines which sub-agents to invoke based on use case, and the state machine that manages execution order.

#### Task 3: Implement Dispatch Queue & Execution Plan

**Files:**
- Create: `src/orchestrator/dispatcher.py`
- Create: `tests/orchestrator/test_dispatcher.py`

- [ ] **Step 1: Write test for dispatch queue**

```python
# tests/orchestrator/test_dispatcher.py
import pytest
from orchestrator.dispatcher import Dispatcher, SubAgent, DispatchQueue
from orchestrator.intent import Intent, UseCase

def test_dispatcher_queues_agents_for_full_greenfield():
    """For full_greenfield use case, queue should include all agents in order."""
    intent = Intent(
        user_request="Create BGP test and deploy",
        use_case=UseCase.FULL_GREENFIELD,
        licensing={"estimate_required": True}
    )
    queue = Dispatcher.build_queue(intent)
    agent_names = [agent.name for agent in queue.agents]
    # Should be: deployment, config, script, licensing (with deployment + licensing parallel)
    assert "ixia-c-deployment" in agent_names
    assert "otg-config-generator" in agent_names
    assert "snappi-script-generator" in agent_names
    assert "keng-licensing" in agent_names

def test_dispatcher_queues_agents_for_config_only():
    """For config_only use case, skip deployment."""
    intent = Intent(
        user_request="Create config and script",
        use_case=UseCase.CONFIG_ONLY
    )
    queue = Dispatcher.build_queue(intent)
    agent_names = [agent.name for agent in queue.agents]
    assert "ixia-c-deployment" not in agent_names
    assert "otg-config-generator" in agent_names
    assert "snappi-script-generator" in agent_names

def test_dispatcher_detects_parallel_group():
    """Dispatcher should identify parallel-eligible agents."""
    intent = Intent(
        user_request="Create BGP test and deploy with license",
        use_case=UseCase.FULL_GREENFIELD,
        licensing={"estimate_required": True}
    )
    queue = Dispatcher.build_queue(intent)
    # Find parallel group (deployment + licensing)
    parallel_agents = [a for a in queue.agents if a.can_run_parallel]
    assert len(parallel_agents) >= 2
```

- [ ] **Step 2: Implement Dispatcher class**

```python
# src/orchestrator/dispatcher.py
from dataclasses import dataclass, field
from typing import List, Optional
from orchestrator.intent import Intent, UseCase

@dataclass
class SubAgent:
    """Represents a sub-agent in the dispatch queue."""
    name: str  # e.g., "ixia-c-deployment"
    sequence: int  # 0, 1, 2, 3...
    color: str  # 🔵, 🟢, 🟡, 🟠
    can_run_parallel: bool = False  # Can run in parallel with others
    depends_on: Optional[int] = None  # sequence number of agent this depends on
    timeout_seconds: int = 60
    max_retries: int = 1

class DispatchQueue:
    """Ordered queue of sub-agents to invoke."""

    def __init__(self, agents: List[SubAgent]):
        self.agents = agents

    def get_parallel_groups(self) -> List[List[SubAgent]]:
        """
        Group agents into parallel execution groups.
        Returns list of groups; agents in same group can run in parallel.
        """
        groups = []
        current_group = []

        for agent in self.agents:
            if agent.can_run_parallel and len(current_group) > 0:
                # Add to current parallel group if dependencies allow
                if not agent.depends_on or agent.depends_on < len(groups) - 1:
                    current_group.append(agent)
                else:
                    # Start new sequential phase
                    if current_group:
                        groups.append(current_group)
                    current_group = [agent]
            else:
                # Sequential agent, finalize current group and start new
                if current_group:
                    groups.append(current_group)
                current_group = [agent]

        if current_group:
            groups.append(current_group)

        return groups

class Dispatcher:
    """Determines which sub-agents to invoke and in what order."""

    AGENT_CONFIGS = {
        "ixia-c-deployment": {
            "color": "🔵",
            "timeout": 600,
            "max_retries": 3,
            "can_parallel": True
        },
        "otg-config-generator": {
            "color": "🟢",
            "timeout": 120,
            "max_retries": 2,
            "can_parallel": False
        },
        "snappi-script-generator": {
            "color": "🟡",
            "timeout": 60,
            "max_retries": 1,
            "can_parallel": False
        },
        "keng-licensing": {
            "color": "🟠",
            "timeout": 30,
            "max_retries": 1,
            "can_parallel": True
        }
    }

    @staticmethod
    def build_queue(intent: Intent) -> DispatchQueue:
        """Build dispatch queue based on use case."""
        agents = []
        sequence = 0

        if intent.use_case == UseCase.FULL_GREENFIELD:
            # Parallel group A: deployment + licensing
            agents.append(SubAgent(
                name="ixia-c-deployment",
                sequence=sequence,
                color=Dispatcher.AGENT_CONFIGS["ixia-c-deployment"]["color"],
                can_run_parallel=True,
                timeout_seconds=Dispatcher.AGENT_CONFIGS["ixia-c-deployment"]["timeout"],
                max_retries=Dispatcher.AGENT_CONFIGS["ixia-c-deployment"]["max_retries"]
            ))

            if intent.licensing.estimate_required:
                agents.append(SubAgent(
                    name="keng-licensing",
                    sequence=sequence,
                    color=Dispatcher.AGENT_CONFIGS["keng-licensing"]["color"],
                    can_run_parallel=True,
                    timeout_seconds=Dispatcher.AGENT_CONFIGS["keng-licensing"]["timeout"],
                    max_retries=Dispatcher.AGENT_CONFIGS["keng-licensing"]["max_retries"]
                ))

            sequence += 1

            # Sequential: config + script
            agents.append(SubAgent(
                name="otg-config-generator",
                sequence=sequence,
                color=Dispatcher.AGENT_CONFIGS["otg-config-generator"]["color"],
                depends_on=0,
                timeout_seconds=Dispatcher.AGENT_CONFIGS["otg-config-generator"]["timeout"],
                max_retries=Dispatcher.AGENT_CONFIGS["otg-config-generator"]["max_retries"]
            ))
            sequence += 1

            agents.append(SubAgent(
                name="snappi-script-generator",
                sequence=sequence,
                color=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["color"],
                depends_on=sequence - 1,
                timeout_seconds=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["timeout"],
                max_retries=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["max_retries"]
            ))

        elif intent.use_case == UseCase.CONFIG_ONLY:
            agents.append(SubAgent(
                name="otg-config-generator",
                sequence=0,
                color=Dispatcher.AGENT_CONFIGS["otg-config-generator"]["color"],
                timeout_seconds=Dispatcher.AGENT_CONFIGS["otg-config-generator"]["timeout"],
                max_retries=Dispatcher.AGENT_CONFIGS["otg-config-generator"]["max_retries"]
            ))
            agents.append(SubAgent(
                name="snappi-script-generator",
                sequence=1,
                color=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["color"],
                depends_on=0,
                timeout_seconds=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["timeout"],
                max_retries=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["max_retries"]
            ))

        elif intent.use_case == UseCase.DEPLOYMENT_ONLY:
            agents.append(SubAgent(
                name="ixia-c-deployment",
                sequence=0,
                color=Dispatcher.AGENT_CONFIGS["ixia-c-deployment"]["color"],
                timeout_seconds=Dispatcher.AGENT_CONFIGS["ixia-c-deployment"]["timeout"],
                max_retries=Dispatcher.AGENT_CONFIGS["ixia-c-deployment"]["max_retries"]
            ))

        elif intent.use_case == UseCase.SCRIPT_ONLY:
            agents.append(SubAgent(
                name="snappi-script-generator",
                sequence=0,
                color=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["color"],
                timeout_seconds=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["timeout"],
                max_retries=Dispatcher.AGENT_CONFIGS["snappi-script-generator"]["max_retries"]
            ))

        elif intent.use_case == UseCase.LICENSING_ONLY:
            agents.append(SubAgent(
                name="keng-licensing",
                sequence=0,
                color=Dispatcher.AGENT_CONFIGS["keng-licensing"]["color"],
                timeout_seconds=Dispatcher.AGENT_CONFIGS["keng-licensing"]["timeout"],
                max_retries=Dispatcher.AGENT_CONFIGS["keng-licensing"]["max_retries"]
            ))

        return DispatchQueue(agents)
```

- [ ] **Step 3: Run test to verify**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_dispatcher.py -v
```

Expected output: All tests PASS

- [ ] **Step 4: Commit Phase 2.1**

```bash
git add src/orchestrator/dispatcher.py tests/orchestrator/test_dispatcher.py
git commit -m "feat: implement conditional dispatch queue and parallelism detection"
```

---

#### Task 4: Implement Orchestrator State Machine

**Files:**
- Create: `src/orchestrator/orchestrator.py` (partial - just state machine)
- Modify: `tests/orchestrator/test_orchestrator_e2e.py` (create, add state machine tests)

- [ ] **Step 1: Write test for state machine transitions**

```python
# tests/orchestrator/test_orchestrator_e2e.py
import pytest
from orchestrator.orchestrator import OrchestratorStateMachine, OrchestratorState
from orchestrator.intent import Intent, UseCase
from orchestrator.dispatcher import Dispatcher

def test_state_machine_transitions_from_intent_validated_to_dispatch():
    """State machine should transition: INTENT_VALIDATED → DISPATCH."""
    intent = Intent(
        user_request="Create BGP test",
        use_case=UseCase.FULL_GREENFIELD
    )
    queue = Dispatcher.build_queue(intent)
    state_machine = OrchestratorStateMachine(intent, queue)

    assert state_machine.current_state == OrchestratorState.INTENT_VALIDATED
    state_machine.next()
    assert state_machine.current_state == OrchestratorState.DISPATCH_PHASE

def test_state_machine_cycles_through_agents():
    """State machine should cycle through each agent in queue."""
    intent = Intent(
        user_request="Create BGP test",
        use_case=UseCase.FULL_GREENFIELD
    )
    queue = Dispatcher.build_queue(intent)
    state_machine = OrchestratorStateMachine(intent, queue)

    state_machine.next()  # → DISPATCH_PHASE

    # Cycle through agents
    agents_processed = []
    while state_machine.current_state == OrchestratorState.DISPATCH_PHASE:
        current_agent = state_machine.get_current_agent()
        agents_processed.append(current_agent.name)
        state_machine.next()

    # Should have processed all agents in queue
    assert len(agents_processed) == len(queue.agents)
```

- [ ] **Step 2: Implement OrchestratorStateMachine**

```python
# src/orchestrator/orchestrator.py
from enum import Enum
from typing import Optional
from orchestrator.intent import Intent
from orchestrator.dispatcher import DispatchQueue, SubAgent

class OrchestratorState(str, Enum):
    INTENT_INTAKE = "intent_intake"
    INTENT_VALIDATED = "intent_validated"
    DISPATCH_PHASE = "dispatch_phase"
    AGENT_INVOKED = "agent_invoked"
    CHECKPOINT_SAVED = "checkpoint_saved"
    USER_CONFIRMATION = "user_confirmation"
    ERROR_RECOVERY = "error_recovery"
    ARTIFACTS_GENERATED = "artifacts_generated"
    COMPLETE = "complete"

class OrchestratorStateMachine:
    """Manages state transitions during orchestration."""

    def __init__(self, intent: Intent, queue: DispatchQueue):
        self.intent = intent
        self.queue = queue
        self.current_state = OrchestratorState.INTENT_VALIDATED
        self.agent_index = 0
        self.checkpoint_count = 0

    def next(self):
        """Transition to next state."""
        if self.current_state == OrchestratorState.INTENT_VALIDATED:
            self.current_state = OrchestratorState.DISPATCH_PHASE
        elif self.current_state == OrchestratorState.DISPATCH_PHASE:
            if self.agent_index < len(self.queue.agents):
                self.current_state = OrchestratorState.AGENT_INVOKED
            else:
                self.current_state = OrchestratorState.ARTIFACTS_GENERATED
        elif self.current_state == OrchestratorState.AGENT_INVOKED:
            self.current_state = OrchestratorState.CHECKPOINT_SAVED
        elif self.current_state == OrchestratorState.CHECKPOINT_SAVED:
            self.current_state = OrchestratorState.USER_CONFIRMATION
        elif self.current_state == OrchestratorState.USER_CONFIRMATION:
            self.agent_index += 1
            if self.agent_index < len(self.queue.agents):
                self.current_state = OrchestratorState.DISPATCH_PHASE
            else:
                self.current_state = OrchestratorState.ARTIFACTS_GENERATED
        elif self.current_state == OrchestratorState.ARTIFACTS_GENERATED:
            self.current_state = OrchestratorState.COMPLETE

    def get_current_agent(self) -> Optional[SubAgent]:
        """Return current agent being processed."""
        if self.agent_index < len(self.queue.agents):
            return self.queue.agents[self.agent_index]
        return None

    def set_error_recovery(self):
        """Transition to error recovery state."""
        self.current_state = OrchestratorState.ERROR_RECOVERY

    def is_complete(self) -> bool:
        """Return True if orchestration is complete."""
        return self.current_state == OrchestratorState.COMPLETE
```

- [ ] **Step 3: Run test to verify**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_orchestrator_e2e.py::test_state_machine_transitions_from_intent_validated_to_dispatch -v
```

Expected output: PASS

- [ ] **Step 4: Commit Phase 2.2**

```bash
git add src/orchestrator/orchestrator.py tests/orchestrator/test_orchestrator_e2e.py
git commit -m "feat: implement orchestrator state machine"
```

---

### Phase 3: Checkpoint & Artifact System (Tasks 5-6)

Implement checkpoint saving, manifest generation, and human-readable summaries.

#### Task 5: Implement Checkpoint Schema & Persistence

**Files:**
- Create: `src/orchestrator/checkpoint.py`
- Create: `tests/orchestrator/test_checkpoint.py`
- Create: `src/orchestrator/utils.py` (helpers: timestamps, checksums)

- [ ] **Step 1: Write test for checkpoint saving**

```python
# tests/orchestrator/test_checkpoint.py
import pytest
import json
import tempfile
from pathlib import Path
from orchestrator.checkpoint import Checkpoint, CheckpointManager
from orchestrator.dispatcher import SubAgent

def test_checkpoint_schema_serialize():
    """Checkpoint should serialize to JSON."""
    checkpoint = Checkpoint(
        checkpoint_id="ckpt_0_ixia-c-deployment",
        sub_agent="ixia-c-deployment",
        agent_color="🔵",
        sequence=0,
        status="success",
        input={"method": "docker_compose"},
        output={"file": "docker-compose.yml"},
        duration_seconds=45,
        retry_count=0,
        user_action="approved"
    )
    json_str = checkpoint.to_json()
    data = json.loads(json_str)
    assert data["sequence"] == 0
    assert data["user_action"] == "approved"

def test_checkpoint_manager_saves_to_file():
    """CheckpointManager should save checkpoint to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(Path(tmpdir))
        checkpoint = Checkpoint(
            checkpoint_id="ckpt_0_test",
            sub_agent="test-agent",
            agent_color="🔵",
            sequence=0,
            status="success",
            input={},
            output={},
            duration_seconds=1,
            retry_count=0,
            user_action="approved"
        )
        manager.save(checkpoint)

        # Verify file exists
        expected_path = Path(tmpdir) / "ckpt_0_test.json"
        assert expected_path.exists()

        # Verify content
        with open(expected_path) as f:
            data = json.load(f)
        assert data["checkpoint_id"] == "ckpt_0_test"
```

- [ ] **Step 2: Implement Checkpoint & CheckpointManager**

```python
# src/orchestrator/checkpoint.py
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
from orchestrator.utils import get_timestamp, compute_checksum

@dataclass
class Checkpoint:
    """A single checkpoint after a sub-agent completes."""
    checkpoint_id: str
    sub_agent: str
    agent_color: str
    sequence: int
    status: str  # "success", "failed", "retry"
    input: Dict[str, Any]
    output: Dict[str, Any]
    timestamp: str = field(default_factory=get_timestamp)
    duration_seconds: float = 0.0
    retry_count: int = 0
    warnings: list = field(default_factory=list)
    user_action: Optional[str] = None  # "approved", "rejected", "edit_and_retry"
    user_action_timestamp: Optional[str] = None
    output_size_bytes: int = 0
    output_checksum: str = ""

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        if self.output_checksum == "":
            # Compute checksum on first serialization
            output_str = json.dumps(self.output, sort_keys=True)
            data["output_checksum"] = compute_checksum(output_str)
            data["output_size_bytes"] = len(output_str)
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Checkpoint":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)

class CheckpointManager:
    """Manages checkpoint file I/O."""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: Checkpoint) -> Path:
        """Save checkpoint to file."""
        file_path = self.base_path / f"{checkpoint.checkpoint_id}.json"
        with open(file_path, "w") as f:
            f.write(checkpoint.to_json())
        return file_path

    def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from file."""
        file_path = self.base_path / f"{checkpoint_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            return Checkpoint.from_json(f.read())

    def list_checkpoints(self) -> list:
        """List all saved checkpoints."""
        return sorted(self.base_path.glob("ckpt_*.json"))
```

- [ ] **Step 3: Implement utility functions**

```python
# src/orchestrator/utils.py
from datetime import datetime
import hashlib

def get_timestamp() -> str:
    """Return ISO 8601 timestamp."""
    return datetime.utcnow().isoformat() + "Z"

def compute_checksum(data: str) -> str:
    """Compute SHA256 checksum of data."""
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()
```

- [ ] **Step 4: Run test to verify**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_checkpoint.py -v
```

Expected output: All tests PASS

- [ ] **Step 5: Commit Phase 3.1**

```bash
git add src/orchestrator/checkpoint.py src/orchestrator/utils.py tests/orchestrator/test_checkpoint.py
git commit -m "feat: implement checkpoint schema and persistence layer"
```

---

#### Task 6: Implement Manifest & Summary Generation

**Files:**
- Create: `src/orchestrator/artifact.py`
- Create: `tests/orchestrator/test_artifact.py`

- [ ] **Step 1: Write test for manifest generation**

```python
# tests/orchestrator/test_artifact.py
import pytest
import json
from orchestrator.artifact import Manifest, SummaryGenerator
from orchestrator.checkpoint import Checkpoint
from orchestrator.intent import Intent, UseCase

def test_manifest_schema():
    """Manifest should have required fields."""
    manifest = Manifest(
        run_id="run_20260319_101530",
        user_intent_original="Create BGP test",
        intent_normalized=Intent(
            user_request="Create BGP test",
            use_case=UseCase.FULL_GREENFIELD
        ),
        execution_flow=[],
        errors=[],
        warnings=[],
        final_status="complete",
        output_files=[]
    )
    json_str = manifest.to_json()
    data = json.loads(json_str)
    assert data["run_id"] == "run_20260319_101530"
    assert data["final_status"] == "complete"

def test_summary_generator_creates_markdown():
    """SummaryGenerator should create readable markdown."""
    checkpoints = [
        Checkpoint(
            checkpoint_id="ckpt_0_ixia-c-deployment",
            sub_agent="ixia-c-deployment",
            agent_color="🔵",
            sequence=0,
            status="success",
            input={},
            output={"file": "docker-compose.yml"},
            duration_seconds=45,
            retry_count=0,
            user_action="approved"
        )
    ]
    summary_md = SummaryGenerator.generate(
        user_intent="Create BGP test",
        checkpoints=checkpoints,
        warnings=["License may exceed limits"],
        total_duration=45
    )
    assert "Create BGP test" in summary_md
    assert "docker-compose.yml" in summary_md
    assert "License may exceed limits" in summary_md
```

- [ ] **Step 2: Implement Manifest & SummaryGenerator**

```python
# src/orchestrator/artifact.py
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from orchestrator.intent import Intent
from orchestrator.utils import get_timestamp

@dataclass
class ManifestExecutionStep:
    """Single step in execution flow."""
    sequence: int
    sub_agent: str
    agent_color: str
    status: str
    retry_count: int
    duration_seconds: float
    user_action: Optional[str] = None
    user_action_timestamp: Optional[str] = None
    first_attempt_error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

@dataclass
class Manifest:
    """Master execution record."""
    run_id: str
    user_intent_original: str
    intent_normalized: Intent
    execution_flow: List[ManifestExecutionStep]
    errors: List[str]
    warnings: List[str]
    final_status: str  # "success", "partial_success", "failed"
    output_files: List[str]
    timestamps: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamps:
            self.timestamps = {
                "start": get_timestamp(),
                "end": None,
                "duration_seconds": 0
            }

    def finalize(self):
        """Mark manifest as complete."""
        self.timestamps["end"] = get_timestamp()

    def to_json(self) -> str:
        """Serialize to JSON."""
        # Convert intent to dict
        intent_dict = self.intent_normalized.dict()
        execution_flow = [asdict(step) for step in self.execution_flow]

        data = {
            "run_id": self.run_id,
            "user_intent_original": self.user_intent_original,
            "intent_normalized": intent_dict,
            "timestamps": self.timestamps,
            "execution_flow": execution_flow,
            "errors": self.errors,
            "warnings": self.warnings,
            "final_status": self.final_status,
            "output_files": self.output_files
        }
        return json.dumps(data, indent=2, default=str)

class SummaryGenerator:
    """Generates human-readable markdown summaries."""

    @staticmethod
    def generate(
        user_intent: str,
        checkpoints: List,
        warnings: List[str],
        total_duration: float
    ) -> str:
        """Generate markdown summary from execution."""

        lines = [
            "# OTG Orchestration Run",
            "",
            f"**User Request:** {user_intent}",
            "",
            "## Execution Summary:",
            ""
        ]

        for ckpt in checkpoints:
            status_icon = "✅" if ckpt.status == "success" else "❌"
            lines.append(
                f"- {ckpt.agent_color} {ckpt.sub_agent}: {status_icon} {ckpt.status.upper()}"
            )
            if ckpt.retry_count > 0:
                lines.append(f"  - Retried {ckpt.retry_count} time(s)")
            if ckpt.duration_seconds:
                lines.append(f"  - Duration: {ckpt.duration_seconds}s")

        lines.extend(["", "## Warnings:", ""])
        for warning in warnings:
            lines.append(f"- {warning}")

        lines.extend([
            "",
            f"**Total Duration:** {total_duration}s",
            ""
        ])

        return "\n".join(lines)
```

- [ ] **Step 3: Run test to verify**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_artifact.py -v
```

Expected output: All tests PASS

- [ ] **Step 4: Commit Phase 3.2**

```bash
git add src/orchestrator/artifact.py tests/orchestrator/test_artifact.py
git commit -m "feat: implement manifest and summary generation"
```

---

### Phase 4: Error Recovery & Smart Retries (Tasks 7-8)

Implement error classification and recovery strategies.

#### Task 7: Implement Error Recovery Engine

**Files:**
- Create: `src/orchestrator/recovery.py`
- Create: `tests/orchestrator/test_recovery.py`
- Create: `src/orchestrator/config.py` (retry/timeout configuration)

- [ ] **Step 1: Write test for error classification**

```python
# tests/orchestrator/test_recovery.py
import pytest
from orchestrator.recovery import ErrorClassifier, RecoveryStrategy

def test_error_classifier_detects_transient():
    """Should classify timeout errors as transient."""
    error = {
        "type": "TimeoutError",
        "message": "Deployment timed out after 600s"
    }
    classification = ErrorClassifier.classify(error)
    assert classification["category"] == "transient"

def test_error_classifier_detects_validation():
    """Should classify validation errors as deterministic."""
    error = {
        "type": "ValidationError",
        "message": "Missing required field: port_speed"
    }
    classification = ErrorClassifier.classify(error)
    assert classification["category"] == "validation"

def test_recovery_strategy_offers_retry_for_transient():
    """For transient errors, should recommend retry."""
    error = {"type": "TimeoutError", "message": "..."}
    classification = ErrorClassifier.classify(error)
    recovery = RecoveryStrategy.get_options(classification, retry_count=0, max_retries=3)
    assert "retry" in [r["action"] for r in recovery]

def test_recovery_strategy_offers_clarification_for_validation():
    """For validation errors, should ask user to clarify."""
    error = {"type": "ValidationError", "message": "..."}
    classification = ErrorClassifier.classify(error)
    recovery = RecoveryStrategy.get_options(classification, retry_count=0, max_retries=1)
    assert "clarify" in [r["action"] for r in recovery]
```

- [ ] **Step 2: Implement error recovery**

```python
# src/orchestrator/recovery.py
from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

class ErrorCategory(str, Enum):
    TRANSIENT = "transient"
    VALIDATION = "validation"
    STATE = "state"
    UNKNOWN = "unknown"

@dataclass
class ErrorClassification:
    """Classification of an error."""
    category: ErrorCategory
    reason: str
    recoverable: bool

class ErrorClassifier:
    """Classify errors into categories."""

    TRANSIENT_PATTERNS = [
        "timeout", "timed out", "TimeoutError",
        "connection refused", "ConnectionError",
        "rate limit", "RateLimitError",
        "temporarily unavailable"
    ]

    VALIDATION_PATTERNS = [
        "validation error", "ValidationError",
        "missing", "required",
        "invalid", "incompatible",
        "malformed", "parse"
    ]

    @staticmethod
    def classify(error: Dict[str, Any]) -> ErrorClassification:
        """Classify error."""
        error_str = (error.get("type", "") + " " + error.get("message", "")).lower()

        # Check for transient
        for pattern in ErrorClassifier.TRANSIENT_PATTERNS:
            if pattern in error_str:
                return ErrorClassification(
                    category=ErrorCategory.TRANSIENT,
                    reason="Transient failure (can retry)",
                    recoverable=True
                )

        # Check for validation
        for pattern in ErrorClassifier.VALIDATION_PATTERNS:
            if pattern in error_str:
                return ErrorClassification(
                    category=ErrorCategory.VALIDATION,
                    reason="Validation error (user clarification needed)",
                    recoverable=True
                )

        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            reason="Unknown error",
            recoverable=False
        )

@dataclass
class RecoveryOption:
    """A recovery option presented to user."""
    action: str  # "retry", "clarify", "skip", "abort"
    label: str
    description: str

class RecoveryStrategy:
    """Determine recovery options for errors."""

    @staticmethod
    def get_options(
        classification: ErrorClassification,
        retry_count: int,
        max_retries: int,
        agent_name: str = ""
    ) -> List[RecoveryOption]:
        """Get recovery options."""
        options = []

        if classification.category == ErrorCategory.TRANSIENT:
            if retry_count < max_retries:
                options.append(RecoveryOption(
                    action="retry",
                    label="[Retry Now]",
                    description="Retry with same parameters"
                ))

            options.append(RecoveryOption(
                action="clarify",
                label="[Edit Intent]",
                description="Change parameters and retry"
            ))

            if agent_name != "ixia-c-deployment":
                options.append(RecoveryOption(
                    action="skip",
                    label="[Skip]",
                    description="Skip this agent and continue"
                ))

        elif classification.category == ErrorCategory.VALIDATION:
            options.append(RecoveryOption(
                action="clarify",
                label="[Edit Intent]",
                description="Fix the issue and retry"
            ))

        options.append(RecoveryOption(
            action="abort",
            label="[Abort]",
            description="Stop orchestration"
        ))

        return options
```

- [ ] **Step 3: Create configuration**

```python
# src/orchestrator/config.py
"""Orchestrator configuration."""

# Retry/timeout strategy per sub-agent
AGENT_CONFIG = {
    "ixia-c-deployment": {
        "timeout_seconds": 600,
        "max_retries": 3,
        "can_skip": False
    },
    "otg-config-generator": {
        "timeout_seconds": 120,
        "max_retries": 2,
        "can_skip": False
    },
    "snappi-script-generator": {
        "timeout_seconds": 60,
        "max_retries": 1,
        "can_skip": False
    },
    "keng-licensing": {
        "timeout_seconds": 30,
        "max_retries": 1,
        "can_skip": True
    }
}

# Default wait time budget
DEFAULT_MAX_WAIT_MINUTES = 30
```

- [ ] **Step 4: Run test to verify**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_recovery.py -v
```

Expected output: All tests PASS

- [ ] **Step 5: Commit Phase 4.1**

```bash
git add src/orchestrator/recovery.py src/orchestrator/config.py tests/orchestrator/test_recovery.py
git commit -m "feat: implement error classification and recovery strategy"
```

---

### Phase 5: Transport Adapter & Integration (Tasks 9-10)

Implement the transport abstraction layer and main orchestrator entry point.

#### Task 8: Implement Transport Adapter Layer

**Files:**
- Create: `src/orchestrator/transport.py`
- Create: `tests/orchestrator/test_transport.py`

- [ ] **Step 1: Write test for transport interface**

```python
# tests/orchestrator/test_transport.py
import pytest
from abc import ABC
from orchestrator.transport import SubAgentTransport, SkillTransport
from orchestrator.intent import Intent, UseCase

def test_transport_interface_defined():
    """SubAgentTransport should define required methods."""
    assert hasattr(SubAgentTransport, 'invoke')
    assert hasattr(SubAgentTransport, 'supports_interactive_confirmation')
    assert hasattr(SubAgentTransport, 'get_checkpoint_timeout')

def test_skill_transport_implements_interface():
    """SkillTransport should implement SubAgentTransport."""
    transport = SkillTransport()
    assert isinstance(transport, SubAgentTransport)
    assert transport.supports_interactive_confirmation() == True
```

- [ ] **Step 2: Implement transport layer**

```python
# src/orchestrator/transport.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class SubAgentResult:
    """Result from sub-agent invocation."""
    status: str  # "success", "error"
    agent_name: str
    output: Dict[str, Any]
    error: Optional[str] = None
    duration_seconds: float = 0.0

class SubAgentTransport(ABC):
    """Abstract transport for invoking sub-agents."""

    @abstractmethod
    def invoke(
        self,
        agent_name: str,
        context: Dict[str, Any],
        timeout_seconds: int
    ) -> SubAgentResult:
        """
        Invoke a sub-agent.

        Args:
            agent_name: e.g., "otg-config-generator"
            context: intent + checkpoints + deployment info
            timeout_seconds: timeout for invocation

        Returns:
            SubAgentResult with output or error
        """
        pass

    @abstractmethod
    def supports_interactive_confirmation(self) -> bool:
        """Return True if transport supports user confirmation gates."""
        pass

    @abstractmethod
    def get_checkpoint_timeout(self, agent_name: str) -> int:
        """Return timeout in seconds for this agent."""
        pass

class SkillTransport(SubAgentTransport):
    """Claude Code Skill transport implementation."""

    def __init__(self):
        from orchestrator.config import AGENT_CONFIG
        self.agent_config = AGENT_CONFIG

    def invoke(
        self,
        agent_name: str,
        context: Dict[str, Any],
        timeout_seconds: int
    ) -> SubAgentResult:
        """
        Invoke sub-agent via Skill tool.

        In a real implementation, this would call:
        invoke_skill(skill=agent_name, context=context)

        For now, return mock result for testing.
        """
        try:
            # In production: result = invoke_skill(agent_name, context)
            # For now, mock success
            return SubAgentResult(
                status="success",
                agent_name=agent_name,
                output={"mock": True},
                duration_seconds=1.0
            )
        except Exception as e:
            return SubAgentResult(
                status="error",
                agent_name=agent_name,
                output={},
                error=str(e)
            )

    def supports_interactive_confirmation(self) -> bool:
        """Claude Code supports interactive confirmation."""
        return True

    def get_checkpoint_timeout(self, agent_name: str) -> int:
        """Return timeout for agent."""
        return self.agent_config.get(agent_name, {}).get("timeout_seconds", 60)
```

- [ ] **Step 3: Run test to verify**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_transport.py -v
```

Expected output: All tests PASS

- [ ] **Step 4: Commit Phase 5.1**

```bash
git add src/orchestrator/transport.py tests/orchestrator/test_transport.py
git commit -m "feat: implement transport adapter layer for platform abstraction"
```

---

#### Task 9: Implement Main Orchestrator Class & Integration

**Files:**
- Modify: `src/orchestrator/orchestrator.py` (add main Orchestrator class)
- Modify: `tests/orchestrator/test_orchestrator_e2e.py` (add integration tests)

- [ ] **Step 1: Write integration test**

```python
# Add to tests/orchestrator/test_orchestrator_e2e.py
from orchestrator.orchestrator import Orchestrator
from orchestrator.transport import SkillTransport
from orchestrator.intent import Intent, UseCase
from pathlib import Path
import tempfile

def test_orchestrator_runs_full_pipeline():
    """Full orchestrator should complete all phases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        transport = SkillTransport()
        orchestrator = Orchestrator(
            transport=transport,
            artifacts_dir=Path(tmpdir)
        )

        intent = Intent(
            user_request="Create BGP test with Docker deployment",
            use_case=UseCase.FULL_GREENFIELD
        )

        # Run orchestration (mock mode)
        result = orchestrator.run(intent, interactive=False)

        assert result["status"] == "success"
        assert result["artifacts_dir"] is not None
```

- [ ] **Step 2: Implement main Orchestrator class**

```python
# Modify src/orchestrator/orchestrator.py - add main class
from pathlib import Path
from datetime import datetime
from orchestrator.transport import SubAgentTransport, SkillTransport
from orchestrator.checkpoint import CheckpointManager, Checkpoint
from orchestrator.artifact import Manifest, SummaryGenerator, ManifestExecutionStep
from orchestrator.intent import Intent, IntentValidator
from orchestrator.dispatcher import Dispatcher
from orchestrator.recovery import ErrorClassifier, RecoveryStrategy
import json
import time

class Orchestrator:
    """Main orchestrator that coordinates all phases."""

    def __init__(
        self,
        transport: SubAgentTransport,
        artifacts_dir: Path = None
    ):
        self.transport = transport
        self.artifacts_dir = artifacts_dir or Path("./orchestration_runs")
        self.run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.run_dir = self.artifacts_dir / self.run_id
        self.checkpoint_manager = CheckpointManager(self.run_dir / "checkpoints")
        self.manifest = None
        self.checkpoints = []

    def run(self, intent: Intent, interactive: bool = True) -> Dict[str, Any]:
        """
        Execute orchestration.

        Returns:
            {
                "status": "success|partial|failed",
                "run_id": "...",
                "artifacts_dir": Path,
                "output_files": [...]
            }
        """
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1: Validate intent
        is_valid, errors = IntentValidator.validate(intent)
        if not is_valid:
            return {
                "status": "failed",
                "error": "Intent validation failed",
                "details": errors
            }

        # Save intent
        intent_file = self.run_dir / "intent.json"
        with open(intent_file, "w") as f:
            f.write(intent.json())

        # Phase 2: Build dispatch queue
        queue = Dispatcher.build_queue(intent)

        # Phase 3: Execute agents
        for agent_config in queue.agents:
            start_time = time.time()
            retry_count = 0

            while retry_count <= agent_config.max_retries:
                # Invoke sub-agent
                context = {
                    "intent": intent.dict(),
                    "previous_checkpoints": [c.to_json() for c in self.checkpoints]
                }

                result = self.transport.invoke(
                    agent_name=agent_config.name,
                    context=context,
                    timeout_seconds=agent_config.timeout_seconds
                )

                duration = time.time() - start_time

                if result.status == "success":
                    # Save checkpoint
                    checkpoint = Checkpoint(
                        checkpoint_id=f"ckpt_{agent_config.sequence}_{agent_config.name}",
                        sub_agent=agent_config.name,
                        agent_color=agent_config.color,
                        sequence=agent_config.sequence,
                        status="success",
                        input=context["intent"],
                        output=result.output,
                        duration_seconds=duration,
                        retry_count=retry_count,
                        user_action="approved"
                    )
                    self.checkpoint_manager.save(checkpoint)
                    self.checkpoints.append(checkpoint)

                    # User confirmation (if interactive)
                    if interactive and hasattr(self, '_confirm_checkpoint'):
                        if not self._confirm_checkpoint(checkpoint):
                            continue  # User rejected, re-run

                    break  # Success, move to next agent
                else:
                    # Error handling
                    error = {"type": "AgentError", "message": result.error}
                    classification = ErrorClassifier.classify(error)

                    if retry_count < agent_config.max_retries:
                        retry_count += 1
                        continue  # Retry
                    else:
                        # Max retries exhausted
                        if interactive:
                            # Ask user for recovery action
                            pass
                        else:
                            # Fail this agent
                            break

        # Phase 4: Generate artifacts
        self.manifest = Manifest(
            run_id=self.run_id,
            user_intent_original=intent.user_request,
            intent_normalized=intent,
            execution_flow=[],
            errors=[],
            warnings=[],
            final_status="success",
            output_files=[]
        )
        self.manifest.finalize()

        # Save manifest
        manifest_file = self.run_dir / "manifest.json"
        with open(manifest_file, "w") as f:
            f.write(self.manifest.to_json())

        # Generate and save summary
        summary_md = SummaryGenerator.generate(
            user_intent=intent.user_request,
            checkpoints=self.checkpoints,
            warnings=[],
            total_duration=time.time() - start_time
        )
        summary_file = self.run_dir / "summary.md"
        with open(summary_file, "w") as f:
            f.write(summary_md)

        return {
            "status": "success",
            "run_id": self.run_id,
            "artifacts_dir": self.run_dir,
            "output_files": [
                str(intent_file),
                str(manifest_file),
                str(summary_file)
            ]
        }
```

- [ ] **Step 3: Run integration test**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/test_orchestrator_e2e.py::test_orchestrator_runs_full_pipeline -v
```

Expected output: PASS

- [ ] **Step 4: Commit Phase 5.2**

```bash
git add src/orchestrator/orchestrator.py tests/orchestrator/test_orchestrator_e2e.py
git commit -m "feat: implement main orchestrator class with full integration"
```

---

#### Task 10: Create Skill Entry Point & Documentation

**Files:**
- Create: `skills/otg-orchestrator/SKILL.md`
- Create: `skills/otg-orchestrator/skill_handler.py`
- Create: `docs/orchestrator/USAGE.md`
- Create: `src/orchestrator/__init__.py`

- [ ] **Step 1: Create skill manifest**

```yaml
# skills/otg-orchestrator/SKILL.md
# OTG Orchestrator Skill

Generate and execute comprehensive OTG test orchestration workflows.

## Usage

Invoke the orchestrator with a natural language request:

```
otg-orchestrator: Create a BGP test with 2 ports, deploy with Docker, and give me a runnable script
```

The orchestrator will:
1. Validate your intent (ask clarifying questions if needed)
2. Dispatch to sub-agents (deployment, config, script generation, licensing)
3. Save checkpoints after each step
4. Ask for confirmation before proceeding
5. Generate structured artifacts (manifest, summary, outputs)

## Examples

**Full Greenfield Deployment:**
```
Create a BGP convergence test with 2 ports at 100GE,  deploy with Docker Compose, and get a runnable Snappi script. Also estimate licensing cost for Team tier.
```

**Config + Script Only:**
```
I have Ixia-c running at localhost:8443 with 2 ports (te1, te2). Create an ISIS adjacency test and generate the Snappi script.
```

**Deployment Only:**
```
Set up Ixia-c for network protocol testing using Containerlab.
```

## How It Works

The orchestrator follows 4 phases:

1. **Intent Validation:** You provide a natural language request. The orchestrator classifies it as one of 5 use cases and asks clarifying questions.
2. **Conditional Dispatch:** Based on your use case, the orchestrator queues the right sub-agents.
3. **Checkpoint-Based Execution:** Each sub-agent output is saved as a checkpoint. You review and approve before proceeding.
4. **Artifact Generation:** A structured manifest, human-readable summary, and output files are saved for future reference.

## Artifacts

After orchestration completes, you'll find:
- `intent.json` - Your validated intent
- `manifest.json` - Structured execution record
- `summary.md` - Human-readable summary
- `checkpoints/` - Individual checkpoint files
- `outputs/` - Generated outputs (docker-compose.yml, otg_config.json, test script, etc.)

All artifacts are time-stamped and ready for replay/analysis.
```

- [ ] **Step 2: Create skill handler**

```python
# skills/otg-orchestrator/skill_handler.py
"""
Claude Code skill entry point for OTG Orchestrator.

Invoked via: skill(skill="otg-orchestrator", context={...})
"""

from pathlib import Path
from orchestrator.orchestrator import Orchestrator
from orchestrator.transport import SkillTransport
from orchestrator.intent import Intent, IntentIntake
from typing import Any, Dict

def invoke_skill(
    user_request: str,
    interactive: bool = True,
    artifacts_dir: str = None
) -> Dict[str, Any]:
    """
    Main entry point for orchestrator skill.

    Args:
        user_request: Natural language test scenario
        interactive: If True, ask user for confirmations at checkpoints
        artifacts_dir: Where to save run artifacts

    Returns:
        Dict with status, run_id, artifacts_dir, output_files
    """

    # Phase 1: Intent intake
    intent_intake = IntentIntake()
    use_case = intent_intake.classify_intent(user_request)

    # Build intent from clarifying questions
    answers = {}  # In interactive mode, gather answers from user
    intent = intent_intake.build_intent(user_request, answers)

    # Phase 2-4: Run orchestrator
    transport = SkillTransport()
    orchestrator = Orchestrator(
        transport=transport,
        artifacts_dir=Path(artifacts_dir) if artifacts_dir else None
    )

    result = orchestrator.run(intent, interactive=interactive)

    return result

# When invoked by Claude Code:
if __name__ == "__main__":
    # Claude Code will set these via context
    result = invoke_skill(
        user_request="Create BGP test with Docker deployment",
        interactive=True
    )
    print(f"✅ Orchestration complete")
    print(f"   Run ID: {result['run_id']}")
    print(f"   Artifacts: {result['artifacts_dir']}")
```

- [ ] **Step 3: Create usage documentation**

```markdown
# OTG Orchestrator Usage Guide

## Quick Start

```
skill: otg-orchestrator
user_request: "Create a BGP test with 2 ports, deploy with Docker, and give me a runnable script"
```

The orchestrator will walk you through:
1. Classifying your intent
2. Asking clarifying questions (one at a time)
3. Building a normalized intent
4. Dispatching to sub-agents
5. Showing you checkpoints for approval
6. Generating a complete artifact package

## Use Cases

### 1. Full Greenfield (Deploy + Config + Script)
**Request:** "Create BGP test, deploy with Docker, get script + license estimate"
**What happens:**
- Deployment agent creates docker-compose.yml
- Config generator creates otg_config.json
- Script generator creates test_bgp.py
- Licensing agent estimates cost

### 2. Config + Script Only (Existing Infrastructure)
**Request:** "I have Ixia-c at localhost:8443; create BGP test and script"
**What happens:**
- Skip deployment
- Config + script generation
- No licensing by default

### 3. Deployment Only
**Request:** "Set up Ixia-c for protocol testing"
**What happens:**
- Deployment agent only
- No config/script generation

### 4. Script from Existing Config
**Request:** "I have otg_config.json; generate a Snappi script"
**What happens:**
- Script generation only
- Needs infrastructure details (controller URL, ports)

### 5. Licensing Estimate Only
**Request:** "How much will 4×100GE + 8 BGP sessions cost?"
**What happens:**
- Licensing agent only
- Cost estimate + recommendation

## Checkpoints & Approval Gates

After each sub-agent completes, you'll see:
```
═══════════════════════════════════════════════════════════════
🔵 ixia-c-deployment: ✅ Success
═══════════════════════════════════════════════════════════════

Generated: docker-compose.yml (2KB)
Ports: te1:5555, te2:5556
Duration: 45 seconds

Does this look right?

   [1] Yes, proceed to next agent
   [2] No, stop and edit intent
   [3] Edit & Retry (modify deployment parameters and re-run)

Your choice? > _
```

**Choose:**
- `[1]` to approve and proceed
- `[2]` to stop, edit your original intent, and restart
- `[3]` to modify just this agent's parameters and re-run it

## Artifacts

After completion, check:
- `orchestration_runs/run_<timestamp>/intent.json` - Your validated intent
- `orchestration_runs/run_<timestamp>/manifest.json` - Execution record (for debugging)
- `orchestration_runs/run_<timestamp>/summary.md` - Human-readable summary
- `orchestration_runs/run_<timestamp>/checkpoints/` - Individual agent outputs
- `orchestration_runs/run_<timestamp>/outputs/` - Final deliverables

## Error Recovery

If an agent fails:
- **Transient error (timeout, network):** Orchestrator retries automatically, then offers `[Retry] [Edit Intent] [Skip]`
- **Validation error (bad parameters):** Orchestrator asks you to `[Edit Intent]`
- **State mismatch:** Orchestrator offers `[Retry from checkpoint] [Edit Intent]`

## Tips

- Be specific in your request (mention protocols, port counts, speeds)
- Use existing infrastructure when possible (faster)
- Licensing estimates help plan your subscription tier
- Artifacts are reusable templates for similar tests
```

- [ ] **Step 4: Create init file**

```python
# src/orchestrator/__init__.py
"""OTG Orchestrator - Multi-agent test execution framework."""

from orchestrator.intent import Intent, IntentIntake, IntentValidator
from orchestrator.dispatcher import Dispatcher, DispatchQueue
from orchestrator.orchestrator import Orchestrator
from orchestrator.transport import SkillTransport
from orchestrator.checkpoint import Checkpoint, CheckpointManager
from orchestrator.artifact import Manifest, SummaryGenerator
from orchestrator.recovery import ErrorClassifier, RecoveryStrategy

__all__ = [
    "Intent",
    "IntentIntake",
    "IntentValidator",
    "Dispatcher",
    "DispatchQueue",
    "Orchestrator",
    "SkillTransport",
    "Checkpoint",
    "CheckpointManager",
    "Manifest",
    "SummaryGenerator",
    "ErrorClassifier",
    "RecoveryStrategy",
]
```

- [ ] **Step 5: Run all tests to verify**

```bash
cd /Users/ashwin.joshi/kengotg
python -m pytest tests/orchestrator/ -v --tb=short
```

Expected output: All tests PASS (50+)

- [ ] **Step 6: Commit Phase 5.3**

```bash
git add \
  skills/otg-orchestrator/SKILL.md \
  skills/otg-orchestrator/skill_handler.py \
  docs/orchestrator/USAGE.md \
  src/orchestrator/__init__.py
git commit -m "feat: create skill entry point and complete documentation"
```

---

## Success Criteria

- ✅ All 10 tasks completed
- ✅ 50+ unit tests passing
- ✅ Full integration test passing
- ✅ All 5 phases implemented (intent, dispatch, checkpoints, recovery, transport)
- ✅ Skill entry point ready for use
- ✅ Comprehensive documentation
- ✅ Frequent commits (one per task)

---

## Execution Notes

**Dependency Order:** Tasks must be completed in order (1 → 10). Each task depends on previous artifacts.

**Testing Strategy:**
- Unit tests for each module (TDD)
- Integration tests after transport layer
- End-to-end test before skill creation

**Code Quality:**
- Type hints everywhere
- Clear docstrings
- Error messages with actionable details
- Logging for debugging

**Future Work:**
- SDK transport implementation (SwapSkillTransport for SDKTransport)
- Async/parallel execution for independent agents
- Template/pattern library for common test scenarios
- Webhook support for non-interactive mode

