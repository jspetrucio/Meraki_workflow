# Cisco Workflows JSON Schema - Knowledge Base

> **IMPORTANTE**: Este documento define o formato CORRETO para criar workflows que podem ser importados no Meraki Dashboard.
> Meraki Workflows usa o motor **Cisco Workflows** (antigo SecureX Orchestration).

---

## Estrutura Raiz do JSON

```json
{
  "workflow": { ... },
  "categories": { ... }
}
```

**AMBOS os objetos sao OBRIGATORIOS** para importacao bem-sucedida.

---

## Objeto `workflow`

### Campos Obrigatorios

| Campo | Formato | Exemplo |
|-------|---------|---------|
| `unique_name` | `definition_workflow_<ID>` | `definition_workflow_02NXTSAQL5ZNK3kEJpVUecfDz1ZNss1zGXd` |
| `name` | String descritiva | `Blink Meraki Device LEDs` |
| `title` | Igual ao name | `Blink Meraki Device LEDs` |
| `type` | SEMPRE `generic.workflow` | `generic.workflow` |
| `base_type` | SEMPRE `workflow` | `workflow` |
| `object_type` | SEMPRE `definition_workflow` | `definition_workflow` |
| `variables` | Array de variaveis | `[...]` |
| `properties` | Objeto de propriedades | `{...}` |
| `actions` | Array de acoes | `[...]` |
| `categories` | Array de IDs | `["category_02NXV6O12LF114DhKxx98npicaIPTPJql2v"]` |

### Geracao de IDs

IDs devem ter exatamente **37 caracteres alfanumericos** apos o prefixo:

```
Prefixo                    + ID (37 chars)
definition_workflow_       + 02NXTSAQL5ZNK3kEJpVUecfDz1ZNss1zGXd
variable_workflow_         + 02NXTSAR6KFTM0WBeVsIxZih1kDUiGd7aJw
definition_activity_       + 02NXTSATP1NXX3sJziA9MInu5AYQyZAqHjU
category_                  + 02NXV6O12LF114DhKxx98npicaIPTPJql2v
```

**Regra de geracao**: Usar caracteres [A-Za-z0-9], 37 caracteres, começando com "02" para novos workflows.

---

## Objeto `properties` (dentro de workflow)

```json
{
  "properties": {
    "atomic": {
      "is_atomic": false
    },
    "delete_workflow_instance": false,
    "description": "Descricao do workflow",
    "display_name": "Nome para exibicao",
    "runtime_user": {
      "target_default": true
    },
    "target": {
      "target_type": "meraki.endpoint",
      "specify_on_workflow_start": true
    }
  }
}
```

### Target Types Disponiveis

| Target Type | Uso |
|-------------|-----|
| `meraki.endpoint` | Acoes que usam Meraki API |
| `web-service.endpoint` | Webhooks e APIs externas |
| `no_target` | Acoes locais sem API |

**IMPORTANTE**: Para workflows Meraki, usar `"target_type": "meraki.endpoint"`.

---

## Objeto `variables` (Array)

Cada variavel deve ter:

```json
{
  "schema_id": "datatype.string",
  "properties": {
    "value": "",
    "scope": "input",
    "name": "Nome da Variavel",
    "type": "datatype.string",
    "description": "Descricao da variavel",
    "is_required": true,
    "display_on_wizard": false,
    "is_invisible": false
  },
  "unique_name": "variable_workflow_02NXTSAR6KFTM0WBeVsIxZih1kDUiGd7aJw",
  "object_type": "variable_workflow"
}
```

### Schema IDs Disponiveis

| schema_id | Tipo Python | Exemplo value |
|-----------|-------------|---------------|
| `datatype.string` | str | `""` |
| `datatype.integer` | int | `0` |
| `datatype.boolean` | bool | `false` |
| `datatype.secure_string` | str (senha) | `""` |
| `datatype.date` | str (ISO) | `"2024-01-01"` |

### Scopes

| Scope | Uso |
|-------|-----|
| `input` | Parametro de entrada (usuario fornece) |
| `output` | Resultado do workflow |
| `local` | Variavel interna |

---

## Objeto `actions` (Array)

### Acao Meraki API Request

Esta e a acao PRINCIPAL para interagir com Meraki:

```json
{
  "unique_name": "definition_activity_02NXTSATP1NXX3sJziA9MInu5AYQyZAqHjU",
  "name": "Generic Meraki API Request",
  "title": "Titulo da Acao",
  "type": "meraki.api_request",
  "base_type": "activity",
  "properties": {
    "action_timeout": 180,
    "api_body": "{\"key\": \"value\"}",
    "api_method": "POST",
    "api_url": "/api/v1/devices/$workflow.definition_workflow_XXX.input.variable_workflow_YYY$/endpoint",
    "continue_on_failure": false,
    "display_name": "Titulo da Acao",
    "runtime_user": {
      "target_default": true
    },
    "skip_execution": false,
    "target": {
      "use_workflow_target": true
    }
  },
  "object_type": "definition_activity"
}
```

### API Methods

| Metodo | Uso |
|--------|-----|
| `GET` | Obter dados |
| `POST` | Criar recursos |
| `PUT` | Atualizar recursos |
| `DELETE` | Remover recursos |

### Referencia de Variaveis em `api_url`

Formato: `$workflow.<workflow_unique_name>.<scope>.<variable_unique_name>$`

Exemplo:
```
/api/v1/devices/$workflow.definition_workflow_02NXTSAQL5ZNK3kEJpVUecfDz1ZNss1zGXd.input.variable_workflow_02NXTSAR6KFTM0WBeVsIxZih1kDUiGd7aJw$/liveTools/leds/blink
```

---

## Objeto `categories` (Raiz)

**OBRIGATORIO** - Deve existir na raiz do JSON:

```json
{
  "categories": {
    "category_02NXV6O12LF114DhKxx98npicaIPTPJql2v": {
      "unique_name": "category_02NXV6O12LF114DhKxx98npicaIPTPJql2v",
      "name": "Meraki Automation",
      "title": "Meraki Automation",
      "type": "basic.category",
      "base_type": "category",
      "category_type": "custom",
      "object_type": "category"
    }
  }
}
```

O ID da categoria deve ser referenciado no array `categories` dentro do workflow.

---

## Exemplo Completo Minimo

```json
{
  "workflow": {
    "unique_name": "definition_workflow_02ABC123XYZ456789DEFGHIJKLMNOPQRST",
    "name": "Device Status Check",
    "title": "Device Status Check",
    "type": "generic.workflow",
    "base_type": "workflow",
    "variables": [
      {
        "schema_id": "datatype.string",
        "properties": {
          "value": "",
          "scope": "input",
          "name": "Device Serial",
          "type": "datatype.string",
          "description": "Serial number do device Meraki",
          "is_required": true,
          "display_on_wizard": false,
          "is_invisible": false
        },
        "unique_name": "variable_workflow_02ABC123XYZ456789DEFGHIJKLMNOPQRSTU",
        "object_type": "variable_workflow"
      }
    ],
    "properties": {
      "atomic": {
        "is_atomic": false
      },
      "delete_workflow_instance": false,
      "description": "Verifica status de um device Meraki",
      "display_name": "Device Status Check",
      "runtime_user": {
        "target_default": true
      },
      "target": {
        "target_type": "meraki.endpoint",
        "specify_on_workflow_start": true
      }
    },
    "object_type": "definition_workflow",
    "actions": [
      {
        "unique_name": "definition_activity_02ABC123XYZ456789DEFGHIJKLMNOPQRSTV",
        "name": "Generic Meraki API Request",
        "title": "Get Device Status",
        "type": "meraki.api_request",
        "base_type": "activity",
        "properties": {
          "action_timeout": 180,
          "api_body": "",
          "api_method": "GET",
          "api_url": "/api/v1/devices/$workflow.definition_workflow_02ABC123XYZ456789DEFGHIJKLMNOPQRST.input.variable_workflow_02ABC123XYZ456789DEFGHIJKLMNOPQRSTU$",
          "continue_on_failure": false,
          "display_name": "Get Device Status",
          "runtime_user": {
            "target_default": true
          },
          "skip_execution": false,
          "target": {
            "use_workflow_target": true
          }
        },
        "object_type": "definition_activity"
      }
    ],
    "categories": [
      "category_02ABC123XYZ456789DEFGHIJKLMNOPQRSTW"
    ]
  },
  "categories": {
    "category_02ABC123XYZ456789DEFGHIJKLMNOPQRSTW": {
      "unique_name": "category_02ABC123XYZ456789DEFGHIJKLMNOPQRSTW",
      "name": "Meraki Automation",
      "title": "Meraki Automation",
      "type": "basic.category",
      "base_type": "category",
      "category_type": "custom",
      "object_type": "category"
    }
  }
}
```

---

## Endpoints Meraki API Comuns

| Operacao | Method | Endpoint |
|----------|--------|----------|
| Get Device | GET | `/api/v1/devices/{serial}` |
| Get Device Status | GET | `/api/v1/organizations/{orgId}/devices/statuses` |
| Blink LEDs | POST | `/api/v1/devices/{serial}/liveTools/leds/blink` |
| Reboot Device | POST | `/api/v1/devices/{serial}/reboot` |
| Get Network | GET | `/api/v1/networks/{networkId}` |
| Get SSIDs | GET | `/api/v1/networks/{networkId}/wireless/ssids` |
| Update SSID | PUT | `/api/v1/networks/{networkId}/wireless/ssids/{number}` |
| Get Firewall Rules | GET | `/api/v1/networks/{networkId}/appliance/firewall/l3FirewallRules` |

---

## Acoes Adicionais

### Condition Block (If/Else)

```json
{
  "unique_name": "definition_activity_XXX",
  "name": "Condition Block",
  "title": "Check if offline",
  "type": "logic.condition_block",
  "base_type": "activity",
  "properties": {
    "continue_on_failure": false,
    "display_name": "Check if offline"
  },
  "object_type": "definition_activity",
  "blocks": [
    {
      "unique_name": "definition_activity_YYY",
      "name": "Condition Branch",
      "title": "If status is offline",
      "type": "logic.condition_block",
      "base_type": "activity",
      "properties": {
        "condition": {
          "left_operand": "$activity.previous_activity.output.body$",
          "operator": "contains",
          "right_operand": "offline"
        },
        "continue_on_failure": false
      },
      "object_type": "definition_activity",
      "actions": [
        // Acoes a executar se condicao for verdadeira
      ]
    }
  ]
}
```

### HTTP Request (Webhook/External API)

```json
{
  "unique_name": "definition_activity_XXX",
  "name": "HTTP Request",
  "title": "Send Slack Notification",
  "type": "web-service.http_request",
  "base_type": "activity",
  "properties": {
    "action_timeout": 180,
    "allow_auto_redirect": true,
    "body": "{\"text\": \"Device offline alert\"}",
    "content_type": "application/json",
    "continue_on_error_status_code": false,
    "display_name": "Send Slack Notification",
    "method": "POST",
    "runtime_user": {
      "target_default": true
    },
    "target": {
      "use_workflow_target": false,
      "target_type": "web-service.endpoint",
      "target_id": "definition_target_XXX"
    },
    "url": "https://hooks.slack.com/services/XXX"
  },
  "object_type": "definition_activity"
}
```

---

## Validacao Antes de Importar

Checklist:
- [ ] `unique_name` começa com `definition_workflow_`
- [ ] ID tem 37 caracteres alfanumericos
- [ ] `type` é `generic.workflow`
- [ ] `base_type` é `workflow`
- [ ] `object_type` é `definition_workflow`
- [ ] `target` tem `target_type` definido (ex: `meraki.endpoint`)
- [ ] Existe objeto `categories` na raiz do JSON
- [ ] Cada variavel tem `object_type: variable_workflow`
- [ ] Cada acao tem `object_type: definition_activity`
- [ ] Referencias de variaveis usam formato completo `$workflow.XXX.scope.YYY$`

---

## Fontes de Referencia

- CiscoDevNet/CiscoWorkflowsAutomation - Exemplos oficiais
- cisco/ActionOrchestratorContent - Atomics e blocos
- Meraki Dashboard Workflows - Exportar workflows existentes

---

**Ultima Atualizacao**: 2026-01-24
**Baseado em**: Engenharia reversa de workflows oficiais Cisco
