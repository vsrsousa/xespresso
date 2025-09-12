from .base import BaseScheduler
from typing import Dict, List, Optional, Any
import subprocess
import logging

logger = logging.getLogger(__name__)

class LocalScheduler(BaseScheduler):
    """Local execution (no scheduler)"""
    
    def generate_script(self, commands: List[str]) -> str:
        """Generate local execution script"""
        script = "#!/bin/bash\n\n"
        script += "echo \"Starting local execution at $(date)\"\n"
        script += f"cd {self.working_dir}\n\n"
        
        for cmd in commands:
            script += f"{cmd}\n"
        
        script += "\necho \"Execution completed at $(date)\"\n"
        return script
    
    def submit_job(self, script_content: str, script_name: str = "job.sh") -> Dict[str, Any]:
        """Execute commands locally"""
        try:
            # Execute commands directly instead of creating a script
            commands = []
            for line in script_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('echo'):
                    commands.append(line)
            
            # Execute each command
            results = []
            for cmd in commands:
                result = subprocess.run(
                    cmd, 
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.working_dir
                )
                results.append({
                    'command': cmd,
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                })
            
            # Check if all commands succeeded
            success = all(result['returncode'] == 0 for result in results)
            
            return {
                'success': success,
                'job_id': 'local_execution',
                'output': '\n'.join([r['stdout'] for r in results]),
                'error': '\n'.join([r['stderr'] for r in results]),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in local execution: {e}")
            return {
                'success': False,
                'error': str(e),
                'job_id': None
            }