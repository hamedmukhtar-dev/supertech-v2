"""
Deterministic Streamlit Key Generator

Provides stable, unique keys for Streamlit widgets to eliminate
StreamlitDuplicateElementId errors.
"""

import hashlib
from pathlib import Path


def normalize_page(path: Path) -> str:
    """
    Normalize a file path to a page identifier string.
    
    Args:
        path: Path object representing the file path
        
    Returns:
        A normalized string suitable for use in Streamlit widget keys.
        Uses the file stem (name without extension) with special characters
        removed or replaced.
    """
    # Get the stem (filename without extension)
    stem = path.stem if isinstance(path, Path) else Path(path).stem
    # Remove leading numbers and underscores (common in Streamlit page naming)
    # e.g., "02_Register" -> "Register"
    parts = stem.split('_')
    # Filter out parts that are purely numeric
    cleaned_parts = [p for p in parts if not p.isdigit()]
    if cleaned_parts:
        return '_'.join(cleaned_parts).upper()
    return stem.upper()


def short_hash(text: str) -> str:
    """
    Generate a short deterministic hash from text.
    
    Args:
        text: The input text to hash
        
    Returns:
        First 6 characters of the md5 hash of the input text
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]


def generate_key(path: Path, component: str, label: str = "") -> str:
    """
    Generate a deterministic, unique key for a Streamlit widget.
    
    Args:
        path: Path to the Python file containing the widget
        component: The Streamlit component type (e.g., 'selectbox', 'text_input')
        label: The label/first argument of the widget (optional)
        
    Returns:
        A unique key string in format: {PAGE}_{COMPONENT}_{HASH}
    """
    page = normalize_page(path)
    component_upper = component.upper()
    
    # Create hash from the combination of path, component, and label
    hash_input = f"{path}:{component}:{label}"
    hash_suffix = short_hash(hash_input)
    
    return f"{page}_{component_upper}_{hash_suffix}"
