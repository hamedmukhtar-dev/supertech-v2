#!/usr/bin/env python3
"""Scanner/editor to normalize Streamlit widget keys across the codebase.

This tool scans the repository for Streamlit widget calls and injects deterministic
key= arguments where missing, using core.streamlit_keys.generate_key.

Usage:
    python tools/normalize_streamlit_keys.py --dry-run    # Preview changes
    python tools/normalize_streamlit_keys.py              # Apply changes
"""

import argparse
import os
import re
import sys
from pathlib import Path

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.streamlit_keys import generate_key, short_hash

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

# Pattern to match widget calls (handles both st.widget and st.sidebar.widget)
WIDGET_PATTERN = re.compile(
    r'(st\.(?:sidebar\.)?(?:' + '|'.join(w.replace('st.', '') for w in WIDGET_TYPES) + r'))\s*\(',
    re.MULTILINE
)


def find_widget_calls(content: str):
    """Find all widget calls in the content.
    
    Yields:
        Tuples of (start_pos, end_pos, widget_type, has_key)
    """
    for match in WIDGET_PATTERN.finditer(content):
        widget_type = match.group(1)
        start = match.start()
        
        # Find the matching closing parenthesis
        paren_count = 0
        in_string = False
        string_char = None
        i = match.end() - 1  # Start at the opening paren
        
        while i < len(content):
            char = content[i]
            
            # Handle string literals
            if char in ('"', "'") and (i == 0 or content[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
            
            if not in_string:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        break
            i += 1
        
        end = i + 1
        call_content = content[start:end]
        
        # Check if key= already exists
        has_key = bool(re.search(r'\bkey\s*=', call_content))
        
        yield start, end, widget_type, call_content, has_key


def extract_label(call_content: str) -> str:
    """Extract the first string argument (label) from a widget call."""
    # Match the first string argument after the opening paren
    # Handle both direct strings and function-wrapped strings like _(f"Label")
    
    # Try direct string first: st.text_input("Label")
    match = re.search(r'\(\s*["\']([^"\']*)["\']', call_content)
    if match:
        return match.group(1)
    
    # Try function-wrapped string: st.text_input(_(f"Label")) or st.text_input(_("Label"))
    match = re.search(r'\(\s*_\(\s*f?["\']([^"\']*)["\']', call_content)
    if match:
        return match.group(1)
    
    return ""


def component_from_label(label: str) -> str:
    """Convert a label to a component identifier."""
    # Clean up the label for use as component name
    clean = re.sub(r'[^\w\s]', '', label)
    words = clean.upper().split()
    if words:
        return "_".join(words[:2])  # Use first two words max
    return "WIDGET"


def inject_key(call_content: str, key: str) -> str:
    """Inject a key= argument into a widget call."""
    # Find the position just before the closing paren
    last_paren = call_content.rfind(')')
    if last_paren == -1:
        return call_content
    
    # Check if there's a trailing comma
    before_paren = call_content[:last_paren].rstrip()
    if before_paren.endswith(','):
        # Already has trailing comma
        new_content = f'{call_content[:last_paren]} key="{key}")'
    else:
        # Add comma before key
        new_content = f'{call_content[:last_paren]}, key="{key}")'
    
    return new_content


def process_file(filepath: Path, dry_run: bool = True) -> list:
    """Process a single file and inject keys where needed.
    
    Returns:
        List of (widget_type, label, key) for changelog
    """
    changes = []
    
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return changes
    
    original_content = content
    offset = 0  # Track position offset as we make changes
    
    widget_calls = list(find_widget_calls(content))
    
    for start, end, widget_type, call_content, has_key in widget_calls:
        if has_key:
            continue  # Skip widgets that already have keys
        
        # Extract label and generate key
        label = extract_label(call_content)
        component = component_from_label(label) if label else "WIDGET"
        key = generate_key(filepath, component, label)
        
        # Inject the key
        new_call = inject_key(call_content, key)
        
        # Apply the change with offset
        adjusted_start = start + offset
        adjusted_end = end + offset
        content = content[:adjusted_start] + new_call + content[adjusted_end:]
        
        # Update offset
        offset += len(new_call) - len(call_content)
        
        changes.append((str(filepath), widget_type, label, key))
    
    if changes and content != original_content:
        if not dry_run:
            filepath.write_text(content, encoding='utf-8')
        
    return changes


def scan_repository(repo_root: Path, dry_run: bool = True) -> list:
    """Scan the repository for files with widget calls.
    
    Returns:
        List of all changes made
    """
    all_changes = []
    
    # Files to scan (Python files, excluding hidden dirs and tools)
    for py_file in repo_root.rglob('*.py'):
        # Skip hidden directories and tools directory (don't modify the tool itself)
        if any(part.startswith('.') for part in py_file.parts):
            continue
        if 'tools' in py_file.parts:
            continue
            
        try:
            content = py_file.read_text(encoding='utf-8')
            if 'st.' in content:  # Quick check for Streamlit usage
                changes = process_file(py_file, dry_run)
                all_changes.extend(changes)
        except Exception as e:
            print(f"Warning: Could not process {py_file}: {e}")
    
    return all_changes


def write_changelog(changes: list, output_path: Path, repo_root: Path):
    """Write the changelog file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Streamlit Keys Normalization Changelog\n")
        f.write("# Generated by tools/normalize_streamlit_keys.py\n")
        f.write("#\n")
        f.write("# Format: FILE | WIDGET | LABEL | KEY\n")
        f.write("#" + "=" * 79 + "\n\n")
        
        if not changes:
            f.write("No changes needed - all widgets already have explicit keys.\n")
            return
        
        current_file = None
        for filepath, widget, label, key in sorted(changes):
            # Convert to relative path for cleaner output
            try:
                rel_path = Path(filepath).relative_to(repo_root)
            except ValueError:
                rel_path = filepath
            
            if filepath != current_file:
                if current_file is not None:
                    f.write("\n")
                f.write(f"## {rel_path}\n")
                current_file = filepath
            
            label_display = label if label else "(no label)"
            f.write(f"  - {widget}: {label_display} -> key=\"{key}\"\n")


def main():
    parser = argparse.ArgumentParser(
        description='Normalize Streamlit widget keys to prevent duplicate element IDs'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--changelog',
        type=str,
        default='normalize_keys_changelog.txt',
        help='Path to output changelog file (default: normalize_keys_changelog.txt)'
    )
    
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parent.parent
    
    print(f"Scanning repository: {repo_root}")
    print(f"Dry run: {args.dry_run}")
    print()
    
    changes = scan_repository(repo_root, dry_run=args.dry_run)
    
    if changes:
        print(f"Found {len(changes)} widget(s) needing keys:")
        for filepath, widget, label, key in changes:
            print(f"  {filepath}: {widget} '{label}' -> key=\"{key}\"")
    else:
        print("No widgets found needing keys.")
    
    # Write changelog
    changelog_path = repo_root / args.changelog
    write_changelog(changes, changelog_path, repo_root)
    print(f"\nChangelog written to: {changelog_path}")
    
    if args.dry_run:
        print("\n[DRY RUN] No files were modified.")
    else:
        print(f"\n{len(changes)} widget(s) updated.")


if __name__ == '__main__':
    main()
