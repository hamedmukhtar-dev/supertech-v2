"""Deterministic Streamlit key generator.

Provides functions for generating stable, unique keys for Streamlit widgets
to avoid StreamlitDuplicateElementId errors.
"""

import hashlib
from pathlib import Path


def normalize_page(path: Path) -> str:
    """Convert a file path to a normalized page identifier.

    Args:
        path: Path to the Python file

    Returns:
        Normalized page identifier (e.g., 'layout_header', 'pages_02_Register')
    """
    # Get the stem (filename without extension)
    stem = path.stem

    # If the path includes 'pages/' directory, prefix with 'pages_'
    parts = path.parts
    if "pages" in parts:
        idx = parts.index("pages")
        # Join remaining parts with underscore
        remaining = parts[idx + 1 :]
        if remaining:
            # Remove .py extension from last part
            last = remaining[-1]
            if last.endswith(".py"):
                last = last[:-3]
            remaining = remaining[:-1] + (last,)
            return "_".join(["pages"] + list(remaining))

    return stem


def short_hash(text: str) -> str:
    """Generate a short hash (first 6 chars of md5).

    Args:
        text: Input text to hash

    Returns:
        First 6 characters of the md5 hex digest
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:6]


def generate_key(path: Path, component: str, label: str = "") -> str:
    """Generate a deterministic key for a Streamlit widget.

    The key format is: {PAGE}_{COMPONENT}_{HASH}
    where HASH is the first 6 chars of md5("{repo_path}:{component}:{label}")

    Args:
        path: Path to the Python file containing the widget
        component: Component type identifier (e.g., 'LANG', 'EMAIL', 'SELECTBOX')
        label: Widget label (optional, used for hash uniqueness)

    Returns:
        Deterministic key string
    """
    page = normalize_page(path)
    # Use posix path for consistent hashes across platforms
    hash_input = f"{path.as_posix()}:{component}:{label}"
    hash_val = short_hash(hash_input)
    return f"{page}_{component}_{hash_val}"
