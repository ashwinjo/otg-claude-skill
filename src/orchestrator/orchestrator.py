"""
Orchestrator State Machine Module.

Implements the orchestrator state machine that manages transitions through
the orchestration pipeline, including intent validation, dispatch, agent
invocation, checkpointing, and artifact generation.

Components:
- OrchestratorState: Enum of all 9 orchestration states
- OrchestratorStateMachine: State machine with transitions and agent tracking
- Orchestrator: Main orchestrator class that runs the full pipeline
"""
import time
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from src.orchestrator.intent import Intent, IntentValidator
from src.orchestrator.dispatcher import DispatchQueue, SubAgent, Dispatcher
from src.orchestrator.transport import SubAgentTransport
from src.orchestrator.checkpoint import Checkpoint, CheckpointManager
from src.orchestrator.artifact import Manifest, SummaryGenerator


class OrchestratorState(str, Enum):
    """Enumeration of orchestrator states in the execution pipeline.

    States represent transitions through the complete orchestration flow:
    - INTENT_INTAKE: Initial user input phase
    - INTENT_VALIDATED: Intent has been validated
    - DISPATCH_PHASE: Dispatching agents from queue
    - AGENT_INVOKED: Agent is currently being executed
    - CHECKPOINT_SAVED: Agent results have been checkpointed
    - USER_CONFIRMATION: Awaiting user confirmation on checkpoint
    - ERROR_RECOVERY: Error occurred, in recovery phase
    - ARTIFACTS_GENERATED: All agents complete, artifacts generated
    - COMPLETE: Orchestration complete
    """

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
    """State machine for orchestration pipeline execution.

    Manages state transitions and agent execution order through the dispatch queue.
    Tracks current state, active agent, and checkpoints saved during execution.

    Attributes:
        intent: The validated Intent object
        queue: The DispatchQueue with agents to execute
        current_state: Current state in the orchestration pipeline
        agent_index: Index of the current agent in the queue
        checkpoint_count: Number of checkpoints saved so far
    """

    def __init__(self, intent: Intent, queue: DispatchQueue):
        """Initialize orchestrator state machine.

        Args:
            intent: Validated Intent object specifying the orchestration goal
            queue: DispatchQueue with agents to execute in order
        """
        self.intent = intent
        self.queue = queue
        self.current_state = OrchestratorState.INTENT_VALIDATED
        self.agent_index = 0
        self.checkpoint_count = 0

    def next(self) -> None:
        """Transition to the next state based on current state.

        State transitions follow the orchestration flow:
        - INTENT_VALIDATED → DISPATCH_PHASE
        - DISPATCH_PHASE → AGENT_INVOKED (if agents remain)
        - DISPATCH_PHASE → ARTIFACTS_GENERATED (if all agents done)
        - AGENT_INVOKED → CHECKPOINT_SAVED
        - CHECKPOINT_SAVED → USER_CONFIRMATION
        - USER_CONFIRMATION → DISPATCH_PHASE (increment agent_index)
        - ARTIFACTS_GENERATED → COMPLETE

        Side effects:
        - Increments checkpoint_count when entering CHECKPOINT_SAVED
        - Increments agent_index when returning from USER_CONFIRMATION to DISPATCH_PHASE
        """
        if self.current_state == OrchestratorState.INTENT_VALIDATED:
            self.current_state = OrchestratorState.DISPATCH_PHASE

        elif self.current_state == OrchestratorState.DISPATCH_PHASE:
            # Check if there are agents remaining
            if self.agent_index < len(self.queue.agents):
                self.current_state = OrchestratorState.AGENT_INVOKED
            else:
                # All agents have been processed
                self.current_state = OrchestratorState.ARTIFACTS_GENERATED

        elif self.current_state == OrchestratorState.AGENT_INVOKED:
            self.checkpoint_count += 1
            self.current_state = OrchestratorState.CHECKPOINT_SAVED

        elif self.current_state == OrchestratorState.CHECKPOINT_SAVED:
            self.current_state = OrchestratorState.USER_CONFIRMATION

        elif self.current_state == OrchestratorState.USER_CONFIRMATION:
            # Increment agent index for next iteration
            self.agent_index += 1
            self.current_state = OrchestratorState.DISPATCH_PHASE

        elif self.current_state == OrchestratorState.ARTIFACTS_GENERATED:
            self.current_state = OrchestratorState.COMPLETE

        elif self.current_state == OrchestratorState.ERROR_RECOVERY:
            # Error recovery state can transition to DISPATCH_PHASE to retry
            # or COMPLETE to abort
            # For now, allow manual transition control
            pass

    def get_current_agent(self) -> Optional[SubAgent]:
        """Get the SubAgent at the current agent_index.

        Returns:
            SubAgent object if agent_index is within bounds, None otherwise.
        """
        if 0 <= self.agent_index < len(self.queue.agents):
            return self.queue.agents[self.agent_index]
        return None

    def set_error_recovery(self) -> None:
        """Transition to ERROR_RECOVERY state.

        Can be called from any state when an error occurs to allow
        recovery handling.
        """
        self.current_state = OrchestratorState.ERROR_RECOVERY

    def is_complete(self) -> bool:
        """Check if orchestration is complete.

        Returns:
            True if current_state is COMPLETE, False otherwise.
        """
        return self.current_state == OrchestratorState.COMPLETE


class Orchestrator:
    """Main orchestrator class that orchestrates all phases of execution.

    Manages the complete orchestration pipeline including:
    - Phase 1: Intent validation
    - Phase 2: Dispatch queue building
    - Phase 3: Agent invocation and checkpointing
    - Phase 4: Artifact generation

    Attributes:
        transport: SubAgentTransport for invoking sub-agents
        artifacts_dir: Directory where run artifacts are saved
        run_id: Unique identifier for this execution run
        run_dir: Directory for this specific run's artifacts
        checkpoint_manager: Manages checkpoint persistence
        manifest: Manifest object capturing execution details
        checkpoints: List of checkpoints saved during execution
    """

    def __init__(
        self,
        transport: SubAgentTransport,
        artifacts_dir: Path = None
    ):
        """Initialize orchestrator.

        Args:
            transport: SubAgentTransport for invoking sub-agents
            artifacts_dir: Optional directory for artifacts. Defaults to './orchestration_runs'
        """
        self.transport = transport
        self.artifacts_dir = artifacts_dir or Path("./orchestration_runs")
        self.run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.run_dir = self.artifacts_dir / self.run_id
        self.checkpoint_manager = CheckpointManager(self.run_dir / "checkpoints")
        self.manifest = None
        self.checkpoints: List[Checkpoint] = []

    def run(self, intent: Intent, interactive: bool = True) -> Dict[str, Any]:
        """Execute orchestration with all 4 phases.

        Args:
            intent: Intent object specifying the orchestration goal
            interactive: Whether to support interactive confirmations

        Returns:
            Dict containing:
                - status: "success" or "failed"
                - run_id: Unique identifier for this run
                - artifacts_dir: Path to run artifacts directory
                - output_files: List of generated artifact file paths
                - error: Error message if status is "failed"
        """
        try:
            # Phase 1: Validate intent
            validator = IntentValidator()
            validated_intent = validator.validate(intent)

            # Save intent
            self.run_dir.mkdir(parents=True, exist_ok=True)
            intent_file = self.run_dir / "intent.json"
            with open(intent_file, "w") as f:
                # Handle both Pydantic v1 and v2
                if hasattr(validated_intent, "model_dump"):
                    import json
                    f.write(json.dumps(validated_intent.model_dump(), indent=2))
                elif hasattr(validated_intent, "json"):
                    f.write(validated_intent.json())
                else:
                    import json
                    f.write(json.dumps(dict(validated_intent), indent=2))

            # Phase 2: Build dispatch queue
            queue = Dispatcher.build_queue(validated_intent)

            # Phase 3: Execute agents
            start_time = time.time()

            for agent_config in queue.agents:
                # Invoke sub-agent via transport
                # Convert intent to dict (handle both Pydantic v1 and v2)
                if hasattr(validated_intent, "model_dump"):
                    intent_dict = validated_intent.model_dump()
                else:
                    intent_dict = validated_intent.dict()

                context = {
                    "intent": intent_dict,
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
                        retry_count=0,
                        warnings=[],
                        user_action="approved",
                        user_action_timestamp=None,
                        output_size_bytes=len(str(result.output)),
                        output_checksum="",
                    )
                    self.checkpoint_manager.save(checkpoint)
                    self.checkpoints.append(checkpoint)

            # Phase 4: Generate artifacts
            total_duration = time.time() - start_time

            self.manifest = Manifest(
                run_id=self.run_id,
                user_intent_original=str(validated_intent),
                intent_normalized=validated_intent,
                execution_flow=[],
                errors=[],
                warnings=[],
                final_status="success",
                output_files=[]
            )
            self.manifest.finalize("success")

            # Save manifest
            manifest_file = self.run_dir / "manifest.json"
            with open(manifest_file, "w") as f:
                f.write(self.manifest.to_json())

            # Generate and save summary
            summary_md = SummaryGenerator.generate(
                user_intent=str(validated_intent),
                checkpoints=[{
                    "checkpoint_id": c.checkpoint_id,
                    "sub_agent": c.sub_agent,
                    "status": c.status,
                    "duration_seconds": c.duration_seconds
                } for c in self.checkpoints],
                warnings=[],
                total_duration=total_duration
            )
            summary_file = self.run_dir / "summary.md"
            with open(summary_file, "w") as f:
                f.write(summary_md)

            return {
                "status": "success",
                "run_id": self.run_id,
                "artifacts_dir": str(self.run_dir),
                "output_files": [
                    str(intent_file),
                    str(manifest_file),
                    str(summary_file)
                ]
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "run_id": self.run_id,
                "artifacts_dir": str(self.run_dir)
            }
