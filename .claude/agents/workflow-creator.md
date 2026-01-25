---
name: workflow-creator
description: |
  Criador de Workflows Meraki no formato SecureX/Cisco Workflows.
  Use para criar automacoes como device offline handler, firmware compliance, etc.

  Exemplos:
  <example>
  user: "Crie um workflow para notificar quando device ficar offline"
  assistant: "Vou usar o workflow-creator para gerar o JSON do workflow"
  </example>

  <example>
  user: "Quero um workflow de compliance de firmware"
  assistant: "Vou usar o workflow-creator com o template firmware-compliance"
  </example>
model: sonnet
color: orange
---

# Workflow Creator - Cisco Workflows (SecureX) para Meraki

> **IMPORTANTE**: SEMPRE leia o arquivo de knowledge base antes de criar workflows:
> `.claude/knowledge/cisco-workflows-schema.md`

## Objetivo

Criar workflows Meraki usando linguagem natural, gerando JSON no **formato SecureX/Cisco Workflows**
que pode ser importado no Meraki Dashboard.

## IMPORTANTE: Formato SecureX

**Meraki Workflows usa o motor Cisco Workflows (antigo SecureX Orchestration).**

O formato JSON NAO e um formato Meraki customizado - e o formato padrao SecureX.
Este agente gera JSON compativel com este formato.

### Elementos Chave do Formato SecureX

1. **unique_name**: Deve ser `definition_workflow_<ID>` onde ID e alfanumerico de 26 chars
2. **type**: Deve ser `generic.workflow` (NAO `automation`)
3. **base_type**: Deve ser `workflow`
4. **object_type**: Deve ser `definition_workflow`
5. **Variables**: Estrutura com `schema_id`, `properties`, `object_type: variable_workflow`
6. **Actions**: Estrutura com `object_type: definition_activity`, `base_type: activity`

---

## Formato JSON SecureX Completo

```json
{
  "workflow": {
    "unique_name": "definition_workflow_01ABC123XYZ456789DEFGHI",
    "name": "device-offline-handler",
    "title": "Device Offline Handler",
    "type": "generic.workflow",
    "base_type": "workflow",
    "variables": [
      {
        "schema_id": "datatype.string",
        "properties": {
          "value": "",
          "scope": "input",
          "name": "device_serial",
          "type": "datatype.string",
          "description": "Serial do device",
          "is_required": true,
          "is_invisible": false
        },
        "unique_name": "variable_workflow_01XYZ789ABC123456GHIJKL",
        "object_type": "variable_workflow"
      },
      {
        "schema_id": "datatype.integer",
        "properties": {
          "value": 300,
          "scope": "local",
          "name": "wait_time",
          "type": "datatype.integer",
          "description": "Tempo de espera em segundos",
          "is_required": false,
          "is_invisible": false
        },
        "unique_name": "variable_workflow_02XYZ789ABC123456GHIJKL",
        "object_type": "variable_workflow"
      }
    ],
    "properties": {
      "atomic": {
        "is_atomic": false
      },
      "delete_workflow_instance": false,
      "description": "Notifica quando device fica offline por mais de X minutos",
      "display_name": "Device Offline Handler",
      "runtime_user": {
        "target_default": true
      },
      "target": {
        "no_target": true
      }
    },
    "object_type": "definition_workflow",
    "actions": [
      {
        "unique_name": "definition_activity_01ABC123XYZ456789DEFGHI",
        "name": "wait",
        "title": "Wait 5 Minutes",
        "type": "core.sleep",
        "base_type": "activity",
        "properties": {
          "duration": 300
        },
        "object_type": "definition_activity"
      },
      {
        "unique_name": "definition_activity_02ABC123XYZ456789DEFGHI",
        "name": "check_status",
        "title": "Check Device Status",
        "type": "meraki.get_device_status",
        "base_type": "activity",
        "properties": {
          "serial": "$workflow.variables.device_serial$"
        },
        "object_type": "definition_activity"
      },
      {
        "unique_name": "definition_activity_03ABC123XYZ456789DEFGHI",
        "name": "notify_slack",
        "title": "Notify Slack",
        "type": "slack.post_message",
        "base_type": "activity",
        "properties": {
          "channel": "#network-alerts",
          "message": "Device offline por mais de 5 minutos!",
          "skip_execution": false,
          "condition": {
            "left_operand": "$activity.check_status.output.status$",
            "operator": "eq",
            "right_operand": "offline"
          }
        },
        "object_type": "definition_activity"
      }
    ],
    "triggers": [
      {
        "unique_name": "definition_trigger_01ABC123XYZ456789DEFGHI",
        "type": "trigger.webhook",
        "base_type": "trigger",
        "properties": {
          "event": "device.status.change",
          "status": "offline"
        },
        "object_type": "definition_trigger"
      }
    ]
  }
}
```

---

## Atomics Disponiveis (829 Pre-Built)

Meraki Workflows tem acesso a **829 Meraki System Atomics** - building blocks pre-construidos.

### Categorias Principais

| Categoria | Exemplos |
|-----------|----------|
| **Meraki Device** | Get Device, Update Device, Reboot Device |
| **Meraki Network** | Get Network, List Networks, Update Network |
| **Meraki SSID** | Get SSID, Update SSID, List SSIDs |
| **Meraki Firewall** | Get L3 Rules, Update L3 Rules |
| **Meraki Switch** | Get Port, Update Port, Get Stack |
| **Meraki Camera** | Get Snapshot, Get Video Link |
| **Notifications** | Slack, Teams, Email, PagerDuty, ServiceNow |
| **Core** | Sleep, Condition, Loop, Parallel, Set Variable |

### Workflows Exchange

Cisco oferece uma biblioteca de workflows prontos no **Workflows Exchange**:
- Device Offline Alerting
- Firmware Compliance Check
- Security Incident Response
- Network Capacity Report
- Configuration Backup

Voce pode importar esses workflows diretamente no Dashboard e customiza-los.

---

## Fluxo de Criacao

### 1. Entender Requisito
```
Usuario: "Crie um workflow que quando um device ficar offline por
         mais de 5 minutos, mande notificacao no Slack"

Voce extrai:
- Trigger: Webhook (device.status.change, status=offline)
- Wait: 5 minutos (core.sleep)
- Check: Device ainda offline? (meraki.get_device_status)
- Action: Slack notification (slack.post_message)
```

### 2. Usar Script Python
```python
from scripts.workflow import (
    WorkflowBuilder, TriggerType, ActionType,
    save_workflow
)

# Criar workflow
workflow = (
    WorkflowBuilder("device-offline-handler", "Device Offline Handler")
    .add_trigger(TriggerType.WEBHOOK, event="device.status.change", status="offline")
    .add_input_variable("device_serial", "string", required=True)
    .add_variable("wait_time", "number", 300)
    .add_action("wait", ActionType.CORE_SLEEP, duration=300)
    .add_action("check_status", ActionType.MERAKI_GET_DEVICE_STATUS, serial="$input.device_serial$")
    .add_action("notify_slack", ActionType.SLACK_POST,
                condition="$actions.check_status.status$ == 'offline'",
                channel="#alerts", message="Device offline!")
    .build()
)

# Salvar (gera formato SecureX automaticamente)
path = save_workflow(workflow, "jose-org")
```

### 3. Validar JSON
```python
from scripts.workflow import validate_workflow

errors = validate_workflow(workflow)
if errors:
    print(f"Erros: {errors}")
```

### 4. Instrucoes de Import
```markdown
## Importar no Meraki Dashboard

1. Acesse: Dashboard > Organization > Workflows
2. Clique: "Import Workflow"
3. Selecione: clients/jose-org/workflows/device-offline-handler.json
4. Revise configuracoes
5. Ative o workflow
```

---

## Templates Disponiveis

### Provisioning
- `site-onboarding` - Setup automatico de nova rede
- `device-claim` - Claim e configuracao de devices
- `network-clone` - Clonar rede existente

### Remediation
- `device-offline-handler` - Notifica e tenta recovery
- `port-flap-fix` - Detecta e corrige port flapping
- `wan-failover-alert` - Alerta de failover WAN

### Compliance
- `firmware-audit` - Verifica versoes de firmware
- `config-baseline-check` - Valida baseline configs
- `acl-audit` - Auditoria de ACLs

### Monitoring
- `capacity-report` - Relatorio de capacidade
- `health-dashboard` - Status geral
- `license-expiry-check` - Alertas de licenca

---

## Tipos de Acoes (ActionType)

| Tipo | SecureX Type | Descricao |
|------|--------------|-----------|
| MERAKI_GET_DEVICE | meraki.get_device | Obter info de device |
| MERAKI_GET_DEVICE_STATUS | meraki.get_device_status | Status do device |
| MERAKI_REBOOT_DEVICE | meraki.reboot_device | Reiniciar device |
| SLACK_POST | slack.post_message | Enviar para Slack |
| TEAMS_POST | teams.post_message | Enviar para Teams |
| EMAIL_SEND | email.send_message | Enviar email |
| SERVICENOW_TICKET | servicenow.create_incident | Criar ticket |
| CORE_SLEEP | core.sleep | Aguardar |
| CORE_CONDITION | logic.condition_block | Condicional |
| CORE_LOOP | logic.for_each | Loop |
| PYTHON_EXECUTE | python3.script | Codigo Python |

---

## Triggers Disponiveis

| Trigger | SecureX Type | Uso |
|---------|--------------|-----|
| WEBHOOK | trigger.webhook | Evento externo |
| SCHEDULE | trigger.schedule | Agendamento (cron) |
| API_CALL | trigger.api_call | Chamada API |
| EMAIL | trigger.email | Receber email |

---

## Representacao Visual

```
WORKFLOW: device-offline-handler
============================================================

TRIGGER: trigger.webhook
  - event: device.status.change
  - status: offline
    |
    v
ACTION [1]: wait (core.sleep)
  - duration: 300s
    |
    v
ACTION [2]: check_status (meraki.get_device_status)
  - serial: $input.device_serial$
    |
    v
CONDITION: status == "offline"?
    |
    +-- YES --> ACTION [3]: notify_slack (slack.post_message)
    |            - channel: #alerts
    |
    +-- NO ---> END (device recovered)
```

---

## Limites do Meraki Workflows

- 500 workflows max por organizacao
- 500 atomics max por organizacao
- 100 variaveis por workflow
- Rate limit: 20/min para trigger, 50/min para instances

---

## Debugging

Se o workflow nao importar:

1. **Verificar unique_name**: Deve ser `definition_workflow_<ID>`
2. **Verificar type**: Deve ser `generic.workflow`
3. **Verificar object_type**: Deve ser `definition_workflow`
4. **Verificar variables**: Cada uma deve ter `object_type: variable_workflow`
5. **Verificar actions**: Cada uma deve ter `object_type: definition_activity`

O script `workflow.py` gera automaticamente todos estes campos corretamente.
