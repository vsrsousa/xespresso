"""
Codes configuration page for XEspresso GUI
"""

import streamlit as st
import json
import os
from typing import Dict, Optional, List

# Default paths
CODES_DIR = os.path.expanduser("~/.xespresso/codes")

def load_codes_configs() -> Dict:
    """Load all codes configurations"""
    configs = {}
    
    if not os.path.exists(CODES_DIR):
        return configs
    
    for filename in os.listdir(CODES_DIR):
        if filename.endswith('.json'):
            machine_name = filename[:-5]  # Remove .json
            try:
                filepath = os.path.join(CODES_DIR, filename)
                with open(filepath, 'r') as f:
                    config = json.load(f)
                    configs[machine_name] = config
            except Exception as e:
                st.warning(f"Erro ao carregar {filename}: {e}")
    
    return configs

def save_codes_config(machine_name: str, config: Dict):
    """Save codes configuration"""
    try:
        os.makedirs(CODES_DIR, exist_ok=True)
        filepath = os.path.join(CODES_DIR, f"{machine_name}.json")
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True, f"Configuração salva em {filepath}"
    except Exception as e:
        return False, f"Erro ao salvar: {e}"

def delete_codes_config(machine_name: str):
    """Delete a codes configuration"""
    try:
        filepath = os.path.join(CODES_DIR, f"{machine_name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao deletar: {e}")
        return False

def show():
    """Main function to display codes page"""
    st.markdown('<div class="main-header">⚙️ Configuração de Códigos</div>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📋 Visualizar", "➕ Criar Nova", "✏️ Editar/Deletar"])
    
    with tab1:
        show_codes_list()
    
    with tab2:
        show_create_codes()
    
    with tab3:
        show_edit_codes()

def show_codes_list():
    """Display list of configured codes"""
    st.subheader("Configurações de Códigos")
    
    configs = load_codes_configs()
    
    if not configs:
        st.info("Nenhuma configuração de código encontrada. Use a aba 'Criar Nova' para adicionar uma.")
        return
    
    # Display configurations
    for machine_name, config in configs.items():
        with st.expander(f"⚙️ {machine_name}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Informações Gerais**")
                st.text(f"Máquina: {config.get('machine_name', 'N/A')}")
                st.text(f"QE Prefix: {config.get('qe_prefix', 'N/A')}")
                st.text(f"QE Version: {config.get('qe_version', 'N/A')}")
            
            with col2:
                # Show modules if present
                if config.get('modules'):
                    st.markdown("**Módulos**")
                    st.code('\n'.join(config.get('modules', [])))
                
                # Show environment if present
                if config.get('environment'):
                    st.markdown("**Variáveis de Ambiente**")
                    for key, value in config.get('environment', {}).items():
                        st.text(f"{key}={value}")
            
            # Display codes
            st.markdown("**Códigos Disponíveis**")
            codes = config.get('codes', {})
            
            if not codes:
                st.info("Nenhum código configurado")
            else:
                # Create a table of codes
                codes_data = []
                for code_name, code_info in codes.items():
                    if isinstance(code_info, dict):
                        codes_data.append({
                            "Nome": code_name,
                            "Caminho": code_info.get('path', 'N/A'),
                            "Versão": code_info.get('version', 'N/A')
                        })
                    else:
                        codes_data.append({
                            "Nome": code_name,
                            "Caminho": str(code_info),
                            "Versão": "N/A"
                        })
                
                import pandas as pd
                df = pd.DataFrame(codes_data)
                st.dataframe(df, use_container_width=True)
            
            # Show versions if present
            if config.get('versions'):
                st.markdown("**Múltiplas Versões**")
                for version, version_config in config.get('versions', {}).items():
                    with st.expander(f"Versão {version}"):
                        st.text(f"QE Prefix: {version_config.get('qe_prefix', 'N/A')}")
                        if version_config.get('modules'):
                            st.text(f"Módulos: {', '.join(version_config.get('modules', []))}")
                        
                        version_codes = version_config.get('codes', {})
                        if version_codes:
                            st.text(f"Códigos: {', '.join(version_codes.keys())}")
            
            # Show raw JSON
            if st.checkbox(f"Mostrar JSON completo - {machine_name}", key=f"json_{machine_name}"):
                st.json(config)

def show_create_codes():
    """Form to create a new codes configuration"""
    st.subheader("Criar Nova Configuração de Códigos")
    
    st.info("💡 Esta interface permite criar configurações manualmente. Para detecção automática, use o CLI: `python -m xespresso.codes.manager --detect`")
    
    with st.form("create_codes_form"):
        st.markdown("### Informações Básicas")
        
        machine_name = st.text_input(
            "Nome da Máquina*",
            placeholder="ex: local_desktop, cluster_a",
            help="Nome da máquina (deve corresponder a uma máquina configurada)"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            qe_prefix = st.text_input(
                "QE Prefix",
                placeholder="/usr/local/qe-7.2/bin",
                help="Diretório onde estão os executáveis do QE"
            )
        
        with col2:
            qe_version = st.text_input(
                "QE Version",
                placeholder="7.2",
                help="Versão do Quantum ESPRESSO"
            )
        
        # Modules
        st.markdown("### Módulos (Opcional)")
        modules_text = st.text_area(
            "Módulos (um por linha)",
            placeholder="quantum-espresso/7.2\nintel/2021",
            help="Módulos a serem carregados antes da execução"
        )
        modules = []
        if modules_text:
            modules = [m.strip() for m in modules_text.split('\n') if m.strip()]
        
        # Environment variables
        st.markdown("### Variáveis de Ambiente (Opcional)")
        env_text = st.text_area(
            "Variáveis (formato: VAR=valor, uma por linha)",
            placeholder="OMP_NUM_THREADS=4\nMKL_NUM_THREADS=4",
            help="Variáveis de ambiente a serem definidas"
        )
        environment = {}
        if env_text:
            for line in env_text.split('\n'):
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    environment[key.strip()] = value.strip()
        
        # Codes
        st.markdown("### Códigos do Quantum ESPRESSO")
        st.info("Adicione os códigos que você deseja usar. Códigos comuns: pw, hp, dos, bands, projwfc, pp, neb")
        
        # Common QE codes
        common_codes = ['pw', 'hp', 'dos', 'bands', 'projwfc', 'pp', 'neb', 'ph', 'dvscf', 'turbo_lanczos']
        
        codes = {}
        num_codes = st.number_input("Número de códigos", min_value=1, max_value=20, value=3)
        
        for i in range(num_codes):
            st.markdown(f"**Código {i+1}**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                code_name = st.selectbox(
                    "Nome",
                    options=common_codes + ["outro"],
                    key=f"code_name_{i}"
                )
                if code_name == "outro":
                    code_name = st.text_input("Nome customizado", key=f"code_custom_{i}")
            
            with col2:
                code_path = st.text_input(
                    "Caminho",
                    placeholder=f"/usr/local/bin/{code_name}.x" if code_name != "outro" else "/usr/local/bin/code.x",
                    key=f"code_path_{i}"
                )
            
            with col3:
                code_version = st.text_input(
                    "Versão",
                    value=qe_version if qe_version else "",
                    key=f"code_version_{i}"
                )
            
            if code_name and code_path:
                codes[code_name] = {
                    "name": code_name,
                    "path": code_path,
                    "version": code_version if code_version else qe_version
                }
        
        submitted = st.form_submit_button("✅ Criar Configuração", type="primary")
        
        if submitted:
            if not machine_name:
                st.error("❌ Nome da máquina é obrigatório!")
                return
            
            # Check if already exists
            existing = load_codes_configs()
            if machine_name in existing:
                st.error(f"❌ Configuração para '{machine_name}' já existe! Use a aba 'Editar/Deletar' para modificá-la.")
                return
            
            if not codes:
                st.error("❌ Adicione pelo menos um código!")
                return
            
            # Build config
            config = {
                "machine_name": machine_name,
                "codes": codes
            }
            
            if qe_prefix:
                config["qe_prefix"] = qe_prefix
            if qe_version:
                config["qe_version"] = qe_version
            if modules:
                config["modules"] = modules
            if environment:
                config["environment"] = environment
            
            # Save
            success, message = save_codes_config(machine_name, config)
            
            if success:
                st.success(f"✅ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")

def show_edit_codes():
    """Edit or delete existing codes configurations"""
    st.subheader("Editar ou Deletar Configuração de Códigos")
    
    configs = load_codes_configs()
    
    if not configs:
        st.info("Nenhuma configuração de código para editar.")
        return
    
    selected_machine = st.selectbox(
        "Selecione uma configuração",
        options=list(configs.keys())
    )
    
    if selected_machine:
        config = configs[selected_machine]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"Editando: **{selected_machine}**")
        
        with col2:
            if st.button("🗑️ Deletar", type="secondary", use_container_width=True):
                if delete_codes_config(selected_machine):
                    st.success(f"✅ Configuração '{selected_machine}' deletada!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao deletar configuração")
        
        # Edit form
        with st.form("edit_codes_form"):
            st.markdown("### Informações Básicas")
            
            col1, col2 = st.columns(2)
            with col1:
                qe_prefix = st.text_input(
                    "QE Prefix",
                    value=config.get('qe_prefix', ''),
                    placeholder="/usr/local/qe-7.2/bin"
                )
            
            with col2:
                qe_version = st.text_input(
                    "QE Version",
                    value=config.get('qe_version', ''),
                    placeholder="7.2"
                )
            
            # Modules
            st.markdown("### Módulos")
            current_modules = config.get('modules', [])
            modules_text = st.text_area(
                "Módulos (um por linha)",
                value='\n'.join(current_modules)
            )
            modules = []
            if modules_text:
                modules = [m.strip() for m in modules_text.split('\n') if m.strip()]
            
            # Environment
            st.markdown("### Variáveis de Ambiente")
            current_env = config.get('environment', {})
            env_lines = [f"{k}={v}" for k, v in current_env.items()]
            env_text = st.text_area(
                "Variáveis (formato: VAR=valor, uma por linha)",
                value='\n'.join(env_lines)
            )
            environment = {}
            if env_text:
                for line in env_text.split('\n'):
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        environment[key.strip()] = value.strip()
            
            # Codes
            st.markdown("### Códigos")
            current_codes = config.get('codes', {})
            
            # Convert codes to editable format
            codes_list = []
            for code_name, code_info in current_codes.items():
                if isinstance(code_info, dict):
                    codes_list.append({
                        'name': code_name,
                        'path': code_info.get('path', ''),
                        'version': code_info.get('version', qe_version)
                    })
            
            num_codes = st.number_input(
                "Número de códigos",
                min_value=1,
                max_value=20,
                value=max(len(codes_list), 1)
            )
            
            common_codes = ['pw', 'hp', 'dos', 'bands', 'projwfc', 'pp', 'neb', 'ph', 'dvscf', 'turbo_lanczos']
            codes = {}
            
            for i in range(num_codes):
                st.markdown(f"**Código {i+1}**")
                col1, col2, col3 = st.columns(3)
                
                # Get existing values if available
                existing_code = codes_list[i] if i < len(codes_list) else {'name': '', 'path': '', 'version': qe_version}
                
                with col1:
                    if existing_code['name'] in common_codes:
                        default_idx = common_codes.index(existing_code['name'])
                    else:
                        default_idx = len(common_codes)  # "outro"
                    
                    code_name = st.selectbox(
                        "Nome",
                        options=common_codes + ["outro"],
                        index=default_idx,
                        key=f"edit_code_name_{i}"
                    )
                    if code_name == "outro":
                        code_name = st.text_input(
                            "Nome customizado",
                            value=existing_code['name'] if existing_code['name'] not in common_codes else '',
                            key=f"edit_code_custom_{i}"
                        )
                
                with col2:
                    code_path = st.text_input(
                        "Caminho",
                        value=existing_code['path'],
                        key=f"edit_code_path_{i}"
                    )
                
                with col3:
                    code_version = st.text_input(
                        "Versão",
                        value=existing_code.get('version', qe_version),
                        key=f"edit_code_version_{i}"
                    )
                
                if code_name and code_path:
                    codes[code_name] = {
                        "name": code_name,
                        "path": code_path,
                        "version": code_version if code_version else qe_version
                    }
            
            submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
            
            if submitted:
                if not codes:
                    st.error("❌ Adicione pelo menos um código!")
                    return
                
                # Build updated config
                updated_config = {
                    "machine_name": selected_machine,
                    "codes": codes
                }
                
                if qe_prefix:
                    updated_config["qe_prefix"] = qe_prefix
                if qe_version:
                    updated_config["qe_version"] = qe_version
                if modules:
                    updated_config["modules"] = modules
                if environment:
                    updated_config["environment"] = environment
                
                # Preserve versions if they exist
                if config.get('versions'):
                    updated_config["versions"] = config["versions"]
                
                success, message = save_codes_config(selected_machine, updated_config)
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
