import os
from xespresso.utils.auth import RemoteAuth

class RemoteExecutionMixin:
    """
    Mixin class that adds remote execution capabilities to any Scheduler.

    This mixin is designed for workflows where multiple calculations are submitted
    to the same or different remote servers, possibly from different notebook cells.

    Features:
    - Reuses SSH connection across multiple calculations on the same server
    - Automatically opens a new connection if the server or user changes
    - Dynamically computes remote working directory based on calc.directory
    - Avoids redundant remote_path setup if calc.directory hasn't changed

    Assumes:
    - self.calc: an Espresso calculator with .prefix, .package, and .directory
    - self.queue: dictionary with keys:
        - 'execution': "remote"
        - 'remote_host': hostname or IP
        - 'remote_user': SSH username
        - 'remote_auth': dict with 'method', 'ssh_key' or 'password'
        - 'remote_dir': base path on remote machine
    - self.job_file: name of the job script
    - self.submit_command(): method that returns the job submission command
    """

    _remote_sessions = {}
    _last_remote_path = None

    def _setup_remote(self):
        """
        Initializes or reuses a remote SSH connection and sets the remote working path
        only if the calculation directory has changed.
        """
        key = (self.queue["remote_host"], self.queue["remote_user"])
        if key not in self._remote_sessions:
            remote = RemoteAuth(
                username=self.queue["remote_user"],
                host=self.queue["remote_host"],
                auth_config=self.queue["remote_auth"]
            )
            remote.connect()
            self._remote_sessions[key] = remote

        self.remote = self._remote_sessions[key]

        # Check if remote_path needs to be updated
        current_path = os.path.join(self.queue["remote_dir"], self.calc.directory)
        if current_path != self._last_remote_path:
            self.remote_path = current_path
            self._last_remote_path = current_path

    def run(self):
        """
        Executes the calculation remotely if queue["execution"] == "remote".
        Otherwise, falls back to local execution.

        Handles:
        - File transfer (input + job script)
        - Remote job submission
        - Output retrieval
        """
        if self.queue.get("execution") != "remote":
            return super().run()

        self._setup_remote()

        input_file  = f"{self.calc.prefix}.{self.calc.package}i"
        output_file = f"{self.calc.prefix}.{self.calc.package}o"
        job_file    = self.job_file

        local_input  = os.path.join(self.calc.directory, input_file)
        local_output = os.path.join(self.calc.directory, output_file)
        local_job    = os.path.join(self.calc.directory, job_file)

        # Upload files to remote
        self.remote.send_file(local_input, f"{self.remote_path}/{input_file}")
        self.remote.send_file(local_job,   f"{self.remote_path}/{job_file}")

        # Execute job remotely
        stdout, stderr = self.remote.run_command(f"cd {self.remote_path} && {self.submit_command()}")

        # Retrieve output file
        self.remote.retrieve_file(f"{self.remote_path}/{output_file}", local_output)

        return stdout, stderr

    @classmethod
    def close_all_connections(cls):
        """
        Closes all active SSH connections managed by the mixin.
        Useful at the end of a notebook or workflow.
        """
        for remote in cls._remote_sessions.values():
            remote.close()
        cls._remote_sessions.clear()
        cls._last_remote_path = None
