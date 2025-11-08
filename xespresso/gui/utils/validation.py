"""
Path validation utilities for the xespresso GUI.
"""

import os


def validate_path(path, allow_creation=False):
    """
    Validate and sanitize file paths to prevent path injection.
    
    Args:
        path: Path to validate
        allow_creation: If True, allow non-existent paths (for file creation)
    
    Returns:
        Tuple of (is_valid, normalized_path, error_message)
    """
    if not path:
        return False, None, "Path cannot be empty"
    
    try:
        # Normalize and resolve the path
        normalized = os.path.abspath(os.path.expanduser(path))
        
        # Check for path traversal attempts
        if '..' in os.path.relpath(normalized, os.path.expanduser('~')):
            # Allow if it's an absolute path or in allowed directories
            allowed_dirs = ['/tmp', '/home', '/Users', os.path.expanduser('~')]
            if not any(normalized.startswith(d) for d in allowed_dirs):
                return False, None, "Path traversal not allowed"
        
        # Check if path exists (if required)
        if not allow_creation and not os.path.exists(normalized):
            return False, normalized, f"Path does not exist: {normalized}"
        
        return True, normalized, None
        
    except Exception as e:
        return False, None, f"Invalid path: {str(e)}"
