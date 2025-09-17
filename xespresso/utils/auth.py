import os
import subprocess
import paramiko
from xespresso.config import VERBOSE_ERRORS

class RemoteAuth:
    """
    Manages persistent SSH authentication and file transfer for remote execution.

    Supports:
    - Password and key-based login
    - Custom SSH port (default: 22)
    - Persistent SSH and SFTP sessions
    - Remote command execution
    - File transfer (send/retrieve)
    - Remote SHA256 checksum validation

    Args:
        username (str): SSH login username.
        host (str): Remote machine hostname or IP.
        auth_config (dict): Authentication configuration with keys:
            - method: "password" or "key"
            - password: (if method == "password")
            - ssh_key: path to private key (if method == "key")
            - port: optional SSH port (default: 22)
    """
    def __init__(self, username, host, auth_config):
        self.username = username
        self.host = host
        self.port = auth_config.get("port", 22)
        self.method = auth_config.get("method", "key")
        self.password = auth_config.get("password")
        self.ssh_key = os.path.expanduser(auth_config.get("ssh_key", "~/.ssh/id_rsa"))
        self.client = None
        self.sftp = None

    def connect(self):
        """Establishes SSH and SFTP sessions if not already connected."""
        if self.client:
            return
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.method == "password":
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )
            else:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.ssh_key
                )
            self.sftp = self.client.open_sftp()
        except Exception as e:
            msg = f"Failed to connect to {self.username}@{self.host}:{self.port}: {e}"
            raise RuntimeError(msg) if VERBOSE_ERRORS else RuntimeError(msg) from None

    def run_command(self, command):
        """
        Executes a shell command on the remote host.

        Args:
            command (str): Shell command to execute.

        Returns:
            tuple: (stdout, stderr) output strings.
        """
        try:
            self.connect()
            stdin, stdout, stderr = self.client.exec_command(command)
            return stdout.read().decode(), stderr.read().decode()
        except Exception as e:
            msg = f"Failed to execute remote command '{command}': {e}"
            raise RuntimeError(msg) if VERBOSE_ERRORS else RuntimeError(msg) from None

    def send_file(self, local_path, remote_path):
        """
        Transfers a file to the remote host.

        Args:
            local_path (str): Path to the local file.
            remote_path (str): Destination path on the remote host.
        """
        try:
            self.connect()
            self.sftp.put(local_path, remote_path)
        except Exception as e:
            msg = f"Failed to send file '{local_path}' to '{remote_path}': {e}"
            raise RuntimeError(msg) if VERBOSE_ERRORS else RuntimeError(msg) from None

    def retrieve_file(self, remote_path, local_path):
        """
        Retrieves a file from the remote host.

        Args:
            remote_path (str): Path to the file on the remote host.
            local_path (str): Destination path on the local machine.
        """
        try:
            self.connect()
            self.sftp.get(remote_path, local_path)
        except Exception as e:
            msg = f"Failed to retrieve file '{remote_path}' to '{local_path}': {e}"
            raise RuntimeError(msg) if VERBOSE_ERRORS else RuntimeError(msg) from None

    def sha256(self, remote_path):
        """
        Computes SHA256 checksum of a file on the remote host.

        Args:
            remote_path (str): Path to the file on the remote machine.

        Returns:
            str: SHA256 hash string (hex), or raises RuntimeError if failed.
        """
        try:
            self.connect()
            cmd = f"sha256sum {remote_path}"
            stdout, stderr = self.run_command(cmd)
            if stderr:
                raise RuntimeError(f"Remote error: {stderr.strip()}")
            return stdout.strip().split()[0]
        except Exception as e:
            msg = f"Failed to compute SHA256 for '{remote_path}': {e}"
            raise RuntimeError(msg) if VERBOSE_ERRORS else RuntimeError(msg) from None

    def close(self):
        """Closes SSH and SFTP sessions."""
        try:
            if self.sftp:
                self.sftp.close()
            if self.client:
                self.client.close()
        except Exception as e:
            msg = f"Failed to close remote session: {e}"
            raise RuntimeError(msg) if VERBOSE_ERRORS else RuntimeError(msg) from None

# 🔧 Auxiliar functions

def generate_ssh_key(private_key_path: str):
    """
    Generates a new RSA SSH key pair at the specified path.

    Args:
        private_key_path (str): Path to the private key file (e.g. ~/.ssh/id_rsa).
    """
    private_key_path = os.path.expanduser(private_key_path)
    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", private_key_path], check=True)
    print(f"✅ SSH key pair created at {private_key_path} and {private_key_path}.pub")

def install_ssh_key(username: str, host: str, public_key_path: str, port: int = 22):
    """
    Installs the public SSH key on the remote server using ssh-copy-id.

    Args:
        username (str): SSH username.
        host (str): Remote host IP or domain.
        public_key_path (str): Path to the public key file.
        port (int): SSH port number.
    """
    public_key_path = os.path.expanduser(public_key_path)
    subprocess.run(["ssh-copy-id", "-p", str(port), "-i", public_key_path, f"{username}@{host}"], check=True)
    print(f"🔐 SSH key installed on {username}@{host}:{port}")


def test_ssh_connection(username: str, host: str, key_path: str = None, port: int = 22):
    """
    Tests SSH connectivity to the remote host.

    Args:
        username (str): SSH username.
        host (str): Remote host IP or domain.
        key_path (str, optional): Path to the private key file.
        port (int): SSH port number.
    """
    key_path = os.path.expanduser(key_path) if key_path else None
    cmd = ["ssh", "-p", str(port)]
    if key_path:
        cmd += ["-i", key_path]
    cmd += [f"{username}@{host}", "echo 'Connection successful'"]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("❌ SSH connection failed.")
