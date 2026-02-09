# Issues Fixed - Bug Memory

> **Purpose:** Known bugs already diagnosed and fixed. Check HERE FIRST before debugging.
> **Rule:** Whenever user reports error/bug/troubleshooting, search this file before investigating.

---

## IF-001 | discover_networks 404 transiente

- **Symptom:** `APIError: organizations, getOrganizationNetworks - 404 Not Found` ao perguntar sobre networks/devices
- **Root Cause:** Meraki API retorna 404 esporadicos (eventual consistency). `discover_networks()` nao tinha retry proprio, falhava e mostrava erro antes de tentar `full_discovery()` que funcionava.
- **Fix:** Adicionado retry com exponential backoff (3 tentativas, 1s/2s wait) em `discover_networks()` para 404 transientes.
- **File:** `scripts/discovery.py:261-293`
- **Date:** 2026-02-09

---

## IF-002 | find_issues() crash em vpn_topology

- **Symptom:** `AttributeError: 'list' object has no attribute 'get'` no `test_full_discovery_integration`
- **Root Cause:** `configurations["vpn_topology"]` e uma lista, mas todos os loops em `find_issues()` fazem `configs.get(...)` assumindo dict. 10 loops afetados.
- **Fix:** Adicionado `if not isinstance(configs, dict): continue` em todos os 10 loops de `find_issues()`. Tambem guard no VPN check: `if isinstance(vpn_topology, dict)`.
- **File:** `scripts/discovery.py` (linhas 1176-1415)
- **Date:** 2026-02-09

---

## IF-003 | discover_firmware_status crash com mock

- **Symptom:** `AttributeError: 'list' object has no attribute 'get'` em `discover_firmware_status` debug log
- **Root Cause:** `safe_call` retorna `[]` quando mock generico e usado, mas funcao chama `result.get(...)` no debug log.
- **Fix:** Adicionado `if isinstance(result, dict):` antes do debug log.
- **File:** `scripts/discovery.py:668-670`
- **Date:** 2026-02-09

---

## IF-004 | safe_call mock retorna tipo errado

- **Symptom:** `test_full_discovery_integration` falhava porque `safe_call.return_value = []` retorna lista para funcoes que esperam dict
- **Root Cause:** Mock generico `return_value=[]` ignora o parametro `default` de `safe_call`. Funcoes com `default={}` recebiam `[]`.
- **Fix:** Trocado para `side_effect = lambda func, *args, default=None, **kwargs: default if default is not None else []` no test.
- **File:** `tests/test_discovery.py:661`
- **Date:** 2026-02-09

---

## IF-005 | FUNCTION_REGISTRY faltando wireless health entries

- **Symptom:** `test_tool_names_match_function_registry` falhava: `Tool get_wireless_connection_stats not in FUNCTION_REGISTRY`
- **Root Cause:** Epic 10 subagent adicionou tool schemas em `agent_tools.py` mas esqueceu de registrar 5 funcoes wireless health no `agent_router.py`.
- **Fix:** Adicionadas 5 lambdas: `get_wireless_connection_stats`, `get_wireless_latency_stats`, `get_wireless_signal_quality`, `get_channel_utilization`, `get_failed_connections`.
- **File:** `scripts/agent_router.py:290-294`
- **Date:** 2026-02-09

---

## IF-006 | Safety classification counts desatualizados

- **Symptom:** `test_all_classified_functions_exist` falhava: expected SAFE:36 got SAFE:51
- **Root Cause:** Epic 10 adicionou 26 novas entries em `SAFETY_CLASSIFICATION` mas o test tinha expected counts hardcoded do Epic 9.
- **Fix:** Atualizado expected counts para SAFE:51, MODERATE:22, DANGEROUS:15.
- **File:** `tests/test_safety.py:723-727`
- **Date:** 2026-02-09

---

## IF-007 | AIEngineError re-raise order

- **Symptom:** `classify()` em `ai_engine.py` engolia `AIEngineError` no except generico
- **Root Cause:** `except Exception` antes de `except AIEngineError` capturava o erro especifico primeiro.
- **Fix:** Movido `except AIEngineError` para antes de `except Exception` na chain.
- **File:** `scripts/ai_engine.py`
- **Date:** 2026-02-05

---

## IF-008 | update_vlan additionalProperties: True

- **Symptom:** `test_all_tool_schemas_valid` falhava
- **Root Cause:** Schema de `update_vlan` tinha `additionalProperties: True` em vez de `False`.
- **Fix:** Alterado para `False` no schema.
- **File:** `scripts/agent_tools.py`
- **Date:** 2026-02-07

---

## IF-009 | _get_task_registry() lazy reload em tests

- **Symptom:** Tests de task_registry falhavam apos `_tasks.clear()` porque lazy loader recarregava automaticamente
- **Root Cause:** `_get_task_registry()` detecta dict vazio e recarrega do disco. Limpar o dict nao funciona como mock.
- **Fix:** Usar `use_modular_tasks=False` (feature flag OFF) em vez de limpar o dict.
- **File:** `scripts/task_registry.py`, tests
- **Date:** 2026-02-07

---

## IF-010 | GitHub push 500/502 transiente

- **Symptom:** `git push` falhava com `500 Internal Server Error` ou `502 Bad Gateway`
- **Root Cause:** GitHub server-side issue temporario.
- **Fix:** Retry apos alguns segundos. Nao e bug do codigo.
- **Date:** 2026-02-09

---

## Quick Lookup by Error Message

| Error Fragment | Issue |
|---------------|-------|
| `404 Not Found` + `getOrganizationNetworks` | IF-001 |
| `'list' object has no attribute 'get'` + `find_issues` | IF-002 |
| `'list' object has no attribute 'get'` + `discover_firmware` | IF-003 |
| `not in FUNCTION_REGISTRY` | IF-005 |
| `Classification counts don't match` | IF-006 |
| `AIEngineError` swallowed | IF-007 |
| `additionalProperties` | IF-008 |
| `_get_task_registry` auto-reload | IF-009 |
| `500 Internal Server Error` + `git push` | IF-010 |
