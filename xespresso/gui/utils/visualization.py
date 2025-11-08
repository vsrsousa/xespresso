"""
Structure visualization utilities for the xespresso GUI.
"""

import streamlit as st
import tempfile
import os

try:
    import plotly.graph_objects as go
    import numpy as np
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from ase.visualize import view
    from ase import io
    ASE_VIEWER_AVAILABLE = True
except ImportError:
    ASE_VIEWER_AVAILABLE = False


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


def create_x3d_viewer(atoms):
    """Create an X3D HTML viewer for the structure (embeddable)."""
    try:
        # Create temporary file for X3D output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Write X3D representation
        io.write(tmp_path, atoms, format='x3d')
        
        # Read and return HTML
        with open(tmp_path, 'r') as f:
            html_content = f.read()
        
        os.unlink(tmp_path)
        return html_content
    except Exception as e:
        st.warning(f"Could not create X3D viewer: {e}")
        return None


def render_structure_viewer(atoms, viewer_type='plotly', key='structure_viewer'):
    """
    Render structure visualization with multiple viewer options.
    
    Args:
        atoms: ASE Atoms object
        viewer_type: Type of viewer ('plotly', 'x3d', 'simple')
        key: Unique key for widgets
    """
    if viewer_type == 'plotly':
        if PLOTLY_AVAILABLE:
            fig = create_3d_structure_plot(atoms)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"{key}_plotly")
            else:
                st.error("Could not create Plotly visualization")
        else:
            st.error("⚠️ Plotly not available. Please install plotly: pip install plotly")
    
    elif viewer_type == 'x3d':
        st.info("💡 X3D viewer provides an embedded 3D view using WebGL")
        html_content = create_x3d_viewer(atoms)
        if html_content:
            st.components.v1.html(html_content, height=500, scrolling=True)
        else:
            st.error("Could not create X3D viewer")
    
    elif viewer_type == 'simple':
        # Simple text-based representation
        st.subheader("Simple Text Representation")
        positions = atoms.get_positions()
        symbols = atoms.get_chemical_symbols()
        
        st.code(f"""
Structure: {atoms.get_chemical_formula()}
Number of atoms: {len(atoms)}

Atomic positions:
{"Symbol":<8} {"X (Å)":<12} {"Y (Å)":<12} {"Z (Å)":<12}
{"="*48}
""" + "\n".join([f"{s:<8} {p[0]:>12.6f} {p[1]:>12.6f} {p[2]:>12.6f}" 
                  for s, p in zip(symbols, positions)]))
    
    else:
        st.error(f"Unknown viewer type: {viewer_type}")


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
