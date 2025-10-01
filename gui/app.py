"""
XEspresso GUI - Streamlit Web Interface

A web-based interface for managing XEspresso configurations.

Run with: streamlit run gui/app.py
"""

import streamlit as st
import os
import sys

# Add parent directory to path to import xespresso modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.pages import machines, codes

# Page configuration
st.set_page_config(
    page_title="XEspresso GUI",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point"""
    
    # Sidebar navigation
    st.sidebar.markdown("# ⚛️ XEspresso GUI")
    st.sidebar.markdown("---")
    
    # Navigation menu
    page = st.sidebar.radio(
        "Navegação",
        ["🏠 Home", "🖥️ Máquinas", "⚙️ Códigos", "📊 Dashboard (em breve)", "🔧 Workflows (em breve)"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Sobre")
    st.sidebar.info(
        "XEspresso é uma interface para Quantum ESPRESSO "
        "integrada com ASE (Atomic Simulation Environment)."
    )
    
    # Main content area
    if page == "🏠 Home":
        show_home()
    elif page == "🖥️ Máquinas":
        machines.show()
    elif page == "⚙️ Códigos":
        codes.show()
    else:
        st.markdown('<div class="main-header">🚧 Em Desenvolvimento</div>', unsafe_allow_html=True)
        st.info("Esta funcionalidade será implementada em breve!")

def show_home():
    """Show home page"""
    st.markdown('<div class="main-header">⚛️ Bem-vindo ao XEspresso GUI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interface Web para Configuração de Quantum ESPRESSO</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🖥️ Configuração de Máquinas")
        st.markdown("""
        Gerencie suas máquinas (locais ou remotas):
        - ✅ Visualizar máquinas configuradas
        - ✅ Criar novas configurações
        - ✅ Editar máquinas existentes
        - ✅ Suporte para execução local e remota
        - ✅ Configuração de schedulers (Direct, SLURM)
        - ✅ Autenticação SSH com chaves
        """)
        
    with col2:
        st.markdown("### ⚙️ Configuração de Códigos")
        st.markdown("""
        Gerencie códigos do Quantum ESPRESSO:
        - ✅ Visualizar códigos disponíveis
        - ✅ Criar configurações de códigos
        - ✅ Detecção automática de códigos
        - ✅ Suporte para múltiplas versões do QE
        - ✅ Configurar módulos e ambiente
        """)
    
    st.markdown("---")
    
    st.markdown("### 🚀 Início Rápido")
    
    with st.expander("📖 Como usar esta GUI", expanded=True):
        st.markdown("""
        1. **Configurar Máquinas**: Vá para a página "Máquinas" para adicionar suas máquinas de cálculo
        2. **Configurar Códigos**: Vá para a página "Códigos" para definir os executáveis do Quantum ESPRESSO
        3. **Executar Cálculos**: Use as funcionalidades de workflow (em breve) para rodar simulações
        
        **Dica**: Comece configurando uma máquina local para testes antes de configurar clusters remotos.
        """)
    
    with st.expander("📁 Localização dos Arquivos de Configuração"):
        st.code(f"""
Configurações de máquinas:
  - Arquivo único: ~/.xespresso/machines.json
  - Arquivos individuais: ~/.xespresso/machines/<nome>.json

Configurações de códigos:
  - Diretório: ~/.xespresso/codes/
  - Formato: ~/.xespresso/codes/<nome_maquina>.json
        """)
    
    st.markdown("---")
    
    # Status indicators
    st.markdown("### 📊 Status do Sistema")
    col1, col2, col3 = st.columns(3)
    
    machines_dir = os.path.expanduser("~/.xespresso/machines")
    codes_dir = os.path.expanduser("~/.xespresso/codes")
    machines_json = os.path.expanduser("~/.xespresso/machines.json")
    
    with col1:
        if os.path.exists(machines_json) or os.path.exists(machines_dir):
            st.success("✅ Máquinas configuradas")
        else:
            st.warning("⚠️ Nenhuma máquina configurada")
    
    with col2:
        if os.path.exists(codes_dir) and os.listdir(codes_dir):
            st.success("✅ Códigos configurados")
        else:
            st.warning("⚠️ Nenhum código configurado")
    
    with col3:
        try:
            import xespresso
            st.success(f"✅ XEspresso instalado")
        except ImportError:
            st.error("❌ XEspresso não encontrado")

if __name__ == "__main__":
    main()
