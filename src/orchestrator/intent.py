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


class IntentIntake:
    """Intent intake engine for classifying user requests and building intents."""

    CLARIFYING_QUESTIONS = {
        UseCase.full_greenfield: [
            "What is the test scenario name?",
            "Describe the test scenario",
            "What protocols are involved?",
            "How many ports are needed?",
            "What deployment method? (docker_compose, containerlab)",
            "What is the port speed? (1GE, 10GE, 25GE, 40GE, 100GE, 400GE)",
            "Traffic rate (optional)?",
            "Test duration in seconds (optional)?",
        ],
        UseCase.config_only: [
            "What is the test scenario name?",
            "Describe the test scenario",
            "What protocols are involved?",
            "How many ports are needed?",
            "What is the controller URL?",
            "Port locations (comma-separated)?",
        ],
        UseCase.deployment_only: [
            "What deployment method? (docker_compose, containerlab)",
            "What is the deployment type? (B2B, CP+DP, LAG)",
            "How many ports are needed?",
            "What is the port speed? (1GE, 10GE, 25GE, 40GE, 100GE, 400GE)",
        ],
        UseCase.script_only: [
            "Path to OTG config?",
            "What is the controller URL?",
            "Port locations (comma-separated)?",
        ],
        UseCase.licensing_only: [
            "How many ports are needed?",
            "What is the port speed? (1GE, 10GE, 25GE, 40GE, 100GE, 400GE)",
            "What protocols are involved?",
            "Session count (optional)?",
            "License tier? (Developer, Team, System)",
        ],
    }

    @staticmethod
    def classify_intent(user_request: str) -> UseCase:
        """
        Classify the intent from a user request based on keywords.

        Args:
            user_request: User's natural language request

        Returns:
            UseCase: Classified use case

        Logic:
            - If request mentions license/licensing -> licensing_only
            - If request mentions script + otg/existing (not config) -> script_only
            - If request mentions config + existing -> config_only
            - If request mentions deploy (not test/config) -> deployment_only
            - If request mentions deploy + test -> full_greenfield
            - Default: full_greenfield
        """
        request_lower = user_request.lower()

        # Check for licensing-only (highest priority)
        if "license" in request_lower:
            return UseCase.licensing_only

        # Check for script-only (script + otg/existing, but not config)
        if "script" in request_lower and ("otg" in request_lower or "existing" in request_lower):
            if "config" not in request_lower:
                return UseCase.script_only

        # Check for config-only (config + existing)
        if "config" in request_lower and "existing" in request_lower:
            return UseCase.config_only

        # Check for deployment-only (deploy/deployment without test/config)
        if ("deploy" in request_lower) and ("test" not in request_lower and "config" not in request_lower):
            return UseCase.deployment_only

        # Check for full greenfield (deploy + test or test + docker)
        if ("deploy" in request_lower or "docker" in request_lower) and "test" in request_lower:
            return UseCase.full_greenfield

        # Default to full_greenfield
        return UseCase.full_greenfield

    @staticmethod
    def build_intent(user_request: str, answers: dict[str, Any]) -> Intent:
        """
        Build a complete Intent object from user answers.

        Args:
            user_request: Original user request
            answers: Dict of user answers to clarifying questions

        Returns:
            Intent: Fully constructed Intent object

        Raises:
            ValueError: If required fields are missing for the classified use case
        """
        use_case = IntentIntake.classify_intent(user_request)

        if use_case == UseCase.full_greenfield:
            return IntentIntake._build_full_greenfield(answers)
        elif use_case == UseCase.config_only:
            return IntentIntake._build_config_only(answers)
        elif use_case == UseCase.deployment_only:
            return IntentIntake._build_deployment_only(answers)
        elif use_case == UseCase.script_only:
            return IntentIntake._build_script_only(answers)
        elif use_case == UseCase.licensing_only:
            return IntentIntake._build_licensing_only(answers)
        else:
            raise ValueError(f"Unknown use case: {use_case}")

    @staticmethod
    def _build_full_greenfield(answers: dict[str, Any]) -> Intent:
        """Build a full_greenfield intent."""
        port_count = int(answers.get("port_count", 2))
        port_speed = answers.get("port_speed", "100GE")
        protocols = answers.get("protocols", [])

        # Build ports
        ports = [
            Port(name=f"te{i+1}", speed=port_speed)
            for i in range(port_count)
        ]

        # Build test scenario
        test_scenario = ScenarioSpec(
            name=answers.get("test_name", "Test Scenario"),
            description=answers.get("test_description", ""),
            protocols=protocols,
            port_count=port_count,
            traffic_rate=answers.get("traffic_rate"),
            duration_seconds=answers.get("duration_seconds"),
        )

        # Build deployment
        deployment = Deployment(
            method=DeploymentMethod(answers.get("deployment_method", "docker_compose")),
            deployment_type=answers.get("deployment_type", "CP+DP"),
            ports=ports,
        )

        return Intent(
            use_case=UseCase.full_greenfield,
            test_scenario=test_scenario,
            deployment=deployment,
        )

    @staticmethod
    def _build_config_only(answers: dict[str, Any]) -> Intent:
        """Build a config_only intent."""
        port_count = int(answers.get("port_count", 2))
        protocols = answers.get("protocols", [])
        port_locations = answers.get("port_locations", [])

        # Parse port locations
        if isinstance(port_locations, str):
            port_locations = [loc.strip() for loc in port_locations.split(",")]

        ports = []
        for i, location in enumerate(port_locations):
            ports.append(Port(name=f"eth{i+1}", location=location))

        # If not enough ports from locations, add more
        while len(ports) < port_count:
            ports.append(Port(name=f"eth{len(ports)+1}"))

        # Build test scenario
        test_scenario = ScenarioSpec(
            name=answers.get("test_name", "Config Test"),
            description=answers.get("test_description", ""),
            protocols=protocols,
            port_count=port_count,
        )

        # Build infrastructure
        infrastructure = Infrastructure(
            controller_url=answers.get("controller_url", "localhost:8443"),
            ports=ports,
        )

        return Intent(
            use_case=UseCase.config_only,
            test_scenario=test_scenario,
            infrastructure=infrastructure,
        )

    @staticmethod
    def _build_deployment_only(answers: dict[str, Any]) -> Intent:
        """Build a deployment_only intent."""
        port_count = int(answers.get("port_count", 2))
        port_speed = answers.get("port_speed", "100GE")

        # Build ports
        ports = [
            Port(name=f"eth{i+1}", speed=port_speed)
            for i in range(port_count)
        ]

        # Build deployment
        deployment = Deployment(
            method=DeploymentMethod(answers.get("deployment_method", "docker_compose")),
            deployment_type=answers.get("deployment_type", "CP+DP"),
            ports=ports,
        )

        return Intent(
            use_case=UseCase.deployment_only,
            deployment=deployment,
        )

    @staticmethod
    def _build_script_only(answers: dict[str, Any]) -> Intent:
        """Build a script_only intent."""
        otg_config_path = answers.get("otg_config_path")
        controller_url = answers.get("controller_url", "localhost:8443")
        port_locations = answers.get("port_locations", [])

        # Parse port locations
        if isinstance(port_locations, str):
            port_locations = [loc.strip() for loc in port_locations.split(",")]

        ports = []
        for i, location in enumerate(port_locations):
            ports.append(Port(name=f"port{i+1}", location=location))

        # Build infrastructure
        infrastructure = Infrastructure(
            controller_url=controller_url,
            ports=ports if ports else None,
        )

        return Intent(
            use_case=UseCase.script_only,
            otg_config_path=otg_config_path,
            infrastructure=infrastructure,
        )

    @staticmethod
    def _build_licensing_only(answers: dict[str, Any]) -> Intent:
        """Build a licensing_only intent."""
        port_count = int(answers.get("port_count", 2))
        port_speed = answers.get("port_speed", "100GE")
        protocols = answers.get("protocols", [])

        # Build licensing
        licensing = Licensing(
            port_count=port_count,
            port_speed=port_speed,
            protocols=protocols,
            session_count=answers.get("session_count"),
            license_tier=answers.get("license_tier", "Developer"),
        )

        return Intent(
            use_case=UseCase.licensing_only,
            licensing=licensing,
        )
