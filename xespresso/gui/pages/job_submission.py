"""Job Submission Page for xespresso GUI."""
import streamlit as st
import os
from pathlib import Path

def render_job_submission_page():
    """Render the job submission page with enhanced job file viewer, editor, and submission."""
    st.header("Job Submission & File Management")
    st.markdown("""
    **Generate calculation files, browse directories, and submit jobs.**
    
    - **Generate Files (Dry Run)**: Create input and job files from your configuration without submitting
    - **File Browser**: Browse, view, and edit existing calculation files
    - **Job Submission**: Submit existing jobs to your scheduler
    """)
    
    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["📂 File Browser", "🧪 Generate Files (Dry Run)", "🚀 Job Submission"])
    
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
        st.info("🧪 **Dry Run Mode** - Generating files without submission...")
        
        with st.spinner("Generating files..."):
            try:
                from xespresso.gui.utils.dry_run import generate_input_files
                from xespresso import Espresso
                
                # Build calculator parameters
                calc_params = {
                    'pseudopotentials': config['pseudopotentials'],
                    'ecutwfc': config.get('ecutwfc', 50),
                    'ecutrho': config.get('ecutrho', 400),
                    'occupations': config.get('occupations', 'smearing'),
                    'label': label,
                }
                
                # Add k-points
                if 'kspacing' in config:
                    calc_params['kspacing'] = config['kspacing']
                elif 'kpts' in config:
                    calc_params['kpts'] = config['kpts']
                
                # Add smearing if applicable
                if config.get('occupations') == 'smearing':
                    calc_params['smearing'] = config.get('smearing', 'gaussian')
                    calc_params['degauss'] = config.get('degauss', 0.02)
                
                # Add convergence threshold
                if 'conv_thr' in config:
                    calc_params['conv_thr'] = config['conv_thr']
                
                # Add spin polarization
                if 'nspin' in config:
                    calc_params['nspin'] = config['nspin']
                
                # Add calculation type
                calc_type = config.get('calc_type', 'scf')
                if calc_type in ['relax', 'vc-relax']:
                    calc_params['calculation'] = calc_type
                else:
                    calc_params['calculation'] = 'scf'
                
                # Add machine/queue if available
                if machine and hasattr(machine, 'queue'):
                    calc_params['queue'] = machine.queue
                
                # Generate files
                result = generate_input_files(
                    atoms=atoms,
                    calc_params=calc_params,
                    workdir=full_path,
                    structure_filename=f"{atoms.get_chemical_formula()}.cif"
                )
                
                if result:
                    st.success("✅ Files generated successfully!")
                    
                    # Display results
                    st.subheader("📄 Generated Files")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Files created:**")
                        if 'structure' in result:
                            st.markdown(f"- ✅ Structure: `{os.path.basename(result['structure'])}`")
                        if 'input' in result:
                            st.markdown(f"- ✅ Input file: `{os.path.basename(result['input'])}`")
                        if 'job_file' in result:
                            st.markdown(f"- ✅ Job script: `{os.path.basename(result['job_file'])}`")
                    
                    with col2:
                        st.write("**Location:**")
                        st.code(result['workdir'])
                    
                    st.markdown("---")
                    
                    # Preview input file
                    if 'input' in result and os.path.exists(result['input']):
                        st.subheader("👁️ Input File Preview")
                        try:
                            # Validate path is under full_path for security
                            input_path = os.path.realpath(result['input'])
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
                                        file_name=os.path.basename(result['input']),
                                        mime="text/plain"
                                    )
                        except Exception as e:
                            st.error(f"Error reading input file: {e}")
                    
                    # Preview job file
                    if 'job_file' in result and os.path.exists(result['job_file']):
                        st.subheader("👁️ Job Script Preview")
                        try:
                            # Validate path is under full_path for security
                            job_path = os.path.realpath(result['job_file'])
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
                                        file_name=os.path.basename(result['job_file']),
                                        mime="text/plain"
                                    )
                        except Exception as e:
                            st.error(f"Error reading job file: {e}")
                    
                    st.markdown("---")
                    
                    # Next steps
                    st.subheader("✨ Next Steps")
                    st.info("""
                    **Files have been generated!** You can now:
                    
                    1. **Review the files** using the File Browser tab above
                    2. **Edit the files** if needed (use Edit mode in File Browser)
                    3. **Submit the job** using the Job Submission tab
                    4. **Transfer files** to another system if needed
                    
                    The generated files are ready to run - no additional configuration needed!
                    """)
                
                else:
                    st.error("❌ Failed to generate files. Check the error messages above.")
                    
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
    """Render the job submission tab for submitting calculations."""
    st.subheader("🚀 Submit Calculation Job")
    st.markdown("""
    Submit a job to run a calculation. You can either do a dry run (generate files only) 
    or actually submit the job to a scheduler.
    """)
    
    # Working directory selection
    try:
        from xespresso.gui.utils.selectors import render_workdir_browser
        workdir = render_workdir_browser(key="job_submit_workdir")
    except ImportError:
        workdir = st.text_input("Working Directory:", value=os.getcwd(), key="job_submit_workdir_input")
        workdir = os.path.abspath(os.path.expanduser(workdir))
    
    # Find calculation folders with job files
    st.markdown("---")
    st.subheader("📂 Select Calculation to Submit")
    
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
    
    calc_folders_with_jobs = []
    try:
        for root, dirs, files in os.walk(workdir, topdown=True):
            # Ensure we stay within workdir (prevent symlink attacks)
            try:
                if not os.path.realpath(root).startswith(workdir):
                    continue
            except (OSError, ValueError):
                continue
                
            depth = root[len(workdir):].count(os.sep)
            if depth < 4:
                # Check for job files
                has_job_file = any(f == 'job_file' or f.endswith(('.sh', '.slurm')) for f in files)
                # Check for input files
                has_input = any(f.endswith(('.pwi', '.phi', '.ppi', '.in')) for f in files)
                if has_job_file and has_input:
                    calc_folders_with_jobs.append(root)
        
        if calc_folders_with_jobs:
            st.success(f"✅ Found {len(calc_folders_with_jobs)} calculation(s) ready for submission")
            
            selected_calc = st.selectbox(
                "Select calculation:",
                calc_folders_with_jobs,
                format_func=lambda x: os.path.relpath(x, workdir) if x != workdir else ".",
                key="submit_calc_selector"
            )
            
            if selected_calc:
                st.info(f"📍 Selected: `{os.path.relpath(selected_calc, workdir)}`")
                
                # Show files in the calculation folder
                files = os.listdir(selected_calc)
                job_files = [f for f in files if f == 'job_file' or f.endswith(('.sh', '.slurm'))]
                input_files = [f for f in files if f.endswith(('.pwi', '.phi', '.ppi', '.in'))]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Job Scripts:**")
                    for jf in job_files:
                        st.markdown(f"- `{jf}`")
                with col2:
                    st.markdown("**Input Files:**")
                    for inf in input_files:
                        st.markdown(f"- `{inf}`")
                
                st.markdown("---")
                
                # Submission options
                st.subheader("⚙️ Submission Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    dry_run = st.checkbox(
                        "🧪 Dry Run (don't actually submit)",
                        value=False,
                        help="If checked, will only validate files without submitting the job"
                    )
                
                with col2:
                    if job_files:
                        selected_job_file = st.selectbox(
                            "Job script to use:",
                            job_files,
                            key="selected_job_script"
                        )
                    else:
                        selected_job_file = None
                        st.warning("No job files found")
                
                # Submission button
                st.markdown("---")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    submit_button = st.button(
                        "🚀 Submit Job" if not dry_run else "🧪 Validate (Dry Run)",
                        type="primary",
                        disabled=(selected_job_file is None),
                        key="submit_job_button"
                    )
                
                if submit_button and selected_job_file:
                    job_file_path = os.path.join(selected_calc, selected_job_file)
                    
                    if dry_run:
                        # Dry run - just validate files
                        st.info("🧪 **Dry Run Mode** - Validating files...")
                        
                        with st.spinner("Validating..."):
                            try:
                                # Check if files exist and are readable
                                validation_results = []
                                
                                # Check job file
                                if os.path.exists(job_file_path):
                                    with open(job_file_path, 'r') as f:
                                        job_content = f.read()
                                    validation_results.append(("✅", "Job script", f"{selected_job_file} ({len(job_content)} bytes)"))
                                else:
                                    validation_results.append(("❌", "Job script", f"{selected_job_file} not found"))
                                
                                # Check input files
                                for inf in input_files:
                                    inf_path = os.path.join(selected_calc, inf)
                                    if os.path.exists(inf_path):
                                        file_size = os.path.getsize(inf_path)
                                        validation_results.append(("✅", "Input file", f"{inf} ({file_size} bytes)"))
                                    else:
                                        validation_results.append(("❌", "Input file", f"{inf} not found"))
                                
                                # Display validation results
                                st.success("✅ Validation complete!")
                                st.subheader("Validation Results")
                                
                                for status, file_type, details in validation_results:
                                    st.markdown(f"{status} **{file_type}:** {details}")
                                
                                # Show what would be submitted
                                st.markdown("---")
                                st.subheader("📋 Job Submission Preview")
                                st.info(f"""
                                **Job would be submitted with the following details:**
                                - **Working Directory:** `{selected_calc}`
                                - **Job Script:** `{selected_job_file}`
                                - **Input Files:** {len(input_files)} file(s)
                                - **Command:** `bash {selected_job_file}` (or `sbatch {selected_job_file}` for SLURM)
                                """)
                                
                                # Preview job script content
                                with st.expander("👁️ View Job Script"):
                                    st.code(job_content, language="bash", line_numbers=True)
                                
                            except Exception as e:
                                st.error(f"❌ Validation error: {e}")
                                import traceback
                                with st.expander("Error Details"):
                                    st.code(traceback.format_exc())
                    
                    else:
                        # Actually submit the job
                        st.warning("⚠️ **Live Submission** - Job will be submitted to scheduler")
                        
                        with st.spinner("Submitting job..."):
                            try:
                                import subprocess
                                
                                # Determine submission command
                                if 'slurm' in selected_job_file.lower() or any('SBATCH' in line for line in open(job_file_path).readlines()):
                                    submit_cmd = f"sbatch {selected_job_file}"
                                else:
                                    submit_cmd = f"bash {selected_job_file}"
                                
                                # Submit the job
                                result = subprocess.run(
                                    submit_cmd,
                                    shell=True,
                                    cwd=selected_calc,
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                
                                if result.returncode == 0:
                                    st.success("✅ Job submitted successfully!")
                                    st.subheader("Submission Output")
                                    st.code(result.stdout)
                                    
                                    # Try to extract job ID for SLURM
                                    if 'sbatch' in submit_cmd:
                                        import re
                                        match = re.search(r'Submitted batch job (\d+)', result.stdout)
                                        if match:
                                            job_id = match.group(1)
                                            st.info(f"🎫 **Job ID:** {job_id}")
                                            st.markdown(f"Monitor with: `squeue -j {job_id}`")
                                else:
                                    st.error("❌ Job submission failed!")
                                    st.subheader("Error Output")
                                    st.code(result.stderr)
                                
                            except subprocess.TimeoutExpired:
                                st.error("❌ Job submission timed out (30s)")
                            except Exception as e:
                                st.error(f"❌ Submission error: {e}")
                                import traceback
                                with st.expander("Error Details"):
                                    st.code(traceback.format_exc())
        
        else:
            st.warning("⚠️ No calculation folders with job scripts found")
            st.info("""
            **To submit a job, you need:**
            1. A calculation folder with input files (`.pwi`, `.in`, etc.)
            2. A job script (`job_file`, `*.sh`, or `*.slurm`)
            
            You can create these using the Calculation Setup page or by using the File Browser tab above.
            """)
    
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
