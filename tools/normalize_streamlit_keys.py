#!/usr/bin/env python3
"""Normalize Streamlit widget keys across the repository.

Scans repository for Streamlit widget calls and injects deterministic keys
to avoid StreamlitDuplicateElementId errors.
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.streamlit_keys import generate_key

# Widget types to scan for
WIDGET_TYPES = [
    'selectbox', 'multiselect', 'radio', 'text_input', 'checkbox',
    'text_area', 'number_input', 'date_input', 'time_input', 'slider',
    'file_uploader', 'color_picker', 'button', 'download_button'
]

# Directories to skip
SKIP_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'env', '.env'}

# Language-related patterns
LANGUAGE_PATTERNS = ['Language', 'اللغة', '🌐']


def find_python_files(root: Path) -> List[Path]:
    """Find all Python files in the repository, skipping excluded directories."""
    python_files = []
    for path in root.rglob('*.py'):
        if not any(skip in path.parts for skip in SKIP_DIRS):
            python_files.append(path)
    return python_files


def is_escaped(text: str, pos: int) -> bool:
    """Check if a character at position is escaped by counting preceding backslashes.
    
    A character is escaped if preceded by an odd number of backslashes.
    """
    if pos == 0:
        return False
    backslash_count = 0
    i = pos - 1
    while i >= 0 and text[i] == '\\':
        backslash_count += 1
        i -= 1
    return backslash_count % 2 == 1


def find_matching_paren(text: str, start: int) -> int:
    """Find the index of the closing parenthesis matching the opening one at start.
    
    Returns -1 if not found.
    """
    if start >= len(text) or text[start] != '(':
        return -1
    
    depth = 1
    i = start + 1
    in_string = False
    string_char = None
    
    while i < len(text) and depth > 0:
        char = text[i]
        
        # Handle string boundaries (properly handle escaped quotes)
        if char in ('"', "'") and not is_escaped(text, i):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
        elif not in_string:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
        
        i += 1
    
    return i - 1 if depth == 0 else -1


def extract_label(call_content: str) -> str:
    """Extract the first positional argument (label) from widget call content.
    
    Args:
        call_content: Content between opening and closing parentheses.
    """
    content = call_content.strip()
    if not content:
        return ""
    
    # Try direct string match
    match = re.match(r'^(["\'])(.*?)\1', content)
    if match:
        return match.group(2)
    
    # Try f-string match
    match = re.match(r'^f(["\'])(.*?)\1', content)
    if match:
        return match.group(2)
    
    # Try _("text") pattern (translation function)
    match = re.match(r'^_\(\s*f?(["\'])([^"\']*)\1\s*\)', content)
    if match:
        return match.group(2)
    
    # Try t(lang, "key") pattern
    match = re.match(r'^t\([^,]+,\s*(["\'])([^"\']*)\1', content)
    if match:
        return match.group(2)
    
    return ""


def has_key_argument(call_content: str) -> bool:
    """Check if widget call content already has a key= argument."""
    # More robust check: look for key= not inside a string
    # Simple heuristic: check if 'key=' appears outside of quotes
    in_string = False
    string_char = None
    i = 0
    while i < len(call_content) - 3:
        char = call_content[i]
        if char in ('"', "'") and not is_escaped(call_content, i):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
        elif not in_string and call_content[i:i+4] == 'key=':
            return True
        i += 1
    return False


def is_language_widget(label: str) -> bool:
    """Check if a widget label indicates it's a language selector.
    
    Used to identify widgets that may need additional normalization
    to update st.session_state['lang'] with canonical values ('ar' or 'en').
    
    This function is exported for use by external scripts or future extensions
    that need to identify and handle language selector widgets specially.
    """
    return any(pattern in label for pattern in LANGUAGE_PATTERNS)


class WidgetCall:
    """Represents a Streamlit widget call in source code."""
    def __init__(self, widget_type: str, start: int, end: int, 
                 paren_start: int, paren_end: int, label: str, has_key: bool):
        self.widget_type = widget_type
        self.start = start  # Start of st.widget
        self.end = end  # End of closing paren
        self.paren_start = paren_start  # Position of opening paren
        self.paren_end = paren_end  # Position of closing paren
        self.label = label
        self.has_key = has_key


def find_widget_calls_in_content(content: str) -> List[WidgetCall]:
    """Find all Streamlit widget calls in content."""
    widgets = []
    
    for widget_type in WIDGET_TYPES:
        # Pattern to find st.widget( or st.sidebar.widget(
        pattern = rf'st\.(?:sidebar\.)?{widget_type}\s*\('
        
        for match in re.finditer(pattern, content):
            start = match.start()
            paren_start = match.end() - 1  # Position of opening paren
            
            # Find matching closing paren
            paren_end = find_matching_paren(content, paren_start)
            if paren_end == -1:
                continue  # Can't find closing paren, skip
            
            end = paren_end + 1
            call_content = content[paren_start + 1:paren_end]
            
            label = extract_label(call_content)
            has_key = has_key_argument(call_content)
            
            widgets.append(WidgetCall(
                widget_type=widget_type,
                start=start,
                end=end,
                paren_start=paren_start,
                paren_end=paren_end,
                label=label,
                has_key=has_key
            ))
    
    # Sort by position (reverse order for safe replacement)
    widgets.sort(key=lambda w: w.start, reverse=True)
    return widgets


def get_line_number(content: str, pos: int) -> int:
    """Get the 1-based line number for a position in content."""
    return content[:pos].count('\n') + 1


def process_file(file_path: Path, changelog: List[str]) -> bool:
    """Process a single Python file and inject keys where needed.
    
    Returns True if the file was modified.
    """
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    widgets = find_widget_calls_in_content(content)
    
    for widget in widgets:
        if widget.has_key:
            continue
        
        key = generate_key(file_path, widget.widget_type, widget.label)
        
        # Build the new call content
        call_content = content[widget.paren_start + 1:widget.paren_end]
        
        # Add key argument
        if call_content.strip():
            new_call_content = f'{call_content}, key="{key}"'
        else:
            new_call_content = f'key="{key}"'
        
        # Replace in content
        new_content = (
            content[:widget.paren_start + 1] +
            new_call_content +
            content[widget.paren_end:]
        )
        content = new_content
        
        # Log the change (note language widgets for manual review)
        line_num = get_line_number(original_content, widget.start)
        is_lang = is_language_widget(widget.label)
        lang_note = " [LANGUAGE_WIDGET]" if is_lang else ""
        changelog.append(f"{file_path}:{line_num}: widget={widget.widget_type}{lang_note}")
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return True
    
    return False


def main():
    """Main entry point."""
    # Get repository root (parent of tools directory)
    repo_root = Path(__file__).parent.parent
    
    print(f"Scanning repository: {repo_root}")
    
    # Find all Python files
    python_files = find_python_files(repo_root)
    print(f"Found {len(python_files)} Python files to scan")
    
    # Track changes
    changelog: List[str] = []
    modified_files = 0
    
    for file_path in python_files:
        try:
            if process_file(file_path, changelog):
                modified_files += 1
                print(f"Modified: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Write changelog
    changelog_path = repo_root / 'normalize_keys_changelog.txt'
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(changelog))
    
    print(f"\nSummary:")
    print(f"  Modified files: {modified_files}")
    print(f"  Total key injections: {len(changelog)}")
    print(f"  Changelog written to: {changelog_path}")


if __name__ == '__main__':
    main()
