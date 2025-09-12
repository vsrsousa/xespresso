import os
import pytest
from unittest.mock import MagicMock, patch
from xespresso.remote_runner import RemoteRunner

def test_check_quantum_espresso_mocked():
    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    with patch("paramiko.SSHClient") as MockSSHClient:
        mock_client = MagicMock()
        MockSSHClient.return_value = mock_client

        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"/usr/bin/pw.x\n"

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        output = runner.check_quantum_espresso()
        assert output == "/usr/bin/pw.x"
        print(f"✅ QE executable found at: {output}")

def test_check_qe_version_remote_mocked():
    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    with patch("paramiko.SSHClient") as MockSSHClient:
        mock_client = MagicMock()
        MockSSHClient.return_value = mock_client

        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"Program PWSCF v.7.2 starts\n"

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        result = runner.check_qe_version_remote(min_version="6.5")
        assert result is True
        print("✅ QE version is compatible")

def test_list_remote_files_mocked():
    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    remote_subdir = "testjob"

    with patch("paramiko.SSHClient") as MockSSHClient:
        mock_client = MagicMock()
        MockSSHClient.return_value = mock_client

        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"-rw-r--r-- 1 user user 1.2K Sep 12 testjob.out\n"

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        output = runner.list_remote_files(remote_subdir)
        assert "testjob.out" in output
        print(f"📂 Remote files listed:\n{output}")

def test_test_connection_mocked():
    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    with patch("paramiko.SSHClient") as MockSSHClient:
        mock_client = MagicMock()
        MockSSHClient.return_value = mock_client

        runner.test_connection()
        mock_client.connect.assert_called_once()
        mock_client.close.assert_called_once()
        print("✅ SSH connection test passed")

