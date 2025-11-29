"""Deterministic Streamlit key generator for avoiding StreamlitDuplicateElementId errors."""

import hashlib
from pathlib import Path


def normalize_page(path: Path) -> str:
    """Normalize a file path to a short page identifier.
    
    Args:
        path: File path to normalize (e.g., 'pages/02_Register.py')
    
    Returns:
        Normalized page name (e.g., 'register')
    """
    stem = path.stem
    # Remove numeric prefixes like "02_" from page names
    if stem and "_" in stem:
        parts = stem.split("_", 1)
        if parts[0].isdigit():
            stem = parts[1]
    return stem.lower().replace("_", "")


def short_hash(text: str) -> str:
    """Generate a short hash (first 6 chars of md5).
    
    Args:
        text: Text to hash
    
    Returns:
        First 6 characters of the md5 hash
    """
    return hashlib.md5(text.encode()).hexdigest()[:6]


def generate_key(path: Path, component: str, label: str = "") -> str:
    """Generate a deterministic widget key.
    
    Args:
        path: File path where the widget is located
        component: Component type identifier (e.g., 'EMAIL', 'LANG')
        label: Optional label text for additional uniqueness
    
    Returns:
        Key in format: {PAGE}_{COMPONENT}_{HASH}
    """
    page = normalize_page(path)
    hash_input = f"{path}:{component}:{label}"
    hash_value = short_hash(hash_input)
    return f"{page}_{component}_{hash_value}"
