"""Job Submission Page for xespresso GUI."""
import streamlit as st
import os
from pathlib import Path

def render_job_submission_page():
    """Render the job submission page with enhanced job file viewer and editor."""
    st.header("Job Submission & File Management")
    st.markdown("""
    Browse calculation directories, view job files, edit input files, and manage your calculations.
    """)
    
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

