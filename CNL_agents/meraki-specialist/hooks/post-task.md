# Hook: post-task

## Propósito
Roda DEPOIS de qualquer task do Meraki Specialist.
Garante registro, notificação e encaminhamento adequados.

---

## Sequência de Execução

```
post-task hook
├── 1. write_audit_log()
├── 2. write_changelog()
├── 3. process_handoffs()
├── 4. update_session()
└── 5. on_error()          ← só se task falhou
```

---

## 1. write_audit_log()

```python
async def write_audit_log(change_log_entry):
    """
    Registra a mudança no audit trail permanente.
    Formato: change-log schema (ver schemas/change-log.schema.md)
    """
    log_entry = {
        "change_id": change_log_entry.change_id,
        "timestamp": datetime.utcnow().isoformat(),
        "task": change_log_entry.task,
        "operation": change_log_entry.operation,
        "targets": change_log_entry.targets,
        "result": change_log_entry.result,
        "user_confirmed": change_log_entry.context.user_confirmed,
        "session_id": session.id
    }
    
    # Persistir no session store
    session.audit_log.append(log_entry)
    
    # Se arquivo de log existe, append
    if session.log_file:
        await append_to_file(session.log_file, log_entry)
    
    return log_entry
```

---

## 2. write_changelog()

```python
async def write_changelog(change_log_entry):
    """
    Gera changelog legível para o usuário.
    Usa change-log.human_readable template.
    """
    changelog_md = f"""
## {change_log_entry.timestamp}

**Ação:** {change_log_entry.operation.action}
**Status:** {change_log_entry.result.status}
**Device(s):** {', '.join(change_log_entry.targets.device_names)}
**Rede:** {change_log_entry.targets.network_name}

### Mudanças
- [antes] {summarize(change_log_entry.backup_state)}
- [depois] {summarize(change_log_entry.applied_state)}

### Rollback
- Disponível: {change_log_entry.rollback.available}
- ID: `{change_log_entry.change_id}`
"""
    
    session.changelog.append(changelog_md)
    return changelog_md
```

---

## 3. process_handoffs()

```python
async def process_handoffs(change_log_entry, task_result):
    """
    Verifica se a mudança aplicada requer ação de outro agente.
    """
    handoff_needed = False
    handoff_target = None
    handoff_reason = None
    
    # Caso 1: Mudança aplicada → precisa validação do Analyst
    if task_result.needs_validation:
        handoff_needed = True
        handoff_target = "network-analyst"
        handoff_reason = "post-change-validation"
    
    # Caso 2: Mudança parcial → precisa troubleshooting
    if change_log_entry.result.status == "partial_success":
        handoff_needed = True
        handoff_target = "network-analyst"
        handoff_reason = "partial-failure-investigation"
    
    # Caso 3: Task gerou necessidade de workflow
    if task_result.workflow_needed:
        handoff_needed = True
        handoff_target = "workflow-creator"
        handoff_reason = "automation-opportunity"
    
    if handoff_needed:
        handoff = {
            "from": "meraki-specialist",
            "to": handoff_target,
            "reason": handoff_reason,
            "change_id": change_log_entry.change_id,
            "context": {
                "operation": change_log_entry.operation,
                "targets": change_log_entry.targets,
                "result": change_log_entry.result
            }
        }
        session.pending_handoffs.append(handoff)
        
        # Informar usuário
        print(f"💡 Sugestão: {handoff_reason_to_message(handoff_reason)}")
    
    return handoff_needed
```

### Mensagens de Handoff

| Reason | Mensagem |
|--------|----------|
| post-change-validation | "Mudança aplicada. Quer que o Network Analyst faça um health-check para confirmar?" |
| partial-failure-investigation | "Algumas operações falharam. Recomendo que o Network Analyst investigue." |
| automation-opportunity | "Esta configuração pode ser automatizada. Quer que o Workflow Creator crie um workflow?" |

---

## 4. update_session()

```python
async def update_session(change_log_entry):
    """
    Atualiza o estado da sessão com a mudança realizada.
    """
    session.changes_count += 1
    session.last_change_id = change_log_entry.change_id
    session.last_change_timestamp = change_log_entry.timestamp
    
    # Track targets modificados (para evitar conflitos)
    for serial in change_log_entry.targets.device_serials:
        session.modified_devices.add(serial)
    
    # Track resources modificados
    session.modified_resources.append({
        "resource": change_log_entry.operation.resource,
        "network_id": change_log_entry.targets.network_id,
        "timestamp": change_log_entry.timestamp
    })
    
    # Se muitas mudanças na sessão, sugerir review
    if session.changes_count >= 5:
        print("📊 Já foram 5 mudanças nesta sessão. Quer um resumo antes de continuar?")
```

---

## 5. on_error() — Só se task falhou

```python
async def on_error(error, change_request, backup_state):
    """
    Tratamento de erro quando task falha durante execução.
    """
    error_type = classify_error(error)
    
    if error_type == "rate_limit":  # 429
        retry_after = error.headers.get('Retry-After', 60)
        print(f"⏳ Rate limit atingido. Aguardando {retry_after}s...")
        await asyncio.sleep(int(retry_after))
        return {"action": "retry", "wait": retry_after}
    
    elif error_type == "sgt_readonly":  # 400 - SGT
        print("⛔ Porta protegida por TrustSec/SGT. Não é possível modificar via API.")
        print("Consulte hooks/pre-task.md para detalhes sobre SGT detection.")
        return {"action": "abort", "reason": "sgt_readonly"}
    
    elif error_type == "not_found":  # 404
        print(f"❌ Recurso não encontrado: {error.message}")
        print("Verifique se org_id, network_id e serial estão corretos.")
        return {"action": "abort", "reason": "not_found"}
    
    elif error_type == "auth":  # 401/403
        print("🔑 Erro de autenticação. API key pode ter expirado.")
        return {"action": "abort", "reason": "auth_failure"}
    
    elif error_type == "server_error":  # 5xx
        print("🔧 Erro no servidor Meraki. Tentando novamente em 30s...")
        await asyncio.sleep(30)
        return {"action": "retry", "wait": 30, "max_retries": 3}
    
    elif error_type == "partial_apply":
        # Mudança aplicou parcialmente — tentar rollback
        print("⚠️ Mudança aplicou parcialmente. Tentando rollback automático...")
        try:
            await rollback_to_state(backup_state)
            print("✅ Rollback automático realizado com sucesso.")
            return {"action": "rolled_back"}
        except Exception:
            print("❌ Rollback automático falhou. Estado pode estar inconsistente.")
            print(f"Backup salvo em: change_id={change_request.id}")
            print("Use 'rollback --change-id=...' para reverter manualmente.")
            return {"action": "abort", "reason": "partial_apply_rollback_failed"}
    
    else:
        print(f"❌ Erro inesperado: {error}")
        return {"action": "abort", "reason": "unknown"}
```

### Retry Policy

| Erro | Retry | Max Retries | Wait |
|------|-------|-------------|------|
| 429 Rate Limit | Sim | 5 | Retry-After header |
| 5xx Server Error | Sim | 3 | 30s |
| Timeout | Sim | 2 | 10s |
| 400 Bad Request | Não | — | — |
| 401/403 Auth | Não | — | — |
| 404 Not Found | Não | — | — |

---

## Diagrama Completo

```
Task executa
    ↓
┌─ SUCESSO ──────────────────────┐
│ write_audit_log()              │
│ write_changelog()              │
│ process_handoffs()             │
│ update_session()               │
│ → Informar usuário "Concluído" │
└────────────────────────────────┘

┌─ FALHA ────────────────────────┐
│ on_error()                     │
│   ├─ retry? → re-executar step │
│   ├─ rollback? → restaurar     │
│   └─ abort? → informar erro    │
│ write_audit_log() (com falha)  │
│ update_session()               │
└────────────────────────────────┘
```
