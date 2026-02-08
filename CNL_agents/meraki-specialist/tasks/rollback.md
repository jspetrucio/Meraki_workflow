# Task: rollback

## Metadata
- **ID:** T5
- **Trigger:** rollback, reverter, desfazer, undo, voltar atrás, restaurar, "deu errado", "não funcionou"
- **Scope:** Qualquer mudança feita por este agente (rastreada via change-log)
- **Risk:** MODERATE-HIGH (rollback pode também causar disrupção se estado original era problemático)

---

## Steps

### Step 1 — Identify Change
- **Type:** agent
- **Input:** mensagem do usuário + session changelog
- **Output:** change-log entry a ser revertida
- **LLM Action:**
  - Se usuário especifica: "reverte a ACL que acabei de criar" → buscar no changelog
  - Se genérico: "reverte a última mudança" → pegar último entry
  - Se ambíguo: listar últimas mudanças e perguntar qual reverter
- **Mostrar:**
```text
Encontrei estas mudanças recentes:

  1. [14:32] ACL "block-telnet" criada em 5 switches
  2. [14:28] SSID "Guest-WiFi" habilitado na rede SP
  3. [14:15] VLAN 100 criada na rede HQ

Qual mudança quer reverter?
```

### Step 2 — Load Backup State
- **Type:** tool
- **Action:** Carregar o estado backup salvo pelo pre-task hook
- **Source:** `change-log.backup_state` do entry selecionado
- **Validation:**
  - Backup existe? (se não → informar que rollback manual será necessário)
  - Backup é do mesmo device/network? (sanity check)
  - Tempo desde o backup (se > 1h, alertar que estado pode ter mudado)

### Step 3 — Generate Rollback Preview
- **Type:** agent
- **Output:** `change-preview` schema (inverso)
- **Format:**
```text
Vou reverter a seguinte mudança:

  Mudança original: ACL "block-telnet" criada em 5 switches
  Timestamp: 2024-01-15 14:32
  
  [atual]  ACL contém regra: DENY TCP any → any:23
  [depois] ACL será removida / estado anterior restaurado

  Devices afetados: 5 switches

Confirma rollback? (sim/não)
```

### Step 4 — Confirmation Gate
- **Type:** gate
- **Nível:** Confirmação obrigatória + resumo do que será revertido
- **Se mudança afeta > 5 devices:** Confirmação dupla

### Step 5 — Apply Rollback
- **Type:** tool
- **Action:** PUT o estado backup de volta
- **Strategy por tipo:**
  - **SSID criado:** PUT com enabled=false + nome original (não deleta, desabilita)
  - **VLAN criada:** DELETE VLAN (se não tem devices atribuídos)
  - **ACL rules adicionadas:** PUT array original (sem as regras novas)
  - **Firewall rules:** PUT array original completo
  - **Port config:** PUT config original da porta
  - **NAT/VPN:** PUT config original
- **Rate limit:** Respeitar 1 req/s para batch rollback

### Step 6 — Verify Rollback
- **Type:** tool
- **Action:** GET recurso e comparar com estado backup
- **Se sucesso:** "Rollback concluído. Estado restaurado para {timestamp}."
- **Se falha parcial:** Listar o que reverteu e o que falhou

---

## Change-Log Lookup

O rollback depende do change-log mantido pelo post-task hook.
Cada entry contém:

```json
{
  "change_id": "CHG-20240115-143200",
  "timestamp": "2024-01-15T14:32:00Z",
  "task": "configure-switching",
  "operation": "create_acl",
  "targets": ["XXXX-XXXX-XXXX", ...],
  "backup_state": { ... },     // Estado ANTES da mudança
  "applied_state": { ... },     // Estado DEPOIS da mudança
  "user_confirmed": true,
  "rollback_available": true
}
```

---

## Limitações

1. **Mudanças fora do agente:** Se alguém mudou via Dashboard/API depois, o backup pode conflitar
2. **Delete de VLAN com devices:** Não pode deletar VLAN se devices estão atribuídos
3. **VPN tunnel:** Rollback do lado local não afeta o peer remoto
4. **Firmware:** NÃO tem rollback de firmware via API — informar que é processo manual
5. **Sem backup:** Se pre-task hook falhou em salvar backup, rollback não é possível via estado salvo — sugerir recriação manual
