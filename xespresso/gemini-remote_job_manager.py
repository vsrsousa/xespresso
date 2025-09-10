import paramiko
import os
import json
import time
from datetime import datetime

class RemoteJobManager:
    def __init__(self, host, user, remote_base=None, port=22, key_path=None, password=None):
        self.host = host
        self.user = user
        self.port = port
        self.remote_base = remote_base or os.path.join("/home", self.user, "jobs")
        self.key_path = key_path
        self.password = password

        if not self.key_path and not self.password:
            raise ValueError("You must provide either an SSH key path or a password.")

    def _connect_ssh(self):
        """Helper method to establish an SSH connection, preferring key over password."""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
        
        try:
            if self.key_path:
                print("Attempting to connect using SSH key...")
                ssh.connect(self.host, username=self.user, key_filename=self.key_path, port=self.port)
            elif self.password:
                print("Attempting to connect using password...")
                ssh.connect(self.host, username=self.user, password=self.password, port=self.port)
            return ssh
        except paramiko.AuthenticationException:
            raise Exception("Authentication failed. Please check your credentials.")
        except paramiko.SSHException as e:
            raise Exception(f"SSH connection failed: {e}")
        except Exception as e:
            raise Exception(f"Could not connect to the server: {e}")

    def _execute_command(self, ssh, command):
        """Helper method to execute a command and return stdout."""
        try:
            _, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode().strip()
            error_output = stderr.read().decode().strip()
            if error_output:
                print(f"Stderr: {error_output}")
            return output
        except paramiko.SSHException as e:
            raise Exception(f"Command execution failed: {e}")

    def submit(self, local_dir, job_file=".job_file", prefix=None, remote_dir=None, label=None):
        info_path = os.path.join(local_dir, ".remote_info.json")

        if os.path.exists(info_path):
            with open(info_path, "r") as f:
                info = json.load(f)
            remote_dir = info["remote_dir"]
            print(f"📁 Cálculo já submetido anteriormente em: {remote_dir}")

            response = input("Do you want to restart the calculation? (y/n): ")
            if response.lower() == "y":
                print("🧹 Limpando diretório remoto e reiniciando...")
                with self._connect_ssh() as ssh:
                    self._execute_command(ssh, f"rm -rf {remote_dir}")
                os.remove(info_path)
                remote_dir = None

        if remote_dir is None:
            if label:
                remote_dir = os.path.join(self.remote_base, label)
            else:
                timestamp = int(time.time())
                remote_dir = os.path.join(self.remote_base, f"job_{timestamp}")

        if prefix is None:
            pwi_files = [f for f in os.listdir(local_dir) if f.endswith(".pwi")]
            if not pwi_files:
                raise FileNotFoundError("No .pwi file found in the local directory.")
            prefix = pwi_files[0]
            
        with self._connect_ssh() as ssh:
            self._execute_command(ssh, f"mkdir -p {remote_dir}")

            with ssh.open_sftp() as sftp:
                for file in os.listdir(local_dir):
                    local_path = os.path.join(local_dir, file)
                    remote_path = os.path.join(remote_dir, file)
                    sftp.put(local_path, remote_path)
            
            slurm_path = self._execute_command(ssh, "command -v sbatch")
            
            exec_cmd = ""
            if slurm_path and self._execute_command(ssh, f"test -f {os.path.join(remote_dir, job_file)} && echo 'exists'"):
                print("Slurm detected. Submitting with sbatch.")
                exec_cmd = f"cd {remote_dir} && sbatch {job_file}"
            elif self._execute_command(ssh, f"test -f {os.path.join(remote_dir, job_file)} && echo 'exists'"):
                print("Slurm not detected. Executing with bash.")
                exec_cmd = f"cd {remote_dir} && bash {job_file}"
            else:
                print("No Slurm or .job_file. Executing directly with pw.x.")
                output_file = prefix.replace(".pwi", ".pwo")
                exec_cmd = f"cd {remote_dir} && pw.x < {prefix} > {output_file}"

            print(self._execute_command(ssh, exec_cmd))

        with open(info_path, "w") as f:
            json.dump({
                "remote_dir": remote_dir,
                "host": self.host,
                "submitted": datetime.now().isoformat()
            }, f)