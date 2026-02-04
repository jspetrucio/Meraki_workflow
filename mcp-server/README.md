# Meraki Workflow MCP Server

MCP (Model Context Protocol) Server que expõe funcionalidades do Meraki Workflow para Claude Desktop.

## Quick Start (5 minutos)

### 1. Clonar o Repositório

```bash
git clone https://github.com/yourusername/Meraki_Workflow.git
cd Meraki_Workflow
```

### 2. Instalar Dependências

```bash
# Criar virtual environment (recomendado)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install meraki python-dotenv pydantic pyyaml click rich jinja2 mcp
```

### 3. Configurar Claude Desktop

Edite o arquivo de configuração do Claude Desktop:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Adicione:

```json
{
  "mcpServers": {
    "meraki-workflow": {
      "command": "python",
      "args": ["-m", "mcp_server.src.server"],
      "cwd": "/CAMINHO/COMPLETO/PARA/Meraki_Workflow",
      "env": {
        "PYTHONPATH": "/CAMINHO/COMPLETO/PARA/Meraki_Workflow"
      }
    }
  }
}
```

**Importante:** Substitua `/CAMINHO/COMPLETO/PARA/Meraki_Workflow` pelo caminho real no seu sistema.

### 4. Reiniciar Claude Desktop

Feche completamente e reabra o Claude Desktop para carregar o servidor MCP.

### 5. Testar

No Claude Desktop, diga:

```
Use a ferramenta meraki_list_networks para listar as redes disponíveis
```

## Tools Disponíveis (6)

### `meraki_discover`

Executa discovery completo de uma rede Meraki. Retorna topologia, status dos devices e issues identificados.

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `client` | string | Sim | Nome do cliente (ex: "acme") |
| `full` | boolean | Não | Discovery completo (default: true) |
| `save` | boolean | Não | Salvar snapshot (default: true) |
| `profile` | string | Não | Profile de credenciais (default: "default") |

**Exemplo:**
```
Execute meraki_discover para o cliente "acme" com discovery completo
```

### `meraki_list_networks`

Lista networks de uma organização Meraki com tipos, tags e opcionalmente devices.

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `org_id` | string | Não | Organization ID |
| `profile` | string | Não | Profile de credenciais |
| `include_devices` | boolean | Não | Incluir contagem de devices |

**Exemplo:**
```
Liste as networks com meraki_list_networks incluindo contagem de devices
```

### `meraki_configure`

Aplica configuração a uma rede Meraki. Suporta SSID, Firewall e VLAN.

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `network_id` | string | Sim | ID da network (ex: "N_123456") |
| `config_type` | enum | Sim | Tipo: "ssid", "firewall", "vlan" |
| `params` | object | Sim | Parâmetros da configuração |
| `client` | string | Sim | Nome do cliente |
| `dry_run` | boolean | Não | Validar sem aplicar (default: false) |

**Exemplo:**
```
Configure um SSID "Visitantes" na network N_123 para o cliente acme
```

### `meraki_create_workflow`

Cria um novo workflow a partir de template usando Clone + Patch. Gera IDs únicos automaticamente.

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `template` | string | Sim | Nome do template |
| `client` | string | Sim | Nome do cliente |
| `name` | string | Sim | Nome do novo workflow |
| `description` | string | Não | Descrição |
| `variables` | object | Não | Variáveis do template |

**Exemplo:**
```
Crie um workflow de "Device Offline Handler" para o cliente acme chamado "Alerta Offline"
```

### `meraki_report`

Gera relatórios para redes Meraki. Suporta discovery, changes, inventory e security.

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `client` | string | Sim | Nome do cliente |
| `report_type` | enum | Não | Tipo: "discovery", "changes", "inventory", "security" |
| `output_format` | enum | Não | Formato: "html", "pdf" |
| `days` | integer | Não | Dias para relatório de changes |

**Exemplo:**
```
Gere um relatório de discovery em HTML para o cliente acme
```

### `meraki_get_device_status`

Obtém status detalhado de um device Meraki incluindo uplinks e clientes conectados.

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `serial` | string | Sim | Serial do device (ex: "Q2XX-XXXX-XXXX") |
| `profile` | string | Não | Profile de credenciais |
| `include_clients` | boolean | Não | Incluir lista de clientes |
| `include_uplinks` | boolean | Não | Incluir status de uplinks |

**Exemplo:**
```
Qual o status do device Q2XX-1234-5678?
```

## Prompts Disponíveis (3)

### `onboarding`

Guia interativo de setup inicial para novos usuários.

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `api_key` | Sim | API Key do Meraki Dashboard |
| `org_id` | Sim | Organization ID |
| `client_name` | Sim | Nome do cliente |

### `select_agent`

Ajuda a escolher o agente especializado correto (meraki-specialist, network-analyst, workflow-creator).

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `task_description` | Não | Descrição da tarefa |

### `troubleshoot`

Diagnóstico guiado de problemas comuns de rede Meraki.

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `problem_type` | Não | Tipo: device_offline, slow_network, connectivity, wireless, security |
| `description` | Não | Contexto adicional do problema |

## Estrutura do Projeto

```
mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py              # Entry point MCP
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── discovery.py       # meraki_discover
│   │   ├── network.py         # meraki_list_networks
│   │   ├── config.py          # meraki_configure
│   │   ├── workflow.py        # meraki_create_workflow
│   │   ├── report.py          # meraki_report
│   │   └── device.py          # meraki_get_device_status
│   └── prompts/
│       ├── __init__.py
│       ├── onboarding.py      # Prompt de onboarding
│       ├── select_agent.py    # Prompt de seleção de agente
│       └── troubleshoot.py    # Prompt de troubleshooting
├── mcp.json                   # Manifest MCP
├── requirements.txt
└── README.md
```

## Configuração de Credenciais

Antes de usar as tools, configure suas credenciais Meraki:

```bash
mkdir -p ~/.meraki
cat > ~/.meraki/credentials << 'EOF'
[default]
api_key = SUA_API_KEY_AQUI
org_id = SEU_ORG_ID_AQUI
EOF
```

### Múltiplos Clientes

```ini
[default]
api_key = API_KEY_PADRAO
org_id = ORG_ID_PADRAO

[cliente-acme]
api_key = API_KEY_ACME
org_id = ORG_ID_ACME

[cliente-xyz]
api_key = API_KEY_XYZ
org_id = ORG_ID_XYZ
```

Use o parâmetro `profile` nas tools para especificar qual cliente usar.

## Desenvolvimento

### Testar Localmente

```bash
# Rodar servidor diretamente
cd /path/to/Meraki_Workflow
python -m mcp_server.src.server

# Ou usar MCP Inspector
npx @modelcontextprotocol/inspector python -m mcp_server.src.server
```

### Rodar Testes

```bash
# Testes de integração
cd /path/to/Meraki_Workflow
python -m pytest tests/test_mcp_server.py -v

# Testes do Template Loader
python -m pytest tests/test_template_loader.py -v
```

### Adicionar Novos Tools

1. Criar arquivo em `src/tools/nova_tool.py`
2. Definir função async e `TOOL_SCHEMA`
3. Importar e registrar em `src/tools/__init__.py`
4. Adicionar handler em `server.py`
5. Atualizar `mcp.json`

## Troubleshooting

### "MCP SDK not installed"

```bash
pip install mcp
```

### "Module import failed"

Certifique-se de que está rodando a partir do diretório raiz do projeto:

```bash
cd /path/to/Meraki_Workflow
python -m mcp_server.src.server
```

### "Credenciais não encontradas"

Configure em `~/.meraki/credentials`:

```ini
[default]
api_key = YOUR_API_KEY
org_id = YOUR_ORG_ID
```

### Claude Desktop não mostra as tools

1. Verifique se o caminho no config está correto
2. Verifique se o Python está no PATH
3. Reinicie completamente o Claude Desktop
4. Verifique logs em: `~/Library/Logs/Claude/mcp*.log` (macOS)

## Status do Projeto

- [x] Sprint 1: Template Loader (Clone + Patch)
- [x] Sprint 2: MCP Server Base (estrutura + 2 tools)
- [x] Sprint 3: MCP Server Completo (6 tools + 3 prompts)
- [x] Sprint 4: Integração e testes com Claude Desktop
- [ ] Sprint 5: Squad N8N + Agente
- [ ] Sprint 6: Templates N8N + Documentação Final

## Contribuição

1. Fork o repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

## Licença

MIT License - veja LICENSE para detalhes.
