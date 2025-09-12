import paramiko
import os

class RemoteRunner:
    def __init__(self, hostname, username, remote_base_dir, module_command,
                 port=22, password=None, key_path=None):
        self.hostname = hostname
        self.username = username
        self.remote_base_dir = remote_base_dir
        self.module_command = module_command
        self.port = port
        self.password = password
        self.key_path = key_path

    def _connect(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.key_path:
            key = paramiko.RSAKey.from_private_key_file(self.key_path)
            client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                pkey=key
            )
        else:
            client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password
            )

        return client

    def transfer_inputs(self, local_dir, remote_subdir):
        """
        Transfere os arquivos de entrada para o servidor remoto,
        garantindo que o diretório remoto exista.

        Args:
            local_dir (str): Caminho local contendo os arquivos de entrada.
            remote_subdir (str): Nome do subdiretório remoto dentro de remote_base_dir.
        """
        remote_dir = os.path.join(self.remote_base_dir, remote_subdir)
        client = self._connect()

        # Garante que o diretório remoto exista (criação recursiva)
        client.exec_command(f"mkdir -p {remote_dir}")

        sftp = client.open_sftp()
        for filename in os.listdir(local_dir):
            local_path = os.path.join(local_dir, filename)
            remote_path = os.path.join(remote_dir, filename)
            sftp.put(local_path, remote_path)

        sftp.close()
        client.close()
        print(f"✅ Arquivos transferidos para {remote_dir}")

    def submit_remote_job(self, remote_subdir):
        remote_dir = os.path.join(self.remote_base_dir, remote_subdir)
        client = self._connect()
        command = f"cd {remote_dir} && {self.module_command} && sbatch .job_file"
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()

        if error:
            raise RuntimeError(f"Erro ao submeter job: {error}")
        print(f"🚀 Job submetido: {output.strip()}")
        return output.strip()

    def retrieve_results(self, remote_subdir, local_dir):
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
        print(f"📥 Resultados recuperados para {local_dir}")

    def test_connection(self):
        try:
            client = self._connect()
            client.close()
            print(f"✅ Conexão SSH bem-sucedida com {self.hostname}:{self.port} como {self.username}")
        except Exception as e:
            print(f"❌ Falha na conexão SSH: {e}")

    def check_quantum_espresso(self):
        try:
            client = self._connect()
            # Usa o comando definido pelo usuário para carregar o módulo
            command = f"source /etc/profile && {self.module_command} && which pw.x"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            client.close()

            if output:
                print(f"✅ Quantum ESPRESSO detectado: {output}")
                return output
            else:
                print("⚠️ Quantum ESPRESSO não encontrado. O executável 'pw.x' não está no PATH.")
                if error:
                    print(f"🔍 Mensagem do sistema:\n{error}")
                return None
        except Exception as e:
            print(f"❌ Falha ao verificar Quantum ESPRESSO: {e}")
            return None

    def list_available_modules(self):
        try:
            client = self._connect()
            command = "source /etc/profile && module avail"
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            client.close()

            full_output = output + error  # Junta stdout e stderr
            print("📦 Módulos disponíveis:\n")
            print(full_output)
            return full_output
        except Exception as e:
            print(f"❌ Falha ao listar módulos disponíveis: {e}")
            return None

    def list_remote_files(self, remote_subdir):
        """
        Lista os arquivos presentes no diretório remoto especificado.

        Args:
            remote_subdir (str): Nome do subdiretório remoto dentro de remote_base_dir.

        Returns:
            str: Saída do comando 'ls -lh' com os arquivos listados, ou mensagem de erro.
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
                print(f"⚠️ Erro ao listar arquivos remotos:\n{error}")
            else:
                print(f"📂 Arquivos no servidor ({remote_path}):\n{output}")
            return output
        except Exception as e:
            print(f"❌ Falha ao listar arquivos remotos: {e}")
            return None



