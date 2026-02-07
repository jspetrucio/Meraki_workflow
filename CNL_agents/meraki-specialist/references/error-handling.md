# Reference: error-handling

## Propósito
Catálogo de erros da Meraki Dashboard API e ações corretivas.
Consultado pelo post-task hook (on_error) e pelo LLM para formatar mensagens claras.

---

## Erros por HTTP Status Code

### 400 — Bad Request

| Mensagem | Causa | Ação |
|----------|-------|------|
| `"Peer SGT capable is read-only"` | Porta com TrustSec/SGT peering do ISE | Executar `sgt_preflight_check()`. Usar porta writable ou ajustar ISE. |
| `"VLAN ID already exists"` | Tentativa de criar VLAN com ID já existente | GET VLAN existente, oferecer update ao invés de create. |
| `"Invalid port"` | Port ID fora do range do switch | Verificar modelo e range de portas válidas. |
| `"Invalid CIDR"` | Formato de CIDR inválido na regra | Validar formato (ex: 10.0.0.0/24, não 10.0.0.0/255.255.255.0). |
| `"PSK must be at least 8 characters"` | PSK muito curta para SSID | Gerar PSK com mínimo 8 chars (recomendar 12+). |
| `"SSID number out of range"` | SSID number > 14 | Máximo 15 SSIDs (0-14) por rede. Listar SSIDs em uso. |
| `"This network does not support VLANs"` | Rede não tem VLANs habilitadas | Habilitar VLANs na rede primeiro (requer appliance ou switch). |
| `"Cannot delete VLAN with devices"` | VLAN tem devices/ports atribuídos | Mover devices para outra VLAN antes de deletar. |
| `"Invalid protocol"` | Protocolo não reconhecido na regra | Usar: tcp, udp, icmp, any. |

### 401 — Unauthorized

| Mensagem | Causa | Ação |
|----------|-------|------|
| `"Invalid API key"` | API key inválida, expirada ou revogada | Verificar credenciais. Gerar nova key no Dashboard. |
| `"Missing API key"` | Header X-Cisco-Meraki-API-Key ausente | Verificar configuração do client HTTP. |

### 403 — Forbidden

| Mensagem | Causa | Ação |
|----------|-------|------|
| `"You don't have permission"` | API key sem permissão para esta org/network | Verificar permissões do admin no Dashboard. |
| `"Read-only admin"` | Admin é read-only, não pode fazer write | Solicitar permissão full admin. |
| `"This action is not available for your organization"` | Feature não disponível na licença | Verificar nível de licença da org. |

### 404 — Not Found

| Mensagem | Causa | Ação |
|----------|-------|------|
| `"Network not found"` | network_id inválido | Listar redes da org e verificar ID. |
| `"Device not found"` | Serial inválido ou device não está na rede | Verificar serial e network membership. |
| `"VLAN not found"` | VLAN ID não existe na rede | Listar VLANs existentes. |
| `"Resource not found"` | Endpoint não existe para este tipo de rede | Verificar se o tipo de recurso é válido para a rede. |

### 429 — Too Many Requests

| Mensagem | Causa | Ação |
|----------|-------|------|
| `"Rate limit exceeded"` | Mais de 10 req/s para a org | Respeitar header `Retry-After`. Aguardar e retry. |

**Tratamento:**
```python
if status == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    log.warning(f"Rate limit. Aguardando {retry_after}s...")
    await asyncio.sleep(retry_after)
    # Retry com backoff exponencial se persistir
```

### 500/502/503 — Server Error

| Causa | Ação |
|-------|------|
| Erro interno do servidor Meraki | Retry após 30s. Máximo 3 retries. |
| Gateway timeout | Retry após 60s. Se persistir, verificar status.meraki.com. |
| Service unavailable | Aguardar e retry. Pode ser manutenção. |

---

## Erros de Lógica (Não-HTTP)

### Conflito de Configuração

| Cenário | Detecção | Ação |
|---------|----------|------|
| ACL deny-all sem allow | Array de rules só tem deny | Alertar e pedir confirmação explícita |
| SSID open em rede corporativa | authMode=open em rede não-guest | Alertar risco e recomendar WPA2 |
| Port trunk em porta de acesso | Mudar para trunk pode derrubar endpoint | Alertar e confirmar |
| VPN PSK fraca | PSK < 20 chars | Alertar e sugerir geração automática |
| Firewall PUT sem default allow | Array não termina com allow all | Alertar que tráfego será implicitly denied |

### Timeout de Confirmação

| Cenário | Ação |
|---------|------|
| Usuário não responde em 5 min | Cancelar operação, informar que preview expirou |
| Usuário responde "não" | Perguntar o que ajustar, voltar ao parsing |
| Usuário responde "cancelar" | Cancelar completamente, nenhuma mudança |

---

## Mensagens de Erro Padronizadas

### Template de Erro para o Usuário
```
❌ ERRO: {resumo curto}

  Tipo: {status_code} - {status_text}
  Detalhe: {mensagem da API}
  Recurso: {endpoint simplificado}
  
  Causa provável: {explicação em linguagem natural}
  
  Ação recomendada:
  {lista de passos para resolver}
  
  Rollback: {necessário? disponível?}
```

### Exemplo
```
❌ ERRO: Porta protegida por SGT

  Tipo: 400 - Bad Request
  Detalhe: "Peer SGT capable is read-only"
  Recurso: Switch port 12 em MS425-Core
  
  Causa provável: Esta porta participa do TrustSec fabric via Cisco ISE.
  O Meraki Dashboard não pode modificar portas gerenciadas pelo ISE.
  
  Ação recomendada:
  1. Escolha uma porta diferente (portas writable: 1-8, 13-24)
  2. Ou modifique a política SGT diretamente no Cisco ISE
  3. Ou remova o TrustSec peering desta porta no ISE
  
  Rollback: Não necessário (nenhuma mudança foi aplicada)
```

---

## Prevenção de Erros (Pre-Checks)

| Check | Quando | O que verifica |
|-------|--------|----------------|
| CIDR validation | Antes de criar regra | Formato X.X.X.X/Y válido |
| Port range check | Antes de configurar porta | portId existe no modelo |
| VLAN ID uniqueness | Antes de criar VLAN | ID não está em uso |
| SSID slot available | Antes de criar SSID | Slot 0-14 disponível |
| PSK strength | Antes de criar SSID PSK | Mínimo 8 chars, recomendar 12+ |
| Catalyst mode | Antes de qualquer write em switch | Device aceita write? |
| SGT writeability | Antes de write em porta managed | Porta é writable? |
| License level | Antes de configurar Adaptive Policy | Tem Advanced? |
