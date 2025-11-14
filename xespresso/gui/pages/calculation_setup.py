"""
Calculation Setup Page for xespresso GUI.

This page is responsible for configuring calculations and using the
calculation modules to prepare atoms and Espresso calculator objects.
"""

import streamlit as st


def render_calculation_setup_page():
    """
    Render the calculation setup page.

    This page configures calculation parameters and uses the calculation
    modules to prepare atoms and Espresso objects, following the modular
    design pattern where calculation modules create objects.
    """
    st.header("📊 Calculation Setup")
    st.markdown(
        """
    Configure your calculation parameters. This page uses **calculation modules**
    to prepare atoms and Espresso calculator objects following xespresso's design patterns.
    
    **Modular Design:**
    - This page configures parameters in `workflow_config`
    - Calculation modules (`gui/calculations/`) create atoms and Espresso objects
    - Job submission receives prepared objects from calculation modules
    """
    )

    # Check if structure is loaded
    if (
        "current_structure" not in st.session_state
        or st.session_state.current_structure is None
    ):
        st.warning(
            "⚠️ No structure loaded. Please load a structure first in the Structure Viewer page."
        )
        return

    atoms = st.session_state.current_structure
    st.success(
        f"✅ Structure loaded: {atoms.get_chemical_formula()} ({len(atoms)} atoms)"
    )

    st.markdown("---")

    # Initialize workflow_config if not exists
    if "workflow_config" not in st.session_state:
        st.session_state.workflow_config = {}

    config = st.session_state.workflow_config

    # Calculation Type
    st.subheader("⚙️ Calculation Type")
    calc_type = st.selectbox(
        "Calculation:",
        ["scf", "relax", "vc-relax"],
        index=["scf", "relax", "vc-relax"].index(config.get("calc_type", "scf")),
        help="Type of calculation to perform",
    )
    config["calc_type"] = calc_type

    # Basic Parameters
    st.subheader("🔧 Basic Parameters")

    col1, col2 = st.columns(2)
    with col1:
        ecutwfc = st.number_input(
            "Energy Cutoff (Ry):",
            value=float(config.get("ecutwfc", 50.0)),
            min_value=10.0,
            max_value=200.0,
            step=5.0,
            help="Plane-wave energy cutoff in Rydberg",
        )
        config["ecutwfc"] = ecutwfc

        occupations = st.selectbox(
            "Occupations:",
            ["smearing", "fixed", "tetrahedra"],
            index=["smearing", "fixed", "tetrahedra"].index(
                config.get("occupations", "smearing")
            ),
        )
        config["occupations"] = occupations

    with col2:
        ecutrho = st.number_input(
            "Charge Density Cutoff (Ry):",
            value=float(config.get("ecutrho", ecutwfc * 8)),
            min_value=40.0,
            max_value=1600.0,
            step=20.0,
            help="Charge density cutoff (typically 8-12 times ecutwfc)",
        )
        config["ecutrho"] = ecutrho

        conv_thr = st.number_input(
            "Convergence Threshold:",
            value=float(config.get("conv_thr", 1.0e-8)),
            format="%.2e",
            help="SCF convergence threshold",
        )
        config["conv_thr"] = conv_thr

    # Smearing parameters
    if occupations == "smearing":
        st.subheader("📊 Smearing Parameters")
        col1, col2 = st.columns(2)
        with col1:
            smearing = st.selectbox(
                "Smearing Type:",
                ["gaussian", "methfessel-paxton", "marzari-vanderbilt", "fermi-dirac"],
                index=[
                    "gaussian",
                    "methfessel-paxton",
                    "marzari-vanderbilt",
                    "fermi-dirac",
                ].index(config.get("smearing", "gaussian")),
            )
            config["smearing"] = smearing
        with col2:
            degauss = st.number_input(
                "Degauss (Ry):",
                value=float(config.get("degauss", 0.02)),
                min_value=0.001,
                max_value=0.1,
                step=0.005,
                format="%.4f",
            )
            config["degauss"] = degauss

    # K-points
    st.subheader("🔷 K-points")
    kpts_mode = st.radio(
        "K-points Mode:", ["Explicit Grid", "K-spacing"], horizontal=True
    )

    if kpts_mode == "Explicit Grid":
        col1, col2, col3 = st.columns(3)
        with col1:
            k1 = st.number_input(
                "k₁:", value=config.get("kpts", (4, 4, 4))[0], min_value=1, max_value=20
            )
        with col2:
            k2 = st.number_input(
                "k₂:", value=config.get("kpts", (4, 4, 4))[1], min_value=1, max_value=20
            )
        with col3:
            k3 = st.number_input(
                "k₃:", value=config.get("kpts", (4, 4, 4))[2], min_value=1, max_value=20
            )
        config["kpts"] = (int(k1), int(k2), int(k3))
        if "kspacing" in config:
            del config["kspacing"]
    else:
        kspacing = st.number_input(
            "K-spacing (Å⁻¹):",
            value=float(config.get("kspacing", 0.3)),
            min_value=0.1,
            max_value=1.0,
            step=0.05,
            help="K-point density in reciprocal space",
        )
        config["kspacing"] = kspacing
        if "kpts" in config:
            del config["kpts"]

    # Pseudopotentials
    st.subheader("🧪 Pseudopotentials")
    elements = set(atoms.get_chemical_symbols())

    if "pseudopotentials" not in config:
        config["pseudopotentials"] = {}

    for elem in sorted(elements):
        pseudo = st.text_input(
            f"Pseudopotential for {elem}:",
            value=config["pseudopotentials"].get(elem, f"{elem}.UPF"),
            key=f"pseudo_{elem}",
        )
        config["pseudopotentials"][elem] = pseudo

    st.markdown("---")

    # Machine and Code Selection
    st.subheader("🖥️ Execution Environment")
    st.info(
        """
    Select the machine and code version to run this calculation.
    The machine will be passed to Espresso via the `queue` parameter for backwards compatibility.
    """
    )

    col1, col2 = st.columns(2)

    with col1:
        # Machine Selection
        st.write("**Machine:**")
        try:
            from xespresso.machines.config.loader import (
                list_machines,
                load_machine,
                DEFAULT_CONFIG_PATH,
                DEFAULT_MACHINES_DIR,
            )

            available_machines = list_machines()

            if available_machines:
                selected_machine_name = st.selectbox(
                    "Select Machine:",
                    options=available_machines,
                    help="Machine where the calculation will run",
                    key="calc_machine_selector",
                )
                # Store selection in separate state variable for compatibility
                st.session_state.selected_machine_for_calc = selected_machine_name
                config["machine_name"] = selected_machine_name

                # Load the machine object
                try:
                    machine = load_machine(
                        DEFAULT_CONFIG_PATH,
                        selected_machine_name,
                        DEFAULT_MACHINES_DIR,
                        return_object=True,
                    )
                    st.session_state.calc_machine = machine

                    # Show machine info
                    st.caption(f"Type: {machine.execution}")
                    if machine.scheduler:
                        st.caption(f"Scheduler: {machine.scheduler}")
                except Exception as e:
                    st.warning(f"Could not load machine: {e}")
            else:
                st.warning(
                    "⚠️ No machines configured. Please configure a machine first in the Machine Configuration page."
                )
                st.session_state.selected_machine_for_calc = None
                config["machine_name"] = None
        except ImportError:
            st.error("❌ Machine configuration modules not available")
            st.session_state.selected_machine_for_calc = None
            config["machine_name"] = None

    with col2:
        # Code/Version Selection using the proper selector
        st.write("**Code Version:**")
        if st.session_state.get("selected_machine_for_calc"):
            try:
                from xespresso.codes.manager import load_codes_config, DEFAULT_CODES_DIR

                codes = load_codes_config(
                    st.session_state.selected_machine_for_calc, DEFAULT_CODES_DIR
                )

                if codes and codes.has_any_codes():
                    # Check if multiple versions are available
                    available_versions = codes.list_versions()

                    if codes.versions and len(available_versions) > 1:
                        # Multiple versions available - show version selector
                        st.info(
                            f"📦 Multiple QE versions available: {', '.join(available_versions)}"
                        )

                        # Version selector
                        default_idx = 0
                        if (
                            st.session_state.get("calc_selected_version")
                            and st.session_state.calc_selected_version
                            in available_versions
                        ):
                            default_idx = available_versions.index(
                                st.session_state.calc_selected_version
                            )

                        selected_version = st.selectbox(
                            "Select QE Version:",
                            available_versions,
                            index=default_idx,
                            key="calc_version_selector",
                            help="Choose which Quantum ESPRESSO version to use for this calculation",
                        )

                        # Store selected version
                        st.session_state.calc_selected_version = selected_version
                        config["qe_version"] = selected_version

                        # Get codes for selected version
                        version_codes = codes.get_all_codes(version=selected_version)

                        # Show version details
                        with st.expander("⚙️ Version Details", expanded=False):
                            st.write(f"**Version:** {selected_version}")
                            if codes.versions and selected_version in codes.versions:
                                version_config = codes.versions[selected_version]
                                if version_config.get("label"):
                                    st.write(f"**Label:** {version_config['label']}")
                                if version_config.get("qe_prefix"):
                                    st.write(
                                        f"**Prefix:** {version_config['qe_prefix']}"
                                    )
                            st.write(
                                f"**Available codes:** {', '.join(version_codes.keys())}"
                            )

                    else:
                        # Single version or no version structure
                        version_codes = codes.get_all_codes()
                        selected_version = codes.qe_version
                        if selected_version:
                            st.caption(f"QE Version: {selected_version}")
                            config["qe_version"] = selected_version

                    # Show available codes and allow selection
                    code_names = list(version_codes.keys())
                    if code_names:
                        st.caption(
                            f"✓ {len(code_names)} codes configured: {', '.join(code_names[:3])}{' ...' if len(code_names) > 3 else ''}"
                        )

                        # Individual code selection
                        st.markdown("**Select Code:**")
                        default_code_idx = 0
                        # Try to select 'pw' by default if available
                        if "pw" in code_names:
                            default_code_idx = code_names.index("pw")
                        elif (
                            st.session_state.get("calc_selected_code")
                            and st.session_state.calc_selected_code in code_names
                        ):
                            default_code_idx = code_names.index(
                                st.session_state.calc_selected_code
                            )

                        selected_code = st.selectbox(
                            "Choose code executable:",
                            code_names,
                            index=default_code_idx,
                            key="calc_code_selector",
                            help="Select which Quantum ESPRESSO executable to use (e.g., pw for scf/relax, ph for phonons, bands for band structure)",
                        )

                        # Store selected code
                        st.session_state.calc_selected_code = selected_code
                        config["selected_code"] = selected_code

                        # Show code details
                        selected_code_obj = version_codes[selected_code]
                        st.caption(f"📍 Path: {selected_code_obj.path}")
                        if (
                            hasattr(selected_code_obj, "version")
                            and selected_code_obj.version
                        ):
                            st.caption(f"📦 Version: {selected_code_obj.version}")

                else:
                    st.warning(
                        f"⚠️ No codes configured for machine '{st.session_state.selected_machine_for_calc}'. Please configure codes in the Codes Configuration page."
                    )
                    config["qe_version"] = None
                    config["selected_code"] = None
            except Exception as e:
                st.warning(f"Could not load codes: {e}")
                config["qe_version"] = None
        else:
            st.info("Select a machine first")
            config["qe_version"] = None
            config["selected_code"] = None

    st.markdown("---")

    # Prepare Calculation Button
    st.subheader("✨ Prepare Calculation")
    st.info(
        """
    Click below to prepare atoms and Espresso calculator objects using the **calculation module**.
    This follows the modular design where calculation modules create objects.
    """
    )

    if st.button("🔧 Prepare Calculation", type="primary"):
        try:
            from xespresso.gui.calculations import prepare_calculation_from_gui

            # Validate configuration
            if not config.get("pseudopotentials"):
                st.error("❌ Please specify pseudopotentials for all elements")
                return

            # Validate machine and code selection
            if not st.session_state.get("calc_machine"):
                st.error("❌ Please select a machine")
                return

            # Add machine to config as queue parameter
            # Convert Machine object to queue dict for compatibility
            machine = st.session_state.calc_machine
            config["queue"] = machine.to_queue() if hasattr(machine, 'to_queue') else machine

            # Set environment variable for xespresso command template
            # xespresso will replace LAUNCHER, PACKAGE, PARALLEL, PREFIX placeholders
            import os
            os.environ["ASE_ESPRESSO_COMMAND"] = "LAUNCHER PACKAGE.x PARALLEL -in PREFIX.PACKAGEi > PREFIX.PACKAGEo"
            
            # Use calculation module to prepare atoms and calculator
            st.info(
                "📦 Using calculation module to prepare atoms and Espresso calculator..."
            )
            st.info(f"   Machine: {st.session_state.selected_machine_for_calc}")
            if st.session_state.get("calc_selected_code"):
                st.info(f"   Code: {st.session_state.calc_selected_code}")

            label = "prepared_calculation"  # Temporary label, will be updated in job submission

            with st.spinner("Preparing calculation objects..."):
                prepared_atoms, calc = prepare_calculation_from_gui(
                    atoms, config, label=label
                )

            # Store prepared objects in session state
            st.session_state.espresso_calculator = calc
            st.session_state.prepared_atoms = prepared_atoms

            st.success(
                """
            ✅ **Calculation prepared successfully!**
            
            The calculation module has created:
            - ✓ Prepared atoms object
            - ✓ Espresso calculator with your configuration
            
            These objects are now stored in session state and ready for:
            - Dry run (generate input files)
            - Job submission (execute calculation)
            """
            )

            # Show summary
            with st.expander("📋 Prepared Calculation Summary"):
                st.write("**Calculator Label:**", calc.label)
                st.write("**Calculation Type:**", calc_type)
                st.write("**Energy Cutoff:**", f"{ecutwfc} Ry")
                st.write("**Charge Density Cutoff:**", f"{ecutrho} Ry")
                st.write("**Pseudopotentials:**")
                for elem, pseudo in config["pseudopotentials"].items():
                    st.text(f"  {elem}: {pseudo}")

        except Exception as e:
            st.error(f"❌ Error preparing calculation: {e}")
            import traceback

            with st.expander("Error Details"):
                st.code(traceback.format_exc())

    # Show current configuration
    with st.expander("📝 Current Configuration"):
        st.json(config)

    st.markdown("---")
    st.info(
        """
    **Next Steps:**
    1. Configure your calculation parameters above
    2. Click "Prepare Calculation" to create atoms and calculator objects
    3. Go to "Job Submission" page to generate files or run calculation
    """
    )
