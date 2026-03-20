"""
Agent Configuration Module.

Defines configuration for all orchestrator agents including:
- Timeout settings
- Retry policies
- Skip/abort capabilities
- Global workflow settings
"""

AGENT_CONFIG = {
    "ixia-c-deployment": {
        "timeout_seconds": 600,
        "max_retries": 3,
        "can_skip": False
    },
    "otg-config-generator": {
        "timeout_seconds": 120,
        "max_retries": 2,
        "can_skip": False
    },
    "snappi-script-generator": {
        "timeout_seconds": 60,
        "max_retries": 1,
        "can_skip": False
    },
    "keng-licensing": {
        "timeout_seconds": 30,
        "max_retries": 1,
        "can_skip": True
    }
}

DEFAULT_MAX_WAIT_MINUTES = 30
