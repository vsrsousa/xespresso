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


def get_active_sessions() -> Dict[str, Dict[str, Any]]:
    """
    Get all active sessions from session state.
    
    Returns:
        Dictionary mapping session IDs to session data
    """
    if '_active_sessions' not in st.session_state:
        st.session_state._active_sessions = {}
    return st.session_state._active_sessions


def get_current_session_id() -> str:
    """
    Get the current active session ID.
    
    Returns:
        Current session ID
    """
    if '_current_session_id' not in st.session_state:
        # Create first session automatically
        st.session_state._current_session_id = 'session_1'
        st.session_state._session_counter = 1
        
        # Initialize active sessions and add the first session
        if '_active_sessions' not in st.session_state:
            st.session_state._active_sessions = {}
        
        st.session_state._active_sessions['session_1'] = {
            'name': 'Session 1',
            'created_at': datetime.now().isoformat(),
            'state': {}
        }
    
    return st.session_state._current_session_id


def create_new_session() -> str:
    """
    Create a new calculation session.
    
    Returns:
        New session ID
    """
    # Increment session counter
    if '_session_counter' not in st.session_state:
        st.session_state._session_counter = 1
    else:
        st.session_state._session_counter += 1
    
    # Create new session ID
    new_session_id = f"session_{st.session_state._session_counter}"
    
    # Initialize sessions dict if needed
    if '_active_sessions' not in st.session_state:
        st.session_state._active_sessions = {}
    
    # Create new session with empty state
    st.session_state._active_sessions[new_session_id] = {
        'name': f"Session {st.session_state._session_counter}",
        'created_at': datetime.now().isoformat(),
        'state': {}
    }
    
    # Switch to new session
    st.session_state._current_session_id = new_session_id
    
    # Clear current calculation state (but keep machine/code configs)
    # Reset to defaults for session-specific values
    keys_to_clear = [
        'current_structure', 'workflow_config',
        'selected_code_version', 'current_machine_name',
        'espresso_calculator', 'prepared_atoms'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Initialize working_directory for the new session to default
    import os
    st.session_state.working_directory = os.path.expanduser("~")
    
    return new_session_id


def switch_session(session_id: str):
    """
    Switch to a different active session.
    
    Args:
        session_id: ID of session to switch to
    """
    if '_active_sessions' not in st.session_state:
        st.session_state._active_sessions = {}
    
    if session_id not in st.session_state._active_sessions:
        return
    
    # Save current session state before switching
    current_id = get_current_session_id()
    if current_id in st.session_state._active_sessions:
        st.session_state._active_sessions[current_id]['state'] = get_serializable_state()
    
    # Switch to new session
    st.session_state._current_session_id = session_id
    
    # Restore new session state
    session_data = st.session_state._active_sessions[session_id]
    if session_data.get('state'):
        restore_session(session_data['state'], clear_first=True)
    else:
        # If no saved state yet, initialize with defaults
        import os
        if 'working_directory' not in st.session_state:
            st.session_state.working_directory = os.path.expanduser("~")


def close_session(session_id: str):
    """
    Close an active session.
    
    Args:
        session_id: ID of session to close
    """
    if '_active_sessions' not in st.session_state:
        return
    
    if session_id in st.session_state._active_sessions:
        del st.session_state._active_sessions[session_id]
    
    # If closing current session, switch to another or create new
    if st.session_state._current_session_id == session_id:
        remaining = list(st.session_state._active_sessions.keys())
        if remaining:
            switch_session(remaining[0])
        else:
            create_new_session()


def rename_session(session_id: str, new_name: str):
    """
    Rename an active session.
    
    Args:
        session_id: ID of session to rename
        new_name: New name for the session
    """
    if '_active_sessions' not in st.session_state:
        return
    
    if session_id in st.session_state._active_sessions:
        st.session_state._active_sessions[session_id]['name'] = new_name


def render_session_manager(key: str = "session_manager"):
    """
    Render multi-session management UI component.
    
    Similar to Jupyter notebooks - users can create, switch, and manage multiple independent sessions.
    
    Args:
        key: Unique key for the component
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("📑 Sessions")
    
    # Get active sessions
    active_sessions = get_active_sessions()
    current_session_id = get_current_session_id()
    
    # Create new session button
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        if st.button("➕ New Session", key=f"{key}_new", use_container_width=True, 
                    help="Start a new calculation session"):
            new_id = create_new_session()
            st.sidebar.success(f"✅ Created new session!")
            st.rerun()
    
    with col2:
        if st.button("💾 Save", key=f"{key}_save", use_container_width=True, 
                    help="Save current session"):
            try:
                # Save current session state first
                if current_session_id in active_sessions:
                    active_sessions[current_session_id]['state'] = get_serializable_state()
                
                # Generate filename with session name
                session_name = active_sessions[current_session_id].get('name', 'Session')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{session_name.replace(' ', '_')}_{timestamp}.json"
                
                filepath = save_session(filename=filename)
                st.sidebar.success(f"✅ Saved!")
                st.sidebar.caption(f"📁 {os.path.basename(filepath)}")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {e}")
    
    # Active sessions list
    if active_sessions:
        st.sidebar.markdown("**Active Sessions:**")
        
        for sess_id, sess_data in active_sessions.items():
            is_current = (sess_id == current_session_id)
            
            col1, col2, col3 = st.sidebar.columns([4, 1, 1])
            with col1:
                # Session name - all sessions are buttons with visual indicator for current
                name = sess_data.get('name', sess_id)
                button_label = f"{'→ ' if is_current else ''}{name}{' ✓' if is_current else ''}"
                button_type = "primary" if is_current else "secondary"
                
                if st.button(button_label, key=f"{key}_switch_{sess_id}", 
                           use_container_width=True, type=button_type,
                           help="Switch to this session" if not is_current else "Current session"):
                    if not is_current:
                        switch_session(sess_id)
                        st.rerun()
            
            with col2:
                # Rename button
                if st.button("✏️", key=f"{key}_rename_{sess_id}", 
                           help="Rename this session"):
                    st.session_state[f'{key}_renaming_{sess_id}'] = True
                    st.rerun()
            
            with col3:
                # Close button (only if more than 1 session)
                if len(active_sessions) > 1:
                    if st.button("✖", key=f"{key}_close_{sess_id}", 
                               help="Close this session"):
                        close_session(sess_id)
                        st.rerun()
            
            # Rename input (if renaming this session)
            if st.session_state.get(f'{key}_renaming_{sess_id}', False):
                new_name = st.sidebar.text_input(
                    "New name:",
                    value=name,
                    key=f"{key}_new_name_{sess_id}"
                )
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    if st.button("✓ OK", key=f"{key}_rename_ok_{sess_id}", use_container_width=True):
                        rename_session(sess_id, new_name)
                        st.session_state[f'{key}_renaming_{sess_id}'] = False
                        st.rerun()
                with col2:
                    if st.button("✗ Cancel", key=f"{key}_rename_cancel_{sess_id}", use_container_width=True):
                        st.session_state[f'{key}_renaming_{sess_id}'] = False
                        st.rerun()
    
    # Load saved sessions
    with st.sidebar.expander("📂 Load Saved Session", expanded=False):
        sessions = list_sessions()
        
        if sessions:
            st.markdown("**Saved sessions:**")
            
            for session in sessions[:5]:  # Show last 5
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"📄 {session['filename']}")
                    st.caption(f"🕐 {session['saved_at'][:19]}")
                with col2:
                    if st.button("Load", key=f"{key}_load_{session['filename']}", 
                               use_container_width=True):
                        try:
                            state = load_session(session['path'])
                            
                            # Create new session for loaded state
                            new_id = create_new_session()
                            
                            # Set session name from filename
                            name = session['filename'].replace('.json', '').replace('_', ' ')
                            active_sessions[new_id]['name'] = name
                            
                            # Restore state
                            restore_session(state, clear_first=True)
                            active_sessions[new_id]['state'] = state
                            
                            st.success("✅ Session loaded!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                st.markdown("---")
        else:
            st.info("No saved sessions found")
