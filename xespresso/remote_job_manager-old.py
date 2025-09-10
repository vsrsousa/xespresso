import paramiko
import os

class RemoteJobManager:
    def __init__(self, host, user, key_path, remote_base="/home/{user}/jobs", port=22):
        self.host = host
        self.user = user
        self.key_path = key_path
        self.port = port
        self.remote_base = remote_base.format(user=user)

    def submit(self, local_dir, job_file=".job_file", prefix="test.pwi"):
        remote_dir = f"{self.remote_base}/job_{int(os.times()[4])}"

        # Conecta via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.user, key_filename=self.key_path, port=self.port)

        # Cria diretório remoto
        ssh.exec_command(f"mkdir -p {remote_dir}")

        # Envia arquivos
        sftp = ssh.open_sftp()
        for file in os.listdir(local_dir):
            sftp.put(os.path.join(local_dir, file), f"{remote_dir}/{file}")
        sftp.close()

        # Detecta se Slurm está disponível
        stdin, stdout, stderr = ssh.exec_command("command -v sbatch")
        slurm_path = stdout.read().decode().strip()

        # Decide como submeter
        if slurm_path:
            print("✅ Slurm detectado. Submetendo com sbatch.")
            exec_cmd = f"cd {remote_dir} && sbatch {job_file}"
        elif job_file in os.listdir(local_dir):
            print("⚠️ Slurm não detectado. Executando com bash.")
            exec_cmd = f"cd {remote_dir} && bash {job_file}"
        else:
            print("🔧 Sem Slurm e sem .job_file. Executando diretamente com pw.x.")
            output_file = prefix.replace(".pwi", ".pwo")
            exec_cmd = f"cd {remote_dir} && pw.x < {prefix} > {output_file}"

        # Executa comando remoto
        stdin, stdout, stderr = ssh.exec_command(exec_cmd)
        print(stdout.read().decode())
        ssh.close()
