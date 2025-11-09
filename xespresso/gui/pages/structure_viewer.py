"""
Structure Viewer Page for xespresso GUI.

This page uses the structures module to handle loading and exporting,
following the modular design pattern where dedicated modules handle
specific functionality.
"""
import streamlit as st
import os

def render_structure_viewer_page():
    """
    Render the structure viewer page with embeddable 3D viewers and visualization options.
    
    This page coordinates user interaction and uses the structures module for
    loading and exporting operations, following the modular design pattern.
    """
    st.header("Structure Viewer")
    st.markdown("""
    Load and visualize atomic structures with interactive 3D viewers.
    All viewers are embeddable and work in web browsers without external applications.
    
    **Modular Design:** This page uses the structures module to handle loading and exporting.
    """)
    
    # File upload section
    st.subheader("📂 Load Structure")
    
    # Tab for different input methods
    tab1, tab2, tab3, tab4 = st.tabs(["Upload File", "Browse Directory", "Build Structure", "ASE Database"])
    
    with tab1:
        render_upload_tab()
    
    with tab2:
        render_browse_tab()
    
    with tab3:
        render_build_structure_tab()
    
    with tab4:
        render_ase_database_tab()


def render_upload_tab():
    """Render the file upload tab using structures module."""
    from xespresso.gui.structures import load_structure_from_upload
    
    uploaded_file = st.file_uploader(
        "Upload structure file",
        type=['cif', 'xyz', 'pdb', 'vasp', 'poscar', 'traj', 'json'],
        help="Supported formats: CIF, XYZ, PDB, VASP, POSCAR, TRAJ, JSON"
    )
    
    if uploaded_file:
        try:
            # Use structures module to load from upload
            atoms, loader = load_structure_from_upload(
                uploaded_file.getvalue(),
                uploaded_file.name
            )
            
            st.success(f"✅ Loaded: {uploaded_file.name}")
            
            # Store in session state
            st.session_state.current_structure = atoms
            st.session_state.structure_info = loader.get_info()
            
            render_structure_controls_and_viewer(atoms)
            
        except Exception as e:
            st.error(f"❌ Error loading file: {e}")


def render_browse_tab():
    """Render the directory browser tab using structures module."""
    from xespresso.gui.structures import StructureLoader, load_structure_from_file
    
    # Working directory browser
    try:
        from xespresso.gui.utils.selectors import render_workdir_browser
        workdir = render_workdir_browser(key="structure_viewer_workdir")
    except ImportError:
        workdir = st.text_input("Working Directory:", value=os.getcwd())
        workdir = os.path.abspath(os.path.expanduser(workdir))
    
    if os.path.exists(workdir) and os.path.isdir(workdir):
        # Use structures module to find structure files
        structure_files = StructureLoader.find_structure_files(
            workdir,
            max_depth=3,
            validate_safety=True
        )
        
        if structure_files:
            st.success(f"✅ Found {len(structure_files)} structure file(s)")
            
            selected_file = st.selectbox(
                "Select structure file:",
                structure_files,
                format_func=lambda x: os.path.relpath(x, workdir)
            )
            
            if selected_file and st.button("Load Structure"):
                try:
                    # Use structures module to load from file
                    atoms, loader = load_structure_from_file(selected_file)
                    
                    st.success(f"✅ Loaded: {os.path.relpath(selected_file, workdir)}")
                    
                    # Store in session state
                    st.session_state.current_structure = atoms
                    st.session_state.structure_info = loader.get_info()
                    
                    render_structure_controls_and_viewer(atoms)
                except Exception as e:
                    st.error(f"❌ Error loading file: {e}")
        else:
            st.warning("⚠️ No structure files found in directory")
    else:
        st.error("❌ Invalid working directory")


def render_build_structure_tab():
    """Render the build structure tab for creating simple structures."""
    try:
        from ase.build import bulk, molecule
    except ImportError:
        st.error("❌ ASE not available. Structure building is disabled.")
        return
    
    st.markdown("""
    Build simple structures using ASE's built-in builders.
    """)
    
    build_type = st.selectbox(
        "Structure Type:",
        ["Bulk Crystal", "Molecule"],
        key="build_type_selector"
    )
    
    atoms = None
    
    if build_type == "Bulk Crystal":
        st.subheader("🔷 Build Bulk Crystal")
        
        col1, col2 = st.columns(2)
        with col1:
            element = st.text_input("Element", value="Fe", key="crystal_element")
            crystal_structure = st.selectbox(
                "Crystal Structure",
                ["fcc", "bcc", "hcp", "diamond", "sc"],
                key="crystal_structure"
            )
        with col2:
            a_param = st.number_input(
                "Lattice Parameter (Å)", 
                value=3.6, 
                step=0.1,
                key="lattice_param"
            )
            cubic = st.checkbox("Cubic Cell", value=True, key="cubic_cell")
        
        if st.button("🔨 Build Crystal", key="build_crystal_btn"):
            try:
                atoms = bulk(
                    element,
                    crystal_structure,
                    a=a_param,
                    cubic=cubic
                )
                st.success(f"✅ Built {element} {crystal_structure} structure")
                
                # Store in session state
                st.session_state.current_structure = atoms
                
                render_structure_controls_and_viewer(atoms)
            except Exception as e:
                st.error(f"❌ Error building structure: {e}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())
    
    else:  # Molecule
        st.subheader("🧪 Build Molecule")
        
        molecule_name = st.text_input(
            "Molecule Name",
            value="H2O",
            help="Common molecules: H2O, CO2, CH4, NH3, C6H6, etc.",
            key="molecule_name"
        )
        
        st.info("💡 Tip: Try H2O, CO2, CH4, NH3, C6H6, or other common molecules")
        
        if st.button("🔨 Build Molecule", key="build_molecule_btn"):
            try:
                atoms = molecule(molecule_name)
                # Center molecule in a box
                atoms.center(vacuum=5.0)
                st.success(f"✅ Built {molecule_name} molecule")
                
                # Store in session state
                st.session_state.current_structure = atoms
                
                render_structure_controls_and_viewer(atoms)
            except Exception as e:
                st.error(f"❌ Error building molecule: {e}")
                st.info("Make sure the molecule name is recognized by ASE. Check ASE documentation for available molecules.")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())


def render_ase_database_tab():
    """Render the ASE database tab for loading/saving structures."""
    try:
        from ase.db import connect
    except ImportError:
        st.error("❌ ASE not available. Database functionality is disabled.")
        return
    
    st.markdown("""
    Load and save structures to an ASE database for easy management.
    """)
    
    # Database path configuration
    db_path = st.text_input(
        "Database Path",
        value=st.session_state.get('ase_db_path', os.path.expanduser("~/.xespresso/structures.db")),
        help="Path to ASE database file",
        key="ase_db_path_input"
    )
    
    # Validate database path
    try:
        from xespresso.gui.utils.validation import validate_path, safe_path_exists, safe_makedirs
    except ImportError:
        # Fallback validation
        def validate_path(path, allow_creation=False):
            if not path:
                return False, None, "Path cannot be empty"
            try:
                normalized = os.path.abspath(os.path.expanduser(path))
                if '\0' in normalized:
                    return False, None, "Path contains null bytes"
                if not allow_creation and not os.path.exists(normalized):  # nosec B108
                    return False, normalized, f"Path does not exist: {normalized}"
                return True, normalized, None
            except Exception as e:
                return False, None, f"Invalid path: {str(e)}"
        
        def safe_path_exists(path):
            try:
                return os.path.exists(path)  # nosec B108
            except (OSError, ValueError):
                return False
        
        def safe_makedirs(path):
            try:
                os.makedirs(path, exist_ok=True)  # nosec B108
            except OSError as e:
                raise OSError(f"Failed to create directory: {e}") from e
    
    is_valid, normalized_db_path, error_msg = validate_path(db_path, allow_creation=True)
    
    if not is_valid:
        st.error(f"❌ Invalid database path: {error_msg}")
        return
    
    st.session_state['ase_db_path'] = normalized_db_path
    
    # Database operations
    db_operation = st.radio(
        "Operation:",
        ["Load from Database", "Save to Database"],
        key="db_operation"
    )
    
    if db_operation == "Load from Database":
        render_database_load_section(normalized_db_path)
    else:
        render_database_save_section(normalized_db_path)


def render_database_load_section(db_path):
    """Render the load from database section.
    
    Args:
        db_path: Pre-validated and normalized database path
    """
    # Import safe path utilities
    try:
        from xespresso.gui.utils.validation import safe_path_exists
    except ImportError:
        def safe_path_exists(path):
            try:
                return os.path.exists(path)  # nosec B108
            except (OSError, ValueError):
                return False
    
    if safe_path_exists(db_path):
        try:
            from ase.db import connect
            db = connect(db_path)
            
            # List structures in database
            rows = list(db.select())
            if rows:
                st.success(f"✅ Found {len(rows)} structure(s) in database")
                
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
                    value=1,
                    key="selected_db_id"
                )
                
                if st.button("📥 Load Selected Structure", key="load_db_structure_btn"):
                    try:
                        row = db.get(id=selected_id)
                        atoms = row.toatoms()
                        st.success(f"✅ Loaded structure ID {selected_id}: {atoms.get_chemical_formula()}")
                        
                        # Store in session state
                        st.session_state.current_structure = atoms
                        
                        render_structure_controls_and_viewer(atoms)
                    except Exception as e:
                        st.error(f"❌ Error loading structure: {e}")
                        import traceback
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())
            else:
                st.info("ℹ️ Database is empty. Save structures to start building your library.")
        except Exception as e:
            st.error(f"❌ Error reading database: {e}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    else:
        st.info(f"ℹ️ Database does not exist yet. It will be created when you save your first structure.")


def render_database_save_section(db_path):
    """Render the save to database section.
    
    Args:
        db_path: Pre-validated and normalized database path
    """
    if st.session_state.current_structure is not None:
        current_atoms = st.session_state.current_structure
        st.info(f"Ready to save: {current_atoms.get_chemical_formula()} ({len(current_atoms)} atoms)")
        
        # Add metadata
        save_tags = st.text_input(
            "Tags (comma-separated)",
            help="Add tags to help identify this structure later",
            key="db_save_tags"
        )
        
        save_description = st.text_area(
            "Description (optional)",
            help="Add notes about this structure",
            key="db_save_description"
        )
        
        if st.button("💾 Save to Database", key="save_db_structure_btn"):
            try:
                from ase.db import connect
                
                # Import safe path utilities
                try:
                    from xespresso.gui.utils.validation import safe_makedirs
                except ImportError:
                    def safe_makedirs(path):
                        try:
                            os.makedirs(path, exist_ok=True)  # nosec B108
                        except OSError as e:
                            raise OSError(f"Failed to create directory: {e}") from e
                
                # Create database directory if it doesn't exist
                # db_path has already been validated, so this is safe
                db_dir = os.path.dirname(db_path)
                if db_dir:
                    safe_makedirs(db_dir)
                
                db = connect(db_path)
                
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
                st.success(f"✅ Structure saved to database: {db_path}")
                st.info("Refresh the 'Load from Database' section to see the updated list.")
            except Exception as e:
                st.error(f"❌ Error saving to database: {e}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())
    else:
        st.warning("⚠️ No structure loaded. Load a structure first before saving to database.")


def render_structure_controls_and_viewer(atoms):
    """Render visualization controls and the structure viewer.
    
    Args:
        atoms: ASE Atoms object to visualize
    """
    from xespresso.gui.utils.visualization import render_structure_viewer, display_structure_info
    
    # Display structure information
    display_structure_info(atoms)
    
    st.markdown("---")
    
    # Visualization controls
    st.subheader("🎨 Visualization Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        viewer_type = st.selectbox(
            "Viewer Type:",
            options=['plotly', 'x3d', 'jmol', 'py3dmol', 'simple'],
            format_func=lambda x: {
                'plotly': '📊 Plotly (Interactive 3D)',
                'x3d': '🎨 X3D (WebGL)',
                'jmol': '⚛️ JMol (JavaScript)',
                'py3dmol': '🧬 py3Dmol (Molecular)',
                'simple': '📝 Simple Text'
            }.get(x, x),
            help="Choose visualization method. All viewers are embeddable."
        )
    
    with col2:
        show_conventional = st.checkbox(
            "Show Conventional Cell",
            value=False,
            help="Display conventional cell instead of primitive cell"
        )
    
    with col3:
        white_background = st.checkbox(
            "White Background",
            value=True,
            help="Use white background for better visibility"
        )
    
    # Additional visualization options
    with st.expander("⚙️ Advanced Options"):
        st.info("Additional visualization options can be added here")
        show_axes = st.checkbox("Show Axes Labels", value=True)
        show_bonds = st.checkbox("Show Bonds", value=True)
        atom_size = st.slider("Atom Size", min_value=0.1, max_value=2.0, value=1.0, step=0.1)
    
    st.markdown("---")
    
    # Render the structure
    st.subheader("🔬 Structure Visualization")
    
    try:
        render_structure_viewer(
            atoms, 
            viewer_type=viewer_type,
            show_conventional=show_conventional,
            white_background=white_background,
            key='main_structure_viewer'
        )
    except Exception as e:
        st.error(f"❌ Error rendering structure: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
    
    # Export options
    st.markdown("---")
    st.subheader("💾 Export Options")
    
    render_export_section(atoms)


def render_export_section(atoms):
    """Render the export section using structures module."""
    from xespresso.gui.structures import export_structure, StructureExporter
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "Export Format:",
            options=StructureExporter.get_supported_formats(),
            help="Format for exporting the structure"
        )
    
    with col2:
        if st.button("⬇️ Download Structure", type="secondary"):
            try:
                # Use structures module to export
                file_data = export_structure(atoms, format=export_format)
                
                st.download_button(
                    label=f"Download as {export_format.upper()}",
                    data=file_data,
                    file_name=f"structure.{export_format}",
                    mime="application/octet-stream"
                )
            except Exception as e:
                st.error(f"❌ Error exporting structure: {e}")
