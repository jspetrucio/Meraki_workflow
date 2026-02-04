# Squad: N8N Automation

Squad especializado em automação via N8N para ambientes multi-vendor.

## Quando Usar Este Squad

Use quando precisar de:
- Automação sem limites de rate limiting
- Integração multi-vendor (Meraki + Fortinet, Palo Alto, etc.)
- Interface visual para criar workflows
- Integrações não suportadas pelo Meraki Workflows

**NÃO use quando:**
- Ambiente 100% Cisco/Meraki (use Meraki Workflows nativo)
- Precisar de suporte TAC Cisco
- Quiser audit trail nativo Meraki

## Agente Principal

### 🔄 Nate (n8n-specialist)

Especialista em N8N e integrações multi-vendor.

**Ativação:**
```
@squads/n8n-automation/agents/n8n-specialist.md
```

**Comandos principais:**
- `*create-workflow` - Criar workflow N8N
- `*list-nodes` - Listar nodes disponíveis
- `*validate-workflow` - Validar antes de deploy
- `*list-templates` - Templates disponíveis

## Ferramentas Externas

### n8n-mcp

MCP Server que expõe 1,084 nodes do N8N para Claude.

**Instalação:**
```bash
npx n8n-mcp
```

**Claude Desktop config:**
```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio"
      }
    }
  }
}
```

### n8n-skills

7 skills complementares para expertise em N8N:
- n8n Expression Syntax
- n8n MCP Tools Expert
- n8n Workflow Patterns
- n8n Validation Expert
- n8n Node Configuration
- n8n Code JavaScript
- n8n Code Python

## Templates Disponíveis

| Template | Uso |
|----------|-----|
| `meraki-device-offline.json` | Alerta de device offline |
| `meraki-config-backup.json` | Backup agendado |
| `meraki-discovery-scheduled.json` | Discovery diário |
| `multi-vendor-alert.json` | Alerta multi-vendor |

## Estrutura do Squad

```
squads/n8n-automation/
├── squad.yaml              # Manifest
├── README.md               # Este arquivo
├── config/
│   ├── n8n-setup.md       # Setup N8N
│   └── meraki-nodes.md    # Nodes Meraki
├── agents/
│   └── n8n-specialist.md  # Agente Nate
├── tasks/
│   ├── create-n8n-workflow.md
│   ├── deploy-n8n-instance.md
│   ├── migrate-meraki-to-n8n.md
│   └── validate-n8n-workflow.md
├── templates/
│   └── n8n-workflows/
├── checklists/
│   └── n8n-workflow-review.md
└── data/
    ├── n8n-meraki-nodes.md
    └── n8n-vs-meraki-workflows.md
```

## Referências

- [n8n-mcp](https://github.com/czlonkowski/n8n-mcp)
- [n8n-skills](https://github.com/czlonkowski/n8n-skills)
- [N8N Docs](https://docs.n8n.io/)
- [Meraki Workflows](https://documentation.meraki.com/Platform_Management/Workflows)
