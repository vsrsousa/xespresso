"""Structure Viewer Page for xespresso GUI."""
import streamlit as st
from ase import io as ase_io
import os
import tempfile

def render_structure_viewer_page():
    """Render the structure viewer page with embeddable 3D viewers and visualization options."""
    st.header("Structure Viewer")
    st.markdown("""
    Load and visualize atomic structures with interactive 3D viewers.
    All viewers are embeddable and work in web browsers without external applications.
    """)
    
    # File upload section
    st.subheader("📂 Load Structure")
    
    # Tab for different input methods
    tab1, tab2 = st.tabs(["Upload File", "Browse Directory"])
    
    with tab1:
        uploaded_file = st.file_uploader(
            "Upload structure file",
            type=['cif', 'xyz', 'pdb', 'vasp', 'poscar', 'traj', 'json'],
            help="Supported formats: CIF, XYZ, PDB, VASP, POSCAR, TRAJ, JSON"
        )
        
        if uploaded_file:
            try:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                # Read structure
                atoms = ase_io.read(tmp_path)
                os.unlink(tmp_path)
                
                st.success(f"✅ Loaded: {uploaded_file.name}")
                render_structure_controls_and_viewer(atoms)
                
            except Exception as e:
                st.error(f"❌ Error loading file: {e}")
    
    with tab2:
        # Working directory browser
        try:
            from xespresso.gui.utils.selectors import render_workdir_browser
            workdir = render_workdir_browser(key="structure_viewer_workdir")
        except ImportError:
            workdir = st.text_input("Working Directory:", value=os.getcwd())
            workdir = os.path.abspath(os.path.expanduser(workdir))
        
        if os.path.exists(workdir) and os.path.isdir(workdir):
            # Find structure files
            structure_extensions = ['.cif', '.xyz', '.pdb', '.vasp', '.poscar', '.traj', '.json']
            structure_files = []
            
            for root, dirs, files in os.walk(workdir):
                depth = root[len(workdir):].count(os.sep)
                if depth < 3:  # Limit recursion depth
                    for f in files:
                        if any(f.lower().endswith(ext) for ext in structure_extensions):
                            structure_files.append(os.path.join(root, f))
            
            if structure_files:
                st.success(f"✅ Found {len(structure_files)} structure file(s)")
                
                selected_file = st.selectbox(
                    "Select structure file:",
                    structure_files,
                    format_func=lambda x: os.path.relpath(x, workdir)
                )
                
                if selected_file and st.button("Load Structure"):
                    try:
                        atoms = ase_io.read(selected_file)
                        st.success(f"✅ Loaded: {os.path.relpath(selected_file, workdir)}")
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
            options=['plotly', 'py3dmol', 'simple'],
            format_func=lambda x: {
                'plotly': '📊 Plotly (Interactive 3D)',
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "Export Format:",
            options=['cif', 'xyz', 'pdb', 'vasp', 'json'],
            help="Format for exporting the structure"
        )
    
    with col2:
        if st.button("⬇️ Download Structure", type="secondary"):
            try:
                # Create temporary file for export
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{export_format}") as tmp:
                    ase_io.write(tmp.name, atoms, format=export_format)
                    with open(tmp.name, 'rb') as f:
                        file_data = f.read()
                    os.unlink(tmp.name)
                
                st.download_button(
                    label=f"Download as {export_format.upper()}",
                    data=file_data,
                    file_name=f"structure.{export_format}",
                    mime="application/octet-stream"
                )
            except Exception as e:
                st.error(f"❌ Error exporting structure: {e}")
