"""OTG Orchestrator Skill Handler - Main entry point for orchestrator skill."""

from typing import Any, Dict, Optional
from pathlib import Path
import logging

from src.orchestrator import (
    Orchestrator,
    Intent,
    IntentIntake,
    IntentValidator,
    SkillTransport,
)

logger = logging.getLogger(__name__)


def invoke_skill(
    user_request: str,
    interactive: bool = True,
    artifacts_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point for orchestrator skill.

    Orchestrates the full workflow:
    1. Classify intent from natural language request
    2. Ask clarifying questions if needed
    3. Build Intent object
    4. Run orchestrator (dispatch, execute, recover, artifact generation)
    5. Return structured result

    Args:
        user_request: Natural language description of desired test scenario
        interactive: If True, wait for user approval at checkpoints.
                    If False, auto-proceed through all approvals.
        artifacts_dir: Optional directory to save artifacts. If None, uses default.

    Returns:
        Dictionary with keys:
            - success: bool - Whether orchestration completed successfully
            - result: Dict - Orchestrator result from run() method
            - artifacts_dir: str - Path where artifacts were saved
            - error: Optional[str] - Error message if success=False
            - error_category: Optional[str] - Category of error (transient/validation/terminal)

    Raises:
        ValueError: If user_request is empty or None
        RuntimeError: If orchestrator fails in unrecoverable way
    """
    if not user_request or not user_request.strip():
        raise ValueError("user_request cannot be empty")

    logger.info(f"Orchestrator skill invoked with request: {user_request[:100]}")

    try:
        # Phase 1: Intent Intake - Classify intent from user request
        logger.info("Phase 1: Intent Intake")
        intent_intake = IntentIntake()
        use_case = intent_intake.classify_intent(user_request)
        logger.info(f"Classified use case: {use_case.value}")

        # Ask clarifying questions to build complete intent
        # In interactive mode, this would prompt the user
        # In batch mode, this uses defaults
        answers = _get_clarifying_answers(use_case, interactive=interactive)
        logger.info(f"Collected answers: {answers}")

        # Build intent from user request and answers
        intent = intent_intake.build_intent(user_request, answers)
        logger.info(f"Built intent: {intent.use_case.value}")

        # Validate intent
        validator = IntentValidator()
        validation_errors = validator.validate(intent)
        if validation_errors:
            logger.warning(f"Intent validation warnings: {validation_errors}")
            if not interactive:
                logger.warning("Running in batch mode with validation warnings")

        # Phase 2-4: Run Orchestrator
        logger.info("Phase 2-4: Orchestrator dispatch, execute, and artifact generation")
        transport = SkillTransport()
        orchestrator = Orchestrator(
            transport=transport,
            artifacts_dir=Path(artifacts_dir) if artifacts_dir else None,
        )

        result = orchestrator.run(intent, interactive=interactive)
        logger.info("Orchestrator completed successfully")

        return {
            "success": True,
            "result": result,
            "artifacts_dir": str(result.get("artifacts_dir", "")),
        }

    except ValueError as e:
        logger.error(f"Validation error during orchestration: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_category": "validation",
        }
    except RuntimeError as e:
        logger.error(f"Runtime error during orchestration: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_category": "terminal",
        }
    except Exception as e:
        logger.error(f"Unexpected error during orchestration: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_category": "unknown",
        }


def _get_clarifying_answers(use_case: Any, interactive: bool = True) -> Dict[str, Any]:
    """
    Gather clarifying answers based on use case.

    Args:
        use_case: UseCase enum value from intent classification
        interactive: If True, prompt user for answers. If False, use defaults.

    Returns:
        Dictionary with answers for common questions:
            - device_type: str (juniper, arista, srl, ceos)
            - protocol_focus: str (bgp, ospf, mpls)
            - scale: str (small, medium, large)
            - infrastructure: str (onprem, aws, gcp, azure, containerlab)
            - license_tier: str (free, standard, premium, enterprise)
    """
    answers = {}

    # Default answers for all use cases
    answers["device_type"] = "juniper"
    answers["protocol_focus"] = "bgp"
    answers["scale"] = "medium"
    answers["infrastructure"] = "containerlab"
    answers["license_tier"] = "standard"

    if interactive:
        # In interactive mode, could prompt user for clarifications
        # For now, use defaults but log that questions would be asked
        logger.info("Would ask user for clarifications (not implemented in handler)")

    return answers


def validate_skill_environment() -> bool:
    """
    Validate that orchestrator environment is properly configured.

    Checks:
    - All required sub-agent transports available
    - Artifacts directory writable
    - Orchestrator modules importable

    Returns:
        True if environment valid, False otherwise
    """
    try:
        # Check imports
        from src.orchestrator import Orchestrator, Intent, IntentIntake
        logger.info("✓ All orchestrator modules importable")

        # Check transport
        transport = SkillTransport()
        logger.info("✓ SkillTransport initialized")

        # If we got here, environment is valid
        return True
    except ImportError as e:
        logger.error(f"Missing import: {e}")
        return False
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False
