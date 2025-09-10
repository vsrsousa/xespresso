import paramiko
import os
import json
from datetime import datetime

class RemoteJobManager:
    def __init__(self, host, user, key_path, remote_base="/home/{user}/jobs", port=22):
        self.host = host
        self.user = user
        self.key_path = key_path
        self.port = port
        self.remote_base = remote_base.format(user=user)

    def submit(self, local_dir, job_file=".job_file", prefix=None, remote_dir=None, label=None):
        # Detecta o arquivo .pwi automaticamente
        if prefix is None:
            for f in os.listdir(local_dir):
                if f.endswith(".pwi"):
                    prefix = f
                    break
            if prefix is None:
                raise FileNotFoundError("Nenhum arquivo .pwi encontrado no diretório local.")

        # Caminho para o arquivo de rastreamento local
        info_path = os.path.join(local_dir, ".remote_info.json")

        # Se já existe info de submissão anterior
        if os.path.exists(info_path):
            with open(info_path) as f:
                info = json.load(f)
            remote_dir = info["remote_dir"]
            print(f"📁 Cálculo já submetido anteriormente em: {remote_dir}")

            resposta = input("Deseja reiniciar o cálculo do zero? (s/n): ")
            if resposta.lower() == "s":
                print("🧹 Limpando diretório remoto e reiniciando...")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.host, username=self.user, key_filename=self.key_path, port=self.port)
                ssh.exec_command(f"rm -rf {remote_dir}")
                ssh.close()
                os.remove(info_path)
                remote_dir = None  # Gera novo diretório

        # Se label for passado e remote_dir ainda não definido
        if label and remote_dir is None:
            remote_dir = os.path.join(self.remote_base, label)

        # Se ainda não definido, gera com timestamp
        if remote_dir is None:
            remote_dir = f"{self.remote_base}/job_{int(os.times()[4])}"

        # Conecta via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.user, key_filename=self.key_path, port=self.port)

        # Cria diretório remoto
        ssh.exec_command(f"mkdir -p {remote_dir}")

        # Envia todos os arquivos do diretório local
        sftp = ssh.open_sftp()
        for file in os.listdir(local_dir):
            sftp.put(os.path.join(local_dir, file), f"{remote_dir}/{file}")
        sftp.close()

        # Detecta se Slurm está disponível
        stdin, stdout, stderr = ssh.exec_command("command -v sbatch")
        slurm_path = stdout.read().decode().strip()

        # Lista arquivos remotos
        stdin, stdout, stderr = ssh.exec_command(f"ls {remote_dir}")
        remote_files = stdout.read().decode().split()

        # Decide como submeter
        if slurm_path and job_file in remote_files:
            print("✅ Slurm detectado. Submetendo com sbatch.")
            exec_cmd = f"cd {remote_dir} && sbatch {job_file}"
        elif job_file in remote_files:
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

        # Salva info de submissão localmente
        with open(info_path, "w") as f:
            json.dump({
                "remote_dir": remote_dir,
                "host": self.host,
                "submitted": datetime.now().isoformat()
            }, f)

