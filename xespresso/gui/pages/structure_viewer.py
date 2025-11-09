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
    tab1, tab2 = st.tabs(["Upload File", "Browse Directory"])
    
    with tab1:
        render_upload_tab()
    
    with tab2:
        render_browse_tab()


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
