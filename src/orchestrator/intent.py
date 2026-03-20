"""
Intent Schema & Validation Module.

Defines the structure of user intent for orchestration, including:
- Intent: Top-level intent container
- UseCase: Classification of what user wants (full_greenfield, config_only, etc.)
- Deployment: Infrastructure deployment configuration
- Port: Port specification
- TestScenario: Test scenario description
- Licensing: License requirement specification
- Flags: Runtime flags and options
- IntentValidator: Validation and parsing logic

Following OTG Sub-Agent Orchestration Plan.
"""
import json
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# Enums
class UseCase(str, Enum):
    """Enumeration of supported orchestration use cases."""

    full_greenfield = "full_greenfield"
    config_only = "config_only"
    deployment_only = "deployment_only"
    script_only = "script_only"
    licensing_only = "licensing_only"


class DeploymentMethod(str, Enum):
    """Enumeration of supported deployment methods."""

    docker_compose = "docker_compose"
    containerlab = "containerlab"


class PortSpeed(str, Enum):
    """Enumeration of supported port speeds."""

    ge_1 = "1GE"
    ge_10 = "10GE"
    ge_25 = "25GE"
    ge_40 = "40GE"
    ge_100 = "100GE"
    ge_400 = "400GE"


class DeploymentType(str, Enum):
    """Enumeration of deployment types."""

    B2B = "B2B"
    CP_DP = "CP+DP"
    LAG = "LAG"


class LicenseTier(str, Enum):
    """Enumeration of license tiers."""

    Developer = "Developer"
    Team = "Team"
    System = "System"


# Models
class Port(BaseModel):
    """Port specification."""

    name: str = Field(..., description="Port name/identifier")
    speed: Optional[str] = Field(
        None, description="Port speed (1GE, 10GE, 25GE, 40GE, 100GE, 400GE)"
    )
    location: Optional[str] = Field(None, description="Port location after deployment")

    @field_validator("speed")
    @classmethod
    def validate_speed(cls, v: Optional[str]) -> Optional[str]:
        """Validate port speed against supported values."""
        if v is None:
            return v
        valid_speeds = ["1GE", "10GE", "25GE", "40GE", "100GE", "400GE"]
        if v not in valid_speeds:
            raise ValueError(
                f"Invalid port speed: {v}. Must be one of {valid_speeds}"
            )
        return v


class ScenarioSpec(BaseModel):
    """Test scenario specification."""

    name: str = Field(..., description="Name of the test scenario")
    description: str = Field(..., description="Description of the test scenario")
    protocols: List[str] = Field(
        default_factory=list, description="List of protocols (BGP, ISIS, LACP, etc.)"
    )
    port_count: int = Field(..., description="Number of ports needed")
    traffic_rate: Optional[str] = Field(None, description="Traffic rate (e.g., 1000 pps)")
    duration_seconds: Optional[int] = Field(
        None, description="Test duration in seconds"
    )

    @field_validator("port_count")
    @classmethod
    def validate_port_count(cls, v: int) -> int:
        """Validate port count is positive."""
        if v <= 0:
            raise ValueError("port_count must be a positive integer")
        return v


# Aliases for backward compatibility
Scenario = ScenarioSpec
TestScenario = ScenarioSpec


class Deployment(BaseModel):
    """Deployment configuration."""

    method: DeploymentMethod = Field(..., description="Deployment method")
    deployment_type: str = Field(..., description="Deployment type (B2B, CP+DP, LAG)")
    ports: List[Port] = Field(..., description="List of ports to deploy")

    @field_validator("deployment_type")
    @classmethod
    def validate_deployment_type(cls, v: str) -> str:
        """Validate deployment type."""
        valid_types = ["B2B", "CP+DP", "LAG"]
        if v not in valid_types:
            raise ValueError(f"Invalid deployment_type: {v}. Must be one of {valid_types}")
        return v

    @field_validator("ports")
    @classmethod
    def validate_ports_not_empty(cls, v: List[Port]) -> List[Port]:
        """Validate that at least one port is specified."""
        if not v or len(v) == 0:
            raise ValueError("At least one port must be specified in deployment")
        return v


class Infrastructure(BaseModel):
    """Infrastructure specification for existing deployments."""

    controller_url: str = Field(..., description="Controller URL (e.g., localhost:8443)")
    ports: Optional[List[Port]] = Field(None, description="List of available ports")


class Licensing(BaseModel):
    """Licensing specification."""

    port_count: int = Field(..., description="Number of ports")
    port_speed: str = Field(..., description="Port speed (1GE, 10GE, 25GE, 40GE, 100GE, 400GE)")
    protocols: Optional[List[str]] = Field(None, description="Protocols used")
    session_count: Optional[int] = Field(None, description="Number of sessions")
    license_tier: Optional[str] = Field(
        "Developer", description="License tier (Developer, Team, System)"
    )

    @field_validator("license_tier")
    @classmethod
    def validate_license_tier(cls, v: Optional[str]) -> Optional[str]:
        """Validate license tier."""
        if v is None:
            return v
        valid_tiers = ["Developer", "Team", "System"]
        if v not in valid_tiers:
            raise ValueError(
                f"Invalid license_tier: {v}. Must be one of {valid_tiers}"
            )
        return v


class Flags(BaseModel):
    """Runtime flags and options."""

    verbose: bool = Field(False, description="Enable verbose output")
    dry_run: bool = Field(False, description="Perform dry run without execution")
    skip_validation: bool = Field(False, description="Skip validation checks")
    interactive: bool = Field(False, description="Enable interactive prompts")


class Intent(BaseModel):
    """Top-level intent container for orchestration."""

    use_case: UseCase = Field(..., description="Use case classification")

    # Test scenario (required for greenfield, config_only; optional for others)
    test_scenario: Optional[ScenarioSpec] = Field(
        None, description="Test scenario specification"
    )

    # Deployment (required for full_greenfield, deployment_only; optional for others)
    deployment: Optional[Deployment] = Field(
        None, description="Deployment configuration"
    )

    # Infrastructure (required for config_only, script_only; optional for others)
    infrastructure: Optional[Infrastructure] = Field(
        None, description="Existing infrastructure specification"
    )

    # OTG config path (required for script_only)
    otg_config_path: Optional[str] = Field(
        None, description="Path or identifier to existing OTG config"
    )

    # Licensing
    include_licensing: bool = Field(
        False, description="Include licensing check in pipeline"
    )
    licensing: Optional[Licensing] = Field(None, description="Licensing specification")

    # Flags
    flags: Optional[Flags] = Field(
        default_factory=Flags, description="Runtime flags and options"
    )

    @model_validator(mode="after")
    def validate_use_case_requirements(self) -> "Intent":
        """Validate required fields based on use_case."""
        if self.use_case == UseCase.full_greenfield:
            if self.test_scenario is None:
                raise ValueError(
                    "test_scenario is required for full_greenfield use case"
                )
            if self.deployment is None:
                raise ValueError("deployment is required for full_greenfield use case")

        elif self.use_case == UseCase.config_only:
            if self.test_scenario is None:
                raise ValueError("test_scenario is required for config_only use case")
            if self.infrastructure is None:
                raise ValueError(
                    "infrastructure is required for config_only use case"
                )

        elif self.use_case == UseCase.deployment_only:
            if self.deployment is None:
                raise ValueError("deployment is required for deployment_only use case")

        elif self.use_case == UseCase.script_only:
            if self.otg_config_path is None and self.deployment is None:
                raise ValueError(
                    "otg_config_path or deployment is required for script_only use case"
                )
            if self.infrastructure is None:
                raise ValueError(
                    "infrastructure is required for script_only use case"
                )

        elif self.use_case == UseCase.licensing_only:
            if self.licensing is None:
                raise ValueError("licensing is required for licensing_only use case")

        return self


class IntentValidator:
    """Validator for parsing and validating intent input."""

    def validate(self, intent_input: Any) -> Intent:
        """
        Validate and parse intent input.

        Args:
            intent_input: Dict, JSON string, or already-parsed Intent object

        Returns:
            Intent: Validated Intent object

        Raises:
            ValueError: If input is not a valid intent type
            ValidationError: If intent validation fails
        """
        # If already an Intent, return as-is
        if isinstance(intent_input, Intent):
            return intent_input

        # Parse JSON string if needed
        intent_dict = intent_input
        if isinstance(intent_input, str):
            try:
                intent_dict = json.loads(intent_input)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON input: {e}")

        # Validate and construct Intent
        if not isinstance(intent_dict, dict):
            raise ValueError(
                f"Intent input must be dict or JSON string, got {type(intent_dict)}"
            )

        return Intent(**intent_dict)
