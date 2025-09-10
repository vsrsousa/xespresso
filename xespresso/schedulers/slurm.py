from .base import BaseScheduler
from typing import Dict, List, Optional, Any
import tempfile
import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class SlurmScheduler(BaseScheduler):
    """Slurm scheduler implementation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_script_template = """#!/bin/bash -l
#SBATCH --job-name={job_name}
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-node={cores_per_node}
#SBATCH --time={time}
#SBATCH --partition={partition}
#SBATCH --output={job_name}.%j.out
#SBATCH --error={job_name}.%j.err
"""
    
    def generate_script(self, commands: List[str]) -> str:
        """Generate Slurm job script"""
        cores_per_node = self.cores // self.nodes
        
        script = self.job_script_template.format(
            job_name=self.job_name,
            nodes=self.nodes,
            cores_per_node=cores_per_node,
            time=self.time,
            partition=self.partition
        )
        
        # Add memory if specified
        if self.memory:
            script += f"#SBATCH --mem={self.memory}\n"
        
        # Add account if specified
        if self.account:
            script += f"#SBATCH --account={self.account}\n"
        
        # Add email notifications if specified
        if self.email:
            script += f"#SBATCH --mail-user={self.email}\n"
            script += f"#SBATCH --mail-type={self.email_events}\n"
        
        # Add any extra SBATCH parameters
        for key, value in self.extra_params.items():
            if key.startswith('sbatch_'):
                param_name = key.replace('sbatch_', '--')
                script += f"#SBATCH {param_name}={value}\n"
        
        script += "\n# Environment setup\n"
        script += "echo \"Starting job at $(date)\"\n"
        script += "echo \"Working directory: $(pwd)\"\n"
        script += "echo \"Job ID: $SLURM_JOB_ID\"\n\n"
        
        # Add commands
        script += "# Job commands\n"
        for cmd in commands:
            script += f"{cmd}\n"
        
        script += "\n# Cleanup\n"
        script += "echo \"Job completed at $(date)\"\n"
        
        return script
    
    def submit_job(self, script_content: str, script_name: str = "job.sh") -> Dict[str, Any]:
        """Submit job to Slurm scheduler"""
        try:
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                temp_script = f.name
            
            # Make script executable
            os.chmod(temp_script, 0o755)
            
            # Submit job
            result = subprocess.run(
                ['sbatch', temp_script],
                capture_output=True,
                text=True,
                cwd=self.working_dir
            )
            
            # Clean up
            os.unlink(temp_script)
            
            # Parse output
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode == 0:
                # Extract job ID from output
                job_id = None
                if "Submitted batch job" in output:
                    job_id = output.split()[-1]
                
                return {
                    'success': True,
                    'job_id': job_id,
                    'output': output,
                    'error': error
                }
            else:
                return {
                    'success': False,
                    'job_id': None,
                    'output': output,
                    'error': error,
                    'returncode': result.returncode
                }
                
        except Exception as e:
            logger.error(f"Error submitting Slurm job: {e}")
            return {
                'success': False,
                'error': str(e),
                'job_id': None
            }