import paramiko
import os
import json
from datetime import datetime
import time
import getpass

class RemoteJobManager:
    def __init__(self, host, user, key_path=None, password=None, remote_base="/home/{user}/jobs", port=22):
        self.host = host
        self.user = user
        self.key_path = os.path.expanduser(key_path) if key_path else None
        self.password = password
        self.port = port
        self.remote_base = remote_base.format(user=user)
        self.ssh_connected = False
        self.ssh_client = None
        
        if not self.key_path and not self.password:
            raise ValueError("Deve fornecer key_path ou password para autenticação")

    def _read_queue_config(self, local_dir, job_file=".job_file"):
        """Lê a configuração do scheduler do arquivo de submissão"""
        job_file_path = os.path.join(local_dir, job_file)
        
        if os.path.exists(job_file_path):
            with open(job_file_path, 'r') as f:
                content = f.read()
                if '#SBATCH' in content:
                    return 'slurm'
                elif '#PBS' in content:
                    return 'pbs'
                elif '#!/bin/bash' in content or '#!/bin/sh' in content:
                    return 'direct'
    
        # Fallback: verifica se existe arquivo de info anterior
        info_path = os.path.join(local_dir, ".remote_info.json")
        if os.path.exists(info_path):
            with open(info_path) as f:
                info = json.load(f)
                if "scheduler" in info:
                    return info["scheduler"]
        
        # Verifica se existe arquivo .pwi para execução direta do pw.x
        pwi_files = [f for f in os.listdir(local_dir) if f.endswith('.pwi')]
        if pwi_files:
            return 'direct'
        
        return 'direct'  # Default

    def _connect_ssh(self):
        """Estabelece conexão SSH usando chave ou senha (reutiliza conexão)"""
        if self.ssh_connected and self.ssh_client:
            return self.ssh_client
            
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.key_path:
                ssh.connect(self.host, username=self.user, key_filename=self.key_path, port=self.port)
            else:
                if not self.password:
                    # Pede senha apenas uma vez
                    self.password = getpass.getpass(f"Senha para {self.user}@{self.host}: ")
                ssh.connect(self.host, username=self.user, password=self.password, port=self.port)
            
            self.ssh_client = ssh
            self.ssh_connected = True
            return ssh
            
        except paramiko.AuthenticationException:
            raise Exception("❌ Autenticação falhou. Verifique chave/senha.")
        except Exception as e:
            raise Exception(f"❌ Erro de conexão: {e}")

    def _disconnect_ssh(self):
        """Fecha conexão SSH"""
        if self.ssh_connected and self.ssh_client:
            self.ssh_client.close()
            self.ssh_connected = False
            self.ssh_client = None

    def _execute_command(self, command):
        """Executa comando SSH reutilizando a conexão"""
        ssh = self._connect_ssh()
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        return output, error

    def test_connection(self):
        """Testa a conexão SSH"""
        try:
            ssh = self._connect_ssh()
            
            # Testa comando simples
            output, error = self._execute_command("echo 'Connection test'")
            
            if error:
                print(f"❌ Erro no teste: {error}")
                return False
            
            print("✅ Conexão SSH bem-sucedida!")
            return True
            
        except Exception as e:
            print(f"❌ {e}")
            return False
        finally:
            self._disconnect_ssh()

    def submit(self, local_dir, job_file=".job_file", prefix=None, remote_dir=None, label=None):
        """Submete um job para execução remota"""
        try:
            # Detecta o arquivo .pwi automaticamente
            if prefix is None:
                for f in os.listdir(local_dir):
                    if f.endswith(".pwi"):
                        prefix = f.replace(".pwi", "")
                        break
                if prefix is None:
                    raise FileNotFoundError("Nenhum arquivo .pwi encontrado no diretório local.")

            # Lê a configuração do scheduler (passa o job_file)
            scheduler_type = self._read_queue_config(local_dir, job_file)
            print(f"🎯 Scheduler detectado: {scheduler_type}")

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
                    output, error = self._execute_command(f"rm -rf {remote_dir}")
                    if error:
                        print(f"⚠️ Erro ao limpar diretório: {error}")
                    os.remove(info_path)
                    remote_dir = None

            # Se label for passado e remote_dir ainda não definido
            if label and remote_dir is None:
                remote_dir = f"{self.remote_base}/{label}"

            # Se ainda não definido, gera com timestamp
            if remote_dir is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                remote_dir = f"{self.remote_base}/{prefix}_{timestamp}"

            # Conecta via SSH (reutiliza conexão)
            ssh = self._connect_ssh()

            # Cria diretório remoto
            output, error = self._execute_command(f"mkdir -p {remote_dir}")
            if error:
                print(f"❌ Erro ao criar diretório: {error}")
                return False

            # Envia todos os arquivos do diretório local
            sftp = ssh.open_sftp()
            for file in os.listdir(local_dir):
                if file not in ['.remote_info.json']:
                    local_path = os.path.join(local_dir, file)
                    if os.path.isfile(local_path):
                        sftp.put(local_path, f"{remote_dir}/{file}")
            sftp.close()

            # Lista arquivos remotos
            output, error = self._execute_command(f"ls {remote_dir}")
            if error:
                print(f"❌ Erro ao listar arquivos: {error}")
                return False
                
            remote_files = output.split()

            # Verifica se o arquivo do job existe
            if job_file not in remote_files:
                print(f"❌ Arquivo {job_file} não encontrado no diretório remoto")
                return False

            # Submissão baseada no tipo de scheduler
            job_id = None
            success = False
            
            if scheduler_type == "slurm":
                success, job_id = self._submit_slurm(remote_dir, job_file)
            elif scheduler_type == "pbs":
                success, job_id = self._submit_pbs(remote_dir, job_file)
            elif scheduler_type == "direct":
                success = self._submit_direct(remote_dir, job_file, prefix)
            else:
                print(f"❌ Tipo de scheduler não suportado: {scheduler_type}")
                success = False

            if not success:
                return False

            # Salva info de submissão localmente
            with open(info_path, "w") as f:
                json.dump({
                    "remote_dir": remote_dir,
                    "host": self.host,
                    "user": self.user,
                    "prefix": prefix,
                    "scheduler": scheduler_type,
                    "job_id": job_id,
                    "submitted": datetime.now().isoformat(),
                    "status": "submitted"
                }, f, indent=2)

            print(f"✅ Job submetido com sucesso!")
            print(f"📁 Diretório remoto: {remote_dir}")
            if job_id:
                print(f"🔢 Job ID: {job_id}")

            return True

        except Exception as e:
            print(f"❌ Erro durante submissão: {e}")
            return False
        finally:
            self._disconnect_ssh()

    def _submit_slurm(self, remote_dir, job_file):
        """Submete job via Slurm"""
        print("✅ Submetendo via Slurm...")
        
        # Verifica se slurm está disponível
        output, error = self._execute_command("command -v sbatch")
        if not output:
            print("❌ Slurm não está disponível no cluster")
            return False, None
        
#        output, error = self._execute_command(f"cd {remote_dir} && sbatch --parsable {job_file}")
        output, error = self._execute_command(f"cd {remote_dir} && sbatch {job_file}")
        
        if error:
            print(f"❌ Erro ao submeter job no Slurm: {error}")
            return False, None
        
        if output and output.isdigit():
            job_id = output
            print(f"✅ Job Slurm submetido. Job ID: {job_id}")
            return True, job_id
        else:
            print("❌ Falha ao submeter job no Slurm")
            return False, None

    def _submit_pbs(self, remote_dir, job_file):
        """Submete job via PBS"""
        print("✅ Submetendo via PBS...")
        
        # Verifica se PBS está disponível
        output, error = self._execute_command("command -v qsub")
        if not output:
            print("❌ PBS não está disponível no cluster")
            return False, None
        
        output, error = self._execute_command(f"cd {remote_dir} && qsub {job_file}")
        
        if error:
            print(f"❌ Erro ao submeter job no PBS: {error}")
            return False, None
        
        if output:
            job_id = output.split('.')[0]
            print(f"✅ Job PBS submetido. Job ID: {job_id}")
            return True, job_id
        else:
            print("❌ Falha ao submeter job no PBS")
            return False, None

    def _submit_direct(self, remote_dir, job_file, prefix):
        """Executa job diretamente (apenas para máquinas locais)"""
        print("⚠️  Executando diretamente...")
        
        # Verifica se é seguro executar
        if not self._is_safe_for_direct_execution():
            print("❌ Ambiente não seguro para execução direta")
            return False
        
        # Executa em background
        output, error = self._execute_command(f"cd {remote_dir} && nohup bash {job_file} > job.out 2> job.err &")
        
        # Verifica se executou
        output, error = self._execute_command(f"ps aux | grep '{job_file}' | grep -v grep")
        if output:
            print("✅ Job executado em background")
            return True
        else:
            print("❌ Falha ao executar job")
            return False

    def _is_safe_for_direct_execution(self):
        """Verifica se é seguro executar cálculo diretamente"""
        try:
            # Verifica se é um nó de login/gerência
            output, error = self._execute_command("hostname")
            hostname = output.lower()
            
            login_indicators = ['login', 'manager', 'head', 'master', 'admin', 'control', 'frontend']
            if any(indicator in hostname for indicator in login_indicators):
                print(f"❌ Host identificado como nó de gerência: {hostname}")
                return False
            
            # Pergunta confirmação para segurança (apenas uma vez por sessão)
            if not hasattr(self, '_direct_execution_confirmed'):
                print(f"⚠️  Host: {hostname}")
                confirm = input("Tem certeza que deseja executar cálculo diretamente? (s/n): ")
                self._direct_execution_confirmed = confirm.lower() == 's'
            
            return self._direct_execution_confirmed
            
        except Exception:
            return False

    def get_job_status(self, local_dir):
        """Verifica status do job remoto"""
        info_path = os.path.join(local_dir, ".remote_info.json")
        if not os.path.exists(info_path):
            return "not_submitted"
        
        try:
            with open(info_path) as f:
                info = json.load(f)
            
            status = "unknown"
            
            if info.get("scheduler") == "slurm" and info.get("job_id"):
                # Verifica status no Slurm
                output, error = self._execute_command(f"squeue -j {info['job_id']} -h -o %T")
                if output:
                    status = f"slurm_{output}"
            
            elif info.get("scheduler") == "pbs" and info.get("job_id"):
                # Verifica status no PBS
                output, error = self._execute_command(f"qstat -f {info['job_id']} | grep job_state")
                if output and '=' in output:
                    status = f"pbs_{output.split('=')[1].strip()}"
            
            # Verificação genérica de conclusão
            output, error = self._execute_command(f"ls {info['remote_dir']}/{info['prefix']}.pwo 2>/dev/null || echo 'none'")
            if "none" not in output:
                status = "completed"
            
            return status
            
        except Exception as e:
            print(f"❌ Erro ao verificar status: {e}")
            return "error"

    def download_results(self, local_dir, overwrite=False):
        """Baixa resultados do cálculo remoto"""
        info_path = os.path.join(local_dir, ".remote_info.json")
        if not os.path.exists(info_path):
            print("❌ Nenhum job submetido deste diretório")
            return False
        
        try:
            with open(info_path) as f:
                info = json.load(f)
            
            ssh = self._connect_ssh()
            sftp = ssh.open_sftp()
            remote_dir = info["remote_dir"]
            
            remote_files = sftp.listdir(remote_dir)
            downloaded = 0
            
            for file in remote_files:
                remote_path = f"{remote_dir}/{file}"
                local_path = os.path.join(local_dir, file)
                
                if overwrite or not os.path.exists(local_path):
                    sftp.get(remote_path, local_path)
                    downloaded += 1
                    print(f"📥 Baixado: {file}")
            
            sftp.close()
            
            print(f"✅ {downloaded} arquivos baixados com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao baixar resultados: {e}")
            return False
        finally:
            self._disconnect_ssh()

    def monitor_job(self, local_dir, interval=30):
        """Monitora o job periodicamente"""
        print(f"👀 Monitorando job (atualiza a cada {interval}s)...")
        
        try:
            while True:
                status = self.get_job_status(local_dir)
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                status_messages = {
                    "completed": "✅ Job concluído!",
                    "slurm_running": "🔄 Job rodando no Slurm",
                    "slurm_pending": "⏳ Job pendente no Slurm", 
                    "pbs_running": "🔄 Job rodando no PBS",
                    "pbs_queued": "⏳ Job na fila do PBS",
                    "error": "❌ Erro no job",
                    "unknown": "❓ Status desconhecido"
                }
                
                print(f"[{timestamp}] Status: {status_messages.get(status, status)}")
                
                if status in ["completed", "error"]:
                    if status == "completed":
                        self.download_results(local_dir)
                    break
                    
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n⏹️  Monitoramento interrompido pelo usuário.")
        finally:
            self._disconnect_ssh()

    def __del__(self):
        """Destrutor - fecha conexão ao destruir objeto"""
        self._disconnect_ssh()