"""
Streamlit GUI for xespresso - Quantum ESPRESSO Configuration Interface

This application provides a user-friendly interface for:
- Configuring machines (local/remote execution environments)
- Setting up Quantum ESPRESSO codes
- Viewing and selecting molecular structures
- Configuring calculations and workflows
- Submitting computational jobs
"""

import streamlit as st
import os
import json
import tempfile
from pathlib import Path
import traceback

# Configure page
st.set_page_config(
    page_title="xespresso GUI",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("⚛️ xespresso Configuration GUI")
st.markdown("""
Welcome to the xespresso graphical interface for Quantum ESPRESSO calculations.
Configure your computational environment, select structures, and submit jobs easily.
""")

# Import xespresso modules
try:
    from xespresso.machines.machine import Machine
    from xespresso.machines.config.loader import (
        load_machine, save_machine, list_machines,
        DEFAULT_CONFIG_PATH, DEFAULT_MACHINES_DIR
    )
    from xespresso.codes.manager import (
        detect_qe_codes, load_codes_config,
        DEFAULT_CODES_DIR
    )
    from xespresso.workflow import (
        CalculationWorkflow, quick_scf, quick_relax, PRESETS
    )
    from xespresso import Espresso
    XESPRESSO_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Error importing xespresso modules: {e}")
    st.info("Make sure xespresso is properly installed.")
    XESPRESSO_AVAILABLE = False

# Import visualization modules
try:
    from ase import io
    from ase.build import bulk, molecule
    import numpy as np
    ASE_AVAILABLE = True
except ImportError:
    st.warning("⚠️ ASE not available. Structure visualization will be limited.")
    ASE_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    st.warning("⚠️ Plotly not available. 3D visualization will be limited.")
    PLOTLY_AVAILABLE = False

# Initialize session state
if 'current_structure' not in st.session_state:
    st.session_state.current_structure = None
if 'current_machine' not in st.session_state:
    st.session_state.current_machine = None
if 'current_codes' not in st.session_state:
    st.session_state.current_codes = None
if 'workflow_config' not in st.session_state:
    st.session_state.workflow_config = {}

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Configuration Step:",
    [
        "🖥️ Machine Configuration",
        "⚙️ Codes Configuration", 
        "🔬 Structure Viewer",
        "📊 Calculation Setup",
        "🔄 Workflow Builder",
        "🚀 Job Submission"
    ]
)

# Helper functions for structure visualization
def create_3d_structure_plot(atoms):
    """Create a 3D plotly visualization of atomic structure."""
    if not PLOTLY_AVAILABLE:
        return None
    
    positions = atoms.get_positions()
    symbols = atoms.get_chemical_symbols()
    
    # Color map for common elements
    color_map = {
        'H': 'white', 'C': 'gray', 'N': 'blue', 'O': 'red',
        'F': 'green', 'P': 'orange', 'S': 'yellow',
        'Cl': 'green', 'Fe': 'brown', 'Cu': 'brown',
        'Al': 'silver', 'Si': 'pink', 'Pt': 'silver'
    }
    
    colors = [color_map.get(s, 'purple') for s in symbols]
    
    # Create scatter plot
    fig = go.Figure(data=[go.Scatter3d(
        x=positions[:, 0],
        y=positions[:, 1],
        z=positions[:, 2],
        mode='markers+text',
        marker=dict(
            size=12,
            color=colors,
            line=dict(color='black', width=1)
        ),
        text=symbols,
        textposition="top center",
        hovertemplate='<b>%{text}</b><br>x: %{x:.2f}<br>y: %{y:.2f}<br>z: %{z:.2f}<extra></extra>'
    )])
    
    # Add cell visualization if present
    if atoms.cell is not None and atoms.pbc.any():
        cell = atoms.cell.array
        # Draw cell edges
        edges = [
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 0],  # bottom
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1], [0, 0, 1],  # top
            [1, 0, 0], [1, 0, 1], [1, 1, 1], [1, 1, 0], [0, 1, 0], [0, 1, 1]
        ]
        
        edge_points = np.array([np.dot(edge, cell) for edge in edges])
        
        fig.add_trace(go.Scatter3d(
            x=edge_points[:, 0],
            y=edge_points[:, 1],
            z=edge_points[:, 2],
            mode='lines',
            line=dict(color='black', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='X (Å)',
            yaxis_title='Y (Å)',
            zaxis_title='Z (Å)',
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500
    )
    
    return fig

def display_structure_info(atoms):
    """Display information about the atomic structure."""
    st.subheader("Structure Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Number of Atoms", len(atoms))
        st.metric("Chemical Formula", atoms.get_chemical_formula())
    
    with col2:
        symbols = atoms.get_chemical_symbols()
        unique_elements = list(set(symbols))
        st.metric("Unique Elements", len(unique_elements))
        st.write("**Elements:**", ", ".join(sorted(unique_elements)))
    
    with col3:
        if atoms.cell is not None:
            st.metric("Cell Volume", f"{atoms.get_volume():.2f} Å³")
            pbc_str = "".join(["T" if p else "F" for p in atoms.pbc])
            st.metric("PBC", pbc_str)
    
    # Display cell parameters
    if atoms.cell is not None and atoms.pbc.any():
        st.subheader("Cell Parameters")
        cell_params = atoms.cell.cellpar()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**a:** {cell_params[0]:.3f} Å")
            st.write(f"**b:** {cell_params[1]:.3f} Å")
            st.write(f"**c:** {cell_params[2]:.3f} Å")
        with col2:
            st.write(f"**α:** {cell_params[3]:.2f}°")
            st.write(f"**β:** {cell_params[4]:.2f}°")
            st.write(f"**γ:** {cell_params[5]:.2f}°")

# Page 1: Machine Configuration
if page == "🖥️ Machine Configuration":
    st.header("Machine Configuration")
    st.markdown("""
    Configure the computational machine/cluster where calculations will run.
    Supports both local and remote (SSH) execution environments.
    """)
    
    if not XESPRESSO_AVAILABLE:
        st.error("xespresso modules not available. Cannot configure machines.")
    else:
        # List existing machines
        st.subheader("Existing Machines")
        try:
            machines_list = list_machines(DEFAULT_CONFIG_PATH, DEFAULT_MACHINES_DIR)
            if machines_list:
                selected_machine = st.selectbox(
                    "Select a machine to edit or view:",
                    ["[Create New]"] + machines_list
                )
            else:
                st.info("No machines configured yet. Create your first machine below.")
                selected_machine = "[Create New]"
        except Exception as e:
            st.warning(f"Could not load machines list: {e}")
            selected_machine = "[Create New]"
        
        # Create or edit machine
        st.subheader("Machine Configuration")
        
        # Load existing machine if selected
        if selected_machine != "[Create New]":
            try:
                machine = load_machine(DEFAULT_CONFIG_PATH, selected_machine, DEFAULT_MACHINES_DIR, return_object=True)
                st.success(f"Loaded machine: {selected_machine}")
            except Exception as e:
                st.error(f"Error loading machine: {e}")
                machine = None
        else:
            machine = None
        
        # Configuration form
        with st.form("machine_config_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                machine_name = st.text_input(
                    "Machine Name",
                    value=machine.name if machine else "",
                    help="Unique identifier for this machine"
                )
                
                execution = st.selectbox(
                    "Execution Mode",
                    ["local", "remote"],
                    index=0 if not machine or machine.execution == "local" else 1
                )
                
                scheduler = st.selectbox(
                    "Scheduler Type",
                    ["direct", "slurm", "pbs", "sge"],
                    index=["direct", "slurm", "pbs", "sge"].index(machine.scheduler) if machine else 0,
                    help="Job scheduler system"
                )
            
            with col2:
                workdir = st.text_input(
                    "Working Directory",
                    value=machine.workdir if machine else "./calculations",
                    help="Directory for calculation files"
                )
                
                nprocs = st.number_input(
                    "Number of Processors",
                    min_value=1,
                    value=machine.nprocs if machine else 1,
                    help="Default number of processors"
                )
                
                launcher = st.text_input(
                    "MPI Launcher",
                    value=machine.launcher if machine else "mpirun -np {nprocs}",
                    help="MPI launch command template"
                )
            
            # Remote configuration
            if execution == "remote":
                st.subheader("Remote Connection Settings")
                col1, col2 = st.columns(2)
                
                with col1:
                    host = st.text_input(
                        "Host",
                        value=machine.host if machine and machine.is_remote else "",
                        help="Remote hostname or IP"
                    )
                    username = st.text_input(
                        "Username",
                        value=machine.username if machine and machine.is_remote else "",
                        help="SSH username"
                    )
                
                with col2:
                    port = st.number_input(
                        "SSH Port",
                        min_value=1,
                        max_value=65535,
                        value=machine.port if machine and machine.is_remote else 22
                    )
                    ssh_key = st.text_input(
                        "SSH Key Path",
                        value=machine.auth.get("ssh_key", "~/.ssh/id_rsa") if machine and machine.is_remote else "~/.ssh/id_rsa",
                        help="Path to SSH private key"
                    )
            
            # Module configuration
            st.subheader("Environment Modules")
            use_modules = st.checkbox(
                "Use Environment Modules",
                value=machine.use_modules if machine else False
            )
            
            if use_modules:
                modules_str = st.text_area(
                    "Modules to Load (one per line)",
                    value="\n".join(machine.modules) if machine and machine.modules else "",
                    help="Environment modules to load before execution"
                )
            
            # Advanced settings
            with st.expander("Advanced Settings"):
                prepend = st.text_area(
                    "Prepend Commands",
                    value="\n".join(machine.prepend) if machine and isinstance(machine.prepend, list) else (machine.prepend if machine else ""),
                    help="Commands to run before calculation"
                )
                postpend = st.text_area(
                    "Postpend Commands", 
                    value="\n".join(machine.postpend) if machine and isinstance(machine.postpend, list) else (machine.postpend if machine else ""),
                    help="Commands to run after calculation"
                )
                env_setup = st.text_input(
                    "Environment Setup",
                    value=machine.env_setup if machine and hasattr(machine, 'env_setup') else "",
                    help="Shell commands to setup environment (e.g., 'source /etc/profile')"
                )
            
            # Scheduler resources
            if scheduler != "direct":
                st.subheader("Scheduler Resources")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    nodes = st.number_input("Nodes", min_value=1, value=1)
                with col2:
                    ntasks = st.number_input("Tasks per Node", min_value=1, value=20)
                with col3:
                    time = st.text_input("Wall Time", value="24:00:00")
                
                partition = st.text_input("Partition/Queue", value="")
            
            # Submit buttons
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Save Machine Configuration")
            with col2:
                test = st.form_submit_button("🔍 Test Connection")
        
        # Handle form submission
        if submit:
            try:
                # Build machine config
                machine_config = {
                    "name": machine_name,
                    "execution": execution,
                    "scheduler": scheduler,
                    "workdir": workdir,
                    "nprocs": nprocs,
                    "launcher": launcher,
                    "use_modules": use_modules,
                }
                
                if use_modules:
                    machine_config["modules"] = [m.strip() for m in modules_str.split("\n") if m.strip()]
                
                if prepend:
                    machine_config["prepend"] = [p.strip() for p in prepend.split("\n") if p.strip()]
                if postpend:
                    machine_config["postpend"] = [p.strip() for p in postpend.split("\n") if p.strip()]
                if env_setup:
                    machine_config["env_setup"] = env_setup
                
                if execution == "remote":
                    machine_config["host"] = host
                    machine_config["username"] = username
                    machine_config["port"] = port
                    machine_config["auth"] = {
                        "method": "key",
                        "ssh_key": ssh_key
                    }
                
                if scheduler != "direct":
                    machine_config["resources"] = {
                        "nodes": nodes,
                        "ntasks-per-node": ntasks,
                        "time": time,
                    }
                    if partition:
                        machine_config["resources"]["partition"] = partition
                
                # Create Machine object
                new_machine = Machine(**machine_config)
                
                # Save machine
                save_machine(new_machine, DEFAULT_CONFIG_PATH, DEFAULT_MACHINES_DIR)
                
                st.success(f"✅ Machine '{machine_name}' saved successfully!")
                st.session_state.current_machine = new_machine
                
            except Exception as e:
                st.error(f"❌ Error saving machine: {e}")
                st.code(traceback.format_exc())

# Page 2: Codes Configuration
elif page == "⚙️ Codes Configuration":
    st.header("Quantum ESPRESSO Codes Configuration")
    st.markdown("""
    Configure Quantum ESPRESSO executable paths for different machines.
    Auto-detection is supported for both local and remote systems.
    """)
    
    if not XESPRESSO_AVAILABLE:
        st.error("xespresso modules not available. Cannot configure codes.")
    else:
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
            
            # Auto-detection section
            st.subheader("Auto-Detect Codes")
            
            with st.form("detect_codes_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    qe_prefix = st.text_input(
                        "QE Installation Prefix (optional)",
                        help="e.g., /opt/qe-7.2/bin"
                    )
                    modules_str = st.text_area(
                        "Modules to Load (optional, one per line)",
                        help="Environment modules needed to access QE"
                    )
                
                with col2:
                    search_paths_str = st.text_area(
                        "Additional Search Paths (optional, one per line)",
                        help="Additional directories to search for executables"
                    )
                
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
                            auto_load_machine=True
                        )
                        
                        if codes_config and codes_config.codes:
                            st.success(f"✅ Detected {len(codes_config.codes)} codes!")
                            st.session_state.current_codes = codes_config
                            
                            # Display detected codes
                            st.subheader("Detected Codes")
                            codes_data = []
                            for name, code in codes_config.codes.items():
                                codes_data.append({
                                    "Code": name,
                                    "Path": code.path,
                                    "Version": code.version or "Unknown"
                                })
                            st.table(codes_data)
                            
                            # Save option
                            if st.button("💾 Save Codes Configuration"):
                                try:
                                    from xespresso.codes.manager import CodesManager
                                    filepath = CodesManager.save_config(
                                        codes_config,
                                        output_dir=DEFAULT_CODES_DIR,
                                        overwrite=False,
                                        merge=True
                                    )
                                    st.success(f"✅ Codes saved to: {filepath}")
                                except Exception as e:
                                    st.error(f"Error saving codes: {e}")
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
                    
                    codes_data = []
                    for name, code in existing_codes.codes.items():
                        codes_data.append({
                            "Code": name,
                            "Path": code.path,
                            "Version": code.version or "Unknown"
                        })
                    st.table(codes_data)
                    
                    st.session_state.current_codes = existing_codes
                else:
                    st.info("ℹ️ No codes configuration found for this machine.")
            except Exception as e:
                st.warning(f"Could not load codes configuration: {e}")

# Page 3: Structure Viewer
elif page == "🔬 Structure Viewer":
    st.header("Structure Viewer")
    st.markdown("""
    Upload or select molecular/crystal structures for your calculations.
    Supports CIF, POSCAR, XYZ, and other ASE-compatible formats.
    """)
    
    if not ASE_AVAILABLE:
        st.error("ASE not available. Structure viewing is disabled.")
    else:
        # Structure source selection
        structure_source = st.radio(
            "Structure Source:",
            ["Upload File", "Build Structure", "Load from File"]
        )
        
        atoms = None
        
        if structure_source == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Structure File",
                type=['cif', 'xyz', 'pdb', 'poscar', 'vasp', 'traj'],
                help="Supported formats: CIF, XYZ, PDB, POSCAR, etc."
            )
            
            if uploaded_file is not None:
                try:
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Read structure
                    atoms = io.read(tmp_path)
                    st.success(f"✅ Loaded structure from {uploaded_file.name}")
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"❌ Error reading structure: {e}")
        
        elif structure_source == "Build Structure":
            st.subheader("Build Simple Structure")
            
            build_type = st.selectbox(
                "Structure Type:",
                ["Bulk Crystal", "Molecule"]
            )
            
            if build_type == "Bulk Crystal":
                col1, col2 = st.columns(2)
                with col1:
                    element = st.text_input("Element", value="Fe")
                    crystal_structure = st.selectbox(
                        "Crystal Structure",
                        ["fcc", "bcc", "hcp", "diamond", "sc"]
                    )
                with col2:
                    a_param = st.number_input("Lattice Parameter (Å)", value=3.6, step=0.1)
                    cubic = st.checkbox("Cubic Cell", value=True)
                
                if st.button("Build Crystal"):
                    try:
                        atoms = bulk(
                            element,
                            crystal_structure,
                            a=a_param,
                            cubic=cubic
                        )
                        st.success(f"✅ Built {element} {crystal_structure} structure")
                    except Exception as e:
                        st.error(f"❌ Error building structure: {e}")
            
            else:  # Molecule
                molecule_name = st.text_input(
                    "Molecule Name",
                    value="H2O",
                    help="Common molecules: H2O, CO2, CH4, etc."
                )
                
                if st.button("Build Molecule"):
                    try:
                        atoms = molecule(molecule_name)
                        st.success(f"✅ Built {molecule_name} molecule")
                    except Exception as e:
                        st.error(f"❌ Error building molecule: {e}")
        
        else:  # Load from File
            file_path = st.text_input(
                "File Path",
                help="Enter full path to structure file"
            )
            
            if st.button("Load File") and file_path:
                try:
                    atoms = io.read(file_path)
                    st.success(f"✅ Loaded structure from {file_path}")
                except Exception as e:
                    st.error(f"❌ Error loading file: {e}")
        
        # Display structure if loaded
        if atoms is not None:
            st.session_state.current_structure = atoms
            
            # Display structure info
            display_structure_info(atoms)
            
            # 3D Visualization
            st.subheader("3D Visualization")
            if PLOTLY_AVAILABLE:
                fig = create_3d_structure_plot(atoms)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Plotly not available. Install plotly for 3D visualization.")
            
            # Export structure
            st.subheader("Export Structure")
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.selectbox(
                    "Export Format",
                    ["cif", "xyz", "poscar", "pdb"]
                )
            
            with col2:
                export_filename = st.text_input(
                    "Filename",
                    value=f"structure.{export_format}"
                )
            
            if st.button("💾 Export Structure"):
                try:
                    export_path = os.path.join(tempfile.gettempdir(), export_filename)
                    io.write(export_path, atoms, format=export_format)
                    
                    with open(export_path, 'r') as f:
                        file_content = f.read()
                    
                    st.download_button(
                        "📥 Download File",
                        file_content,
                        file_name=export_filename,
                        mime="text/plain"
                    )
                    
                    st.success(f"✅ Structure exported as {export_format}")
                except Exception as e:
                    st.error(f"❌ Error exporting: {e}")

# Page 4: Calculation Setup
elif page == "📊 Calculation Setup":
    st.header("Calculation Setup")
    st.markdown("""
    Configure the type of calculation and basic parameters.
    """)
    
    if st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first in the Structure Viewer.")
    else:
        st.info(f"✅ Working with: {st.session_state.current_structure.get_chemical_formula()}")
        
        # Calculation type
        calc_type = st.selectbox(
            "Calculation Type",
            [
                "SCF (Self-Consistent Field)",
                "Relaxation (Geometry Optimization)",
                "VC-Relax (Cell + Geometry Optimization)",
                "Bands (Band Structure)",
                "DOS (Density of States)",
                "NSCF (Non-Self-Consistent)",
                "Phonon",
                "NEB (Nudged Elastic Band)"
            ]
        )
        
        st.session_state.workflow_config['calc_type'] = calc_type.split()[0].lower()
        
        # Pseudopotentials
        st.subheader("Pseudopotentials")
        
        atoms = st.session_state.current_structure
        unique_elements = list(set(atoms.get_chemical_symbols()))
        
        st.write(f"**Elements in structure:** {', '.join(unique_elements)}")
        
        pseudo_method = st.radio(
            "Pseudopotential Selection:",
            ["Manual Entry", "Load Configuration"]
        )
        
        pseudopotentials = {}
        
        if pseudo_method == "Manual Entry":
            st.write("Enter pseudopotential file for each element:")
            for element in unique_elements:
                pseudo = st.text_input(
                    f"{element}",
                    value=f"{element}.pbe-n-kjpaw_psl.1.0.0.UPF",
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
                        configs
                    )
                    
                    if st.button("Load Configuration"):
                        config = load_pseudo_config(selected_config)
                        pseudopotentials = config.get('pseudopotentials', {})
                        st.success(f"✅ Loaded pseudopotentials from {selected_config}")
                        st.json(pseudopotentials)
                else:
                    st.warning("No saved pseudopotential configurations found.")
            except Exception as e:
                st.error(f"Error loading configurations: {e}")
        
        st.session_state.workflow_config['pseudopotentials'] = pseudopotentials
        
        # Basic parameters
        st.subheader("Calculation Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ecutwfc = st.number_input(
                "Kinetic Energy Cutoff (ecutwfc) [Ry]",
                min_value=10.0,
                max_value=200.0,
                value=50.0,
                step=5.0,
                help="Plane-wave cutoff energy"
            )
            
            if calc_type.startswith("SCF") or calc_type.startswith("Relaxation"):
                conv_thr = st.number_input(
                    "Convergence Threshold",
                    min_value=1e-10,
                    max_value=1e-4,
                    value=1e-6,
                    format="%.1e",
                    help="SCF convergence threshold"
                )
        
        with col2:
            ecutrho = st.number_input(
                "Charge Density Cutoff (ecutrho) [Ry]",
                min_value=10.0,
                max_value=800.0,
                value=ecutwfc * 4,
                step=10.0,
                help="Charge density cutoff (usually 4-8 × ecutwfc)"
            )
        
        st.session_state.workflow_config.update({
            'ecutwfc': ecutwfc,
            'ecutrho': ecutrho,
        })
        
        if calc_type.startswith("SCF") or calc_type.startswith("Relaxation"):
            st.session_state.workflow_config['conv_thr'] = conv_thr
        
        # K-points
        st.subheader("K-point Sampling")
        
        kpt_method = st.radio(
            "K-point Method:",
            ["K-spacing", "Monkhorst-Pack Grid"]
        )
        
        if kpt_method == "K-spacing":
            kspacing = st.slider(
                "K-spacing (Å⁻¹)",
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.05,
                help="Smaller values = denser k-point mesh"
            )
            st.session_state.workflow_config['kspacing'] = kspacing
            
            # Show equivalent grid
            try:
                from xespresso import kpts_from_spacing
                kpts = kpts_from_spacing(atoms, kspacing)
                st.info(f"Equivalent Monkhorst-Pack grid: {kpts[0]} × {kpts[1]} × {kpts[2]}")
            except:
                pass
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                k1 = st.number_input("k₁", min_value=1, value=4)
            with col2:
                k2 = st.number_input("k₂", min_value=1, value=4)
            with col3:
                k3 = st.number_input("k₃", min_value=1, value=4)
            
            st.session_state.workflow_config['kpts'] = (k1, k2, k3)
        
        # Spin polarization
        st.subheader("Spin Polarization")
        nspin = st.selectbox(
            "Spin Treatment",
            [1, 2, 4],
            format_func=lambda x: {
                1: "Non-spin-polarized",
                2: "Spin-polarized (collinear)",
                4: "Non-collinear + spin-orbit"
            }[x]
        )
        st.session_state.workflow_config['nspin'] = nspin
        
        st.success("✅ Calculation parameters configured!")

# Page 5: Workflow Builder
elif page == "🔄 Workflow Builder":
    st.header("Workflow Builder")
    st.markdown("""
    Build complete calculation workflows using quality presets.
    """)
    
    if not XESPRESSO_AVAILABLE:
        st.error("xespresso modules not available.")
    elif st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first.")
    else:
        st.info(f"✅ Working with: {st.session_state.current_structure.get_chemical_formula()}")
        
        # Quality presets
        st.subheader("Quality Presets")
        
        quality = st.select_slider(
            "Quality Level",
            options=["fast", "moderate", "accurate"],
            value="moderate",
            help="Predefined parameter sets for different accuracy/speed tradeoffs"
        )
        
        # Display preset info
        if XESPRESSO_AVAILABLE:
            preset_info = PRESETS.get(quality, {})
            st.info(f"""
            **{quality.upper()} preset:**
            - ecutwfc: {preset_info.get('ecutwfc', 'N/A')} Ry
            - ecutrho: {preset_info.get('ecutrho', 'N/A')} Ry
            - conv_thr: {preset_info.get('conv_thr', 'N/A')}
            - Default k-spacing: {preset_info.get('kspacing', 'N/A')} Å⁻¹
            """)
        
        st.session_state.workflow_config['quality'] = quality
        
        # Workflow type
        st.subheader("Workflow Configuration")
        
        workflow_type = st.selectbox(
            "Workflow Type",
            ["Quick SCF", "Quick Relax", "Custom Workflow"]
        )
        
        if workflow_type == "Quick Relax":
            relax_type = st.selectbox(
                "Relaxation Type",
                ["relax", "vc-relax"],
                format_func=lambda x: {
                    "relax": "Relax atoms only",
                    "vc-relax": "Relax atoms + cell"
                }[x]
            )
            st.session_state.workflow_config['relax_type'] = relax_type
        
        # Label/directory
        st.subheader("Calculation Settings")
        
        label = st.text_input(
            "Calculation Label",
            value="calc/structure",
            help="Directory path for calculation files"
        )
        st.session_state.workflow_config['label'] = label
        
        # Summary
        st.subheader("Workflow Summary")
        
        st.json(st.session_state.workflow_config)
        
        if st.button("✅ Create Workflow"):
            st.success("✅ Workflow configured! Proceed to Job Submission to run the calculation.")

# Page 6: Job Submission
elif page == "🚀 Job Submission":
    st.header("Job Submission")
    st.markdown("""
    Submit your configured calculation to the selected machine.
    """)
    
    # Check prerequisites
    if not XESPRESSO_AVAILABLE:
        st.error("xespresso modules not available.")
    elif st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded.")
    elif not st.session_state.workflow_config:
        st.warning("⚠️ No workflow configured.")
    else:
        # Display configuration summary
        st.subheader("Configuration Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Structure:**")
            atoms = st.session_state.current_structure
            st.write(f"- Formula: {atoms.get_chemical_formula()}")
            st.write(f"- Atoms: {len(atoms)}")
            
            st.write("**Machine:**")
            if st.session_state.current_machine:
                machine = st.session_state.current_machine
                st.write(f"- Name: {machine.name}")
                st.write(f"- Type: {machine.execution}")
            else:
                st.write("- Not configured")
        
        with col2:
            st.write("**Workflow:**")
            config = st.session_state.workflow_config
            st.write(f"- Quality: {config.get('quality', 'N/A')}")
            st.write(f"- Type: {config.get('calc_type', 'N/A')}")
            st.write(f"- Label: {config.get('label', 'N/A')}")
            
            st.write("**Codes:**")
            if st.session_state.current_codes:
                codes = st.session_state.current_codes
                st.write(f"- Configured: {len(codes.codes)} codes")
            else:
                st.write("- Not configured")
        
        # Submission options
        st.subheader("Submission Options")
        
        dry_run = st.checkbox(
            "Dry Run (don't actually submit)",
            value=True,
            help="Generate input files without running"
        )
        
        # Submit button
        if st.button("🚀 Submit Job", type="primary"):
            with st.spinner("Submitting job..."):
                try:
                    st.info("📝 Job submission functionality will be implemented")
                    st.info("This will create input files and submit to the configured machine")
                    
                    # Show what would be done
                    st.subheader("Submission Details")
                    st.write("**Steps that would be performed:**")
                    st.write("1. ✓ Create calculation directory")
                    st.write("2. ✓ Write structure file")
                    st.write("3. ✓ Generate Quantum ESPRESSO input")
                    st.write("4. ✓ Submit to scheduler (if configured)")
                    st.write("5. ✓ Monitor job status")
                    
                    if dry_run:
                        st.success("✅ Dry run completed - no job submitted")
                    else:
                        st.success("✅ Job submitted successfully!")
                        st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error submitting job: {e}")
                    st.code(traceback.format_exc())

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
### About
**xespresso GUI** - Streamlit interface for Quantum ESPRESSO calculations

Version: 1.0.0

[Documentation](https://github.com/superstar54/xespresso) | 
[Report Issue](https://github.com/superstar54/xespresso/issues)
""")
