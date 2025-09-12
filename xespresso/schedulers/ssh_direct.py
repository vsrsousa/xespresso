from .base import BaseScheduler
import paramiko
from typing import Dict, List, Optional, Any
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SSHDirectScheduler(BaseScheduler):
    """Direct SSH execution without job managers (Slurm/PBS)"""
    
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
        self.remote_dir = remote_dir or f"/home/{username}/direct_jobs"
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
        """Ensure remote directory exists recursively"""
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
    
    def upload_file(self, local_path: str, remote_path: str):
        """Upload a file to remote server"""
        remote_dir = os.path.dirname(remote_path)
        if remote_dir:
            self.ensure_remote_dir(remote_dir)
        
        self.sftp.put(local_path, remote_path)
    
    def upload_directory(self, local_dir: str, remote_dir: str):
        """Upload entire directory recursively"""
        self.ensure_remote_dir(remote_dir)
        
        for root, dirs, files in os.walk(local_dir):
            # Create corresponding remote directories
            remote_root = root.replace(local_dir, remote_dir, 1)
            self.ensure_remote_dir(remote_root)
            
            # Upload files
            for file in files:
                local_file = os.path.join(root, file)
                remote_file = os.path.join(remote_root, file)
                self.upload_file(local_file, remote_file)
    
    def execute_command(self, command: str, wait: bool = True) -> Dict[str, Any]:
        """Execute command on remote server"""
        if not self.ssh_client:
            self.connect()
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            
            if wait:
                exit_code = stdout.channel.recv_exit_status()
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                return {
                    'success': exit_code == 0,
                    'exit_code': exit_code,
                    'output': output,
                    'error': error,
                    'command': command
                }
            else:
                # For non-blocking execution
                return {
                    'success': True,
                    'command': command,
                    'stdin': stdin,
                    'stdout': stdout,
                    'stderr': stderr
                }
                
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                'success': False,
                'error': str(e),
                'command': command
            }
    
    def generate_script(self, commands: List[str]) -> str:
        """Generate a shell script for direct execution"""
        script = "#!/bin/bash\n\n"
        script += f"cd {self.working_dir}\n\n"
        script += "echo \"Starting direct execution at $(date)\"\n"
        script += "echo \"Working directory: $(pwd)\"\n\n"
        
        for cmd in commands:
            script += f"{cmd}\n"
        
        script += "\necho \"Execution completed at $(date)\"\n"
        return script
    
    def submit_job(self, script_content: str, script_name: str = "direct_job.sh") -> Dict[str, Any]:
        """Execute commands directly via SSH (no job manager)"""
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
            self.execute_command(f"chmod +x {remote_script_path}")
            
            # Execute script
            execute_cmd = f"cd {self.remote_dir} && ./{script_name}"
            result = self.execute_command(execute_cmd)
            
            result['remote_script_path'] = remote_script_path
            return result
            
        except Exception as e:
            logger.error(f"Error in direct SSH execution: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_direct(self, 
                  commands: List[str],
                  modules: Optional[List[str]] = None,
                  background: bool = False) -> Dict[str, Any]:
        """
        Run commands directly without creating a script file
        
        Args:
            commands: List of commands to execute
            modules: List of modules to load
            background: Whether to run in background (non-blocking)
        """
        # Prepare environment
        all_commands = []
        
        if modules:
            for module in modules:
                all_commands.append(f"module load {module}")
        
        all_commands.append(f"cd {self.working_dir}")
        all_commands.extend(commands)
        
        # Execute commands
        full_command = " && ".join(all_commands)
        
        if background:
            # Run in background with nohup
            full_command = f"nohup bash -c '{full_command}' > {self.remote_dir}/nohup.out 2>&1 &"
        
        return self.execute_command(full_command, wait=not background)
    
    def close(self):
        """Close SSH connection"""
        if self.sftp:
            self.sftp.close()
        if self.ssh_client:
            self.ssh_client.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __del__(self):
        self.close()