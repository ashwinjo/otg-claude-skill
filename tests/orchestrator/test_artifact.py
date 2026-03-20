"""
Tests for Manifest and Summary Generation.

TDD approach: Define expected behavior before implementation.
Tests for artifact generation including manifests and human-readable summaries.
"""
import json
import pytest
from datetime import datetime

from src.orchestrator.artifact import (
    ManifestExecutionStep,
    Manifest,
    SummaryGenerator,
)
from src.orchestrator.intent import (
    Intent,
    UseCase,
    Deployment,
    DeploymentMethod,
    Port,
    ScenarioSpec,
)


class TestManifestExecutionStep:
    """Test ManifestExecutionStep dataclass."""

    def test_manifest_execution_step_creation(self):
        """Create a basic execution step."""
        step = ManifestExecutionStep(
            sequence=1,
            sub_agent="deployment_agent",
            agent_color="blue",
            status="success",
            retry_count=0,
            duration_seconds=15.5,
            user_action=None,
            user_action_timestamp=None,
            first_attempt_error=None,
            warnings=[],
        )
        assert step.sequence == 1
        assert step.sub_agent == "deployment_agent"
        assert step.agent_color == "blue"
        assert step.status == "success"
        assert step.retry_count == 0
        assert step.duration_seconds == 15.5

    def test_manifest_execution_step_with_warnings(self):
        """Create execution step with warnings."""
        warnings = ["Port speed not validated", "Timeout near threshold"]
        step = ManifestExecutionStep(
            sequence=2,
            sub_agent="config_agent",
            agent_color="green",
            status="success",
            retry_count=0,
            duration_seconds=20.0,
            user_action=None,
            user_action_timestamp=None,
            first_attempt_error=None,
            warnings=warnings,
        )
        assert len(step.warnings) == 2
        assert "Port speed not validated" in step.warnings

    def test_manifest_execution_step_with_error(self):
        """Create execution step with error details."""
        step = ManifestExecutionStep(
            sequence=1,
            sub_agent="deployment_agent",
            agent_color="red",
            status="failed",
            retry_count=2,
            duration_seconds=45.0,
            user_action=None,
            user_action_timestamp=None,
            first_attempt_error="Connection timeout to Docker daemon",
            warnings=["Fallback to containerlab attempted"],
        )
        assert step.status == "failed"
        assert step.retry_count == 2
        assert step.first_attempt_error == "Connection timeout to Docker daemon"

    def test_manifest_execution_step_with_user_action(self):
        """Create execution step with user action."""
        step = ManifestExecutionStep(
            sequence=2,
            sub_agent="config_agent",
            agent_color="green",
            status="success",
            retry_count=0,
            duration_seconds=10.0,
            user_action="approved",
            user_action_timestamp="2025-03-19T14:30:45.123456Z",
            first_attempt_error=None,
            warnings=[],
        )
        assert step.user_action == "approved"
        assert step.user_action_timestamp == "2025-03-19T14:30:45.123456Z"


class TestManifest:
    """Test Manifest dataclass."""

    def test_manifest_creation_basic(self):
        """Create a basic manifest with required fields."""
        intent = Intent(
            use_case=UseCase.full_greenfield,
            test_scenario=ScenarioSpec(
                name="Test Scenario",
                description="Test scenario description",
                protocols=["BGP"],
                port_count=2,
            ),
            deployment=Deployment(
                method=DeploymentMethod.docker_compose,
                deployment_type="CP+DP",
                ports=[
                    Port(name="te1", speed="100GE"),
                    Port(name="te2", speed="100GE"),
                ],
            ),
        )

        manifest = Manifest(
            run_id="run-2025-03-19-001",
            user_intent_original="Deploy a test scenario with 2 ports",
            intent_normalized=intent,
            execution_flow=[],
            errors=[],
            warnings=[],
            final_status="success",
            output_files=[],
            timestamps={},
        )

        assert manifest.run_id == "run-2025-03-19-001"
        assert manifest.user_intent_original == "Deploy a test scenario with 2 ports"
        assert manifest.final_status == "success"
        assert manifest.intent_normalized == intent

    def test_manifest_post_init_sets_start_timestamp(self):
        """__post_init__ should set initial_timestamp in timestamps."""
        intent = Intent(
            use_case=UseCase.licensing_only,
            licensing={"port_count": 2, "port_speed": "100GE"},
        )

        manifest = Manifest(
            run_id="run-test",
            user_intent_original="Check licensing",
            intent_normalized=intent,
            execution_flow=[],
            errors=[],
            warnings=[],
            final_status="in_progress",
            output_files=[],
            timestamps={},
        )

        assert "initial_timestamp" in manifest.timestamps
        assert manifest.timestamps["initial_timestamp"] is not None

    def test_manifest_finalize_sets_end_timestamp(self):
        """finalize() should set end_timestamp and update final_status."""
        intent = Intent(
            use_case=UseCase.licensing_only,
            licensing={"port_count": 2, "port_speed": "100GE"},
        )

        manifest = Manifest(
            run_id="run-test",
            user_intent_original="Check licensing",
            intent_normalized=intent,
            execution_flow=[],
            errors=[],
            warnings=[],
            final_status="in_progress",
            output_files=[],
            timestamps={},
        )

        initial_ts = manifest.timestamps.get("initial_timestamp")
        manifest.finalize("success")

        assert manifest.final_status == "success"
        assert "end_timestamp" in manifest.timestamps
        assert manifest.timestamps["end_timestamp"] is not None
        assert manifest.timestamps["initial_timestamp"] == initial_ts

    def test_manifest_to_json_serialization(self):
        """to_json() should serialize manifest to valid JSON."""
        intent = Intent(
            use_case=UseCase.full_greenfield,
            test_scenario=ScenarioSpec(
                name="BGP Test",
                description="BGP convergence test",
                protocols=["BGP"],
                port_count=2,
            ),
            deployment=Deployment(
                method=DeploymentMethod.docker_compose,
                deployment_type="CP+DP",
                ports=[Port(name="te1", speed="100GE")],
            ),
        )

        step = ManifestExecutionStep(
            sequence=1,
            sub_agent="deployment_agent",
            agent_color="blue",
            status="success",
            retry_count=0,
            duration_seconds=15.0,
            user_action=None,
            user_action_timestamp=None,
            first_attempt_error=None,
            warnings=[],
        )

        manifest = Manifest(
            run_id="run-001",
            user_intent_original="Deploy test scenario",
            intent_normalized=intent,
            execution_flow=[step],
            errors=[],
            warnings=["Minor warning"],
            final_status="success",
            output_files=["/path/to/config.yaml"],
            timestamps={},
        )

        manifest.finalize("success")
        json_str = manifest.to_json()

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["run_id"] == "run-001"
        assert data["final_status"] == "success"
        assert len(data["execution_flow"]) == 1
        assert data["execution_flow"][0]["sequence"] == 1

    def test_manifest_with_execution_flow(self):
        """Manifest should track execution flow steps."""
        intent = Intent(
            use_case=UseCase.full_greenfield,
            test_scenario=ScenarioSpec(
                name="Test",
                description="Test",
                protocols=["BGP"],
                port_count=2,
            ),
            deployment=Deployment(
                method=DeploymentMethod.docker_compose,
                deployment_type="CP+DP",
                ports=[Port(name="te1", speed="100GE")],
            ),
        )

        steps = [
            ManifestExecutionStep(
                sequence=1,
                sub_agent="deployment_agent",
                agent_color="blue",
                status="success",
                retry_count=0,
                duration_seconds=10.0,
                user_action=None,
                user_action_timestamp=None,
                first_attempt_error=None,
                warnings=[],
            ),
            ManifestExecutionStep(
                sequence=2,
                sub_agent="config_agent",
                agent_color="green",
                status="success",
                retry_count=0,
                duration_seconds=15.0,
                user_action=None,
                user_action_timestamp=None,
                first_attempt_error=None,
                warnings=[],
            ),
        ]

        manifest = Manifest(
            run_id="run-001",
            user_intent_original="Deploy test",
            intent_normalized=intent,
            execution_flow=steps,
            errors=[],
            warnings=[],
            final_status="success",
            output_files=[],
            timestamps={},
        )

        assert len(manifest.execution_flow) == 2
        assert manifest.execution_flow[0].sequence == 1
        assert manifest.execution_flow[1].sequence == 2

    def test_manifest_with_errors_and_warnings(self):
        """Manifest should track errors and warnings."""
        intent = Intent(
            use_case=UseCase.licensing_only,
            licensing={"port_count": 2, "port_speed": "100GE"},
        )

        manifest = Manifest(
            run_id="run-failed",
            user_intent_original="Check license",
            intent_normalized=intent,
            execution_flow=[],
            errors=["License validation failed: expired tier"],
            warnings=["License tier downgraded", "Session count reduced"],
            final_status="failed",
            output_files=[],
            timestamps={},
        )

        assert len(manifest.errors) == 1
        assert "License validation failed" in manifest.errors[0]
        assert len(manifest.warnings) == 2


class TestSummaryGenerator:
    """Test SummaryGenerator class."""

    def test_summary_generator_creates_markdown(self):
        """SummaryGenerator should create readable markdown summary."""
        intent = Intent(
            use_case=UseCase.full_greenfield,
            test_scenario=ScenarioSpec(
                name="BGP Convergence Test",
                description="Test BGP convergence with 2 ports",
                protocols=["BGP"],
                port_count=2,
            ),
            deployment=Deployment(
                method=DeploymentMethod.docker_compose,
                deployment_type="CP+DP",
                ports=[
                    Port(name="te1", speed="100GE"),
                    Port(name="te2", speed="100GE"),
                ],
            ),
        )

        checkpoints = [
            {
                "checkpoint_id": "cp-001",
                "sub_agent": "deployment_agent",
                "status": "success",
                "duration_seconds": 15.5,
            },
            {
                "checkpoint_id": "cp-002",
                "sub_agent": "config_agent",
                "status": "success",
                "duration_seconds": 20.0,
            },
        ]

        summary = SummaryGenerator.generate(
            user_intent="Deploy BGP Convergence Test scenario with 2 ports",
            checkpoints=checkpoints,
            warnings=[],
            total_duration=35.5,
        )

        assert isinstance(summary, str)
        assert "BGP Convergence Test" in summary
        assert "deployment_agent" in summary
        assert "config_agent" in summary

    def test_summary_includes_status_icons(self):
        """Summary should include status icons (✅ ❌) for each step."""
        checkpoints = [
            {"checkpoint_id": "cp-001", "sub_agent": "agent_a", "status": "success"},
            {"checkpoint_id": "cp-002", "sub_agent": "agent_b", "status": "failed"},
        ]

        summary = SummaryGenerator.generate(
            user_intent="Test intent",
            checkpoints=checkpoints,
            warnings=[],
            total_duration=30.0,
        )

        # Should have success and failure icons
        assert "✅" in summary or "success" in summary.lower()
        assert "❌" in summary or "failed" in summary.lower()

    def test_summary_includes_warnings(self):
        """Summary should include warnings section if provided."""
        checkpoints = [
            {"checkpoint_id": "cp-001", "sub_agent": "agent_a", "status": "success"}
        ]
        warnings = ["Port speed not validated", "Timeout near threshold"]

        summary = SummaryGenerator.generate(
            user_intent="Test intent",
            checkpoints=checkpoints,
            warnings=warnings,
            total_duration=15.0,
        )

        assert "Port speed not validated" in summary
        assert "Timeout near threshold" in summary

    def test_summary_includes_duration(self):
        """Summary should include total execution duration."""
        checkpoints = [
            {"checkpoint_id": "cp-001", "sub_agent": "agent_a", "status": "success"}
        ]

        summary = SummaryGenerator.generate(
            user_intent="Test intent",
            checkpoints=checkpoints,
            warnings=[],
            total_duration=42.5,
        )

        assert "42.5" in summary or "duration" in summary.lower()

    def test_summary_no_warnings(self):
        """Summary should handle empty warnings list gracefully."""
        checkpoints = [
            {"checkpoint_id": "cp-001", "sub_agent": "agent_a", "status": "success"}
        ]

        summary = SummaryGenerator.generate(
            user_intent="Test intent",
            checkpoints=checkpoints,
            warnings=[],
            total_duration=10.0,
        )

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summary_with_next_steps(self):
        """Summary should include next steps section."""
        checkpoints = [
            {"checkpoint_id": "cp-001", "sub_agent": "agent_a", "status": "success"}
        ]

        summary = SummaryGenerator.generate(
            user_intent="Deploy test scenario",
            checkpoints=checkpoints,
            warnings=[],
            total_duration=20.0,
        )

        # Should have next steps section (case-insensitive)
        assert "next" in summary.lower() or "steps" in summary.lower()

    def test_summary_handles_empty_checkpoints(self):
        """Summary should handle empty checkpoints list."""
        summary = SummaryGenerator.generate(
            user_intent="Test intent",
            checkpoints=[],
            warnings=[],
            total_duration=0.0,
        )

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summary_generator_format_is_markdown(self):
        """Summary format should be readable markdown."""
        checkpoints = [
            {"checkpoint_id": "cp-001", "sub_agent": "deployment", "status": "success"}
        ]

        summary = SummaryGenerator.generate(
            user_intent="Deploy infrastructure",
            checkpoints=checkpoints,
            warnings=["Warning 1"],
            total_duration=25.0,
        )

        # Should have markdown elements
        assert (
            "#" in summary  # Heading markers
            or "=" in summary  # Alternative heading markers
            or len(summary) > 50  # At least some substantive content
        )
