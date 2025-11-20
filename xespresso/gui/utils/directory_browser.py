"""
Directory browsing utilities for xespresso GUI.

Provides functionality to browse and select directories with subfolder navigation.
Includes a JupyterLab-like hierarchical tree view for better folder navigation,
especially on macOS where native dialogs may have issues.
"""

import streamlit as st
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import threading
import platform

# Try to import tkinter for native file dialog
try:
    import tkinter as tk
    from tkinter import filedialog

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


def get_subdirectories(path: str) -> List[str]:
    """
    Get list of subdirectories in the given path.

    Args:
        path: Directory path to scan

    Returns:
        List of subdirectory paths
    """
    if not os.path.exists(path) or not os.path.isdir(path):
        return []

    try:
        subdirs = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and not item.startswith("."):
                subdirs.append(item_path)
        return sorted(subdirs)
    except (PermissionError, OSError):
        return []


def get_folder_tree(path: str, max_depth: int = 2, current_depth: int = 0) -> Dict[str, Dict]:
    """
    Get folder structure as a hierarchical tree.
    
    Args:
        path: Root directory path to scan
        max_depth: Maximum depth to scan (default 2 levels)
        current_depth: Current recursion depth (internal use)
    
    Returns:
        Dictionary representing the folder tree structure
    """
    if current_depth >= max_depth:
        return {}
    
    tree = {}
    try:
        items = sorted(os.listdir(path))
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and not item.startswith("."):
                tree[item] = {
                    'path': item_path,
                    'has_children': bool(get_subdirectories(item_path)) if current_depth < max_depth - 1 else False,
                    'children': get_folder_tree(item_path, max_depth, current_depth + 1) if current_depth < max_depth - 1 else {}
                }
    except (PermissionError, OSError):
        pass
    
    return tree


def render_folder_tree_item(
    folder_name: str,
    folder_path: str,
    has_children: bool,
    is_expanded: bool,
    depth: int,
    key_prefix: str,
) -> Tuple[bool, Optional[str]]:
    """
    Render a single folder tree item with expand/collapse functionality.
    
    Args:
        folder_name: Display name of the folder
        folder_path: Full path to the folder
        has_children: Whether the folder has subfolders
        is_expanded: Current expansion state
        depth: Indentation depth level
        key_prefix: Unique key prefix for the item
    
    Returns:
        Tuple of (was_clicked, selected_path)
    """
    indent = "    " * depth
    
    # Create columns for expand button and folder button
    if has_children:
        col1, col2 = st.columns([1, 10])
        with col1:
            expand_icon = "📂" if is_expanded else "📁"
            if st.button(expand_icon, key=f"{key_prefix}_expand", help="Expand/Collapse"):
                return True, None
        with col2:
            if st.button(f"{indent}{folder_name}", key=f"{key_prefix}_select", help=f"Select: {folder_path}", use_container_width=True):
                return False, folder_path
    else:
        # No children, just show the folder button
        if st.button(f"{indent}📁 {folder_name}", key=f"{key_prefix}_select", help=f"Select: {folder_path}", use_container_width=True):
            return False, folder_path
    
    return False, None


def render_tree_view_browser(
    key: str = "tree_browser",
    initial_path: Optional[str] = None,
    max_depth: int = 3,
) -> Optional[str]:
    """
    Render a JupyterLab-like hierarchical tree view for folder browsing.
    
    Args:
        key: Unique key for the component
        initial_path: Starting directory path
        max_depth: Maximum depth of folder tree to display
    
    Returns:
        Selected folder path or None
    """
    if initial_path is None:
        initial_path = os.path.expanduser("~")
    
    # Initialize tree state
    if f"{key}_expanded" not in st.session_state:
        st.session_state[f"{key}_expanded"] = set()
    if f"{key}_root" not in st.session_state:
        st.session_state[f"{key}_root"] = initial_path
    
    root_path = st.session_state[f"{key}_root"]
    expanded_folders = st.session_state[f"{key}_expanded"]
    
    selected_path = None
    
    # Get folder tree
    tree = get_folder_tree(root_path, max_depth=max_depth)
    
    # Render tree items recursively
    def render_tree_recursive(tree_dict: Dict, parent_path: str, depth: int = 0):
        nonlocal selected_path
        
        for folder_name, folder_info in tree_dict.items():
            folder_path = folder_info['path']
            has_children = folder_info['has_children']
            children = folder_info.get('children', {})
            is_expanded = folder_path in expanded_folders
            
            key_prefix = f"{key}_{folder_path.replace('/', '_').replace(' ', '_')}"
            
            # Render the folder item
            expand_toggled, sel_path = render_folder_tree_item(
                folder_name, folder_path, has_children, is_expanded, depth, key_prefix
            )
            
            if expand_toggled:
                # Toggle expansion state
                if is_expanded:
                    expanded_folders.discard(folder_path)
                else:
                    expanded_folders.add(folder_path)
                st.rerun()
            
            if sel_path:
                selected_path = sel_path
            
            # Render children if expanded
            if is_expanded and children:
                render_tree_recursive(children, folder_path, depth + 1)
    
    # Render the tree
    if tree:
        render_tree_recursive(tree, root_path)
    else:
        st.info("📂 No subfolders in this directory")
    
    return selected_path


def open_folder_dialog(initial_path: str) -> Optional[str]:
    """
    Open a native tkinter folder selection dialog.
    
    On macOS, tkinter dialogs may not work properly with certain Python installations
    (e.g., Python from Homebrew or conda without proper Tk framework).
    This function handles these cases gracefully.

    Args:
        initial_path: Initial directory to show in the dialog

    Returns:
        Selected folder path or None if cancelled/unavailable
    """
    if not TKINTER_AVAILABLE:
        return None

    try:
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()

        # On macOS, we need to bring the dialog to front
        if platform.system() == "Darwin":
            # macOS specific: lift the window and make it topmost
            try:
                root.lift()
                root.attributes("-topmost", True)
                root.focus_force()
                root.update()
            except tk.TclError:
                # If Tk is not properly configured on macOS, fall back
                root.destroy()
                return None
        else:
            root.attributes("-topmost", True)

        # Open folder dialog
        folder_path = filedialog.askdirectory(
            initialdir=initial_path, title="Select Working Directory", parent=root
        )

        # Clean up
        root.destroy()

        # Return the selected path (empty string if cancelled)
        return folder_path if folder_path else None

    except (tk.TclError, Exception) as e:
        # If tkinter fails for any reason, return None
        # On some systems, especially macOS with certain Python installations,
        # tkinter may not be properly configured
        # Common issues:
        # - Python from Homebrew without python-tk
        # - conda environments without proper Tk framework
        # - Running via SSH without X11 forwarding
        return None


def render_directory_browser(
    key: str = "directory_browser",
    initial_path: Optional[str] = None,
    help_text: str = "Choose the base directory where calculation folders will be created",
) -> str:
    """
    Render an enhanced directory browser with subfolder navigation.

    Args:
        key: Unique key for the component
        initial_path: Initial directory path
        help_text: Help text to display

    Returns:
        Selected directory path
    """
    if initial_path is None:
        initial_path = os.path.expanduser("~")

    # Initialize browsing state
    if f"{key}_current_path" not in st.session_state:
        st.session_state[f"{key}_current_path"] = initial_path

    current_path = st.session_state[f"{key}_current_path"]

    # Add navigation mode selector
    st.sidebar.markdown("**Navigation Mode:**")
    nav_mode = st.sidebar.radio(
        "Select navigation style:",
        options=["🌳 Tree View (JupyterLab-like)", "📋 Classic Navigation"],
        key=f"{key}_nav_mode",
        help="Tree View provides a hierarchical folder browser similar to JupyterLab. "
             "Classic Navigation offers traditional folder-by-folder browsing.",
        label_visibility="collapsed"
    )
    st.sidebar.markdown("---")
    
    # Handle tree view mode
    if nav_mode == "🌳 Tree View (JupyterLab-like)":
        # Add root directory selector for tree view
        st.sidebar.markdown("**Tree Root Directory:**")
        
        # Show current root with option to change
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.caption(f"📁 {current_path}")
        with col2:
            if st.button("📂", key=f"{key}_change_root", help="Change root directory"):
                # Use the classic browser below to change root
                st.session_state[f"{key}_changing_root"] = True
        
        # Show tree view
        if not st.session_state.get(f"{key}_changing_root", False):
            st.sidebar.markdown("**Folder Tree:**")
            
            with st.sidebar.container():
                # Render tree view in a scrollable area
                selected_from_tree = render_tree_view_browser(
                    key=f"{key}_tree",
                    initial_path=current_path,
                    max_depth=3
                )
                
                if selected_from_tree:
                    st.session_state[f"{key}_current_path"] = selected_from_tree
                    st.rerun()
            
            # Add quick access below tree
            st.sidebar.markdown("---")
            st.sidebar.markdown("**Quick Access:**")
            common_dirs = {
                "🏠 Home": os.path.expanduser("~"),
                "📊 Calculations": os.path.join(os.path.expanduser("~"), "calculations"),
                "📄 Documents": os.path.join(os.path.expanduser("~"), "Documents"),
            }
            
            for label, path in common_dirs.items():
                if st.sidebar.button(label, key=f"{key}_tree_quick_{label}", use_container_width=True):
                    if os.path.exists(path):
                        st.session_state[f"{key}_current_path"] = path
                        # Reset tree state for new root
                        st.session_state[f"{key}_tree_root"] = path
                        st.session_state[f"{key}_tree_expanded"] = set()
                        st.rerun()
            
            st.sidebar.markdown("---")
            st.sidebar.info(help_text)
            
            return current_path
        else:
            # Show classic browser to select new root
            st.sidebar.info("👆 Use the navigation below to select a new root directory")
            # Fall through to classic navigation
            st.session_state[f"{key}_changing_root"] = False
    
    # Classic navigation mode (also used when changing tree root)
    # Add "Browse System Folders" button if tkinter is available
    if TKINTER_AVAILABLE:
        st.sidebar.markdown("**System Folder Browser:**")
        if st.sidebar.button(
            "📂 Browse System Folders",
            key=f"{key}_tkinter_browse",
            help="Open native file dialog to browse anywhere on your system",
            use_container_width=True,
        ):
            selected_folder = open_folder_dialog(current_path)
            if selected_folder:
                st.session_state[f"{key}_current_path"] = selected_folder
                st.rerun()
            else:
                # Check if we're on macOS and provide helpful message
                if platform.system() == "Darwin":
                    st.sidebar.warning(
                        "⚠️ **macOS Note**: Native file dialog didn't open or was cancelled.\n\n"
                        "If the dialog didn't appear, this is a known issue with certain Python "
                        "installations on macOS (e.g., Homebrew, conda).\n\n"
                        "**Solution**: Switch to **Tree View** mode above for a JupyterLab-like "
                        "folder browser that works reliably on macOS!"
                    )
                else:
                    st.sidebar.info("No folder selected")
        st.sidebar.markdown("---")
    else:
        # If tkinter is not available, show a note about alternatives
        st.sidebar.info(
            "💡 **Note**: System file browser not available (tkinter not installed). "
            "Use **Tree View** mode above for easy navigation, or use Quick Access / Custom Path below."
        )
        st.sidebar.markdown("---")

    # Common directories as quick shortcuts
    st.sidebar.markdown("**Quick Access:**")
    common_dirs = {
        "🏠 Home": os.path.expanduser("~"),
        "📂 Current Directory": os.getcwd(),
        "📊 Calculations": os.path.join(os.path.expanduser("~"), "calculations"),
        "📄 Documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "🖥️ Desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    }

    cols = st.sidebar.columns(len(common_dirs))
    for idx, (label, path) in enumerate(common_dirs.items()):
        with cols[idx]:
            if st.button(
                label.split()[0],
                key=f"{key}_quick_{idx}",
                help=label,
                use_container_width=True,
            ):
                if os.path.exists(path):
                    st.session_state[f"{key}_current_path"] = path
                    st.rerun()

    st.sidebar.markdown("---")

    # Current path display with parent navigation
    st.sidebar.markdown("**Current Path:**")

    # Show path with ability to go up
    parent_path = os.path.dirname(current_path)
    if parent_path and parent_path != current_path:
        col1, col2 = st.sidebar.columns([1, 4])
        with col1:
            if st.button("⬆️", key=f"{key}_up", help="Go to parent directory"):
                st.session_state[f"{key}_current_path"] = parent_path
                st.rerun()
        with col2:
            st.caption(f"📁 {current_path}")
    else:
        st.sidebar.caption(f"📁 {current_path}")

    # Browse subdirectories
    subdirs = get_subdirectories(current_path)

    if subdirs:
        st.sidebar.markdown("**Subfolders:**")

        # Show subdirectories in a selectbox for better UX
        subdir_names = [os.path.basename(d) for d in subdirs]

        # Add option to stay in current directory
        display_options = ["(Stay here)"] + subdir_names

        selected_subdir = st.sidebar.selectbox(
            "Select subfolder:",
            options=display_options,
            key=f"{key}_subdir_selector",
            help="Choose a subfolder or stay in current directory",
        )

        if selected_subdir != "(Stay here)":
            idx = subdir_names.index(selected_subdir)
            col1, col2 = st.sidebar.columns([3, 1])
            with col2:
                if st.button("→", key=f"{key}_enter_subdir", help="Enter this folder"):
                    st.session_state[f"{key}_current_path"] = subdirs[idx]
                    st.rerun()
    else:
        st.sidebar.info("📂 No subfolders in this directory")

    st.sidebar.markdown("---")

    # Custom path input
    with st.sidebar.expander("✏️ Enter Custom Path", expanded=False):
        custom_path = st.text_input(
            "Enter path:",
            value=current_path,
            key=f"{key}_custom_path",
            help="Enter a custom directory path",
        )

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Go", key=f"{key}_go_custom", use_container_width=True):
                # Validate path
                expanded_path = os.path.expanduser(custom_path)
                expanded_path = os.path.abspath(expanded_path)

                if os.path.exists(expanded_path) and os.path.isdir(expanded_path):
                    st.session_state[f"{key}_current_path"] = expanded_path
                    st.rerun()
                else:
                    st.error("❌ Invalid directory path")

        with col2:
            if st.button("Create", key=f"{key}_create_dir", use_container_width=True):
                expanded_path = os.path.expanduser(custom_path)
                expanded_path = os.path.abspath(expanded_path)

                try:
                    os.makedirs(expanded_path, exist_ok=True)
                    st.session_state[f"{key}_current_path"] = expanded_path
                    st.success(f"✅ Created")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    st.sidebar.markdown("---")
    st.sidebar.info(help_text)

    return current_path
