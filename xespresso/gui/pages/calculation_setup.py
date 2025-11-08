"""Calculation Setup Page for xespresso GUI."""
import streamlit as st
import os

def render_calculation_setup_page():
    """
    Render the calculation setup page.
    
    This page allows users to:
    1. Configure calculation parameters
    2. Set up pseudopotentials
    3. Configure k-points, cutoffs, etc.
    4. Run calculations directly using calc.get_potential_energy()
    5. Or generate input files (dry run)
    
    The page creates an Espresso calculator instance with the configured parameters
    and an ASE Atoms object from the structure, then provides buttons to either:
    - Run the calculation directly (calls calc.get_potential_energy())
    - Generate input files for review (calls calc.write_input())
    """
    st.header("Calculation Setup")
    st.markdown("""
    Configure your calculation parameters and run calculations using xespresso.
    
    **Workflow:**
    1. Configure calculation parameters below
    2. Choose to either:
       - **Run Calculation**: Creates calculator and runs with `calc.get_potential_energy()`
       - **Generate Files (Dry Run)**: Creates calculator and generates input files with `calc.write_input()`
    """)
    
    # Check if structure is loaded
    if 'current_structure' not in st.session_state or st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first in the Structure Viewer page.")
        return
    
    atoms = st.session_state.current_structure
    st.success(f"✅ Working with: {atoms.get_chemical_formula()} ({len(atoms)} atoms)")
    
    st.markdown("---")
    
    # Create tabs for configuration and execution
    config_tab, run_tab = st.tabs(["⚙️ Configuration", "🚀 Run Calculation"])
    
    with config_tab:
        render_configuration_section()
    
    with run_tab:
        render_run_calculation_section()


def render_configuration_section():
    """Render the configuration section for calculation parameters."""
    atoms = st.session_state.current_structure
    
    # Calculation type
    st.subheader("Calculation Type")
    calc_type_display = st.selectbox(
        "Calculation Type",
        [
            "SCF (Self-Consistent Field)",
            "Relaxation (Geometry Optimization)",
            "VC-Relax (Cell + Geometry Optimization)",
            "Bands (Band Structure)",
            "DOS (Density of States)",
            "NSCF (Non-Self-Consistent)",
        ],
        index=["scf", "relax", "vc-relax", "bands", "dos", "nscf"].index(
            st.session_state.workflow_config.get('calc_type', 'scf')
        ) if st.session_state.workflow_config.get('calc_type', 'scf') in ["scf", "relax", "vc-relax", "bands", "dos", "nscf"] else 0
    )
    
    calc_type = calc_type_display.split()[0].lower()
    st.session_state.workflow_config['calc_type'] = calc_type
    
    st.markdown("---")
    
    # Pseudopotentials
    st.subheader("Pseudopotentials")
    
    unique_elements = list(set(atoms.get_chemical_symbols()))
    st.write(f"**Elements in structure:** {', '.join(unique_elements)}")
    
    pseudo_method = st.radio(
        "Pseudopotential Selection:",
        ["Manual Entry", "Load Configuration"],
        key="pseudo_method"
    )
    
    pseudopotentials = {}
    
    if pseudo_method == "Manual Entry":
        st.write("Enter pseudopotential file for each element:")
        for element in unique_elements:
            default_pseudo = st.session_state.workflow_config.get('pseudopotentials', {}).get(
                element, f"{element}.pbe-n-kjpaw_psl.1.0.0.UPF"
            )
            pseudo = st.text_input(
                f"{element}",
                value=default_pseudo,
                key=f"pseudo_{element}"
            )
            pseudopotentials[element] = pseudo
    else:
        try:
            from xespresso.utils import list_pseudo_configs, load_pseudo_config
            configs = list_pseudo_configs()
            
            if configs:
                selected_config = st.selectbox(
                    "Select Configuration:",
                    configs,
                    key="pseudo_config_selector"
                )
                
                if st.button("Load Configuration", key="load_pseudo_config"):
                    config = load_pseudo_config(selected_config)
                    pseudopotentials = config.get('pseudopotentials', {})
                    st.session_state.workflow_config['pseudopotentials'] = pseudopotentials
                    st.success(f"✅ Loaded pseudopotentials from {selected_config}")
                    st.json(pseudopotentials)
                else:
                    # Use previously loaded or default
                    pseudopotentials = st.session_state.workflow_config.get('pseudopotentials', {})
            else:
                st.warning("No saved pseudopotential configurations found.")
                # Fall back to manual entry
                for element in unique_elements:
                    default_pseudo = f"{element}.pbe-n-kjpaw_psl.1.0.0.UPF"
                    pseudopotentials[element] = default_pseudo
        except Exception as e:
            st.error(f"Error loading configurations: {e}")
            # Fall back to manual entry
            for element in unique_elements:
                default_pseudo = f"{element}.pbe-n-kjpaw_psl.1.0.0.UPF"
                pseudopotentials[element] = default_pseudo
    
    st.session_state.workflow_config['pseudopotentials'] = pseudopotentials
    
    st.markdown("---")
    
    # Basic parameters
    st.subheader("Calculation Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ecutwfc = st.number_input(
            "Kinetic Energy Cutoff (ecutwfc) [Ry]",
            min_value=10.0,
            max_value=200.0,
            value=float(st.session_state.workflow_config.get('ecutwfc', 50.0)),
            step=5.0,
            help="Plane-wave cutoff energy",
            key="ecutwfc_input"
        )
        
        dual = st.number_input(
            "Dual Parameter (ecutrho/ecutwfc ratio)",
            min_value=1.0,
            max_value=12.0,
            value=float(st.session_state.workflow_config.get('dual', 4.0)),
            step=0.5,
            help="Ratio between charge density and wavefunction cutoffs (typically 4-8)",
            key="dual_input"
        )
        
        if calc_type in ["scf", "relax", "vc-relax"]:
            conv_thr = st.number_input(
                "Convergence Threshold",
                min_value=1e-10,
                max_value=1e-4,
                value=float(st.session_state.workflow_config.get('conv_thr', 1e-6)),
                format="%.1e",
                help="SCF convergence threshold",
                key="conv_thr_input"
            )
            st.session_state.workflow_config['conv_thr'] = conv_thr
    
    with col2:
        ecutrho = ecutwfc * dual
        st.number_input(
            "Charge Density Cutoff (ecutrho) [Ry]",
            min_value=10.0,
            max_value=800.0,
            value=ecutrho,
            step=10.0,
            help="Charge density cutoff = dual × ecutwfc",
            disabled=True,
            key="ecutrho_display"
        )
    
    st.session_state.workflow_config.update({
        'ecutwfc': ecutwfc,
        'ecutrho': ecutrho,
        'dual': dual,
    })
    
    st.markdown("---")
    
    # Electronic Occupations
    st.subheader("Electronic Occupations")
    
    col1, col2 = st.columns(2)
    with col1:
        occupations = st.selectbox(
            "Occupation Type",
            ["smearing", "fixed", "tetrahedra"],
            index=["smearing", "fixed", "tetrahedra"].index(
                st.session_state.workflow_config.get('occupations', 'smearing')
            ),
            help="Method for determining electronic occupations",
            key="occupations_input"
        )
        st.session_state.workflow_config['occupations'] = occupations
    
    with col2:
        if occupations == "smearing":
            smearing_type = st.selectbox(
                "Smearing Type",
                ["gaussian", "methfessel-paxton", "marzari-vanderbilt", "fermi-dirac"],
                index=["gaussian", "methfessel-paxton", "marzari-vanderbilt", "fermi-dirac"].index(
                    st.session_state.workflow_config.get('smearing', 'gaussian')
                ),
                help="Type of smearing function",
                key="smearing_type_input"
            )
            st.session_state.workflow_config['smearing'] = smearing_type
            
            degauss = st.number_input(
                "Smearing Width (degauss) [Ry]",
                min_value=0.001,
                max_value=0.1,
                value=st.session_state.workflow_config.get('degauss', 0.02),
                step=0.001,
                format="%.3f",
                help="Width of smearing (typically 0.01-0.03 Ry)",
                key="degauss_input"
            )
            st.session_state.workflow_config['degauss'] = degauss
    
    st.markdown("---")
    
    # K-points
    st.subheader("K-point Sampling")
    
    kpt_method = st.radio(
        "K-point Method:",
        ["K-spacing", "Monkhorst-Pack Grid"],
        key="kpt_method"
    )
    
    if kpt_method == "K-spacing":
        kspacing = st.slider(
            "K-spacing (Å⁻¹)",
            min_value=0.1,
            max_value=1.0,
            value=st.session_state.workflow_config.get('kspacing', 0.3),
            step=0.05,
            help="Smaller values = denser k-point mesh",
            key="kspacing_input"
        )
        st.session_state.workflow_config['kspacing'] = kspacing
        
        # Remove kpts if kspacing is used
        if 'kpts' in st.session_state.workflow_config:
            del st.session_state.workflow_config['kpts']
    else:
        col1, col2, col3 = st.columns(3)
        default_kpts = st.session_state.workflow_config.get('kpts', (4, 4, 4))
        with col1:
            k1 = st.number_input("k₁", min_value=1, value=int(default_kpts[0]), key="k1_input")
        with col2:
            k2 = st.number_input("k₂", min_value=1, value=int(default_kpts[1]), key="k2_input")
        with col3:
            k3 = st.number_input("k₃", min_value=1, value=int(default_kpts[2]), key="k3_input")
        
        st.session_state.workflow_config['kpts'] = (k1, k2, k3)
        
        # Remove kspacing if kpts is used
        if 'kspacing' in st.session_state.workflow_config:
            del st.session_state.workflow_config['kspacing']
    
    st.markdown("---")
    
    # Spin polarization
    st.subheader("Spin Polarization")
    nspin = st.selectbox(
        "Spin Treatment",
        [1, 2, 4],
        index=[1, 2, 4].index(st.session_state.workflow_config.get('nspin', 1)),
        format_func=lambda x: {
            1: "Non-spin-polarized",
            2: "Spin-polarized (collinear)",
            4: "Non-collinear + spin-orbit"
        }[x],
        help="Spin treatment for magnetic systems",
        key="nspin_input"
    )
    st.session_state.workflow_config['nspin'] = nspin
    
    st.success("✅ Configuration saved! Go to the 'Run Calculation' tab to execute.")


def render_run_calculation_section():
    """Render the run calculation section with buttons for running or generating files."""
    # Check if configuration is complete
    if 'workflow_config' not in st.session_state or not st.session_state.workflow_config.get('pseudopotentials'):
        st.warning("⚠️ Please configure your calculation first in the Configuration tab.")
        return
    
    atoms = st.session_state.current_structure
    config = st.session_state.workflow_config
    
    st.subheader("Run Calculation")
    st.markdown("""
    You can either:
    1. **Run Calculation**: Creates Espresso calculator and runs with `calc.get_potential_energy()`
    2. **Generate Files (Dry Run)**: Creates calculator and generates input files with `calc.write_input()`
    """)
    
    # Show configuration summary
    with st.expander("📋 Configuration Summary", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Calculation Type", config.get('calc_type', 'scf').upper())
            st.metric("Energy Cutoff", f"{config.get('ecutwfc', 50)} Ry")
            if 'kspacing' in config:
                st.metric("K-spacing", f"{config.get('kspacing')} Å⁻¹")
            elif 'kpts' in config:
                kpts = config.get('kpts')
                st.metric("K-points", f"{kpts[0]}×{kpts[1]}×{kpts[2]}")
        
        with col2:
            st.write("**Pseudopotentials:**")
            for elem, pseudo in config.get('pseudopotentials', {}).items():
                st.text(f"  {elem}: {pseudo}")
    
    st.markdown("---")
    
    # Working directory for output
    st.subheader("📁 Working Directory")
    
    try:
        from xespresso.gui.utils.selectors import render_workdir_browser
        workdir = render_workdir_browser(key="calc_workdir")
    except ImportError:
        workdir = st.text_input(
            "Working Directory:", 
            value=os.path.join(os.getcwd(), "calculations"),
            key="calc_workdir_input"
        )
        workdir = os.path.abspath(os.path.expanduser(workdir))
    
    # Validate workdir
    try:
        workdir = os.path.realpath(workdir)
        safe_bases = [os.path.realpath(os.path.expanduser("~")), os.path.realpath("/tmp")]
        is_safe = any(workdir.startswith(base) for base in safe_bases)
        
        if not is_safe:
            st.warning("⚠️ For security, only directories under your home directory or /tmp are allowed")
            return
    except (OSError, ValueError) as e:
        st.error(f"❌ Invalid directory path: {e}")
        return
    
    # Label for this calculation
    label = st.text_input(
        "Calculation Label:",
        value=f"{config.get('calc_type', 'scf')}/{atoms.get_chemical_formula()}",
        help="Label for this calculation",
        key="calc_label_input"
    )
    
    full_path = os.path.join(workdir, label)
    
    # Validate full path
    try:
        full_path = os.path.realpath(full_path)
        if not full_path.startswith(workdir):
            st.error("❌ Invalid calculation label - path traversal detected")
            return
    except (OSError, ValueError) as e:
        st.error(f"❌ Invalid path: {e}")
        return
    
    st.info(f"📍 Calculation will run in: `{full_path}`")
    
    st.markdown("---")
    
    # Buttons for running or generating files
    st.subheader("🚀 Execute")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Run Calculation", type="primary", key="run_calc_button", use_container_width=True):
            run_calculation(atoms, config, label)
    
    with col2:
        if st.button("🧪 Generate Files (Dry Run)", key="dry_run_button", use_container_width=True):
            generate_input_files(atoms, config, label)


def run_calculation(atoms, config, label):
    """
    Run a calculation using xespresso.
    
    This function:
    1. Creates an Espresso calculator with the configured parameters
    2. Sets the calculator on the atoms object
    3. Calls atoms.get_potential_energy() to run the calculation
    
    Args:
        atoms: ASE Atoms object
        config: Configuration dictionary with calculation parameters
        label: Label for the calculation (directory/prefix)
    """
    try:
        from xespresso import Espresso
        
        st.info("🔧 Creating Espresso calculator with configured parameters...")
        
        # Build input_data dictionary for Espresso
        input_data = {
            'CONTROL': {},
            'SYSTEM': {},
            'ELECTRONS': {}
        }
        
        # Set calculation type
        calc_type = config.get('calc_type', 'scf')
        input_data['CONTROL']['calculation'] = calc_type
        
        # Set convergence threshold
        if 'conv_thr' in config:
            input_data['ELECTRONS']['conv_thr'] = config['conv_thr']
        
        # Build calculator parameters
        calc_params = {
            'pseudopotentials': config.get('pseudopotentials', {}),
            'label': label,
            'ecutwfc': config.get('ecutwfc', 50),
            'ecutrho': config.get('ecutrho', 200),
            'occupations': config.get('occupations', 'smearing'),
            'input_data': input_data,
        }
        
        # Add k-points or k-spacing
        if 'kspacing' in config:
            calc_params['kspacing'] = config['kspacing']
        elif 'kpts' in config:
            calc_params['kpts'] = config['kpts']
        else:
            calc_params['kpts'] = (4, 4, 4)
        
        # Add smearing parameters
        if config.get('occupations') == 'smearing':
            calc_params['smearing'] = config.get('smearing', 'gaussian')
            calc_params['degauss'] = config.get('degauss', 0.02)
        
        # Add spin polarization
        if config.get('nspin', 1) != 1:
            input_data['SYSTEM']['nspin'] = config['nspin']
        
        st.info("📝 Calculator parameters:")
        st.json(calc_params)
        
        # Create the calculator
        calc = Espresso(**calc_params)
        
        # Set calculator on atoms
        atoms.calc = calc
        
        st.info("🚀 Running calculation with calc.get_potential_energy()...")
        st.info("This will automatically generate input files and run the calculation.")
        
        with st.spinner("Running calculation... This may take a while."):
            # Run the calculation by calling get_potential_energy()
            energy = atoms.get_potential_energy()
        
        # Display results
        st.success("✅ Calculation completed successfully!")
        st.subheader("📊 Results")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Energy", f"{energy:.6f} eV")
        with col2:
            st.metric("Structure", atoms.get_chemical_formula())
        
        # Show additional information
        with st.expander("📁 Output Files"):
            calc_dir = calc.directory
            st.info(f"Calculation directory: `{calc_dir}`")
            
            if os.path.exists(calc_dir):
                files = os.listdir(calc_dir)
                st.write("**Files generated:**")
                for f in files:
                    st.text(f"  - {f}")
        
        # Store results in session state
        if 'calculation_results' not in st.session_state:
            st.session_state.calculation_results = []
        
        st.session_state.calculation_results.append({
            'label': label,
            'energy': energy,
            'formula': atoms.get_chemical_formula(),
            'calc_type': config.get('calc_type', 'scf')
        })
        
    except Exception as e:
        st.error(f"❌ Calculation failed: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


def generate_input_files(atoms, config, label):
    """
    Generate input files without running the calculation.
    
    This function:
    1. Creates an Espresso calculator with the configured parameters
    2. Calls calc.write_input(atoms) to generate input files
    
    Args:
        atoms: ASE Atoms object
        config: Configuration dictionary with calculation parameters
        label: Label for the calculation (directory/prefix)
    """
    try:
        from xespresso import Espresso
        
        st.info("🔧 Creating Espresso calculator with configured parameters...")
        
        # Build input_data dictionary for Espresso
        input_data = {
            'CONTROL': {},
            'SYSTEM': {},
            'ELECTRONS': {}
        }
        
        # Set calculation type
        calc_type = config.get('calc_type', 'scf')
        input_data['CONTROL']['calculation'] = calc_type
        
        # Set convergence threshold
        if 'conv_thr' in config:
            input_data['ELECTRONS']['conv_thr'] = config['conv_thr']
        
        # Build calculator parameters
        calc_params = {
            'pseudopotentials': config.get('pseudopotentials', {}),
            'label': label,
            'ecutwfc': config.get('ecutwfc', 50),
            'ecutrho': config.get('ecutrho', 200),
            'occupations': config.get('occupations', 'smearing'),
            'input_data': input_data,
        }
        
        # Add k-points or k-spacing
        if 'kspacing' in config:
            calc_params['kspacing'] = config['kspacing']
        elif 'kpts' in config:
            calc_params['kpts'] = config['kpts']
        else:
            calc_params['kpts'] = (4, 4, 4)
        
        # Add smearing parameters
        if config.get('occupations') == 'smearing':
            calc_params['smearing'] = config.get('smearing', 'gaussian')
            calc_params['degauss'] = config.get('degauss', 0.02)
        
        # Add spin polarization
        if config.get('nspin', 1) != 1:
            input_data['SYSTEM']['nspin'] = config['nspin']
        
        # Create the calculator
        calc = Espresso(**calc_params)
        
        st.info("📝 Generating input files with calc.write_input(atoms)...")
        
        with st.spinner("Generating files..."):
            # Generate input files
            calc.write_input(atoms)
        
        # Display results
        st.success("✅ Input files generated successfully!")
        
        calc_dir = calc.directory
        st.info(f"📁 Files generated in: `{calc_dir}`")
        
        if os.path.exists(calc_dir):
            files = os.listdir(calc_dir)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Files created:**")
                for f in files:
                    st.markdown(f"- ✅ {f}")
            
            with col2:
                st.write("**Location:**")
                st.code(calc_dir)
            
            # Preview input file
            input_file = f"{calc.prefix}.pwi"
            input_file_path = os.path.join(calc_dir, input_file)
            
            if os.path.exists(input_file_path):
                st.subheader("👁️ Input File Preview")
                with open(input_file_path, 'r') as f:
                    input_content = f.read()
                
                with st.expander("View Input File", expanded=True):
                    st.code(input_content, language='fortran', line_numbers=True)
                    
                    st.download_button(
                        label="⬇️ Download Input File",
                        data=input_content,
                        file_name=input_file,
                        mime="text/plain"
                    )
        
        st.markdown("---")
        st.info("""
        **Next Steps:**
        
        1. **Review the generated files** in the file browser
        2. **Edit if needed** before running
        3. **Run the calculation** using the 'Job Submission & Files' page
        
        Or you can run the calculation directly by clicking the 'Run Calculation' button above!
        """)
        
    except Exception as e:
        st.error(f"❌ File generation failed: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
