#!/usr/bin/env python3
"""
Scanner/editor for normalizing Streamlit widget keys.

Scans repository Python files for Streamlit widget calls and injects
deterministic keys for widgets that don't have one. Also normalizes
language selector values to 'ar' or 'en'.
"""
import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.streamlit_keys import generate_key


# Streamlit widgets that need key= arguments
STREAMLIT_WIDGETS = {
    'selectbox', 'multiselect', 'radio', 'text_input', 'checkbox',
    'text_area', 'number_input', 'date_input', 'slider', 'button',
    'file_uploader', 'color_picker', 'time_input', 'download_button'
}

# Directories to skip when scanning
SKIP_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'node_modules'}

# Language selector patterns
LANG_PATTERNS = ['Language', 'اللغة', '🌐', 'language']


def extract_label_from_call(call_str: str) -> str:
    """
    Extract the first string argument (label) from a widget call.
    
    Args:
        call_str: The widget call string
        
    Returns:
        The first string label or empty string if not found
    """
    # Match string literals (single, double, or triple-quoted)
    # Also handle _() translation wrapper and f-strings
    patterns = [
        r'st\.\w+\(\s*_?\(?f?["\']([^"\']*)["\']',  # Simple strings with optional _() wrapper
        r'st\.\w+\(\s*_?\(?f?"""([^"]*)"""',  # Triple double-quoted
        r"st\.\w+\(\s*_?\(?f?'''([^']*)'''",  # Triple single-quoted
    ]
    for pattern in patterns:
        match = re.search(pattern, call_str)
        if match:
            return match.group(1)
    return ""


def derive_component_name(label: str, widget_type: str) -> str:
    """
    Derive a short uppercase component token from label or widget type.
    
    Args:
        label: The widget's label string
        widget_type: The widget type (e.g., 'selectbox', 'text_input')
        
    Returns:
        Short uppercase component name
    """
    if label:
        # Use the label: replace non-alphanumeric with underscore, uppercase
        component = re.sub(r'[^a-zA-Z0-9]+', '_', label)
        component = component.strip('_').upper()
        # Truncate if too long
        if len(component) > 20:
            component = component[:20]
        if component:
            return component
    # Fallback to widget type
    return widget_type.upper()


def is_language_selector(call_str: str, label: str) -> bool:
    """
    Check if a widget call is a language selector.
    
    Args:
        call_str: The widget call string
        label: The extracted label
        
    Returns:
        True if the widget is a language selector
    """
    text_to_check = call_str + " " + label
    for pattern in LANG_PATTERNS:
        if pattern.lower() in text_to_check.lower() or pattern in text_to_check:
            return True
    return False


def has_key_argument(call_str: str) -> bool:
    """
    Check if a widget call already has a key= argument.
    
    Args:
        call_str: The widget call string
        
    Returns:
        True if the call already has a key= argument
    """
    # Check for key= in the call
    return bool(re.search(r'\bkey\s*=', call_str))


def find_widget_calls(content: str) -> List[Tuple[int, str, str, str]]:
    """
    Find all Streamlit widget calls in file content.
    
    Args:
        content: The file content
        
    Returns:
        List of tuples: (line_number, full_call, widget_type, label)
    """
    results = []
    lines = content.split('\n')
    
    # Pattern to match st.widget_name(
    widget_pattern = re.compile(r'(st\.(' + '|'.join(STREAMLIT_WIDGETS) + r')\s*\()')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        match = widget_pattern.search(line)
        if match:
            widget_type = match.group(2)
            # Collect full call (may span multiple lines)
            full_call = line
            paren_count = full_call.count('(') - full_call.count(')')
            j = i + 1
            while paren_count > 0 and j < len(lines):
                full_call += '\n' + lines[j]
                paren_count += lines[j].count('(') - lines[j].count(')')
                j += 1
            
            label = extract_label_from_call(full_call)
            results.append((i + 1, full_call, widget_type, label))  # 1-indexed line number
            i = j
        else:
            i += 1
    
    return results


def inject_key_into_call(call_str: str, key: str) -> str:
    """
    Inject a key= argument into a widget call.
    
    Args:
        call_str: The original widget call string
        key: The key to inject
        
    Returns:
        Modified call string with key argument
    """
    # Find the last closing parenthesis
    # Insert key= before it
    
    # Handle trailing comma or whitespace before closing paren
    pattern = r'(\s*\)\s*)$'
    match = re.search(pattern, call_str)
    if match:
        # Check if there are other arguments (look for comma or content after opening paren)
        content_before_close = call_str[:match.start()]
        if content_before_close.rstrip().endswith(','):
            # Already has trailing comma
            replacement = f' key="{key}"{match.group(1)}'
        else:
            # Add comma before key
            replacement = f', key="{key}"{match.group(1)}'
        return call_str[:match.start()] + replacement
    
    return call_str


def get_assignment_variable(line: str) -> Optional[str]:
    """
    Get the variable name if the widget is assigned to a variable.
    
    Args:
        line: The line containing the widget call
        
    Returns:
        Variable name or None
    """
    match = re.match(r'^\s*(\w+)\s*=\s*st\.', line)
    if match:
        return match.group(1)
    return None


def process_file(file_path: Path, dry_run: bool = False) -> List[str]:
    """
    Process a single Python file to inject keys and normalize language selectors.
    
    Args:
        file_path: Path to the Python file
        dry_run: If True, don't modify the file
        
    Returns:
        List of changelog entries
    """
    changelog = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"{file_path}: ERROR reading file - {e}"]
    
    original_content = content
    lines = content.split('\n')
    modifications = []  # List of (line_idx, original_line, new_line, changelog_entry)
    
    widget_calls = find_widget_calls(content)
    
    for line_num, full_call, widget_type, label in widget_calls:
        if has_key_argument(full_call):
            continue
        
        # Generate component name and key
        component = derive_component_name(label, widget_type)
        key = generate_key(file_path, component, label)
        
        # Find the line in content and inject key
        line_idx = line_num - 1  # Convert to 0-indexed
        original_line = lines[line_idx]
        
        # Handle multi-line calls
        if '\n' in full_call:
            # Find where the closing paren is
            call_lines = full_call.split('\n')
            end_line_idx = line_idx + len(call_lines) - 1
            last_line = lines[end_line_idx]
            
            # Inject key before the closing paren
            if ')' in last_line:
                # Find the position of the last ) in the last line
                paren_idx = last_line.rfind(')')
                indent = len(last_line) - len(last_line.lstrip())
                
                # Check if we need a comma
                content_before = last_line[:paren_idx].rstrip()
                if content_before and not content_before.endswith(','):
                    new_last_line = content_before + f', key="{key}"' + last_line[paren_idx:]
                else:
                    new_last_line = content_before + f' key="{key}"' + last_line[paren_idx:]
                
                modifications.append((end_line_idx, last_line, new_last_line,
                    f"{file_path}:{end_line_idx + 1}: widget={widget_type} key={key}"))
        else:
            # Single line call
            new_line = inject_key_into_call(original_line, key)
            if new_line != original_line:
                modifications.append((line_idx, original_line, new_line,
                    f"{file_path}:{line_num}: widget={widget_type} key={key}"))
        
        # Check if this is a language selector that needs normalization
        if is_language_selector(full_call, label):
            var_name = get_assignment_variable(lines[line_idx])
            if var_name:
                # Check if normalization already exists on the next line
                next_line_idx = line_idx + (len(full_call.split('\n')))
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx]
                    if "st.session_state['lang']" not in next_line and 'st.session_state["lang"]' not in next_line:
                        # Need to add normalization
                        indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
                        norm_line = ' ' * indent + f"st.session_state['lang'] = 'ar' if {var_name} in ('العربية', 'ar') else 'en'"
                        # We'll insert this after the widget call
                        modifications.append((-1, 'INSERT_AFTER', 
                            (next_line_idx, norm_line),
                            f"{file_path}:{next_line_idx + 1}: lang_normalization for {var_name}"))
    
    if not modifications:
        return []
    
    # Apply modifications (in reverse order to preserve line numbers)
    for mod in sorted(modifications, key=lambda x: x[0] if x[0] >= 0 else 999999, reverse=True):
        if mod[0] == -1:  # Insert operation
            insert_idx, insert_line = mod[2]
            lines.insert(insert_idx, insert_line)
        else:  # Replace operation
            line_idx, old_line, new_line = mod[0], mod[1], mod[2]
            lines[line_idx] = new_line
        changelog.append(mod[3])
    
    new_content = '\n'.join(lines)
    
    if not dry_run and new_content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return changelog


def scan_repository(repo_path: Path, dry_run: bool = False) -> List[str]:
    """
    Scan repository for Python files and process them.
    
    Args:
        repo_path: Path to the repository root
        dry_run: If True, don't modify files
        
    Returns:
        Complete changelog
    """
    changelog = []
    
    for root, dirs, files in os.walk(repo_path):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                entries = process_file(file_path, dry_run)
                changelog.extend(entries)
    
    return changelog


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Normalize Streamlit widget keys')
    parser.add_argument('--repo', type=str, default='.', 
                        help='Repository path to scan')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be changed without modifying files')
    parser.add_argument('--output', type=str, default='normalize_keys_changelog.txt',
                        help='Output changelog file path')
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo).resolve()
    print(f"Scanning repository: {repo_path}")
    
    changelog = scan_repository(repo_path, args.dry_run)
    
    if changelog:
        print(f"\n{len(changelog)} modifications {'would be made' if args.dry_run else 'made'}:")
        for entry in changelog:
            print(f"  {entry}")
        
        if not args.dry_run:
            output_path = repo_path / args.output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(changelog))
            print(f"\nChangelog written to: {output_path}")
    else:
        print("\nNo modifications needed.")


if __name__ == '__main__':
    main()
