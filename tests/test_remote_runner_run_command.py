import pytest
from unittest.mock import MagicMock, patch
from xespresso.remote_runner import RemoteRunner

def test_run_command_success():
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
        mock_stdout.read.return_value = b"Execution completed\n"

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        output = runner.run_command("echo Hello")
        assert "Execution completed" in output
        print(f"✅ Command executed successfully:\n{output}")

def test_run_command_with_error():
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
        mock_stdout.read.return_value = b""

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"bash: command not found\n"

        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        output = runner.run_command("invalid_command")
        assert "command not found" in output
        print(f"⚠️ Command error captured:\n{output}")

