"""Job Submission Page for xespresso GUI."""
import streamlit as st
import os
from pathlib import Path

def render_job_submission_page():
    """Render the job submission page with enhanced job file viewer, editor, and submission."""
    st.header("Job Submission & File Management")
    st.markdown("""
    **Generate calculation files, browse directories, and run calculations using xespresso.**
    
    - **Generate Files (Dry Run)**: Creates Espresso calculator and generates input files with `calc.write_input(atoms)` for review
    - **File Browser**: Browse, view, and edit existing calculation files
    - **Run Calculation**: Creates Espresso calculator and runs with `calc.get_potential_energy()`
    """)
    
    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["📂 File Browser", "🧪 Generate Files (Dry Run)", "🚀 Run Calculation"])
    
    with tab1:
        render_file_browser_tab()
    
    with tab2:
        render_dry_run_tab()
    
    with tab3:
        render_job_submission_tab()


def render_dry_run_tab():
    """Render the dry run tab for generating input and job files without submission."""
    st.subheader("🧪 Generate Calculation Files (Dry Run)")
    st.markdown("""
    Generate input files and job scripts for your calculation **without submitting the job**.
    This is useful for:
    - Testing your configuration before submission
    - Manually reviewing and editing files before running
    - Creating files to transfer to another system
    """)
    
    # Check if structure is loaded
    if 'current_structure' not in st.session_state or st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first in the Structure Viewer page.")
        return
    
    atoms = st.session_state.current_structure
    st.success(f"✅ Structure loaded: {atoms.get_chemical_formula()} ({len(atoms)} atoms)")
    
    st.markdown("---")
    
    # Check if calculation is configured
    if 'workflow_config' not in st.session_state or not st.session_state.workflow_config.get('pseudopotentials'):
        st.warning("⚠️ No calculation configured. Please configure your calculation first in the Calculation Setup page.")
        st.info("""
        **Required configuration:**
        - Pseudopotentials for all elements
        - Calculation parameters (ecutwfc, kpts, etc.)
        - Machine and codes selection
        
        Go to **📊 Calculation Setup** page to configure these.
        """)
        return
    
    # Show current configuration summary
    st.subheader("📋 Current Configuration")
    config = st.session_state.workflow_config
    
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
    
    # Working directory selection
    st.subheader("📁 Output Directory")
    
    try:
        from xespresso.gui.utils.selectors import render_workdir_browser
        workdir = render_workdir_browser(key="dry_run_workdir")
    except ImportError:
        workdir = st.text_input(
            "Working Directory:", 
            value=os.path.join(os.getcwd(), "calculations"),
            key="dry_run_workdir_input"
        )
        workdir = os.path.abspath(os.path.expanduser(workdir))
    
    # Validate and normalize workdir to prevent path traversal
    try:
        workdir = os.path.realpath(workdir)
        # Check if workdir is under a safe base directory (e.g., user's home or /tmp)
        safe_bases = [os.path.realpath(os.path.expanduser("~")), os.path.realpath("/tmp")]
        is_safe = any(workdir.startswith(base) for base in safe_bases)
        
        if not is_safe:
            st.warning("⚠️ For security, only directories under your home directory or /tmp are allowed")
            return
    except (OSError, ValueError) as e:
        st.error(f"❌ Invalid directory path: {e}")
        return
    
    # Label/subfolder for this calculation
    label = st.text_input(
        "Calculation Label (subfolder):",
        value=f"{config.get('calc_type', 'scf')}/{atoms.get_chemical_formula()}",
        help="Label for this calculation - will create subfolder under working directory",
        key="dry_run_label"
    )
    
    # Full path where files will be created
    full_path = os.path.join(workdir, label)
    
    # Validate the full path to prevent path traversal in the label
    try:
        full_path = os.path.realpath(full_path)
        # Ensure full_path is under workdir (prevent path traversal via label)
        if not full_path.startswith(workdir):
            st.error("❌ Invalid calculation label - path traversal detected")
            return
    except (OSError, ValueError) as e:
        st.error(f"❌ Invalid path: {e}")
        return
    
    st.info(f"📍 Files will be created in: `{full_path}`")
    
    st.markdown("---")
    
    # Machine and Queue Configuration
    st.subheader("🖥️ Machine & Queue Configuration")
    
    try:
        from xespresso.gui.utils.selectors import render_machine_selector
        machine_name, machine = render_machine_selector(key="dry_run_machine")
    except ImportError:
        st.warning("Machine selector not available - will create input files without job script")
        machine_name, machine = None, None
    
    if machine_name and machine:
        st.success(f"✅ Machine selected: {machine_name}")
        
        # Show queue info if available
        if hasattr(machine, 'queue') and machine.queue:
            with st.expander("Queue Configuration"):
                import json
                st.json(machine.queue)
    
    st.markdown("---")
    
    # Generate button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        generate_button = st.button(
            "🧪 Generate Files (Dry Run)",
            type="primary",
            help="Generate input and job files without submitting",
            key="generate_files_button"
        )
    
    if generate_button:
        st.info("🧪 **Dry Run Mode** - Generating files using xespresso calculator...")
        
        with st.spinner("Generating files..."):
            try:
                from xespresso import Espresso
                from ase import io as ase_io
                
                # Create output directory if it doesn't exist
                os.makedirs(full_path, exist_ok=True)
                
                # Save structure file
                structure_filename = f"{atoms.get_chemical_formula()}.cif"
                structure_path = os.path.join(full_path, structure_filename)
                ase_io.write(structure_path, atoms)
                st.info(f"💾 Saved structure: {structure_filename}")
                
                # Build calculator parameters from configuration
                calc_params = {
                    'pseudopotentials': config['pseudopotentials'],
                    'label': os.path.join(full_path, 'espresso'),
                }
                
                # Build input_data dictionary
                input_data = {}
                
                # Add basic parameters
                if 'ecutwfc' in config:
                    input_data['ecutwfc'] = config['ecutwfc']
                if 'ecutrho' in config:
                    input_data['ecutrho'] = config['ecutrho']
                if 'occupations' in config:
                    input_data['occupations'] = config['occupations']
                if 'conv_thr' in config:
                    input_data['conv_thr'] = config['conv_thr']
                
                # Add smearing if applicable
                if config.get('occupations') == 'smearing':
                    input_data['smearing'] = config.get('smearing', 'gaussian')
                    input_data['degauss'] = config.get('degauss', 0.02)
                
                # Add spin polarization
                if 'nspin' in config:
                    input_data['nspin'] = config['nspin']
                
                # Add calculation type
                calc_type = config.get('calc_type', 'scf')
                if calc_type in ['relax', 'vc-relax']:
                    input_data['calculation'] = calc_type
                else:
                    input_data['calculation'] = 'scf'
                
                calc_params['input_data'] = input_data
                
                # Add k-points
                if 'kspacing' in config:
                    calc_params['kspacing'] = config['kspacing']
                elif 'kpts' in config:
                    calc_params['kpts'] = config['kpts']
                
                # Add machine/queue if available
                if machine and hasattr(machine, 'queue'):
                    calc_params['queue'] = machine.queue
                
                # Create Espresso calculator with all parameters
                st.info("🔧 Creating Espresso calculator...")
                calc = Espresso(**calc_params)
                
                # Generate input files using xespresso's write_input method
                st.info("📝 Writing input files with calc.write_input(atoms)...")
                calc.write_input(atoms)
                
                st.success("✅ Files generated successfully using xespresso!")
                
                # Display results
                st.subheader("📄 Generated Files")
                
                # List generated files
                generated_files = []
                if os.path.exists(full_path):
                    for f in os.listdir(full_path):
                        if f.endswith(('.pwi', '.asei', '.cif', 'job_file', '.sh', '.slurm')):
                            generated_files.append(f)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Files created:**")
                    for f in generated_files:
                        st.markdown(f"- ✅ {f}")
                
                with col2:
                    st.write("**Location:**")
                    st.code(full_path)
                
                st.markdown("---")
                
                # Preview input file
                input_file_path = os.path.join(full_path, 'espresso.pwi')
                if os.path.exists(input_file_path):
                    st.subheader("👁️ Input File Preview")
                    try:
                        # Validate path is under full_path for security
                        input_path = os.path.realpath(input_file_path)
                        if not input_path.startswith(full_path):
                            st.error("❌ Security error: input file path is outside expected directory")
                        else:
                            with open(input_path, 'r') as f:
                                input_content = f.read()
                            
                            with st.expander("View Input File", expanded=True):
                                st.code(input_content, language='fortran', line_numbers=True)
                                
                                # Download button
                                st.download_button(
                                    label="⬇️ Download Input File",
                                    data=input_content,
                                    file_name='espresso.pwi',
                                    mime="text/plain"
                                )
                    except Exception as e:
                        st.error(f"Error reading input file: {e}")
                
                # Preview job file if it exists
                job_file_path = os.path.join(full_path, 'job_file')
                if os.path.exists(job_file_path):
                    st.subheader("👁️ Job Script Preview")
                    try:
                        # Validate path is under full_path for security
                        job_path = os.path.realpath(job_file_path)
                        if not job_path.startswith(full_path):
                            st.error("❌ Security error: job file path is outside expected directory")
                        else:
                            with open(job_path, 'r') as f:
                                job_content = f.read()
                            
                            with st.expander("View Job Script", expanded=False):
                                st.code(job_content, language='bash', line_numbers=True)
                                
                                # Download button
                                st.download_button(
                                    label="⬇️ Download Job Script",
                                    data=job_content,
                                    file_name='job_file',
                                    mime="text/plain"
                                )
                    except Exception as e:
                        st.error(f"Error reading job file: {e}")
                
                st.markdown("---")
                
                # Next steps
                st.subheader("✨ Next Steps")
                st.info("""
                **Files have been generated using xespresso!** You can now:
                
                1. **Review the files** using the File Browser tab above
                2. **Edit the files** if needed (use Edit mode in File Browser)
                3. **Run the calculation** using the Run Calculation tab
                4. **Transfer files** to another system if needed
                
                The Espresso calculator was created with your configuration and used to generate these files.
                """)
                    
            except Exception as e:
                st.error(f"❌ Error generating files: {e}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())


def render_file_browser_tab():
    """Render the file browser tab."""
    # Working Directory Browser Section
    st.subheader("📁 Working Directory Browser")
    
    # Import the workdir browser utility
    try:
        from xespresso.gui.utils.selectors import render_workdir_browser
        workdir = render_workdir_browser(key="job_submission_workdir")
    except ImportError:
        workdir = st.text_input("Working Directory:", value=os.getcwd())
        workdir = os.path.abspath(os.path.expanduser(workdir))
    
    if not os.path.exists(workdir) or not os.path.isdir(workdir):
        st.error(f"❌ Invalid working directory: {workdir}")
        return
    
    st.markdown("---")
    
    # Calculation Folder Navigation
    st.subheader("📂 Calculation Folders")
    st.info("💡 xespresso organizes calculations in label-based folders (e.g., 'calc/structure')")
    
    # Find calculation folders (those with input files)
    calc_folders = []
    input_file_extensions = ['.in', '.pwi', '.phi', '.ppi', '.bandi']
    
    try:
        for root, dirs, files in os.walk(workdir, topdown=True):
            # Limit depth to avoid too much recursion
            depth = root[len(workdir):].count(os.sep)
            if depth < 4:
                has_input_files = any(f.endswith(tuple(input_file_extensions)) or 
                                     f == 'job_file' or f.endswith('.sh') or f.endswith('.slurm')
                                     for f in files)
                if has_input_files:
                    calc_folders.append(root)
        
        if calc_folders:
            st.success(f"✅ Found {len(calc_folders)} calculation folder(s)")
            
            # Select calculation folder
            selected_folder = st.selectbox(
                "Select Calculation Folder:",
                calc_folders,
                format_func=lambda x: os.path.relpath(x, workdir) if x != workdir else "."
            )
            
            if selected_folder:
                st.info(f"📍 Selected: `{os.path.relpath(selected_folder, workdir)}`")
                
                # List files in the selected folder
                try:
                    files_in_folder = [f for f in os.listdir(selected_folder) 
                                      if os.path.isfile(os.path.join(selected_folder, f))]
                    
                    # Categorize files
                    input_files = [f for f in files_in_folder if f.endswith(tuple(input_file_extensions))]
                    job_files = [f for f in files_in_folder if f == 'job_file' or f.endswith(('.sh', '.slurm'))]
                    output_files = [f for f in files_in_folder if f.endswith(('.out', '.pwo', '.pho', '.ppo'))]
                    other_files = [f for f in files_in_folder if f not in input_files + job_files + output_files]
                    
                    # Display file categories
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Input Files", len(input_files))
                    with col2:
                        st.metric("Job Scripts", len(job_files))
                    with col3:
                        st.metric("Output Files", len(output_files))
                    with col4:
                        st.metric("Other Files", len(other_files))
                    
                    st.markdown("---")
                    
                    # File Viewer/Editor Section
                    st.subheader("📄 File Viewer & Editor")
                    
                    # File type selector
                    file_type = st.radio(
                        "File Category:",
                        ["Input Files", "Job Scripts", "Output Files", "All Files"],
                        horizontal=True
                    )
                    
                    # Select file to view based on category
                    if file_type == "Input Files":
                        available_files = input_files
                    elif file_type == "Job Scripts":
                        available_files = job_files
                    elif file_type == "Output Files":
                        available_files = output_files
                    else:
                        available_files = files_in_folder
                    
                    if available_files:
                        selected_file = st.selectbox(
                            "Select File:",
                            available_files
                        )
                        
                        if selected_file:
                            file_path = os.path.join(selected_folder, selected_file)
                            
                            # Security check
                            if not os.path.commonpath([selected_folder, file_path]) == selected_folder:
                                st.error("❌ Invalid file path")
                                return
                            
                            # View/Edit mode selector
                            mode = st.radio(
                                "Mode:",
                                ["View", "Edit"],
                                horizontal=True,
                                key="file_mode"
                            )
                            
                            try:
                                with open(file_path, 'r') as f:
                                    file_content = f.read()
                                
                                # Show file info
                                file_stat = os.stat(file_path)
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("File Size", f"{file_stat.st_size} bytes")
                                with col2:
                                    st.metric("Lines", len(file_content.splitlines()))
                                with col3:
                                    from datetime import datetime
                                    mod_time = datetime.fromtimestamp(file_stat.st_mtime)
                                    st.metric("Modified", mod_time.strftime("%Y-%m-%d %H:%M"))
                                
                                if mode == "View":
                                    # View mode - display as code
                                    st.subheader("File Content")
                                    st.code(file_content, language="bash" if selected_file.endswith(('.sh', '.slurm', 'job_file')) else "fortran", line_numbers=True)
                                    
                                    # Download button
                                    st.download_button(
                                        label="⬇️ Download File",
                                        data=file_content,
                                        file_name=selected_file,
                                        mime="text/plain"
                                    )
                                    
                                    # Parse job file information
                                    if selected_file in job_files:
                                        st.subheader("Job File Summary")
                                        
                                        # Extract SLURM/PBS directives
                                        scheduler_directives = []
                                        commands = []
                                        for line in file_content.splitlines():
                                            line_stripped = line.strip()
                                            if line_stripped.startswith("#SBATCH") or line_stripped.startswith("#PBS"):
                                                scheduler_directives.append(line_stripped)
                                            elif line_stripped and not line_stripped.startswith("#"):
                                                commands.append(line_stripped)
                                        
                                        if scheduler_directives:
                                            st.markdown("**Scheduler Directives:**")
                                            for directive in scheduler_directives:
                                                st.markdown(f"- `{directive}`")
                                        
                                        if commands:
                                            st.markdown("**Key Commands:**")
                                            for cmd in commands[:10]:
                                                st.markdown(f"- `{cmd}`")
                                            if len(commands) > 10:
                                                st.markdown(f"... and {len(commands) - 10} more commands")
                                
                                else:
                                    # Edit mode - text area for editing
                                    st.subheader("Edit File Content")
                                    st.warning("⚠️ **Caution:** Editing files can affect your calculations. Make sure you know what you're doing!")
                                    
                                    edited_content = st.text_area(
                                        "File Content:",
                                        value=file_content,
                                        height=400,
                                        key="file_editor"
                                    )
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("💾 Save Changes", type="primary"):
                                            try:
                                                with open(file_path, 'w') as f:
                                                    f.write(edited_content)
                                                st.success(f"✅ File saved successfully: {selected_file}")
                                            except Exception as e:
                                                st.error(f"❌ Error saving file: {e}")
                                    
                                    with col2:
                                        if st.button("↩️ Revert Changes"):
                                            st.rerun()
                            
                            except Exception as e:
                                st.error(f"❌ Error reading file: {e}")
                    else:
                        st.warning(f"⚠️ No files found in the '{file_type}' category")
                
                except Exception as e:
                    st.error(f"❌ Error listing files: {e}")
        else:
            st.warning("⚠️ No calculation folders found in the working directory")
            st.info("""
            **Tip:** Calculation folders typically contain:
            - Input files (`*.in`, `*.pwi`, etc.)
            - Job scripts (`job_file`, `*.sh`, `*.slurm`)
            - Output files (`*.out`, `*.pwo`, etc.)
            
            Make sure you've set up calculations first in the Calculation Setup page.
            """)
    
    except Exception as e:
        st.error(f"❌ Error scanning directory: {e}")
    
    # Additional info section
    st.markdown("---")
    st.subheader("💡 Tips")
    st.info("""
    **Working with xespresso calculations:**
    - xespresso organizes files in label-based folders (e.g., `calc/label/`)
    - Input files are named based on the calculation type (e.g., `*.pwi` for pw.x)
    - Job files are typically named `job_file` or have `.sh`/`.slurm` extensions
    - The results folder is the same as the calculation folder
    
    **File editing:**
    - Use the Edit mode to modify input parameters
    - Always backup important files before editing
    - Changes are saved immediately when you click "Save Changes"
    """)


def render_job_submission_tab():
    """Render the job submission tab for running calculations with xespresso."""
    st.subheader("🚀 Run Calculation")
    st.markdown("""
    Run a calculation using xespresso by calling `calc.get_potential_energy()`.
    
    This will:
    - Create an Espresso calculator from your configuration
    - Automatically generate input files if they don't exist
    - Run the calculation and return the energy
    """)
    
    # Check if structure is loaded
    if 'current_structure' not in st.session_state or st.session_state.current_structure is None:
        st.warning("⚠️ No structure loaded. Please load a structure first in the Structure Viewer page.")
        return
    
    atoms = st.session_state.current_structure
    st.success(f"✅ Structure loaded: {atoms.get_chemical_formula()} ({len(atoms)} atoms)")
    
    st.markdown("---")
    
    # Check if calculation is configured
    if 'workflow_config' not in st.session_state or not st.session_state.workflow_config.get('pseudopotentials'):
        st.warning("⚠️ No calculation configured. Please configure your calculation first in the Calculation Setup page.")
        st.info("""
        **Required configuration:**
        - Pseudopotentials for all elements
        - Calculation parameters (ecutwfc, kpts, etc.)
        - Machine and codes selection
        
        Go to **📊 Calculation Setup** page to configure these.
        """)
        return
    
    # Show current configuration summary
    st.subheader("📋 Current Configuration")
    config = st.session_state.workflow_config
    
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
    
    # Working directory and label
    st.subheader("📁 Output Location")
    
    try:
        from xespresso.gui.utils.selectors import render_workdir_browser
        workdir = render_workdir_browser(key="run_calc_workdir")
    except ImportError:
        workdir = st.text_input(
            "Working Directory:", 
            value=os.path.join(os.getcwd(), "calculations"),
            key="run_calc_workdir_input"
        )
        workdir = os.path.abspath(os.path.expanduser(workdir))
    
    # Validate and normalize workdir to prevent path traversal
    try:
        workdir = os.path.realpath(workdir)
        # Check if workdir is under a safe base directory
        safe_bases = [os.path.realpath(os.path.expanduser("~")), os.path.realpath("/tmp")]
        is_safe = any(workdir.startswith(base) for base in safe_bases)
        
        if not is_safe:
            st.warning("⚠️ For security, only directories under your home directory or /tmp are allowed")
            return
    except (OSError, ValueError) as e:
        st.error(f"❌ Invalid directory path: {e}")
        return
    
    # Label for calculation
    label = st.text_input(
        "Calculation Label (subfolder):",
        value=f"{config.get('calc_type', 'scf')}/{atoms.get_chemical_formula()}",
        help="Label for this calculation - will create subfolder under working directory",
        key="run_calc_label"
    )
    
    # Full path where calculation will run
    full_path = os.path.join(workdir, label)
    
    # Validate the full path to prevent path traversal in the label
    try:
        full_path = os.path.realpath(full_path)
        # Ensure full_path is under workdir (prevent path traversal via label)
        if not full_path.startswith(workdir):
            st.error("❌ Invalid calculation label - path traversal detected")
            return
    except (OSError, ValueError) as e:
        st.error(f"❌ Invalid path: {e}")
        return
    
    st.info(f"📍 Calculation will run in: `{full_path}`")
    
    st.markdown("---")
    
    # Run calculation button
    st.subheader("▶️ Execute Calculation")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        run_button = st.button(
            "🚀 Run Calculation",
            type="primary",
            help="Run calculation using calc.get_potential_energy()",
            key="run_calculation_button"
        )
    
    if run_button:
        st.info("🚀 **Running Calculation** - Using xespresso's calc.get_potential_energy()...")
        
        with st.spinner("Running calculation..."):
            try:
                from xespresso import Espresso
                
                # Create output directory if it doesn't exist
                os.makedirs(full_path, exist_ok=True)
                
                # Check if calculator already exists in session_state
                # (created by Calculation Setup or Workflow Builder)
                if 'espresso_calculator' in st.session_state and st.session_state.espresso_calculator is not None:
                    st.info("📦 Using pre-configured calculator from Calculation Setup...")
                    calc = st.session_state.espresso_calculator
                    
                    # Update the label to use the current output path
                    calc.label = os.path.join(full_path, 'espresso')
                else:
                    # Fallback: Create calculator from workflow_config
                    st.info("🔧 Creating Espresso calculator from configuration...")
                    
                    # Build calculator parameters from configuration
                    calc_params = {
                        'pseudopotentials': config['pseudopotentials'],
                        'label': os.path.join(full_path, 'espresso'),
                    }
                    
                    # Build input_data dictionary
                    input_data = {}
                    
                    # Add basic parameters
                    if 'ecutwfc' in config:
                        input_data['ecutwfc'] = config['ecutwfc']
                    if 'ecutrho' in config:
                        input_data['ecutrho'] = config['ecutrho']
                    if 'occupations' in config:
                        input_data['occupations'] = config['occupations']
                    if 'conv_thr' in config:
                        input_data['conv_thr'] = config['conv_thr']
                    
                    # Add smearing if applicable
                    if config.get('occupations') == 'smearing':
                        input_data['smearing'] = config.get('smearing', 'gaussian')
                        input_data['degauss'] = config.get('degauss', 0.02)
                    
                    # Add spin polarization
                    if 'nspin' in config:
                        input_data['nspin'] = config['nspin']
                    
                    # Add calculation type
                    calc_type = config.get('calc_type', 'scf')
                    if calc_type in ['relax', 'vc-relax']:
                        input_data['calculation'] = calc_type
                    else:
                        input_data['calculation'] = 'scf'
                    
                    calc_params['input_data'] = input_data
                    
                    # Add k-points
                    if 'kspacing' in config:
                        calc_params['kspacing'] = config['kspacing']
                    elif 'kpts' in config:
                        calc_params['kpts'] = config['kpts']
                    
                    # Create Espresso calculator
                    calc = Espresso(**calc_params)
                
                # Attach calculator to atoms
                st.info("🔗 Attaching calculator to atoms object...")
                atoms.calc = calc
                
                # Run calculation using get_potential_energy()
                st.info("⚡ Calling atoms.get_potential_energy()...")
                energy = atoms.get_potential_energy()
                
                # Display results
                st.success("✅ Calculation completed successfully!")
                st.markdown("---")
                st.subheader("📊 Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Energy", f"{energy:.6f} eV")
                with col2:
                    st.metric("Structure", atoms.get_chemical_formula())
                
                # Show calculation details
                with st.expander("📋 Calculation Details"):
                    st.write("**Input Parameters:**")
                    st.json(input_data)
                    
                    st.write("**Pseudopotentials:**")
                    for species, pseudo in config['pseudopotentials'].items():
                        st.text(f"  {species}: {pseudo}")
                    
                    if 'kpts' in calc_params:
                        st.write("**K-points:**")
                        st.text(f"  {calc_params['kpts']}")
                    elif 'kspacing' in calc_params:
                        st.write("**K-spacing:**")
                        st.text(f"  {calc_params['kspacing']} Å⁻¹")
                
                # Show output location
                st.markdown("---")
                st.subheader("📁 Output Files")
                st.info(f"Calculation files saved in: `{full_path}`")
                
                # List generated files
                if os.path.exists(full_path):
                    generated_files = []
                    for f in os.listdir(full_path):
                        if f.endswith(('.pwi', '.pwo', '.out', '.log')):
                            generated_files.append(f)
                    
                    if generated_files:
                        st.write("**Generated files:**")
                        for f in generated_files:
                            st.markdown(f"- `{f}`")
                
            except Exception as e:
                st.error(f"❌ Calculation error: {e}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())
