"""
Magnetic configuration selector utility for GUI pages.

This module provides a reusable component for configuring magnetic properties
using xespresso's setup_magnetic_config functionality.
"""

import streamlit as st
from typing import Dict, Set, Optional


def render_magnetic_selector(
    elements: Set[str],
    config_dict: dict,
    key_prefix: str = "calc"
) -> None:
    """
    Render a magnetic configuration selector component.
    
    This component allows users to configure magnetic properties per element
    following xespresso's setup_magnetic_config pattern.
    
    Args:
        elements: Set of element symbols in the structure
        config_dict: Dictionary to store the magnetic configuration
        key_prefix: Prefix for widget keys to avoid conflicts
    """
    st.subheader("🧲 Magnetic Configuration")
    
    # Initialize magnetic config in config_dict if not present
    if "enable_magnetism" not in config_dict:
        config_dict["enable_magnetism"] = False
    if "magnetic_config" not in config_dict:
        config_dict["magnetic_config"] = {}
    
    # Checkbox to enable magnetic configuration
    enable_magnetism = st.checkbox(
        "Enable Magnetic Configuration",
        value=config_dict.get("enable_magnetism", False),
        help="Enable to configure magnetic moments per element. Required for magnetic systems.",
        key=f"{key_prefix}_enable_magnetism"
    )
    config_dict["enable_magnetism"] = enable_magnetism
    
    if enable_magnetism:
        st.markdown("**Configure Magnetic Moments:**")
        st.info("""
        💡 **How it works:**
        - Specify magnetic moment(s) for each element
        - Multiple values create non-equivalent atoms (different species)
        - Example: Fe = [1, -1] creates antiferromagnetic configuration
        - Example: Fe = [1] makes all Fe atoms equivalent with moment 1
        """)
        
        # Configure each element
        for element in sorted(elements):
            with st.expander(f"**{element}** Magnetization", expanded=False):
                # Get current config for this element
                current_config = config_dict["magnetic_config"].get(element, {})
                
                # Determine if using simple or advanced config
                if isinstance(current_config, dict) and 'mag' in current_config:
                    # Advanced config with Hubbard
                    mag_moments = current_config.get('mag', [0])
                else:
                    # Simple config - just list of moments
                    mag_moments = current_config if isinstance(current_config, list) else [0]
                
                # Input format selector
                config_type = st.radio(
                    "Configuration Type:",
                    ["Simple (magnetic moments only)", "Advanced (with Hubbard U)"],
                    index=1 if isinstance(current_config, dict) and 'mag' in current_config else 0,
                    key=f"{key_prefix}_mag_type_{element}",
                    help="Simple: Just specify magnetic moments. Advanced: Include Hubbard U parameters."
                )
                
                # Magnetic moments input
                st.markdown("**Magnetic Moments:**")
                moments_str = st.text_input(
                    f"Moments for {element} (comma-separated):",
                    value=", ".join(map(str, mag_moments)),
                    help="Example: '1, -1' for AFM, '1' for all equivalent, '0' for non-magnetic",
                    key=f"{key_prefix}_mag_moments_{element}"
                )
                
                # Parse moments
                try:
                    moments = [float(m.strip()) for m in moments_str.split(',') if m.strip()]
                    if not moments:
                        moments = [0]
                except ValueError:
                    st.error(f"Invalid input for {element}. Use numbers separated by commas.")
                    moments = [0]
                
                if config_type == "Simple (magnetic moments only)":
                    # Store as simple list
                    config_dict["magnetic_config"][element] = moments
                else:
                    # Advanced configuration with Hubbard
                    st.markdown("**Hubbard U Parameters:**")
                    
                    # Single U value or per-species
                    u_type = st.radio(
                        "U parameter type:",
                        ["Same U for all", "Different U per species"],
                        key=f"{key_prefix}_u_type_{element}"
                    )
                    
                    if u_type == "Same U for all":
                        u_value = st.number_input(
                            f"Hubbard U (eV) for {element}:",
                            value=float(current_config.get('U', 0.0)) if isinstance(current_config, dict) else 0.0,
                            min_value=0.0,
                            max_value=20.0,
                            step=0.1,
                            key=f"{key_prefix}_u_value_{element}"
                        )
                        u_param = u_value if u_value > 0 else None
                    else:
                        # Different U for each species
                        u_values_str = st.text_input(
                            f"Hubbard U values for {element} (comma-separated, one per moment):",
                            value=", ".join(map(str, current_config.get('U', [0] * len(moments)))) if isinstance(current_config.get('U'), list) else "",
                            key=f"{key_prefix}_u_values_{element}"
                        )
                        try:
                            u_values = [float(u.strip()) for u in u_values_str.split(',') if u.strip()]
                            u_param = u_values if u_values and any(u > 0 for u in u_values) else None
                        except ValueError:
                            st.error("Invalid U values. Use numbers separated by commas.")
                            u_param = None
                    
                    # Store advanced config
                    adv_config = {'mag': moments}
                    if u_param is not None:
                        adv_config['U'] = u_param
                    config_dict["magnetic_config"][element] = adv_config
                
                # Show what will be created
                num_species = len(moments)
                if num_species == 1:
                    st.caption(f"✓ Will create 1 species: {element} with moment {moments[0]}")
                else:
                    species_names = [element] + [f"{element}{i}" for i in range(1, num_species)]
                    st.caption(f"✓ Will create {num_species} species: {', '.join(species_names)}")
        
        # Additional options
        st.markdown("---")
        st.markdown("**Additional Options:**")
        
        col1, col2 = st.columns(2)
        with col1:
            expand_cell = st.checkbox(
                "Auto-expand cell",
                value=config_dict.get("expand_cell", False),
                help="Automatically expand cell if needed to accommodate magnetic configuration",
                key=f"{key_prefix}_expand_cell"
            )
            config_dict["expand_cell"] = expand_cell
        
        with col2:
            # QE version for format selection
            qe_version = st.selectbox(
                "QE Version:",
                ["auto", "6.x", "7.x"],
                index=["auto", "6.x", "7.x"].index(config_dict.get("qe_version", "auto")),
                help="Quantum ESPRESSO version (affects Hubbard format)",
                key=f"{key_prefix}_qe_version"
            )
            config_dict["qe_version"] = qe_version if qe_version != "auto" else None
        
        # Show summary
        with st.expander("📋 Configuration Summary", expanded=False):
            st.json(config_dict["magnetic_config"])
    else:
        # Clear magnetic config if disabled
        config_dict["magnetic_config"] = {}
