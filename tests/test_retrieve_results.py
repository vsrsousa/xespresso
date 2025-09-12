def test_retrieve_results_mocked():
    runner = RemoteRunner(
        hostname="fake.host",
        username="user",
        remote_base_dir="/remote/base",
        module_command="module load qe"
    )

    remote_subdir = "testjob"

    with tempfile.TemporaryDirectory() as local_dir:
        with patch("paramiko.SSHClient") as MockSSHClient:
            mock_client = MagicMock()
            MockSSHClient.return_value = mock_client

            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp

            # Simula arquivos remotos
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

            # Garante que arquivos irrelevantes não foram baixados
            assert not any(call[0][0].endswith("irrelevant.txt") for call in mock_sftp.get.call_args_list)

            mock_sftp.close.assert_called_once()
            mock_client.close.assert_called_once()

