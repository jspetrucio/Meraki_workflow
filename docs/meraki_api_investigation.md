# Meraki API Investigation - Workflows & Automation

**Data**: 2026-02-05
**Cliente**: jose-org (Org ID: 1437319)
**Objetivo**: Investigar suporte da API para workflows e automation

---

## Executive Summary

### Principais Descobertas

1. **Workflows Dashboard NÃO são acessíveis via API**
   - Nenhum endpoint para criar, importar, validar ou diagnosticar workflows
   - Workflows são gerenciados EXCLUSIVAMENTE pelo Dashboard UI
   - JSON de workflow deve ser importado manualmente

2. **Action Batches SÃO suportados e funcionais**
   - Endpoint completo (CRUD) disponível
   - Permite automação em massa de configurações
   - Suporta preview mode (dry-run) antes de aplicar
   - **Melhor alternativa para automação programática**

3. **Config Templates são diferentes de Workflows**
   - Templates são configurações reusáveis aplicadas a networks
   - Não substituem workflows para lógica condicional/triggers

---

## Detalhamento dos Endpoints

### 1. Action Batches (`/organizations/{orgId}/actionBatches`)

#### Status: ✅ TOTALMENTE FUNCIONAL

#### Capabilities

| Operação | Método | Endpoint | SDK Method |
|----------|--------|----------|------------|
| Criar | POST | `/organizations/{orgId}/actionBatches` | `createOrganizationActionBatch()` |
| Listar | GET | `/organizations/{orgId}/actionBatches` | `getOrganizationActionBatches()` |
| Obter | GET | `/organizations/{orgId}/actionBatches/{id}` | `getOrganizationActionBatch()` |
| Atualizar | PUT | `/organizations/{orgId}/actionBatches/{id}` | `updateOrganizationActionBatch()` |
| Deletar | DELETE | `/organizations/{orgId}/actionBatches/{id}` | `deleteOrganizationActionBatch()` |

#### Exemplo de Uso

```python
# Preview mode (dry-run)
batch = dashboard.organizations.createOrganizationActionBatch(
    org_id,
    confirmed=False,  # Preview sem aplicar
    synchronous=False,
    actions=[
        {
            'resource': '/devices/SERIAL/switchPorts/3',
            'operation': 'update',
            'body': {'enabled': True, 'vlan': 100}
        },
        {
            'resource': '/networks/NET_ID/vlans',
            'operation': 'create',
            'body': {'id': 100, 'name': 'Data', 'subnet': '10.0.100.0/24'}
        }
    ]
)

# Batch ID retornado: pode verificar status, executar ou cancelar
```

#### Recursos Avançados

- **Rate Limiting**: Evita exceder limites da API
- **Synchronous vs Asynchronous**:
  - `synchronous=True`: Aguarda conclusão (max 20 actions)
  - `synchronous=False`: Execução em background
- **Error Handling**: Retorna erros por action individual
- **Preview Mode**: `confirmed=False` permite validar antes de aplicar

#### Limitações

- Máximo de 100 actions por batch (recomendado: 20-50)
- Não suporta lógica condicional (if/else)
- Não suporta triggers automáticos
- Execução única (não recorrente)

---

### 2. Config Templates (`/organizations/{orgId}/configTemplates`)

#### Status: ✅ FUNCIONAL (mas não substitui workflows)

#### Capabilities

| Operação | Método | Endpoint | SDK Method |
|----------|--------|----------|------------|
| Listar | GET | `/organizations/{orgId}/configTemplates` | `getOrganizationConfigTemplates()` |
| Criar | POST | `/organizations/{orgId}/configTemplates` | `createOrganizationConfigTemplate()` |
| Obter | GET | `/organizations/{orgId}/configTemplates/{id}` | `getOrganizationConfigTemplate()` |
| Atualizar | PUT | `/organizations/{orgId}/configTemplates/{id}` | `updateOrganizationConfigTemplate()` |
| Deletar | DELETE | `/organizations/{orgId}/configTemplates/{id}` | `deleteOrganizationConfigTemplate()` |

#### Diferença entre Templates e Workflows

| Aspecto | Config Template | Workflow |
|---------|----------------|----------|
| **Propósito** | Configuração padrão reusável | Automação com lógica e triggers |
| **Aplicação** | Manual (bind a network) | Automática (baseada em eventos) |
| **Lógica** | Estática | Condicional (if/else) |
| **Triggers** | Não | Sim (device offline, alert, etc) |
| **Via API** | ✅ Sim | ❌ Não |

#### Exemplo de Uso

```python
# Criar template
template = dashboard.organizations.createOrganizationConfigTemplate(
    org_id,
    name='Branch Office Standard',
    timeZone='America/Sao_Paulo'
)

# Aplicar template a uma network
dashboard.networks.bindNetwork(
    network_id,
    configTemplateId=template['id']
)
```

---

### 3. Workflows (`/organizations/{orgId}/workflows`)

#### Status: ❌ NÃO EXISTE NA API

#### Tentativas de Busca

```python
# Buscado em todos os módulos do SDK
modules_searched = [
    'organizations', 'networks', 'devices',
    'appliance', 'switch', 'wireless',
    'camera', 'sensor'
]

# Métodos procurados
patterns = ['workflow', 'automation', 'trigger', 'orchestrat']

# Resultado: NENHUM método encontrado
```

#### Confirmação via Documentação

De acordo com:
- Meraki Dashboard API v1 (https://developer.cisco.com/meraki/api-v1/)
- Cisco Workflows Documentation
- Community Forums

**Workflows são baseados em Cisco SecureX Orchestration**, que:
- Roda em infraestrutura separada do Meraki Dashboard
- Não expõe API pública para criação/importação
- Requer importação manual de JSON via Dashboard UI

---

## Alternativas para Automação

### Opção 1: Action Batches (Recomendado para Configurações em Massa)

**Quando usar:**
- Aplicar mesma configuração em múltiplos devices/networks
- Mudanças planejadas em lote
- Evitar rate limiting

**Vantagens:**
- ✅ Totalmente via API
- ✅ Preview mode
- ✅ Error handling granular
- ✅ Status tracking

**Desvantagens:**
- ❌ Sem triggers automáticos
- ❌ Sem lógica condicional
- ❌ Execução única (não recorrente)

**Exemplo de Caso de Uso:**
```python
# Configurar VLAN 100 em todos os switches da org
devices = dashboard.organizations.getOrganizationDevices(org_id, productTypes=['switch'])

actions = []
for device in devices:
    ports = dashboard.switch.getDeviceSwitchPorts(device['serial'])
    for port in ports:
        if port['type'] == 'access':
            actions.append({
                'resource': f'/devices/{device["serial"]}/switchPorts/{port["portId"]}',
                'operation': 'update',
                'body': {'vlan': 100}
            })

batch = dashboard.organizations.createOrganizationActionBatch(
    org_id,
    confirmed=True,
    synchronous=False,
    actions=actions
)
```

---

### Opção 2: Scripts Python + Scheduler (Recomendado para Automação Recorrente)

**Quando usar:**
- Verificações periódicas (ex: device offline)
- Compliance checks
- Relatórios automáticos

**Arquitetura:**
```
┌─────────────────┐
│   Cron / PM2    │  ← Scheduler
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Python Script  │  ← Lógica de automação
│   (Meraki SDK)  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Meraki API     │
└─────────────────┘
```

**Exemplo:**
```python
# check_offline_devices.py
import meraki
import smtplib

dashboard = meraki.DashboardAPI(API_KEY)
devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID)

offline = [d for d in devices if d['status'] == 'offline']

if offline:
    # Enviar email de alerta
    send_alert(offline)

    # Ou criar ticket
    create_ticket(offline)
```

```bash
# Crontab: executar a cada 15 minutos
*/15 * * * * /path/to/venv/bin/python /path/to/check_offline_devices.py
```

---

### Opção 3: Webhooks + N8N/Zapier (Recomendado para Event-Driven)

**Quando usar:**
- Reagir a eventos em tempo real
- Integrações com sistemas externos
- Workflows complexos com múltiplos steps

**Arquitetura:**
```
┌─────────────────┐
│  Meraki Event   │  (Alert triggered)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Meraki Webhook │  → POST to external URL
└────────┬────────┘
         │
         v
┌─────────────────┐
│   N8N / Zapier  │  ← Workflow engine
│   (automation)  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Actions        │  (Slack, Email, Ticket, API call)
└─────────────────┘
```

**Configuração:**
```python
# Criar webhook HTTP server
webhook = dashboard.networks.createNetworkWebhooksHttpServer(
    network_id,
    name='N8N Automation',
    url='https://n8n.mycompany.com/webhook/meraki',
    sharedSecret='SECRET_TOKEN'
)

# Configurar alert para enviar ao webhook
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

---

### Opção 4: Workflows JSON (Manual Import)

**Quando usar:**
- Automações complexas nativas do Dashboard
- Não há necessidade de criação programática
- Usar recursos do Cisco Workflows (condicionais, loops)

**Processo:**
1. Gerar JSON do workflow (seguir schema em `.claude/knowledge/cisco-workflows-schema.md`)
2. Importar manualmente via Dashboard UI:
   - Organization > Workflows > Import workflow
   - Upload JSON
   - Configurar trigger e targets

**Limitações:**
- ❌ Import manual obrigatório
- ❌ Não há validação via API
- ❌ Difícil de versionar (Git)
- ❌ Sem diagnóstico de erros via API

---

## Endpoints Relacionados a Automation

### Alerts

```python
# Obter configurações de alertas
alerts = dashboard.networks.getNetworkAlertsSettings(network_id)

# Atualizar alertas
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
# Listar HTTP servers (webhooks)
servers = dashboard.networks.getNetworkWebhooksHttpServers(network_id)

# Criar novo webhook
webhook = dashboard.networks.createNetworkWebhooksHttpServer(
    network_id,
    name='External Automation',
    url='https://automation.company.com/meraki',
    sharedSecret='SECRET'
)

# Webhook payload test
dashboard.networks.sendNetworkWebhooksTest(
    network_id,
    url='https://automation.company.com/meraki'
)
```

### Live Tools (Diagnostics)

```python
# Blink device LEDs
dashboard.devices.blinkDeviceLeds(serial, duration=20, duty=50, period=160)

# Reboot device
dashboard.devices.rebootDevice(serial)

# Ping device
ping = dashboard.devices.createDeviceLiveToolsPing(
    serial,
    target='8.8.8.8',
    count=5
)

# Get ping results
results = dashboard.devices.getDeviceLiveToolsPing(serial, ping['pingId'])
```

---

## Recomendações para o Projeto Meraki_Workflow

### Arquitetura Híbrida Proposta

```
┌────────────────────────────────────────────────────────┐
│                  MERAKI_WORKFLOW                        │
├────────────────────────────────────────────────────────┤
│                                                         │
│  1. Python Scripts (scripts/)                          │
│     ├── discovery.py      → Network analysis           │
│     ├── config.py         → Apply configurations       │
│     ├── automation.py     → Action Batches wrapper     │
│     └── scheduler.py      → Cron-like automation       │
│                                                         │
│  2. Workflow JSON Generator (scripts/workflow.py)      │
│     └── Gera JSONs válidos para import manual         │
│                                                         │
│  3. N8N Integration (opcional)                         │
│     └── Webhooks para event-driven automation          │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### Workflows: Estratégia Dual

1. **Para Automação Programática**: Usar Action Batches
   ```python
   # scripts/automation.py
   def bulk_update_vlans(org_id, vlan_id, networks):
       actions = build_vlan_actions(vlan_id, networks)
       return execute_action_batch(org_id, actions)
   ```

2. **Para Workflows Dashboard**: Gerar JSON para import manual
   ```python
   # scripts/workflow.py
   def create_workflow_json(workflow_type, params):
       return generate_cisco_workflow_json(workflow_type, params)

   # Uso:
   json = create_workflow_json('device_offline_alert', {...})
   save_to_file(f'clients/{client}/workflows/device_offline.json', json)
   # → Usuario importa manualmente no Dashboard
   ```

### Implementar em `scripts/automation.py`

```python
"""
Action Batches wrapper para automação em massa.
"""

class ActionBatchManager:
    def __init__(self, dashboard, org_id):
        self.dashboard = dashboard
        self.org_id = org_id

    def preview_batch(self, actions):
        """Executa batch em preview mode."""
        return self.dashboard.organizations.createOrganizationActionBatch(
            self.org_id,
            confirmed=False,
            synchronous=True,
            actions=actions
        )

    def execute_batch(self, actions, synchronous=False):
        """Executa batch confirmado."""
        return self.dashboard.organizations.createOrganizationActionBatch(
            self.org_id,
            confirmed=True,
            synchronous=synchronous,
            actions=actions
        )

    def get_batch_status(self, batch_id):
        """Verifica status de um batch."""
        return self.dashboard.organizations.getOrganizationActionBatch(
            self.org_id,
            batch_id
        )

    # Helpers para casos comuns
    def bulk_update_switch_ports(self, devices, port_config):
        """Atualizar portas de múltiplos switches."""
        actions = []
        for device in devices:
            ports = self.dashboard.switch.getDeviceSwitchPorts(device['serial'])
            for port in ports:
                actions.append({
                    'resource': f'/devices/{device["serial"]}/switchPorts/{port["portId"]}',
                    'operation': 'update',
                    'body': port_config
                })
        return self.execute_batch(actions)
```

---

## Conclusões Finais

### O que a API Oferece

✅ **Action Batches**: Automação em massa (CRUD completo)
✅ **Config Templates**: Templates reusáveis (CRUD completo)
✅ **Alerts**: Configuração de notificações
✅ **Webhooks**: Event-driven integrations
✅ **Live Tools**: Diagnostics e troubleshooting

### O que a API NÃO Oferece

❌ **Workflows Dashboard**: Criação/importação programática
❌ **Workflow Validation**: Diagnóstico de erros
❌ **Triggers Automation**: Via API (apenas manual no Dashboard)
❌ **Scheduled Tasks**: Cron-like nativo

### Estratégia Recomendada

1. **Usar Action Batches** para configurações em massa via API
2. **Gerar Workflow JSONs** para import manual no Dashboard
3. **Scripts Python + Cron** para automação recorrente
4. **Webhooks + N8N** para event-driven (opcional)
5. **Documentar claramente** que workflows requerem import manual

---

## Próximos Passos

- [x] Investigar endpoints da API
- [ ] Implementar `scripts/automation.py` (Action Batches wrapper)
- [ ] Atualizar `scripts/workflow.py` para gerar JSONs válidos
- [ ] Documentar no README.md a estratégia dual
- [ ] Criar exemplos de Action Batches comuns
- [ ] (Opcional) Integração com N8N para webhooks

---

**Última Atualização**: 2026-02-05
**Investigador**: Claude Code (Opus 4.5)
**Cliente**: jose-org (Org ID: 1437319)
