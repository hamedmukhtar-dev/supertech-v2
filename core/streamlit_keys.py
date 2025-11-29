"""Deterministic Streamlit key generator.

Provides functions to generate stable, unique keys for Streamlit widgets
to avoid StreamlitDuplicateElementId errors.
"""
import hashlib
import re
from pathlib import Path


def normalize_page(path: Path) -> str:
    """Return normalized page token from file path stem.
    
    Non-alphanumeric characters are converted to underscores.
    
    Args:
        path: Path to the file.
        
    Returns:
        Normalized page token string.
    """
    stem = path.stem
    return re.sub(r'[^a-zA-Z0-9]', '_', stem)


def short_hash(text: str) -> str:
    """Return first 6 chars of md5 hash of text.
    
    Args:
        text: Input text to hash.
        
    Returns:
        First 6 characters of the MD5 hash.
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]


def generate_key(path: Path, component: str, label: str = "") -> str:
    """Generate a deterministic key for a Streamlit widget.
    
    The key format is: {PAGE}_{COMPONENT}_{HASH}
    where HASH = short_hash(f"{path.as_posix()}:{component}:{label}")
    
    Args:
        path: Path to the file containing the widget.
        component: Widget component type (e.g., 'selectbox', 'text_input').
        label: Widget label text.
        
    Returns:
        Deterministic key string.
    """
    page = normalize_page(path)
    hash_input = f"{path.as_posix()}:{component}:{label}"
    hash_value = short_hash(hash_input)
    return f"{page}_{component}_{hash_value}"
