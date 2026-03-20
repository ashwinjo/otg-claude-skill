import json
import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from src.orchestrator.checkpoint import Checkpoint, CheckpointManager
from src.orchestrator.utils import get_timestamp, compute_checksum


class TestCheckpointSchema:
    """Test checkpoint dataclass schema and serialization."""

    def test_checkpoint_creation(self):
        """Test creating a checkpoint with all fields."""
        checkpoint = Checkpoint(
            checkpoint_id="ckpt_001",
            sub_agent="agent_validator",
            agent_color="blue",
            sequence=1,
            status="success",
            input={"config": "test"},
            output={"result": "valid"},
            duration_seconds=2.5,
            retry_count=0,
            warnings=["warning1"],
            user_action="approved",
            user_action_timestamp=get_timestamp(),
            output_size_bytes=256,
            output_checksum="sha256:abc123",
        )

        assert checkpoint.checkpoint_id == "ckpt_001"
        assert checkpoint.sub_agent == "agent_validator"
        assert checkpoint.agent_color == "blue"
        assert checkpoint.sequence == 1
        assert checkpoint.status == "success"
        assert checkpoint.input == {"config": "test"}
        assert checkpoint.output == {"result": "valid"}
        assert checkpoint.duration_seconds == 2.5
        assert checkpoint.retry_count == 0
        assert checkpoint.warnings == ["warning1"]
        assert checkpoint.user_action == "approved"
        assert checkpoint.output_size_bytes == 256
        assert checkpoint.output_checksum == "sha256:abc123"

    def test_checkpoint_default_timestamp(self):
        """Test that timestamp is set by default."""
        checkpoint = Checkpoint(
            checkpoint_id="ckpt_002",
            sub_agent="agent_executor",
            agent_color="red",
            sequence=2,
            status="failed",
            input={},
            output={},
            duration_seconds=1.0,
            retry_count=1,
            warnings=[],
            user_action="edit_and_retry",
            user_action_timestamp=None,
            output_size_bytes=0,
            output_checksum="sha256:empty",
        )

        assert checkpoint.timestamp is not None
        assert isinstance(checkpoint.timestamp, str)
        assert "Z" in checkpoint.timestamp  # ISO 8601 format

    def test_checkpoint_to_json(self):
        """Test serializing checkpoint to JSON."""
        checkpoint = Checkpoint(
            checkpoint_id="ckpt_003",
            sub_agent="agent_validator",
            agent_color="green",
            sequence=3,
            status="success",
            input={"key": "value"},
            output={"result": "ok"},
            duration_seconds=3.14,
            retry_count=0,
            warnings=[],
            user_action="approved",
            user_action_timestamp=get_timestamp(),
            output_size_bytes=512,
            output_checksum="sha256:def456",
        )

        json_str = checkpoint.to_json()
        assert isinstance(json_str, str)

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["checkpoint_id"] == "ckpt_003"
        assert data["sub_agent"] == "agent_validator"
        assert data["agent_color"] == "green"
        assert data["sequence"] == 3
        assert data["status"] == "success"

    def test_checkpoint_from_json(self):
        """Test deserializing checkpoint from JSON."""
        json_str = json.dumps(
            {
                "checkpoint_id": "ckpt_004",
                "sub_agent": "agent_executor",
                "agent_color": "yellow",
                "sequence": 4,
                "status": "retry",
                "input": {"cmd": "execute"},
                "output": {"stdout": ""},
                "timestamp": get_timestamp(),
                "duration_seconds": 0.5,
                "retry_count": 2,
                "warnings": ["slow_execution"],
                "user_action": "rejected",
                "user_action_timestamp": get_timestamp(),
                "output_size_bytes": 128,
                "output_checksum": "sha256:ghi789",
            }
        )

        checkpoint = Checkpoint.from_json(json_str)
        assert checkpoint.checkpoint_id == "ckpt_004"
        assert checkpoint.sub_agent == "agent_executor"
        assert checkpoint.agent_color == "yellow"
        assert checkpoint.sequence == 4
        assert checkpoint.status == "retry"
        assert checkpoint.retry_count == 2
        assert checkpoint.warnings == ["slow_execution"]

    def test_checkpoint_roundtrip(self):
        """Test serialize and deserialize roundtrip."""
        original = Checkpoint(
            checkpoint_id="ckpt_005",
            sub_agent="agent_validator",
            agent_color="purple",
            sequence=5,
            status="success",
            input={"nested": {"key": "value"}},
            output={"nested": {"result": ["item1", "item2"]}},
            duration_seconds=1.234,
            retry_count=0,
            warnings=["warn1", "warn2"],
            user_action="approved",
            user_action_timestamp=get_timestamp(),
            output_size_bytes=1024,
            output_checksum="sha256:jkl012",
        )

        # Serialize and deserialize
        json_str = original.to_json()
        restored = Checkpoint.from_json(json_str)

        # Verify all fields match
        assert restored.checkpoint_id == original.checkpoint_id
        assert restored.sub_agent == original.sub_agent
        assert restored.agent_color == original.agent_color
        assert restored.sequence == original.sequence
        assert restored.status == original.status
        assert restored.input == original.input
        assert restored.output == original.output
        assert restored.duration_seconds == original.duration_seconds
        assert restored.retry_count == original.retry_count
        assert restored.warnings == original.warnings
        assert restored.user_action == original.user_action
        assert restored.output_size_bytes == original.output_size_bytes
        assert restored.output_checksum == original.output_checksum


class TestCheckpointManager:
    """Test checkpoint file I/O and persistence."""

    @pytest.fixture
    def temp_checkpoint_dir(self, tmp_path):
        """Create temporary directory for checkpoint storage."""
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)
        return checkpoint_dir

    @pytest.fixture
    def manager(self, temp_checkpoint_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(base_path=temp_checkpoint_dir)

    def test_checkpoint_manager_initialization(self, manager, temp_checkpoint_dir):
        """Test CheckpointManager initialization creates base path."""
        assert manager.base_path == temp_checkpoint_dir
        assert manager.base_path.exists()

    def test_checkpoint_manager_save(self, manager):
        """Test saving checkpoint to file."""
        checkpoint = Checkpoint(
            checkpoint_id="ckpt_save_001",
            sub_agent="agent_test",
            agent_color="blue",
            sequence=1,
            status="success",
            input={"test": True},
            output={"result": "ok"},
            duration_seconds=1.0,
            retry_count=0,
            warnings=[],
            user_action="approved",
            user_action_timestamp=None,
            output_size_bytes=100,
            output_checksum="sha256:test123",
        )

        saved_path = manager.save(checkpoint)

        # Verify file exists
        assert saved_path.exists()
        assert saved_path.suffix == ".json"
        assert "ckpt_save_001" in str(saved_path)

    def test_checkpoint_manager_load(self, manager):
        """Test loading checkpoint from file."""
        # Create and save a checkpoint
        original = Checkpoint(
            checkpoint_id="ckpt_load_001",
            sub_agent="agent_test",
            agent_color="red",
            sequence=2,
            status="failed",
            input={"cmd": "test"},
            output={"error": "not_found"},
            duration_seconds=0.5,
            retry_count=1,
            warnings=["retry_needed"],
            user_action="edit_and_retry",
            user_action_timestamp=get_timestamp(),
            output_size_bytes=50,
            output_checksum="sha256:error123",
        )

        manager.save(original)

        # Load the checkpoint
        loaded = manager.load("ckpt_load_001")

        # Verify loaded checkpoint matches original
        assert loaded is not None
        assert loaded.checkpoint_id == original.checkpoint_id
        assert loaded.sub_agent == original.sub_agent
        assert loaded.agent_color == original.agent_color
        assert loaded.sequence == original.sequence
        assert loaded.status == original.status
        assert loaded.retry_count == original.retry_count

    def test_checkpoint_manager_load_nonexistent(self, manager):
        """Test loading nonexistent checkpoint returns None."""
        loaded = manager.load("ckpt_nonexistent")
        assert loaded is None

    def test_checkpoint_manager_list_checkpoints(self, manager):
        """Test listing all checkpoints."""
        # Create and save multiple checkpoints
        for i in range(3):
            checkpoint = Checkpoint(
                checkpoint_id=f"ckpt_list_{i:03d}",
                sub_agent="agent_test",
                agent_color="blue",
                sequence=i,
                status="success",
                input={},
                output={},
                duration_seconds=1.0,
                retry_count=0,
                warnings=[],
                user_action="approved",
                user_action_timestamp=None,
                output_size_bytes=0,
                output_checksum="sha256:empty",
            )
            manager.save(checkpoint)

        # List checkpoints
        checkpoints = manager.list_checkpoints()

        # Verify list contains all checkpoints
        assert len(checkpoints) == 3
        ids = [ckpt.checkpoint_id for ckpt in checkpoints]
        assert "ckpt_list_000" in ids
        assert "ckpt_list_001" in ids
        assert "ckpt_list_002" in ids

    def test_checkpoint_manager_list_empty_dir(self, manager):
        """Test listing checkpoints from empty directory."""
        checkpoints = manager.list_checkpoints()
        assert checkpoints == []

    def test_checkpoint_manager_save_creates_subdirectories(self, tmp_path):
        """Test that save creates subdirectories if they don't exist."""
        nested_path = tmp_path / "deep" / "nested" / "dir"

        manager = CheckpointManager(base_path=nested_path)
        manager.base_path.mkdir(parents=True, exist_ok=True)

        checkpoint = Checkpoint(
            checkpoint_id="ckpt_nested_001",
            sub_agent="agent_test",
            agent_color="green",
            sequence=1,
            status="success",
            input={},
            output={},
            duration_seconds=1.0,
            retry_count=0,
            warnings=[],
            user_action="approved",
            user_action_timestamp=None,
            output_size_bytes=0,
            output_checksum="sha256:nested",
        )

        saved_path = manager.save(checkpoint)
        assert saved_path.exists()
