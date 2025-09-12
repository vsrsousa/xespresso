import os
import paramiko
import socket
import time
import logging

logging.basicConfig(filename="remote_runner.log", level=logging.INFO)

class RemoteRunner:
    def __init__(self, hostname, username, remote_base_dir, module_command, port=22, password=None, key_path=None):
        self.hostname = hostname
        self.username = username
        self.remote_base_dir = remote_base_dir
        self.module_command = module_command
        self.port = port
        self.password = password
        self.key_path = key_path

    def _connect(self, retries=3, delay=5, timeout=10):
        """
        Establishes an SSH connection to the remote host with retry and timeout support.
        Tries key-based authentication first, then falls back to password if key fails.

        Args:
            retries (int): Number of connection attempts before failing.
            delay (int): Delay in seconds between retries.
            timeout (int): Timeout in seconds for each connection attempt.

        Returns:
            paramiko.SSHClient: Connected SSH client.

        Raises:
            ConnectionError: If all connection attempts fail.
        """
        import socket
        import time
        import paramiko
        import logging

        logging.basicConfig(filename="remote_runner.log", level=logging.INFO)

        for attempt in range(1, retries + 1):
            logging.info(f"🔌 Attempt {attempt}: Connecting to {self.hostname}:{self.port} as {self.username}")
            print(f"🔌 Attempt {attempt}: Connecting to {self.hostname}:{self.port} as {self.username}")
            try:
                socket.create_connection((self.hostname, self.port), timeout=timeout).close()

                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if self.key_path:
                    try:
                        key_path_expanded = os.path.expanduser(self.key_path)
                        client.connect(
                            hostname=self.hostname,
                            port=self.port,
                            username=self.username,
                            key_filename=key_path_expanded,
                            timeout=timeout
                        )
                        return client
                    except FileNotFoundError as e:
                        logging.warning(f"⚠️ Key file not found: {e}")
                        print(f"⚠️ Key file not found: {e}")
                    except paramiko.ssh_exception.SSHException as e:
                        logging.warning(f"⚠️ Key-based authentication failed: {e}")
                        print(f"⚠️ Key-based authentication failed: {e}")

                if self.password:
                    try:
                        client.connect(
                            hostname=self.hostname,
                            port=self.port,
                            username=self.username,
                            password=self.password,
                            timeout=timeout
                        )
                        return client
                    except paramiko.ssh_exception.SSHException as e:
                        logging.warning(f"⚠️ Password-based authentication failed: {e}")
                        print(f"⚠️ Password-based authentication failed: {e}")

                raise ConnectionError("Authentication failed with both key and password.")

            except Exception as e:
                logging.warning(f"⚠️ Connection attempt {attempt} failed: {e}")
                print(f"⚠️ Connection attempt {attempt} failed: {e}")
                time.sleep(delay)

        raise ConnectionError(f"❌ Failed to connect to {self.hostname} after {retries} attempts.")

    def run_command(self, command):
        """
        Executes a remote command via SSH and returns the full output (stdout + stderr).
        """
        client = self._connect()
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()
        return output + error

    def transfer_inputs(self, local_dir, remote_subdir):
        """
        Transfers input files to the remote server, ensuring the target directory exists.

        Args:
            local_dir (str): Local path containing input files.
            remote_subdir (str): Subdirectory name inside remote_base_dir.
        """
        remote_dir = os.path.join(self.remote_base_dir, remote_subdir)
        client = self._connect()
        client.exec_command(f"mkdir -p {remote_dir}")
        sftp = client.open_sftp()
        for filename in os.listdir(local_dir):
            local_path = os.path.join(local_dir, filename)
            remote_path = os.path.join(remote_dir, filename)
            sftp.put(local_path, remote_path)
        sftp.close()
        client.close()
        print(f"✅ Files transferred to {remote_dir}")


    def submit_remote_job(self, remote_subdir, calc=None):
        """
        Submits a remote job to the target machine using the appropriate scheduler.

        This method assumes that the job script (e.g., .job_file or run.sh) has already been
        generated and that the correct submission command is stored in `calc.command`.

        The submission command is executed remotely via SSH, and the output is returned.

        Args:
            remote_subdir (str): Subdirectory name inside `remote_base_dir` where the job files are located.
            calc (object, optional): Calculator object with a `.command` attribute containing the submission command.
                                     If not provided, defaults to 'sbatch .job_file'.

        Returns:
            str: Output from the remote job submission command (typically job ID or confirmation message).

        Raises:
            RuntimeError: If the remote command produces an error.
        """
        remote_dir = os.path.join(self.remote_base_dir, remote_subdir)
        client = self._connect()

        # Use the scheduler-defined command if available
        if calc and hasattr(calc, "command"):
            job_command = calc.command
        else:
            job_command = "sbatch .job_file"

        full_command = f"cd {remote_dir} && {self.module_command} && {job_command}"

        stdin, stdout, stderr = client.exec_command(full_command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        client.close()

        if error:
            raise RuntimeError(f"❌ Error submitting job:\n{error}")

        print(f"🚀 Job submitted successfully:\n{output.strip()}")
        return output.strip()

    def retrieve_results(self, remote_subdir, local_dir):
        """
        Retrieves output files from the remote server.

        Args:
            remote_subdir (str): Subdirectory name inside remote_base_dir.
            local_dir (str): Local directory to store retrieved files.
        """
        remote_dir = os.path.join(self.remote_base_dir, remote_subdir)
        client = self._connect()
        sftp = client.open_sftp()
        for filename in sftp.listdir(remote_dir):
            if filename.endswith(".out") or filename.endswith(".err"):
                remote_path = os.path.join(remote_dir, filename)
                local_path = os.path.join(local_dir, filename)
                sftp.get(remote_path, local_path)
        sftp.close()
        client.close()
        print(f"📥 Results retrieved to {local_dir}")

    def test_connection(self):
        """
        Tests SSH connectivity to the remote server.
        """
        try:
            client = self._connect()
            client.close()
            print(f"✅ SSH connection successful to {self.hostname}:{self.port} as {self.username}")
        except Exception as e:
            print(f"❌ SSH connection failed: {e}")

    def check_quantum_espresso(self):
        """
        Checks if Quantum ESPRESSO is available on the remote server.
        """
        try:
            client = self._connect()
            command = f"source /etc/profile && {self.module_command} && which pw.x"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            client.close()
            if output:
                print(f"✅ Quantum ESPRESSO detected: {output}")
                return output
            else:
                print("⚠️ Quantum ESPRESSO not found. The 'pw.x' executable is not in PATH.")
                if error:
                    print(f"🔍 System message:\n{error}")
                return None
        except Exception as e:
            print(f"❌ Failed to check Quantum ESPRESSO: {e}")
            return None

    def check_qe_version_remote(self, min_version="6.5"):
        """
        Checks the version of Quantum ESPRESSO on the remote server.

        Args:
            min_version (str): Minimum required version (e.g., "6.5").

        Returns:
            bool: True if version is compatible, False otherwise.
        """
        try:
            client = self._connect()
            command = f"source /etc/profile && {self.module_command} && pw.x < /dev/null"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            client.close()

            full_output = output + error
            for line in full_output.splitlines():
                if "Program PWSCF" in line:
                    version = line.split("v.")[1].split()[0]
                    def parse(v): return tuple(map(int, v.split(".")))
                    if parse(version) >= parse(min_version):
                        print(f"✅ Remote QE version {version} is compatible (minimum required: {min_version})")
                        return True
                    else:
                        raise EnvironmentError(f"⚠️ Remote QE version {version} is below required minimum ({min_version})")

            raise EnvironmentError("❌ Unable to detect QE version on remote server.")
        except Exception as e:
            print(f"❌ Failed to check QE version remotely: {e}")
            return False

    def list_available_modules(self):
        """
        Lists available modules on the remote server.
        """
        try:
            client = self._connect()
            command = "source /etc/profile && module avail"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            client.close()
            full_output = output + error
            print("📦 Available modules:\n")
            print(full_output)
            return full_output
        except Exception as e:
            print(f"❌ Failed to list available modules: {e}")
            return None

    def list_remote_files(self, remote_subdir):
        """
        Lists files in the specified remote directory.

        Args:
            remote_subdir (str): Subdirectory name inside remote_base_dir.

        Returns:
            str: Output of 'ls -lh' or error message.
        """
        try:
            client = self._connect()
            remote_path = os.path.join(self.remote_base_dir, remote_subdir)
            command = f"ls -lh {remote_path}"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            client.close()
            if error:
                print(f"⚠️ Error listing remote files:\n{error}")
            else:
                print(f"📂 Files on server ({remote_path}):\n{output}")
            return output
        except Exception as e:
            print(f"❌ Failed to list remote files: {e}")
            return None
