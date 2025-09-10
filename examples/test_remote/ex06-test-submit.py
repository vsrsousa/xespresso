import os
import shutil
from xespresso.remote_job_manager import RemoteJobManager

# --- CONFIGURAÇÃO SSH ---
# Escolha UMA das duas opções abaixo para a autenticação.
# --------------------

# OPÇÃO 1: Usando chave SSH (Recomendado)
#ssh_config = {
#    "host": "seu_host_aqui",
#    "user": "seu_usuario_aqui",
#    "key_path": "/caminho/para/sua/chave_ssh",
#}
user="vinicius"
remote_base=f"/home/{user}/scratch/vinicius/xespresso/"
# OPÇÃO 2: Usando senha (Menos seguro)
ssh_config = {
     "host": "152.92.133.79",
     "user": "vinicius",
     "password": "tomarnocu",
     "port": 222,
     "remote_base": "/home/{user}/scratch/vinicius/xespresso"
 }
# --------------------

# Cria um diretório de teste e um arquivo de exemplo
test_dir = "test_job_simple"
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.makedirs(test_dir, exist_ok=True)

with open(os.path.join(test_dir, "test.pwi"), "w") as f:
    f.write("&CONTROL\n    calculation='scf'\n/ \n&SYSTEM\n    ibrav=2, celldm(1)=10.2, nat=2, ntyp=1\n/")

print(f"📁 Diretório de teste '{test_dir}' e arquivo 'test.pwi' criados com sucesso.")

# --- EXECUÇÃO DO TESTE ---
try:
    # Instancia a classe RemoteJobManager
    manager = RemoteJobManager(**ssh_config)

    # Submete o job para o servidor remoto
    manager.submit(local_dir=remote_base+test_dir, label="teste_simples")

    print("✅ Submissão concluída! Verifique o diretório 'teste_simples' no servidor remoto.")

except Exception as e:
    print(f"❌ Ocorreu um erro durante a submissão: {e}")

finally:
    # Limpa o diretório de teste
#    shutil.rmtree(test_dir)
    print(f"🧹 Diretório de teste '{test_dir}' removido.")