"""
Workflow Builder Page for xespresso GUI.

This page creates multi-step workflows using the GUI workflow modules,
which coordinate multiple calculations following xespresso's design patterns.
"""
import streamlit as st


def render_workflow_builder_page():
    """
    Render the workflow builder page.
    
    This page uses the GUI workflow modules to orchestrate multiple
    calculations, with each calculation prepared by calculation modules.
    """
    st.header("🔄 Workflow Builder")
    st.markdown("""
    Build multi-step workflows using **workflow modules** that orchestrate calculations.
    
    **Modular Design:**
    - Workflow modules (`gui/workflows/`) coordinate multiple calculations
    - Each calculation step uses calculation modules to prepare objects
    - Job submission executes the prepared workflow steps
    """)
    
    # Check if structure is loaded
    if 'current_structure' not in st.session_state or st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first in the Structure Viewer page.")
        return
    
    atoms = st.session_state.current_structure
    st.success(f"✅ Structure loaded: {atoms.get_chemical_formula()} ({len(atoms)} atoms)")
    
    st.markdown("---")
    
    # Workflow Type Selection
    st.subheader("🔧 Workflow Type")
    workflow_type = st.selectbox(
        "Select Workflow:",
        [
            'Single SCF',
            'SCF + Relaxation',
            'SCF + Relax + SCF (on relaxed structure)',
            'Custom Multi-Step'
        ],
        help="Choose a predefined workflow or build a custom one"
    )
    
    # Initialize workflow_config if needed
    if 'workflow_config' not in st.session_state:
        st.session_state.workflow_config = {}
    
    config = st.session_state.workflow_config
    
    # Common Parameters
    st.subheader("⚙️ Common Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        ecutwfc = st.number_input("Energy Cutoff (Ry):", value=50.0, min_value=10.0, max_value=200.0, step=5.0)
        config['ecutwfc'] = ecutwfc
        
        kpts_input = st.text_input("K-points (e.g., 4,4,4):", value="4,4,4")
        try:
            kpts = tuple(int(k.strip()) for k in kpts_input.split(','))
            if len(kpts) == 3:
                config['kpts'] = kpts
        except:
            st.warning("Invalid k-points format")
    
    with col2:
        ecutrho = st.number_input("Charge Density Cutoff (Ry):", value=ecutwfc * 8, min_value=40.0, step=20.0)
        config['ecutrho'] = ecutrho
        
        occupations = st.selectbox("Occupations:", ['smearing', 'fixed', 'tetrahedra'])
        config['occupations'] = occupations
    
    # Pseudopotentials
    st.subheader("🧪 Pseudopotentials")
    elements = set(atoms.get_chemical_symbols())
    
    if 'pseudopotentials' not in config:
        config['pseudopotentials'] = {}
    
    for elem in sorted(elements):
        pseudo = st.text_input(
            f"Pseudopotential for {elem}:",
            value=config['pseudopotentials'].get(elem, f"{elem}.UPF"),
            key=f"wf_pseudo_{elem}"
        )
        config['pseudopotentials'][elem] = pseudo
    
    st.markdown("---")
    
    # Workflow-specific configuration
    if workflow_type == 'Single SCF':
        st.subheader("📊 Single SCF Calculation")
        st.info("This workflow performs a single self-consistent field calculation.")
        config['calc_type'] = 'scf'
        
    elif workflow_type == 'SCF + Relaxation':
        st.subheader("🔄 SCF + Relaxation Workflow")
        st.info("""
        This workflow:
        1. Performs an initial SCF calculation
        2. Relaxes the structure geometry
        """)
        
        relax_type = st.radio("Relaxation Type:", ['relax', 'vc-relax'], horizontal=True)
        config['relax_type'] = relax_type
        
        forc_conv_thr = st.number_input(
            "Force Convergence (Ry/bohr):",
            value=1.0e-3,
            format="%.1e"
        )
        config['forc_conv_thr'] = forc_conv_thr
        
    elif workflow_type == 'SCF + Relax + SCF (on relaxed structure)':
        st.subheader("🔄 Complete Relaxation Workflow")
        st.info("""
        This workflow:
        1. Performs initial SCF calculation
        2. Relaxes the structure
        3. Performs final SCF on relaxed structure for accurate energy
        """)
        
        relax_type = st.radio("Relaxation Type:", ['relax', 'vc-relax'], horizontal=True, key="wf_relax_type2")
        config['relax_type'] = relax_type
        
    else:  # Custom Multi-Step
        st.subheader("🔧 Custom Multi-Step Workflow")
        st.info("Build a custom workflow with multiple calculation steps.")
        
        num_steps = st.number_input("Number of Steps:", min_value=1, max_value=10, value=2)
        
        if 'custom_steps' not in st.session_state:
            st.session_state.custom_steps = []
        
        for i in range(num_steps):
            with st.expander(f"Step {i+1}"):
                step_type = st.selectbox(
                    "Calculation Type:",
                    ['scf', 'relax', 'vc-relax', 'nscf', 'bands'],
                    key=f"step_{i}_type"
                )
                st.session_state.custom_steps.append({'type': step_type, 'index': i})
    
    st.markdown("---")
    
    # Build Workflow Button
    st.subheader("✨ Build Workflow")
    st.info("""
    Click below to build the workflow using **workflow modules**.
    The workflow will use calculation modules to prepare each step.
    """)
    
    if st.button("🔄 Build Workflow", type="primary"):
        try:
            from xespresso.gui.workflows import GUIWorkflow
            
            # Validate configuration
            if not config.get('pseudopotentials'):
                st.error("❌ Please specify pseudopotentials for all elements")
                return
            
            # Create workflow using workflow module
            st.info("📦 Creating workflow using workflow module...")
            
            base_label = "workflow"
            workflow = GUIWorkflow(atoms, config, base_label=base_label)
            
            # Add calculation steps based on workflow type
            if workflow_type == 'Single SCF':
                scf_config = config.copy()
                scf_config['calc_type'] = 'scf'
                workflow.add_calculation('scf', scf_config)
                
            elif workflow_type == 'SCF + Relaxation':
                # Step 1: SCF
                scf_config = config.copy()
                scf_config['calc_type'] = 'scf'
                workflow.add_calculation('scf', scf_config)
                
                # Step 2: Relax
                relax_config = config.copy()
                relax_config['calc_type'] = config.get('relax_type', 'relax')
                workflow.add_calculation('relax', relax_config)
                
            elif workflow_type == 'SCF + Relax + SCF (on relaxed structure)':
                # Step 1: Initial SCF
                scf_config = config.copy()
                scf_config['calc_type'] = 'scf'
                workflow.add_calculation('scf_initial', scf_config)
                
                # Step 2: Relax
                relax_config = config.copy()
                relax_config['calc_type'] = config.get('relax_type', 'relax')
                workflow.add_calculation('relax', relax_config)
                
                # Step 3: Final SCF
                scf_final_config = config.copy()
                scf_final_config['calc_type'] = 'scf'
                workflow.add_calculation('scf_final', scf_final_config)
            
            # Store workflow in session state
            st.session_state.gui_workflow = workflow
            
            st.success(f"""
            ✅ **Workflow built successfully!**
            
            The workflow module has created a {workflow_type} workflow with:
            - {len(workflow.calculations)} calculation step(s)
            - Each step prepared using calculation modules
            
            The workflow is stored in session state and ready for execution.
            """)
            
            # Show workflow summary
            with st.expander("📋 Workflow Summary"):
                st.write(f"**Workflow Type:** {workflow_type}")
                st.write(f"**Base Label:** {base_label}")
                st.write(f"**Number of Steps:** {len(workflow.calculations)}")
                st.write("**Steps:**")
                for i, (name, calc_info) in enumerate(workflow.calculations.items(), 1):
                    st.write(f"{i}. **{name}** - {calc_info['config'].get('calc_type', 'unknown')}")
            
        except Exception as e:
            st.error(f"❌ Error building workflow: {e}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    # Show current workflow if exists
    if 'gui_workflow' in st.session_state and st.session_state.gui_workflow:
        st.markdown("---")
        st.subheader("📊 Current Workflow")
        workflow = st.session_state.gui_workflow
        
        st.write(f"**Steps:** {len(workflow.calculations)}")
        for name, calc_info in workflow.calculations.items():
            st.write(f"- {name}: {calc_info['config'].get('calc_type', 'unknown')}")
    
    st.markdown("---")
    st.info("""
    **Next Steps:**
    1. Configure your workflow parameters above
    2. Click "Build Workflow" to create the workflow using workflow modules
    3. Go to "Job Submission" page to execute the workflow steps
    """)

