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
    st.markdown("""
    Configure your calculation parameters. This page uses **calculation modules**
    to prepare atoms and Espresso calculator objects following xespresso's design patterns.
    
    **Modular Design:**
    - This page configures parameters in `workflow_config`
    - Calculation modules (`gui/calculations/`) create atoms and Espresso objects
    - Job submission receives prepared objects from calculation modules
    """)
    
    # Check if structure is loaded
    if 'current_structure' not in st.session_state or st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first in the Structure Viewer page.")
        return
    
    atoms = st.session_state.current_structure
    st.success(f"✅ Structure loaded: {atoms.get_chemical_formula()} ({len(atoms)} atoms)")
    
    st.markdown("---")
    
    # Initialize workflow_config if not exists
    if 'workflow_config' not in st.session_state:
        st.session_state.workflow_config = {}
    
    config = st.session_state.workflow_config
    
    # Calculation Type
    st.subheader("⚙️ Calculation Type")
    calc_type = st.selectbox(
        "Calculation:",
        ['scf', 'relax', 'vc-relax'],
        index=['scf', 'relax', 'vc-relax'].index(config.get('calc_type', 'scf')),
        help="Type of calculation to perform"
    )
    config['calc_type'] = calc_type
    
    # Basic Parameters
    st.subheader("🔧 Basic Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        ecutwfc = st.number_input(
            "Energy Cutoff (Ry):",
            value=float(config.get('ecutwfc', 50.0)),
            min_value=10.0,
            max_value=200.0,
            step=5.0,
            help="Plane-wave energy cutoff in Rydberg"
        )
        config['ecutwfc'] = ecutwfc
        
        occupations = st.selectbox(
            "Occupations:",
            ['smearing', 'fixed', 'tetrahedra'],
            index=['smearing', 'fixed', 'tetrahedra'].index(config.get('occupations', 'smearing'))
        )
        config['occupations'] = occupations
    
    with col2:
        ecutrho = st.number_input(
            "Charge Density Cutoff (Ry):",
            value=float(config.get('ecutrho', ecutwfc * 8)),
            min_value=40.0,
            max_value=1600.0,
            step=20.0,
            help="Charge density cutoff (typically 8-12 times ecutwfc)"
        )
        config['ecutrho'] = ecutrho
        
        conv_thr = st.number_input(
            "Convergence Threshold:",
            value=float(config.get('conv_thr', 1.0e-8)),
            format="%.2e",
            help="SCF convergence threshold"
        )
        config['conv_thr'] = conv_thr
    
    # Smearing parameters
    if occupations == 'smearing':
        st.subheader("📊 Smearing Parameters")
        col1, col2 = st.columns(2)
        with col1:
            smearing = st.selectbox(
                "Smearing Type:",
                ['gaussian', 'methfessel-paxton', 'marzari-vanderbilt', 'fermi-dirac'],
                index=['gaussian', 'methfessel-paxton', 'marzari-vanderbilt', 'fermi-dirac'].index(
                    config.get('smearing', 'gaussian')
                )
            )
            config['smearing'] = smearing
        with col2:
            degauss = st.number_input(
                "Degauss (Ry):",
                value=float(config.get('degauss', 0.02)),
                min_value=0.001,
                max_value=0.1,
                step=0.005,
                format="%.4f"
            )
            config['degauss'] = degauss
    
    # K-points
    st.subheader("🔷 K-points")
    kpts_mode = st.radio(
        "K-points Mode:",
        ['Explicit Grid', 'K-spacing'],
        horizontal=True
    )
    
    if kpts_mode == 'Explicit Grid':
        col1, col2, col3 = st.columns(3)
        with col1:
            k1 = st.number_input("k₁:", value=config.get('kpts', (4, 4, 4))[0], min_value=1, max_value=20)
        with col2:
            k2 = st.number_input("k₂:", value=config.get('kpts', (4, 4, 4))[1], min_value=1, max_value=20)
        with col3:
            k3 = st.number_input("k₃:", value=config.get('kpts', (4, 4, 4))[2], min_value=1, max_value=20)
        config['kpts'] = (int(k1), int(k2), int(k3))
        if 'kspacing' in config:
            del config['kspacing']
    else:
        kspacing = st.number_input(
            "K-spacing (Å⁻¹):",
            value=float(config.get('kspacing', 0.3)),
            min_value=0.1,
            max_value=1.0,
            step=0.05,
            help="K-point density in reciprocal space"
        )
        config['kspacing'] = kspacing
        if 'kpts' in config:
            del config['kpts']
    
    # Pseudopotentials
    st.subheader("🧪 Pseudopotentials")
    elements = set(atoms.get_chemical_symbols())
    
    if 'pseudopotentials' not in config:
        config['pseudopotentials'] = {}
    
    for elem in sorted(elements):
        pseudo = st.text_input(
            f"Pseudopotential for {elem}:",
            value=config['pseudopotentials'].get(elem, f"{elem}.UPF"),
            key=f"pseudo_{elem}"
        )
        config['pseudopotentials'][elem] = pseudo
    
    st.markdown("---")
    
    # Machine and Code Selection
    st.subheader("🖥️ Execution Environment")
    st.info("""
    Select the machine and code version to run this calculation.
    The machine will be passed to Espresso via the `queue` parameter for backwards compatibility.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Machine Selection
        st.write("**Machine:**")
        try:
            from xespresso.machines.config.loader import (
                list_machines, load_machine,
                DEFAULT_CONFIG_PATH, DEFAULT_MACHINES_DIR
            )
            available_machines = list_machines()
            
            if available_machines:
                selected_machine_name = st.selectbox(
                    "Select Machine:",
                    options=available_machines,
                    help="Machine where the calculation will run",
                    key="calc_machine_selector"
                )
                # Store selection in separate state variable for compatibility
                st.session_state.selected_machine_for_calc = selected_machine_name
                config['machine_name'] = selected_machine_name
                
                # Load the machine object
                try:
                    machine = load_machine(
                        DEFAULT_CONFIG_PATH,
                        selected_machine_name,
                        DEFAULT_MACHINES_DIR,
                        return_object=True
                    )
                    st.session_state.calc_machine = machine
                    
                    # Show machine info
                    st.caption(f"Type: {machine.execution}")
                    if machine.scheduler:
                        st.caption(f"Scheduler: {machine.scheduler}")
                except Exception as e:
                    st.warning(f"Could not load machine: {e}")
            else:
                st.warning("⚠️ No machines configured. Please configure a machine first in the Machine Configuration page.")
                st.session_state.selected_machine_for_calc = None
                config['machine_name'] = None
        except ImportError:
            st.error("❌ Machine configuration modules not available")
            st.session_state.selected_machine_for_calc = None
            config['machine_name'] = None
    
    with col2:
        # Code Version Selection
        st.write("**Code Version:**")
        if st.session_state.get('selected_machine_for_calc'):
            try:
                from xespresso.codes.manager import load_codes_config
                codes = load_codes_config(st.session_state.selected_machine_for_calc)
                
                if codes and codes.codes:
                    code_options = list(codes.codes.keys())
                    selected_code = st.selectbox(
                        "Select Code:",
                        options=code_options,
                        help="Quantum ESPRESSO code version to use",
                        key="calc_code_selector"
                    )
                    # Store selection in separate state variable for compatibility
                    st.session_state.selected_code_for_calc = selected_code
                    config['code_name'] = selected_code
                    
                    # Show code info
                    code_obj = codes.codes[selected_code]
                    st.caption(f"Version: {code_obj.version or 'Unknown'}")
                    if hasattr(code_obj, 'modules') and code_obj.modules:
                        st.caption(f"Modules: {', '.join(code_obj.modules[:2])}{'...' if len(code_obj.modules) > 2 else ''}")
                else:
                    st.warning(f"⚠️ No codes configured for machine '{st.session_state.selected_machine_for_calc}'. Please configure codes in the Codes Configuration page.")
                    st.session_state.selected_code_for_calc = None
                    config['code_name'] = None
            except Exception as e:
                st.warning(f"Could not load codes: {e}")
                st.session_state.selected_code_for_calc = None
                config['code_name'] = None
        else:
            st.info("Select a machine first")
            st.session_state.selected_code_for_calc = None
            config['code_name'] = None
    
    st.markdown("---")
    
    # Prepare Calculation Button
    st.subheader("✨ Prepare Calculation")
    st.info("""
    Click below to prepare atoms and Espresso calculator objects using the **calculation module**.
    This follows the modular design where calculation modules create objects.
    """)
    
    if st.button("🔧 Prepare Calculation", type="primary"):
        try:
            from xespresso.gui.calculations import prepare_calculation_from_gui
            
            # Validate configuration
            if not config.get('pseudopotentials'):
                st.error("❌ Please specify pseudopotentials for all elements")
                return
            
            # Validate machine and code selection
            if not st.session_state.get('calc_machine'):
                st.error("❌ Please select a machine")
                return
            
            # Add machine to config as queue parameter (for backwards compatibility)
            config['queue'] = st.session_state.calc_machine
            
            # Use calculation module to prepare atoms and calculator
            st.info("📦 Using calculation module to prepare atoms and Espresso calculator...")
            st.info(f"   Machine: {st.session_state.selected_machine_for_calc}")
            if st.session_state.get('selected_code_for_calc'):
                st.info(f"   Code: {st.session_state.selected_code_for_calc}")
            
            label = "prepared_calculation"  # Temporary label, will be updated in job submission
            
            with st.spinner("Preparing calculation objects..."):
                prepared_atoms, calc = prepare_calculation_from_gui(atoms, config, label=label)
            
            # Store prepared objects in session state
            st.session_state.espresso_calculator = calc
            st.session_state.prepared_atoms = prepared_atoms
            
            st.success("""
            ✅ **Calculation prepared successfully!**
            
            The calculation module has created:
            - ✓ Prepared atoms object
            - ✓ Espresso calculator with your configuration
            
            These objects are now stored in session state and ready for:
            - Dry run (generate input files)
            - Job submission (execute calculation)
            """)
            
            # Show summary
            with st.expander("📋 Prepared Calculation Summary"):
                st.write("**Calculator Label:**", calc.label)
                st.write("**Calculation Type:**", calc_type)
                st.write("**Energy Cutoff:**", f"{ecutwfc} Ry")
                st.write("**Charge Density Cutoff:**", f"{ecutrho} Ry")
                st.write("**Pseudopotentials:**")
                for elem, pseudo in config['pseudopotentials'].items():
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
    st.info("""
    **Next Steps:**
    1. Configure your calculation parameters above
    2. Click "Prepare Calculation" to create atoms and calculator objects
    3. Go to "Job Submission" page to generate files or run calculation
    """)

