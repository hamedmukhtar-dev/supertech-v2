"""
Deterministic Streamlit key generator for eliminating StreamlitDuplicateElementId errors.
"""
import hashlib
from pathlib import Path


def normalize_page(path: Path) -> str:
    """
    Convert file path stem to safe PAGE token.
    
    Args:
        path: Path object to the file
        
    Returns:
        Uppercase stem with non-alphanumeric characters replaced by underscores
    """
    stem = path.stem
    # Replace non-alphanumeric characters with underscores
    safe_stem = ''.join(c if c.isalnum() else '_' for c in stem)
    return safe_stem.upper()


def short_hash(text: str) -> str:
    """
    Return first 6 hex chars of md5(text).
    
    Args:
        text: String to hash
        
    Returns:
        First 6 hex characters of the MD5 hash
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]


def generate_key(path: Path, component: str, label: str = "") -> str:
    """
    Generate a deterministic key for a Streamlit widget.
    
    Args:
        path: Path to the file containing the widget
        component: Widget component type (e.g., 'selectbox', 'text_input')
        label: Widget label text (optional)
        
    Returns:
        Key in format "{PAGE}_{COMPONENT}_{HASH}"
    """
    page = normalize_page(path)
    # Get repo-relative path for hash input
    try:
        repo_path = str(path.resolve())
    except Exception:
        repo_path = str(path)
    
    hash_input = f"{repo_path}:{component}:{label}"
    hash_value = short_hash(hash_input)
    
    return f"{page}_{component}_{hash_value}"
