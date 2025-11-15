"""
Session management utilities for xespresso GUI.

Provides functionality to:
- Save current session state to a file
- Load session state from a file
- Reset session state
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Default directory for session files
DEFAULT_SESSION_DIR = os.path.expanduser("~/.xespresso/sessions")


def get_serializable_state(exclude_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Extract serializable items from session state.
    
    Excludes machine and code configurations as these are persistent
    and stored separately in ~/.xespresso/
    
    Args:
        exclude_keys: List of keys to exclude from serialization
        
    Returns:
        Dictionary of serializable session state items
    """
    if exclude_keys is None:
        # Default keys to exclude (non-serializable or internal Streamlit keys)
        exclude_keys = [
            # Streamlit internal keys
            'FormSubmitter',
            'FileUploader',
            # Widget keys that will be recreated
            '_widget_state',
            # Machine and code configurations (persistent, not session-specific)
            'current_machine',  # Machine object - config stored in ~/.xespresso/machines/
            'current_codes',    # Codes config - stored in ~/.xespresso/codes/
        ]
    
    serializable_state = {}
    
    for key, value in st.session_state.items():
        # Skip excluded keys
        if key in exclude_keys:
            continue
            
        # Skip keys starting with underscore (usually internal)
        if key.startswith('_'):
            continue
        
        # Try to serialize the value
        try:
            # Test if value is JSON serializable
            json.dumps(value)
            serializable_state[key] = value
        except (TypeError, ValueError):
            # Skip non-serializable values
            # Try to convert common types
            if hasattr(value, '__dict__'):
                try:
                    serializable_state[key] = str(value)
                except:
                    pass
    
    return serializable_state


def save_session(filename: Optional[str] = None, session_dir: Optional[str] = None) -> str:
    """
    Save current session state to a JSON file.
    
    Args:
        filename: Name of the session file. If None, generates timestamp-based name
        session_dir: Directory to save session files. If None, uses default
        
    Returns:
        Path to saved session file
        
    Raises:
        IOError: If unable to save session
    """
    if session_dir is None:
        session_dir = DEFAULT_SESSION_DIR
    
    # Create session directory if it doesn't exist
    os.makedirs(session_dir, exist_ok=True)
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.json"
    
    # Ensure .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = os.path.join(session_dir, filename)
    
    # Get serializable state
    state = get_serializable_state()
    
    # Add metadata
    session_data = {
        "metadata": {
            "saved_at": datetime.now().isoformat(),
            "version": "1.0",
        },
        "state": state
    }
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    return filepath


def load_session(filepath: str) -> Dict[str, Any]:
    """
    Load session state from a JSON file.
    
    Args:
        filepath: Path to session file
        
    Returns:
        Dictionary of session state
        
    Raises:
        IOError: If unable to read file
        ValueError: If file format is invalid
    """
    if not os.path.exists(filepath):
        raise IOError(f"Session file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        session_data = json.load(f)
    
    # Validate format
    if "state" not in session_data:
        raise ValueError("Invalid session file format: missing 'state' key")
    
    return session_data["state"]


def restore_session(state: Dict[str, Any], clear_first: bool = True):
    """
    Restore session state from a dictionary.
    
    Args:
        state: Dictionary of session state to restore
        clear_first: Whether to clear current session state first
    """
    if clear_first:
        # Clear current session state but keep some internal keys
        keys_to_keep = [k for k in st.session_state.keys() if k.startswith('_')]
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
    
    # Restore state
    for key, value in state.items():
        st.session_state[key] = value


def reset_session(keep_keys: Optional[List[str]] = None):
    """
    Reset session state, optionally keeping specified keys.
    
    Args:
        keep_keys: List of keys to keep. If None, clears everything
    """
    if keep_keys is None:
        keep_keys = []
    
    # Store values to keep
    kept_values = {key: st.session_state[key] for key in keep_keys if key in st.session_state}
    
    # Clear all session state
    for key in list(st.session_state.keys()):
        if not key.startswith('_'):  # Keep internal Streamlit keys
            del st.session_state[key]
    
    # Restore kept values
    for key, value in kept_values.items():
        st.session_state[key] = value


def list_sessions(session_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List available session files.
    
    Args:
        session_dir: Directory containing session files. If None, uses default
        
    Returns:
        List of dictionaries with session info (filename, path, saved_at)
    """
    if session_dir is None:
        session_dir = DEFAULT_SESSION_DIR
    
    if not os.path.exists(session_dir):
        return []
    
    sessions = []
    for filename in os.listdir(session_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(session_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    saved_at = data.get('metadata', {}).get('saved_at', 'Unknown')
                    sessions.append({
                        'filename': filename,
                        'path': filepath,
                        'saved_at': saved_at
                    })
            except:
                # Skip invalid files
                pass
    
    # Sort by saved_at (most recent first)
    sessions.sort(key=lambda x: x['saved_at'], reverse=True)
    
    return sessions


def render_session_manager(key: str = "session_manager"):
    """
    Render session management UI component.
    
    Args:
        key: Unique key for the component
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Session Management")
    
    st.sidebar.caption("""
    **What gets saved:**
    - Structure and calculation parameters
    - Workflow configuration
    - Working directory selection
    - Selected machine/code names
    
    **Not saved (persistent configs):**
    - Machine configurations
    - Code configurations
    """)
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("💾 Save", key=f"{key}_save", use_container_width=True, help="Save current session state"):
            try:
                filepath = save_session()
                st.sidebar.success(f"✅ Session saved!")
                st.sidebar.caption(f"📁 {os.path.basename(filepath)}")
            except Exception as e:
                st.sidebar.error(f"❌ Error saving: {e}")
    
    with col2:
        if st.button("🔄 Reset", key=f"{key}_reset", use_container_width=True, help="Clear all session data"):
            reset_session()
            st.sidebar.success("✅ Session reset!")
            st.rerun()
    
    # Load session section
    with st.sidebar.expander("📂 Load Session", expanded=False):
        sessions = list_sessions()
        
        if sessions:
            st.markdown("**Available sessions:**")
            
            for session in sessions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"📄 {session['filename']}")
                    st.caption(f"🕐 {session['saved_at'][:19]}")
                with col2:
                    if st.button("Load", key=f"{key}_load_{session['filename']}", use_container_width=True):
                        try:
                            state = load_session(session['path'])
                            restore_session(state)
                            st.success("✅ Session loaded!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error loading: {e}")
                st.markdown("---")
        else:
            st.info("No saved sessions found")
