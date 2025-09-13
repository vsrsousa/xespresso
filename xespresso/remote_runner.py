import os
import paramiko
import socket
import time
import logging

logging.basicConfig(filename="remote_runner.log", level=logging.INFO)

class RemoteRunner:
    """
    A class to manage persistent SSH connections and remote job execution.
    
    This class provides methods to connect to remote servers, transfer files,
    execute commands, submit computational jobs, and retrieve results while
    maintaining a persistent SSH connection for improved performance.
    
    Attributes:
        hostname (str): Remote server hostname or IP address.
        username (str): SSH username for authentication.
        remote_base_dir (str): Base directory on remote server for job files.
        module_command (str): Command to load required modules (e.g., "module load quantum-espresso").
        port (int): SSH port number (default: 22).
        password (str): SSH password for authentication (optional if using key-based auth).
        key_path (str): Path to SSH private key file (optional if using password auth).
        client (paramiko.SSHClient): Persistent SSH client instance.
        sftp (paramiko.SFTPClient): Persistent SFTP client instance.
        is_connected (bool): Connection status indicator.
    """
    
    def __init__(self, hostname, username, remote_base_dir, module_command, port=22, password=None, key_path=None):
        """
        Initialize the RemoteRunner with connection parameters.
        
        Args:
            hostname (str): Remote server hostname or IP address.
            username (str): SSH username for authentication.
            remote_base_dir (str): Base directory on remote server where job directories will be created.
            module_command (str): Command to load required environment modules.
            port (int, optional): SSH port number. Defaults to 22.
            password (str, optional): SSH password for authentication. Required if not using key-based auth.
            key_path (str, optional): Path to SSH private key file. Required if not using password auth.
            
        Example:
            >>> runner = RemoteRunner(
            ...     hostname="cluster.university.edu",
            ...     username="johndoe",
            ...     remote_base_dir="/scratch/johndoe/jobs",
            ...     module_command="module load quantum-espresso/6.8",
            ...     key_path="~/.ssh/id_rsa"
            ... )
        """
        self.hostname = hostname
        self.username = username
        self.remote_base_dir = remote_base_dir
        self.module_command = module_command
        self.port = port
        self.password = password
        self.key_path = key_path
        self.client = None
        self.sftp = None
        self.is_connected = False

    def _connect(self, retries=3, delay=5, timeout=10):
        """
        Establish and maintain a persistent SSH connection to the remote host.
        
        This method implements a robust connection strategy with retry logic and
        connection health checking. It attempts key-based authentication first,
        then falls back to password authentication if key-based auth fails.
        
        Args:
            retries (int, optional): Number of connection attempts before failing. Defaults to 3.
            delay (int, optional): Delay in seconds between retry attempts. Defaults to 5.
            timeout (int, optional): Connection timeout in seconds for each attempt. Defaults to 10.
            
        Returns:
            paramiko.SSHClient: Connected and authenticated SSH client instance.
            
        Raises:
            ConnectionError: If all connection attempts fail or authentication is unsuccessful.
            
        Note:
            The connection is maintained persistently and reused for subsequent operations.
        """
        # Check if existing connection is still alive
        if self.is_connected and self.client:
            try:
                self.client.exec_command("echo 'connection test'", timeout=5)
                return self.client
            except:
                # Connection is dead, reset and reconnect
                self.is_connected = False
                if self.client:
                    self.client.close()
                if self.sftp:
                    self.sftp.close()
                self.client = None
                self.sftp = None

        for attempt in range(1, retries + 1):
            logging.info(f"🔌 Attempt {attempt}: Connecting to {self.hostname}:{self.port} as {self.username}")
            print(f"🔌 Attempt {attempt}: Connecting to {self.hostname}:{self.port} as {self.username}")
            try:
                # Test network connectivity first
                socket.create_connection((self.hostname, self.port), timeout=timeout).close()

                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Try key-based authentication first
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
                        self.client = client
                        self.is_connected = True
                        return client
                    except FileNotFoundError as e:
                        logging.warning(f"⚠️ Key file not found: {e}")
                        print(f"⚠️ Key file not found: {e}")
                    except paramiko.ssh_exception.SSHException as e:
                        logging.warning(f"⚠️ Key-based authentication failed: {e}")
                        print(f"⚠️ Key-based authentication failed: {e}")

                # Fall back to password authentication
                if self.password:
                    try:
                        client.connect(
                            hostname=self.hostname,
                            port=self.port,
                            username=self.username,
                            password=self.password,
                            timeout=timeout
                        )
                        self.client = client
                        self.is_connected = True
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

    def _get_sftp(self):
        """
        Get or create an SFTP client using the persistent SSH connection.
        
        Returns:
            paramiko.SFTPClient: Connected SFTP client for file operations.
            
        Raises:
            ConnectionError: If SSH connection is not established or fails.
        """
        if not self.sftp or not self.sftp.sock or not self.sftp.sock.getpeername():
            self._connect()
            self.sftp = self.client.open_sftp()
        return self.sftp

    def run_command(self, command):
        """
        Execute a remote command via SSH and return the combined output.
        
        Args:
            command (str): The shell command to execute on the remote server.
            
        Returns:
            str: Combined stdout and stderr output from the command execution.
            
        Example:
            >>> output = runner.run_command("ls -la /tmp")
            >>> print(output)
        """
        client = self._connect()
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        return output + error

    def transfer_inputs(self, local_dir, remote_subdir):
        """
        Transfer input files from local directory to remote server.
        
        Copies all top-level files from the local directory to the remote
        subdirectory. If a 'pseudos/' subfolder exists locally, it will be
        created remotely and its contents (typically .UPF files) will be
        transferred as well for Quantum ESPRESSO pseudopotentials.
        
        Args:
            local_dir (str): Path to the local directory containing input files.
            remote_subdir (str): Name of the subdirectory within remote_base_dir
                                where files will be placed.
                                
        Raises:
            FileNotFoundError: If local_dir does not exist.
            ConnectionError: If SSH/SFTP connection fails during transfer.
            
        Example:
            >>> runner.transfer_inputs(
            ...     local_dir="/home/user/job_123",
            ...     remote_subdir="job_123"
            ... )
        """
        remote_dir = os.path.join(self.remote_base_dir, remote_subdir)
        client = self._connect()
        client.exec_command(f"mkdir -p {remote_dir}")
        sftp = self._get_sftp()

        # Transfer top-level files
        for filename in os.listdir(local_dir):
            local_path = os.pathjoin(local_dir, filename)
            remote_path = os.path.join(remote_dir, filename)

            if os.path.isfile(local_path):
                sftp.put(local_path, remote_path)

        # Transfer pseudos folder if it exists
        pseudos_local = os.path.join(local_dir, "pseudos")
        pseudos_remote = os.path.join(remote_dir, "pseudos")

        if os.path.isdir(pseudos_local):
            try:
                sftp.mkdir(pseudos_remote)
            except IOError:
                pass  # Folder may already exist

            for filename in os.listdir(pseudos_local):
                local_path = os.path.join(pseudos_local, filename)
                remote_path = os.path.join(pseudos_remote, filename)

                if os.path.isfile(local_path):
                    sftp.put(local_path, remote_path)
                    logging.info(f"📤 Transferred pseudo: {filename} → {remote_path}")

        print(f"✅ Files transferred to {remote_dir}")

    def submit_remote_job(self, remote_subdir, calc=None):
        """
        Submit a computational job to the remote cluster's job scheduler.
        
        This method assumes the job script has been generated and is present
        in the remote directory. It executes the appropriate scheduler command
        (e.g., sbatch, qsub) to submit the job.
        
        Args:
            remote_subdir (str): Subdirectory name within remote_base_dir where
                                job files are located.
            calc (object, optional): Calculator object with a `.command` attribute
                                    containing the submission command. If not provided,
                                    defaults to 'sbatch .job_file'.
                                    
        Returns:
            str: Output from the job submission command (typically job ID or status message).
            
        Raises:
            RuntimeError: If the job submission command fails or returns an error.
            
        Example:
            >>> job_id = runner.submit_remote_job("job_123", calc=qe_calculator)
            >>> print(f"Job submitted with ID: {job_id}")
        """
        remote_dir = os.path.join(self.remote_base_dir, remote_subdir)
        client = self._connect()

        # Use the scheduler-defined command if available
        if calc and hasattr(calc, "command"):
            job_command = calc.command
        else:
            job_command = "sbatch .job_file"

        full_command = f"cd {remote_dir} && source /etc/profile && {self.module_command} && {job_command}"

        stdin, stdout, stderr = client.exec_command(full_command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if error and not error.strip().startswith("Loading"):
            raise RuntimeError(f"❌ Error submitting job:\n{error}")

        logging.info(f"📤 Job submission stdout:\n{output}")
        logging.info(f"📤 Job submission stderr:\n{error}")

        print(f"🚀 Job submitted successfully:\n{output.strip()}")
        return output.strip()

    def retrieve_results(self, remote_subdir, local_dir):
        """
        Retrieve output files from the remote server to local directory.
        
        Downloads relevant output files including Quantum ESPRESSO output files
        (.pwo), scheduler logs (.out, .err), and other result files for local
        parsing and analysis.
        
        Args:
            remote_subdir (str): Subdirectory name within remote_base_dir containing
                                the job output files.
            local_dir (str): Local directory where files will be downloaded.
                            
        Example:
            >>> runner.retrieve_results(
            ...     remote_subdir="job_123",
            ...     local_dir="/home/user/job_123_results"
            ... )
        """
        remote_dir = os.path.join(self.remote_base_dir, remote_subdir)
        sftp = self._get_sftp()

        for filename in sftp.listdir(remote_dir):
            if filename.endswith(".out") or filename.endswith(".err") or filename.endswith(".pwo"):
                remote_path = os.path.join(remote_dir, filename)
                local_path = os.path.join(local_dir, filename)
                sftp.get(remote_path, local_path)
                logging.info(f"📥 Retrieved: {filename} → {local_path}")

        print(f"📥 Results retrieved to {local_dir}")

    def test_connection(self):
        """
        Test SSH connectivity to the remote server.
        
        Performs a basic connection test to verify SSH access and authentication.
        
        Returns:
            bool: True if connection is successful, False otherwise.
            
        Example:
            >>> if runner.test_connection():
            ...     print("Connection successful")
            ... else:
            ...     print("Connection failed")
        """
        try:
            client = self._connect()
            client.close()
            print(f"✅ SSH connection successful to {self.hostname}:{self.port} as {self.username}")
            return True
        except Exception as e:
            print(f"❌ SSH connection failed: {e}")
            return False

    def check_quantum_espresso(self):
        """
        Check if Quantum ESPRESSO is available on the remote server.
        
        Verifies that the 'pw.x' executable is accessible in the PATH after
        loading the required modules.
        
        Returns:
            str or None: Path to pw.x executable if found, None otherwise.
            
        Example:
            >>> qe_path = runner.check_quantum_espresso()
            >>> if qe_path:
            ...     print(f"QE found at: {qe_path}")
        """
        try:
            client = self._connect()
            command = f"source /etc/profile && {self.module_command} && which pw.x"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
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
        Check the version of Quantum ESPRESSO on the remote server.
        
        Args:
            min_version (str, optional): Minimum required version in format "X.Y".
                                        Defaults to "6.5".
                                        
        Returns:
            bool: True if version is compatible, False otherwise.
            
        Raises:
            EnvironmentError: If QE version is below minimum requirement or
                             version detection fails.
                             
        Example:
            >>> if runner.check_qe_version_remote("6.5"):
            ...     print("QE version is compatible")
        """
        try:
            client = self._connect()
            command = f"source /etc/profile && {self.module_command} && pw.x < /dev/null"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()

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
        List available environment modules on the remote server.
        
        Returns:
            str: Output of the 'module avail' command, or None if failed.
            
        Example:
            >>> modules = runner.list_available_modules()
            >>> print(modules)
        """
        try:
            client = self._connect()
            command = "source /etc/profile && module avail"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            full_output = output + error
            print("📦 Available modules:\n")
            print(full_output)
            return full_output
        except Exception as e:
            print(f"❌ Failed to list available modules: {e}")
            return None

    def list_remote_files(self, remote_subdir):
        """
        List files in the specified remote directory.
        
        Args:
            remote_subdir (str): Subdirectory name within remote_base_dir to list.
            
        Returns:
            str: Output of 'ls -lh' command, or None if failed.
            
        Example:
            >>> files = runner.list_remote_files("job_123")
            >>> print(files)
        """
        try:
            client = self._connect()
            remote_path = os.path.join(self.remote_base_dir, remote_subdir)
            command = f"ls -lh {remote_path}"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            if error:
                print(f"⚠️ Error listing remote files:\n{error}")
            else:
                print(f"📂 Files on server ({remote_path}):\n{output}")
            return output
        except Exception as e:
            print(f"❌ Failed to list remote files: {e}")
            return None

    def close(self):
        """
        Close the persistent SSH connection and SFTP session.
        
        This method should be called when the RemoteRunner is no longer needed
        to ensure proper cleanup of network resources. It safely closes both
        the SFTP and SSH connections, handling any potential exceptions.
        
        Example:
            >>> runner.close()
        """
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None
                print("🔌 SFTP connection closed")
        except Exception as e:
            print(f"⚠️ Error closing SFTP connection: {e}")
        
        try:
            if self.client:
                self.client.close()
                self.client = None
                print("🔌 SSH connection closed")
        except Exception as e:
            print(f"⚠️ Error closing SSH connection: {e}")
        
        self.is_connected = False
        print("✅ All connections closed successfully")
