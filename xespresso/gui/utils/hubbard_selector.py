"""
Standalone Hubbard configuration selector utility for GUI pages.

This module provides a component for configuring Hubbard parameters
independently of magnetic configuration.
"""

import streamlit as st
from typing import Dict, Set, Optional


def render_hubbard_selector(
    elements: Set[str],
    config_dict: dict,
    key_prefix: str = "calc"
) -> None:
    """
    Render a Hubbard configuration selector component.
    
    This component allows users to configure Hubbard U and V parameters
    for DFT+U calculations.
    
    Args:
        elements: Set of element symbols in the structure
        config_dict: Dictionary to store the Hubbard configuration
        key_prefix: Prefix for widget keys to avoid conflicts
    """
    st.subheader("⚛️ Hubbard (DFT+U) Configuration")
    
    # Initialize Hubbard config in config_dict if not present
    if "enable_hubbard" not in config_dict:
        config_dict["enable_hubbard"] = False
    if "hubbard_u" not in config_dict:
        config_dict["hubbard_u"] = {}
    
    # Checkbox to enable Hubbard configuration
    enable_hubbard = st.checkbox(
        "Enable Hubbard (DFT+U) Corrections",
        value=config_dict.get("enable_hubbard", False),
        help="Enable DFT+U for strongly correlated systems (transition metals, rare earths)",
        key=f"{key_prefix}_enable_hubbard"
    )
    config_dict["enable_hubbard"] = enable_hubbard
    
    if enable_hubbard:
        st.markdown("**Configure Hubbard U Parameters:**")
        st.info("""
        💡 **DFT+U Corrections:**
        - Used for strongly correlated systems (3d/4f electrons)
        - Common for transition metals (Fe, Mn, Co, Ni, etc.)
        - U values typically range from 2-8 eV
        - Check literature for appropriate U values for your system
        """)
        
        # Format selection
        format_type = st.radio(
            "Hubbard Format:",
            ["Old Format (QE < 7.0)", "New Format (QE >= 7.0)"],
            index=0 if config_dict.get("hubbard_format", "old") == "old" else 1,
            help="New format (QE 7.0+) allows orbital-specific U parameters",
            key=f"{key_prefix}_hubbard_format"
        )
        config_dict["hubbard_format"] = "old" if "Old" in format_type else "new"
        
        # Configure U for each element
        for element in sorted(elements):
            with st.expander(f"**{element}** Hubbard U", expanded=False):
                # Current U value
                current_u = config_dict["hubbard_u"].get(element, 0.0)
                
                if config_dict["hubbard_format"] == "new":
                    # New format with orbital specification
                    st.markdown("**Orbital-Specific U:**")
                    
                    # Get orbital type
                    orbital = st.text_input(
                        f"Orbital for {element}:",
                        value=config_dict.get(f"hubbard_orbital_{element}", "3d"),
                        help="Examples: '3d', '4f', '2p'",
                        key=f"{key_prefix}_hubbard_orbital_{element}"
                    )
                    config_dict[f"hubbard_orbital_{element}"] = orbital
                    
                    u_value = st.number_input(
                        f"U value (eV) for {element}-{orbital}:",
                        value=float(current_u),
                        min_value=0.0,
                        max_value=20.0,
                        step=0.1,
                        help="Hubbard U parameter in eV",
                        key=f"{key_prefix}_hubbard_u_{element}"
                    )
                else:
                    # Old format - just U value
                    u_value = st.number_input(
                        f"U value (eV) for {element}:",
                        value=float(current_u),
                        min_value=0.0,
                        max_value=20.0,
                        step=0.1,
                        help="Hubbard U parameter in eV",
                        key=f"{key_prefix}_hubbard_u_{element}"
                    )
                
                # Store U value
                if u_value > 0:
                    config_dict["hubbard_u"][element] = u_value
                elif element in config_dict["hubbard_u"]:
                    del config_dict["hubbard_u"][element]
        
        # Additional Hubbard options
        if config_dict["hubbard_format"] == "new":
            st.markdown("---")
            st.markdown("**Projector Type:**")
            projector = st.selectbox(
                "Projector:",
                ["atomic", "ortho-atomic", "norm-atomic", "wf", "pseudo"],
                index=["atomic", "ortho-atomic", "norm-atomic", "wf", "pseudo"].index(
                    config_dict.get("hubbard_projector", "ortho-atomic")
                ),
                help="Projector type for Hubbard calculations (new format only)",
                key=f"{key_prefix}_hubbard_projector"
            )
            config_dict["hubbard_projector"] = projector
        
        # Show summary
        with st.expander("📋 Hubbard Configuration Summary", expanded=False):
            if config_dict["hubbard_u"]:
                st.json({
                    "format": config_dict["hubbard_format"],
                    "U_parameters": config_dict["hubbard_u"],
                    "projector": config_dict.get("hubbard_projector") if config_dict["hubbard_format"] == "new" else "N/A"
                })
            else:
                st.warning("No Hubbard U parameters configured")
    else:
        # Clear Hubbard config if disabled
        config_dict["hubbard_u"] = {}
