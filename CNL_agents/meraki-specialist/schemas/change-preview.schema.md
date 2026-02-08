# Schema: change-preview

## Propósito
Estrutura padronizada do preview mostrado ao usuário ANTES de aplicar qualquer mudança.
Gerado no Step 3 (Generate Preview) de qualquer task.

---

## Schema

```json
{
  "change_preview": {
    "request_id": "REQ-{id} — referência ao change-request",
    "timestamp": "ISO-8601",
    
    "summary": "string — 1 linha descrevendo a mudança",
    
    "current_state": {
      "description": "string — estado atual legível",
      "raw": "object — GET response completo da API"
    },
    
    "proposed_state": {
      "description": "string — estado proposto legível",
      "raw": "object — payload que será enviado na API"
    },
    
    "diff": [
      {
        "field": "string — campo que muda",
        "before": "any — valor atual",
        "after": "any — valor proposto"
      }
    ],
    
    "impact": {
      "devices_affected": "integer",
      "device_list": ["string — name (serial)"],
      "users_affected": "integer | unknown",
      "downtime_expected": "none | brief (<5s) | moderate (5-60s) | extended (>60s)",
      "risk_level": "low | moderate | high | critical"
    },
    
    "warnings": [
      {
        "severity": "info | warning | critical",
        "message": "string"
      }
    ],
    
    "catalyst_info": {
      "present": "boolean — se algum device é Catalyst",
      "mode": "native_meraki | managed | monitored",
      "sgt_ports_locked": "integer — número de portas SGT locked",
      "license": "enterprise | advanced"
    },
    
    "rollback_available": "boolean",
    "requires_confirmation": "boolean — sempre true"
  }
}
```

---

## Template de Apresentação ao Usuário

O LLM deve formatar o preview assim:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 PREVIEW DA MUDANÇA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{summary}

Dispositivos: {devices_affected} ({device_list resumido})
Risco: {risk_level}
Downtime esperado: {downtime_expected}

Mudanças:
  [antes] {current_state.description}
  [depois] {proposed_state.description}

{warnings — se houver}

Rollback disponível: {sim/não}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Confirma? (sim/não)
```

---

## Regras de Apresentação

1. **SEMPRE mostrar antes/depois** — nunca apenas o estado proposto
2. **SEMPRE mostrar contagem de devices** — "5 switches" é mais claro que lista
3. **Se > 3 devices:** Resumir lista, mostrar completa só se pedido
4. **Warnings na frente:** Se tem critical warning, mostrar ANTES do diff
5. **Catalyst info:** Só mostrar se há devices Catalyst na operação
6. **Downtime:** Ser honesto — SSID change = "brief", firewall = "none", port change = "brief"
7. **Risk level visual:**
   - 🟢 low
   - 🟡 moderate
   - 🟠 high
   - 🔴 critical

---

## Exemplo Preenchido

```json
{
  "change_preview": {
    "request_id": "REQ-20240115-143200",
    "timestamp": "2024-01-15T14:32:05Z",
    "summary": "Criar ACL 'block-telnet' (deny TCP:23) em 5 switches",
    "current_state": {
      "description": "ACL atual: 1 regra (allow all)",
      "raw": { "rules": [{ "policy": "allow", "protocol": "any" }] }
    },
    "proposed_state": {
      "description": "ACL proposta: 2 regras (deny TCP:23 + allow all)",
      "raw": { "rules": [
        { "policy": "deny", "protocol": "tcp", "dstPort": "23", "comment": "Block Telnet" },
        { "policy": "allow", "protocol": "any" }
      ]}
    },
    "diff": [
      {
        "field": "acl_rules",
        "before": "1 regra (allow all)",
        "after": "2 regras (deny TCP:23 + allow all)"
      }
    ],
    "impact": {
      "devices_affected": 5,
      "device_list": ["MS425-Core (XXXX-01)", "MS225-Acc1 (XXXX-02)", "..."],
      "users_affected": "unknown",
      "downtime_expected": "none",
      "risk_level": "high"
    },
    "warnings": [
      {
        "severity": "info",
        "message": "Telnet (TCP:23) será bloqueado — confirme que nenhum device usa telnet para gerência"
      }
    ],
    "catalyst_info": { "present": false },
    "rollback_available": true,
    "requires_confirmation": true
  }
}
```
