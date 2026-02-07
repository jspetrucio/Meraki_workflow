# Schema: change-log

## Propósito
Registro permanente de cada mudança aplicada. Usado para:
- Audit trail
- Rollback (contém backup_state)
- Histórico da sessão
- Handoff context entre agentes

---

## Schema

```json
{
  "change_log": {
    "change_id": "CHG-{YYYYMMDD}-{HHMMSS}",
    "request_id": "REQ-{id} — referência ao change-request original",
    "timestamp": "ISO-8601 — quando foi aplicado",
    
    "task": "configure-wireless | configure-switching | configure-security | configure-monitoring | rollback | executar-especifico",
    
    "operation": {
      "type": "create | update | delete | rollback",
      "resource": "string",
      "action": "string — ação específica"
    },
    
    "targets": {
      "organization_id": "string",
      "network_id": "string",
      "network_name": "string",
      "device_serials": ["string"],
      "device_names": ["string"],
      "specific_ids": {}
    },
    
    "backup_state": {
      "captured_at": "ISO-8601",
      "data": "object — GET response ANTES da mudança (estado completo)"
    },
    
    "applied_state": {
      "applied_at": "ISO-8601",
      "data": "object — payload enviado para a API"
    },
    
    "verified_state": {
      "verified_at": "ISO-8601",
      "matches_expected": "boolean",
      "data": "object — GET response DEPOIS da mudança"
    },
    
    "result": {
      "status": "success | partial_success | failed | rolled_back",
      "api_responses": [
        {
          "endpoint": "string",
          "method": "GET | POST | PUT | DELETE",
          "status_code": "integer",
          "success": "boolean",
          "error_message": "string | null"
        }
      ],
      "duration_ms": "integer"
    },
    
    "context": {
      "user_confirmed": "boolean",
      "catalyst_mode": "native_meraki | managed | monitored | null",
      "sgt_check_passed": "boolean | null",
      "handoff_from": "string | null",
      "handoff_to": "string | null",
      "session_id": "string"
    },
    
    "rollback": {
      "available": "boolean",
      "performed": "boolean",
      "performed_at": "ISO-8601 | null",
      "rollback_change_id": "CHG-{id} | null — referência ao CHG do rollback"
    },
    
    "human_readable": {
      "summary": "string — 1 linha para display",
      "details": "string — markdown formatado para changelog"
    }
  }
}
```

---

## Template human_readable.details

```markdown
## {timestamp}

**Ação:** {operation.action}
**Status:** {result.status}
**Task:** {task}
**Device(s):** {device_names} ({device_serials})
**Rede:** {network_name}

### Mudanças
- [antes] {backup_state resumido}
- [depois] {applied_state resumido}

### Verificação
- Match esperado: {verified_state.matches_expected}

### Contexto
- Catalyst mode: {catalyst_mode}
- Confirmado pelo usuário: {user_confirmed}
- Handoff: {handoff_from} → {handoff_to}

### Rollback
- Disponível: {rollback.available}
- Comando: `rollback --change-id={change_id}`
```

---

## Regras

1. **backup_state é OBRIGATÓRIO** — sem backup, sem mudança
2. **verified_state:** SEMPRE fazer GET após aplicar para confirmar
3. **result.api_responses:** Registrar CADA call individual (para debug)
4. **rollback.available:** `true` para tudo exceto firmware e operações destrutivas
5. **Retenção:** Manter na sessão. Persistir em arquivo se sessão longa (>10 changes)
6. **change_id é único:** Nunca reutilizar, mesmo após rollback
7. **Rollback gera novo CHG:** Rollback é uma mudança — gera seu próprio change_log entry

---

## Exemplo Preenchido

```json
{
  "change_log": {
    "change_id": "CHG-20240115-143215",
    "request_id": "REQ-20240115-143200",
    "timestamp": "2024-01-15T14:32:15Z",
    "task": "configure-switching",
    "operation": {
      "type": "update",
      "resource": "acl",
      "action": "add_deny_rule"
    },
    "targets": {
      "organization_id": "123456",
      "network_id": "L_789",
      "network_name": "HQ-Network",
      "device_serials": ["XXXX-01", "XXXX-02", "XXXX-03", "XXXX-04", "XXXX-05"],
      "device_names": ["MS425-Core", "MS225-Acc1", "MS225-Acc2", "MS225-Acc3", "MS225-Acc4"]
    },
    "backup_state": {
      "captured_at": "2024-01-15T14:32:10Z",
      "data": { "rules": [{ "policy": "allow", "protocol": "any" }] }
    },
    "applied_state": {
      "applied_at": "2024-01-15T14:32:15Z",
      "data": { "rules": [
        { "policy": "deny", "protocol": "tcp", "dstPort": "23" },
        { "policy": "allow", "protocol": "any" }
      ]}
    },
    "verified_state": {
      "verified_at": "2024-01-15T14:32:17Z",
      "matches_expected": true,
      "data": { "rules": [
        { "policy": "deny", "protocol": "tcp", "dstPort": "23" },
        { "policy": "allow", "protocol": "any" }
      ]}
    },
    "result": {
      "status": "success",
      "api_responses": [
        { "endpoint": "/networks/L_789/switch/accessControlLists", "method": "PUT", "status_code": 200, "success": true, "error_message": null }
      ],
      "duration_ms": 2340
    },
    "context": {
      "user_confirmed": true,
      "catalyst_mode": "native_meraki",
      "sgt_check_passed": null,
      "handoff_from": null,
      "handoff_to": null,
      "session_id": "sess_abc123"
    },
    "rollback": {
      "available": true,
      "performed": false,
      "performed_at": null,
      "rollback_change_id": null
    },
    "human_readable": {
      "summary": "ACL 'block-telnet' criada em 5 switches (HQ-Network)",
      "details": "## 2024-01-15 14:32\n\n**Ação:** add_deny_rule\n**Status:** success\n..."
    }
  }
}
```
