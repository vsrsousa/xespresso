import os
import pytest
from unittest.mock import MagicMock, patch
from xespresso.remote_runner import RemoteRunner
from xespresso.schedulers import get_scheduler

class DummyCalc:
    def __init__(self, command):
        self.command = command

@pytest.mark.parametrize("scheduler_type,expected_command", [
    ("slurm", "sbatch .job_file"),
    ("direct", "bash run.sh"),
    ("pbs", None),  # Simulate unsupported scheduler
])
def test_submit_remote_job_scheduler_variants(scheduler_type, expected_command):
    print(f"\n🔧 Testing scheduler: {scheduler_type}")

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

        with patch("paramiko.SSHClient") as MockSSHClient:
            mock_client = MagicMock()
            MockSSHClient.return_value = mock_client

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

