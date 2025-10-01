"""
manager.py

Utilities for managing Quantum ESPRESSO code configurations.
"""

import os
import re
import json
import subprocess
from typing import Dict, Optional, List, Union
from pathlib import Path

from .config import Code, CodesConfig

# Common QE executable names
COMMON_QE_CODES = [
    'pw', 'ph', 'pp', 'projwfc', 'dos', 'bands', 
    'neb', 'hp', 'dynmat', 'matdyn', 'q2r',
    'pwcond', 'turbo_lanczos', 'turbo_davidson',
]

DEFAULT_CODES_DIR = os.path.expanduser("~/.xespresso/codes")


class CodesManager:
    """
    Manager for Quantum ESPRESSO code configurations.
    
    This class provides utilities to:
    - Detect available QE codes on a machine
    - Create and manage code configurations
    - Load and save code configurations
    """
    
    def __init__(self, config: Optional[CodesConfig] = None):
        """
        Initialize CodesManager.
        
        Args:
            config: Optional CodesConfig object
        """
        self.config = config
    
    @classmethod
    def detect_codes(cls, 
                     search_paths: Optional[List[str]] = None,
                     qe_prefix: Optional[str] = None,
                     modules: Optional[List[str]] = None,
                     ssh_connection: Optional[Dict] = None) -> Dict[str, str]:
        """
        Detect available QE codes on the system.
        
        Args:
            search_paths: List of paths to search for executables
            qe_prefix: QE installation prefix (e.g., '/opt/qe-7.2/bin')
            modules: List of modules to load before detection
            ssh_connection: SSH connection info for remote detection
                           {'host': 'hostname', 'username': 'user'}
        
        Returns:
            Dictionary mapping code name to executable path
        """
        detected_codes = {}
        
        # Build search paths
        if qe_prefix:
            if not search_paths:
                search_paths = []
            search_paths.insert(0, qe_prefix)
        
        if not search_paths:
            # Use PATH environment variable
            path_env = os.environ.get('PATH', '')
            search_paths = path_env.split(':')
        
        # Build module load command if needed
        module_cmd = ""
        if modules:
            module_cmd = " && ".join([f"module load {mod}" for mod in modules])
            module_cmd += " && "
        
        # Check for each common QE code
        for code_name in COMMON_QE_CODES:
            executable = f"{code_name}.x"
            
            if ssh_connection:
                # Remote detection
                found_path = cls._detect_remote(executable, search_paths, 
                                                module_cmd, ssh_connection)
            else:
                # Local detection
                found_path = cls._detect_local(executable, search_paths, module_cmd)
            
            if found_path:
                detected_codes[code_name] = found_path
        
        return detected_codes
    
    @staticmethod
    def _detect_local(executable: str, search_paths: List[str], 
                     module_cmd: str = "") -> Optional[str]:
        """Detect executable on local machine."""
        # Try using 'which' command
        try:
            cmd = f"{module_cmd}which {executable}"
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=10)
            if result.returncode == 0:
                path = result.stdout.strip()
                if path and os.path.exists(path):
                    return path
        except (subprocess.TimeoutExpired, Exception):
            pass
        
        # Manual search in paths
        for search_path in search_paths:
            full_path = os.path.join(search_path, executable)
            if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                return full_path
        
        return None
    
    @staticmethod
    def _detect_remote(executable: str, search_paths: List[str],
                      module_cmd: str, ssh_connection: Dict) -> Optional[str]:
        """Detect executable on remote machine via SSH."""
        try:
            host = ssh_connection.get('host')
            username = ssh_connection.get('username', os.environ.get('USER'))
            
            # Try using 'which' command remotely
            cmd = f"ssh {username}@{host} '{module_cmd}which {executable}'"
            result = subprocess.run(cmd, shell=True, capture_output=True,
                                  text=True, timeout=30)
            if result.returncode == 0:
                path = result.stdout.strip()
                if path:
                    return path
            
            # Try manual search in paths
            for search_path in search_paths:
                full_path = os.path.join(search_path, executable)
                cmd = f"ssh {username}@{host} 'test -x {full_path} && echo {full_path}'"
                result = subprocess.run(cmd, shell=True, capture_output=True,
                                      text=True, timeout=30)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
        
        except (subprocess.TimeoutExpired, Exception):
            pass
        
        return None
    
    @staticmethod
    def detect_qe_version(pw_path: str, ssh_connection: Optional[Dict] = None) -> Optional[str]:
        """
        Detect Quantum ESPRESSO version from pw.x executable.
        
        Args:
            pw_path: Path to pw.x executable
            ssh_connection: SSH connection info for remote detection
        
        Returns:
            Version string (e.g., '7.2') or None
        """
        try:
            if ssh_connection:
                host = ssh_connection.get('host')
                username = ssh_connection.get('username', os.environ.get('USER'))
                cmd = f"ssh {username}@{host} '{pw_path} --version 2>&1 | head -5'"
            else:
                cmd = f"{pw_path} --version 2>&1 | head -5"
            
            result = subprocess.run(cmd, shell=True, capture_output=True,
                                  text=True, timeout=10)
            
            if result.returncode == 0 or result.stderr:
                output = result.stdout + result.stderr
                # Look for version pattern like "7.2" or "6.8"
                match = re.search(r'(\d+\.\d+)', output)
                if match:
                    return match.group(1)
        except (subprocess.TimeoutExpired, Exception):
            pass
        
        return None
    
    @classmethod
    def create_config(cls,
                     machine_name: str,
                     detected_codes: Dict[str, str],
                     qe_version: Optional[str] = None,
                     qe_prefix: Optional[str] = None,
                     modules: Optional[List[str]] = None,
                     environment: Optional[Dict[str, str]] = None) -> CodesConfig:
        """
        Create a CodesConfig from detected codes.
        
        Args:
            machine_name: Name of the machine
            detected_codes: Dictionary mapping code name to path
            qe_version: QE version string
            qe_prefix: QE installation prefix
            modules: List of modules to load
            environment: Environment variables
        
        Returns:
            CodesConfig object
        """
        config = CodesConfig(
            machine_name=machine_name,
            qe_prefix=qe_prefix,
            qe_version=qe_version,
            modules=modules,
            environment=environment
        )
        
        for code_name, code_path in detected_codes.items():
            code = Code(
                name=code_name,
                path=code_path,
                version=qe_version
            )
            config.add_code(code)
        
        return config
    
    @staticmethod
    def save_config(config: CodesConfig, 
                   output_dir: str = DEFAULT_CODES_DIR,
                   filename: Optional[str] = None) -> str:
        """
        Save a CodesConfig to JSON file.
        
        Args:
            config: CodesConfig object to save
            output_dir: Directory to save the file
            filename: Optional filename (default: <machine_name>.json)
        
        Returns:
            Path to saved file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            filename = f"{config.machine_name}.json"
        
        filepath = os.path.join(output_dir, filename)
        config.to_json(filepath)
        
        return filepath
    
    @staticmethod
    def load_config(machine_name: str,
                   codes_dir: str = DEFAULT_CODES_DIR) -> Optional[CodesConfig]:
        """
        Load a CodesConfig from JSON file.
        
        Args:
            machine_name: Name of the machine
            codes_dir: Directory containing codes configurations
        
        Returns:
            CodesConfig object or None if not found
        """
        filepath = os.path.join(codes_dir, f"{machine_name}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            return CodesConfig.from_json(filepath)
        except Exception as e:
            print(f"Error loading codes config: {e}")
            return None


def detect_qe_codes(machine_name: str = "local",
                   qe_prefix: Optional[str] = None,
                   search_paths: Optional[List[str]] = None,
                   modules: Optional[List[str]] = None,
                   ssh_connection: Optional[Dict] = None) -> CodesConfig:
    """
    Convenience function to detect and create a codes configuration.
    
    Args:
        machine_name: Name of the machine
        qe_prefix: QE installation prefix (e.g., '/opt/qe-7.2/bin')
        search_paths: List of paths to search for executables
        modules: List of modules to load before detection
        ssh_connection: SSH connection info for remote detection
    
    Returns:
        CodesConfig object with detected codes
    """
    print(f"🔍 Detecting Quantum ESPRESSO codes on '{machine_name}'...")
    
    detected_codes = CodesManager.detect_codes(
        search_paths=search_paths,
        qe_prefix=qe_prefix,
        modules=modules,
        ssh_connection=ssh_connection
    )
    
    if not detected_codes:
        print("⚠️  No Quantum ESPRESSO codes detected")
        return CodesConfig(machine_name=machine_name)
    
    print(f"✅ Found {len(detected_codes)} codes: {', '.join(detected_codes.keys())}")
    
    # Try to detect QE version from pw.x
    qe_version = None
    if 'pw' in detected_codes:
        qe_version = CodesManager.detect_qe_version(
            detected_codes['pw'], 
            ssh_connection=ssh_connection
        )
        if qe_version:
            print(f"📦 Detected Quantum ESPRESSO version: {qe_version}")
    
    config = CodesManager.create_config(
        machine_name=machine_name,
        detected_codes=detected_codes,
        qe_version=qe_version,
        qe_prefix=qe_prefix,
        modules=modules
    )
    
    return config


def create_codes_config(machine_name: str = "local",
                       qe_prefix: Optional[str] = None,
                       search_paths: Optional[List[str]] = None,
                       modules: Optional[List[str]] = None,
                       ssh_connection: Optional[Dict] = None,
                       save: bool = True,
                       output_dir: str = DEFAULT_CODES_DIR) -> CodesConfig:
    """
    Create a codes configuration (with optional auto-save).
    
    Args:
        machine_name: Name of the machine
        qe_prefix: QE installation prefix
        search_paths: List of paths to search for executables
        modules: List of modules to load before detection
        ssh_connection: SSH connection info for remote detection
        save: Whether to save the configuration to file
        output_dir: Directory to save the configuration
    
    Returns:
        CodesConfig object
    """
    config = detect_qe_codes(
        machine_name=machine_name,
        qe_prefix=qe_prefix,
        search_paths=search_paths,
        modules=modules,
        ssh_connection=ssh_connection
    )
    
    if save and config.codes:
        filepath = CodesManager.save_config(config, output_dir=output_dir)
        print(f"💾 Configuration saved to: {filepath}")
    
    return config


def load_codes_config(machine_name: str,
                     codes_dir: str = DEFAULT_CODES_DIR,
                     version: Optional[str] = None) -> Optional[CodesConfig]:
    """
    Load a codes configuration from file.
    
    Args:
        machine_name: Name of the machine
        codes_dir: Directory containing codes configurations
        version: Optional QE version to use. If None, uses default or main codes.
    
    Returns:
        CodesConfig object or None if not found
    """
    config = CodesManager.load_config(machine_name, codes_dir)
    
    if config:
        versions = config.list_versions()
        if versions:
            print(f"✅ Loaded codes configuration for '{machine_name}'")
            print(f"   Available versions: {', '.join(versions)}")
            
            # Show codes for specified version or default
            target_version = version or config.qe_version or versions[0]
            codes = config.list_codes(version=target_version)
            if codes:
                print(f"   Codes in version {target_version}: {', '.join(codes)}")
        else:
            print(f"✅ Loaded codes configuration for '{machine_name}'")
            print(f"   Available codes: {', '.join(config.list_codes())}")
    else:
        print(f"⚠️  No codes configuration found for '{machine_name}'")
    
    return config


def add_version_to_config(machine_name: str,
                         version: str,
                         qe_prefix: Optional[str] = None,
                         search_paths: Optional[List[str]] = None,
                         modules: Optional[List[str]] = None,
                         ssh_connection: Optional[Dict] = None,
                         codes_dir: str = DEFAULT_CODES_DIR) -> Optional[CodesConfig]:
    """
    Add a new QE version to an existing codes configuration.
    
    This allows managing multiple QE versions on the same machine. Each version
    can have its own set of executables, modules, and environment settings.
    
    Args:
        machine_name: Name of the machine
        version: QE version string (e.g., '7.2', '6.8')
        qe_prefix: QE installation prefix for this version
        search_paths: Paths to search for executables
        modules: Modules to load for this version
        ssh_connection: SSH connection info for remote detection
        codes_dir: Directory containing codes configurations
    
    Returns:
        Updated CodesConfig object or None if machine config doesn't exist
    
    Example:
        # Add QE 7.2 to existing config
        config = add_version_to_config(
            machine_name="cluster1",
            version="7.2",
            qe_prefix="/opt/qe-7.2/bin",
            modules=["quantum-espresso/7.2"]
        )
        
        # Add QE 6.8
        config = add_version_to_config(
            machine_name="cluster1",
            version="6.8",
            qe_prefix="/opt/qe-6.8/bin",
            modules=["quantum-espresso/6.8"]
        )
    """
    # Load existing config
    config = CodesManager.load_config(machine_name, codes_dir)
    
    if not config:
        print(f"⚠️  No codes configuration found for '{machine_name}'")
        print(f"   Creating new configuration...")
        config = CodesConfig(
            machine_name=machine_name,
            qe_version=version  # Set as default version
        )
    
    print(f"🔍 Detecting Quantum ESPRESSO {version} codes on '{machine_name}'...")
    
    # Detect codes for this version
    detected_codes = CodesManager.detect_codes(
        search_paths=search_paths,
        qe_prefix=qe_prefix,
        modules=modules,
        ssh_connection=ssh_connection
    )
    
    if not detected_codes:
        print(f"⚠️  No codes detected for version {version}")
        return config
    
    print(f"✅ Found {len(detected_codes)} codes: {', '.join(detected_codes.keys())}")
    
    # Initialize versions dict if needed
    if not config.versions:
        config.versions = {}
    
    # Add version configuration
    config.versions[version] = {
        'qe_prefix': qe_prefix,
        'modules': modules or [],
        'codes': {}
    }
    
    # Add detected codes to this version
    for code_name, code_path in detected_codes.items():
        code = Code(
            name=code_name,
            path=code_path,
            version=version
        )
        config.add_code(code, version=version)
    
    # Set as default version if not set
    if not config.qe_version:
        config.qe_version = version
        print(f"📌 Set {version} as default version")
    
    # Save updated configuration
    filepath = CodesManager.save_config(config, output_dir=codes_dir)
    print(f"💾 Configuration saved to: {filepath}")
    
    return config
