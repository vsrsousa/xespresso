"""
Standalone Hubbard configuration selector utility for GUI pages.

This module provides a component for configuring Hubbard parameters
independently of magnetic configuration.
"""

import streamlit as st
from typing import Dict, Set, Optional


# Element-to-orbital mapping for common elements requiring Hubbard U
ELEMENT_ORBITAL_MAP = {
    # 3d transition metals (first row)
    "Sc": ["3d"],
    "Ti": ["3d"],
    "V": ["3d"],
    "Cr": ["3d"],
    "Mn": ["3d"],
    "Fe": ["3d"],
    "Co": ["3d"],
    "Ni": ["3d"],
    "Cu": ["3d"],
    "Zn": ["3d"],
    # 4d transition metals (second row)
    "Y": ["4d"],
    "Zr": ["4d"],
    "Nb": ["4d"],
    "Mo": ["4d"],
    "Tc": ["4d"],
    "Ru": ["4d"],
    "Rh": ["4d"],
    "Pd": ["4d"],
    "Ag": ["4d"],
    "Cd": ["4d"],
    # 5d transition metals (third row)
    "La": ["5d"],
    "Hf": ["5d"],
    "Ta": ["5d"],
    "W": ["5d"],
    "Re": ["5d"],
    "Os": ["5d"],
    "Ir": ["5d"],
    "Pt": ["5d"],
    "Au": ["5d"],
    "Hg": ["5d"],
    # Lanthanides (4f)
    "Ce": ["4f"],
    "Pr": ["4f"],
    "Nd": ["4f"],
    "Pm": ["4f"],
    "Sm": ["4f"],
    "Eu": ["4f"],
    "Gd": ["4f"],
    "Tb": ["4f"],
    "Dy": ["4f"],
    "Ho": ["4f"],
    "Er": ["4f"],
    "Tm": ["4f"],
    "Yb": ["4f"],
    "Lu": ["4f"],
    # Actinides (5f)
    "Th": ["5f"],
    "Pa": ["5f"],
    "U": ["5f"],
    "Np": ["5f"],
    "Pu": ["5f"],
    "Am": ["5f"],
    "Cm": ["5f"],
    "Bk": ["5f"],
    "Cf": ["5f"],
    # p-block elements (sometimes need U)
    "O": ["2p"],
    "N": ["2p"],
    "C": ["2p"],
    "S": ["3p"],
    "P": ["3p"],
    "Si": ["3p"],
}


def get_suggested_orbitals(element: str) -> list:
    """
    Get suggested orbital types for a given element.

    Args:
        element: Element symbol (e.g., 'Fe', 'O')

    Returns:
        List of suggested orbital strings
    """
    return ELEMENT_ORBITAL_MAP.get(element, ["3d"])  # Default to 3d if unknown


def render_hubbard_selector(
    elements: Set[str], config_dict: dict, key_prefix: str = "calc"
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
        key=f"{key_prefix}_enable_hubbard",
    )
    config_dict["enable_hubbard"] = enable_hubbard

    if enable_hubbard:
        st.markdown("**Configure Hubbard U Parameters:**")
        st.info(
            """
        💡 **DFT+U Corrections:**
        - Used for strongly correlated systems (3d/4f electrons)
        - Common for transition metals (Fe, Mn, Co, Ni, etc.)
        - U values typically range from 2-8 eV
        - Check literature for appropriate U values for your system
        """
        )

        # Format selection
        format_type = st.radio(
            "Hubbard Format:",
            ["Old Format (QE < 7.0)", "New Format (QE >= 7.0)"],
            index=0 if config_dict.get("hubbard_format", "old") == "old" else 1,
            help="New format (QE 7.0+) allows orbital-specific U parameters",
            key=f"{key_prefix}_hubbard_format",
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

                    # Get suggested orbitals for this element
                    suggested_orbitals = get_suggested_orbitals(element)
                    default_orbital = suggested_orbitals[0]

                    # Show info about suggested orbitals
                    if len(suggested_orbitals) > 1:
                        st.info(
                            f"💡 Common orbitals for {element}: {', '.join(suggested_orbitals)}"
                        )
                    else:
                        st.info(f"💡 Common orbital for {element}: {default_orbital}")

                    # Get orbital type (use selectbox for common orbitals, allow custom)
                    current_orbital = config_dict.get(
                        f"hubbard_orbital_{element}", default_orbital
                    )

                    # Provide selectbox with suggested orbitals plus "Custom" option
                    orbital_options = suggested_orbitals + ["Custom..."]

                    # Determine which option to select
                    if current_orbital in suggested_orbitals:
                        orbital_select_idx = suggested_orbitals.index(current_orbital)
                    else:
                        orbital_select_idx = len(
                            suggested_orbitals
                        )  # "Custom..." option

                    orbital_selection = st.selectbox(
                        f"Select orbital for {element}:",
                        options=orbital_options,
                        index=orbital_select_idx,
                        help=f"Choose orbital for Hubbard U. Common choices for {element}: {', '.join(suggested_orbitals)}",
                        key=f"{key_prefix}_hubbard_orbital_select_{element}",
                    )

                    # If "Custom..." is selected, show text input
                    if orbital_selection == "Custom...":
                        orbital = st.text_input(
                            f"Custom orbital for {element}:",
                            value=(
                                current_orbital
                                if current_orbital not in suggested_orbitals
                                else ""
                            ),
                            help="Examples: '3d', '4f', '2p'",
                            key=f"{key_prefix}_hubbard_orbital_custom_{element}",
                        )
                    else:
                        orbital = orbital_selection

                    config_dict[f"hubbard_orbital_{element}"] = orbital

                    u_value = st.number_input(
                        f"U value (eV) for {element}-{orbital}:",
                        value=float(current_u),
                        min_value=0.0,
                        max_value=20.0,
                        step=0.1,
                        help="Hubbard U parameter in eV",
                        key=f"{key_prefix}_hubbard_u_{element}",
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
                        key=f"{key_prefix}_hubbard_u_{element}",
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
                key=f"{key_prefix}_hubbard_projector",
            )
            config_dict["hubbard_projector"] = projector

        # Show summary
        with st.expander("📋 Hubbard Configuration Summary", expanded=False):
            if config_dict["hubbard_u"]:
                st.json(
                    {
                        "format": config_dict["hubbard_format"],
                        "U_parameters": config_dict["hubbard_u"],
                        "projector": (
                            config_dict.get("hubbard_projector")
                            if config_dict["hubbard_format"] == "new"
                            else "N/A"
                        ),
                    }
                )
            else:
                st.warning("No Hubbard U parameters configured")
    else:
        # Clear Hubbard config if disabled
        config_dict["hubbard_u"] = {}
