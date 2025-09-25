"""
Tests for machine configuration consistency across different loader modules.

This test file ensures that machine configuration loaders remain consistent
and behave correctly with various configuration scenarios.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch

# Import all machine loaders
from xespresso.utils.machines.machine_config import load_machine as load_machine_main
from xespresso.utils.machines.config.loader import load_machine as load_machine_new
from xespresso.utils.machines.config.old.loader import load_machine as load_machine_old


class TestMachineConfigConsistency:
    """Test consistency across all machine configuration loaders."""
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample machine configuration for testing."""
        return {
            "machines": {
                "test_local": {
                    "execution": "local",
                    "scheduler": "direct",
                    "workdir": "./test_dir",
                    "modules": [],
                    "use_modules": False,
                    "prepend": ["echo 'Starting job'"],
                    "postpend": ["echo 'Job finished'"],
                    "resources": {},
                    "launcher": "mpirun -np {nprocs}",
                    "nprocs": 2
                },
                "test_remote": {
                    "execution": "remote",
                    "scheduler": "slurm",
                    "host": "test.example.com",
                    "username": "testuser",
                    "workdir": "/home/testuser/jobs",
                    "auth": {
                        "method": "key",
                        "ssh_key": "~/.ssh/test_key",
                        "port": 22
                    },
                    "modules": ["module1", "module2"],
                    "use_modules": True,
                    "prepend": "module load gcc",
                    "postpend": "module unload gcc",
                    "resources": {
                        "nodes": 1,
                        "ntasks-per-node": 4,
                        "time": "01:00:00",
                        "partition": "test"
                    },
                    "launcher": "srun -n {nprocs}",
                    "nprocs": 4
                }
            }
        }
    
    @pytest.fixture
    def config_file(self, sample_config):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f, indent=2)
            f.flush()  # Ensure data is written to disk
            config_path = f.name
        yield config_path
        os.unlink(config_path)
    
    def test_all_loaders_return_consistent_defaults(self, config_file):
        """Test that all loaders use consistent default values."""
        loaders = [
            ("machine_config.py", load_machine_main),
            ("config/loader.py", load_machine_new),
            ("config/old/loader.py", load_machine_old)
        ]
        
        results = []
        for loader_name, loader_func in loaders:
            result = loader_func(config_file, "test_local")
            results.append((loader_name, result))
        
        # Check that all loaders return the same scheduler default
        schedulers = [result[1]["scheduler"] for result in results]
        assert all(s == "direct" for s in schedulers), f"Inconsistent scheduler defaults: {schedulers}"
        
        # Check that all loaders have the same execution type
        executions = [result[1]["execution"] for result in results]
        assert all(e == "local" for e in executions), f"Inconsistent execution types: {executions}"
    
    def test_all_loaders_support_required_fields(self, config_file):
        """Test that all loaders support required fields."""
        loaders = [
            ("machine_config.py", load_machine_main),
            ("config/loader.py", load_machine_new), 
            ("config/old/loader.py", load_machine_old)
        ]
        
        required_fields = ["execution", "scheduler", "use_modules", "modules", "resources", "prepend", "postpend", "launcher", "nprocs"]
        
        for loader_name, loader_func in loaders:
            result = loader_func(config_file, "test_local")
            
            for field in required_fields:
                assert field in result, f"{loader_name} missing required field: {field}"
    
    def test_remote_auth_consistency(self, config_file):
        """Test that remote authentication is handled consistently."""
        loaders = [
            ("machine_config.py", load_machine_main),
            ("config/loader.py", load_machine_new),
            ("config/old/loader.py", load_machine_old)
        ]
        
        for loader_name, loader_func in loaders:
            result = loader_func(config_file, "test_remote")
            
            # Check remote auth structure
            assert "remote_auth" in result, f"{loader_name} missing remote_auth"
            auth = result["remote_auth"]
            
            # All loaders should only support key-based auth
            assert auth["method"] == "key", f"{loader_name} supports non-key authentication"
            assert "ssh_key" in auth, f"{loader_name} missing ssh_key in auth"
            assert "port" in auth, f"{loader_name} missing port in auth"
    
    def test_no_password_auth_support(self, config_file):
        """Test that no loader supports password authentication."""
        # Create config with password auth
        config_with_password = {
            "machines": {
                "test_password": {
                    "execution": "remote",
                    "scheduler": "direct",
                    "host": "test.example.com",
                    "username": "testuser",
                    "workdir": "/home/testuser/jobs",
                    "auth": {
                        "method": "password",
                        "password": "testpass"
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_with_password, f, indent=2)
            config_path = f.name
        
        try:
            loaders = [
                ("machine_config.py", load_machine_main),
                ("config/loader.py", load_machine_new),
                ("config/old/loader.py", load_machine_old)
            ]
            
            for loader_name, loader_func in loaders:
                with pytest.raises(ValueError, match="Unsupported authentication method"):
                    loader_func(config_path, "test_password")
        finally:
            os.unlink(config_path)
    
    def test_nonexistent_config_handling(self):
        """Test how loaders handle non-existent config files."""
        non_existent_path = "/tmp/does_not_exist.json"
        
        # machine_config.py and old/loader.py should return None with warning
        # config/loader.py should return None with warning  
        loaders_returning_none = [
            ("machine_config.py", load_machine_main),
            ("config/old/loader.py", load_machine_old)
        ]
        
        for loader_name, loader_func in loaders_returning_none:
            with patch('warnings.warn') as mock_warn:
                result = loader_func(non_existent_path)
                assert result is None, f"{loader_name} should return None for missing config"
                mock_warn.assert_called_once()
        
        # config/loader.py has different behavior but should still return None
        with patch('warnings.warn') as mock_warn:
            result = load_machine_new(non_existent_path)
            assert result is None, "config/loader.py should return None for missing config"
    
    def test_script_block_normalization(self, config_file):
        """Test that script blocks are properly normalized."""
        loaders = [
            ("machine_config.py", load_machine_main),
            ("config/loader.py", load_machine_new),
            ("config/old/loader.py", load_machine_old)
        ]
        
        for loader_name, loader_func in loaders:
            result = loader_func(config_file, "test_local")
            
            # prepend and postpend should be strings (normalized from lists)
            assert isinstance(result["prepend"], str), f"{loader_name} prepend should be normalized to string"
            assert isinstance(result["postpend"], str), f"{loader_name} postpend should be normalized to string"
            
            # Check remote machine with string values
            result_remote = loader_func(config_file, "test_remote")
            assert isinstance(result_remote["prepend"], str), f"{loader_name} remote prepend should be string"
            assert isinstance(result_remote["postpend"], str), f"{loader_name} remote postpend should be string"


class TestMachineConfigDefaults:
    """Test default values in machine configurations."""
    
    @pytest.fixture
    def minimal_config(self):
        """Create a minimal machine configuration."""
        return {
            "machines": {
                "minimal_local": {
                    "execution": "local",
                    "workdir": "./test"
                },
                "minimal_remote": {
                    "execution": "remote",
                    "host": "test.example.com",
                    "username": "testuser",
                    "workdir": "/home/testuser/test"
                }
            }
        }
    
    @pytest.fixture
    def minimal_config_file(self, minimal_config):
        """Create a temporary minimal config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(minimal_config, f, indent=2)
            f.flush()  # Ensure data is written to disk
            config_path = f.name
        yield config_path
        os.unlink(config_path)
    
    def test_consistent_scheduler_defaults(self, minimal_config_file):
        """Test that all loaders use 'direct' as default scheduler."""
        loaders = [
            ("machine_config.py", load_machine_main),
            ("config/loader.py", load_machine_new),
            ("config/old/loader.py", load_machine_old)
        ]
        
        for loader_name, loader_func in loaders:
            result = loader_func(minimal_config_file, "minimal_local")
            assert result["scheduler"] == "direct", f"{loader_name} should default scheduler to 'direct'"
    
    def test_consistent_launcher_defaults(self, minimal_config_file):
        """Test that all loaders provide launcher defaults."""
        loaders = [
            ("machine_config.py", load_machine_main),
            ("config/loader.py", load_machine_new),
            ("config/old/loader.py", load_machine_old)
        ]
        
        for loader_name, loader_func in loaders:
            result = loader_func(minimal_config_file, "minimal_local")
            assert "launcher" in result, f"{loader_name} should provide launcher field"
            assert "nprocs" in result, f"{loader_name} should provide nprocs field"
            assert result["nprocs"] == 1, f"{loader_name} should default nprocs to 1"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])