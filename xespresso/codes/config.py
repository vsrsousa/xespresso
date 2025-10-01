"""
config.py

Data structures for Quantum ESPRESSO code configuration.
"""

import json
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict, field


@dataclass
class Code:
    """
    Represents a single Quantum ESPRESSO executable.
    
    Attributes:
        name: Code name (e.g., 'pw', 'hp', 'dos', 'bands')
        path: Full path to executable (e.g., '/usr/bin/pw.x')
        version: QE version string (e.g., '7.2', '6.8')
        parallel_command: Optional MPI command prefix (e.g., 'mpirun -np {nprocs}')
        default_parallel: Default parallelization options (e.g., '-nk 4')
    """
    name: str
    path: str
    version: Optional[str] = None
    parallel_command: Optional[str] = None
    default_parallel: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Code':
        """Create Code from dictionary."""
        return cls(**data)


@dataclass
class CodesConfig:
    """
    Configuration for all QE codes on a machine.
    
    Attributes:
        machine_name: Name of the machine
        qe_prefix: Common prefix for QE executables (e.g., '/opt/qe-7.2/bin')
        qe_version: Default QE version on this machine
        codes: Dictionary mapping code name to Code object
        modules: Optional list of modules to load (e.g., ['quantum-espresso/7.2'])
        environment: Optional environment variables to set
    """
    machine_name: str
    codes: Dict[str, Code] = field(default_factory=dict)
    qe_prefix: Optional[str] = None
    qe_version: Optional[str] = None
    modules: Optional[List[str]] = None
    environment: Optional[Dict[str, str]] = None
    
    def add_code(self, code: Code):
        """Add a code to the configuration."""
        self.codes[code.name] = code
    
    def get_code(self, name: str) -> Optional[Code]:
        """Get a code by name."""
        return self.codes.get(name)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = {
            'machine_name': self.machine_name,
            'codes': {name: code.to_dict() for name, code in self.codes.items()},
        }
        if self.qe_prefix:
            result['qe_prefix'] = self.qe_prefix
        if self.qe_version:
            result['qe_version'] = self.qe_version
        if self.modules:
            result['modules'] = self.modules
        if self.environment:
            result['environment'] = self.environment
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CodesConfig':
        """Create CodesConfig from dictionary."""
        codes_data = data.pop('codes', {})
        codes = {name: Code.from_dict(code_data) for name, code_data in codes_data.items()}
        return cls(codes=codes, **data)
    
    def to_json(self, filepath: str, indent: int = 2):
        """Save to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent)
    
    @classmethod
    def from_json(cls, filepath: str) -> 'CodesConfig':
        """Load from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def list_codes(self) -> List[str]:
        """List all available code names."""
        return list(self.codes.keys())
    
    def has_code(self, name: str) -> bool:
        """Check if a code is available."""
        return name in self.codes
