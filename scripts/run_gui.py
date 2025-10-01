#!/usr/bin/env python3
"""
Script para executar a GUI do XEspresso

Uso:
    python scripts/run_gui.py
    python scripts/run_gui.py --port 8502
"""

import sys
import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='Executar XEspresso GUI')
    parser.add_argument('--port', type=int, default=8501, help='Porta para o servidor (padrão: 8501)')
    parser.add_argument('--no-browser', action='store_true', help='Não abrir o navegador automaticamente')
    args = parser.parse_args()
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    gui_app = os.path.join(project_root, 'gui', 'app.py')
    
    if not os.path.exists(gui_app):
        print(f"❌ Erro: Arquivo GUI não encontrado em {gui_app}")
        sys.exit(1)
    
    # Build streamlit command
    cmd = [
        sys.executable, '-m', 'streamlit', 'run',
        gui_app,
        f'--server.port={args.port}'
    ]
    
    if args.no_browser:
        cmd.append('--server.headless=true')
    
    print(f"🚀 Iniciando XEspresso GUI na porta {args.port}...")
    print(f"📂 Diretório: {project_root}")
    print(f"🌐 URL: http://localhost:{args.port}")
    print("\nPara parar o servidor, pressione Ctrl+C\n")
    
    try:
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n\n✅ Servidor GUI encerrado.")
    except Exception as e:
        print(f"\n❌ Erro ao executar GUI: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
