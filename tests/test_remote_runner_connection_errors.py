import pytest
from unittest.mock import patch, MagicMock
from paramiko.ssh_exception import AuthenticationException, SSHException
from xespresso.remote_runner import RemoteRunner

def test_connection_authentication_failure():
    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe",
        password="wrongpass"
    )

    with patch("paramiko.SSHClient") as MockSSHClient:
        mock_client = MagicMock()
        MockSSHClient.return_value = mock_client
        mock_client.connect.side_effect = AuthenticationException("Authentication failed")

        runner.test_connection()
        print("✅ Authentication failure handled gracefully")

def test_connection_host_unreachable():
    runner = RemoteRunner(
        hostname="unreachable.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    with patch("paramiko.SSHClient") as MockSSHClient:
        mock_client = MagicMock()
        MockSSHClient.return_value = mock_client
        mock_client.connect.side_effect = SSHException("Unable to connect to host")

        runner.test_connection()
        print("✅ Host unreachable error handled gracefully")

def test_connection_key_file_missing():
    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe",
        key_path="/invalid/key/path"
    )

    with patch("paramiko.RSAKey.from_private_key_file") as mock_key_loader:
        mock_key_loader.side_effect = FileNotFoundError("Key file not found")

        runner.test_connection()
        print("✅ Missing key file handled gracefully")

