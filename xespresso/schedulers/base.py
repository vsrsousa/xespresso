from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

class BaseScheduler(ABC):
    """Abstract base class for all schedulers"""
    
    def __init__(self, 
                 job_name: str = "xespresso_job",
                 nodes: int = 1,
                 cores: int = 1,
                 memory: str = "4GB",
                 time: str = "01:00:00",
                 partition: str = "parallel",
                 account: Optional[str] = None,
                 email: Optional[str] = None,
                 email_events: str = "FAIL",
                 working_dir: Optional[str] = None,
                 **kwargs):
        self.job_name = job_name
        self.nodes = nodes
        self.cores = cores
        self.memory = memory
        self.time = time
        self.partition = partition
        self.account = account
        self.email = email
        self.email_events = email_events
        self.working_dir = working_dir or os.getcwd()
        self.extra_params = kwargs
        
    @abstractmethod
    def generate_script(self, commands: List[str]) -> str:
        """Generate scheduler-specific job script"""
        pass
    
    @abstractmethod
    def submit_job(self, script_content: str, script_name: str = "job.sh") -> Dict[str, Any]:
        """Submit job to scheduler"""
        pass
    
    def prepare_environment(self, modules: Optional[List[str]] = None) -> List[str]:
        """Prepare environment commands (module loading, etc.)"""
        env_commands = []
        
        if modules:
            for module in modules:
                env_commands.append(f"module load {module}")
        
        if self.working_dir:
            env_commands.append(f"cd {self.working_dir}")
            
        return env_commands
    
    def create_job_script(self, 
                         commands: List[str], 
                         modules: Optional[List[str]] = None) -> str:
        """Create complete job script with environment setup"""
        env_commands = self.prepare_environment(modules)
        all_commands = env_commands + commands
        
        return self.generate_script(all_commands)
    
    def run(self, 
           commands: List[str], 
           modules: Optional[List[str]] = None,
           script_name: str = "job.sh") -> Dict[str, Any]:
        """Run commands through the scheduler"""
        script_content = self.create_job_script(commands, modules)
        return self.submit_job(script_content, script_name)