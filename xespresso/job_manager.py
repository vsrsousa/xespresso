"""
Advanced Remote Job Manager for xespresso
Leverages the new scheduler architecture for comprehensive job management
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import os
import logging
import time
from datetime import datetime
import json

from .schedulers import (
    get_scheduler, 
    BaseScheduler,
    SlurmScheduler,
    PBSScheduler, 
    SSHDirectScheduler,
    RemoteSlurmScheduler
)

logger = logging.getLogger(__name__)

class RemoteJobManager:
    """
    Advanced remote job manager that provides high-level interface
    for job submission, monitoring, and management using the scheduler system
    """
    
    def __init__(self, 
                 scheduler_type: str = 'slurm',
                 hostname: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 key_filename: Optional[str] = None,
                 remote_dir: Optional[str] = None,
                 working_dir: Optional[str] = None,
                 port: Optional[int] = 22,
                 **scheduler_kwargs):
        """
        Initialize remote job manager
        
        Args:
            scheduler_type: Type of scheduler ('slurm', 'pbs', 'ssh_direct', 'remote_slurm', 'local')
            hostname: Remote hostname (required for remote schedulers)
            port: ssh remote port (required for remote schedulers, using default value: 22)
            username: Remote username (required for remote schedulers)
            password: SSH password (optional if using key-based auth)
            key_filename: Path to SSH private key
            remote_dir: Base remote directory for job files
            working_dir: Working directory for job execution
            **scheduler_kwargs: Additional scheduler-specific parameters
        """
        self.scheduler_type = scheduler_type.lower()
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.remote_dir = remote_dir
        self.working_dir = working_dir
        self.scheduler_kwargs = scheduler_kwargs
        
        self.scheduler = None
        self.job_history = []
        self.active_jobs = {}
        
        self._initialize_scheduler()
    
    def _initialize_scheduler(self):
        """Initialize the appropriate scheduler based on type"""
        common_kwargs = {
            'job_name': f'xespresso_job_{int(time.time())}',
            'working_dir': self.working_dir,
            **self.scheduler_kwargs
        }
        
        if self.scheduler_type in ['ssh_direct', 'remote_slurm']:
            if not self.hostname or not self.username:
                raise ValueError("hostname and username are required for remote schedulers")
            
            remote_kwargs = {
                'hostname': self.hostname,
                'port': self.port,
                'username': self.username,
                'password': self.password,
                'key_filename': self.key_filename,
                'remote_dir': self.remote_dir or f"/home/{self.username}/xespresso_jobs",
                **common_kwargs
            }
            
            if self.scheduler_type == 'ssh_direct':
                self.scheduler = SSHDirectScheduler(**remote_kwargs)
            else:  # remote_slurm
                self.scheduler = RemoteSlurmScheduler(**remote_kwargs)
                
        else:  # local, slurm, pbs
            if self.scheduler_type == 'local':
                from .schedulers.local import LocalScheduler
                self.scheduler = LocalScheduler(**common_kwargs)
            else:
                self.scheduler = get_scheduler(self.scheduler_type, **common_kwargs)
    
    def connect(self):
        """Establish connection to remote server (if applicable)"""
        if hasattr(self.scheduler, 'connect'):
            self.scheduler.connect()
        return self
    
    def disconnect(self):
        """Close connections"""
        if hasattr(self.scheduler, 'close'):
            self.scheduler.close()
    
    def submit_job(self,
                  commands: Union[str, List[str]],
                  job_name: Optional[str] = None,
                  modules: Optional[List[str]] = None,
                  input_files: Optional[List[str]] = None,
                  output_files: Optional[List[str]] = None,
                  script_name: str = "job.sh",
                  wait_for_completion: bool = False,
                  timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Submit a job with comprehensive file management
        
        Args:
            commands: Commands to execute
            job_name: Custom job name
            modules: Modules to load
            input_files: Files to upload before job execution
            output_files: Files to download after job completion
            script_name: Name of the job script
            wait_for_completion: Whether to wait for job completion
            timeout: Timeout in seconds for waiting
        
        Returns:
            Job submission result
        """
        # Set custom job name if provided
        if job_name and hasattr(self.scheduler, 'job_name'):
            self.scheduler.job_name = job_name
        
        # Upload input files if specified
        if input_files and hasattr(self.scheduler, 'upload_file'):
            self._upload_files(input_files)
        
        # Submit the job
        result = self.scheduler.run(commands, modules, script_name)
        
        # Record job information
        job_info = {
            'job_id': result.get('job_id'),
            'job_name': job_name or getattr(self.scheduler, 'job_name', 'unknown'),
            'submission_time': datetime.now().isoformat(),
            'commands': commands,
            'result': result,
            'status': 'submitted'
        }
        
        self.job_history.append(job_info)
        if job_info['job_id']:
            self.active_jobs[job_info['job_id']] = job_info
        
        # Wait for completion if requested
        if wait_for_completion and job_info['job_id']:
            result = self.wait_for_job(job_info['job_id'], timeout)
            
            # Download output files after completion
            if output_files and result.get('success', False):
                self._download_files(output_files)
        
        return job_info
    
    def submit_espresso_job(self,
                           input_file: str,
                           executable: str = "pw.x",
                           modules: Optional[List[str]] = None,
                           mpi_processes: Optional[int] = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Specialized method for Quantum ESPRESSO jobs
        
        Args:
            input_file: QE input file
            executable: QE executable (pw.x, ph.x, etc.)
            modules: Modules to load
            mpi_processes: Number of MPI processes
            **kwargs: Additional arguments for submit_job
        """
        # Upload input file
        input_files = [input_file]
        
        # Determine output file name
        output_file = input_file.replace('.in', '.out')
        output_files = [output_file]
        
        # Build execution command
        if mpi_processes and self.scheduler_type != 'ssh_direct':
            command = f"mpirun -np {mpi_processes} {executable} < {os.path.basename(input_file)} > {os.path.basename(output_file)}"
        else:
            command = f"{executable} < {os.path.basename(input_file)} > {os.path.basename(output_file)}"
        
        # Default modules for QE
        if modules is None:
            modules = ["quantum-espresso"]
        
        return self.submit_job(
            commands=[command],
            modules=modules,
            input_files=input_files,
            output_files=output_files,
            **kwargs
        )
    
    def _upload_files(self, files: List[str]):
        """Upload files to remote server"""
        if not hasattr(self.scheduler, 'upload_file'):
            logger.warning("Scheduler does not support file upload")
            return
        
        for file_path in files:
            if os.path.exists(file_path):
                remote_path = os.path.join(self.scheduler.working_dir, os.path.basename(file_path))
                self.scheduler.upload_file(file_path, remote_path)
                logger.info(f"Uploaded {file_path} to {remote_path}")
            else:
                logger.warning(f"File not found: {file_path}")
    
    def _download_files(self, files: List[str], local_dir: Optional[str] = None):
        """Download files from remote server"""
        if not hasattr(self.scheduler, 'download_file'):
            logger.warning("Scheduler does not support file download")
            return
        
        local_dir = local_dir or os.getcwd()
        
        for file_path in files:
            remote_path = os.path.join(self.scheduler.working_dir, os.path.basename(file_path))
            local_path = os.path.join(local_dir, os.path.basename(file_path))
            
            try:
                self.scheduler.download_file(remote_path, local_path)
                logger.info(f"Downloaded {remote_path} to {local_path}")
            except Exception as e:
                logger.error(f"Failed to download {remote_path}: {e}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current status of a job"""
        if hasattr(self.scheduler, 'check_job_status'):
            return self.scheduler.check_job_status(job_id)
        
        # Fallback for schedulers without status checking
        return {'status': 'unknown', 'job_id': job_id}
    
    def wait_for_job(self, job_id: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Wait for job completion with timeout
        
        Args:
            job_id: Job ID to wait for
            timeout: Maximum time to wait in seconds
        
        Returns:
            Final job status
        """
        start_time = time.time()
        poll_interval = 30  # seconds
        
        while True:
            status = self.get_job_status(job_id)
            
            # Check if job is completed
            if status.get('status') in ['COMPLETED', 'FAILED', 'CANCELLED']:
                # Update job history
                for job in self.job_history:
                    if job['job_id'] == job_id:
                        job['completion_time'] = datetime.now().isoformat()
                        job['status'] = status['status']
                        job['final_status'] = status
                        break
                
                # Remove from active jobs
                self.active_jobs.pop(job_id, None)
                
                return status
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
            
            # Wait before polling again
            time.sleep(poll_interval)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if hasattr(self.scheduler, 'cancel_job'):
            return self.scheduler.cancel_job(job_id)
        
        # Generic cancellation for systems with scancel/qdel
        if self.scheduler_type in ['slurm', 'remote_slurm']:
            result = self.scheduler.execute_command(f"scancel {job_id}")
            return result['success']
        elif self.scheduler_type == 'pbs':
            result = self.scheduler.execute_command(f"qdel {job_id}")
            return result['success']
        
        logger.warning(f"Cancellation not supported for scheduler type: {self.scheduler_type}")
        return False
    
    def get_job_output(self, job_id: str, output_file: str = "slurm.out") -> str:
        """Get job output content"""
        if hasattr(self.scheduler, 'get_job_output'):
            return self.scheduler.get_job_output(job_id, output_file)
        
        # Fallback: try to read output file
        try:
            output_path = os.path.join(self.scheduler.working_dir, output_file)
            if hasattr(self.scheduler, 'read_file'):
                return self.scheduler.read_file(output_path)
        except Exception as e:
            logger.error(f"Failed to read job output: {e}")
        
        return ""
    
    def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List jobs with optional status filter"""
        if status:
            return [job for job in self.job_history if job.get('status') == status]
        return self.job_history
    
    def cleanup(self, remove_files: bool = False):
        """Clean up job files and connections"""
        if remove_files and hasattr(self.scheduler, 'working_dir'):
            # Clean up working directory
            try:
                self.scheduler.execute_command(f"rm -rf {self.scheduler.working_dir}/*")
            except Exception as e:
                logger.warning(f"Failed to clean up directory: {e}")
        
        self.disconnect()
    
    def save_state(self, filepath: str):
        """Save job manager state to file"""
        state = {
            'job_history': self.job_history,
            'active_jobs': self.active_jobs,
            'scheduler_type': self.scheduler_type,
            'hostname': self.hostname,
            'username': self.username,
            'remote_dir': self.remote_dir,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str):
        """Load job manager state from file"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.job_history = state.get('job_history', [])
            self.active_jobs = state.get('active_jobs', {})
            
            # Reinitialize scheduler if needed
            if state.get('scheduler_type') != self.scheduler_type:
                self.scheduler_type = state['scheduler_type']
                self._initialize_scheduler()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def __del__(self):
        self.cleanup()


# Utility function for quick job submission
def submit_remote_job(commands: Union[str, List[str]],
                     scheduler_type: str = 'slurm',
                     **kwargs) -> Dict[str, Any]:
    """
    Quick function for submitting remote jobs
    
    Args:
        commands: Commands to execute
        scheduler_type: Type of scheduler to use
        **kwargs: Additional arguments for RemoteJobManager
    
    Returns:
        Job submission result
    """
    with RemoteJobManager(scheduler_type=scheduler_type, **kwargs) as manager:
        return manager.submit_job(commands)