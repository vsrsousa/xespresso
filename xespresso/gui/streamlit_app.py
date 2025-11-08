"""
Streamlit GUI for xespresso - Quantum ESPRESSO Configuration Interface

This application provides a user-friendly interface for:
- Configuring machines (local/remote execution environments)
- Setting up Quantum ESPRESSO codes
- Viewing and selecting molecular structures
- Configuring calculations and workflows
- Submitting computational jobs

This is the main entry point for the modular GUI.
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

# Import modular page components
try:
    from xespresso.gui.pages import (
        render_machine_config_page,
        render_codes_config_page,
        render_structure_viewer_page,
        render_calculation_setup_page,
        render_workflow_builder_page,
        render_job_submission_page,
        render_results_postprocessing_page
    )
    PAGES_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Error importing page modules: {e}")
    PAGES_AVAILABLE = False

# Import xespresso modules for pages that still need them inline
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

# Import utility functions
try:
    from xespresso.gui.utils import validate_path, create_3d_structure_plot, display_structure_info
    UTILS_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ GUI utilities not fully available: {e}")
    UTILS_AVAILABLE = False
    # Fallback implementations
    def validate_path(path, allow_creation=False):
        """Fallback path validation."""
        return True, path, None
    
    def create_3d_structure_plot(atoms):
        """Fallback plot function."""
        return None
    
    def display_structure_info(atoms):
        """Fallback structure info display."""
        st.write(f"Structure: {atoms.get_chemical_formula()}")

# Initialize session state
if 'current_structure' not in st.session_state:
    st.session_state.current_structure = None
if 'current_machine' not in st.session_state:
    st.session_state.current_machine = None
if 'current_machine_name' not in st.session_state:
    st.session_state.current_machine_name = None
if 'current_codes' not in st.session_state:
    st.session_state.current_codes = None
if 'selected_code_version' not in st.session_state:
    st.session_state.selected_code_version = None
if 'workflow_config' not in st.session_state:
    st.session_state.workflow_config = {}
if 'local_workdir' not in st.session_state:
    st.session_state.local_workdir = os.getcwd()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Page:",
    [
        "🖥️ Machine Configuration",
        "⚙️ Codes Configuration", 
        "🔬 Structure Viewer",
        "📊 Calculation Setup",
        "🔄 Workflow Builder",
        "🚀 Job Submission & Files",
        "📈 Results & Post-Processing"
    ]
)

# Page routing
if page == "🖥️ Machine Configuration":
    if PAGES_AVAILABLE:
        render_machine_config_page()
    else:
        st.error("Page modules not available. Please check installation.")

elif page == "⚙️ Codes Configuration":
    if PAGES_AVAILABLE:
        render_codes_config_page()
    else:
        st.error("Page modules not available. Please check installation.")

elif page == "🔬 Structure Viewer":
    st.header("Structure Viewer")
    st.markdown("""
    Upload or select molecular/crystal structures for your calculations.
    Supports CIF, POSCAR, XYZ, and other ASE-compatible formats.
    """)
    
    # Show currently loaded structure if available
    if st.session_state.current_structure is not None:
        st.success(f"✅ Current structure: {st.session_state.current_structure.get_chemical_formula()} ({len(st.session_state.current_structure)} atoms)")
    
    if not ASE_AVAILABLE:
        st.error("ASE not available. Structure viewing is disabled.")
    else:
        # Structure source selection
        structure_source = st.radio(
            "Structure Source:",
            ["Upload File", "Build Structure", "Load from File", "ASE Database"]
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
        
        elif structure_source == "Load from File":
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
        
        else:  # ASE Database
            st.subheader("ASE Database")
            
            db_path = st.text_input(
                "Database Path",
                value=st.session_state.get('ase_db_path', os.path.expanduser("~/.xespresso/structures.db")),
                help="Path to ASE database file"
            )
            
            # Validate database path
            is_valid, normalized_db_path, error_msg = validate_path(db_path, allow_creation=True)
            if not is_valid:
                st.error(f"❌ Invalid database path: {error_msg}")
                normalized_db_path = None
            else:
                st.session_state['ase_db_path'] = normalized_db_path
            
            # Database operations
            db_operation = st.radio(
                "Operation:",
                ["Load from Database", "Save to Database"]
            )
            
            if normalized_db_path and is_valid:
                if db_operation == "Load from Database":
                    if os.path.exists(normalized_db_path):
                        try:
                            from ase.db import connect
                            db = connect(normalized_db_path)
                            
                            # List structures in database
                            rows = list(db.select())
                            if rows:
                                st.write(f"Found {len(rows)} structures in database")
                            
                            # Create selection table
                            structures_info = []
                            for row in rows:
                                structures_info.append({
                                    "ID": row.id,
                                    "Formula": row.formula,
                                    "Atoms": row.natoms,
                                    "Tags": ", ".join(row.key_value_pairs.keys()) if row.key_value_pairs else ""
                                })
                            
                            st.table(structures_info)
                            
                            selected_id = st.number_input(
                                "Select structure ID to load:",
                                min_value=1,
                                max_value=len(rows),
                                value=1
                            )
                            
                            if st.button("Load Selected Structure"):
                                try:
                                    row = db.get(id=selected_id)
                                    atoms = row.toatoms()
                                    st.success(f"✅ Loaded structure ID {selected_id}: {atoms.get_chemical_formula()}")
                                except Exception as e:
                                    st.error(f"❌ Error loading structure: {e}")
                            else:
                                st.info("Database is empty. Save structures to start building your library.")
                        except Exception as e:
                            st.error(f"❌ Error reading database: {e}")
                    else:
                        st.info(f"Database does not exist yet. It will be created when you save your first structure.")
                
                else:  # Save to Database
                    if st.session_state.current_structure is not None:
                        current_atoms = st.session_state.current_structure
                        st.info(f"Ready to save: {current_atoms.get_chemical_formula()} ({len(current_atoms)} atoms)")
                        
                        # Add metadata
                        save_tags = st.text_input(
                            "Tags (comma-separated)",
                            help="Add tags to help identify this structure later"
                        )
                        
                        save_description = st.text_area(
                            "Description (optional)",
                            help="Add notes about this structure"
                        )
                        
                        if st.button("💾 Save to Database"):
                            try:
                                from ase.db import connect
                                db = connect(normalized_db_path)
                                
                                # Parse tags
                                key_value_pairs = {}
                                if save_tags:
                                    for tag in save_tags.split(','):
                                        tag = tag.strip()
                                        if tag:
                                            key_value_pairs[tag] = True
                                
                                if save_description:
                                    key_value_pairs['description'] = save_description
                                
                                # Save to database
                                db.write(current_atoms, **key_value_pairs)
                                st.success(f"✅ Structure saved to database: {normalized_db_path}")
                            except Exception as e:
                                st.error(f"❌ Error saving to database: {e}")
                    else:
                        st.warning("⚠️ No structure loaded. Load a structure first before saving to database.")
        
        # Display structure if loaded (or show current structure)
        display_atoms = atoms if atoms is not None else st.session_state.current_structure
        
        if display_atoms is not None:
            # Update session state if new structure was loaded
            if atoms is not None:
                st.session_state.current_structure = atoms
            
            # Display structure info
            display_structure_info(display_atoms)
            
            # 3D Visualization with multiple viewer options
            st.subheader("3D Visualization")
            
            # Viewer type selector
            viewer_type = st.radio(
                "Select Viewer:",
                [
                    "Plotly (Interactive 3D)", 
                    "JMol (No WebGL)", 
                    "py3Dmol (Lightweight)", 
                    "ASE Native (External Window)",
                    "X3D (WebGL)", 
                    "Simple (Text)"
                ],
                horizontal=False,
                help="""Choose your preferred structure viewer:
                
• **Plotly**: Interactive 3D with WebGL (best for modern browsers)
• **JMol**: Browser-based without WebGL requirements (good compatibility)
• **py3Dmol**: Lightweight JavaScript viewer (requires py3Dmol package)
• **ASE Native**: Opens in separate window (requires display/X11)
• **X3D**: WebGL-based embedded viewer
• **Simple**: Text-only representation (no graphics)
                """
            )
            
            viewer_map = {
                "Plotly (Interactive 3D)": "plotly",
                "JMol (No WebGL)": "jmol",
                "py3Dmol (Lightweight)": "py3dmol",
                "ASE Native (External Window)": "ase",
                "X3D (WebGL)": "x3d",
                "Simple (Text)": "simple"
            }
            
            try:
                from xespresso.gui.utils.visualization import render_structure_viewer
                render_structure_viewer(display_atoms, viewer_type=viewer_map[viewer_type], key="structure_viz")
            except Exception as e:
                st.error(f"Error rendering structure: {e}")
                # Fallback to simple plotly
                if PLOTLY_AVAILABLE:
                    fig = create_3d_structure_plot(display_atoms)
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
                    io.write(export_path, display_atoms, format=export_format)
                    
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
    Configure calculations: select machine, codes, and set calculation parameters.
    """)
    
    # Machine and Codes Selection Section
    st.subheader("🖥️ Machine & Codes Selection")
    st.info("💡 Select a configured machine and code version for your calculations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            from xespresso.gui.utils.selectors import render_machine_selector
            machine_name, machine = render_machine_selector(key="calc_setup_machine")
        except ImportError:
            st.warning("Machine selector not available")
            machine_name, machine = None, None
    
    with col2:
        if machine_name:
            try:
                from xespresso.gui.utils.selectors import render_codes_selector
                codes = render_codes_selector(machine_name, key="calc_setup_codes")
            except ImportError:
                st.warning("Codes selector not available")
                codes = None
        else:
            st.info("Select a machine first to choose codes")
            codes = None
    
    st.markdown("---")
    
    # Structure Check
    if st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first in the Structure Viewer.")
    else:
        st.success(f"✅ Structure loaded: {st.session_state.current_structure.get_chemical_formula()}")
        
        # Calculation type
        st.subheader("Calculation Type")
        calc_type = st.selectbox(
            "Select Calculation:",
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
        
        # Pseudopotential family selector
        st.info("💡 **Pseudopotential families** vary based on functional (LDA, GGA-PBE, GGA-PBESOL) and type")
        pp_family = st.selectbox(
            "Pseudopotential Family:",
            [
                "PBE - PAW (pbe-n-kjpaw_psl)",
                "PBE - Ultrasoft (pbe-n-rrkjus_psl)",
                "PBE - Norm-conserving (pbe-n-nc)",
                "PBESOL - PAW (pbesol-n-kjpaw_psl)",
                "PBESOL - Ultrasoft (pbesol-n-rrkjus_psl)",
                "LDA - Ultrasoft (lda)",
                "Custom (Manual Entry)"
            ],
            help="Select the pseudopotential family matching your functional"
        )
        
        # Parse family info
        pp_mapping = {
            "PBE - PAW (pbe-n-kjpaw_psl)": ("pbe", "kjpaw_psl", "1.0.0"),
            "PBE - Ultrasoft (pbe-n-rrkjus_psl)": ("pbe", "rrkjus_psl", "1.0.0"),
            "PBE - Norm-conserving (pbe-n-nc)": ("pbe", "nc", "1.0.0"),
            "PBESOL - PAW (pbesol-n-kjpaw_psl)": ("pbesol", "kjpaw_psl", "1.0.0"),
            "PBESOL - Ultrasoft (pbesol-n-rrkjus_psl)": ("pbesol", "rrkjus_psl", "1.0.0"),
            "LDA - Ultrasoft (lda)": ("lda", "pz", "2.0.1"),
        }
        
        pseudopotentials = {}
        
        if pp_family == "Custom (Manual Entry)":
            st.write("**Manual Entry:** Enter pseudopotential file for each element:")
            for element in unique_elements:
                pseudo = st.text_input(
                    f"{element}:",
                    value=f"{element}.pbe-n-kjpaw_psl.1.0.0.UPF",
                    key=f"pseudo_{element}",
                    help="Full pseudopotential filename (e.g., Fe.pbe-n-kjpaw_psl.1.0.0.UPF)"
                )
                pseudopotentials[element] = pseudo
        else:
            # Auto-generate pseudo names based on family
            functional, pp_type, version = pp_mapping[pp_family]
            
            st.write(f"**Auto-generated pseudopotentials** (Family: {functional}, Type: {pp_type}):")
            
            # Allow user to override specific elements if needed
            override_elements = st.multiselect(
                "Override specific elements (optional):",
                unique_elements,
                help="Select elements for which you want to manually specify the pseudopotential"
            )
            
            for element in unique_elements:
                if element in override_elements:
                    # Manual override
                    pseudo = st.text_input(
                        f"{element} (Override):",
                        value=f"{element}.{functional}-n-{pp_type}.{version}.UPF",
                        key=f"pseudo_{element}"
                    )
                    pseudopotentials[element] = pseudo
                else:
                    # Auto-generate
                    pseudo = f"{element}.{functional}-n-{pp_type}.{version}.UPF"
                    pseudopotentials[element] = pseudo
                    st.text(f"{element}: {pseudo}")
            
            st.info("""
            **Note on pseudopotentials:**
            - Pseudopotentials must be available in your `ESPRESSO_PSEUDO` directory or specified path
            - For remote calculations, xespresso handles transferring pseudopotential files automatically
            - Different families are optimized for different functionals (LDA, PBE, PBESOL)
            """)
        
        st.session_state.workflow_config['pseudopotentials'] = pseudopotentials
        
        # Basic parameters
        st.subheader("Calculation Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Use session state for persistence
            default_ecutwfc = st.session_state.workflow_config.get('ecutwfc', 50.0)
            ecutwfc = st.number_input(
                "Kinetic Energy Cutoff (ecutwfc) [Ry]",
                min_value=10.0,
                max_value=200.0,
                value=float(default_ecutwfc),
                step=5.0,
                help="Plane-wave cutoff energy"
            )
            
            # Add dual parameter
            default_dual = st.session_state.workflow_config.get('dual', 4.0)
            dual = st.number_input(
                "Dual Parameter (ecutrho/ecutwfc ratio)",
                min_value=1.0,
                max_value=12.0,
                value=float(default_dual),
                step=0.5,
                help="Ratio between charge density and wavefunction cutoffs (typically 4-8)"
            )
            
            if calc_type.startswith("SCF") or calc_type.startswith("Relaxation"):
                default_conv_thr = st.session_state.workflow_config.get('conv_thr', 1e-6)
                conv_thr = st.number_input(
                    "Convergence Threshold",
                    min_value=1e-10,
                    max_value=1e-4,
                    value=float(default_conv_thr),
                    format="%.1e",
                    help="SCF convergence threshold"
                )
        
        with col2:
            # Calculate ecutrho from dual
            ecutrho = ecutwfc * dual
            st.number_input(
                "Charge Density Cutoff (ecutrho) [Ry]",
                min_value=10.0,
                max_value=800.0,
                value=ecutrho,
                step=10.0,
                help="Charge density cutoff = dual × ecutwfc",
                disabled=True
            )
        
        st.session_state.workflow_config.update({
            'ecutwfc': ecutwfc,
            'ecutrho': ecutrho,
            'dual': dual,
        })
        
        if calc_type.startswith("SCF") or calc_type.startswith("Relaxation"):
            st.session_state.workflow_config['conv_thr'] = conv_thr
        
        # Smearing options
        st.subheader("Electronic Occupations")
        
        col1, col2 = st.columns(2)
        with col1:
            occupations = st.selectbox(
                "Occupation Type",
                ["smearing", "fixed", "tetrahedra"],
                index=["smearing", "fixed", "tetrahedra"].index(
                    st.session_state.workflow_config.get('occupations', 'smearing')
                ),
                help="Method for determining electronic occupations"
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
                    help="Type of smearing function"
                )
                st.session_state.workflow_config['smearing'] = smearing_type
                
                degauss = st.number_input(
                    "Smearing Width (degauss) [Ry]",
                    min_value=0.001,
                    max_value=0.1,
                    value=st.session_state.workflow_config.get('degauss', 0.02),
                    step=0.001,
                    format="%.3f",
                    help="Width of smearing (typically 0.01-0.03 Ry)"
                )
                st.session_state.workflow_config['degauss'] = degauss
        
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
        default_nspin = st.session_state.workflow_config.get('nspin', 1)
        nspin = st.selectbox(
            "Spin Treatment",
            [1, 2, 4],
            index=[1, 2, 4].index(default_nspin),
            format_func=lambda x: {
                1: "Non-spin-polarized",
                2: "Spin-polarized (collinear)",
                4: "Non-collinear + spin-orbit"
            }[x],
            help="Spin treatment for magnetic systems"
        )
        st.session_state.workflow_config['nspin'] = nspin
        
        # DFT+U section
        st.subheader("DFT+U Configuration")
        use_dft_u = st.checkbox(
            "Enable DFT+U",
            value=st.session_state.workflow_config.get('use_dft_u', False),
            help="Add Hubbard U correction for strongly correlated systems"
        )
        st.session_state.workflow_config['use_dft_u'] = use_dft_u
        
        if use_dft_u:
            st.info("Configure Hubbard U parameters for each element")
            
            atoms = st.session_state.current_structure
            unique_elements = list(set(atoms.get_chemical_symbols()))
            
            hubbard_u = st.session_state.workflow_config.get('hubbard_u', {})
            
            for element in unique_elements:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**{element}**")
                with col2:
                    u_val = st.number_input(
                        f"U value (eV)",
                        min_value=0.0,
                        max_value=10.0,
                        value=hubbard_u.get(element, {}).get('U', 0.0),
                        step=0.5,
                        key=f"hubbard_u_{element}"
                    )
                with col3:
                    orbital = st.selectbox(
                        f"Orbital",
                        ["2p", "3d", "4f"],
                        index=["2p", "3d", "4f"].index(hubbard_u.get(element, {}).get('orbital', '3d')),
                        key=f"hubbard_orbital_{element}"
                    )
                
                if u_val > 0:
                    hubbard_u[element] = {'U': u_val, 'orbital': orbital}
            
            st.session_state.workflow_config['hubbard_u'] = hubbard_u
        
        # Calculation-specific options
        if calc_type.startswith("Bands"):
            st.subheader("Band Structure Settings")
            
            band_path_method = st.radio(
                "K-path Selection:",
                ["Automatic (seekpath)", "Custom Path"]
            )
            
            if band_path_method == "Automatic (seekpath)":
                st.info("Will use automatic k-path detection based on crystal symmetry")
                st.session_state.workflow_config['band_path'] = 'auto'
            else:
                st.write("Define custom k-path (e.g., 'GXMGRX' for cubic systems)")
                custom_path = st.text_input(
                    "K-path",
                    value=st.session_state.workflow_config.get('custom_band_path', 'GXMGRX'),
                    help="Specify high-symmetry points"
                )
                st.session_state.workflow_config['band_path'] = 'custom'
                st.session_state.workflow_config['custom_band_path'] = custom_path
                
            npoints = st.number_input(
                "Number of k-points along path",
                min_value=10,
                max_value=500,
                value=st.session_state.workflow_config.get('band_npoints', 100),
                help="Total number of k-points along the band path"
            )
            st.session_state.workflow_config['band_npoints'] = npoints
        
        st.success("✅ Calculation parameters configured!")

# Page 5: Workflow Builder
elif page == "🔄 Workflow Builder":
    st.header("Workflow Builder")
    st.markdown("""
    Build complete calculation workflows using quality presets.
    """)
    
    # Machine and Codes Selection Section
    st.subheader("🖥️ Machine & Codes Selection")
    st.info("💡 Select machine and code version before configuring workflow")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            from xespresso.gui.utils.selectors import render_machine_selector
            machine_name, machine = render_machine_selector(key="workflow_machine")
        except ImportError:
            st.warning("Machine selector not available")
            machine_name, machine = None, None
    
    with col2:
        if machine_name:
            try:
                from xespresso.gui.utils.selectors import render_codes_selector
                codes = render_codes_selector(machine_name, key="workflow_codes")
            except ImportError:
                st.warning("Codes selector not available")
                codes = None
        else:
            st.info("Select a machine first to choose codes")
            codes = None
    
    st.markdown("---")
    
    if not XESPRESSO_AVAILABLE:
        st.error("xespresso modules not available.")
    elif st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first.")
    else:
        st.success(f"✅ Structure loaded: {st.session_state.current_structure.get_chemical_formula()}")
        
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

# Page 6: Job Submission & File Management
elif page == "🚀 Job Submission & Files":
    if PAGES_AVAILABLE:
        render_job_submission_page()
    else:
        st.error("Page modules not available. Please check installation.")

# Page 7: Results & Post-Processing
elif page == "📈 Results & Post-Processing":
    st.header("Results & Post-Processing")
    st.markdown("""
    View calculation results, analyze output files, and perform post-processing.
    """)
    
    # Working directory browser
    st.subheader("📁 Results Directory")
    st.info("💡 **Note:** The results folder is the same as the calculation folder (label-based directory)")
    
    try:
        from xespresso.gui.utils.selectors import render_workdir_browser
        results_dir = render_workdir_browser(
            current_dir=st.session_state.get('local_workdir', os.getcwd()),
            key="results_workdir"
        )
    except ImportError:
        results_dir = st.text_input(
            "Results Directory",
            value=st.session_state.local_workdir,
            help="Path to directory containing calculation results (same as calculation working directory)"
        )
        results_dir = os.path.abspath(os.path.expanduser(results_dir))
    
    st.markdown("---")
    
    # Validate results directory path
    is_valid_results, normalized_results_dir, error_msg = validate_path(results_dir, allow_creation=False)
    
    if not is_valid_results:
        st.error(f"❌ Invalid results directory: {error_msg}")
    elif os.path.exists(normalized_results_dir):
        st.success(f"✅ Directory found: {normalized_results_dir}")
        
        # List output files
        st.subheader("Output Files")
        
        try:
            files = os.listdir(normalized_results_dir)
            output_files = [f for f in files if f.endswith(('.out', '.pwo', '.xml', '.log'))]
            
            if output_files:
                selected_file = st.selectbox(
                    "Select output file to view:",
                    output_files
                )
                
                # Validate selected filename (no path traversal)
                if '..' in selected_file or '/' in selected_file or '\\' in selected_file:
                    st.error("❌ Invalid filename")
                else:
                    file_path = os.path.join(normalized_results_dir, selected_file)
                
                    # Display file info
                    file_size = os.path.getsize(file_path)
                    st.info(f"File: {selected_file} | Size: {file_size / 1024:.2f} KB")
                    
                    # View file content
                    if st.button("📄 View File Content"):
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                            
                            # Show in expandable text area
                            with st.expander("File Content", expanded=True):
                                st.text_area(
                                    "Output",
                                    value=content,
                                    height=400,
                                    key="file_content"
                                )
                            
                            # Parse for key information
                            st.subheader("Extracted Information")
                            
                            # Simple parsing for common outputs
                            if "Final energy" in content or "!" in content:
                                st.write("**Energy Information:**")
                                for line in content.split('\n'):
                                    if "Final energy" in line or (line.strip().startswith("!") and "total energy" in line.lower()):
                                        st.code(line.strip())
                            
                            if "convergence has been achieved" in content.lower():
                                st.success("✅ Calculation converged successfully")
                            elif "convergence NOT achieved" in content.lower():
                                st.warning("⚠️ Calculation did not converge")
                            
                        except Exception as e:
                            st.error(f"❌ Error reading file: {e}")
                    
                    # Download button
                    try:
                        with open(file_path, 'r') as f:
                            file_content = f.read()
                        
                        st.download_button(
                            "📥 Download Output File",
                            file_content,
                            file_name=selected_file,
                            mime="text/plain"
                        )
                    except Exception as e:
                        st.error(f"❌ Error preparing download: {e}")
            else:
                st.warning("⚠️ No output files found in this directory.")
        
        except Exception as e:
            st.error(f"❌ Error listing files: {e}")
        
        # Structure visualization from results
        st.subheader("Structure Visualization")
        
        try:
            structure_files = [f for f in files if f.endswith(('.cif', '.xyz', '.pdb', '.poscar', 'CONTCAR'))]
            
            if structure_files and ASE_AVAILABLE:
                selected_structure = st.selectbox(
                    "Select structure file:",
                    structure_files
                )
                
                # Validate structure filename
                if '..' in selected_structure or '/' in selected_structure or '\\' in selected_structure:
                    st.error("❌ Invalid structure filename")
                elif st.button("🔬 Visualize Structure"):
                    try:
                        struct_path = os.path.join(normalized_results_dir, selected_structure)
                        atoms = io.read(struct_path)
                        
                        st.success(f"✅ Loaded: {atoms.get_chemical_formula()} ({len(atoms)} atoms)")
                        
                        # Display structure info
                        display_structure_info(atoms)
                        
                        # 3D Visualization
                        if PLOTLY_AVAILABLE:
                            fig = create_3d_structure_plot(atoms)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"❌ Error visualizing structure: {e}")
            else:
                st.info("No structure files found for visualization.")
        
        except Exception as e:
            st.error(f"❌ Error searching for structure files: {e}")
        
        # Post-processing tools
        st.subheader("Post-Processing Tools")
        
        post_tool = st.selectbox(
            "Select Tool:",
            [
                "Energy Analysis",
                "DOS Plotting",
                "Band Structure Plotting",
                "Structure Comparison"
            ]
        )
        
        if post_tool == "Energy Analysis":
            st.info("📊 Energy analysis tools will extract and plot total energy convergence.")
            st.write("*Feature coming soon*")
        
        elif post_tool == "DOS Plotting":
            st.info("📈 DOS plotting tools will visualize density of states from dos.x output.")
            st.write("*Feature coming soon*")
        
        elif post_tool == "Band Structure Plotting":
            st.info("📉 Band structure plotting from bands.x output.")
            st.write("*Feature coming soon*")
        
        elif post_tool == "Structure Comparison":
            st.info("🔄 Compare initial and final structures from relaxation calculations.")
            st.write("*Feature coming soon*")
    
    else:
        st.error(f"❌ Directory not found: {results_dir}")
        st.info("Please check the path or complete a calculation first.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
### About
**xespresso GUI** - Streamlit interface for Quantum ESPRESSO calculations

Version: 1.0.0

[Documentation](https://github.com/superstar54/xespresso) | 
[Report Issue](https://github.com/superstar54/xespresso/issues)
""")
