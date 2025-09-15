import os
import hashlib
from xespresso.utils.auth import RemoteAuth
from xespresso.utils import warnings as warnings  # Custom warning system

# Apply custom formatting globally (if your module supports it)
warnings.formatwarning = lambda msg, cat, fname, lineno, *_: (
    f"\n⚠️ {cat.__name__} in {fname}:{lineno}\n→ {msg}\n"
)

class RemoteExecutionMixin:
    """
    Mixin class that adds remote execution capabilities to any Scheduler.

    Features:
    - Reuses SSH connection across multiple calculations on the same server
    - Automatically opens a new connection if the server or user changes
    - Dynamically computes remote working directory based on calc.directory
    - Avoids redundant remote_path setup if calc.directory hasn't changed
    - Transfers required pseudopotentials to remote ./pseudo directory
    - Logs file transfers and warnings
    - Validates file integrity using SHA256 checksums

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
    - self.logger: optional logger object with .info() and .warning()
    """
    _remote_sessions = {}
    _last_remote_path = None

    def _setup_remote(self):
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

        current_path = os.path.join(self.queue["remote_dir"], self.calc.directory)
        if current_path != self._last_remote_path:
            self.remote_path = current_path
            self._last_remote_path = current_path

    def _sha256(self, filepath):
        """Returns SHA256 checksum of a file."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _transfer_pseudopotentials(self, max_retries=1):
        pseudopotentials = self.calc.parameters.get("pseudopotentials", {})
        remote_pseudo_dir = os.path.join(self.remote_path, "pseudo")
        self.remote.run_command(f"mkdir -p {remote_pseudo_dir}")

        search_dirs = []
        control = self.calc.parameters.get("input_data", {}).get("CONTROL", {})
        if "pseudo_dir" in control:
            search_dirs.append(control["pseudo_dir"])
        if "ESPRESSO_PSEUDO" in os.environ:
            search_dirs.append(os.path.join(os.environ["ESPRESSO_PSEUDO"]))
        search_dirs.append(os.path.expanduser("~/espresso/pseudo/"))

        for symbol, pseudo_file in pseudopotentials.items():
            found = False
            for attempt in range(max_retries + 1):
                for pseudo_dir in search_dirs:
                    local_path = os.path.join(pseudo_dir, pseudo_file)
                    if os.path.exists(local_path):
                        remote_path = os.path.join(remote_pseudo_dir, pseudo_file)
                        self.remote.send_file(local_path, remote_path)

                        # Verify checksum
                        local_hash = self._sha256(local_path)
                        remote_hash = self.remote.sha256(remote_path)
                        if local_hash != remote_hash:
                            warnings.warn(f"Checksum mismatch for {pseudo_file} after transfer.")
                            if hasattr(self, "logger"):
                                self.logger.warning(f"Checksum mismatch: {pseudo_file}")
                        else:
                            if hasattr(self, "logger"):
                                self.logger.info(f"Transferred {pseudo_file} for {symbol} with verified checksum.")
                        found = True
                        break
                if found:
                    break
            if not found:
                warnings.warn(f"Pseudopotential '{pseudo_file}' not found in any known directory.")
                if hasattr(self, "logger"):
                    self.logger.warning(f"Missing pseudopotential: {pseudo_file} for {symbol}")

        self.calc.parameters["input_data"]["CONTROL"]["pseudo_dir"] = "./pseudo"
        self.calc.write_input(self.calc.atoms)

    def run(self):
        if self.queue.get("execution") != "remote":
            return super().run()

        self._setup_remote()

        input_file = f"{self.calc.prefix}.{self.calc.package}i"
        output_file = f"{self.calc.prefix}.{self.calc.package}o"
        job_file = self.job_file

        local_input = os.path.join(self.calc.directory, input_file)
        local_output = os.path.join(self.calc.directory, output_file)
        local_job = os.path.join(self.calc.directory, job_file)

        self._transfer_pseudopotentials()

        self.remote.send_file(local_input, f"{self.remote_path}/{input_file}")
        self.remote.send_file(local_job, f"{self.remote_path}/{job_file}")

        if hasattr(self, "logger"):
            self.logger.info(f"Submitting job via: {self.submit_command()}")

        stdout, stderr = self.remote.run_command(f"cd {self.remote_path} && {self.submit_command()}")

        self.remote.retrieve_file(f"{self.remote_path}/{output_file}", local_output)

        return stdout, stderr

    @classmethod
    def close_all_connections(cls):
        for remote in cls._remote_sessions.values():
            remote.close()
        cls._remote_sessions.clear()
        cls._last_remote_path = None
