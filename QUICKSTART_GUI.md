# XEspresso GUI - Guia de Uso Rápido

## Como Executar a GUI

### Método 1: Streamlit direto
```bash
cd /caminho/para/xespresso
streamlit run gui/app.py
```

### Método 2: Script auxiliar
```bash
cd /caminho/para/xespresso
python scripts/run_gui.py
```

### Método 3: Com porta customizada
```bash
python scripts/run_gui.py --port 8502
```

A interface será aberta automaticamente no navegador em: http://localhost:8501

## Páginas Disponíveis

### 🏠 Home
- Visão geral das funcionalidades
- Status do sistema
- Guias de início rápido

### 🖥️ Máquinas
**Aba Visualizar:**
- Lista todas as máquinas configuradas
- Mostra detalhes de cada máquina em seções expansíveis
- Exibe configurações de execução, scheduler, recursos SLURM, módulos, etc.

**Aba Criar Nova:**
- Formulário completo para criar uma nova máquina
- Campos para configuração local ou remota
- Suporte para SLURM com recursos (nodes, tasks, walltime, partition)
- Configuração de módulos do sistema
- Escolha do formato de salvamento (individual ou machines.json)

**Aba Editar/Deletar:**
- Selecione uma máquina existente
- Edite qualquer configuração
- Opção para deletar máquinas

### ⚙️ Códigos
**Aba Visualizar:**
- Lista todas as configurações de códigos por máquina
- Mostra QE prefix, version, módulos e variáveis de ambiente
- Tabela com códigos disponíveis (nome, caminho, versão)
- Suporte para múltiplas versões do QE

**Aba Criar Nova:**
- Formulário para criar configuração de códigos
- Campos para QE prefix e version
- Adicionar múltiplos códigos (pw, hp, dos, bands, etc.)
- Configurar módulos e variáveis de ambiente
- Info sobre detecção automática via CLI

**Aba Editar/Deletar:**
- Selecione uma configuração existente
- Edite códigos, módulos, variáveis
- Opção para deletar configurações

## Arquivos de Configuração

### Máquinas
- `~/.xespresso/machines.json` - Todas as máquinas em um arquivo
- `~/.xespresso/machines/<nome>.json` - Arquivo individual por máquina (recomendado)

### Códigos
- `~/.xespresso/codes/<nome_maquina>.json` - Configuração de códigos

## Funcionalidades Futuras (em breve)
- 📊 Dashboard de monitoramento
- 🔧 Gerenciamento de workflows
- Visualização de resultados
- Terminal integrado

## Dicas

1. **Comece com uma máquina local** para testes
2. **Use formato individual** para melhor organização
3. **Configure máquinas antes dos códigos**
4. **Teste conectividade SSH** antes de configurar máquinas remotas

## Exemplo de Fluxo de Trabalho

1. Abra a GUI: `streamlit run gui/app.py`
2. Vá para "Máquinas" > "Criar Nova"
3. Crie uma máquina local de teste
4. Vá para "Códigos" > "Criar Nova"
5. Configure os códigos do QE para essa máquina
6. Use as configurações em seus scripts Python com xespresso

## Resolução de Problemas

**GUI não abre:**
- Instale streamlit: `pip install streamlit`
- Verifique a porta: `streamlit run gui/app.py --server.port 8502`

**Erro ao salvar:**
- Verifique permissões em `~/.xespresso/`
- Certifique-se de preencher campos obrigatórios

**Configurações não aparecem:**
- Verifique se os arquivos JSON estão bem formatados
- Olhe os logs no terminal para erros de parsing
