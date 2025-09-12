from typing import Dict, Optional, Type
from .base import BaseScheduler
from .slurm import SlurmScheduler
from .pbs import PBSScheduler
from .local import LocalScheduler
from .ssh_direct import SSHDirectScheduler
from .remote import RemoteSlurmScheduler
import logging

logger = logging.getLogger(__name__)

class SchedulerFactory:
    """Factory class for creating scheduler instances"""
    
    _schedulers = {
        'slurm': SlurmScheduler,
        'pbs': PBSScheduler,
        'local': LocalScheduler,
        'ssh_direct': SSHDirectScheduler,
        'remote_slurm': RemoteSlurmScheduler
    }
    
    @classmethod
    def get_scheduler(cls, 
                     scheduler_type: str = 'slurm',
                     **kwargs) -> BaseScheduler:
        """
        Get scheduler instance by type
        
        Args:
            scheduler_type: Type of scheduler ('slurm', 'pbs', 'local', 'ssh_direct', 'remote_slurm')
            **kwargs: Additional parameters for scheduler initialization
            
        Returns:
            BaseScheduler instance
        """
        scheduler_class = cls._schedulers.get(scheduler_type.lower())
        
        if not scheduler_class:
            raise ValueError(f"Unknown scheduler type: {scheduler_type}. "
                           f"Available types: {list(cls._schedulers.keys())}")
        
        return scheduler_class(**kwargs)
    
    @classmethod
    def register_scheduler(cls, name: str, scheduler_class: Type[BaseScheduler]):
        """Register a new scheduler type"""
        if not issubclass(scheduler_class, BaseScheduler):
            raise TypeError("Scheduler class must inherit from BaseScheduler")
        cls._schedulers[name.lower()] = scheduler_class

# Convenience function
def get_scheduler(scheduler_type: str = 'slurm', **kwargs) -> BaseScheduler:
    return SchedulerFactory.get_scheduler(scheduler_type, **kwargs)