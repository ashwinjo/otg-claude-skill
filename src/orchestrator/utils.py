"""Utility functions for orchestrator."""
from datetime import datetime, timezone
import hashlib


def get_timestamp() -> str:
    """Return ISO 8601 timestamp in UTC.

    Returns:
        str: ISO 8601 formatted timestamp with 'Z' suffix (e.g., "2025-03-19T14:30:45.123456Z")
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compute_checksum(data: str) -> str:
    """Compute SHA256 checksum of data.

    Args:
        data: String data to compute checksum for.

    Returns:
        str: Checksum in format "sha256:<hex_hash>"
    """
    hash_hex = hashlib.sha256(data.encode()).hexdigest()
    return f"sha256:{hash_hex}"
