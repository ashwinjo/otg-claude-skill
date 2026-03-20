"""
Tests for Error Recovery Engine.

TDD approach: Define expected behavior before implementation.
Tests for error classification, recovery strategies, and agent configuration.
"""
import pytest
from src.orchestrator.recovery import (
    ErrorCategory,
    ErrorClassification,
    ErrorClassifier,
    RecoveryOption,
    RecoveryStrategy,
)
from src.orchestrator.config import AGENT_CONFIG, DEFAULT_MAX_WAIT_MINUTES


class TestErrorClassifier:
    """Test error classification logic."""

    def test_error_classifier_detects_transient_timeout(self):
        """Classifier should detect timeout errors as transient."""
        error_dict = {
            "message": "Operation timed out",
            "error_type": "TimeoutError",
            "context": "deployment"
        }
        classifier = ErrorClassifier()
        classification = classifier.classify(error_dict)

        assert classification.category == ErrorCategory.TRANSIENT
        assert classification.recoverable is True
        assert "timed out" in classification.reason.lower()

    def test_error_classifier_detects_transient_connection_refused(self):
        """Classifier should detect connection refused as transient."""
        error_dict = {
            "message": "connection refused",
            "error_type": "ConnectionError",
            "context": "api_call"
        }
        classifier = ErrorClassifier()
        classification = classifier.classify(error_dict)

        assert classification.category == ErrorCategory.TRANSIENT
        assert classification.recoverable is True

    def test_error_classifier_detects_validation_error(self):
        """Classifier should detect validation errors."""
        error_dict = {
            "message": "Validation error: missing required field 'name'",
            "error_type": "ValidationError",
            "context": "input"
        }
        classifier = ErrorClassifier()
        classification = classifier.classify(error_dict)

        assert classification.category == ErrorCategory.VALIDATION
        assert classification.recoverable is True
        assert "validation" in classification.reason.lower()

    def test_error_classifier_detects_missing_field(self):
        """Classifier should detect missing required field errors."""
        error_dict = {
            "message": "Missing required field: port_count",
            "error_type": "ValueError",
            "context": "schema"
        }
        classifier = ErrorClassifier()
        classification = classifier.classify(error_dict)

        assert classification.category == ErrorCategory.VALIDATION
        assert classification.recoverable is True

    def test_error_classifier_detects_state_mismatch(self):
        """Classifier should detect state mismatch errors."""
        error_dict = {
            "message": "State mismatch: expected running, got stopped",
            "error_type": "StateError",
            "context": "deployment"
        }
        classifier = ErrorClassifier()
        classification = classifier.classify(error_dict)

        assert classification.category == ErrorCategory.STATE
        assert classification.recoverable is True

    def test_error_classifier_detects_unknown_error(self):
        """Classifier should classify unrecognized errors as unknown."""
        error_dict = {
            "message": "Something went wrong but we don't know what",
            "error_type": "UnknownError",
            "context": "unknown"
        }
        classifier = ErrorClassifier()
        classification = classifier.classify(error_dict)

        assert classification.category == ErrorCategory.UNKNOWN
        # Unknown errors are not recoverable
        assert classification.recoverable is False

    def test_error_classifier_case_insensitive(self):
        """Classifier should be case-insensitive."""
        error_dict = {
            "message": "TIMEOUT ERROR",
            "error_type": "TimeoutError",
        }
        classifier = ErrorClassifier()
        classification = classifier.classify(error_dict)

        assert classification.category == ErrorCategory.TRANSIENT
        assert classification.recoverable is True


class TestRecoveryStrategy:
    """Test recovery strategy and option generation."""

    def test_recovery_strategy_offers_retry_for_transient(self):
        """Strategy should offer retry option for transient errors."""
        classification = ErrorClassification(
            category=ErrorCategory.TRANSIENT,
            reason="timeout detected",
            recoverable=True
        )
        strategy = RecoveryStrategy()
        options = strategy.get_options(
            classification=classification,
            retry_count=0,
            max_retries=3,
            agent_name="ixia-c-deployment"
        )

        assert len(options) > 0
        retry_options = [o for o in options if o.action == "retry"]
        assert len(retry_options) > 0
        assert retry_options[0].label == "Retry"

    def test_recovery_strategy_offers_clarification_for_validation(self):
        """Strategy should offer clarification option for validation errors."""
        classification = ErrorClassification(
            category=ErrorCategory.VALIDATION,
            reason="missing required field",
            recoverable=True
        )
        strategy = RecoveryStrategy()
        options = strategy.get_options(
            classification=classification,
            retry_count=0,
            max_retries=2,
            agent_name="otg-config-generator"
        )

        clarify_options = [o for o in options if o.action == "clarify"]
        assert len(clarify_options) > 0
        assert clarify_options[0].label == "Edit Intent"

    def test_recovery_strategy_no_retry_after_max_retries(self):
        """Strategy should not offer retry after max retries reached."""
        classification = ErrorClassification(
            category=ErrorCategory.TRANSIENT,
            reason="timeout",
            recoverable=True
        )
        strategy = RecoveryStrategy()
        options = strategy.get_options(
            classification=classification,
            retry_count=3,
            max_retries=3,
            agent_name="ixia-c-deployment"
        )

        # Should not have retry after max retries
        retry_options = [o for o in options if o.action == "retry"]
        assert len(retry_options) == 0

    def test_recovery_strategy_offers_skip_for_skippable_agents(self):
        """Strategy should offer skip option for skippable agents."""
        classification = ErrorClassification(
            category=ErrorCategory.TRANSIENT,
            reason="timeout",
            recoverable=True
        )
        strategy = RecoveryStrategy()
        options = strategy.get_options(
            classification=classification,
            retry_count=0,
            max_retries=1,
            agent_name="keng-licensing"
        )

        skip_options = [o for o in options if o.action == "skip"]
        assert len(skip_options) > 0

    def test_recovery_strategy_no_skip_for_non_skippable_agents(self):
        """Strategy should not offer skip for non-skippable agents."""
        classification = ErrorClassification(
            category=ErrorCategory.TRANSIENT,
            reason="timeout",
            recoverable=True
        )
        strategy = RecoveryStrategy()
        options = strategy.get_options(
            classification=classification,
            retry_count=0,
            max_retries=1,
            agent_name="ixia-c-deployment"
        )

        skip_options = [o for o in options if o.action == "skip"]
        assert len(skip_options) == 0

    def test_recovery_strategy_always_has_abort(self):
        """Strategy should always offer abort as final option."""
        classification = ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            reason="unknown error",
            recoverable=False
        )
        strategy = RecoveryStrategy()
        options = strategy.get_options(
            classification=classification,
            retry_count=0,
            max_retries=1,
            agent_name="ixia-c-deployment"
        )

        abort_options = [o for o in options if o.action == "abort"]
        assert len(abort_options) > 0


class TestAgentConfig:
    """Test agent configuration."""

    def test_agent_config_has_required_agents(self):
        """Config should have all required agents."""
        required_agents = [
            "ixia-c-deployment",
            "otg-config-generator",
            "snappi-script-generator",
            "keng-licensing"
        ]
        for agent in required_agents:
            assert agent in AGENT_CONFIG

    def test_agent_config_has_timeout_seconds(self):
        """Each agent config should have timeout_seconds."""
        for agent_name, config in AGENT_CONFIG.items():
            assert "timeout_seconds" in config
            assert isinstance(config["timeout_seconds"], int)
            assert config["timeout_seconds"] > 0

    def test_agent_config_has_max_retries(self):
        """Each agent config should have max_retries."""
        for agent_name, config in AGENT_CONFIG.items():
            assert "max_retries" in config
            assert isinstance(config["max_retries"], int)
            assert config["max_retries"] >= 0

    def test_agent_config_has_can_skip(self):
        """Each agent config should have can_skip flag."""
        for agent_name, config in AGENT_CONFIG.items():
            assert "can_skip" in config
            assert isinstance(config["can_skip"], bool)

    def test_agent_config_deployment_timeout_long(self):
        """Deployment agent should have longer timeout."""
        assert AGENT_CONFIG["ixia-c-deployment"]["timeout_seconds"] >= 600

    def test_agent_config_licensing_skippable(self):
        """Licensing agent should be skippable."""
        assert AGENT_CONFIG["keng-licensing"]["can_skip"] is True

    def test_agent_config_critical_agents_not_skippable(self):
        """Critical agents should not be skippable."""
        critical_agents = [
            "ixia-c-deployment",
            "otg-config-generator",
            "snappi-script-generator"
        ]
        for agent in critical_agents:
            assert AGENT_CONFIG[agent]["can_skip"] is False

    def test_default_max_wait_minutes_is_positive(self):
        """DEFAULT_MAX_WAIT_MINUTES should be positive."""
        assert DEFAULT_MAX_WAIT_MINUTES > 0
        assert isinstance(DEFAULT_MAX_WAIT_MINUTES, int)

    def test_default_max_wait_minutes_reasonable(self):
        """DEFAULT_MAX_WAIT_MINUTES should be reasonable value."""
        # Should be between 10 and 120 minutes for typical workflows
        assert 10 <= DEFAULT_MAX_WAIT_MINUTES <= 120


class TestErrorClassificationDataclass:
    """Test ErrorClassification dataclass structure."""

    def test_error_classification_creates_instance(self):
        """Should create ErrorClassification instance."""
        classification = ErrorClassification(
            category=ErrorCategory.TRANSIENT,
            reason="timeout occurred",
            recoverable=True
        )
        assert classification.category == ErrorCategory.TRANSIENT
        assert classification.reason == "timeout occurred"
        assert classification.recoverable is True

    def test_error_classification_with_all_categories(self):
        """Should handle all error categories."""
        for category in ErrorCategory:
            classification = ErrorClassification(
                category=category,
                reason=f"Error in {category.value}",
                recoverable=True
            )
            assert classification.category == category


class TestRecoveryOptionDataclass:
    """Test RecoveryOption dataclass structure."""

    def test_recovery_option_creates_instance(self):
        """Should create RecoveryOption instance."""
        option = RecoveryOption(
            action="retry",
            label="Retry",
            description="Retry the failed operation"
        )
        assert option.action == "retry"
        assert option.label == "Retry"
        assert option.description == "Retry the failed operation"

    def test_recovery_option_has_all_fields(self):
        """RecoveryOption should have action, label, and description."""
        option = RecoveryOption(
            action="skip",
            label="Skip Agent",
            description="Skip this optional agent"
        )
        assert hasattr(option, 'action')
        assert hasattr(option, 'label')
        assert hasattr(option, 'description')
