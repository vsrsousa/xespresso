import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from xespresso.remote_runner import RemoteRunner
from xespresso.schedulers import get_scheduler
import socket

class DummyCalc:
    """Simple calculator mock that holds a submission command."""
    def __init__(self, command):
        self.command = command

# 🧪 Test remote job submission for different scheduler types
@pytest.mark.parametrize("scheduler_type,expected_command", [
    ("slurm", "sbatch .job_file"),
    ("direct", "bash run.sh"),
    ("pbs", None),  # Simulate unsupported scheduler
])
@patch("socket.create_connection")
@patch("paramiko.SSHClient")
def test_submit_remote_job_scheduler_variants(mock_ssh, mock_socket, scheduler_type, expected_command):
    print(f"\n🔧 Testing scheduler: {scheduler_type}")
    mock_socket.return_value = MagicMock()  # Simulate reachable host

    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    remote_subdir = f"{scheduler_type}_job"

    if expected_command is None:
        print("🚫 Expecting failure for unsupported scheduler")
        with pytest.raises(ValueError, match=f"Unsupported scheduler type: {scheduler_type}"):
            get_scheduler(DummyCalc(command="noop"), "echo Hello", {"scheduler": scheduler_type})
    else:
        calc = DummyCalc(command=expected_command)

        mock_client = MagicMock()
        mock_ssh.return_value = mock_client

        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"Job submitted successfully\n"

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        output = runner.submit_remote_job(remote_subdir, calc=calc)

        full_expected = f"cd /remote/base/{remote_subdir} && module load qe && {expected_command}"
        mock_client.exec_command.assert_called_once_with(full_expected)
        assert output == "Job submitted successfully"
        print(f"✅ {scheduler_type} submission simulated successfully")

# 🧪 Test input file transfer to remote server
@patch("socket.create_connection")
@patch("paramiko.SSHClient")
def test_transfer_inputs_mocked(mock_ssh, mock_socket):
    mock_socket.return_value = MagicMock()

    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    with tempfile.TemporaryDirectory() as local_dir:
        filenames = ["input1.pwi", "input2.pwi"]
        for name in filenames:
            with open(os.path.join(local_dir, name), "w") as f:
                f.write("dummy content")

        remote_subdir = "testjob"

        mock_client = MagicMock()
        mock_ssh.return_value = mock_client

        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp

        runner.transfer_inputs(local_dir, remote_subdir)

        remote_dir = os.path.join(runner.remote_base_dir, remote_subdir)
        mock_client.exec_command.assert_called_once_with(f"mkdir -p {remote_dir}")

        for name in filenames:
            local_path = os.path.join(local_dir, name)
            remote_path = os.path.join(remote_dir, name)
            mock_sftp.put.assert_any_call(local_path, remote_path)

        mock_sftp.close.assert_called_once()
        mock_client.close.assert_called_once()
        print(f"📤 Input files transferred to {remote_dir}")

# 🧪 Test retrieval of output files from remote server
@patch("socket.create_connection")
@patch("paramiko.SSHClient")
def test_retrieve_results_mocked(mock_ssh, mock_socket):
    mock_socket.return_value = MagicMock()

    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    remote_subdir = "testjob"

    with tempfile.TemporaryDirectory() as local_dir:
        mock_client = MagicMock()
        mock_ssh.return_value = mock_client

        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp

        # Simulate remote directory contents
        mock_sftp.listdir.return_value = ["testjob.out", "testjob.err", "irrelevant.txt"]

        runner.retrieve_results(remote_subdir, local_dir)

        remote_dir = os.path.join(runner.remote_base_dir, remote_subdir)
        mock_sftp.get.assert_any_call(
            os.path.join(remote_dir, "testjob.out"),
            os.path.join(local_dir, "testjob.out")
        )
        mock_sftp.get.assert_any_call(
            os.path.join(remote_dir, "testjob.err"),
            os.path.join(local_dir, "testjob.err")
        )

        # Ensure irrelevant file was not downloaded
        assert not any(call[0][0].endswith("irrelevant.txt") for call in mock_sftp.get.call_args_list)

        mock_sftp.close.assert_called_once()
        mock_client.close.assert_called_once()
        print(f"📥 Output files retrieved from {remote_dir}")

