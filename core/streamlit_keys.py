"""Deterministic Streamlit key generator.

Provides functions to generate stable, unique keys for Streamlit widgets
to eliminate StreamlitDuplicateElementId / StreamlitDuplicateElementKey errors.
"""

import hashlib
import re
from pathlib import Path


def normalize_page(path: Path) -> str:
    """Normalize file stem to PAGE token.

    Replaces non-alphanumeric characters with underscore,
    strips leading/trailing underscores, and uppercases result.

    Args:
        path: Path to the Python file.

    Returns:
        Normalized PAGE token string.
    """
    stem = path.stem
    # Replace non-alphanumeric with underscore
    normalized = re.sub(r"[^a-zA-Z0-9]", "_", stem)
    # Strip leading/trailing underscores
    normalized = normalized.strip("_")
    # Uppercase
    return normalized.upper()


def short_hash(text: str) -> str:
    """Return first 6 hex chars of md5(text).

    Args:
        text: Input string to hash.

    Returns:
        First 6 hex characters of MD5 hash.
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:6]


def generate_key(path: Path, component: str, label: str = "") -> str:
    """Generate a deterministic key for a Streamlit widget.

    Returns a key in format: {PAGE}_{COMPONENT}_{HASH}
    where HASH = short_hash(f"{path.as_posix()}:{component}:{label}")

    Args:
        path: Path to the Python file containing the widget.
        component: Component identifier (usually derived from widget type or label).
        label: First string argument of the widget (for hashing).

    Returns:
        Deterministic key string.
    """
    page = normalize_page(path)
    hash_input = f"{path.as_posix()}:{component}:{label}"
    hash_value = short_hash(hash_input)
    return f"{page}_{component}_{hash_value}"
