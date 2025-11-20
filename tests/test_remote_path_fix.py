"""Test that remote path construction handles absolute paths correctly."""

import pytest
import os
from unittest.mock import Mock, patch
from xespresso.schedulers.slurm import SlurmScheduler


class TestRemotePathConstruction:
    """Test suite for remote path construction with absolute local paths."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_calc = Mock()
        self.mock_calc.prefix = "test_job"
        self.mock_calc.package = "pw"
        self.mock_calc.parameters = {
            "pseudopotentials": {},
            "input_data": {"CONTROL": {}},
        }

        self.queue_config = {
            "scheduler": "slurm",
            "execution": "remote",
            "remote_host": "cluster.edu",
            "remote_user": "testuser",
            "remote_auth": {"method": "key", "ssh_key": "~/.ssh/id_rsa"},
            "remote_dir": "/home/testuser/calculations",
        }

    @patch("xespresso.schedulers.remote_mixin.RemoteAuth")
    def test_absolute_path_uses_basename(self, mock_remote_auth_class):
        """Test that absolute local paths use only basename for remote path."""
        mock_remote = Mock()
        mock_remote_auth_class.return_value = mock_remote
        mock_remote.connect = Mock()

        # Set an absolute path for calc.directory
        self.mock_calc.directory = "/Users/vinicius/opt/tests/xespresso/scf/Gd2"

        scheduler = SlurmScheduler(
            calc=self.mock_calc, queue=self.queue_config, command="test command"
        )

        scheduler._setup_remote()

        # Verify that remote_path uses only the basename
        expected_remote_path = "/home/testuser/calculations/Gd2"
        assert (
            scheduler.remote_path == expected_remote_path
        ), f"Expected {expected_remote_path}, got {scheduler.remote_path}"

    @patch("xespresso.schedulers.remote_mixin.RemoteAuth")
    def test_relative_path_uses_basename(self, mock_remote_auth_class):
        """Test that relative local paths also use basename for remote path."""
        mock_remote = Mock()
        mock_remote_auth_class.return_value = mock_remote
        mock_remote.connect = Mock()

        # Set a relative path for calc.directory
        self.mock_calc.directory = "relative/path/test_calc"

        scheduler = SlurmScheduler(
            calc=self.mock_calc, queue=self.queue_config, command="test command"
        )

        scheduler._setup_remote()

        # Verify that remote_path uses only the basename
        expected_remote_path = "/home/testuser/calculations/test_calc"
        assert (
            scheduler.remote_path == expected_remote_path
        ), f"Expected {expected_remote_path}, got {scheduler.remote_path}"

    @patch("xespresso.schedulers.remote_mixin.RemoteAuth")
    def test_path_with_trailing_slash(self, mock_remote_auth_class):
        """Test that paths with trailing slashes are handled correctly."""
        mock_remote = Mock()
        mock_remote_auth_class.return_value = mock_remote
        mock_remote.connect = Mock()

        # Set a path with trailing slash
        self.mock_calc.directory = "/tmp/test_calc/"

        scheduler = SlurmScheduler(
            calc=self.mock_calc, queue=self.queue_config, command="test command"
        )

        scheduler._setup_remote()

        # Verify that remote_path uses only the basename without empty string
        expected_remote_path = "/home/testuser/calculations/test_calc"
        assert (
            scheduler.remote_path == expected_remote_path
        ), f"Expected {expected_remote_path}, got {scheduler.remote_path}"

    @patch("xespresso.schedulers.remote_mixin.RemoteAuth")
    def test_pseudo_dir_construction(self, mock_remote_auth_class):
        """Test that pseudopotential directory is correctly constructed under remote_path."""
        mock_remote = Mock()
        mock_remote_auth_class.return_value = mock_remote
        mock_remote.connect = Mock()
        mock_remote.run_command = Mock(return_value=("", ""))

        # Set an absolute path for calc.directory
        self.mock_calc.directory = "/Users/vinicius/opt/tests/xespresso/scf/Gd2"
        self.mock_calc.parameters = {
            "pseudopotentials": {},
            "input_data": {"CONTROL": {}},
        }
        self.mock_calc.write_input = Mock()

        scheduler = SlurmScheduler(
            calc=self.mock_calc, queue=self.queue_config, command="test command"
        )

        # Manually set the remote to use our mock
        scheduler.remote = mock_remote
        scheduler.remote_path = "/home/testuser/calculations/Gd2"

        # Call _transfer_pseudopotentials to verify pseudo_dir construction
        scheduler._transfer_pseudopotentials()

        # Verify that mkdir was called with correct pseudo directory
        expected_pseudo_dir = "/home/testuser/calculations/Gd2/pseudo"
        mock_remote.run_command.assert_called_with(f"mkdir -p {expected_pseudo_dir}")

        # Verify that pseudo_dir in input_data is set to ./pseudo (relative)
        assert (
            self.mock_calc.parameters["input_data"]["CONTROL"]["pseudo_dir"]
            == "./pseudo"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
