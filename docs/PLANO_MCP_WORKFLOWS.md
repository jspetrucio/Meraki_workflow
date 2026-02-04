# 🏛️ Plano de Implementação: MCP Server + Workflow Templates

> **Arquiteto**: Aria (@architect)
> **Data**: 2026-02-03
> **Versão**: 1.0

---

## 📋 Resumo Executivo

Este plano resolve os dois problemas identificados:

| Problema | Solução | Esforço |
|----------|---------|---------|
| **1. Workflows não podem ser criados via API** | Clone + Patch (templates exportados) | 1-2 semanas |
| **2. Distribuição do produto** | MCP Server para Claude Desktop | 3-4 semanas |

**Total estimado**: 4-6 semanas para MVP funcional.

---

## 🎯 Objetivos

### Problema 1: Workflow Automation
- [ ] Exportar 5 templates base do Meraki Dashboard
- [ ] Criar sistema de "clone + patch" no Python
- [ ] Permitir que agentes criem workflows parametrizados
- [ ] Workflows prontos para import manual no Dashboard

### Problema 2: Distribuição
- [ ] MCP Server que expõe tools do projeto
- [ ] Onboarding via prompts (API keys, org selection)
- [ ] Chat interface via Claude Desktop
- [ ] Logs em tempo real

---

## 📦 Entregáveis

```
Meraki_Workflow/
├── mcp-server/                    # NOVO: MCP Server
│   ├── src/
│   │   ├── server.py              # Protocolo MCP
│   │   ├── tools/                 # Tools expostos
│   │   │   ├── discovery.py       # mcp__meraki__discover
│   │   │   ├── config.py          # mcp__meraki__configure
│   │   │   ├── workflow.py        # mcp__meraki__create_workflow
│   │   │   └── report.py          # mcp__meraki__generate_report
│   │   └── prompts/               # Prompts guiados
│   │       ├── onboarding.py      # Setup inicial
│   │       └── agent_select.py    # Seleção de agente
│   ├── mcp.json                   # Manifest
│   └── README.md                  # Instalação
│
├── templates/                     # NOVO: Templates exportados
│   └── workflows/
│       ├── device-offline-handler.json      # Template 1
│       ├── security-alert-handler.json      # Template 2
│       ├── firmware-compliance-check.json   # Template 3
│       ├── scheduled-report.json            # Template 4
│       └── bulk-config-change.json          # Template 5
│
├── scripts/
│   ├── workflow.py                # MODIFICAR: Adicionar clone+patch
│   └── template_loader.py         # NOVO: Carrega e parametriza templates
│
└── docs/
    └── PLANO_MCP_WORKFLOWS.md     # Este documento
```

---

## 🔄 Sprint 1: Exportar Templates (Semana 1)

### Objetivo
Obter 5 templates "golden" exportados diretamente do Meraki Dashboard.

### Passo a Passo: Como Exportar Workflow do Dashboard

#### Pré-requisitos
- Acesso ao Meraki Dashboard com permissão de Automation
- Pelo menos 1 workflow existente (ou criar um básico)

#### Passos Detalhados

**1. Acessar Meraki Dashboard**
```
URL: https://dashboard.meraki.com
Login com suas credenciais
```

**2. Navegar para Workflows**
```
Menu lateral → Automation → Workflows
```

**3. Criar ou Selecionar um Workflow**

Se não existir nenhum workflow, crie um básico:
```
1. Clique em "Create Workflow"
2. Escolha "Blank Workflow" ou template do Exchange
3. Dê um nome: "Template - Device Offline Handler"
4. Adicione os blocos básicos:
   - Trigger: Webhook ou Schedule
   - Action: Meraki API Request (GET device status)
   - Condition: Check if offline
   - Action: Send notification (Slack/Email)
5. Salve o workflow
```

**4. Exportar o Workflow como JSON**
```
1. Na lista de Workflows, encontre o workflow criado
2. Clique nos "..." (três pontos) ao lado do workflow
3. Selecione "Export"
4. Escolha formato "JSON"
5. Salve o arquivo com nome descritivo:
   - device-offline-handler.json
   - security-alert-handler.json
   - etc.
```

**5. Verificar o JSON exportado**

O arquivo deve ter esta estrutura:
```json
{
  "workflow": {
    "unique_name": "definition_workflow_XXXXX...",
    "name": "...",
    "type": "generic.workflow",
    "base_type": "workflow",
    ...
  },
  "categories": {
    "category_XXXXX...": { ... }
  }
}
```

**6. Salvar no projeto**
```
Mover para: Meraki_Workflow/templates/workflows/
```

### Templates Necessários

| # | Nome | Trigger | Ação Principal |
|---|------|---------|----------------|
| 1 | device-offline-handler | Webhook/Schedule | Detectar device offline → Notificar |
| 2 | security-alert-handler | Webhook | Evento de segurança → Slack/Teams |
| 3 | firmware-compliance-check | Schedule (weekly) | Verificar firmware → Relatório |
| 4 | scheduled-report | Schedule (daily) | Discovery → Email report |
| 5 | bulk-config-change | Manual | Aplicar config em lote |

### Se não conseguir exportar

**Alternativa A**: Usar Cisco DevNet Exchange
```
1. Acesse: https://developer.cisco.com/codeexchange/
2. Busque por "Meraki Workflow"
3. Baixe exemplos do CiscoDevNet/CiscoWorkflowsAutomation
```

**Alternativa B**: Usar templates existentes no projeto
```
Já existem em: clients/jose-org/workflows/
- device-offline-handler.json
- blink-device-leds.json
```

### Entregável Sprint 1
- [ ] 5 arquivos JSON em `templates/workflows/`
- [ ] Cada arquivo validado com estrutura correta
- [ ] Documentação de cada template

---

## 🔄 Sprint 2: Sistema Clone + Patch (Semana 2)

### Objetivo
Criar `template_loader.py` que permite criar novos workflows baseados em templates.

### Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│  template_loader.py                                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  load_template("device-offline-handler")                     │
│       ↓                                                      │
│  TemplateWorkflow object                                     │
│       ↓                                                      │
│  .set_name("Alerta Cliente ACME")                           │
│  .set_description("...")                                     │
│  .set_variable("webhook_url", "https://...")                │
│  .set_variable("slack_channel", "#alerts")                  │
│       ↓                                                      │
│  .build() → Novo JSON com IDs únicos                        │
│       ↓                                                      │
│  save_workflow("cliente-acme", "acme-offline-alert")        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### API Proposta

```python
from scripts.template_loader import TemplateLoader

# Carregar template base
loader = TemplateLoader()
template = loader.load("device-offline-handler")

# Parametrizar
workflow = template.clone()
workflow.set_name("ACME - Device Offline Alert")
workflow.set_description("Alerta customizado para Cliente ACME")
workflow.set_variable("notification_channel", "#acme-alerts")
workflow.set_variable("severity_threshold", "critical")

# Gerar novo JSON (com novos IDs únicos)
new_workflow = workflow.build()

# Salvar
loader.save(new_workflow, client="acme", name="device-offline-alert")
# → clients/acme/workflows/device-offline-alert.json
```

### Regras do Clone + Patch

| Campo | Comportamento |
|-------|---------------|
| `unique_name` | **REGENERAR** com novo ID de 37 chars |
| `name`, `title` | **SUBSTITUIR** pelo novo nome |
| `description` | **SUBSTITUIR** pela nova descrição |
| `variables[].value` | **SUBSTITUIR** se especificado |
| `actions[].unique_name` | **REGENERAR** IDs |
| `categories` | **MANTER** (ou criar nova categoria) |
| Referências `$workflow.XXX$` | **ATUALIZAR** com novos IDs |

### Entregável Sprint 2
- [ ] `scripts/template_loader.py` implementado
- [ ] Testes em `tests/test_template_loader.py`
- [ ] CLI command: `meraki workflow create --template X --client Y`

---

## 🔄 Sprint 3: MCP Server Base (Semana 3)

### Objetivo
Criar MCP Server que expõe as funcionalidades do projeto.

### Estrutura MCP

```
mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py           # Entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── discovery.py    # Discover network
│   │   ├── config.py       # Apply configurations
│   │   ├── workflow.py     # Create workflows from templates
│   │   └── report.py       # Generate reports
│   └── prompts/
│       ├── __init__.py
│       ├── onboarding.py   # First-time setup
│       └── agents.py       # Agent selection
├── mcp.json                # MCP manifest
├── requirements.txt
└── README.md
```

### Tools Expostos

| Tool | Descrição | Parâmetros |
|------|-----------|------------|
| `meraki_discover` | Executa discovery completo | `client`, `full` |
| `meraki_configure` | Aplica configuração | `network_id`, `config_type`, `params` |
| `meraki_create_workflow` | Cria workflow de template | `template`, `client`, `name`, `variables` |
| `meraki_report` | Gera relatório | `client`, `type`, `format` |
| `meraki_list_networks` | Lista networks | `org_id` |
| `meraki_get_device_status` | Status de device | `serial` |

### Prompts

| Prompt | Propósito |
|--------|-----------|
| `onboarding` | Guia setup inicial (API key, Org ID, cliente) |
| `select_agent` | Escolhe agente especializado |
| `troubleshoot` | Diagnóstico guiado de problemas |

### mcp.json

```json
{
  "name": "meraki-workflow",
  "version": "1.0.0",
  "description": "Meraki Network Automation via Natural Language",
  "tools": [
    {
      "name": "meraki_discover",
      "description": "Execute full network discovery",
      "inputSchema": {
        "type": "object",
        "properties": {
          "client": { "type": "string", "description": "Client name" },
          "full": { "type": "boolean", "default": true }
        },
        "required": ["client"]
      }
    }
  ],
  "prompts": [
    {
      "name": "onboarding",
      "description": "First-time setup for Meraki credentials"
    }
  ]
}
```

### Entregável Sprint 3
- [ ] MCP Server funcional
- [ ] 4 tools básicos implementados
- [ ] Prompt de onboarding
- [ ] Testado localmente

---

## 🔄 Sprint 4: Integração Claude Desktop (Semana 4)

### Objetivo
Integrar MCP Server com Claude Desktop para uso por colegas.

### Instalação no Claude Desktop

**1. Editar configuração do Claude Desktop**

Arquivo: `~/.config/Claude/claude_desktop_config.json` (Linux/Mac)
ou `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "meraki-workflow": {
      "command": "python",
      "args": ["/path/to/Meraki_Workflow/mcp-server/src/server.py"],
      "env": {
        "MERAKI_API_KEY": "your-api-key",
        "MERAKI_ORG_ID": "your-org-id"
      }
    }
  }
}
```

**2. Reiniciar Claude Desktop**

**3. Verificar no Claude Desktop**
- Tools aparecem com ícone 🔧
- Prompts aparecem com ícone 📝

### Fluxo de Onboarding para Colegas

```
┌─────────────────────────────────────────────────────────────┐
│  Colega abre Claude Desktop pela primeira vez              │
│                                                             │
│  Claude: "Vejo que você tem o MCP Meraki instalado.        │
│           Vamos configurar? Use /onboarding"               │
│                                                             │
│  Colega: /onboarding                                       │
│                                                             │
│  Claude: "1. Qual sua API Key Meraki?"                     │
│  Colega: [cola API key]                                    │
│                                                             │
│  Claude: "2. Qual Organization ID?"                         │
│          [lista orgs disponíveis]                          │
│  Colega: [seleciona]                                       │
│                                                             │
│  Claude: "3. Nome do cliente?"                              │
│  Colega: "acme"                                            │
│                                                             │
│  Claude: "✅ Configurado! Agora você pode:"               │
│          - "Faça um discovery da rede ACME"                │
│          - "Crie uma regra de firewall bloqueando Telnet"  │
│          - "Gere um workflow de alerta de device offline"  │
└─────────────────────────────────────────────────────────────┘
```

### Entregável Sprint 4
- [ ] Documentação de instalação
- [ ] Script de setup automatizado
- [ ] Teste com 2-3 colegas
- [ ] Ajustes baseados em feedback

---

## 🔄 Sprint 5: Polish & Logs (Semana 5-6)

### Objetivo
Adicionar logs em tempo real e melhorias de UX.

### Features

1. **Logs em tempo real**
   - Cada operação gera log estruturado
   - Log visível no Claude Desktop via tool `meraki_get_logs`

2. **Seleção de Agente**
   - Prompt `/select_agent` mostra agentes disponíveis
   - Agente selecionado influencia comportamento

3. **Histórico de operações**
   - Tool `meraki_history` mostra últimas operações
   - Permite reverter configurações

### Entregável Sprint 5-6
- [ ] Sistema de logs implementado
- [ ] Tool de histórico
- [ ] UX refinada
- [ ] Documentação final

---

## 📊 Cronograma Visual

```
Semana 1  │████████████████████│ Sprint 1: Exportar Templates
Semana 2  │████████████████████│ Sprint 2: Clone + Patch
Semana 3  │████████████████████│ Sprint 3: MCP Server Base
Semana 4  │████████████████████│ Sprint 4: Integração Claude
Semana 5  │██████████          │ Sprint 5: Logs
Semana 6  │          ██████████│ Sprint 6: Polish & Docs
```

---

## ✅ Critérios de Sucesso

### MVP (Semana 4)
- [ ] MCP Server instalável em Claude Desktop
- [ ] Onboarding funcional
- [ ] 3 tools básicos (discover, configure, workflow)
- [ ] 5 templates de workflow disponíveis

### Produto Completo (Semana 6)
- [ ] Todos os tools implementados
- [ ] Logs em tempo real
- [ ] Documentação completa
- [ ] Testado com 3+ colegas
- [ ] Feedback incorporado

---

## 🚀 Próximos Passos Imediatos

1. **AGORA**: Acessar Meraki Dashboard e exportar primeiro template
2. **Hoje**: Salvar em `templates/workflows/`
3. **Amanhã**: Começar `template_loader.py`

---

## 📞 Suporte

Se tiver dúvidas durante a exportação de templates:
- Documentação Meraki: https://documentation.meraki.com/
- Cisco DevNet: https://developer.cisco.com/meraki/

---

*Plano criado por Aria (@architect) - Synkra AIOS*
