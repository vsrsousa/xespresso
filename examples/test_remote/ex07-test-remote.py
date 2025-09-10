#!/usr/bin/env python3
"""
Teste de submissão remota para cálculos Quantum ESPRESSO usando xespresso
"""

from xespresso import Espresso
from ase.build import bulk
from xespresso.remote_job_manager import RemoteJobManager
import os
import getpass

def test_remote_calculation():
    """Testa um cálculo remoto completo do Quantum ESPRESSO"""
    
    print("🔬 Teste de Cálculo Remoto - Quantum ESPRESSO")
    print("=" * 50)
    label="si_teste/scf"
    
    # =========================================================================
    # 1. CONFIGURAÇÃO DO CÁLCULO LOCAL
    # =========================================================================
    
    print("\n1. 🏗️  Configurando cálculo local...")
    
    # Criar estrutura de Silício
    atoms = bulk("Si", "diamond", a=5.43)
    
    # Configurações do cálculo
    input_data = {
        'calculation': 'scf',
        'outdir': './tmp',
        'prefix': 'si',
        'pseudo_dir': '/home/vinicius/pseudos/',
        'tprnfor': True,
        'tstress': True,
        'disk_io': 'low',
    }
    
    # Pseudopotenciais (ajuste para seus arquivos)
    pseudopotentials = {
#        'Si': 'Si.pbe-n-rrkjus_psl.1.0.0.UPF',
        'Si': 'Si.pz-vbc.UPF'
    }
    
    # Configurações de queue (Slurm)
    queue = {
        "scheduler": "slurm",
        "nodes": 1,
        "ntasks-per-node": 16,
        "time": "00:30:00",
        "partition": "parallel",
        "config": ".xespressorc-medusa",
    }
    
    # Criar calculadora
    calc = Espresso(
        label=label,  # Diretório do cálculo
        queue=queue,
        parallel='srun --mpi=pmi2',
        input_data=input_data,
        pseudopotentials=pseudopotentials,
        kpts=(4, 4, 4),  # Malha k-points
        tprnfor=True,
        tstress=True
    )
    
    # Escrever arquivos de input
    calc.write_input(atoms)
    
    print(f"✅ Cálculo local configurado em: {calc.directory}")
    print(f"📁 Arquivos gerados: {os.listdir(calc.directory)}")
    
    # =========================================================================
    # 2. CONFIGURAÇÃO DO REMOTE JOB MANAGER
    # =========================================================================
    
    print("\n2. 🌐 Configurando conexão remota...")
    
    # Configurações do cluster remoto
    cluster_config = {
        "host": "medusa.fis.uerj.br",  # Ajuste para seu host
        "user": "vinicius",             # Seu usuário no cluster
        "port": 22,                        # Porta SSH
#        "password": "AcimadeTudoRN@1981",
        "remote_base": "/home/{user}/scratch/xespresso"  # Diretório remoto
    }
    
    # Escolher método de autenticação
    print("\n🔐 Métodos de autenticação:")
    print("1. Chave SSH (Recomendado)")
    print("2. Senha")
#    choice = input("Escolha o método (1/2): ")
    choice = 2
    
    if choice == "1":
        # Autenticação por chave SSH
        key_path = input("Caminho para chave SSH [~/.ssh/id_rsa]: ") or "~/.ssh/id_rsa"
        manager = RemoteJobManager(
            host=cluster_config["host"],
            user=cluster_config["user"],
            key_path=key_path,
            port=cluster_config["port"],
            remote_base=cluster_config["remote_base"]
        )
    else:
        # Autenticação por senha
#        password = getpass.getpass(f"Senha para {cluster_config['user']}@{cluster_config['host']}: ")
        password="AcimadeTudoRN@1981"
        manager = RemoteJobManager(
            host=cluster_config["host"],
            user=cluster_config["user"],
            password=password,
            port=cluster_config["port"],
            remote_base=cluster_config["remote_base"]
        )
    
    # Testar conexão
    print("\n🧪 Testando conexão...")
    if not manager.test_connection():
        print("❌ Falha na conexão. Verifique as credenciais.")
        return False
    
    # =========================================================================
    # 3. SUBMISSÃO DO JOB
    # =========================================================================
    
    print("\n3. 🚀 Submetendo job remoto...")
    
    # Submeter o cálculo
    success = manager.submit(
        local_dir=calc.directory,
        job_file="job_file",  # Arquivo do job Slurm
        label="si_test_calculation"  # Nome do job
    )
    
    if not success:
        print("❌ Falha na submissão do job.")
        return False
    
    # =========================================================================
    # 4. MONITORAMENTO E RESULTADOS
    # =========================================================================
    
    print("\n4. 📊 Monitorando execução...")
    
    # Verificar status inicial
    status = manager.get_job_status(calc.directory)
    print(f"Status inicial: {status}")
    
    # Opção para monitoramento automático ou manual
    monitor_choice = input("\nDeseja monitorar automaticamente? (s/n): ")
    
    if monitor_choice.lower() == 's':
        # Monitoramento automático
        print("\n👀 Iniciando monitoramento automático...")
        manager.monitor_job(calc.directory, interval=60)  # Verifica a cada 60s
    else:
        # Monitoramento manual
        print("\n⏳ Aguardando conclusão (use Ctrl+C para parar)...")
        try:
            while True:
                status = manager.get_job_status(calc.directory)
                if status == "completed":
                    print("✅ Cálculo concluído!")
                    break
                elif status == "error":
                    print("❌ Erro no cálculo.")
                    break
                print(f"Status: {status} - Aguardando...")
                time.sleep(60)  # Espera 60 segundos
        except KeyboardInterrupt:
            print("\n⏹️  Monitoramento interrompido pelo usuário.")
    
    # =========================================================================
    # 5. BAIXAR RESULTADOS
    # =========================================================================
    
    print("\n5. 📥 Baixando resultados...")
    
    # Baixar resultados independentemente do status
    download = input("Deseja baixar os resultados? (s/n): ")
    if download.lower() == 's':
        success = manager.download_results(calc.directory)
        if success:
            print("✅ Resultados baixados com sucesso!")
            print(f"📁 Arquivos locais: {os.listdir(calc.directory)}")
        else:
            print("❌ Falha ao baixar resultados.")
    
    # =========================================================================
    # 6. ANALISAR RESULTADOS
    # =========================================================================
    
    print("\n6. 📈 Análise dos resultados...")
    
    # Verificar se temos resultados para analisar
    output_file = os.path.join(calc.directory, "si.pwo")
    if os.path.exists(output_file):
        print("📋 Arquivo de output encontrado. Analisando...")
        
        # Ler e analisar o output
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Extrair informações importantes
        if "JOB DONE" in content:
            print("✅ Cálculo finalizado com sucesso!")
            
            # Extrair energia total
            energy_line = [line for line in content.split('\n') if "!    total energy" in line]
            if energy_line:
                energy = energy_line[0].split()[-2]
                print(f"⚡ Energia total: {energy} Ry")
            
            # Extrair forças
            forces_section = False
            for line in content.split('\n'):
                if "Forces acting on atoms" in line:
                    forces_section = True
                    print("\n🔧 Forças atômicas:")
                elif forces_section and "atom" in line and "force" in line:
                    print(line.strip())
                elif forces_section and line.strip() == "":
                    forces_section = False
        
        else:
            print("❌ Cálculo não finalizado ou com erros.")
            # Mostrar últimas linhas para debug
            last_lines = content.split('\n')[-20:]
            print("\n🔍 Últimas linhas do output:")
            for line in last_lines:
                if line.strip():
                    print(line)
    
    else:
        print("📭 Arquivo de output não encontrado.")
    
    print("\n" + "=" * 50)
    print("🎉 Teste concluído!")
    return True

if __name__ == "__main__":
    import time
    import sys
    
    try:
        # Adicionar o path do xespresso se necessário
        sys.path.append('/path/to/xespresso')
        
        test_remote_calculation()
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("Verifique se xespresso e ase estão instalados:")
        print("pip install ase")
        print("pip install xespresso")
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()