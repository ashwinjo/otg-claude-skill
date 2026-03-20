"""
Orchestrator State Machine Module.

Implements the orchestrator state machine that manages transitions through
the orchestration pipeline, including intent validation, dispatch, agent
invocation, checkpointing, and artifact generation.

Components:
- OrchestratorState: Enum of all 9 orchestration states
- OrchestratorStateMachine: State machine with transitions and agent tracking
"""
from enum import Enum
from typing import Optional
from src.orchestrator.intent import Intent
from src.orchestrator.dispatcher import DispatchQueue, SubAgent


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
