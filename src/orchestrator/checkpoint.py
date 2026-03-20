"""Checkpoint schema and persistence layer for orchestrator execution state."""
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

from .utils import get_timestamp


@dataclass
class Checkpoint:
    """Schema for capturing execution state at a point in time.

    Attributes:
        checkpoint_id: Unique identifier for this checkpoint.
        sub_agent: Name of the sub-agent that created this checkpoint.
        agent_color: Color/label for the sub-agent (e.g., 'blue', 'red').
        sequence: Sequence number in the execution flow.
        status: Execution status ('success', 'failed', 'retry').
        input: Input data passed to the sub-agent.
        output: Output data returned by the sub-agent.
        timestamp: ISO 8601 timestamp when checkpoint was created.
        duration_seconds: Execution duration in seconds.
        retry_count: Number of retries performed.
        warnings: List of warning messages.
        user_action: User action on this checkpoint ('approved', 'rejected', 'edit_and_retry').
        user_action_timestamp: ISO 8601 timestamp of user action.
        output_size_bytes: Size of output in bytes.
        output_checksum: SHA256 checksum of output for integrity verification.
    """

    checkpoint_id: str
    sub_agent: str
    agent_color: str
    sequence: int
    status: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    duration_seconds: float
    retry_count: int
    warnings: List[str]
    user_action: str
    user_action_timestamp: Optional[str]
    output_size_bytes: int
    output_checksum: str
    timestamp: str = field(default_factory=get_timestamp)

    def to_json(self) -> str:
        """Serialize checkpoint to JSON string.

        Returns:
            str: JSON representation of checkpoint.
        """
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(json_str: str) -> "Checkpoint":
        """Deserialize checkpoint from JSON string.

        Args:
            json_str: JSON string representation of checkpoint.

        Returns:
            Checkpoint: Deserialized checkpoint instance.

        Raises:
            json.JSONDecodeError: If JSON is invalid.
            TypeError: If required fields are missing.
        """
        data = json.loads(json_str)
        return Checkpoint(**data)


class CheckpointManager:
    """Manages checkpoint persistence and retrieval.

    Stores checkpoints as JSON files in a configurable base directory.
    Provides save, load, and list operations.
    """

    def __init__(self, base_path: Path):
        """Initialize checkpoint manager.

        Args:
            base_path: Path to directory where checkpoints will be stored.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: Checkpoint) -> Path:
        """Save checkpoint to file.

        Filename format: {checkpoint_id}.json

        Args:
            checkpoint: Checkpoint instance to save.

        Returns:
            Path: Path to saved checkpoint file.
        """
        filepath = self.base_path / f"{checkpoint.checkpoint_id}.json"
        with open(filepath, "w") as f:
            f.write(checkpoint.to_json())
        return filepath

    def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from file.

        Args:
            checkpoint_id: ID of checkpoint to load.

        Returns:
            Checkpoint: Loaded checkpoint, or None if not found.
        """
        filepath = self.base_path / f"{checkpoint_id}.json"
        if not filepath.exists():
            return None

        with open(filepath, "r") as f:
            json_str = f.read()
        return Checkpoint.from_json(json_str)

    def list_checkpoints(self) -> List[Checkpoint]:
        """List all checkpoints in base directory.

        Returns:
            List[Checkpoint]: List of loaded checkpoints, sorted by sequence.
        """
        checkpoints = []
        for filepath in sorted(self.base_path.glob("*.json")):
            try:
                with open(filepath, "r") as f:
                    json_str = f.read()
                checkpoint = Checkpoint.from_json(json_str)
                checkpoints.append(checkpoint)
            except (json.JSONDecodeError, TypeError) as e:
                # Log and skip malformed checkpoints
                print(f"Warning: Failed to load checkpoint {filepath}: {e}")
                continue

        # Sort by sequence for consistent ordering
        checkpoints.sort(key=lambda c: c.sequence)
        return checkpoints
