import os
from xespresso.utils.auth import RemoteAuth

class RemoteExecutionMixin:
    """
    Mixin class to add remote execution capabilities to any Scheduler.

    When queue["execution"] == "remote", this mixin handles:
        - Remote authentication via RemoteAuth
        - File transfer (input + job script)
        - Remote job submission
        - Output retrieval

    Assumes the scheduler defines:
        - self.calc (with .prefix and .directory)
        - self.queue (with remote config keys)
        - self.job_file (name of the job script)
        - self.submit_command() method
    """

    def _setup_remote(self):
        self.remote_path = self.queue["remote_path"]
        self.remote = RemoteAuth(
            username=self.queue["remote_user"],
            host=self.queue["remote_host"],
            auth_config=self.queue["remote_auth"]
        )

    def run(self):
        if self.queue.get("execution") != "remote":
            # Fallback to local execution
            return super().run()

        self._setup_remote()

        input_file = f"{self.calc.prefix}.in"
        output_file = f"{self.calc.prefix}.out"
        job_file = self.job_file

        # Transfer input and job script
        self.remote.send_file(os.path.join(self.script_dir, input_file), f"{self.remote_path}/{input_file}")
        self.remote.send_file(os.path.join(self.script_dir, job_file), f"{self.remote_path}/{job_file}")

        # Submit job remotely
        stdout, stderr = self.remote.run_command(f"cd {self.remote_path} && {self.submit_command()}")

        # Retrieve output
        self.remote.retrieve_file(f"{self.remote_path}/{output_file}", os.path.join(self.script_dir, output_file))

        self.remote.close()
        return stdout, stderr
