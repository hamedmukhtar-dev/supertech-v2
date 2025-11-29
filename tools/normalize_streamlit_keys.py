#!/usr/bin/env python3
"""Scanner/editor for normalizing Streamlit widget keys.

This tool scans the repository for Streamlit widget calls and injects
deterministic keys where missing to prevent StreamlitDuplicateElementId errors.

Usage:
    python tools/normalize_streamlit_keys.py           # Apply changes
    python tools/normalize_streamlit_keys.py --dry-run # Preview changes
"""

import argparse
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.streamlit_keys import generate_key


# Widget types to scan for
WIDGET_TYPES = [
    "st.selectbox",
    "st.multiselect",
    "st.radio",
    "st.text_input",
    "st.checkbox",
    "st.text_area",
    "st.number_input",
    "st.date_input",
]

# Pattern to match widget calls - captures the full call including arguments
WIDGET_PATTERN = re.compile(
    r"(st\.(?:selectbox|multiselect|radio|text_input|checkbox|text_area|number_input|date_input))"
    r"\s*\("
)


def has_key_argument(call_text: str) -> bool:
    """Check if a widget call already has a key= argument."""
    # Look for key= or key = in the call
    return bool(re.search(r"\bkey\s*=", call_text))


def extract_label(call_text: str) -> str:
    """Extract the label (first positional argument) from a widget call."""
    # Find the first string argument after the opening parenthesis
    match = re.search(r'\(\s*(["\'])(.*?)\1', call_text)
    if match:
        return match.group(2)
    # Try to match function call like _(...)
    match = re.search(r'\(\s*_\(["\']([^"\']+)["\']', call_text)
    if match:
        return match.group(1)
    # Try to match variable or expression
    match = re.search(r'\(\s*([^,)]+)', call_text)
    if match:
        return match.group(1).strip()
    return ""


def get_component_name(label: str, widget_type: str) -> str:
    """Generate a component name from label and widget type."""
    # Clean up label for use in key
    label_clean = label.upper()
    # Remove common prefixes/suffixes
    label_clean = re.sub(r'[^\w\s]', '', label_clean)
    label_clean = re.sub(r'\s+', '_', label_clean.strip())

    if label_clean:
        return label_clean[:20]  # Limit length

    # Fallback to widget type
    widget_name = widget_type.replace("st.", "").upper()
    return widget_name


def find_closing_paren(content: str, start: int) -> int:
    """Find the position of the closing parenthesis for a function call."""
    depth = 0
    in_string = None
    escape_next = False
    i = start

    while i < len(content):
        char = content[i]

        if escape_next:
            escape_next = False
            i += 1
            continue

        if char == '\\':
            escape_next = True
            i += 1
            continue

        if in_string:
            # Check for end of triple-quote string
            if len(in_string) == 3:
                if content[i:i+3] == in_string:
                    in_string = None
                    i += 3
                    continue
            elif char == in_string:
                in_string = None
            i += 1
            continue

        if char in ('"', "'"):
            # Check for triple quotes
            if content[i:i+3] in ('"""', "'''"):
                in_string = content[i:i+3]
                i += 3
                continue
            else:
                in_string = char
            i += 1
            continue

        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                return i

        i += 1

    return -1


def inject_key(call_text: str, key: str) -> str:
    """Inject a key= argument into a widget call."""
    # Find the position before the closing parenthesis
    # Handle multiline calls
    last_paren = call_text.rfind(')')

    if last_paren == -1:
        return call_text

    # Check if there are existing arguments
    before_paren = call_text[:last_paren].rstrip()

    # Add comma if needed
    if before_paren.endswith(','):
        separator = " "
    elif before_paren.endswith('('):
        separator = ""
    else:
        separator = ", "

    return before_paren + separator + f'key="{key}")' + call_text[last_paren + 1:]


def process_file(filepath: Path, dry_run: bool = False) -> list:
    """Process a single file and inject keys where needed.

    Returns:
        List of (widget_type, label, key) tuples for changes made
    """
    changes = []

    try:
        content = filepath.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return changes
    except UnicodeDecodeError as e:
        print(f"Encoding error reading {filepath}: {e}")
        return changes
    except OSError as e:
        print(f"Error reading {filepath}: {e}")
        return changes

    original_content = content
    new_content = content
    offset = 0

    for match in WIDGET_PATTERN.finditer(content):
        widget_type = match.group(1)
        start = match.start()

        # Find the full call (including closing parenthesis)
        call_start = match.start()
        paren_start = match.end() - 1  # Position of opening paren
        call_end = find_closing_paren(content, paren_start)

        if call_end == -1:
            continue

        call_text = content[call_start:call_end + 1]

        # Skip if already has a key
        if has_key_argument(call_text):
            continue

        # Extract label and generate key
        label = extract_label(call_text)
        component = get_component_name(label, widget_type)
        key = generate_key(filepath, component, label)

        # Inject the key
        new_call = inject_key(call_text, key)

        # Apply the change with offset adjustment
        adj_start = call_start + offset
        adj_end = call_end + 1 + offset
        new_content = new_content[:adj_start] + new_call + new_content[adj_end:]

        # Update offset for subsequent replacements
        offset += len(new_call) - len(call_text)

        changes.append((widget_type, label, key))

    if changes and not dry_run:
        filepath.write_text(new_content, encoding="utf-8")

    return changes


def scan_repository(repo_root: Path, dry_run: bool = False) -> dict:
    """Scan repository for Python files and process them.

    Returns:
        Dictionary mapping filepath to list of changes
    """
    all_changes = {}

    # Find all Python files
    for py_file in repo_root.rglob("*.py"):
        # Skip __pycache__ and hidden directories
        if "__pycache__" in str(py_file) or any(
            part.startswith(".") for part in py_file.parts
        ):
            continue

        # Skip this tool itself
        if py_file.name == "normalize_streamlit_keys.py":
            continue

        changes = process_file(py_file, dry_run=dry_run)
        if changes:
            all_changes[py_file] = changes

    return all_changes


def generate_changelog(changes: dict, output_path: Path, repo_root: Path):
    """Generate a changelog file documenting all injected keys."""
    lines = [
        "# Streamlit Keys Normalization Changelog",
        "# Generated by tools/normalize_streamlit_keys.py",
        "",
        "This file documents all widget keys that were automatically injected.",
        "",
    ]

    for filepath, file_changes in sorted(changes.items()):
        rel_path = filepath.relative_to(repo_root)
        lines.append(f"## {rel_path}")
        lines.append("")
        for widget_type, label, key in file_changes:
            lines.append(f"- {widget_type}: label='{label}' -> key='{key}'")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def find_repo_root(start_path: Path) -> Path:
    """Find the repository root by looking for .git directory."""
    current = start_path.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    # Fallback to parent of tools directory
    return start_path.parent


def main():
    parser = argparse.ArgumentParser(
        description="Normalize Streamlit widget keys to prevent duplicate element IDs"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=Path("normalize_keys_changelog.txt"),
        help="Path to changelog output file",
    )
    args = parser.parse_args()

    # Determine repository root
    repo_root = find_repo_root(Path(__file__).parent)

    print(f"Scanning repository: {repo_root}")
    if args.dry_run:
        print("DRY RUN - no files will be modified\n")

    changes = scan_repository(repo_root, dry_run=args.dry_run)

    if not changes:
        print("No widgets found that need key injection.")
        return

    print(f"\n{'Would modify' if args.dry_run else 'Modified'} {len(changes)} file(s):\n")

    for filepath, file_changes in sorted(changes.items()):
        rel_path = filepath.relative_to(repo_root)
        print(f"  {rel_path}:")
        for widget_type, label, key in file_changes:
            print(f"    - {widget_type} '{label}' -> key='{key}'")

    if not args.dry_run:
        changelog_path = repo_root / args.changelog
        generate_changelog(changes, changelog_path, repo_root)
        print(f"\nChangelog written to: {changelog_path}")


if __name__ == "__main__":
    main()
