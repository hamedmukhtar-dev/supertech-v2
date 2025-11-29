#!/usr/bin/env python3
"""
Streamlit Widget Key Normalizer

Scans Python files for Streamlit widget calls that are missing explicit keys,
and injects deterministic keys using the core.streamlit_keys module.

Usage:
    python tools/normalize_streamlit_keys.py [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.streamlit_keys import generate_key


# Streamlit widgets that need unique keys
WIDGET_PATTERNS = [
    'selectbox',
    'multiselect',
    'radio',
    'text_input',
    'checkbox',
    'text_area',
    'number_input',
    'date_input',
]

# Language-related labels that need special handling
LANGUAGE_LABELS = ['Language', 'اللغة', '🌐']


def find_python_files(repo_root: Path) -> list:
    """Find all Python files in the repository."""
    python_files = []
    for pattern in ['*.py', 'pages/*.py', 'core/**/*.py', 'utils/*.py']:
        python_files.extend(repo_root.glob(pattern))
    return sorted(set(python_files))


def has_key_argument(call_text: str) -> bool:
    """Check if a widget call already has a key= argument."""
    # Check for key= anywhere in the call
    return bool(re.search(r'\bkey\s*=', call_text))


def extract_label(call_text: str) -> str:
    """Extract the first argument (label) from a widget call."""
    # Match the first string argument (single or double quoted)
    # Handle cases like st.selectbox("Label", ...)
    match = re.search(r'\(\s*(["\'])(.*?)\1', call_text)
    if match:
        return match.group(2)
    
    # Handle cases like st.selectbox(variable, ...)
    match = re.search(r'\(\s*([^,\)]+)', call_text)
    if match:
        return match.group(1).strip()
    
    return ""


def is_language_selector(label: str) -> bool:
    """Check if a widget is a language selector based on its label."""
    for lang_label in LANGUAGE_LABELS:
        if lang_label in label:
            return True
    return False


def find_widget_call_end(content: str, start_pos: int) -> int:
    """Find the end position of a widget call (matching closing parenthesis)."""
    paren_count = 0
    in_string = None
    escape_next = False
    
    i = start_pos
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
            if char == in_string:
                in_string = None
        else:
            if char in ('"', "'"):
                # Check for triple quotes
                if content[i:i+3] in ('"""', "'''"):
                    in_string = content[i:i+3]
                    i += 3
                    continue
                in_string = char
            elif char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    return i + 1
        
        i += 1
    
    return len(content)


def process_file(file_path: Path, dry_run: bool = False) -> list:
    """
    Process a single Python file, adding keys to widgets that don't have them.
    
    Returns a list of changes made: [(line_number, widget_type, label), ...]
    """
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return changes
    
    original_content = content
    lines = content.split('\n')
    
    # Track widgets per component type to ensure unique keys
    widget_counts = {}
    
    for widget in WIDGET_PATTERNS:
        # Pattern to match st.widget_name( calls
        pattern = rf'(st\.{widget}\s*\()'
        
        # Find all matches with their positions
        for match in re.finditer(pattern, content):
            start_pos = match.start()
            call_start = match.end() - 1  # Position of opening paren
            call_end = find_widget_call_end(content, call_start)
            
            call_text = content[match.start():call_end]
            
            # Skip if already has a key
            if has_key_argument(call_text):
                continue
            
            # Extract label
            label = extract_label(call_text)
            
            # Generate unique key
            # Track count for this widget type to ensure uniqueness
            widget_key = (str(file_path), widget, label)
            if widget_key not in widget_counts:
                widget_counts[widget_key] = 0
            widget_counts[widget_key] += 1
            
            # If same widget+label appears multiple times, add suffix
            count = widget_counts[widget_key]
            if count > 1:
                unique_label = f"{label}_{count}"
            else:
                unique_label = label
            
            key = generate_key(file_path, widget, unique_label)
            
            # Calculate line number for reporting
            line_number = content[:start_pos].count('\n') + 1
            
            changes.append((line_number, widget, label))
    
    # Now apply changes - we need to do this carefully to avoid position shifts
    if changes and not dry_run:
        new_content = content
        
        # Process in reverse order to avoid position shifts
        for widget in WIDGET_PATTERNS:
            pattern = rf'(st\.{widget}\s*\()([^)]*?)(\))'
            
            def replace_widget(m):
                full_match = m.group(0)
                prefix = m.group(1)
                
                # Find the full call including nested parens
                start = m.start()
                call_start = m.start() + len(prefix) - 1
                call_end = find_widget_call_end(new_content, call_start)
                full_call = new_content[m.start():call_end]
                
                if has_key_argument(full_call):
                    return full_call
                
                label = extract_label(full_call)
                
                # Track for uniqueness
                widget_key = (str(file_path), widget, label)
                
                key = generate_key(file_path, widget, label)
                
                # Find position to insert key= before the closing paren
                # We need to insert before the last )
                insert_pos = full_call.rfind(')')
                
                if insert_pos > 0:
                    # Check if there's already content (need comma)
                    before_close = full_call[:insert_pos].rstrip()
                    if before_close.endswith(','):
                        new_call = full_call[:insert_pos] + f'key="{key}")'
                    elif before_close.endswith('('):
                        new_call = full_call[:insert_pos] + f'key="{key}")'
                    else:
                        new_call = full_call[:insert_pos] + f', key="{key}")'
                    
                    # Handle language selectors - add normalization line
                    if is_language_selector(label):
                        # Add normalization after the widget
                        norm_line = f'\n    st.session_state["lang"] = "ar" if {full_call[:full_call.find(")")].split("=")[-1].strip() if "=" in full_call else "selected"} == "العربية" else "en"'
                        # This is complex - we'll handle it separately
                        pass
                    
                    return new_call
                
                return full_call
            
            # Apply replacements
            new_content = re.sub(pattern, replace_widget, new_content, flags=re.DOTALL)
        
        # Write back
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
    
    return changes


def process_file_v2(file_path: Path, dry_run: bool = False) -> list:
    """
    Process a single Python file, adding keys to widgets that don't have them.
    Uses a line-by-line approach for more reliable modifications.
    
    Returns a list of changes made: [(line_number, widget_type, label), ...]
    """
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return changes
    
    original_content = content
    modified_content = content
    
    # Track used keys to ensure uniqueness
    used_keys = set()
    
    for widget in WIDGET_PATTERNS:
        # Pattern to match st.widget_name( calls - handles multi-line
        # We'll process the content as a whole
        
        offset = 0
        search_start = 0
        
        while True:
            # Find next occurrence
            pattern = rf'st\.{widget}\s*\('
            match = re.search(pattern, modified_content[search_start:])
            
            if not match:
                break
            
            abs_start = search_start + match.start()
            call_start = search_start + match.end() - 1  # Position of opening paren
            call_end = find_widget_call_end(modified_content, call_start)
            
            call_text = modified_content[abs_start:call_end]
            
            # Move search position forward
            search_start = call_end
            
            # Skip if already has a key
            if has_key_argument(call_text):
                continue
            
            # Extract label
            label = extract_label(call_text)
            
            # Generate unique key
            base_key = generate_key(file_path, widget, label)
            key = base_key
            suffix = 1
            while key in used_keys:
                suffix += 1
                key = f"{base_key}_{suffix}"
            used_keys.add(key)
            
            # Calculate line number for reporting
            line_number = modified_content[:abs_start].count('\n') + 1
            
            changes.append((line_number, widget, label))
            
            if not dry_run:
                # Find position to insert key= before the closing paren
                insert_pos = call_text.rfind(')')
                
                if insert_pos > 0:
                    # Check if there's already content (need comma)
                    before_close = call_text[:insert_pos].rstrip()
                    if before_close.endswith(','):
                        new_call = call_text[:insert_pos] + f'key="{key}")'
                    elif before_close.endswith('('):
                        new_call = call_text[:insert_pos] + f'key="{key}")'
                    else:
                        new_call = call_text[:insert_pos] + f', key="{key}")'
                    
                    # Replace in content
                    modified_content = modified_content[:abs_start] + new_call + modified_content[call_end:]
                    
                    # Adjust search position for the change in length
                    len_diff = len(new_call) - len(call_text)
                    search_start += len_diff
                    
                    # Handle language selectors - check if normalization is needed
                    if is_language_selector(label):
                        # Check if there's already a normalization line after
                        after_widget = modified_content[abs_start + len(new_call):abs_start + len(new_call) + 200]
                        if 'session_state' not in after_widget.split('\n')[0] and 'session_state["lang"]' not in after_widget[:100]:
                            # We would add normalization, but this is complex
                            # For now, just note it in the changelog
                            pass
    
    # Write back if changes were made
    if modified_content != original_content and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
    
    return changes


def write_changelog(changes: dict, repo_root: Path):
    """Write the changelog file listing all changes."""
    changelog_path = repo_root / 'normalize_keys_changelog.txt'
    
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write("Streamlit Widget Key Normalization Changelog\n")
        f.write("=" * 50 + "\n\n")
        
        for file_path, file_changes in sorted(changes.items()):
            if file_changes:
                f.write(f"{file_path}:\n")
                for line_num, widget, label in file_changes:
                    display_label = label[:40] + "..." if len(label) > 40 else label
                    f.write(f"  Line {line_num}: widget={widget} label=\"{display_label}\"\n")
                f.write("\n")
        
        if not any(changes.values()):
            f.write("No changes needed - all widgets already have explicit keys.\n")


def main():
    parser = argparse.ArgumentParser(
        description='Normalize Streamlit widget keys across the codebase'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--repo-root',
        type=Path,
        default=Path(__file__).parent.parent,
        help='Repository root directory'
    )
    
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    
    print(f"Scanning repository: {repo_root}")
    if args.dry_run:
        print("DRY RUN - no files will be modified\n")
    
    python_files = find_python_files(repo_root)
    print(f"Found {len(python_files)} Python files\n")
    
    all_changes = {}
    total_changes = 0
    
    for file_path in python_files:
        relative_path = file_path.relative_to(repo_root)
        changes = process_file_v2(file_path, dry_run=args.dry_run)
        
        if changes:
            all_changes[str(relative_path)] = changes
            total_changes += len(changes)
            print(f"{'[DRY RUN] ' if args.dry_run else ''}Modified {relative_path}: {len(changes)} widget(s)")
            for line_num, widget, label in changes:
                print(f"  Line {line_num}: st.{widget}(\"{label[:30]}...\")" if len(label) > 30 else f"  Line {line_num}: st.{widget}(\"{label}\")")
    
    # Write changelog
    if not args.dry_run:
        write_changelog(all_changes, repo_root)
        print(f"\nChangelog written to: normalize_keys_changelog.txt")
    
    print(f"\nTotal: {total_changes} widget(s) {'would be ' if args.dry_run else ''}updated")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
