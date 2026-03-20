"""
Tests for Intent Schema and Validation.

TDD approach: Define expected behavior before implementation.
"""
import json
import pytest
from pydantic import ValidationError

# These imports will fail initially (import error) until we create intent.py
from src.orchestrator.intent import (
    Intent,
    UseCase,
    Deployment,
    DeploymentMethod,
    Port,
    TestScenario,
    Licensing,
    Flags,
    IntentValidator,
)


class TestIntentSchemaBasics:
    """Test basic intent schema structure and parsing."""

    def test_intent_schema_parse_valid_full_greenfield(self):
        """Parse a valid full greenfield intent with all fields."""
        intent_dict = {
            "use_case": "full_greenfield",
            "test_scenario": {
                "name": "BGP Convergence Test",
                "description": "Test BGP convergence with 2 ports",
                "protocols": ["BGP"],
                "port_count": 2,
                "traffic_rate": "1000 pps",
                "duration_seconds": 30,
            },
            "deployment": {
                "method": "docker_compose",
                "deployment_type": "CP+DP",
                "ports": [
                    {
                        "name": "te1",
                        "speed": "100GE",
                        "location": None,
                    },
                    {
                        "name": "te2",
                        "speed": "100GE",
                        "location": None,
                    },
                ],
            },
            "include_licensing": False,
        }
        intent = Intent(**intent_dict)
        assert intent.use_case == UseCase.full_greenfield
        assert intent.test_scenario.name == "BGP Convergence Test"
        assert len(intent.deployment.ports) == 2
        assert intent.include_licensing is False

    def test_intent_schema_parse_config_only(self):
        """Parse a config_only intent with existing infrastructure."""
        intent_dict = {
            "use_case": "config_only",
            "test_scenario": {
                "name": "BGP Test",
                "description": "Simple BGP test",
                "protocols": ["BGP"],
                "port_count": 2,
            },
            "infrastructure": {
                "controller_url": "localhost:8443",
                "ports": [
                    {"name": "eth1", "location": "te1:5555"},
                    {"name": "eth2", "location": "te2:5556"},
                ],
            },
        }
        intent = Intent(**intent_dict)
        assert intent.use_case == UseCase.config_only
        assert intent.infrastructure is not None
        assert intent.infrastructure.controller_url == "localhost:8443"

    def test_intent_schema_parse_deployment_only(self):
        """Parse a deployment_only intent."""
        intent_dict = {
            "use_case": "deployment_only",
            "deployment": {
                "method": "containerlab",
                "deployment_type": "CP+DP",
                "ports": [
                    {"name": "eth1", "speed": "100GE"},
                    {"name": "eth2", "speed": "100GE"},
                ],
            },
        }
        intent = Intent(**intent_dict)
        assert intent.use_case == UseCase.deployment_only
        assert intent.deployment.method == DeploymentMethod.containerlab

    def test_intent_schema_parse_script_only(self):
        """Parse a script_only intent from existing OTG config."""
        intent_dict = {
            "use_case": "script_only",
            "otg_config_path": "/path/to/otg_config.json",
            "infrastructure": {
                "controller_url": "192.168.1.100:8443",
                "ports": [
                    {"name": "port1", "location": "ixia_port_1"},
                ],
            },
        }
        intent = Intent(**intent_dict)
        assert intent.use_case == UseCase.script_only
        assert intent.otg_config_path == "/path/to/otg_config.json"

    def test_intent_schema_parse_licensing_only(self):
        """Parse a licensing_only intent."""
        intent_dict = {
            "use_case": "licensing_only",
            "licensing": {
                "port_count": 2,
                "port_speed": "100GE",
                "protocols": ["BGP"],
                "session_count": 4,
                "license_tier": "Team",
            },
        }
        intent = Intent(**intent_dict)
        assert intent.use_case == UseCase.licensing_only
        assert intent.licensing is not None
        assert intent.licensing.port_count == 2


class TestIntentValidation:
    """Test intent schema validation rules."""

    def test_intent_validates_use_case_enum(self):
        """Validate that use_case is restricted to valid enum values."""
        # Valid enum value should work
        intent_dict = {
            "use_case": "full_greenfield",
            "test_scenario": {
                "name": "Test",
                "description": "Test",
                "protocols": ["BGP"],
                "port_count": 1,
            },
            "deployment": {
                "method": "docker_compose",
                "deployment_type": "CP+DP",
                "ports": [{"name": "te1"}],
            },
        }
        intent = Intent(**intent_dict)
        assert intent.use_case == UseCase.full_greenfield

        # Invalid enum value should raise ValidationError
        bad_dict = {
            "use_case": "invalid_use_case",
            "test_scenario": {
                "name": "Test",
                "description": "Test",
                "protocols": ["BGP"],
                "port_count": 1,
            },
            "deployment": {
                "method": "docker_compose",
                "deployment_type": "CP+DP",
                "ports": [{"name": "te1"}],
            },
        }
        with pytest.raises(ValidationError):
            Intent(**bad_dict)

    def test_intent_requires_use_case(self):
        """Validate that use_case is required."""
        intent_dict = {
            "test_scenario": {
                "name": "Test",
                "description": "Test",
                "protocols": ["BGP"],
                "port_count": 1,
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            Intent(**intent_dict)
        assert "use_case" in str(exc_info.value)

    def test_intent_requires_test_scenario_for_greenfield(self):
        """Validate that test_scenario is required for greenfield use case."""
        intent_dict = {
            "use_case": "full_greenfield",
            "deployment": {
                "method": "docker_compose",
                "deployment_type": "CP+DP",
                "ports": [{"name": "te1", "speed": "100GE"}],
            },
        }
        with pytest.raises(ValidationError):
            Intent(**intent_dict)

    def test_intent_requires_deployment_for_greenfield(self):
        """Validate that deployment is required for greenfield use case."""
        intent_dict = {
            "use_case": "full_greenfield",
            "test_scenario": {
                "name": "Test",
                "description": "Test",
                "protocols": ["BGP"],
                "port_count": 2,
            },
        }
        with pytest.raises(ValidationError):
            Intent(**intent_dict)

    def test_intent_validates_port_speed(self):
        """Validate port speed is a recognized value."""
        valid_speeds = ["1GE", "10GE", "25GE", "40GE", "100GE", "400GE"]
        for speed in valid_speeds:
            port_dict = {"name": "port1", "speed": speed}
            port = Port(**port_dict)
            assert port.speed == speed

        # Invalid speed should raise error
        bad_dict = {"name": "port1", "speed": "999GE"}
        with pytest.raises(ValidationError):
            Port(**bad_dict)

    def test_intent_validates_deployment_method(self):
        """Validate deployment method enum."""
        valid_methods = ["docker_compose", "containerlab"]
        for method in valid_methods:
            dep_dict = {
                "method": method,
                "deployment_type": "CP+DP",
                "ports": [{"name": "te1", "speed": "100GE"}],
            }
            dep = Deployment(**dep_dict)
            assert str(dep.method.value) == method

        bad_dict = {
            "method": "invalid_method",
            "deployment_type": "CP+DP",
            "ports": [{"name": "te1"}],
        }
        with pytest.raises(ValidationError):
            Deployment(**bad_dict)

    def test_intent_validates_deployment_type(self):
        """Validate deployment_type enum."""
        valid_types = ["B2B", "CP+DP", "LAG"]
        for dep_type in valid_types:
            dep_dict = {
                "method": "docker_compose",
                "deployment_type": dep_type,
                "ports": [{"name": "te1"}],
            }
            dep = Deployment(**dep_dict)
            assert dep.deployment_type == dep_type

        bad_dict = {
            "method": "docker_compose",
            "deployment_type": "INVALID",
            "ports": [{"name": "te1"}],
        }
        with pytest.raises(ValidationError):
            Deployment(**bad_dict)

    def test_test_scenario_requires_name_and_description(self):
        """Validate that test_scenario requires name and description."""
        # Missing name
        bad_dict = {
            "description": "Test",
            "protocols": ["BGP"],
            "port_count": 1,
        }
        with pytest.raises(ValidationError):
            TestScenario(**bad_dict)

        # Missing description
        bad_dict = {
            "name": "Test",
            "protocols": ["BGP"],
            "port_count": 1,
        }
        with pytest.raises(ValidationError):
            TestScenario(**bad_dict)

    def test_test_scenario_port_count_positive(self):
        """Validate that port_count must be positive."""
        bad_dict = {
            "name": "Test",
            "description": "Test",
            "protocols": ["BGP"],
            "port_count": 0,
        }
        with pytest.raises(ValidationError):
            TestScenario(**bad_dict)

        bad_dict["port_count"] = -1
        with pytest.raises(ValidationError):
            TestScenario(**bad_dict)

    def test_licensing_requires_port_count_and_speed(self):
        """Validate that licensing requires port_count and port_speed."""
        bad_dict = {
            "port_count": 2,
            "protocols": ["BGP"],
        }
        with pytest.raises(ValidationError):
            Licensing(**bad_dict)

        bad_dict = {
            "port_speed": "100GE",
            "protocols": ["BGP"],
        }
        with pytest.raises(ValidationError):
            Licensing(**bad_dict)


class TestIntentValidatorClass:
    """Test the IntentValidator class validation methods."""

    def test_intent_validator_validate_full_greenfield(self):
        """Validator should validate and return full greenfield intent."""
        intent_dict = {
            "use_case": "full_greenfield",
            "test_scenario": {
                "name": "BGP Test",
                "description": "BGP test",
                "protocols": ["BGP"],
                "port_count": 2,
            },
            "deployment": {
                "method": "docker_compose",
                "deployment_type": "CP+DP",
                "ports": [
                    {"name": "te1", "speed": "100GE"},
                    {"name": "te2", "speed": "100GE"},
                ],
            },
        }
        validator = IntentValidator()
        intent = validator.validate(intent_dict)
        assert isinstance(intent, Intent)
        assert intent.use_case == UseCase.full_greenfield

    def test_intent_validator_raises_on_invalid(self):
        """Validator should raise ValidationError on invalid input."""
        bad_dict = {
            "use_case": "invalid",
            "test_scenario": {
                "name": "Test",
                "description": "Test",
                "protocols": ["BGP"],
                "port_count": 1,
            },
        }
        validator = IntentValidator()
        with pytest.raises(ValidationError):
            validator.validate(bad_dict)

    def test_intent_validator_validate_from_json_string(self):
        """Validator should accept and parse JSON strings."""
        json_str = json.dumps({
            "use_case": "deployment_only",
            "deployment": {
                "method": "containerlab",
                "deployment_type": "CP+DP",
                "ports": [{"name": "eth1"}],
            },
        })
        validator = IntentValidator()
        intent = validator.validate(json_str)
        assert isinstance(intent, Intent)
        assert intent.use_case == UseCase.deployment_only


class TestIntentEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_intent_allows_optional_flags(self):
        """Intent should allow optional flags object."""
        intent_dict = {
            "use_case": "config_only",
            "test_scenario": {
                "name": "Test",
                "description": "Test",
                "protocols": ["BGP"],
                "port_count": 1,
            },
            "infrastructure": {
                "controller_url": "localhost:8443",
            },
            "flags": {
                "verbose": True,
                "dry_run": False,
                "skip_validation": False,
            },
        }
        intent = Intent(**intent_dict)
        assert intent.flags.verbose is True

    def test_intent_deployment_ports_required(self):
        """Deployment must have at least one port if method is specified."""
        bad_dict = {
            "method": "docker_compose",
            "deployment_type": "CP+DP",
            "ports": [],
        }
        with pytest.raises(ValidationError):
            Deployment(**bad_dict)

    def test_intent_licensing_license_tier_validation(self):
        """Licensing should validate license tier values."""
        valid_tiers = ["Developer", "Team", "System"]
        for tier in valid_tiers:
            lic_dict = {
                "port_count": 2,
                "port_speed": "100GE",
                "license_tier": tier,
            }
            lic = Licensing(**lic_dict)
            assert lic.license_tier == tier

        bad_dict = {
            "port_count": 2,
            "port_speed": "100GE",
            "license_tier": "InvalidTier",
        }
        with pytest.raises(ValidationError):
            Licensing(**bad_dict)

    def test_intent_infrastructure_with_multiple_ports(self):
        """Infrastructure should support multiple ports."""
        intent_dict = {
            "use_case": "config_only",
            "test_scenario": {
                "name": "Multi-Port Test",
                "description": "Test with 4 ports",
                "protocols": ["BGP"],
                "port_count": 4,
            },
            "infrastructure": {
                "controller_url": "localhost:8443",
                "ports": [
                    {"name": "eth1", "location": "te1:5555"},
                    {"name": "eth2", "location": "te2:5556"},
                    {"name": "eth3", "location": "te3:5557"},
                    {"name": "eth4", "location": "te4:5558"},
                ],
            },
        }
        intent = Intent(**intent_dict)
        assert len(intent.infrastructure.ports) == 4


class TestIntentMultipleUseCase:
    """Test full pipeline use cases with multiple subagents."""

    def test_intent_full_pipeline_with_licensing(self):
        """Full pipeline intent with licensing check."""
        intent_dict = {
            "use_case": "full_greenfield",
            "test_scenario": {
                "name": "BGP + Licensing Test",
                "description": "Complete test with licensing",
                "protocols": ["BGP"],
                "port_count": 2,
                "traffic_rate": "1000 pps",
            },
            "deployment": {
                "method": "docker_compose",
                "deployment_type": "CP+DP",
                "ports": [
                    {"name": "te1", "speed": "100GE"},
                    {"name": "te2", "speed": "100GE"},
                ],
            },
            "include_licensing": True,
            "licensing": {
                "port_count": 2,
                "port_speed": "100GE",
                "protocols": ["BGP"],
                "session_count": 4,
                "license_tier": "Team",
            },
        }
        intent = Intent(**intent_dict)
        assert intent.include_licensing is True
        assert intent.licensing.session_count == 4
