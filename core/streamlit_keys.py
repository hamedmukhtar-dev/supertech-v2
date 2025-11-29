"""Deterministic Streamlit key generator for widget elements."""
import hashlib
import re
from pathlib import Path


def normalize_page(path: Path) -> str:
    """Return normalized page token from file path stem (non-alphanumeric -> underscore)."""
    stem = path.stem
    return re.sub(r'[^a-zA-Z0-9]', '_', stem)


def short_hash(text: str) -> str:
    """Return first 6 chars of md5 hash of the text."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]


def generate_key(path: Path, component: str, label: str = "") -> str:
    """
    Generate a deterministic Streamlit widget key.
    
    Returns: f"{PAGE}_{COMPONENT}_{HASH}" where:
      - PAGE = normalize_page(path)
      - COMPONENT = component name (e.g. 'selectbox')
      - HASH = short_hash(f"{path.as_posix()}:{component}:{label}")
    """
    page = normalize_page(path)
    hash_input = f"{path.as_posix()}:{component}:{label}"
    return f"{page}_{component}_{short_hash(hash_input)}"
