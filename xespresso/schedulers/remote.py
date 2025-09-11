from .base import BaseScheduler
from .slurm import SlurmScheduler
import paramiko
from typing import Dict, List, Optional, Any
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

class RemoteSlurmScheduler(SlurmScheduler):
    """Slurm scheduler with remote execution via SSH"""
    
    def __init__(self, 
                 hostname: str,
                 username: str,
                 password: Optional[str] = None,
                 key_filename: Optional[str] = None,
                 remote_dir: Optional[str] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.remote_dir = remote_dir or f"/home/{username}/slurm_jobs"
        self.ssh_client = None
        self.sftp = None
    
    def connect(self):
        """Establish SSH connection"""
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if self.key_filename:
            self.ssh_client.connect(
                self.hostname, 
                username=self.username, 
                key_filename=self.key_filename
            )
        else:
            self.ssh_client.connect(
                self.hostname, 
                username=self.username, 
                password=self.password
            )
        
        self.sftp = self.ssh_client.open_sftp()
        return self
    
    def ensure_remote_dir(self, path: str):
        """Ensure remote directory exists"""
        try:
            self.sftp.chdir(path)
        except IOError:
            dirs = path.split('/')
            current_path = ''
            for dir_name in dirs:
                if not dir_name:
                    continue
                current_path += '/' + dir_name
                try:
                    self.sftp.chdir(current_path)
                except IOError:
                    self.sftp.mkdir(current_path)
                    self.sftp.chdir(current_path)
    
    def submit_job(self, script_content: str, script_name: str = "job.sh") -> Dict[str, Any]:
        """Submit job to remote Slurm scheduler via SSH"""
        if not self.ssh_client:
            self.connect()
        
        try:
            # Ensure remote directory exists
            self.ensure_remote_dir(self.remote_dir)
            
            # Upload script to remote
            remote_script_path = f"{self.remote_dir}/{script_name}"
            with self.sftp.file(remote_script_path, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            self.ssh_client.exec_command(f"chmod +x {remote_script_path}")
            
            # Submit job
            submit_cmd = f"cd {self.remote_dir} && sbatch {script_name}"
            stdin, stdout, stderr = self.ssh_client.exec_command(submit_cmd)
            
            # Get results
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if exit_code == 0:
                job_id = None
                if "Submitted batch job" in output:
                    job_id = output.split()[-1]
                
                return {
                    'success': True,
                    'job_id': job_id,
                    'output': output,
                    'error': error,
                    'remote_script_path': remote_script_path
                }
            else:
                return {
                    'success': False,
                    'job_id': None,
                    'output': output,
                    'error': error,
                    'exit_code': exit_code
                }
                
        except Exception as e:
            logger.error(f"Error submitting remote Slurm job: {e}")
            return {
                'success': False,
                'error': str(e),
                'job_id': None
            }
    
    def close(self):
        """Close SSH connection"""
        if self.sftp:
            self.sftp.close()
        if self.ssh_client:
            self.ssh_client.close()
    
    def __del__(self):
        self.close()