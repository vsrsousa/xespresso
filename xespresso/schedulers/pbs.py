from .base import BaseScheduler
from typing import Dict, List, Optional, Any
import tempfile
import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class PBSScheduler(BaseScheduler):
    """PBS scheduler implementation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_script_template = """#!/bin/bash
#PBS -N {job_name}
#PBS -l nodes={nodes}:ppn={cores_per_node}
#PBS -l walltime={time}
#PBS -q {partition}
#PBS -o {job_name}.$PBS_JOBID.out
#PBS -e {job_name}.$PBS_JOBID.err
"""
    
    def generate_script(self, commands: List[str]) -> str:
        """Generate PBS job script"""
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
            script += f"#PBS -l mem={self.memory}\n"
        
        # Add account if specified
        if self.account:
            script += f"#PBS -A {self.account}\n"
        
        # Add email notifications if specified
        if self.email:
            script += f"#PBS -M {self.email}\n"
            script += f"#PBS -m {self.email_events.lower()}\n"
        
        script += "\n# Environment setup\n"
        script += "echo \"Starting job at $(date)\"\n"
        script += "echo \"Working directory: $(pwd)\"\n"
        script += "echo \"Job ID: $PBS_JOBID\"\n\n"
        
        # Change to working directory
        script += f"cd {self.working_dir}\n\n"
        
        # Add commands
        script += "# Job commands\n"
        for cmd in commands:
            script += f"{cmd}\n"
        
        script += "\n# Cleanup\n"
        script += "echo \"Job completed at $(date)\"\n"
        
        return script
    
    def submit_job(self, script_content: str, script_name: str = "job.sh") -> Dict[str, Any]:
        """Submit job to PBS scheduler"""
        try:
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                temp_script = f.name
            
            # Submit job
            result = subprocess.run(
                ['qsub', temp_script],
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
                job_id = output.split('.')[0] if output else None
                
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
            logger.error(f"Error submitting PBS job: {e}")
            return {
                'success': False,
                'error': str(e),
                'job_id': None
            }