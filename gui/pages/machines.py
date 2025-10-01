"""
Machines configuration page for XEspresso GUI
"""

import streamlit as st
import json
import os
from typing import Dict, Optional

# Default paths
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.xespresso/machines.json")
MACHINES_DIR = os.path.expanduser("~/.xespresso/machines")

def load_machines() -> Dict:
    """Load all machines from configuration files"""
    machines = {}
    
    # Load from machines.json if exists
    if os.path.exists(DEFAULT_CONFIG_PATH):
        try:
            with open(DEFAULT_CONFIG_PATH, 'r') as f:
                config = json.load(f)
                machines.update(config.get('machines', {}))
        except Exception as e:
            st.error(f"Erro ao carregar machines.json: {e}")
    
    # Load from individual machine files
    if os.path.exists(MACHINES_DIR):
        for filename in os.listdir(MACHINES_DIR):
            if filename.endswith('.json'):
                machine_name = filename[:-5]  # Remove .json
                try:
                    filepath = os.path.join(MACHINES_DIR, filename)
                    with open(filepath, 'r') as f:
                        machine_config = json.load(f)
                        machines[machine_name] = machine_config
                except Exception as e:
                    st.warning(f"Erro ao carregar {filename}: {e}")
    
    return machines

def save_machine(machine_name: str, machine_config: Dict, save_format: str = "individual"):
    """Save machine configuration"""
    try:
        if save_format == "individual":
            # Save as individual file
            os.makedirs(MACHINES_DIR, exist_ok=True)
            filepath = os.path.join(MACHINES_DIR, f"{machine_name}.json")
            with open(filepath, 'w') as f:
                json.dump(machine_config, f, indent=2)
            return True, f"Máquina salva em {filepath}"
        else:
            # Save to machines.json
            os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH), exist_ok=True)
            config = {"machines": {}}
            if os.path.exists(DEFAULT_CONFIG_PATH):
                with open(DEFAULT_CONFIG_PATH, 'r') as f:
                    config = json.load(f)
            
            config["machines"][machine_name] = machine_config
            
            with open(DEFAULT_CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=2)
            return True, f"Máquina salva em {DEFAULT_CONFIG_PATH}"
    except Exception as e:
        return False, f"Erro ao salvar: {e}"

def delete_machine(machine_name: str):
    """Delete a machine configuration"""
    success = False
    
    # Try to delete from individual file
    individual_path = os.path.join(MACHINES_DIR, f"{machine_name}.json")
    if os.path.exists(individual_path):
        try:
            os.remove(individual_path)
            success = True
        except Exception as e:
            st.error(f"Erro ao deletar arquivo individual: {e}")
    
    # Try to delete from machines.json
    if os.path.exists(DEFAULT_CONFIG_PATH):
        try:
            with open(DEFAULT_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            
            if machine_name in config.get("machines", {}):
                del config["machines"][machine_name]
                with open(DEFAULT_CONFIG_PATH, 'w') as f:
                    json.dump(config, f, indent=2)
                success = True
        except Exception as e:
            st.error(f"Erro ao remover de machines.json: {e}")
    
    return success

def show():
    """Main function to display machines page"""
    st.markdown('<div class="main-header">🖥️ Configuração de Máquinas</div>', unsafe_allow_html=True)
    
    # Create tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 Visualizar", "➕ Criar Nova", "✏️ Editar/Deletar"])
    
    with tab1:
        show_machines_list()
    
    with tab2:
        show_create_machine()
    
    with tab3:
        show_edit_machine()

def show_machines_list():
    """Display list of configured machines"""
    st.subheader("Máquinas Configuradas")
    
    machines = load_machines()
    
    if not machines:
        st.info("Nenhuma máquina configurada. Use a aba 'Criar Nova' para adicionar uma máquina.")
        return
    
    # Display machines in expandable sections
    for machine_name, config in machines.items():
        with st.expander(f"🖥️ {machine_name}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Configurações Básicas**")
                st.text(f"Execução: {config.get('execution', 'N/A')}")
                st.text(f"Scheduler: {config.get('scheduler', 'N/A')}")
                st.text(f"Workdir: {config.get('workdir', 'N/A')}")
                st.text(f"Nprocs: {config.get('nprocs', 'N/A')}")
                st.text(f"Launcher: {config.get('launcher', 'N/A')}")
            
            with col2:
                if config.get('execution') == 'remote':
                    st.markdown("**Configurações Remotas**")
                    st.text(f"Host: {config.get('host', 'N/A')}")
                    st.text(f"Username: {config.get('username', 'N/A')}")
                    st.text(f"Port: {config.get('port', 22)}")
                    auth = config.get('auth', {})
                    st.text(f"Auth: {auth.get('method', 'N/A')}")
                
                if config.get('scheduler') == 'slurm':
                    st.markdown("**Recursos SLURM**")
                    resources = config.get('resources', {})
                    st.text(f"Nodes: {resources.get('nodes', 'N/A')}")
                    st.text(f"Tasks/node: {resources.get('ntasks-per-node', 'N/A')}")
                    st.text(f"Time: {resources.get('time', 'N/A')}")
                    st.text(f"Partition: {resources.get('partition', 'N/A')}")
            
            # Show modules if present
            if config.get('use_modules') and config.get('modules'):
                st.markdown("**Módulos**")
                st.code('\n'.join(config.get('modules', [])))
            
            # Show raw JSON
            if st.checkbox(f"Mostrar JSON completo - {machine_name}", key=f"json_{machine_name}"):
                st.json(config)

def show_create_machine():
    """Form to create a new machine"""
    st.subheader("Criar Nova Máquina")
    
    with st.form("create_machine_form"):
        st.markdown("### Informações Básicas")
        
        machine_name = st.text_input(
            "Nome da Máquina*",
            placeholder="ex: local_desktop, cluster_a",
            help="Nome único para identificar esta máquina"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            execution = st.selectbox(
                "Modo de Execução*",
                ["local", "remote"],
                help="Local: executa na máquina atual. Remote: executa via SSH"
            )
        
        with col2:
            scheduler = st.selectbox(
                "Scheduler*",
                ["direct", "slurm"],
                help="Direct: execução direta. SLURM: usa sistema de filas"
            )
        
        workdir = st.text_input(
            "Diretório de Trabalho*",
            value="./xespresso",
            help="Caminho onde os arquivos de cálculo serão armazenados"
        )
        
        nprocs = st.number_input(
            "Número de Processos*",
            min_value=1,
            value=1,
            help="Número de processos MPI para cálculos paralelos"
        )
        
        launcher = st.text_input(
            "Comando Launcher*",
            value="mpirun -np {nprocs}",
            help="Comando para executar jobs. Use {nprocs} como placeholder"
        )
        
        # Remote configuration
        if execution == "remote":
            st.markdown("### Configurações Remotas")
            
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input(
                    "Host*",
                    placeholder="cluster.example.com",
                    help="Endereço do servidor remoto"
                )
                username = st.text_input(
                    "Username*",
                    help="Nome de usuário SSH"
                )
            
            with col2:
                port = st.number_input(
                    "Porta SSH",
                    min_value=1,
                    max_value=65535,
                    value=22
                )
                ssh_key = st.text_input(
                    "Chave SSH*",
                    value="~/.ssh/id_rsa.pub",
                    help="Caminho para a chave pública SSH"
                )
        
        # SLURM configuration
        if scheduler == "slurm":
            st.markdown("### Configurações SLURM")
            
            col1, col2 = st.columns(2)
            with col1:
                nodes = st.number_input("Nodes", min_value=1, value=1)
                ntasks = st.number_input("Tasks per Node", min_value=1, value=1)
            
            with col2:
                time = st.text_input("Walltime", value="01:00:00", placeholder="HH:MM:SS")
                partition = st.text_input("Partition", placeholder="normal")
        
        # Modules configuration
        st.markdown("### Módulos (Opcional)")
        use_modules = st.checkbox("Usar módulos do sistema")
        modules = []
        if use_modules:
            modules_text = st.text_area(
                "Módulos (um por linha)",
                placeholder="quantum-espresso/7.2\nintel/2021",
                help="Módulos a serem carregados antes da execução"
            )
            if modules_text:
                modules = [m.strip() for m in modules_text.split('\n') if m.strip()]
        
        # Save format
        st.markdown("### Formato de Salvamento")
        save_format = st.radio(
            "Como salvar?",
            ["individual", "machines.json"],
            format_func=lambda x: "Arquivo individual (recomendado)" if x == "individual" else "machines.json (tradicional)",
            help="Individual: um arquivo por máquina. machines.json: todas em um arquivo"
        )
        
        submitted = st.form_submit_button("✅ Criar Máquina", type="primary")
        
        if submitted:
            if not machine_name:
                st.error("❌ Nome da máquina é obrigatório!")
                return
            
            # Check if machine already exists
            machines = load_machines()
            if machine_name in machines:
                st.error(f"❌ Máquina '{machine_name}' já existe! Use a aba 'Editar/Deletar' para modificá-la.")
                return
            
            # Build machine config
            machine_config = {
                "execution": execution,
                "scheduler": scheduler,
                "workdir": workdir,
                "nprocs": nprocs,
                "launcher": launcher,
                "use_modules": use_modules,
                "modules": modules,
                "prepend": [],
                "postpend": [],
                "resources": {}
            }
            
            if execution == "remote":
                if not host or not username:
                    st.error("❌ Host e username são obrigatórios para execução remota!")
                    return
                
                machine_config["host"] = host
                machine_config["username"] = username
                machine_config["port"] = port
                machine_config["auth"] = {
                    "method": "key",
                    "ssh_key": ssh_key,
                    "port": port
                }
            
            if scheduler == "slurm":
                machine_config["resources"] = {
                    "nodes": nodes,
                    "ntasks-per-node": ntasks,
                    "time": time,
                    "partition": partition
                }
            
            # Save machine
            success, message = save_machine(machine_name, machine_config, save_format)
            
            if success:
                st.success(f"✅ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")

def show_edit_machine():
    """Edit or delete existing machines"""
    st.subheader("Editar ou Deletar Máquina")
    
    machines = load_machines()
    
    if not machines:
        st.info("Nenhuma máquina configurada para editar.")
        return
    
    selected_machine = st.selectbox(
        "Selecione uma máquina",
        options=list(machines.keys())
    )
    
    if selected_machine:
        config = machines[selected_machine]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"Editando: **{selected_machine}**")
        
        with col2:
            if st.button("🗑️ Deletar", type="secondary", use_container_width=True):
                if delete_machine(selected_machine):
                    st.success(f"✅ Máquina '{selected_machine}' deletada!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao deletar máquina")
        
        # Edit form
        with st.form("edit_machine_form"):
            st.markdown("### Informações Básicas")
            
            col1, col2 = st.columns(2)
            with col1:
                execution = st.selectbox(
                    "Modo de Execução",
                    ["local", "remote"],
                    index=0 if config.get('execution') == 'local' else 1
                )
            
            with col2:
                scheduler = st.selectbox(
                    "Scheduler",
                    ["direct", "slurm"],
                    index=0 if config.get('scheduler') == 'direct' else 1
                )
            
            workdir = st.text_input("Diretório de Trabalho", value=config.get('workdir', './xespresso'))
            nprocs = st.number_input("Número de Processos", min_value=1, value=config.get('nprocs', 1))
            launcher = st.text_input("Comando Launcher", value=config.get('launcher', 'mpirun -np {nprocs}'))
            
            # Remote configuration
            if execution == "remote":
                st.markdown("### Configurações Remotas")
                
                col1, col2 = st.columns(2)
                with col1:
                    host = st.text_input("Host", value=config.get('host', ''))
                    username = st.text_input("Username", value=config.get('username', ''))
                
                with col2:
                    port = st.number_input("Porta SSH", min_value=1, max_value=65535, value=config.get('port', 22))
                    auth = config.get('auth', {})
                    ssh_key = st.text_input("Chave SSH", value=auth.get('ssh_key', '~/.ssh/id_rsa.pub'))
            
            # SLURM configuration
            if scheduler == "slurm":
                st.markdown("### Configurações SLURM")
                resources = config.get('resources', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    nodes = st.number_input("Nodes", min_value=1, value=resources.get('nodes', 1))
                    ntasks = st.number_input("Tasks per Node", min_value=1, value=resources.get('ntasks-per-node', 1))
                
                with col2:
                    time = st.text_input("Walltime", value=resources.get('time', '01:00:00'))
                    partition = st.text_input("Partition", value=resources.get('partition', ''))
            
            # Modules
            st.markdown("### Módulos")
            use_modules = st.checkbox("Usar módulos", value=config.get('use_modules', False))
            modules = []
            if use_modules:
                current_modules = config.get('modules', [])
                modules_text = st.text_area(
                    "Módulos (um por linha)",
                    value='\n'.join(current_modules)
                )
                if modules_text:
                    modules = [m.strip() for m in modules_text.split('\n') if m.strip()]
            
            # Save format
            save_format = st.radio(
                "Formato de salvamento",
                ["individual", "machines.json"],
                format_func=lambda x: "Arquivo individual" if x == "individual" else "machines.json"
            )
            
            submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
            
            if submitted:
                # Build updated config
                updated_config = {
                    "execution": execution,
                    "scheduler": scheduler,
                    "workdir": workdir,
                    "nprocs": nprocs,
                    "launcher": launcher,
                    "use_modules": use_modules,
                    "modules": modules,
                    "prepend": config.get('prepend', []),
                    "postpend": config.get('postpend', []),
                    "resources": {}
                }
                
                if execution == "remote":
                    updated_config["host"] = host
                    updated_config["username"] = username
                    updated_config["port"] = port
                    updated_config["auth"] = {
                        "method": "key",
                        "ssh_key": ssh_key,
                        "port": port
                    }
                
                if scheduler == "slurm":
                    updated_config["resources"] = {
                        "nodes": nodes,
                        "ntasks-per-node": ntasks,
                        "time": time,
                        "partition": partition
                    }
                
                success, message = save_machine(selected_machine, updated_config, save_format)
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
