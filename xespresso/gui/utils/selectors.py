"""
Selector utilities for machine and code selection in the GUI.

These functions provide reusable components for selecting already-configured
machines and codes, separate from the configuration/setup pages.
"""

import streamlit as st
import os

try:
    from xespresso.machines.config.loader import (
        load_machine,
        list_machines,
        DEFAULT_CONFIG_PATH,
        DEFAULT_MACHINES_DIR,
    )
    from xespresso.codes.manager import load_codes_config, DEFAULT_CODES_DIR

    XESPRESSO_AVAILABLE = True
except ImportError:
    XESPRESSO_AVAILABLE = False


def render_machine_selector(key="machine_selector", help_text=None):
    """
    Render a machine selector dropdown.

    This is separate from machine configuration - it only allows selecting
    from already-configured machines.

    Args:
        key: Unique key for the selector widget
        help_text: Optional help text for the selector

    Returns:
        tuple: (machine_name, machine_object) or (None, None) if no selection
    """
    if not XESPRESSO_AVAILABLE:
        st.error("xespresso modules not available.")
        return None, None

    try:
        machines_list = list_machines(DEFAULT_CONFIG_PATH, DEFAULT_MACHINES_DIR)

        if not machines_list:
            st.warning(
                "⚠️ No machines configured. Please configure a machine first in the Machine Configuration page."
            )
            return None, None

        # Use session state for persistent selection
        default_idx = 0
        if (
            st.session_state.get("current_machine_name")
            and st.session_state.current_machine_name in machines_list
        ):
            default_idx = machines_list.index(st.session_state.current_machine_name)

        selected_machine = st.selectbox(
            "Select Machine:",
            machines_list,
            index=default_idx,
            key=key,
            help=help_text or "Choose a configured machine for your calculations",
        )

        if selected_machine:
            try:
                machine = load_machine(
                    DEFAULT_CONFIG_PATH,
                    selected_machine,
                    DEFAULT_MACHINES_DIR,
                    return_object=True,
                )
                st.session_state.current_machine_name = selected_machine
                st.session_state.current_machine = machine

                # Show machine info
                with st.expander("📋 Machine Details", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Name:** {machine.name}")
                        st.write(f"**Execution:** {machine.execution}")
                        st.write(f"**Scheduler:** {machine.scheduler}")
                    with col2:
                        st.write(f"**Working Dir:** {machine.workdir}")
                        st.write(f"**Processors:** {machine.nprocs}")
                        if machine.is_remote:
                            st.write(f"**Host:** {machine.host}")

                return selected_machine, machine
            except Exception as e:
                st.error(f"Error loading machine: {e}")
                return None, None
    except Exception as e:
        st.warning(f"Could not load machines list: {e}")
        return None, None


def render_codes_selector(machine_name, key="codes_selector", help_text=None):
    """
    Render a codes/version selector for a specific machine.

    This is separate from codes configuration - it only allows selecting
    from already-configured codes and versions.

    Args:
        machine_name: Name of the machine to load codes for
        key: Unique key for the selector widget
        help_text: Optional help text for the selector

    Returns:
        CodesConfig object or None if no selection
    """
    if not XESPRESSO_AVAILABLE or not machine_name:
        return None

    try:
        codes_config = load_codes_config(machine_name, DEFAULT_CODES_DIR)

        if not codes_config:
            st.warning(
                f"⚠️ No codes configured for machine '{machine_name}'. Please configure codes first in the Codes Configuration page."
            )
            return None

        # Check if multiple versions are available
        if codes_config.versions:
            available_versions = codes_config.list_versions()

            if len(available_versions) > 1:
                st.info(
                    f"📦 Multiple QE versions available: {', '.join(available_versions)}"
                )

            # Version selector
            default_idx = 0
            if (
                st.session_state.get("selected_code_version")
                and st.session_state.selected_code_version in available_versions
            ):
                default_idx = available_versions.index(
                    st.session_state.selected_code_version
                )

            selected_version = st.selectbox(
                "Select QE Version:",
                available_versions,
                index=default_idx,
                key=key,
                help=help_text or "Choose which Quantum ESPRESSO version to use",
            )

            if selected_version:
                # Load codes for the selected version
                version_config = load_codes_config(
                    machine_name, DEFAULT_CODES_DIR, version=selected_version
                )
                st.session_state.selected_code_version = selected_version
                st.session_state.current_codes = version_config

                # Show version info
                with st.expander("⚙️ Version Details", expanded=False):
                    version_codes = version_config.get_all_codes(
                        version=selected_version
                    )
                    st.write(f"**Version:** {selected_version}")
                    if (
                        version_config.versions
                        and selected_version in version_config.versions
                    ):
                        label = version_config.versions[selected_version].get("label")
                        if label:
                            st.write(f"**Label:** {label}")
                    st.write(f"**Codes:** {len(version_codes)} executables configured")

                    # Show code list
                    code_names = list(version_codes.keys())
                    st.write(f"**Available codes:** {', '.join(code_names)}")

                return version_config
        else:
            # Single version or no version structure
            st.session_state.current_codes = codes_config

            with st.expander("⚙️ Codes Details", expanded=False):
                all_codes = codes_config.get_all_codes()
                st.write(f"**Codes:** {len(all_codes)} executables configured")
                code_names = list(all_codes.keys())
                st.write(f"**Available codes:** {', '.join(code_names)}")

            return codes_config

    except Exception as e:
        st.error(f"Error loading codes: {e}")
        return None


def render_workdir_browser(current_dir=None, key="workdir_browser"):
    """
    Render an enhanced working directory browser/selector with folder navigation.

    Features:
    - Text input for direct path entry
    - Quick access buttons (Current, Home)
    - Folder navigator with dropdown to browse subfolders
    - Parent directory navigation
    - Visual directory contents preview

    Args:
        current_dir: Current working directory path
        key: Unique key for the widget

    Returns:
        str: Selected directory path
    """
    if current_dir is None:
        current_dir = st.session_state.get("local_workdir", os.getcwd())

    # Initialize session state if not set
    if "local_workdir" not in st.session_state:
        st.session_state.local_workdir = current_dir

    st.subheader("📁 Working Directory")

    # Quick access buttons
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

    with col1:
        workdir = st.text_input(
            "Directory Path:",
            value=st.session_state.local_workdir,
            key=f"{key}_input",
            help="Enter the path to your working directory or use the navigator below",
        )

    with col2:
        if st.button(
            "📂 Current", key=f"{key}_current", help="Go to current working directory"
        ):
            st.session_state.local_workdir = os.getcwd()
            st.rerun()

    with col3:
        if st.button("🏠 Home", key=f"{key}_home", help="Go to home directory"):
            st.session_state.local_workdir = os.path.expanduser("~")
            st.rerun()

    with col4:
        if st.button("⬆️ Parent", key=f"{key}_parent", help="Go to parent directory"):
            current_dir = st.session_state.local_workdir
            st.session_state.local_workdir = os.path.dirname(current_dir)
            st.rerun()

    with col5:
        if st.button("🗂️ Browse", key=f"{key}_browse", help="Browse for a folder"):
            # Store the browse request in session state
            st.session_state[f"{key}_show_browser"] = True
            st.rerun()

    # Show folder browser modal if requested
    if st.session_state.get(f"{key}_show_browser", False):
        st.markdown("---")
        st.subheader("🗂️ Folder Browser")

        # Start from current directory or home
        if f"{key}_browser_current" not in st.session_state:
            st.session_state[f"{key}_browser_current"] = st.session_state.local_workdir

        browser_dir = st.session_state[f"{key}_browser_current"]

        # Show current browser directory
        st.info(f"📍 Browsing: `{browser_dir}`")

        # Browser navigation buttons
        bcol1, bcol2, bcol3 = st.columns([1, 1, 2])
        with bcol1:
            if st.button("⬆️ Up", key=f"{key}_browser_up"):
                st.session_state[f"{key}_browser_current"] = os.path.dirname(
                    browser_dir
                )
                st.rerun()
        with bcol2:
            if st.button("🏠 Home", key=f"{key}_browser_home"):
                st.session_state[f"{key}_browser_current"] = os.path.expanduser("~")
                st.rerun()

        # List directories in browser_dir
        try:
            browser_dir = os.path.abspath(os.path.expanduser(browser_dir))
            if os.path.exists(browser_dir) and os.path.isdir(browser_dir):
                contents = os.listdir(browser_dir)
                subdirs = [
                    d
                    for d in contents
                    if os.path.isdir(os.path.join(browser_dir, d))
                    and not d.startswith(".")
                ]
                subdirs.sort()

                if subdirs:
                    st.write("**📁 Select a folder:**")
                    for subdir in subdirs[
                        :30
                    ]:  # Limit to 30 folders for UI performance
                        col_folder, col_select = st.columns([3, 1])
                        with col_folder:
                            st.text(f"📁 {subdir}")
                        with col_select:
                            if st.button(
                                "Select", key=f"{key}_browser_select_{subdir}"
                            ):
                                new_path = os.path.join(browser_dir, subdir)
                                st.session_state[f"{key}_browser_current"] = new_path
                                st.rerun()

                    if len(subdirs) > 30:
                        st.caption(
                            f"... and {len(subdirs) - 30} more folders (scroll up to see more)"
                        )
                else:
                    st.info("ℹ️ No subfolders in this directory")

                # Action buttons
                st.markdown("---")
                bcol1, bcol2, bcol3 = st.columns(3)
                with bcol1:
                    if st.button(
                        "✅ Use This Folder",
                        key=f"{key}_browser_confirm",
                        type="primary",
                    ):
                        st.session_state.local_workdir = browser_dir
                        st.session_state[f"{key}_show_browser"] = False
                        # Clean up browser state
                        if f"{key}_browser_current" in st.session_state:
                            del st.session_state[f"{key}_browser_current"]
                        st.rerun()
                with bcol2:
                    if st.button("❌ Cancel", key=f"{key}_browser_cancel"):
                        st.session_state[f"{key}_show_browser"] = False
                        # Clean up browser state
                        if f"{key}_browser_current" in st.session_state:
                            del st.session_state[f"{key}_browser_current"]
                        st.rerun()
        except Exception as e:
            st.error(f"❌ Error browsing directory: {e}")

        st.markdown("---")
        # Don't show the rest of the UI when browser is active
        return st.session_state.local_workdir

    # Validate directory
    if workdir:
        try:
            workdir = os.path.abspath(os.path.expanduser(workdir))

            if os.path.exists(workdir) and os.path.isdir(workdir):
                st.success(f"✅ Current directory: `{workdir}`")
                st.session_state.local_workdir = workdir

                # Folder Navigator Section
                st.markdown("---")
                st.subheader("📂 Folder Navigator")
                st.info("💡 Select a subfolder below to navigate into it")

                try:
                    # List subdirectories (validate workdir first)
                    # Note: workdir comes from user input, but this is intentional for a file browser.
                    # Security measures in place:
                    # 1. Path is validated to exist and be a directory
                    # 2. Application runs with user's permissions (can only access what user can access)
                    # 3. Symlinks are resolved with os.path.realpath()
                    # 4. Navigation is constrained with os.path.commonpath() checks
                    # 5. Directory names are validated to prevent traversal (no .., /, \)
                    if not os.path.isabs(workdir):
                        st.error("❌ Invalid path: must be absolute")
                        return current_dir

                    # Resolve any symlinks to get the real path
                    real_workdir = os.path.realpath(workdir)

                    contents = os.listdir(real_workdir)
                    subdirs = []
                    for d in contents:
                        # Skip hidden directories and validate each subdirectory
                        if d.startswith("."):
                            continue
                        subdir_path = os.path.join(real_workdir, d)
                        # Ensure the path doesn't escape the parent directory
                        if (
                            os.path.isdir(subdir_path)
                            and os.path.commonpath(
                                [real_workdir, os.path.realpath(subdir_path)]
                            )
                            == real_workdir
                        ):
                            subdirs.append(d)
                    subdirs.sort()

                    if subdirs:
                        # Create columns for better layout
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            selected_subdir = st.selectbox(
                                "Select subfolder to navigate:",
                                options=["(Stay in current directory)"] + subdirs,
                                key=f"{key}_subdir_select",
                                help="Choose a subfolder to navigate into",
                            )

                        with col2:
                            st.write("")  # Spacing
                            st.write("")  # Spacing
                            if st.button(
                                "➡️ Navigate", key=f"{key}_navigate", type="primary"
                            ):
                                if selected_subdir != "(Stay in current directory)":
                                    # Validate selected subdirectory to prevent path traversal
                                    if (
                                        ".." in selected_subdir
                                        or "/" in selected_subdir
                                        or "\\" in selected_subdir
                                    ):
                                        st.error("❌ Invalid folder name")
                                    else:
                                        new_workdir = os.path.realpath(
                                            os.path.join(real_workdir, selected_subdir)
                                        )
                                        # Ensure the new path is within the parent directory
                                        if (
                                            os.path.commonpath(
                                                [real_workdir, new_workdir]
                                            )
                                            == real_workdir
                                        ):
                                            st.session_state.local_workdir = new_workdir
                                            st.rerun()
                                        else:
                                            st.error("❌ Invalid navigation path")

                        # Show quick preview of selected subfolder
                        if selected_subdir != "(Stay in current directory)":
                            # Validate before using
                            if (
                                ".." not in selected_subdir
                                and "/" not in selected_subdir
                                and "\\" not in selected_subdir
                            ):
                                subdir_path = os.path.realpath(
                                    os.path.join(real_workdir, selected_subdir)
                                )
                                # Ensure path is within parent directory
                                if (
                                    os.path.commonpath([real_workdir, subdir_path])
                                    == real_workdir
                                ):
                                    try:
                                        subdir_contents = os.listdir(subdir_path)
                                        subdir_subdirs = []
                                        subdir_files = []
                                        for item in subdir_contents:
                                            item_path = os.path.join(subdir_path, item)
                                            if os.path.isdir(item_path):
                                                subdir_subdirs.append(item)
                                            elif os.path.isfile(item_path):
                                                subdir_files.append(item)

                                        st.caption(
                                            f"📁 `{selected_subdir}` contains: {len(subdir_subdirs)} folders, {len(subdir_files)} files"
                                        )
                                    except:
                                        pass
                    else:
                        st.info("ℹ️ No subfolders in current directory")

                except PermissionError:
                    st.warning("⚠️ Permission denied to list directory contents")
                except Exception as e:
                    st.warning(f"⚠️ Could not list subfolders: {e}")

                # Directory Contents Section
                st.markdown("---")
                with st.expander("📋 Directory Contents (Full View)", expanded=False):
                    try:
                        contents = os.listdir(workdir)
                        dirs = [
                            d
                            for d in contents
                            if os.path.isdir(os.path.join(workdir, d))
                        ]
                        files = [
                            f
                            for f in contents
                            if os.path.isfile(os.path.join(workdir, f))
                        ]

                        # Show statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Items", len(contents))
                        with col2:
                            st.metric("Directories", len(dirs))
                        with col3:
                            st.metric("Files", len(files))

                        # Show directories
                        if dirs:
                            st.write("**📁 Directories:**")
                            dirs_display = sorted(dirs)
                            if len(dirs_display) > 20:
                                st.write(", ".join(dirs_display[:20]))
                                st.write(f"... and {len(dirs_display) - 20} more")
                            else:
                                st.write(", ".join(dirs_display))

                        # Show files
                        if files:
                            st.write("**📄 Files:**")
                            files_display = sorted(files)
                            if len(files_display) > 20:
                                st.write(", ".join(files_display[:20]))
                                st.write(f"... and {len(files_display) - 20} more")
                            else:
                                st.write(", ".join(files_display))

                    except PermissionError:
                        st.warning("⚠️ Permission denied to list directory contents")
                    except Exception as e:
                        st.warning(f"⚠️ Could not list directory contents: {e}")

                return workdir
            else:
                st.error(f"❌ Directory does not exist: {workdir}")
                st.info(
                    "💡 Use the Home or Current button to navigate to a valid directory"
                )
                return current_dir
        except Exception as e:
            st.error(f"❌ Invalid path: {e}")
            return current_dir

    return current_dir
