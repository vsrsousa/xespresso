# XEspresso GUI

Interface web interativa para gerenciar configurações do XEspresso usando Streamlit.

## Funcionalidades Implementadas

### ✅ Configuração de Máquinas
- Visualizar máquinas configuradas
- Criar novas configurações de máquinas
- Editar máquinas existentes
- Deletar configurações
- Suporte para:
  - Execução local e remota (SSH)
  - Schedulers: Direct e SLURM
  - Configuração de recursos (nodes, tasks, walltime, partition)
  - Módulos do sistema
  - Autenticação SSH com chaves

### ✅ Configuração de Códigos
- Visualizar códigos configurados por máquina
- Criar novas configurações de códigos
- Editar códigos existentes
- Deletar configurações
- Suporte para:
  - Múltiplos códigos do Quantum ESPRESSO
  - Versões diferentes do QE
  - Módulos e variáveis de ambiente
  - Detecção de códigos comuns (pw, hp, dos, bands, etc.)

### 🚧 Funcionalidades Futuras
- Dashboard de status
- Gerenciamento de workflows
- Monitoramento de jobs
- Visualização de resultados

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

Ou instale apenas o Streamlit se já tem o XEspresso:
```bash
pip install streamlit>=1.28.0
```

## Como Usar

### Método 1: Script direto

```bash
cd /caminho/para/xespresso
streamlit run gui/app.py
```

### Método 2: Usar o script auxiliar

```bash
cd /caminho/para/xespresso
python scripts/run_gui.py
```

### Método 3: Comando direto do Python

```bash
cd /caminho/para/xespresso
python -m streamlit run gui/app.py
```

A interface será aberta automaticamente no navegador em: http://localhost:8501

## Estrutura de Diretórios

```
xespresso/
├── gui/
│   ├── __init__.py
│   ├── app.py              # Aplicação principal
│   └── pages/
│       ├── __init__.py
│       ├── machines.py     # Página de máquinas
│       └── codes.py        # Página de códigos
├── requirements.txt        # Dependências (inclui streamlit)
└── README_GUI.md          # Este arquivo
```

## Arquivos de Configuração

A GUI gerencia os seguintes arquivos:

### Máquinas
- `~/.xespresso/machines.json` - Arquivo único com todas as máquinas
- `~/.xespresso/machines/<nome>.json` - Arquivos individuais por máquina (recomendado)

### Códigos
- `~/.xespresso/codes/<nome_maquina>.json` - Configuração de códigos por máquina

## Usando a Interface

### Página Inicial (Home)
- Visão geral das funcionalidades
- Status do sistema
- Guias de início rápido

### Página de Máquinas
1. **Visualizar**: Veja todas as máquinas configuradas
2. **Criar Nova**: Adicione uma nova máquina
   - Preencha os campos obrigatórios (nome, execução, scheduler, etc.)
   - Configure opções remotas se necessário (host, username, SSH)
   - Configure recursos SLURM se aplicável
   - Escolha o formato de salvamento
3. **Editar/Deletar**: Modifique ou remova máquinas existentes

### Página de Códigos
1. **Visualizar**: Veja todas as configurações de códigos
2. **Criar Nova**: Adicione uma nova configuração
   - Especifique o nome da máquina
   - Configure o prefix e versão do QE
   - Adicione códigos individuais (pw, hp, dos, etc.)
   - Configure módulos e variáveis de ambiente
3. **Editar/Deletar**: Modifique ou remova configurações existentes

## Dicas

- **Comece com uma máquina local**: É mais fácil testar primeiro localmente
- **Use arquivos individuais**: O formato de arquivo individual é recomendado para melhor organização
- **Configure os códigos após as máquinas**: Os códigos dependem das máquinas configuradas
- **Teste a conectividade SSH**: Certifique-se de que suas chaves SSH estão configuradas antes de configurar máquinas remotas

## Exemplos de Configuração

### Máquina Local Simples
```
Nome: local_desktop
Execução: local
Scheduler: direct
Workdir: ./xespresso
Nprocs: 4
Launcher: mpirun -np {nprocs}
```

### Cluster Remoto com SLURM
```
Nome: cluster_hpc
Execução: remote
Scheduler: slurm
Host: cluster.example.com
Username: seu_usuario
SSH Key: ~/.ssh/id_rsa.pub
Nodes: 2
Tasks per node: 16
Walltime: 24:00:00
Partition: normal
```

### Configuração de Códigos
```
Máquina: local_desktop
QE Prefix: /usr/local/qe-7.2/bin
QE Version: 7.2
Códigos:
  - pw: /usr/local/qe-7.2/bin/pw.x
  - hp: /usr/local/qe-7.2/bin/hp.x
  - dos: /usr/local/qe-7.2/bin/dos.x
```

## Resolução de Problemas

### A GUI não abre
- Verifique se o Streamlit está instalado: `pip install streamlit`
- Tente especificar a porta: `streamlit run gui/app.py --server.port 8502`

### Erro ao salvar configurações
- Verifique as permissões do diretório `~/.xespresso/`
- Certifique-se de que todos os campos obrigatórios estão preenchidos

### Máquinas/Códigos não aparecem
- Verifique se os arquivos JSON estão bem formatados
- Procure por erros de sintaxe JSON nos arquivos de configuração

## Suporte

Para mais informações sobre o XEspresso:
- GitHub: https://github.com/superstar54/xespresso
- Documentação: Consulte os arquivos MD no repositório

## Desenvolvimento Futuro

Funcionalidades planejadas:
- Dashboard de monitoramento de jobs
- Editor de workflows interativo
- Visualização de resultados
- Terminal integrado
- Suporte para mais schedulers (PBS, etc.)
