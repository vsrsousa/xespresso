import os
import tempfile
from unittest.mock import MagicMock, patch
from xespresso.remote_runner import RemoteRunner

def test_transfer_inputs_mocked():
    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    with tempfile.TemporaryDirectory() as local_dir:
        # Cria arquivos fictícios
        filenames = ["input1.pwi", "input2.pwi"]
        for name in filenames:
            with open(os.path.join(local_dir, name), "w") as f:
                f.write("dummy content")

        remote_subdir = "testjob"

        with patch("paramiko.SSHClient") as MockSSHClient:
            mock_client = MagicMock()
            MockSSHClient.return_value = mock_client

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

