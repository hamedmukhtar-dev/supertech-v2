"""
Deterministic Streamlit key generator.

Provides functions to generate stable, unique keys for Streamlit widgets
to eliminate StreamlitDuplicateElementId / StreamlitDuplicateElementKey errors.
"""
import hashlib
import re
from pathlib import Path


def normalize_page(path: Path) -> str:
    """
    Return normalized file stem.
    
    Replaces non-alphanumeric characters with underscore and strips
    leading/trailing underscores.
    
    Args:
        path: Path to the Python file
        
    Returns:
        Normalized file stem string
    """
    stem = path.stem
    # Replace non-alphanumeric with underscore
    normalized = re.sub(r'[^a-zA-Z0-9]', '_', stem)
    # Strip leading/trailing underscores
    normalized = normalized.strip('_')
    return normalized


def short_hash(text: str) -> str:
    """
    Return first 6 hex characters of md5 hash.
    
    Args:
        text: Input text to hash
        
    Returns:
        First 6 hex characters of the md5 hash
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]


def generate_key(path: Path, component: str, label: str = "") -> str:
    """
    Generate a deterministic Streamlit widget key.
    
    Produces a key in format: {PAGE}_{COMPONENT}_{HASH}
    where PAGE is the normalized file stem and HASH is the first 6 hex
    characters of md5(path:component:label).
    
    Args:
        path: Path to the Python file containing the widget
        component: Short uppercase token derived from widget type or label
        label: The first string argument of the widget (for hash seed)
        
    Returns:
        Deterministic key string in format PAGE_COMPONENT_HASH
    """
    page = normalize_page(path)
    hash_seed = f"{path.as_posix()}:{component}:{label}"
    hash_val = short_hash(hash_seed)
    return f"{page}_{component}_{hash_val}"
