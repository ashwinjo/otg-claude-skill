"""
Tests for Orchestrator State Machine.

TDD approach: Define expected behavior before implementation.
Tests for state transitions and agent cycling through the orchestration pipeline.
"""
import pytest
from pathlib import Path
from src.orchestrator.orchestrator import OrchestratorState, OrchestratorStateMachine
from src.orchestrator.intent import Intent, UseCase
from src.orchestrator.dispatcher import Dispatcher


class TestOrchestratorState:
    """Test OrchestratorState enum definition."""

    def test_orchestrator_state_has_all_required_states(self):
        """OrchestratorState should have all 9 required states."""
        required_states = [
            "INTENT_INTAKE",
            "INTENT_VALIDATED",
            "DISPATCH_PHASE",
            "AGENT_INVOKED",
            "CHECKPOINT_SAVED",
            "USER_CONFIRMATION",
            "ERROR_RECOVERY",
            "ARTIFACTS_GENERATED",
            "COMPLETE",
        ]
        for state in required_states:
            assert hasattr(OrchestratorState, state)

    def test_orchestrator_state_values_are_strings(self):
        """OrchestratorState values should be strings."""
        assert isinstance(OrchestratorState.INTENT_INTAKE.value, str)
        assert isinstance(OrchestratorState.INTENT_VALIDATED.value, str)
        assert isinstance(OrchestratorState.COMPLETE.value, str)

    def test_orchestrator_state_enum_comparison(self):
        """OrchestratorState should support equality comparison."""
        assert OrchestratorState.INTENT_VALIDATED == OrchestratorState.INTENT_VALIDATED
        assert OrchestratorState.INTENT_VALIDATED != OrchestratorState.DISPATCH_PHASE


class TestOrchestratorStateMachineInit:
    """Test OrchestratorStateMachine initialization."""

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

    def test_state_machine_init_with_intent_and_queue(self):
        """StateMachine should initialize with intent and queue."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        assert sm.intent == intent
        assert sm.queue == queue

    def test_state_machine_starts_in_intent_validated_state(self):
        """StateMachine should start in INTENT_VALIDATED state."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        assert sm.current_state == OrchestratorState.INTENT_VALIDATED

    def test_state_machine_initializes_agent_index_to_zero(self):
        """StateMachine should start with agent_index = 0."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        assert sm.agent_index == 0

    def test_state_machine_initializes_checkpoint_count_to_zero(self):
        """StateMachine should start with checkpoint_count = 0."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        assert sm.checkpoint_count == 0


class TestOrchestratorStateMachineTransitions:
    """Test OrchestratorStateMachine state transitions."""

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

    def test_state_machine_transitions_from_intent_validated_to_dispatch(self):
        """State machine should transition from INTENT_VALIDATED to DISPATCH_PHASE on next()."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        assert sm.current_state == OrchestratorState.INTENT_VALIDATED
        sm.next()
        assert sm.current_state == OrchestratorState.DISPATCH_PHASE

    def test_state_machine_transitions_dispatch_to_agent_invoked(self):
        """State machine should transition from DISPATCH_PHASE to AGENT_INVOKED on next()."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        sm.next()  # INTENT_VALIDATED -> DISPATCH_PHASE
        assert sm.current_state == OrchestratorState.DISPATCH_PHASE
        sm.next()  # DISPATCH_PHASE -> AGENT_INVOKED
        assert sm.current_state == OrchestratorState.AGENT_INVOKED

    def test_state_machine_transitions_agent_invoked_to_checkpoint_saved(self):
        """State machine should transition from AGENT_INVOKED to CHECKPOINT_SAVED on next()."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        sm.next()  # INTENT_VALIDATED -> DISPATCH_PHASE
        sm.next()  # DISPATCH_PHASE -> AGENT_INVOKED
        assert sm.current_state == OrchestratorState.AGENT_INVOKED
        sm.next()  # AGENT_INVOKED -> CHECKPOINT_SAVED
        assert sm.current_state == OrchestratorState.CHECKPOINT_SAVED

    def test_state_machine_increments_checkpoint_count(self):
        """State machine should increment checkpoint_count when saving checkpoints."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        initial_count = sm.checkpoint_count
        sm.next()  # INTENT_VALIDATED -> DISPATCH_PHASE
        sm.next()  # DISPATCH_PHASE -> AGENT_INVOKED
        sm.next()  # AGENT_INVOKED -> CHECKPOINT_SAVED
        assert sm.checkpoint_count == initial_count + 1

    def test_state_machine_transitions_checkpoint_to_user_confirmation(self):
        """State machine should transition from CHECKPOINT_SAVED to USER_CONFIRMATION on next()."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        sm.next()  # INTENT_VALIDATED -> DISPATCH_PHASE
        sm.next()  # DISPATCH_PHASE -> AGENT_INVOKED
        sm.next()  # AGENT_INVOKED -> CHECKPOINT_SAVED
        assert sm.current_state == OrchestratorState.CHECKPOINT_SAVED
        sm.next()  # CHECKPOINT_SAVED -> USER_CONFIRMATION
        assert sm.current_state == OrchestratorState.USER_CONFIRMATION

    def test_state_machine_cycles_through_agents(self):
        """State machine should cycle through all agents in queue."""
        intent = self._build_config_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        # Config only should have 2 agents
        assert len(queue.agents) == 2

        # Initial state: INTENT_VALIDATED, agent_index=0
        assert sm.current_state == OrchestratorState.INTENT_VALIDATED
        assert sm.agent_index == 0

        # Cycle through agent 0 (otg-config-generator)
        sm.next()  # -> DISPATCH_PHASE
        sm.next()  # -> AGENT_INVOKED
        sm.next()  # -> CHECKPOINT_SAVED
        sm.next()  # -> USER_CONFIRMATION
        assert sm.agent_index == 0

        # Return to DISPATCH_PHASE, increment agent_index
        sm.next()  # -> DISPATCH_PHASE, agent_index becomes 1
        assert sm.current_state == OrchestratorState.DISPATCH_PHASE
        assert sm.agent_index == 1

        # Cycle through agent 1 (snappi-script-generator)
        sm.next()  # -> AGENT_INVOKED
        sm.next()  # -> CHECKPOINT_SAVED
        sm.next()  # -> USER_CONFIRMATION
        assert sm.agent_index == 1

        # Return to DISPATCH_PHASE, but we're at end of queue
        sm.next()  # -> ARTIFACTS_GENERATED or DISPATCH_PHASE
        assert sm.agent_index == 2 or sm.current_state == OrchestratorState.ARTIFACTS_GENERATED


class TestOrchestratorStateMachineGetCurrentAgent:
    """Test OrchestratorStateMachine.get_current_agent() method."""

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

    def test_get_current_agent_returns_correct_agent(self):
        """get_current_agent() should return the agent at current agent_index."""
        intent = self._build_config_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        # Should return first agent (index 0)
        agent = sm.get_current_agent()
        assert agent is not None
        assert agent.name == "otg-config-generator"
        assert agent.sequence == 0

    def test_get_current_agent_after_increment(self):
        """get_current_agent() should return correct agent after agent_index increment."""
        intent = self._build_config_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        # Manually increment agent_index
        sm.agent_index = 1
        agent = sm.get_current_agent()
        assert agent is not None
        assert agent.name == "snappi-script-generator"
        assert agent.sequence == 1

    def test_get_current_agent_returns_none_beyond_queue(self):
        """get_current_agent() should return None if agent_index is out of bounds."""
        intent = self._build_config_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        # Move beyond the queue (2 agents total)
        sm.agent_index = 2
        agent = sm.get_current_agent()
        assert agent is None


class TestOrchestratorStateMachineIsComplete:
    """Test OrchestratorStateMachine.is_complete() method."""

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

    def test_is_complete_returns_false_at_start(self):
        """is_complete() should return False at INTENT_VALIDATED state."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        assert sm.is_complete() is False

    def test_is_complete_returns_true_at_complete_state(self):
        """is_complete() should return True when current_state is COMPLETE."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        # Manually set to COMPLETE state
        sm.current_state = OrchestratorState.COMPLETE
        assert sm.is_complete() is True

    def test_is_complete_returns_false_in_dispatch_phase(self):
        """is_complete() should return False during DISPATCH_PHASE."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        sm.current_state = OrchestratorState.DISPATCH_PHASE
        assert sm.is_complete() is False


class TestOrchestratorStateMachineErrorRecovery:
    """Test OrchestratorStateMachine error recovery."""

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

    def test_set_error_recovery_transitions_to_error_recovery_state(self):
        """set_error_recovery() should transition to ERROR_RECOVERY state."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        sm.current_state = OrchestratorState.DISPATCH_PHASE
        sm.set_error_recovery()
        assert sm.current_state == OrchestratorState.ERROR_RECOVERY

    def test_set_error_recovery_can_be_called_from_any_state(self):
        """set_error_recovery() should work from any state."""
        intent = self._build_deployment_only_intent()
        queue = Dispatcher.build_queue(intent)
        sm = OrchestratorStateMachine(intent=intent, queue=queue)

        for state in [
            OrchestratorState.INTENT_VALIDATED,
            OrchestratorState.AGENT_INVOKED,
            OrchestratorState.CHECKPOINT_SAVED,
        ]:
            sm.current_state = state
            sm.set_error_recovery()
            assert sm.current_state == OrchestratorState.ERROR_RECOVERY


class TestOrchestratorE2E:
    """Integration tests for complete orchestrator pipeline execution."""

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

    def test_orchestrator_runs_full_pipeline(self, tmp_path):
        """Full orchestration should run through all phases successfully."""
        from src.orchestrator.transport import SkillTransport
        from src.orchestrator.orchestrator import Orchestrator

        transport = SkillTransport()
        orchestrator = Orchestrator(transport=transport, artifacts_dir=tmp_path)

        intent = self._build_deployment_only_intent()
        result = orchestrator.run(intent=intent, interactive=False)

        # Verify successful completion
        assert result["status"] == "success"
        assert "run_id" in result
        assert "artifacts_dir" in result
        assert "output_files" in result
        assert len(result["output_files"]) > 0

    def test_orchestrator_saves_artifacts(self, tmp_path):
        """Orchestrator should save intent, manifest, and summary artifacts."""
        from src.orchestrator.transport import SkillTransport
        from src.orchestrator.orchestrator import Orchestrator
        from pathlib import Path

        transport = SkillTransport()
        orchestrator = Orchestrator(transport=transport, artifacts_dir=tmp_path)

        intent = self._build_deployment_only_intent()
        result = orchestrator.run(intent=intent, interactive=False)

        # Verify artifacts exist
        run_dir = Path(result["artifacts_dir"])
        assert (run_dir / "intent.json").exists()
        assert (run_dir / "manifest.json").exists()
        assert (run_dir / "summary.md").exists()

    def test_orchestrator_returns_result_structure(self, tmp_path):
        """Orchestrator result should have correct structure."""
        from src.orchestrator.transport import SkillTransport
        from src.orchestrator.orchestrator import Orchestrator

        transport = SkillTransport()
        orchestrator = Orchestrator(transport=transport, artifacts_dir=tmp_path)

        intent = self._build_deployment_only_intent()
        result = orchestrator.run(intent=intent, interactive=False)

        # Verify result structure
        assert isinstance(result, dict)
        assert "status" in result
        assert "run_id" in result
        assert "artifacts_dir" in result
        assert "output_files" in result
        assert isinstance(result["output_files"], list)

    def test_orchestrator_with_multiple_agents(self, tmp_path):
        """Orchestrator should handle multiple agents in sequence."""
        from src.orchestrator.transport import SkillTransport
        from src.orchestrator.orchestrator import Orchestrator

        transport = SkillTransport()
        orchestrator = Orchestrator(transport=transport, artifacts_dir=tmp_path)

        intent = self._build_config_only_intent()
        result = orchestrator.run(intent=intent, interactive=False)

        # Verify successful completion
        assert result["status"] == "success"
        # Config-only should have 2 agents, so 2 checkpoints should be saved
        assert len(orchestrator.checkpoints) >= 1

    def test_orchestrator_creates_run_directory(self, tmp_path):
        """Orchestrator should create run directory with timestamp."""
        from src.orchestrator.transport import SkillTransport
        from src.orchestrator.orchestrator import Orchestrator

        transport = SkillTransport()
        orchestrator = Orchestrator(transport=transport, artifacts_dir=tmp_path)

        intent = self._build_deployment_only_intent()
        result = orchestrator.run(intent=intent, interactive=False)

        run_dir = Path(result["artifacts_dir"])
        assert run_dir.exists()
        assert run_dir.parent == tmp_path
        assert "run_" in run_dir.name

    def test_orchestrator_manifest_has_execution_flow(self, tmp_path):
        """Orchestrator manifest should capture execution flow."""
        from src.orchestrator.transport import SkillTransport
        from src.orchestrator.orchestrator import Orchestrator
        import json

        transport = SkillTransport()
        orchestrator = Orchestrator(transport=transport, artifacts_dir=tmp_path)

        intent = self._build_deployment_only_intent()
        result = orchestrator.run(intent=intent, interactive=False)

        # Load and verify manifest structure
        manifest_path = Path(result["artifacts_dir"]) / "manifest.json"
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)

        assert "run_id" in manifest_data
        assert "user_intent_original" in manifest_data
        assert "final_status" in manifest_data
        assert manifest_data["final_status"] == "success"

    def test_orchestrator_summary_is_valid_markdown(self, tmp_path):
        """Orchestrator summary should be valid markdown."""
        from src.orchestrator.transport import SkillTransport
        from src.orchestrator.orchestrator import Orchestrator

        transport = SkillTransport()
        orchestrator = Orchestrator(transport=transport, artifacts_dir=tmp_path)

        intent = self._build_deployment_only_intent()
        result = orchestrator.run(intent=intent, interactive=False)

        # Load and verify summary
        summary_path = Path(result["artifacts_dir"]) / "summary.md"
        with open(summary_path, "r") as f:
            summary_content = f.read()

        # Basic markdown validation
        assert "#" in summary_content  # Should have headers
        assert "Execution Summary" in summary_content or "Summary" in summary_content
