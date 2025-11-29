#!/usr/bin/env python3
"""
Normalize Streamlit Keys Tool

Scans repository for Streamlit widget calls and injects deterministic keys
to eliminate StreamlitDuplicateElementId / StreamlitDuplicateElementKey errors.
"""
import os
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.streamlit_keys import generate_key

# Directories to skip
SKIP_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'node_modules'}

# Streamlit widgets to process
WIDGET_TYPES = [
    'selectbox', 'multiselect', 'radio', 'text_input', 
    'checkbox', 'text_area', 'number_input', 'date_input'
]

# Language selector indicators
LANG_INDICATORS = ['Language', 'اللغة', '🌐']


def should_skip_path(path: Path) -> bool:
    """Check if path should be skipped."""
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    return False


def find_matching_paren(content: str, start_idx: int) -> int:
    """Find the matching closing parenthesis, handling nested parens and strings."""
    depth = 0
    i = start_idx
    in_string = None
    escape_next = False
    
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
        
        # Handle strings
        if in_string:
            if char == in_string:
                in_string = None
        else:
            if char in ('"', "'"):
                # Check for triple quotes
                if content[i:i+3] in ('"""', "'''"):
                    # Find end of triple quote
                    end_quote = content.find(content[i:i+3], i+3)
                    if end_quote != -1:
                        i = end_quote + 3
                        continue
                in_string = char
            elif char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    return i
        
        i += 1
    
    return -1


def extract_label_from_call(call_text: str) -> str:
    """Extract the first positional argument (label) from a widget call."""
    # Find the opening paren
    paren_idx = call_text.find('(')
    if paren_idx == -1:
        return ""
    
    inner = call_text[paren_idx + 1:-1].strip()
    if not inner:
        return ""
    
    # Extract first argument (could be string literal, f-string, or variable)
    # Try matching quoted string
    match = re.match(r'^(["\'])(.*?)\1', inner, re.DOTALL)
    if match:
        return match.group(2)
    
    # Try matching f-string
    match = re.match(r'^f(["\'])(.*?)\1', inner, re.DOTALL)
    if match:
        return match.group(2)
    
    # Try matching function call like _("text")
    match = re.match(r'^_\(f?["\']([^"\']*)["\']', inner)
    if match:
        return match.group(1)
    
    # Try matching variable or expression before comma
    match = re.match(r'^([^,]+)', inner)
    if match:
        val = match.group(1).strip()
        # If it's a simple identifier, return it
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', val):
            return val
    
    return ""


def is_language_selector(label: str) -> bool:
    """Check if a label indicates a language selector."""
    for indicator in LANG_INDICATORS:
        if indicator in label:
            return True
    return False


def has_key_argument(call_text: str) -> bool:
    """Check if the widget call already has a key= argument."""
    # Look for key= in the call (but not inside a string)
    # Simple approach: check for pattern outside of quotes
    in_string = None
    i = 0
    while i < len(call_text):
        char = call_text[i]
        if in_string:
            if char == '\\' and i + 1 < len(call_text):
                i += 2
                continue
            if char == in_string:
                in_string = None
        else:
            if char in ('"', "'"):
                in_string = char
            elif call_text[i:].startswith('key=') or call_text[i:].startswith('key ='):
                return True
        i += 1
    return False


def find_widget_calls(content: str, file_path: Path):
    """Find all Streamlit widget calls in the content."""
    widget_calls = []
    
    for widget in WIDGET_TYPES:
        # Pattern to find st.widget_name( start
        pattern = rf'st\.{widget}\s*\('
        
        for match in re.finditer(pattern, content):
            start_pos = match.start()
            paren_start = match.end() - 1  # Position of opening paren
            
            # Find matching closing paren
            end_paren = find_matching_paren(content, paren_start)
            if end_paren == -1:
                continue
            
            call_text = content[start_pos:end_paren + 1]
            
            # Calculate line number
            line_num = content[:start_pos].count('\n') + 1
            
            # Skip if already has key=
            if has_key_argument(call_text):
                continue
            
            # Extract label
            label = extract_label_from_call(call_text)
            
            widget_calls.append({
                'widget': widget,
                'call_text': call_text,
                'start': start_pos,
                'end': end_paren + 1,
                'line': line_num,
                'label': label,
                'is_lang_selector': is_language_selector(label)
            })
    
    # Sort by position in reverse order for safe replacement
    widget_calls.sort(key=lambda x: x['start'], reverse=True)
    return widget_calls


def inject_key(call_text: str, key: str) -> str:
    """Inject key= argument into a widget call."""
    # Find the last closing parenthesis
    if not call_text.rstrip().endswith(')'):
        return call_text
    
    # Find the position of opening paren
    paren_idx = call_text.find('(')
    if paren_idx == -1:
        return call_text
    
    inner = call_text[paren_idx + 1:-1]
    
    # Check if there are existing arguments
    if inner.strip():
        # Add comma and key before the closing paren
        new_call = call_text[:-1] + f', key="{key}")'
    else:
        # No existing arguments
        new_call = call_text[:-1] + f'key="{key}")'
    
    return new_call


def add_lang_normalization(content: str, line_num: int, call_text: str) -> str:
    """
    Add language normalization lines after a language selector.
    Ensures the code normalizes/writes to st.session_state['lang'] with values 'ar' or 'en'.
    
    This function is called when processing language selector widgets (those with labels
    containing 'Language', 'اللغة', or '🌐'). It adds a normalization line after the
    widget call to ensure consistent lang values in session state.
    
    Note: In the current codebase, most language selectors already have normalization
    logic nearby, so this function typically returns the content unchanged. It's kept
    for handling edge cases where language selectors lack normalization.
    """
    lines = content.split('\n')
    
    # Find the line and check if normalization already exists nearby
    search_start = max(0, line_num - 2)
    search_end = min(len(lines), line_num + 5)
    nearby_lines = '\n'.join(lines[search_start:search_end])
    
    # Check if normalization already exists
    if 'st.session_state["lang"]' in nearby_lines or "st.session_state['lang']" in nearby_lines:
        return content
    if 'st.session_state.lang' in nearby_lines:
        return content
    
    # Find variable assignment from the widget call
    widget_prefix = call_text.split('(')[0]
    line_content = lines[line_num - 1] if line_num <= len(lines) else ''
    var_match = re.search(r'(\w+)\s*=\s*' + re.escape(widget_prefix), line_content)
    
    if var_match:
        var_name = var_match.group(1)
        # Add normalization after the line
        indent = len(line_content) - len(line_content.lstrip())
        indent_str = ' ' * indent
        
        # Construct normalization line
        norm_line = f'{indent_str}st.session_state["lang"] = "ar" if {var_name} in ["العربية", "ar"] else "en"'
        
        # Insert after the current line
        lines.insert(line_num, norm_line)
        return '\n'.join(lines)
    
    return content


def process_file(file_path: Path, changelog: list) -> bool:
    """Process a single Python file and inject keys."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return False
    
    # Skip files that don't use streamlit
    if 'streamlit' not in content and 'st.' not in content:
        return False
    
    original_content = content
    widget_calls = find_widget_calls(content, file_path)
    
    if not widget_calls:
        return False
    
    modified = False
    
    for call_info in widget_calls:
        widget = call_info['widget']
        call_text = call_info['call_text']
        label = call_info['label']
        line = call_info['line']
        start = call_info['start']
        end = call_info['end']
        
        # Generate the key
        key = generate_key(file_path, widget, label)
        
        # Inject the key
        new_call = inject_key(call_text, key)
        
        if new_call != call_text:
            # Update content
            content = content[:start] + new_call + content[end:]
            modified = True
            
            # Log the change
            changelog.append(f"{file_path}: widget={widget}")
            
            # Handle language selectors
            if call_info['is_lang_selector']:
                content = add_lang_normalization(content, line, call_text)
    
    if modified and content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False


def scan_repository(repo_path: Path) -> list:
    """Scan the repository for Python files and process them."""
    changelog = []
    
    for root, dirs, files in os.walk(repo_path):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if not file.endswith('.py'):
                continue
            
            file_path = Path(root) / file
            
            if should_skip_path(file_path):
                continue
            
            # Skip this tool itself
            if 'normalize_streamlit_keys.py' in str(file_path):
                continue
            
            process_file(file_path, changelog)
    
    return changelog


def main():
    """Main entry point."""
    # Determine repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    print(f"Scanning repository: {repo_root}")
    
    changelog = scan_repository(repo_root)
    
    # Write changelog
    changelog_path = repo_root / 'normalize_keys_changelog.txt'
    with open(changelog_path, 'w', encoding='utf-8') as f:
        for entry in changelog:
            f.write(entry + '\n')
    
    print(f"Processed {len(changelog)} widget calls")
    print(f"Changelog written to: {changelog_path}")


if __name__ == '__main__':
    main()
