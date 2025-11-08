"""
Tests for module listing and version specification features.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from xespresso.codes import CodesManager, detect_qe_codes, create_codes_config


class TestListAvailableModules:
    """Test suite for list_available_modules functionality."""

    @patch('subprocess.run')
    def test_list_modules_local(self, mock_subprocess):
        """Test listing modules on local system."""
        # Mock successful module avail output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
        -------------------- /usr/share/modules --------------------
        quantum-espresso/7.2
        quantum-espresso/7.1
        quantum-espresso/6.8
        intel/2021.4
        """
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Test without search pattern
        modules = CodesManager.list_available_modules()
        
        assert len(modules) >= 3
        assert "quantum-espresso/7.2" in modules
        assert "quantum-espresso/7.1" in modules
        mock_subprocess.assert_called()

    @patch('subprocess.run')
    def test_list_modules_with_pattern(self, mock_subprocess):
        """Test listing modules with search pattern."""
        # Mock module avail output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
        quantum-espresso/7.2
        quantum-espresso/7.1
        espresso/6.8
        intel/2021.4
        gcc/11.2
        """
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Test with "espresso" pattern
        modules = CodesManager.list_available_modules(search_pattern="espresso")
        
        assert len(modules) == 3
        assert "quantum-espresso/7.2" in modules
        assert "intel/2021.4" not in modules
        assert "gcc/11.2" not in modules

    @patch('subprocess.run')
    def test_list_modules_remote(self, mock_subprocess):
        """Test listing modules on remote system."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "quantum-espresso/7.2\nquantum-espresso/7.1"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        ssh_connection = {
            'host': 'cluster.example.edu',
            'username': 'testuser',
            'port': 22
        }
        
        modules = CodesManager.list_available_modules(
            ssh_connection=ssh_connection,
            search_pattern="quantum"
        )
        
        assert len(modules) == 2
        assert "quantum-espresso/7.2" in modules
        
        # Verify SSH command was used
        call_args = mock_subprocess.call_args[0][0]
        assert "ssh" in call_args
        assert "testuser@cluster.example.edu" in call_args

    @patch('subprocess.run')
    def test_list_modules_with_env_setup(self, mock_subprocess):
        """Test listing modules with environment setup."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "quantum-espresso/7.2"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        modules = CodesManager.list_available_modules(
            env_setup="source /etc/profile"
        )
        
        # Verify env_setup was included in command
        call_args = mock_subprocess.call_args[0][0]
        assert "source /etc/profile" in call_args

    @patch('subprocess.run')
    def test_list_modules_empty_result(self, mock_subprocess):
        """Test when no modules are found."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        modules = CodesManager.list_available_modules(search_pattern="nonexistent")
        
        assert len(modules) == 0

    @patch('subprocess.run')
    def test_list_modules_command_failure(self, mock_subprocess):
        """Test handling of command failure."""
        mock_subprocess.side_effect = Exception("Connection failed")
        
        modules = CodesManager.list_available_modules()
        
        # Should return empty list on error
        assert modules == []

    @patch('subprocess.run')
    def test_list_modules_deduplication(self, mock_subprocess):
        """Test that duplicate modules are removed."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        # Simulate output with duplicates
        mock_result.stdout = """
        quantum-espresso/7.2
        quantum-espresso/7.2
        quantum-espresso/7.1
        """
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        modules = CodesManager.list_available_modules()
        
        # Should have unique modules only
        assert modules.count("quantum-espresso/7.2") == 1
        assert len(modules) == 2


class TestExplicitVersionSpecification:
    """Test suite for explicit version specification."""

    @patch('xespresso.codes.manager.CodesManager.detect_codes')
    @patch('xespresso.codes.manager.CodesManager.detect_qe_version')
    def test_detect_codes_with_explicit_version(self, mock_detect_version, mock_detect_codes):
        """Test detect_qe_codes with explicit version parameter."""
        # Setup mocks
        mock_detect_codes.return_value = {
            'pw': '/usr/bin/pw.x',
            'ph': '/usr/bin/ph.x'
        }
        mock_detect_version.return_value = "2021.4"  # Wrong version (compiler)
        
        # Call with explicit version
        config = detect_qe_codes(
            machine_name="test",
            qe_version="7.2",  # Explicit correct version
            auto_load_machine=False
        )
        
        # Version should be 7.2, not the auto-detected 2021.4
        assert config.qe_version == "7.2"
        
        # detect_qe_version should not be called when version is explicit
        mock_detect_version.assert_not_called()

    @patch('xespresso.codes.manager.CodesManager.detect_codes')
    @patch('xespresso.codes.manager.CodesManager.detect_qe_version')
    def test_detect_codes_auto_version(self, mock_detect_version, mock_detect_codes):
        """Test detect_qe_codes with auto-detection."""
        # Setup mocks
        mock_detect_codes.return_value = {'pw': '/usr/bin/pw.x'}
        mock_detect_version.return_value = "7.2"
        
        # Call without explicit version
        config = detect_qe_codes(
            machine_name="test",
            auto_load_machine=False
        )
        
        # Should use auto-detected version
        assert config.qe_version == "7.2"
        mock_detect_version.assert_called_once()

    @patch('xespresso.codes.manager.detect_qe_codes')
    def test_create_codes_config_with_version(self, mock_detect):
        """Test create_codes_config passes version parameter."""
        from xespresso.codes.config import CodesConfig
        
        mock_config = CodesConfig(machine_name="test", qe_version="7.2")
        mock_detect.return_value = mock_config
        
        # Call with explicit version
        config = create_codes_config(
            machine_name="test",
            qe_version="7.2",
            save=False,
            auto_load_machine=False
        )
        
        # Verify detect_qe_codes was called with qe_version
        mock_detect.assert_called_once()
        call_kwargs = mock_detect.call_args[1]
        assert call_kwargs['qe_version'] == "7.2"

    @patch('xespresso.codes.manager.CodesManager.detect_codes')
    def test_version_preference_over_autodetect(self, mock_detect_codes):
        """Test that explicit version takes precedence over auto-detection."""
        mock_detect_codes.return_value = {'pw': '/usr/bin/pw.x'}
        
        # Even if auto-detect would work, explicit version should be used
        config = detect_qe_codes(
            machine_name="test",
            qe_version="6.8",
            auto_load_machine=False
        )
        
        assert config.qe_version == "6.8"


class TestVersionInCodesConfig:
    """Test that version is properly stored in codes."""

    @patch('xespresso.codes.manager.CodesManager.detect_codes')
    def test_codes_have_correct_version(self, mock_detect_codes):
        """Test that all codes in config have the correct version."""
        mock_detect_codes.return_value = {
            'pw': '/usr/bin/pw.x',
            'ph': '/usr/bin/ph.x',
            'pp': '/usr/bin/pp.x'
        }
        
        config = detect_qe_codes(
            machine_name="test",
            qe_version="7.2",
            auto_load_machine=False
        )
        
        # All codes should have version 7.2
        for code_name, code in config.codes.items():
            assert code.version == "7.2"


class TestBackwardCompatibility:
    """Test that changes maintain backward compatibility."""

    @patch('xespresso.codes.manager.CodesManager.detect_codes')
    @patch('xespresso.codes.manager.CodesManager.detect_qe_version')
    def test_detect_codes_without_version_param(self, mock_detect_version, mock_detect_codes):
        """Test that detect_qe_codes works without the new qe_version parameter."""
        mock_detect_codes.return_value = {'pw': '/usr/bin/pw.x'}
        mock_detect_version.return_value = "7.2"
        
        # Call without qe_version parameter (old behavior)
        config = detect_qe_codes(
            machine_name="test",
            auto_load_machine=False
        )
        
        # Should work and auto-detect version
        assert config.qe_version == "7.2"

    @patch('xespresso.codes.manager.detect_qe_codes')
    def test_create_codes_config_backward_compatible(self, mock_detect):
        """Test that create_codes_config works without new parameters."""
        from xespresso.codes.config import CodesConfig
        
        mock_config = CodesConfig(machine_name="test")
        mock_detect.return_value = mock_config
        
        # Call without new parameters
        config = create_codes_config(
            machine_name="test",
            save=False,
            auto_load_machine=False
        )
        
        # Should work fine
        assert config is not None
