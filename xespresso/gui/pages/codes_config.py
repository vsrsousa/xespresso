"""
Codes Configuration Page for xespresso GUI.

This module handles the Quantum ESPRESSO codes configuration interface,
allowing users to:
- Auto-detect QE executables on machines
- Configure multiple versions
- Save and load code configurations
"""

import streamlit as st
import traceback

try:
    from xespresso.machines.config.loader import (
        list_machines,
        DEFAULT_CONFIG_PATH, DEFAULT_MACHINES_DIR
    )
    from xespresso.codes.manager import (
        detect_qe_codes, load_codes_config, CodesManager,
        DEFAULT_CODES_DIR
    )
    XESPRESSO_AVAILABLE = True
except ImportError:
    XESPRESSO_AVAILABLE = False


def render_codes_config_page():
    """Render the codes configuration page."""
    st.header("Quantum ESPRESSO Codes Configuration")
    st.markdown("""
    Configure Quantum ESPRESSO executable paths for different machines.
    Auto-detection is supported for both local and remote systems.
    """)
    
    if not XESPRESSO_AVAILABLE:
        st.error("xespresso modules not available. Cannot configure codes.")
        return
    
    # Machine selection
    try:
        machines_list = list_machines(DEFAULT_CONFIG_PATH, DEFAULT_MACHINES_DIR)
        if machines_list:
            selected_machine = st.selectbox(
                "Select Machine:",
                machines_list,
                help="Choose the machine to configure codes for"
            )
        else:
            st.warning("⚠️ No machines configured. Please configure a machine first.")
            selected_machine = None
    except Exception as e:
        st.warning(f"Could not load machines: {e}")
        selected_machine = None
    
    if selected_machine:
        st.subheader(f"Codes Configuration for: {selected_machine}")
        
        # Feature 1: Module Listing - Discover available modules
        with st.expander("🔍 Discover Available Modules", expanded=False):
            st.markdown("""
            List available Quantum ESPRESSO modules on the selected machine.
            This helps you find which QE versions are available before configuring codes.
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                search_pattern = st.text_input(
                    "Search Pattern (optional)",
                    value="espresso",
                    help="Filter modules by pattern (e.g., 'espresso', 'qe', 'quantum')"
                )
            with col2:
                env_setup_modules = st.text_input(
                    "Environment Setup (optional)",
                    placeholder="source /etc/profile",
                    help="Shell commands to run before listing modules"
                )
            
            if st.button("🔎 List Available Modules"):
                with st.spinner("Discovering modules..."):
                    try:
                        # Get machine config to check if it's remote
                        from xespresso.machines.config.loader import load_machine
                        machine = load_machine(selected_machine, DEFAULT_CONFIG_PATH, DEFAULT_MACHINES_DIR)
                        
                        ssh_connection = None
                        if machine and hasattr(machine, 'host') and machine.host:
                            # Remote machine
                            ssh_connection = {
                                'host': machine.host,
                                'username': machine.username,
                                'port': getattr(machine, 'port', 22)
                            }
                        
                        modules = CodesManager.list_available_modules(
                            ssh_connection=ssh_connection,
                            env_setup=env_setup_modules if env_setup_modules else None,
                            search_pattern=search_pattern if search_pattern else None
                        )
                        
                        if modules:
                            st.success(f"✅ Found {len(modules)} modules!")
                            st.session_state['discovered_modules'] = modules
                            
                            # Display as a nice list
                            st.markdown("**Available Modules:**")
                            for module in modules:
                                st.markdown(f"- `{module}`")
                            
                            st.info("💡 Copy a module name and paste it in the 'Modules to Load' field below.")
                        else:
                            st.warning("⚠️ No modules found matching the pattern.")
                    except Exception as e:
                        st.error(f"❌ Error listing modules: {e}")
                        st.code(traceback.format_exc())
        
        # Auto-detection section
        st.subheader("Auto-Detect Codes")
        
        with st.form("detect_codes_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                qe_prefix = st.text_input(
                    "QE Installation Prefix (optional)",
                    help="e.g., /opt/qe-7.2/bin"
                )
                # Feature 2: Explicit QE Version Specification
                qe_version = st.text_input(
                    "QE Version (optional but recommended)",
                    placeholder="e.g., 7.2, 7.1, 6.8",
                    help="Explicitly specify Quantum ESPRESSO version to avoid confusion with compiler versions"
                )
                version_label = st.text_input(
                    "Version Label (optional)",
                    help="Custom label for this version (e.g., 'qe-7.2', 'qe-dev')"
                )
                modules_str = st.text_area(
                    "Modules to Load (optional, one per line)",
                    value="\n".join(st.session_state.get('discovered_modules', [])[:1]) if st.session_state.get('discovered_modules') else "",
                    help="Version-specific modules (e.g., 'qe/7.2' or 'quantum_espresso-7.4.1')"
                )
            
            with col2:
                search_paths_str = st.text_area(
                    "Additional Search Paths (optional, one per line)",
                    help="Additional directories to search for executables"
                )
                st.info("""
                **💡 Tip: Explicit Version**
                
                Auto-detection may pick up compiler versions.
                It's recommended to specify the QE version explicitly!
                """)
            
            detect_button = st.form_submit_button("🔍 Auto-Detect Codes")
        
        if detect_button:
            with st.spinner("Detecting Quantum ESPRESSO codes..."):
                try:
                    modules = [m.strip() for m in modules_str.split("\n") if m.strip()] if modules_str else None
                    search_paths = [p.strip() for p in search_paths_str.split("\n") if p.strip()] if search_paths_str else None
                    
                    codes_config = detect_qe_codes(
                        machine_name=selected_machine,
                        qe_prefix=qe_prefix if qe_prefix else None,
                        search_paths=search_paths,
                        modules=modules,
                        auto_load_machine=True,
                        qe_version=qe_version.strip() if qe_version and qe_version.strip() else None
                    )
                    
                    if codes_config and codes_config.codes:
                        st.success(f"✅ Detected {len(codes_config.codes)} codes!")
                        
                        # Add version label if provided
                        if version_label:
                            codes_config.version_label = version_label
                        
                        st.session_state.current_codes = codes_config
                        
                        # Display detected codes
                        st.subheader("Detected Codes")
                        codes_data = []
                        for name, code in codes_config.codes.items():
                            codes_data.append({
                                "Code": name,
                                "Path": code.path,
                                "Version": code.version or "Unknown",
                                "Label": version_label or "default"
                            })
                        st.table(codes_data)
                        
                        # Save option with clear explanation
                        st.info("""
                        **💾 Saving Codes:**
                        - Detected codes will be **merged** with existing configurations
                        - Multiple versions on the same machine are supported
                        - Existing codes with different paths/versions will be kept
                        """)
                        
                        if st.button("💾 Save Codes Configuration"):
                            try:
                                filepath = CodesManager.save_config(
                                    codes_config,
                                    output_dir=DEFAULT_CODES_DIR,
                                    overwrite=False,
                                    merge=True
                                )
                                st.success(f"✅ Codes saved to: {filepath}")
                                st.info("Multiple versions are preserved. Reload the page to see all versions.")
                            except Exception as e:
                                st.error(f"Error saving codes: {e}")
                                st.code(traceback.format_exc())
                    else:
                        st.warning("⚠️ No codes detected. Check paths and modules.")
                except Exception as e:
                    st.error(f"❌ Error detecting codes: {e}")
                    st.code(traceback.format_exc())
        
        # Load existing configuration
        st.subheader("Existing Codes Configuration")
        try:
            existing_codes = load_codes_config(selected_machine, DEFAULT_CODES_DIR)
            if existing_codes:
                st.success(f"✅ Loaded existing configuration")
                
                # Feature 3: Version Selection - Show available versions
                if existing_codes.versions:
                    available_versions = existing_codes.list_versions()
                    st.info(f"📦 Available QE versions: {', '.join(available_versions)}")
                    
                    # Version selector
                    st.subheader("Select QE Version for Calculations")
                    selected_version = st.selectbox(
                        "Choose QE Version:",
                        available_versions,
                        help="Select which Quantum ESPRESSO version to use for your calculations"
                    )
                    
                    # Load codes for the selected version
                    if st.button(f"Load QE {selected_version} Configuration"):
                        with st.spinner(f"Loading QE {selected_version}..."):
                            try:
                                version_config = load_codes_config(
                                    selected_machine, 
                                    DEFAULT_CODES_DIR, 
                                    version=selected_version
                                )
                                
                                if version_config:
                                    st.success(f"✅ Loaded QE {selected_version} configuration!")
                                    st.session_state.current_codes = version_config
                                    st.session_state.selected_qe_version = selected_version
                                    
                                    # Display codes for this version
                                    st.markdown(f"**Codes for QE {selected_version}:**")
                                    version_codes_data = []
                                    for name, code in version_config.codes.items():
                                        version_codes_data.append({
                                            "Code": name,
                                            "Path": code.path,
                                            "Version": code.version or selected_version,
                                        })
                                    st.table(version_codes_data)
                                    
                                    # Show version-specific modules if available
                                    if hasattr(version_config, 'modules') and version_config.modules:
                                        st.markdown(f"**Modules for QE {selected_version}:**")
                                        for module in version_config.modules:
                                            st.markdown(f"- `{module}`")
                                else:
                                    st.warning(f"⚠️ Could not load QE {selected_version} configuration.")
                            except Exception as e:
                                st.error(f"❌ Error loading version: {e}")
                                st.code(traceback.format_exc())
                else:
                    # No version-specific configuration, show all codes
                    codes_data = []
                    for name, code in existing_codes.codes.items():
                        codes_data.append({
                            "Code": name,
                            "Path": code.path,
                            "Version": code.version or "Unknown",
                            "Modules": ", ".join(code.modules) if hasattr(code, 'modules') and code.modules else "None"
                        })
                    st.table(codes_data)
                    
                    st.session_state.current_codes = existing_codes
                    
                    # Code/version selection for calculations
                    st.subheader("Select Code Version for Calculations")
                    if existing_codes.codes:
                        code_options = list(existing_codes.codes.keys())
                        selected_code = st.selectbox(
                            "Select QE code to use:",
                            code_options,
                            help="Choose which QE code to use for your calculations"
                        )
                        st.session_state.selected_code_version = selected_code
                        
                        selected_code_obj = existing_codes.codes[selected_code]
                        st.info(f"""
                        **Selected Code Details:**
                        - Path: `{selected_code_obj.path}`
                        - Version: {selected_code_obj.version or 'Unknown'}
                        """)
            else:
                st.info("ℹ️ No codes configuration found for this machine.")
        except Exception as e:
            st.warning(f"Could not load codes configuration: {e}")
