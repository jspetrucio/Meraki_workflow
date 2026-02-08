# Schema: change-request

## Propósito
Estrutura padronizada para representar qualquer requisição de mudança.
Gerado no Step 1 (Parse Intent) de qualquer task.

---

## Schema

```json
{
  "change_request": {
    "id": "REQ-{timestamp}",
    "source": "user | handoff",
    "timestamp": "ISO-8601",
    
    "intent": {
      "raw": "string — mensagem original do usuário",
      "parsed": "string — interpretação do LLM",
      "category": "wireless | switching | security | monitoring | rollback | specific",
      "task_id": "T1 | T2 | T3 | T4 | T5 | T6"
    },
    
    "operation": {
      "type": "create | update | delete | rollback",
      "resource": "ssid | vlan | acl | firewall_l3 | firewall_l7 | nat | vpn | port | qos | alert | snmp | syslog | camera | tag | firmware",
      "action": "string — ação específica (ex: 'create_acl', 'update_ssid_psk')"
    },
    
    "targets": {
      "organization_id": "string",
      "network_id": "string",
      "device_serials": ["string"],
      "specific_ids": {
        "ssid_number": "0-14 | null",
        "vlan_id": "1-4094 | null",
        "port_id": "string | null",
        "rule_index": "integer | null"
      }
    },
    
    "parameters": {
      "// campos variam por operação — exemplos:",
      "name": "string",
      "enabled": "boolean",
      "policy": "allow | deny",
      "protocol": "tcp | udp | icmp | any",
      "src_cidr": "CIDR | any",
      "dst_cidr": "CIDR | any",
      "dst_port": "string | any",
      "comment": "string"
    },
    
    "context": {
      "catalyst_mode": "native_meraki | managed | monitored | null",
      "sgt_restricted": "boolean",
      "writable_ports": ["string"],
      "license_level": "enterprise | advanced | null",
      "handoff_from": "network-analyst | null",
      "handoff_issue_id": "string | null"
    },
    
    "risk_level": "low | moderate | high | critical",
    "requires_confirmation": "boolean — sempre true para write operations"
  }
}
```

---

## Regras de Preenchimento

1. **id:** Gerado automaticamente — `REQ-{YYYYMMDD}-{HHMMSS}`
2. **source:** "user" se veio do chat, "handoff" se recebido de outro agente
3. **intent.raw:** Copiar mensagem do usuário exatamente como veio
4. **intent.parsed:** Interpretação limpa do LLM — sem ambiguidade
5. **targets:** Resolver no Step 2, pode estar parcial após Step 1
6. **context.catalyst_mode:** Preenchido pelo pre-task hook
7. **risk_level:** Classificado automaticamente:
   - `low` → read-only, tags, monitoring
   - `moderate` → SSID, VLAN create, alerts
   - `high` → ACL, port config, NAT
   - `critical` → firewall deny rules, VPN, batch operations

---

## Exemplo Preenchido

```json
{
  "change_request": {
    "id": "REQ-20240115-143200",
    "source": "user",
    "timestamp": "2024-01-15T14:32:00Z",
    "intent": {
      "raw": "Bloqueia telnet em todos os switches",
      "parsed": "Criar ACL deny TCP port 23 em todos os switches da rede",
      "category": "switching",
      "task_id": "T2"
    },
    "operation": {
      "type": "update",
      "resource": "acl",
      "action": "add_deny_rule"
    },
    "targets": {
      "organization_id": "123456",
      "network_id": "L_789",
      "device_serials": ["XXXX-XXXX-XX01", "XXXX-XXXX-XX02"],
      "specific_ids": { "rule_index": null }
    },
    "parameters": {
      "policy": "deny",
      "protocol": "tcp",
      "src_cidr": "any",
      "dst_cidr": "any",
      "dst_port": "23",
      "comment": "Block Telnet - insecure protocol"
    },
    "context": {
      "catalyst_mode": "native_meraki",
      "sgt_restricted": false,
      "writable_ports": [],
      "license_level": null,
      "handoff_from": null,
      "handoff_issue_id": null
    },
    "risk_level": "high",
    "requires_confirmation": true
  }
}
```
