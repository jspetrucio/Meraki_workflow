# PRD_ADD_Features - Product Requirements Document
# Projeto: Meraki Workflow - Novas Features (MCP Server + N8N Integration)

> **Versão:** 1.0.0
> **Data:** 2026-02-04
> **Autor:** Morgan (@pm) com input de Aria (@architect)
> **Status:** Em Planejamento

---

## 1. VISÃO GERAL

### 1.1 Contexto

O projeto Meraki Workflow é uma plataforma de automação de redes Cisco Meraki via linguagem natural. Durante análise arquitetural, foram identificados dois problemas principais que precisam ser resolvidos para tornar o produto distribuível e mais poderoso.

### 1.2 Problemas Identificados

| # | Problema | Impacto | Prioridade |
|---|----------|---------|------------|
| 1 | **Workflows não podem ser criados via API** | Bloqueia automação completa | Alta |
| 2 | **Produto não é distribuível** | Limita adoção por colegas | Alta |

### 1.3 Soluções Propostas

| Problema | Solução | Abordagem |
|----------|---------|-----------|
| 1 | Clone + Patch | Usar templates exportados do Dashboard como base |
| 2 | MCP Server | Expor funcionalidades via MCP para Claude Desktop |
| Bônus | N8N Integration | Alternativa para automação multi-vendor |

---

## 2. OBJETIVOS E MÉTRICAS DE SUCESSO

### 2.1 Objetivos

1. **Permitir criação de workflows parametrizados** a partir de templates exportados
2. **Distribuir o produto** para colegas via Claude Desktop (MCP)
3. **Oferecer alternativa N8N** para automações multi-vendor

### 2.2 Métricas de Sucesso

| Métrica | Meta | Como Medir |
|---------|------|------------|
| Workflows criados via template | 100% sucesso no import | Testes manuais no Dashboard |
| Instalação por colegas | 3+ colegas usando | Feedback qualitativo |
| Tempo de onboarding | < 5 minutos | Cronometrar setup |
| Cobertura de tools MCP | 4+ tools funcionais | Contagem de tools |

---

## 3. REQUISITOS FUNCIONAIS

### 3.1 Epic 1: Sistema Clone + Patch (Template Loader)

**Objetivo:** Permitir criação de novos workflows baseados em templates exportados do Meraki Dashboard.

#### User Stories

| ID | Como... | Eu quero... | Para que... |
|----|---------|-------------|-------------|
| E1.1 | Consultor | Carregar um template de workflow | Usar como base para customização |
| E1.2 | Consultor | Definir nome e descrição do novo workflow | Identificar facilmente |
| E1.3 | Consultor | Substituir variáveis do template | Adaptar ao cliente |
| E1.4 | Consultor | Gerar JSON com IDs únicos | Evitar conflito no import |
| E1.5 | Consultor | Salvar workflow para cliente específico | Organizar por cliente |

#### Requisitos Técnicos

```
Criar: scripts/template_loader.py

Classes:
- TemplateLoader: Carrega templates de templates/workflows/
- TemplateWorkflow: Representa workflow carregado
  - clone() → Cria cópia para modificação
  - set_name(name) → Define nome
  - set_description(desc) → Define descrição
  - set_variable(key, value) → Substitui variável
  - build() → Gera JSON final com novos IDs
  - save(client, name) → Salva em clients/{client}/workflows/

Funções:
- generate_unique_id() → Gera ID de 37 chars (padrão Cisco)
- update_references(json, old_id, new_id) → Atualiza referências internas
- validate_workflow(json) → Valida estrutura antes de salvar
```

#### Critérios de Aceitação

- [x] Carregar qualquer template de `templates/workflows/`
- [x] Gerar IDs únicos no padrão `definition_workflow_02XXXXX...`
- [x] Atualizar todas as referências internas (`$workflow.XXX$`)
- [x] Validar JSON antes de salvar
- [x] Salvar em `clients/{client}/workflows/{name}.json`
- [x] Testes unitários com 80%+ cobertura

---

### 3.2 Epic 2: MCP Server Base

**Objetivo:** Criar MCP Server que expõe funcionalidades do projeto para Claude Desktop.

#### User Stories

| ID | Como... | Eu quero... | Para que... |
|----|---------|-------------|-------------|
| E2.1 | Colega | Instalar MCP no Claude Desktop | Usar as ferramentas |
| E2.2 | Colega | Fazer onboarding guiado | Configurar credenciais |
| E2.3 | Colega | Executar discovery de rede | Ver estado atual |
| E2.4 | Colega | Aplicar configurações | Gerenciar rede |
| E2.5 | Colega | Criar workflows de template | Automatizar tarefas |
| E2.6 | Colega | Gerar relatórios | Documentar para cliente |

#### Estrutura do MCP Server

```
mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py              # Entry point MCP
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── discovery.py       # Tool: meraki_discover
│   │   ├── config.py          # Tool: meraki_configure
│   │   ├── workflow.py        # Tool: meraki_create_workflow
│   │   ├── report.py          # Tool: meraki_report
│   │   └── network.py         # Tool: meraki_list_networks
│   └── prompts/
│       ├── __init__.py
│       ├── onboarding.py      # Prompt: setup inicial
│       └── agents.py          # Prompt: seleção de agente
├── mcp.json                   # Manifest MCP
├── requirements.txt
└── README.md
```

#### Tools MCP

| Tool | Descrição | Parâmetros |
|------|-----------|------------|
| `meraki_discover` | Executa discovery completo | `client`, `full` |
| `meraki_configure` | Aplica configuração | `network_id`, `config_type`, `params` |
| `meraki_create_workflow` | Cria workflow de template | `template`, `client`, `name`, `variables` |
| `meraki_report` | Gera relatório | `client`, `type`, `format` |
| `meraki_list_networks` | Lista networks | `org_id` |
| `meraki_get_device_status` | Status de device | `serial` |

#### Prompts MCP

| Prompt | Descrição |
|--------|-----------|
| `onboarding` | Guia setup inicial (API key, Org ID, cliente) |
| `select_agent` | Escolhe agente especializado |
| `troubleshoot` | Diagnóstico guiado de problemas |

#### Critérios de Aceitação

- [x] MCP Server inicia sem erros
- [x] 6 tools expostos e funcionais (6/6 completos)
- [x] 3 prompts disponíveis (3/3 completos)
- [x] Instalável via Claude Desktop config
- [x] Documentação de instalação completa
- [x] Testes de integração criados (tests/test_mcp_server.py)

---

### 3.3 Epic 3: N8N Integration Squad

**Objetivo:** Criar squad e agente especializado em N8N para automações multi-vendor.

#### Contexto N8N

**Repositórios de referência:**
- https://github.com/czlonkowski/n8n-mcp - MCP Server para N8N
- https://github.com/czlonkowski/n8n-skills - 7 Skills Claude para N8N

**n8n-mcp oferece:**
- 1,084 nodes (537 core + 547 community)
- 2,709 templates de workflow
- 87% cobertura de documentação
- 265 AI-capable tools

**n8n-skills oferece:**
- n8n Expression Syntax
- n8n MCP Tools Expert
- n8n Workflow Patterns
- n8n Validation Expert
- n8n Node Configuration
- n8n Code JavaScript
- n8n Code Python

#### User Stories

| ID | Como... | Eu quero... | Para que... |
|----|---------|-------------|-------------|
| E3.1 | Consultor | Criar workflow N8N para Meraki | Automatizar sem limites de API |
| E3.2 | Consultor | Usar templates N8N prontos | Acelerar desenvolvimento |
| E3.3 | Consultor | Integrar Meraki + outros vendors | Ambiente multi-vendor |
| E3.4 | Consultor | Validar workflows antes de deploy | Evitar erros |

#### Estrutura do Squad

```
squads/n8n-automation/
├── squad.yaml                 # Manifest do squad
├── README.md
├── config/
│   ├── n8n-setup.md          # Como instalar N8N
│   └── meraki-nodes.md       # Nodes Meraki disponíveis
├── agents/
│   └── n8n-specialist.md     # Agente especialista
├── tasks/
│   ├── create-n8n-workflow.md
│   ├── deploy-n8n-instance.md
│   ├── migrate-meraki-to-n8n.md
│   └── validate-n8n-workflow.md
├── templates/
│   └── n8n-workflows/
│       ├── meraki-device-offline.json
│       ├── meraki-config-backup.json
│       ├── meraki-discovery-scheduled.json
│       └── multi-vendor-alert.json
├── checklists/
│   └── n8n-workflow-review.md
└── data/
    ├── n8n-meraki-nodes.md
    └── n8n-vs-meraki-workflows.md
```

#### Agente n8n-specialist

```yaml
agent:
  name: Nate
  id: n8n-specialist
  title: N8N Automation Expert
  icon: 🔄

persona:
  role: N8N Workflow Architect & Multi-Vendor Integration Expert
  style: Visual, practical, integration-focused

tools:
  - n8n-mcp (via npx ou Docker)
  - n8n-skills (7 skills)

commands:
  - *create-workflow     # Cria workflow N8N
  - *list-nodes         # Lista nodes disponíveis
  - *validate-workflow  # Valida antes de deploy
  - *deploy-workflow    # Publica no N8N
  - *list-templates     # Mostra templates disponíveis
```

#### Critérios de Aceitação

- [x] Squad criado com estrutura completa
- [x] Agente n8n-specialist funcional
- [x] 4 templates N8N para Meraki
- [x] Documentação de quando usar N8N vs Meraki Workflows
- [ ] Integração com n8n-mcp testada (opcional - requer instância N8N)

---

## 4. ARQUITETURA DE ALTO NÍVEL

### 4.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Meraki Workflow System                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Claude Desktop                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │ MCP Meraki  │  │  MCP N8N    │  │ Outros MCPs │         │   │
│  │  │  (Nosso)    │  │ (czlonkowski)│  │             │         │   │
│  │  └──────┬──────┘  └──────┬──────┘  └─────────────┘         │   │
│  └─────────┼────────────────┼──────────────────────────────────┘   │
│            │                │                                       │
│  ┌─────────▼────────────────▼──────────────────────────────────┐   │
│  │                    Backend Python                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ Template     │  │ Meraki API   │  │ N8N API      │      │   │
│  │  │ Loader       │  │ Wrapper      │  │ (opcional)   │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Armazenamento                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ templates/   │  │ clients/     │  │ squads/      │      │   │
│  │  │ workflows/   │  │ {client}/    │  │ n8n-auto/    │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Fluxo de Dados

```
Usuario (Claude Desktop)
    │
    ├─► "Crie um workflow de device offline para cliente ACME"
    │
    ▼
MCP Server (meraki_create_workflow)
    │
    ├─► TemplateLoader.load("Device Offline Handler")
    │
    ├─► template.clone()
    │       .set_name("ACME - Device Offline")
    │       .set_variable("slack_channel", "#acme-alerts")
    │       .build()
    │
    ├─► Salva em clients/acme/workflows/device-offline.json
    │
    └─► Retorna: "Workflow criado! Importe no Dashboard: ..."
```

---

## 5. TEMPLATES DISPONÍVEIS

### 5.1 Templates Cisco Workflows (Já Exportados)

| Template | Arquivo | Uso |
|----------|---------|-----|
| Device Offline Handler | `Device Offline Handler.json` | Alertas de device offline |
| Blink Device LEDs | `blink-device-leds.json` | Identificação física |
| Generate Inventory Report | `Generate Meraki Device Inventory Report.json` | Relatórios |
| MX Firewall Block by Tags | `MX Firewall - Block Outbound Traffic by Tags.json` | Segurança |
| Copy Admins Multi-Org | `Copy Meraki Admins to Multiple Organizations.json` | Multi-org |
| Modify VLAN DHCP | `Modify VLAN DHCP Pool.json` | Rede |
| Schedule Firmware Upgrade | `Schedule Firmware Upgrade for Networks by Tag.json` | Compliance |
| Getting Started 1-5 | `Getting Started *.json` | Tutoriais |

### 5.2 Templates N8N (A Criar)

| Template | Uso | Nodes Principais |
|----------|-----|------------------|
| meraki-device-offline.json | Alerta device offline | Webhook + Meraki + Slack |
| meraki-config-backup.json | Backup agendado | Schedule + Meraki + S3 |
| meraki-discovery-scheduled.json | Discovery diário | Cron + Meraki + Email |
| multi-vendor-alert.json | Alerta multi-vendor | Webhook + Meraki + Fortinet + PagerDuty |

---

## 6. CRONOGRAMA

### 6.1 Sprints

| Sprint | Semana | Entregas |
|--------|--------|----------|
| **Sprint 1** | 1 | Template Loader (`scripts/template_loader.py`) |
| **Sprint 2** | 2 | MCP Server Base (estrutura + 2 tools) |
| **Sprint 3** | 3 | MCP Server Completo (6 tools + prompts) |
| **Sprint 4** | 4 | Integração Claude Desktop + Testes |
| **Sprint 5** | 5 | Squad N8N + Agente |
| **Sprint 6** | 6 | Templates N8N + Documentação Final |

### 6.2 Diagrama de Gantt

```
Semana 1  │████████████████████│ Sprint 1: Template Loader
Semana 2  │████████████████████│ Sprint 2: MCP Server Base
Semana 3  │████████████████████│ Sprint 3: MCP Completo
Semana 4  │████████████████████│ Sprint 4: Integração + Testes
Semana 5  │████████████████████│ Sprint 5: Squad N8N
Semana 6  │████████████████████│ Sprint 6: Templates + Docs
```

---

## 7. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Templates não importam corretamente | Média | Alto | Testar cada template manualmente antes de automatizar |
| MCP Server incompatível com Claude Desktop | Baixa | Alto | Seguir spec oficial, testar incrementalmente |
| N8N muito complexo para colegas | Média | Médio | Documentação detalhada, templates prontos |
| Rate limiting da API Meraki | Baixa | Médio | Já implementado no wrapper existente |

---

## 8. DEPENDÊNCIAS

### 8.1 Dependências de Código

| Componente | Depende de |
|------------|------------|
| Template Loader | Templates exportados em `templates/workflows/` |
| MCP Server | Template Loader, scripts existentes (api.py, discovery.py) |
| Squad N8N | n8n-mcp instalado, n8n-skills configuradas |

### 8.2 Dependências Externas

| Dependência | Fonte | Status |
|-------------|-------|--------|
| n8n-mcp | github.com/czlonkowski/n8n-mcp | Disponível |
| n8n-skills | github.com/czlonkowski/n8n-skills | Disponível |
| MCP SDK Python | modelcontextprotocol.io | Documentar versão |

---

## 9. PRÓXIMOS PASSOS IMEDIATOS

### 9.1 Ações Prioritárias

1. **[ ] Criar `scripts/template_loader.py`**
   - Usar templates já exportados em `clients/jose-org/workflows/`
   - Implementar clone + patch com geração de IDs únicos
   - Testes unitários

2. **[ ] Criar estrutura do Squad N8N**
   - `squads/n8n-automation/squad.yaml`
   - `squads/n8n-automation/agents/n8n-specialist.md`
   - Templates básicos

### 9.2 Próxima Sessão

Ao iniciar nova sessão, usar este documento como referência:
```
Leia: docs/PRD_ADD_Features.md
Continue de: Seção 9.1 - Próximos Passos
```

---

## 10. GLOSSÁRIO

| Termo | Definição |
|-------|-----------|
| **Clone + Patch** | Técnica de criar novo workflow a partir de template existente |
| **MCP** | Model Context Protocol - protocolo para expor tools a LLMs |
| **N8N** | Plataforma de automação open-source (alternativa ao Zapier) |
| **Template** | JSON de workflow exportado do Meraki Dashboard |
| **Squad** | Conjunto de agentes, tasks e templates para um domínio específico |

---

## 11. REFERÊNCIAS

### 11.1 Documentação Interna

- `docs/PLANO_MCP_WORKFLOWS.md` - Plano detalhado de implementação
- `BRAINSTORM_WORKFLOWS.md` - Análise comparativa N8N vs Meraki Workflows
- `.claude/knowledge/cisco-workflows-schema.md` - Schema JSON de workflows

### 11.2 Repositórios Externos

- https://github.com/czlonkowski/n8n-mcp - MCP Server para N8N
- https://github.com/czlonkowski/n8n-skills - Skills Claude para N8N
- https://github.com/CiscoDevNet/CiscoWorkflowsAutomation - Exemplos oficiais

### 11.3 Documentação Oficial

- https://documentation.meraki.com/Platform_Management/Workflows
- https://modelcontextprotocol.io/docs
- https://docs.n8n.io/

---

## 12. CHANGELOG

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0.0 | 2026-02-04 | Morgan (@pm) | Versão inicial com 3 epics |

---

*Documento criado por Morgan (@pm) com input arquitetural de Aria (@architect)*
*Synkra AIOS - Meraki Workflow Project*
