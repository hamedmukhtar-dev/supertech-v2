#!/usr/bin/env python3
"""
Normalization tool to scan and inject deterministic keys into Streamlit widget calls.

This tool scans the repository for Streamlit widget calls (st.selectbox, st.multiselect, 
st.radio, st.text_input, st.checkbox, st.text_area, st.number_input, st.date_input) and 
injects explicit key= arguments where missing.
"""
import os
import re
import sys
from pathlib import Path

# Add the repo root to sys.path for imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.streamlit_keys import generate_key


# Streamlit widget patterns to match
WIDGET_TYPES = [
    'selectbox',
    'multiselect',
    'radio',
    'text_input',
    'checkbox',
    'text_area',
    'number_input',
    'date_input',
]

# Language indicator labels
LANGUAGE_LABELS = ['Language', 'اللغة', '🌐']


def find_python_files(root: Path) -> list:
    """Find all Python files in the repository, excluding tools directory."""
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden directories and tools
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != 'tools']
        for filename in filenames:
            if filename.endswith('.py'):
                py_files.append(Path(dirpath) / filename)
    return py_files


def extract_label_from_call(call_str: str) -> str:
    """
    Extract the first string argument (label) from a widget call.
    Handles both single and double quoted strings.
    """
    # Match first string argument (could be in parentheses)
    # Look for patterns like: st.widget("label" or st.widget('label'
    patterns = [
        r'\(\s*"([^"]*)"',  # Double quoted
        r"\(\s*'([^']*)'",  # Single quoted
        r'\(\s*_\(\s*f?"([^"]*)"\s*\)',  # Translation wrapper with double quotes
        r"\(\s*_\(\s*f?'([^']*)'\s*\)",  # Translation wrapper with single quotes
        r'\(\s*t\([^,]+,\s*"([^"]*)"\s*\)',  # t(lang, "key") pattern
        r"\(\s*t\([^,]+,\s*'([^']*)'\s*\)",  # t(lang, 'key') pattern
    ]
    
    for pattern in patterns:
        match = re.search(pattern, call_str)
        if match:
            return match.group(1)
    return ""


def has_key_argument(call_str: str) -> bool:
    """Check if the widget call already has a key= argument."""
    # Match key= followed by string or variable
    return bool(re.search(r'\bkey\s*=', call_str))


def is_language_selector(label: str, call_str: str) -> bool:
    """Check if this is a language selector widget."""
    for lang_indicator in LANGUAGE_LABELS:
        if lang_indicator in label or lang_indicator in call_str:
            return True
    return False


def find_closing_paren(content: str, start: int) -> int:
    """
    Find the matching closing parenthesis for the opening paren at start.
    """
    depth = 0
    in_string = None
    escape_next = False
    
    for i in range(start, len(content)):
        char = content[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if in_string:
            if char == in_string:
                in_string = None
            continue
            
        if char in '"\'':
            in_string = char
            continue
            
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                return i
                
    return -1


def process_file(filepath: Path, changelog: list) -> str:
    """
    Process a single file and inject keys where needed.
    Returns the modified content.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    modified = False
    
    # Build pattern for all widget types
    widget_pattern = r'st\.(' + '|'.join(WIDGET_TYPES) + r')\s*\('
    
    # Find all widget calls
    matches = list(re.finditer(widget_pattern, content))
    
    # Process in reverse order to maintain position accuracy
    for match in reversed(matches):
        widget_type = match.group(1)
        start_pos = match.start()
        paren_start = match.end() - 1  # Position of opening paren
        
        # Find the closing parenthesis
        close_paren = find_closing_paren(content, paren_start)
        if close_paren == -1:
            continue
            
        # Extract the full call
        full_call = content[start_pos:close_paren + 1]
        
        # Skip if already has a key argument
        if has_key_argument(full_call):
            continue
        
        # Extract label
        label = extract_label_from_call(full_call)
        
        # Generate key
        key = generate_key(filepath, widget_type, label)
        
        # Find position to insert key (just before closing paren)
        # Check if there's already trailing content (like other kwargs)
        call_interior = content[paren_start + 1:close_paren].rstrip()
        
        if call_interior.endswith(','):
            # Already has trailing comma
            insert_text = f' key="{key}"'
        elif call_interior:
            # Has content but no trailing comma
            insert_text = f', key="{key}"'
        else:
            # Empty call (unlikely for these widgets)
            insert_text = f'key="{key}"'
        
        # Insert the key
        new_content = content[:close_paren] + insert_text + content[close_paren:]
        content = new_content
        modified = True
        
        # Add to changelog
        changelog.append(f"{filepath}: widget={widget_type} key={key}")
        
        # Handle language selector normalization
        if is_language_selector(label, full_call):
            # Find the line after the widget call
            line_end = content.find('\n', close_paren + len(insert_text))
            if line_end == -1:
                line_end = len(content)
            
            # Check if normalization already exists nearby
            next_lines = content[close_paren:close_paren + 500]
            if "st.session_state['lang']" not in next_lines and 'st.session_state["lang"]' not in next_lines:
                # Find if this is an assignment (variable = st.selectbox...)
                line_start = content.rfind('\n', 0, start_pos) + 1
                line_content = content[line_start:close_paren + len(insert_text) + 1]
                
                # Check for variable assignment
                assign_match = re.match(r'\s*(\w+)\s*=\s*st\.', line_content)
                if assign_match:
                    var_name = assign_match.group(1)
                    # Insert normalization after the line
                    norm_line = f"\n    st.session_state['lang'] = 'ar' if {var_name} in ('العربية', 'ar') else 'en'"
                    # Find end of statement line
                    stmt_end = content.find('\n', close_paren + len(insert_text))
                    if stmt_end != -1:
                        content = content[:stmt_end] + norm_line + content[stmt_end:]
    
    return content if modified else original_content


def normalize_all_files(repo_root: Path) -> list:
    """
    Normalize all Python files in the repository.
    Returns a list of changelog entries.
    """
    changelog = []
    py_files = find_python_files(repo_root)
    
    for filepath in py_files:
        try:
            new_content = process_file(filepath, changelog)
            
            # Read original to compare
            with open(filepath, 'r', encoding='utf-8') as f:
                original = f.read()
            
            if new_content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Modified: {filepath}")
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    return changelog


def main():
    """Main entry point."""
    repo_root = REPO_ROOT
    
    print(f"Scanning repository: {repo_root}")
    print("=" * 60)
    
    changelog = normalize_all_files(repo_root)
    
    # Write changelog
    changelog_path = repo_root / "normalize_keys_changelog.txt"
    with open(changelog_path, 'w', encoding='utf-8') as f:
        for entry in changelog:
            f.write(entry + '\n')
    
    print("=" * 60)
    print(f"Changelog written to: {changelog_path}")
    print(f"Total changes: {len(changelog)}")


if __name__ == "__main__":
    main()
