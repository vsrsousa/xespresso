import paramiko
import os
import sys

# Parâmetros de conexão
HOST = "medusa.fis.uerj.br"  # Substitua pelo endereço IP ou nome do host do servidor
USER = "vinicius"  # Substitua pelo seu nome de usuário
#KEY_PATH = "/caminho/para/sua/chave_ss"  # Substitua pelo caminho completo para sua chave privada
PASSWORD = "AcimadeTudoRN@1981"
PORT = 22

def test_connection():
    """Tenta conectar-se ao servidor via SSH e imprime o resultado."""
    print(f"Attempting to connect to {USER}@{HOST}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USER, key_filename=KEY_PATH, port=PORT, password=PASSWORD)
        print("✅ Connection successful!")
        # Opcional: Executa um comando simples para confirmar a conectividade
        stdin, stdout, stderr = ssh.exec_command("echo 'Hello from remote server!'")
        print("Remote command output:")
        print(stdout.read().decode())
    except paramiko.AuthenticationException:
        print("❌ Authentication failed. Please check your username and key path.")
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"❌ SSH connection failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)
    finally:
        ssh.close()
        print("Connection closed.")

if __name__ == "__main__":
    test_connection()
