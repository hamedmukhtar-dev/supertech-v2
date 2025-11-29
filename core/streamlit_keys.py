"""
Deterministic Streamlit key generator for avoiding StreamlitDuplicateElementId errors.

This module provides utilities to generate stable, unique keys for Streamlit widgets
based on the file path, component type, and label text.
"""
import hashlib
import re
from pathlib import Path


def normalize_page(path: Path) -> str:
    """
    Normalize a file path to a deterministic page identifier.
    
    Replaces non-alphanumeric characters with underscores and converts to uppercase.
    
    Args:
        path: Path to the source file
        
    Returns:
        A normalized string suitable for use as a key prefix
    """
    stem = path.stem
    # Replace non-alphanumeric characters with underscores
    normalized = re.sub(r'[^a-zA-Z0-9]', '_', stem)
    # Remove consecutive underscores and strip leading/trailing underscores
    normalized = re.sub(r'_+', '_', normalized).strip('_')
    return normalized.upper()


def short_hash(text: str) -> str:
    """
    Generate a short hash (first 6 hex chars) from the given text using MD5.
    
    Note: MD5 is used here intentionally for its speed and determinism.
    This is NOT used for cryptographic purposes - only for generating stable,
    short identifiers to differentiate similar widget keys. Collision risk
    is acceptable as keys are prefixed with unique page/component names.
    
    Args:
        text: Input text to hash
        
    Returns:
        First 6 hexadecimal characters of the MD5 hash
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]  # noqa: S324


def generate_key(path: Path, component: str, label: str = "") -> str:
    """
    Generate a deterministic, stable key for a Streamlit widget.
    
    The key format is: {PAGE}_{COMPONENT}_{HASH}
    
    Args:
        path: Path to the source file containing the widget
        component: Short uppercase token describing the component (e.g., 'LANG', 'EMAIL')
        label: The widget label text (used for hash generation)
        
    Returns:
        A unique, deterministic key string
    """
    page = normalize_page(path)
    # Create hash input from path, component, and label
    hash_input = f"{path}:{component}:{label}"
    hash_value = short_hash(hash_input)
    return f"{page}_{component}_{hash_value}"
