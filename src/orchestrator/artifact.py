"""
Artifact generation modules for manifests and human-readable summaries.

Provides:
- ManifestExecutionStep: Captures individual step details in execution flow
- Manifest: High-level execution record with metadata and flow
- SummaryGenerator: Creates human-readable markdown summaries
"""
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List

from .intent import Intent
from .utils import get_timestamp


@dataclass
class ManifestExecutionStep:
    """Captures details of a single execution step in the orchestration flow.

    Attributes:
        sequence: Step number in execution sequence (1-indexed)
        sub_agent: Name of the sub-agent that executed this step
        agent_color: Color/label for identifying the sub-agent (blue, green, red, etc.)
        status: Execution status ('success', 'partial_success', 'failed')
        retry_count: Number of retries performed for this step
        duration_seconds: Time taken to execute this step
        user_action: User intervention action ('approved', 'rejected', 'edit_and_retry')
        user_action_timestamp: ISO 8601 timestamp of user action
        first_attempt_error: Error from first attempt (used for retry tracking)
        warnings: List of non-fatal warnings during execution
    """

    sequence: int
    sub_agent: str
    agent_color: str
    status: str
    retry_count: int
    duration_seconds: float
    user_action: Optional[str]
    user_action_timestamp: Optional[str]
    first_attempt_error: Optional[str]
    warnings: List[str]


@dataclass
class Manifest:
    """High-level execution record capturing the full lifecycle of an orchestration run.

    Attributes:
        run_id: Unique identifier for this execution run
        user_intent_original: Original user request string (unprocessed)
        intent_normalized: Validated and normalized Intent object
        execution_flow: List of ManifestExecutionStep objects in order of execution
        errors: Fatal errors that occurred during execution
        warnings: Non-fatal warnings and advisories
        final_status: Overall outcome ('success', 'partial_success', 'failed')
        output_files: List of generated artifact file paths
        timestamps: Dict of significant timestamps (initial_timestamp, end_timestamp, etc.)
    """

    run_id: str
    user_intent_original: str
    intent_normalized: Intent
    execution_flow: List[ManifestExecutionStep]
    errors: List[str]
    warnings: List[str]
    final_status: str
    output_files: List[str]
    timestamps: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize manifest with starting timestamp."""
        if not self.timestamps:
            self.timestamps = {}
        self.timestamps["initial_timestamp"] = get_timestamp()

    def finalize(self, status: str) -> None:
        """Mark manifest as complete with final status and end timestamp.

        Args:
            status: Final status ('success', 'partial_success', 'failed')
        """
        self.final_status = status
        self.timestamps["end_timestamp"] = get_timestamp()

    def to_json(self) -> str:
        """Serialize manifest to JSON string.

        Returns:
            str: JSON representation of manifest with Pydantic Intent model
                 properly serialized

        Raises:
            TypeError: If manifest contains non-serializable objects
        """
        # Convert to dict for serialization
        manifest_dict = asdict(self)

        # Convert Pydantic Intent object to dict
        if hasattr(self.intent_normalized, "model_dump"):
            # Pydantic v2
            manifest_dict["intent_normalized"] = self.intent_normalized.model_dump()
        elif hasattr(self.intent_normalized, "dict"):
            # Pydantic v1
            manifest_dict["intent_normalized"] = self.intent_normalized.dict()
        else:
            # Fallback for plain dict
            manifest_dict["intent_normalized"] = dict(self.intent_normalized)

        return json.dumps(manifest_dict, indent=2)


class SummaryGenerator:
    """Generates human-readable markdown summaries of execution runs."""

    @staticmethod
    def generate(
        user_intent: str,
        checkpoints: List[Dict[str, Any]],
        warnings: List[str],
        total_duration: float,
    ) -> str:
        """Generate markdown summary of execution.

        Args:
            user_intent: Original user request string
            checkpoints: List of checkpoint dicts with at minimum:
                - checkpoint_id: unique identifier
                - sub_agent: agent name
                - status: execution status
                - duration_seconds: optional execution time
            warnings: List of warning messages
            total_duration: Total execution time in seconds

        Returns:
            str: Markdown formatted summary
        """
        lines = []

        # Header
        lines.append("# Execution Summary")
        lines.append("")

        # User request section
        lines.append("## User Request")
        lines.append(f"{user_intent}")
        lines.append("")

        # Execution summary with status icons
        lines.append("## Execution Flow")
        lines.append("")

        if not checkpoints:
            lines.append("No execution steps recorded.")
        else:
            for cp in checkpoints:
                status = cp.get("status", "unknown")
                sub_agent = cp.get("sub_agent", "unknown")
                checkpoint_id = cp.get("checkpoint_id", "")

                # Status icon
                status_icon = "✅" if status == "success" else "❌"
                duration_part = ""
                if "duration_seconds" in cp:
                    duration_part = f" ({cp['duration_seconds']:.1f}s)"

                lines.append(f"{status_icon} **{sub_agent}** {duration_part}")
                if checkpoint_id:
                    lines.append(f"   ID: {checkpoint_id}")

        lines.append("")

        # Warnings section
        if warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in warnings:
                lines.append(f"- {warning}")
            lines.append("")

        # Duration section
        lines.append("## Execution Details")
        lines.append(f"- **Total Duration**: {total_duration:.2f} seconds")
        lines.append("")

        # Next steps
        lines.append("## Next Steps")
        lines.append("")
        lines.append("1. Review the execution flow above")
        lines.append("2. Check warnings for any advisories")
        lines.append("3. Inspect output files for detailed results")
        lines.append("4. Contact support if issues persist")
        lines.append("")

        return "\n".join(lines)
