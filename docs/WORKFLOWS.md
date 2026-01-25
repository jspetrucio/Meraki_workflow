# Guia de Workflows Meraki

## Visao Geral

Este documento descreve como usar o sistema de geracao de workflows JSON para Meraki Dashboard.

**IMPORTANTE:** Workflows **NAO** podem ser criados via API. O sistema gera arquivos JSON que devem ser importados manualmente no Dashboard.

---

## Quick Start

### 1. Usar Template Pre-definido

```python
from scripts.workflow import create_device_offline_handler, save_workflow

# Criar workflow usando template
workflow = create_device_offline_handler(
    slack_channel="#network-alerts",
    wait_minutes=10
)

# Salvar para cliente
path = save_workflow(workflow, "cliente-acme")
print(f"Workflow salvo: {path}")
```

### 2. Criar Workflow Customizado

```python
from scripts.workflow import WorkflowBuilder, TriggerType, ActionType, save_workflow

workflow = (
    WorkflowBuilder("my-workflow", "My Custom Workflow")
    .add_trigger(TriggerType.WEBHOOK, event="device.status.change")
    .add_action("notify", ActionType.SLACK_POST, channel="#alerts", message="Alert!")
    .build()
)

save_workflow(workflow, "cliente-acme")
```

---

## Templates Disponiveis

### 1. Device Offline Handler

Notifica quando device fica offline por mais de X minutos.

```python
from scripts.workflow import create_device_offline_handler

workflow = create_device_offline_handler(
    slack_channel="#network-alerts",
    wait_minutes=5  # Espera 5min antes de notificar
)
```

**Fluxo:**
1. Trigger: Webhook `device.status.change` (status=offline)
2. Wait: X minutos
3. Check Status: Verifica se ainda offline
4. Notify: Slack se ainda offline

### 2. Firmware Compliance Check

Verifica devices com firmware desatualizado.

```python
from scripts.workflow import create_firmware_compliance_check

workflow = create_firmware_compliance_check(
    target_version="MX 18.211",
    email_recipients=["ops@example.com"]
)
```

**Fluxo:**
1. Trigger: Agendado (diario)
2. Get Devices: Lista todos os devices
3. Check Compliance: Compara firmware
4. Email: Envia relatorio de nao-compliance

### 3. Scheduled Report

Gera relatorios periodicos.

```python
from scripts.workflow import create_scheduled_report

workflow = create_scheduled_report(
    report_type="discovery",
    schedule_cron="0 8 * * 1",  # Segundas as 8h
    email_recipients=["cto@example.com"]
)
```

**Fluxo:**
1. Trigger: Agendado (cron)
2. Generate Report: Executa script Python
3. Email: Envia relatorio

### 4. Security Alert Handler

Processa alertas de seguranca (IDS, firewall).

```python
from scripts.workflow import create_security_alert_handler

workflow = create_security_alert_handler(
    slack_channel="#security",
    pagerduty_enabled=True  # Cria incidente no PagerDuty
)
```

**Fluxo:**
1. Trigger: Webhook `security.alert`
2. Notify Slack: Envia alerta
3. (Opcional) PagerDuty: Cria incidente

---

## Builder Pattern

### Criando Workflow com Builder

```python
from scripts.workflow import WorkflowBuilder, TriggerType, ActionType

workflow = (
    WorkflowBuilder(
        unique_name="my-workflow",  # ID unico (slug)
        name="My Workflow",         # Nome legivel
        description="Descricao"     # Descricao (opcional)
    )
    # Triggers
    .add_trigger(TriggerType.WEBHOOK, event="test.event")
    .add_trigger(TriggerType.SCHEDULE, cron="0 8 * * *")

    # Variables
    .add_variable("counter", "number", 0, "Contador")
    .add_input_variable("serial", "string", required=True, description="Serial do device")

    # Actions
    .add_action("step1", ActionType.MERAKI_GET_DEVICE, serial="$input.serial$")
    .add_action("notify", ActionType.SLACK_POST, channel="#test", message="Done!")

    # Build
    .build()
)
```

### Tipos de Triggers

```python
class TriggerType(Enum):
    WEBHOOK = "webhook"      # Eventos do Meraki
    SCHEDULE = "schedule"    # Cron schedule
    API_CALL = "api_call"    # Chamada API manual
    EMAIL = "email"          # Email recebido
```

**Exemplos de Triggers:**

```python
# Webhook
.add_trigger(TriggerType.WEBHOOK, event="device.status.change", status="offline")

# Schedule (cron)
.add_trigger(TriggerType.SCHEDULE, cron="0 8 * * 1", timezone="America/Sao_Paulo")

# API Call (manual)
.add_trigger(TriggerType.API_CALL)

# Email
.add_trigger(TriggerType.EMAIL, from_address="alerts@example.com")
```

### Tipos de Actions

#### Meraki API
```python
ActionType.MERAKI_GET_DEVICE
ActionType.MERAKI_GET_NETWORK
ActionType.MERAKI_UPDATE_DEVICE
ActionType.MERAKI_REBOOT_DEVICE
ActionType.MERAKI_GET_DEVICE_STATUS
ActionType.MERAKI_UPDATE_PORT
ActionType.MERAKI_GET_CLIENTS
```

#### Notificacao
```python
ActionType.SLACK_POST
ActionType.TEAMS_POST
ActionType.EMAIL_SEND
ActionType.PAGERDUTY_INCIDENT
ActionType.WEBHOOK_POST
```

#### ITSM
```python
ActionType.SERVICENOW_TICKET
ActionType.JIRA_ISSUE
```

#### Controle de Fluxo
```python
ActionType.CORE_SLEEP
ActionType.CORE_CONDITION
ActionType.CORE_LOOP
ActionType.CORE_PARALLEL
ActionType.CORE_SET_VARIABLE
```

#### Python
```python
ActionType.PYTHON_EXECUTE
```

---

## Acoes Condicionais

Acoes podem ter condicoes para execucao:

```python
.add_action(
    "reboot",
    ActionType.MERAKI_REBOOT_DEVICE,
    condition="$actions.get_status.status$ == 'offline'",
    serial="$input.serial$"
)
```

**Sintaxe de Condicoes:**
- Variaveis: `$vars.variable_name$`
- Input: `$input.variable_name$`
- Output de acoes: `$actions.action_name.property$`
- Operadores: `==`, `!=`, `>`, `<`, `>=`, `<=`, `AND`, `OR`

**Exemplos:**

```python
# Simples
condition="$vars.counter$ > 5"

# Multiplas condicoes
condition="$actions.get_device.status$ == 'offline' AND $vars.attempts$ < 3"

# Verificar resultado de acao anterior
condition="$actions.previous_step.executed$ == true"
```

---

## Variaveis

### Variables (Internas)

Variaveis internas do workflow, com valores padrão.

```python
.add_variable(
    name="wait_time",
    var_type="number",
    default_value=300,
    description="Tempo de espera em segundos"
)
```

### Input Variables

Variaveis fornecidas quando workflow e executado.

```python
.add_input_variable(
    name="device_serial",
    var_type="string",
    required=True,
    description="Serial do device"
)
```

**Tipos de variaveis:**
- `string`
- `number`
- `boolean`
- `array`
- `object`

---

## Loops

Executar acoes para multiplos itens:

```python
.add_action(
    "configure_ports",
    ActionType.CORE_LOOP,
    items="$input.port_list$",  # Array de items
    actions=[
        {
            "name": "update_port",
            "type": ActionType.MERAKI_UPDATE_PORT.value,
            "properties": {
                "serial": "$input.switch_serial$",
                "port_id": "$item$",  # Item atual do loop
                "vlan": "$input.vlan_id$"
            }
        }
    ]
)
```

---

## Validacao

Validar workflow antes de salvar:

```python
from scripts.workflow import validate_workflow

errors = validate_workflow(workflow)

if errors:
    print(f"Erros de validacao:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Workflow valido!")
```

**O que e validado:**
- `unique_name` nao vazio e formato correto
- `name` nao vazio
- Pelo menos 1 trigger
- Pelo menos 1 acao
- Nomes de acoes unicos
- Nomes de variaveis unicos

---

## Diagrama Visual

Gerar visualizacao ASCII do workflow:

```python
from scripts.workflow import workflow_to_diagram

print(workflow_to_diagram(workflow))
```

**Output:**
```
============================================================
Workflow: Device Offline Handler
ID: device-offline-handler
============================================================

TRIGGERS:
  [1] webhook
      - event: device.status.change
      - status: offline

ACTIONS:
  |
  +---> [1] wait
         Type: core.sleep
         Properties:
           - duration: $vars.wait_time$
  |
  +---> [2] check_status
         Type: meraki.get_device_status
         Properties:
           - serial: $input.device_serial$
  |
  +---> [3] notify_slack
         Type: slack.post_message
         Condition: $actions.check_status.status$ == 'offline'
         Properties:
           - channel: #alerts
           - message: Device offline!

============================================================
```

---

## Instrucoes de Importacao

Gerar instrucoes de como importar o workflow no Dashboard:

```python
from scripts.workflow import generate_import_instructions

instructions = generate_import_instructions(workflow, "cliente-acme")
print(instructions)

# Ou salvar em arquivo
Path("clients/cliente-acme/workflows/IMPORT.md").write_text(instructions)
```

Isso gera um guia markdown com:
1. Path do arquivo JSON
2. Passo-a-passo de importacao
3. Credenciais necessarias (Slack, Jira, etc)
4. Como ativar o workflow
5. Como monitorar execucoes

---

## Salvar e Carregar

### Salvar Workflow

```python
from scripts.workflow import save_workflow

path = save_workflow(workflow, "cliente-acme")
# Salva em: clients/cliente-acme/workflows/{unique_name}.json
```

Isso tambem:
- Cria diretorio se nao existir
- Registra no changelog do cliente
- Retorna Path do arquivo

### Carregar Workflow

```python
from scripts.workflow import load_workflow
from pathlib import Path

path = Path("clients/cliente-acme/workflows/my-workflow.json")
workflow = load_workflow(path)
```

### Listar Workflows

```python
from scripts.workflow import list_workflows

workflows = list_workflows("cliente-acme")
print(f"Workflows: {workflows}")
# Output: ['device-offline-handler', 'firmware-compliance-check', ...]
```

---

## Formato JSON

O JSON gerado segue o formato Meraki Dashboard:

```json
{
  "workflow": {
    "unique_name": "my-workflow",
    "name": "My Workflow",
    "description": "Descricao",
    "type": "automation",
    "schema_version": "1.0.0"
  },
  "triggers": [
    {
      "type": "webhook",
      "properties": {
        "event": "device.status.change"
      }
    }
  ],
  "actions": [
    {
      "name": "step1",
      "type": "meraki.get_device",
      "properties": {
        "serial": "$input.serial$"
      },
      "condition": "$vars.enabled$ == true"
    }
  ],
  "variables": [
    {
      "name": "enabled",
      "type": "boolean",
      "default": true,
      "description": "Se workflow esta ativo",
      "required": false
    }
  ],
  "input_variables": [
    {
      "name": "serial",
      "type": "string",
      "default": null,
      "description": "Serial do device",
      "required": true
    }
  ]
}
```

---

## Importar no Meraki Dashboard

### Passo-a-Passo

1. **Acessar Dashboard**
   - https://dashboard.meraki.com
   - Selecionar organizacao
   - Organization > Workflows

2. **Importar Workflow**
   - Clicar em "Import Workflow"
   - Selecionar arquivo JSON
   - Revisar configuracoes
   - Clicar em "Import"

3. **Configurar Credenciais**

   Se o workflow usa servicos externos, configurar credenciais:

   - **Slack:** Organization > Settings > Integrations > Slack
   - **Microsoft Teams:** Organization > Settings > Integrations > Teams
   - **PagerDuty:** Organization > Settings > Integrations > PagerDuty
   - **Jira:** Organization > Settings > Integrations > Jira
   - **Email:** Organization > Settings > Email

4. **Ativar Workflow**
   - Workflow importado vem **desativado**
   - Clicar no workflow > Enable
   - Testar com trigger manual (se aplicavel)

5. **Monitorar Execucoes**
   - Organization > Workflows > Executions
   - Ver logs de cada execucao
   - Debugar falhas

---

## Exemplos Completos

Ver `/Users/josdasil/Documents/Meraki_Workflow/examples/workflow_usage.py` para exemplos completos:

```bash
python3 examples/workflow_usage.py
```

Isso gera workflows de exemplo em `clients/exemplo/workflows/`:
- `device-offline-handler.json`
- `firmware-compliance-check.json`
- `scheduled-report-discovery.json`
- `security-alert-handler.json`
- `port-security-violation.json`
- `smart-device-reboot.json`
- `bulk-port-config.json`

---

## Changelog

Toda criacao de workflow e registrada automaticamente no changelog do cliente:

```markdown
## 2026-01-24 17:15

**Tipo:** workflow
**Acao:** created
**Recurso:** Device Offline Handler

**Detalhes:**
- type: automation

**Usuario:** claude
```

---

## Troubleshooting

### Workflow nao importa

- Verificar se JSON e valido (usar validador online)
- Verificar se `unique_name` e unico na organizacao
- Verificar se todos os campos obrigatorios estao presentes

### Workflow nao executa

- Verificar se workflow esta **ativado**
- Verificar credenciais de servicos externos
- Verificar logs de execucao no Dashboard
- Verificar condicoes das acoes

### Acao falha

- Verificar propriedades da acao (serial correto, etc)
- Verificar referencias a variaveis (`$vars.name$`)
- Verificar output de acoes anteriores
- Ver logs no Dashboard

---

## Limitacoes

1. **Workflows NAO podem ser criados via API**
   - Apenas via Dashboard UI
   - Solucao: Gerar JSON e importar manualmente

2. **Alguns action types podem nao estar disponiveis**
   - Depende da licenca Meraki
   - Depende dos produtos na organizacao

3. **Limites de execucao**
   - Cada workflow tem limites de:
     - Execucoes por hora
     - Tempo maximo de execucao
     - Acoes por execucao

4. **Python Execute tem sandbox**
   - Nao pode instalar packages
   - Acesso limitado a recursos externos

---

## Referencias

- [Meraki Workflows Documentation](https://documentation.meraki.com/Platform_Management/Workflows)
- [Meraki Dashboard API](https://developer.cisco.com/meraki/api-v1/)
- [Workflow JSON Schema](https://developer.cisco.com/meraki/workflows/)
