#!/usr/bin/env python3
"""
Normalize Streamlit widget keys across the codebase.

This tool scans Python files for Streamlit widget calls and injects deterministic
key= arguments where they are missing, to prevent StreamlitDuplicateElementId errors.

Usage:
    python tools/normalize_streamlit_keys.py [--dry-run]
    
Options:
    --dry-run    Only write the changelog without modifying files
"""
import argparse
import re
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.streamlit_keys import normalize_page, short_hash, generate_key

# Streamlit widgets that should have explicit keys
WIDGET_PATTERNS = [
    'st.selectbox',
    'st.multiselect',
    'st.radio',
    'st.text_input',
    'st.checkbox',
    'st.text_area',
    'st.number_input',
    'st.date_input',
]

# Directories to skip
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env'}


def extract_label_from_call(call_text: str) -> str:
    """
    Extract the label (first positional argument) from a widget call.
    
    Args:
        call_text: The full widget call text including parentheses
        
    Returns:
        The extracted label string, or empty string if not found
    """
    # Match the first string argument after the opening parenthesis
    # Handles both single and double quoted strings, including f-strings
    match = re.search(r'\(\s*(?:f?["\'])(.*?)(?:["\'])', call_text, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def derive_component_name(label: str, widget_type: str) -> str:
    """
    Derive a short component name from the label text.
    
    Args:
        label: The widget label text
        widget_type: The type of widget (e.g., 'selectbox', 'text_input')
        
    Returns:
        A short uppercase token for the component
    """
    # Language selectors
    if any(kw in label.lower() for kw in ['language', 'اللغة', '🌐']):
        return 'LANG'
    
    # Clean and normalize the label
    cleaned = re.sub(r'[^\w\s]', '', label)
    words = cleaned.split()
    
    if not words:
        # Fallback to widget type if no label
        return widget_type.upper().replace('.', '_')
    
    # Take first 2-3 significant words and uppercase
    significant = [w.upper() for w in words[:3] if len(w) > 1]
    if significant:
        return '_'.join(significant)
    
    return widget_type.upper().replace('.', '_')


def has_key_argument(call_text: str) -> bool:
    """
    Check if a widget call already has a key= argument.
    
    Args:
        call_text: The widget call text
        
    Returns:
        True if the call already has a key= argument
    """
    # Match key= followed by a value (string, variable, or expression)
    return bool(re.search(r'\bkey\s*=', call_text))


def find_widget_calls(content: str, file_path: Path) -> list[dict]:
    """
    Find all Streamlit widget calls in the file content.
    
    Args:
        content: The file content
        file_path: Path to the file
        
    Returns:
        List of dicts with widget info (line, widget_type, label, has_key, start, end)
    """
    widgets = []
    
    for widget in WIDGET_PATTERNS:
        # Pattern to find widget calls - handles multiline calls
        # We need to find the full call including all arguments
        pattern = re.escape(widget) + r'\s*\('
        
        for match in re.finditer(pattern, content):
            start = match.start()
            # Find the matching closing parenthesis
            paren_depth = 0
            end = match.end()
            in_string = False
            string_char = None
            
            for i, char in enumerate(content[match.end():], match.end()):
                if not in_string:
                    if char in ('"', "'"):
                        in_string = True
                        string_char = char
                    elif char == '(':
                        paren_depth += 1
                    elif char == ')':
                        if paren_depth == 0:
                            end = i + 1
                            break
                        paren_depth -= 1
                else:
                    if char == string_char and content[i-1] != '\\':
                        in_string = False
            
            call_text = content[start:end]
            
            # Find line number
            line_num = content[:start].count('\n') + 1
            
            label = extract_label_from_call(call_text)
            has_key = has_key_argument(call_text)
            
            widgets.append({
                'line': line_num,
                'widget_type': widget,
                'label': label,
                'has_key': has_key,
                'start': start,
                'end': end,
                'call_text': call_text,
            })
    
    return widgets


def inject_key(call_text: str, key: str) -> str:
    """
    Inject a key= argument into a widget call.
    
    Args:
        call_text: The original widget call text
        key: The key to inject
        
    Returns:
        The modified call text with key= added
    """
    # Find the position before the closing parenthesis
    last_paren = call_text.rfind(')')
    if last_paren == -1:
        return call_text
    
    # Check if there are existing arguments
    content_before_paren = call_text[:last_paren].rstrip()
    
    # Add comma if needed
    if content_before_paren.endswith(','):
        # Already ends with comma
        new_call = f'{content_before_paren} key="{key}")'
    elif content_before_paren.endswith('('):
        # Empty call - shouldn't happen for widgets with labels
        new_call = f'{content_before_paren}key="{key}")'
    else:
        # Add comma before key
        new_call = f'{content_before_paren}, key="{key}")'
    
    return new_call


def process_file(file_path: Path, dry_run: bool = False) -> list[dict]:
    """
    Process a single Python file and inject keys where needed.
    
    Args:
        file_path: Path to the file to process
        dry_run: If True, don't modify the file
        
    Returns:
        List of changes made (for changelog)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, IOError):
        return []
    
    widgets = find_widget_calls(content, file_path)
    
    # Filter to widgets without keys
    widgets_to_fix = [w for w in widgets if not w['has_key']]
    
    if not widgets_to_fix:
        return []
    
    changes = []
    
    # Process in reverse order to maintain correct positions
    widgets_to_fix.sort(key=lambda x: x['start'], reverse=True)
    
    for widget in widgets_to_fix:
        widget_type_short = widget['widget_type'].replace('st.', '')
        component = derive_component_name(widget['label'], widget_type_short)
        key = generate_key(file_path, component, widget['label'])
        
        new_call = inject_key(widget['call_text'], key)
        
        if not dry_run:
            content = content[:widget['start']] + new_call + content[widget['end']:]
        
        changes.append({
            'file': str(file_path.relative_to(PROJECT_ROOT)),
            'widget': widget['widget_type'],
            'label': widget['label'],
            'key': key,
            'line': widget['line'],
        })
    
    if not dry_run and changes:
        file_path.write_text(content, encoding='utf-8')
    
    return changes


def scan_repository(dry_run: bool = False) -> list[dict]:
    """
    Scan the repository for Python files and process them.
    
    Args:
        dry_run: If True, don't modify files
        
    Returns:
        List of all changes made
    """
    all_changes = []
    
    for file_path in PROJECT_ROOT.rglob('*.py'):
        # Skip excluded directories
        parts = file_path.parts
        if any(skip_dir in parts for skip_dir in SKIP_DIRS):
            continue
        
        # Skip this tool itself
        if file_path.name == 'normalize_streamlit_keys.py':
            continue
        
        changes = process_file(file_path, dry_run)
        all_changes.extend(changes)
    
    return all_changes


def write_changelog(changes: list[dict], output_path: Path) -> None:
    """
    Write the changelog file.
    
    Args:
        changes: List of changes made
        output_path: Path to write the changelog
    """
    with output_path.open('w', encoding='utf-8') as f:
        f.write("# Streamlit Key Normalization Changelog\n")
        f.write("# Generated by tools/normalize_streamlit_keys.py\n")
        f.write("#\n")
        f.write("# Format: <file>: widget=<widget_type> label=<label> key=<generated_key>\n")
        f.write("#\n\n")
        
        for change in sorted(changes, key=lambda x: (x['file'], x['line'])):
            f.write(f"{change['file']}: widget={change['widget']} label=\"{change['label']}\" key=\"{change['key']}\"\n")


def main():
    parser = argparse.ArgumentParser(
        description='Normalize Streamlit widget keys across the codebase'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only write the changelog without modifying files'
    )
    args = parser.parse_args()
    
    print(f"Scanning repository: {PROJECT_ROOT}")
    print(f"Dry run: {args.dry_run}")
    print()
    
    changes = scan_repository(dry_run=args.dry_run)
    
    changelog_path = PROJECT_ROOT / 'normalize_keys_changelog.txt'
    write_changelog(changes, changelog_path)
    
    print(f"Found {len(changes)} widgets requiring key injection")
    print(f"Changelog written to: {changelog_path}")
    
    if changes:
        print("\nChanges:")
        for change in changes:
            print(f"  {change['file']}: {change['widget']} ({change['label']}) -> {change['key']}")
    
    if args.dry_run:
        print("\n[DRY RUN] No files were modified")
    else:
        print(f"\nModified {len(set(c['file'] for c in changes))} files")


if __name__ == '__main__':
    main()
