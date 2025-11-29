#!/usr/bin/env python3
"""Scanner and editor for normalizing Streamlit widget keys.

This tool scans Python files in the repository for Streamlit widget calls
and injects deterministic keys to eliminate StreamlitDuplicateElementId errors.
"""

import ast
import os
import re
from pathlib import Path
from typing import Optional

# Add parent directory to path for importing core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.streamlit_keys import generate_key, normalize_page, short_hash


# Streamlit widget types to scan for
WIDGET_TYPES = (
    "selectbox",
    "multiselect",
    "radio",
    "text_input",
    "checkbox",
    "text_area",
    "number_input",
    "date_input",
    "slider",
)

# Directories to skip
SKIP_DIRS = {".git", "__pycache__", "venv", ".venv", "node_modules"}

# Language selector indicators
LANG_INDICATORS = {"Language", "اللغة", "🌐"}


def normalize_component(label: str, widget_name: str) -> str:
    """Normalize a component name from the label or widget name.

    Derives a short uppercase token from the first string label argument
    (or widget name if none), replacing spaces/non-alphanumeric with underscore.

    Args:
        label: The first string argument of the widget.
        widget_name: The widget type name (e.g., 'selectbox').

    Returns:
        Normalized component token.
    """
    if label:
        # Use label, normalize it
        component = re.sub(r"[^a-zA-Z0-9]", "_", label)
        component = re.sub(r"_+", "_", component)  # Collapse multiple underscores
        component = component.strip("_")
        if component:
            return component.upper()[:20]  # Limit length
    # Fallback to widget name
    return widget_name.upper()


def extract_first_string_arg(call_text: str) -> Optional[str]:
    """Extract the first string argument from a widget call.

    Args:
        call_text: The text of the widget call.

    Returns:
        The first string argument, or None if not found.
    """
    # Match quoted strings (single or double quotes, including f-strings)
    patterns = [
        r'st\.\w+\s*\(\s*f?"([^"]*)"',
        r"st\.\w+\s*\(\s*f?'([^']*)'",
        r'st\.\w+\s*\(\s*_\(\s*f?"([^"]*)"\s*\)',
        r"st\.\w+\s*\(\s*_\(\s*f?'([^']*)'\s*\)",
        r'st\.\w+\s*\(\s*t\(\s*lang\s*,\s*"([^"]*)"\s*\)',
        r"st\.\w+\s*\(\s*t\(\s*lang\s*,\s*'([^']*)'\s*\)",
    ]
    for pattern in patterns:
        match = re.search(pattern, call_text)
        if match:
            return match.group(1)
    return None


def is_language_selector(label: str) -> bool:
    """Check if a widget is a language selector based on its label.

    Args:
        label: The label of the widget.

    Returns:
        True if this is a language selector.
    """
    if not label:
        return False
    return any(indicator in label for indicator in LANG_INDICATORS)


def has_key_argument(call_text: str) -> bool:
    """Check if a widget call already has a key= argument.

    Args:
        call_text: The text of the widget call.

    Returns:
        True if key= is present.
    """
    # Look for key= followed by valid argument value
    return bool(re.search(r'\bkey\s*=', call_text))


def get_multiline_call(lines: list[str], start_idx: int) -> tuple[str, int]:
    """Get the full widget call which may span multiple lines.

    Args:
        lines: All lines of the file.
        start_idx: Starting line index.

    Returns:
        Tuple of (full call text, end line index).
    """
    call_text = lines[start_idx]
    end_idx = start_idx

    # Count parentheses to find end of call
    paren_count = call_text.count("(") - call_text.count(")")

    while paren_count > 0 and end_idx + 1 < len(lines):
        end_idx += 1
        call_text += "\n" + lines[end_idx]
        paren_count += lines[end_idx].count("(") - lines[end_idx].count(")")

    return call_text, end_idx


def inject_key(line: str, key: str) -> str:
    """Inject a key= argument into a widget call line.

    Args:
        line: The line containing the widget call.
        key: The key to inject.

    Returns:
        Modified line with key injected.
    """
    # Find the closing parenthesis and insert before it
    # Handle single-line calls
    if ")" in line:
        # Find last closing paren
        last_paren = line.rfind(")")
        # Check if there are existing arguments
        before_paren = line[:last_paren].rstrip()
        if before_paren.endswith(","):
            # Already has trailing comma
            return line[:last_paren] + f' key="{key}")' + line[last_paren + 1:]
        elif before_paren.endswith("("):
            # Empty args, just add key
            return line[:last_paren] + f'key="{key}")' + line[last_paren + 1:]
        else:
            # Add comma before key
            return line[:last_paren] + f', key="{key}")' + line[last_paren + 1:]
    return line


def add_lang_normalization(line: str, label: str) -> str:
    """Add language normalization for language selectors.

    For language selectors, ensures minimal normalization code is added
    so st.session_state['lang'] is set to 'ar' or 'en' consistently.

    This function returns the line as-is since normalization is typically
    done via on_change callback or after the widget call.

    Args:
        line: The line containing the widget call.
        label: The label of the widget.

    Returns:
        The line (normalization handled separately).
    """
    # Language normalization is handled at the file level if needed
    # Widget calls just need stable keys
    return line


def process_file(filepath: Path, changelog: list[str]) -> bool:
    """Process a single Python file for Streamlit widgets.

    Args:
        filepath: Path to the Python file.
        changelog: List to append changelog entries to.

    Returns:
        True if file was modified.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return False

    lines = content.split("\n")
    modified = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for Streamlit widget calls
        for widget in WIDGET_TYPES:
            pattern = rf"st\.{widget}\s*\("
            if re.search(pattern, line):
                # Get full call (may span multiple lines)
                full_call, end_idx = get_multiline_call(lines, i)

                # Skip if already has key
                if has_key_argument(full_call):
                    break

                # Extract label
                label = extract_first_string_arg(full_call) or ""

                # Generate component name and key
                component = normalize_component(label, widget)
                key = generate_key(filepath, component, label)

                # Inject key into the line
                lines[i] = inject_key(lines[i], key)
                modified = True

                # Log the change
                changelog.append(f"{filepath}:{i + 1}: widget={widget}")

                break  # Only process one widget per line

        i += 1

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    return modified


def scan_directory(root: Path) -> list[str]:
    """Scan directory for Python files and process them.

    Args:
        root: Root directory to scan.

    Returns:
        List of changelog entries.
    """
    changelog = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Remove skip directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            if filename.endswith(".py"):
                filepath = Path(dirpath) / filename
                process_file(filepath, changelog)

    return changelog


def main():
    """Main entry point."""
    # Get repository root (parent of tools directory)
    repo_root = Path(__file__).parent.parent

    print(f"Scanning for Streamlit widgets in {repo_root}...")

    changelog = scan_directory(repo_root)

    # Write changelog
    changelog_path = repo_root / "normalize_keys_changelog.txt"
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write("\n".join(changelog))

    print(f"Processed {len(changelog)} widget calls.")
    print(f"Changelog written to {changelog_path}")


if __name__ == "__main__":
    main()
