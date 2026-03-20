"""
Error Recovery Engine.

Handles error classification, recovery strategy generation, and intelligent
retry logic for orchestrator failures.

Provides:
- ErrorCategory: Enumeration of error types
- ErrorClassification: Structured error analysis result
- ErrorClassifier: Classifies errors based on message patterns
- RecoveryOption: Represents a recovery action
- RecoveryStrategy: Generates recovery options based on error type and context
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.orchestrator.config import AGENT_CONFIG


class ErrorCategory(str, Enum):
    """Enumeration of error categories for classification."""

    TRANSIENT = "transient"
    VALIDATION = "validation"
    STATE = "state"
    UNKNOWN = "unknown"


@dataclass
class ErrorClassification:
    """Result of error classification analysis."""

    category: ErrorCategory
    reason: str
    recoverable: bool


@dataclass
class RecoveryOption:
    """A recovery action option for a failed operation."""

    action: str
    label: str
    description: str


class ErrorClassifier:
    """
    Classifies errors into categories based on message patterns.

    Patterns:
    - TRANSIENT: timeout, connection errors, service unavailable
    - VALIDATION: missing fields, invalid values, schema errors
    - STATE: state mismatch, resource not found, conflict
    - UNKNOWN: unrecognized errors
    """

    # Pattern lists for error classification
    TRANSIENT_PATTERNS = [
        "timeout",
        "timed out",
        "TimeoutError",
        "connection refused",
        "ConnectionError",
        "ECONNREFUSED",
        "service unavailable",
        "503",
        "temporarily unavailable",
        "try again",
        "deadline exceeded",
        "network unreachable",
    ]

    VALIDATION_PATTERNS = [
        "validation error",
        "ValidationError",
        "missing",
        "required",
        "invalid",
        "ValueError",
        "field",
        "schema",
        "malformed",
        "parse error",
    ]

    STATE_PATTERNS = [
        "state mismatch",
        "StateError",
        "expected",
        "resource not found",
        "404",
        "conflict",
        "already exists",
        "not running",
        "not deployed",
    ]

    def classify(self, error: Dict) -> ErrorClassification:
        """
        Classify an error into a category.

        Args:
            error: Dictionary with keys:
                - message: error message string
                - error_type: exception type string
                - context: optional context string

        Returns:
            ErrorClassification with category, reason, and recoverable flag
        """
        message = error.get("message", "").lower()
        error_type = error.get("error_type", "").lower()
        combined = f"{message} {error_type}".lower()

        # Check transient patterns
        if self._matches_patterns(combined, self.TRANSIENT_PATTERNS):
            return ErrorClassification(
                category=ErrorCategory.TRANSIENT,
                reason=f"Transient error detected: {error.get('message', 'Unknown')}",
                recoverable=True
            )

        # Check validation patterns
        if self._matches_patterns(combined, self.VALIDATION_PATTERNS):
            return ErrorClassification(
                category=ErrorCategory.VALIDATION,
                reason=f"Validation error detected: {error.get('message', 'Unknown')}",
                recoverable=True
            )

        # Check state patterns
        if self._matches_patterns(combined, self.STATE_PATTERNS):
            return ErrorClassification(
                category=ErrorCategory.STATE,
                reason=f"State mismatch detected: {error.get('message', 'Unknown')}",
                recoverable=True
            )

        # Unknown error
        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            reason=f"Unknown error: {error.get('message', 'Unknown')}",
            recoverable=False
        )

    @staticmethod
    def _matches_patterns(text: str, patterns: List[str]) -> bool:
        """
        Check if text matches any pattern.

        Args:
            text: Text to check (already lowercased)
            patterns: List of patterns to match (case-insensitive)

        Returns:
            True if any pattern matches, False otherwise
        """
        text_lower = text.lower()
        for pattern in patterns:
            if pattern.lower() in text_lower:
                return True
        return False


class RecoveryStrategy:
    """
    Generates recovery options based on error classification and context.

    Determines what actions are available given:
    - Error category (transient, validation, state, unknown)
    - Retry count vs max retries
    - Agent capabilities (skippable or not)
    """

    def get_options(
        self,
        classification: ErrorClassification,
        retry_count: int,
        max_retries: int,
        agent_name: str
    ) -> List[RecoveryOption]:
        """
        Get recovery options for a classified error.

        Args:
            classification: Error classification result
            retry_count: Current number of retries attempted
            max_retries: Maximum retries allowed for agent
            agent_name: Name of the failing agent

        Returns:
            List of RecoveryOption objects representing available actions
        """
        options = []

        # Get agent config
        agent_config = AGENT_CONFIG.get(agent_name, {})
        can_skip = agent_config.get("can_skip", False)

        if classification.category == ErrorCategory.TRANSIENT:
            # Transient errors: offer retry if retries remain
            if retry_count < max_retries:
                options.append(RecoveryOption(
                    action="retry",
                    label="Retry",
                    description=f"Retry the operation (attempt {retry_count + 1}/{max_retries})"
                ))

            # Always offer clarification
            options.append(RecoveryOption(
                action="clarify",
                label="Edit Intent",
                description="Edit the intent to adjust parameters"
            ))

            # Offer skip if agent is skippable
            if can_skip:
                options.append(RecoveryOption(
                    action="skip",
                    label="Skip Agent",
                    description=f"Skip {agent_name} and continue"
                ))

            # Always have abort
            options.append(RecoveryOption(
                action="abort",
                label="Abort",
                description="Abort the entire workflow"
            ))

        elif classification.category == ErrorCategory.VALIDATION:
            # Validation errors: must clarify intent
            options.append(RecoveryOption(
                action="clarify",
                label="Edit Intent",
                description="Edit the intent to fix validation errors"
            ))

            # Can skip if agent is skippable
            if can_skip:
                options.append(RecoveryOption(
                    action="skip",
                    label="Skip Agent",
                    description=f"Skip {agent_name} and continue"
                ))

            # Always have abort
            options.append(RecoveryOption(
                action="abort",
                label="Abort",
                description="Abort the entire workflow"
            ))

        elif classification.category == ErrorCategory.STATE:
            # State errors: may be recoverable with retry or clarification
            if retry_count < max_retries:
                options.append(RecoveryOption(
                    action="retry",
                    label="Retry",
                    description=f"Retry the operation (attempt {retry_count + 1}/{max_retries})"
                ))

            options.append(RecoveryOption(
                action="clarify",
                label="Edit Intent",
                description="Edit the intent to adjust deployment state"
            ))

            if can_skip:
                options.append(RecoveryOption(
                    action="skip",
                    label="Skip Agent",
                    description=f"Skip {agent_name} and continue"
                ))

            options.append(RecoveryOption(
                action="abort",
                label="Abort",
                description="Abort the entire workflow"
            ))

        else:  # UNKNOWN
            # Unknown errors: can only abort
            options.append(RecoveryOption(
                action="abort",
                label="Abort",
                description="Abort the entire workflow"
            ))

        return options
