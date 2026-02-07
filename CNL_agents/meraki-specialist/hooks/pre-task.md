# Hook: pre-task

## Propósito
Roda ANTES de qualquer task do Meraki Specialist.
Garante que o ambiente é seguro para operar antes de qualquer mudança.

**OBRIGATÓRIO** — nenhuma task executa sem passar por este hook.

---

## Sequência de Execução

```
pre-task hook
├── 1. validate_credentials()
├── 2. resolve_org_and_network()
├── 3. detect_catalyst_mode(serial)    ← CRÍTICO para switches
├── 4. check_license(serial)           ← CRÍTICO para Adaptive Policy
├── 5. sgt_preflight_check(serial)     ← Condicional (só se managed)
├── 6. backup_current_state()
├── 7. check_rate_limit()
└── 8. inject_context()
```

---

## 1. validate_credentials()

```python
async def validate_credentials():
    """Verifica que API key é válida e tem permissão."""
    try:
        orgs = await api.get_organizations()
        if not orgs:
            raise AuthError("API key válida mas sem organizações acessíveis")
        return {"valid": True, "orgs": orgs}
    except 401:
        raise AuthError("API key inválida ou expirada. Verifique credenciais.")
    except 403:
        raise AuthError("API key sem permissão para esta organização.")
```

**Se falhar:** PARAR. Informar erro e como corrigir.

---

## 2. resolve_org_and_network()

```python
async def resolve_org_and_network(intent):
    """Resolve org_id e network_id a partir do contexto."""
    # Se sessão já tem org/network → usar
    # Se não → listar e perguntar ao usuário
    # Se só tem 1 org → usar automaticamente
    # Se múltiplas → perguntar
    
    org_id = session.org_id or await prompt_user_select_org()
    network_id = await resolve_network_from_intent(intent, org_id)
    
    return {"org_id": org_id, "network_id": network_id}
```

---

## 3. detect_catalyst_mode(serial) — CRÍTICO

```python
async def detect_catalyst_mode(serial: str) -> str:
    """
    Detecta se o device é Meraki nativo, Catalyst managed, ou Catalyst monitored.
    
    Returns:
        'native_meraki'  → MS series, operação normal, full API write
        'managed'        → C9300 no Meraki managed mode (= MS390 na API)
                           Full API write MAS precisa SGT preflight check
        'monitored'      → C9200/C9500 monitor-only mode
                           API write BLOQUEADO — só read
    """
    device = await api.get_device(serial)
    model = device.get('model', '')
    firmware = device.get('firmware', '')
    
    # Catalyst C9300 — pode ser managed ou monitored
    if model.startswith('C9300') or model.startswith('C93'):
        if firmware.startswith('CS'):  # Meraki managed firmware (Cloud Services)
            return 'managed'
        else:  # IOS-XE firmware
            return 'monitored'
    
    # Catalyst C9200 — sempre monitor-only no Meraki
    if model.startswith('C9200') or model.startswith('C92'):
        return 'monitored'
    
    # Catalyst C9500 — sempre monitor-only no Meraki
    if model.startswith('C9500') or model.startswith('C95'):
        return 'monitored'
    
    # Catalyst C9400 — verificar firmware
    if model.startswith('C9400') or model.startswith('C94'):
        if firmware.startswith('CS'):
            return 'managed'
        else:
            return 'monitored'
    
    # MS series (MS120, MS210, MS225, MS250, MS350, MS390, MS410, MS425, MS450)
    if model.startswith('MS'):
        return 'native_meraki'
    
    # Fallback — assume native se não reconhece
    # Log warning para investigação
    log.warning(f"Model não reconhecido: {model}. Assumindo native_meraki.")
    return 'native_meraki'
```

### Ações por Modo

| Modo | API Write | Ação |
|------|-----------|------|
| `native_meraki` | Full | Prosseguir normalmente |
| `managed` | Full + SGT check | Executar `sgt_preflight_check()` antes de qualquer write |
| `monitored` | BLOQUEADO | **PARAR** — informar que device é read-only |

### Mensagem para `monitored`:
```
⛔ DEVICE READ-ONLY

  Switch: {name} ({model})
  Serial: {serial}
  Firmware: {firmware}
  Modo: Monitored (IOS-XE)

  Este dispositivo está no modo monitor — visível no Dashboard Meraki
  mas NÃO configurável via API. As configurações são feitas via CLI
  ou Cisco DNA Center / Catalyst Center.

  Opções:
  1. Configurar via CLI/DNA Center (fora do escopo deste agente)
  2. Migrar para managed mode (requer re-flash de firmware)
  3. Escolher outro device que aceite configuração via API
```

---

## 4. check_license(serial)

```python
async def check_license(serial: str) -> dict:
    """
    Verifica nível de licença do device.
    Importante para features como Adaptive Policy (SGT) que requer Advanced.
    """
    device = await api.get_device(serial)
    license_info = await api.get_network_licenses(device['networkId'])
    
    # Determinar nível
    level = 'enterprise'  # default
    for lic in license_info:
        if 'advanced' in lic.get('licenseType', '').lower():
            level = 'advanced'
            break
    
    return {
        "serial": serial,
        "license_level": level,
        "adaptive_policy_available": level == 'advanced',
        "features_restricted": get_restricted_features(level)
    }
```

### Features por Licença

| Feature | Enterprise | Advanced |
|---------|-----------|----------|
| VLANs | ✅ | ✅ |
| ACLs | ✅ | ✅ |
| QoS | ✅ | ✅ |
| Port Config | ✅ | ✅ |
| Adaptive Policy (SGT) | ❌ | ✅ |
| RADIUS CoA | ❌ | ✅ |
| Dynamic VLAN | ❌ | ✅ |

### Se Adaptive Policy é solicitado mas licença é Enterprise:
```
⚠️ FEATURE NÃO DISPONÍVEL

  Adaptive Policy (SGT) requer licença Advanced.
  Licença atual: Enterprise

  Opções:
  1. Upgrade de licença para Advanced
  2. Usar ACL tradicional (sem SGT) como alternativa
```

---

## 5. sgt_preflight_check(serial) — Condicional

**Só executa se `detect_catalyst_mode()` retornou `managed`.**

```python
async def sgt_preflight_check(serial: str) -> dict:
    """
    Testa writeability de cada porta do switch.
    Portas com SGT/TrustSec peering do ISE são read-only.
    """
    ports = await api.get_device_switch_ports(serial)
    
    writable = []
    read_only = []
    
    for port in ports:
        try:
            # Tentar atualizar descrição (operação não-destrutiva)
            test_payload = {"name": port.get('name', '')}
            await api.update_device_switch_port(serial, port['portId'], test_payload)
            writable.append(port['portId'])
        except APIError as e:
            if 'Peer SGT capable is read-only' in str(e):
                read_only.append({
                    'portId': port['portId'],
                    'name': port.get('name', ''),
                    'reason': 'SGT/TrustSec peering'
                })
            else:
                raise  # Erro inesperado — propagar
    
    total = len(ports)
    writable_count = len(writable)
    ro_count = len(read_only)
    
    result = {
        "serial": serial,
        "total_ports": total,
        "writable_ports": writable,
        "writable_count": writable_count,
        "read_only_ports": read_only,
        "read_only_count": ro_count,
        "has_sgt_restriction": ro_count > 0,
        "fully_locked": writable_count == 0,
        "ratio_writable": f"{(writable_count/total*100):.0f}%" if total > 0 else "N/A"
    }
    
    return result
```

### Alerta ao Usuário (se SGT detectado):
```
⚠️ SWITCH COM RESTRIÇÃO TrustSec/SGT

  Switch: {name} ({model})
  Total de portas: {total}
  Portas configuráveis (writable): {writable_count} ({ratio}%)
  Portas bloqueadas (SGT locked): {ro_count}

  Portas writable: {writable list}
  Portas read-only: {read_only list}

  Causa: Cisco ISE TrustSec Security Group Tags
  Resolução: Modificar política SGT no ISE ou remover TrustSec das portas afetadas
```

### Se `fully_locked` (todas as portas SGT):
```
⛔ SWITCH TOTALMENTE BLOQUEADO

  TODAS as portas deste switch são read-only (SGT/TrustSec).
  Não é possível configurar NENHUMA porta via API.

  Ação necessária: Ajustar política no Cisco ISE antes de continuar.
```
**→ PARAR task. Não prosseguir.**

---

## 6. backup_current_state()

```python
async def backup_current_state(operation, targets):
    """
    Salva estado atual do recurso que será modificado.
    Usado para rollback e para change-log.
    """
    backup = {
        "captured_at": datetime.utcnow().isoformat(),
        "operation": operation,
        "data": {}
    }
    
    # Backup específico por tipo de operação
    if operation.resource == 'acl':
        backup['data'] = await api.get_network_switch_acls(targets.network_id)
    elif operation.resource == 'ssid':
        backup['data'] = await api.get_network_ssid(targets.network_id, targets.ssid_number)
    elif operation.resource == 'firewall_l3':
        backup['data'] = await api.get_network_l3_firewall_rules(targets.network_id)
    elif operation.resource == 'vlan':
        backup['data'] = await api.get_network_vlan(targets.network_id, targets.vlan_id)
    elif operation.resource == 'port':
        for serial in targets.device_serials:
            backup['data'][serial] = await api.get_device_switch_port(serial, targets.port_id)
    # ... etc para cada resource type
    
    return backup
```

**Se backup falhar:** PARAR. Informar que não é seguro prosseguir sem backup.

---

## 7. check_rate_limit()

```python
async def check_rate_limit():
    """Verifica se estamos perto do rate limit."""
    # Meraki rate limit: 10 req/s por org
    # Burst: 30 req nos primeiros 2 segundos
    
    current_rate = session.get_request_rate()
    
    if current_rate > 8:  # 80% do limite
        log.warning(f"Rate limit alto: {current_rate}/10 req/s")
        await asyncio.sleep(1)  # Cooldown preventivo
    
    return {"rate": current_rate, "limit": 10, "safe": current_rate <= 8}
```

---

## 8. inject_context()

```python
async def inject_context(task, catalyst_info, license_info, sgt_info, backup):
    """
    Injeta contexto coletado pelos hooks no change-request.
    O task_executor usa esse contexto para decisões durante a task.
    """
    context = {
        "catalyst_mode": catalyst_info.mode,
        "sgt_restricted": sgt_info.has_sgt_restriction if sgt_info else False,
        "writable_ports": sgt_info.writable_ports if sgt_info else [],
        "license_level": license_info.license_level,
        "backup_id": backup.captured_at,
        "rate_safe": True
    }
    
    task.change_request.context = context
    return task
```

---

## Resumo: Quando Cada Check Roda

| Check | Sempre | Só Switches | Só Managed | Só Write |
|-------|--------|-------------|------------|----------|
| validate_credentials | ✅ | | | |
| resolve_org_network | ✅ | | | |
| detect_catalyst_mode | | ✅ | | |
| check_license | | ✅ | | |
| sgt_preflight_check | | | ✅ | |
| backup_current_state | | | | ✅ |
| check_rate_limit | ✅ | | | |
| inject_context | ✅ | | | |
