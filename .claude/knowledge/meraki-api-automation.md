# Meraki API Automation - Knowledge Base

> **IMPORTANTE**: Este documento contém descobertas críticas sobre automação via Meraki API.
> Leia antes de implementar qualquer automação.

---

## Descoberta Crítica: Workflows ≠ API

### ❌ O QUE NÃO EXISTE NA API

**Dashboard Workflows NÃO são acessíveis via API**

- Nenhum endpoint para criar workflows
- Nenhum endpoint para importar JSON de workflow
- Nenhum endpoint para validar workflow
- Nenhum endpoint para diagnosticar erros de importação

**Confirmado por:**
- Documentação oficial Meraki Dashboard API v1
- Investigação completa do SDK Python
- Testes práticos com org_id 1437319

### ✅ O QUE EXISTE NA API

**Action Batches - Alternativa Funcional**

Endpoint completo para executar múltiplas operações em batch:

```
POST   /organizations/{orgId}/actionBatches  (criar)
GET    /organizations/{orgId}/actionBatches  (listar)
GET    /organizations/{orgId}/actionBatches/{id}  (obter)
PUT    /organizations/{orgId}/actionBatches/{id}  (atualizar)
DELETE /organizations/{orgId}/actionBatches/{id}  (deletar)
```

---

## Action Batches - Guia Completo

### Quando Usar

✅ **Ideal para:**
- Aplicar mesma configuração em múltiplos devices/networks
- Mudanças planejadas em lote (maintenance windows)
- Evitar rate limiting (10 req/s)
- Preview de mudanças antes de aplicar

❌ **NÃO usar para:**
- Lógica condicional complexa (if/else)
- Triggers automáticos baseados em eventos
- Execução recorrente (cron-like)
- Workflows com múltiplos steps dependentes

### Capacidades

| Feature | Suportado | Notas |
|---------|-----------|-------|
| Preview Mode | ✅ | `confirmed=false` para dry-run |
| Sync/Async | ✅ | Sync limitado a 20 actions |
| Error Handling | ✅ | Erros por action individual |
| Status Tracking | ✅ | Verificar progresso via GET |
| Rollback | ❌ | Não automático (criar batch reverso) |
| Scheduling | ❌ | Executar imediatamente |
| Triggers | ❌ | Apenas execução manual |

### Exemplo Básico

```python
import meraki

dashboard = meraki.DashboardAPI(API_KEY)

# Preview mode (dry-run)
preview = dashboard.organizations.createOrganizationActionBatch(
    org_id,
    confirmed=False,  # NÃO aplicar
    synchronous=True,  # Aguardar resultado
    actions=[
        {
            'resource': '/devices/Q2XX-XXXX-XXXX/switchPorts/1',
            'operation': 'update',
            'body': {'vlan': 100, 'enabled': True}
        },
        {
            'resource': '/networks/N_123/appliance/vlans',
            'operation': 'create',
            'body': {
                'id': 100,
                'name': 'DataVLAN',
                'subnet': '10.0.100.0/24',
                'applianceIp': '10.0.100.1'
            }
        }
    ]
)

# Verificar preview
if not preview['status']['failed']:
    # Aplicar para valer
    result = dashboard.organizations.createOrganizationActionBatch(
        org_id,
        confirmed=True,
        synchronous=False,  # Background
        actions=[...]  # Mesmas actions
    )

    # Verificar status depois
    status = dashboard.organizations.getOrganizationActionBatch(
        org_id,
        result['id']
    )
```

### Limitações Importantes

1. **Máximo de 100 actions por batch** (recomendado: 20-50)
2. **Synchronous limitado a 20 actions** (senão usar async)
3. **Sem lógica condicional** (não tem if/else/loops)
4. **Sem triggers** (executar manualmente ou via script externo)
5. **Rate limit ainda se aplica** (batch ajuda mas não remove limite)

---

## Workflows JSON - Importação Manual

### Processo Correto

1. **Gerar JSON válido** usando schema em `cisco-workflows-schema.md`
2. **Salvar arquivo** em `clients/{client}/workflows/workflow_name.json`
3. **Importação MANUAL** no Dashboard:
   - Acessar Organization > Workflows
   - Clicar "Import workflow"
   - Upload do arquivo JSON
   - Configurar triggers e targets manualmente

### Por que Importação Manual?

**Workflows usam Cisco SecureX Orchestration:**
- Infraestrutura separada do Meraki Dashboard
- Não expõe API pública para criação/importação
- Apenas Dashboard UI tem acesso ao orchestrator
- JSON é serialização do estado interno (não API contract)

### Diagnóstico de Erros

**Erros de importação NÃO podem ser diagnosticados via API.**

Erros comuns e soluções:

| Erro | Causa | Solução |
|------|-------|---------|
| "Invalid workflow format" | JSON malformado | Validar schema completo |
| "Missing required fields" | Faltando `categories` raiz | Adicionar objeto `categories` |
| "Invalid unique_name" | ID não tem 37 chars | Gerar ID correto |
| "Target not found" | `target_type` inválido | Usar `meraki.endpoint` |
| Importação silenciosa falha | Referência de variável errada | Formato `$workflow.XXX.scope.YYY$` |

**Debugging:**
1. Exportar workflow existente do Dashboard
2. Comparar estrutura com seu JSON
3. Validar TODOS os campos obrigatórios
4. Testar com workflow mínimo primeiro

---

## Alternativas para Automação

### Opção 1: Action Batches (Recomendado)

**Usar módulo `scripts/automation.py`:**

```python
from scripts.automation import ActionBatchManager
import meraki

dashboard = meraki.DashboardAPI(API_KEY)
manager = ActionBatchManager(dashboard, ORG_ID)

# Atualizar VLAN em todos os switches
devices = dashboard.organizations.getOrganizationDevices(
    ORG_ID,
    productTypes=['switch']
)

result = manager.bulk_update_switch_ports(
    devices,
    {'vlan': 100},
    lambda p: p['type'] == 'access'  # Filtro
)
```

**Casos de uso:**
- Configurar VLAN em múltiplos switches
- Criar mesma SSID em todas as networks
- Atualizar firewall rules em massa
- Reboot múltiplos devices

---

### Opção 2: Scripts Python + Cron

**Para automação recorrente:**

```python
# scripts/check_offline_devices.py
import meraki
import smtplib

dashboard = meraki.DashboardAPI(API_KEY)
devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID)

offline = [d for d in devices if d['status'] == 'offline']

if offline:
    # Enviar email
    send_alert_email(offline)

    # Ou criar ticket
    create_jira_ticket(offline)
```

```bash
# Crontab: a cada 15 minutos
*/15 * * * * /path/to/venv/bin/python /path/to/check_offline_devices.py
```

**Casos de uso:**
- Verificar devices offline periodicamente
- Compliance checks (portas abertas, VLANs incorretas)
- Relatórios automáticos
- Backup de configurações

---

### Opção 3: Webhooks + N8N/Zapier

**Para automação event-driven:**

```
Meraki Event → Webhook → N8N → Actions (Slack/Email/Ticket/API)
```

**Setup:**

```python
# 1. Criar webhook HTTP server
webhook = dashboard.networks.createNetworkWebhooksHttpServer(
    network_id,
    name='N8N Automation',
    url='https://n8n.mycompany.com/webhook/meraki',
    sharedSecret='SECRET_TOKEN'
)

# 2. Configurar alert para enviar ao webhook
dashboard.networks.updateNetworkAlertsSettings(
    network_id,
    alerts=[
        {
            'type': 'gatewayDown',
            'enabled': True,
            'alertDestinations': {
                'httpServerIds': [webhook['id']]
            }
        }
    ]
)
```

**Casos de uso:**
- Alertas em tempo real (device offline, link down)
- Integrações com sistemas externos
- Workflows complexos com múltiplos steps
- Notificações customizadas

---

### Opção 4: Workflows JSON (Manual)

**Apenas quando necessário:**

Usar para automações que:
- Requerem lógica condicional complexa
- Precisam de loops/iterações
- Devem rodar nativamente no Dashboard
- Não precisam ser criadas programaticamente

**Processo:**
1. Gerar JSON usando `scripts/workflow.py`
2. Salvar em `clients/{client}/workflows/`
3. **Import manual** no Dashboard UI
4. Documentar no changelog

---

## Config Templates vs Workflows

**NÃO CONFUNDIR:**

| Aspecto | Config Template | Workflow |
|---------|----------------|----------|
| **API** | ✅ CRUD completo | ❌ Sem API |
| **Propósito** | Configuração padrão | Automação com lógica |
| **Aplicação** | Manual (bind network) | Triggers automáticos |
| **Lógica** | Estática | Condicional (if/else) |
| **Quando usar** | Padronizar networks | Reagir a eventos |

**Config Templates via API:**

```python
# Criar template
template = dashboard.organizations.createOrganizationConfigTemplate(
    org_id,
    name='Branch Office Standard',
    timeZone='America/Sao_Paulo'
)

# Aplicar a network
dashboard.networks.bindNetwork(
    network_id,
    configTemplateId=template['id']
)
```

---

## Endpoints Úteis para Automation

### Alerts

```python
# Obter configurações
alerts = dashboard.networks.getNetworkAlertsSettings(network_id)

# Atualizar
dashboard.networks.updateNetworkAlertsSettings(
    network_id,
    alerts=[
        {
            'type': 'gatewayDown',
            'enabled': True,
            'alertDestinations': {
                'emails': ['admin@company.com'],
                'httpServerIds': [webhook_id]
            }
        }
    ]
)
```

### Webhooks

```python
# Listar
servers = dashboard.networks.getNetworkWebhooksHttpServers(network_id)

# Criar
webhook = dashboard.networks.createNetworkWebhooksHttpServer(
    network_id,
    name='External Automation',
    url='https://automation.company.com/meraki',
    sharedSecret='SECRET'
)

# Testar
dashboard.networks.sendNetworkWebhooksTest(
    network_id,
    url='https://automation.company.com/meraki'
)
```

### Live Tools

```python
# Blink LEDs
dashboard.devices.blinkDeviceLeds(serial, duration=20)

# Reboot
dashboard.devices.rebootDevice(serial)

# Ping
ping = dashboard.devices.createDeviceLiveToolsPing(
    serial, target='8.8.8.8', count=5
)
results = dashboard.devices.getDeviceLiveToolsPing(serial, ping['pingId'])

# Cable test
cable = dashboard.devices.createDeviceLiveToolsCableTest(serial)
```

---

## Recomendações para o Projeto

### Arquitetura Híbrida

```
MERAKI_WORKFLOW
├── scripts/automation.py       → Action Batches (massa)
├── scripts/scheduler.py        → Cron-like automation
├── scripts/workflow.py         → JSON generator (import manual)
└── integrations/n8n/           → Event-driven (opcional)
```

### Quando Usar Cada Abordagem

```
┌─────────────────────────────────────────────────────────┐
│ Necessidade              → Solução                       │
├─────────────────────────────────────────────────────────┤
│ Config em massa          → Action Batches               │
│ Verificação recorrente   → Python + Cron                │
│ Event-driven             → Webhooks + N8N               │
│ Lógica complexa nativa   → Workflow JSON (manual)       │
└─────────────────────────────────────────────────────────┘
```

### Boas Práticas

1. **Sempre usar preview mode** antes de aplicar changes
2. **Logar todas as actions** em changelog
3. **Validar batch size** (max 100, recomendado 20-50)
4. **Tratar erros individuais** (não falhar batch inteiro)
5. **Documentar workflows JSON** (não há validação via API)

---

## Referências

- [Meraki Dashboard API v1](https://developer.cisco.com/meraki/api-v1/)
- [Action Batches Overview](https://developer.cisco.com/meraki/api-v1/action-batches-overview/)
- [Cisco Workflows Schema](cisco-workflows-schema.md)
- [Investigation Report](../docs/meraki_api_investigation.md)
- [Automation Module](../scripts/automation.py)

---

**Última Atualização**: 2026-02-05
**Testado com**: Meraki Python SDK 2.1.0
**Org ID**: 1437319 (jose-org)
