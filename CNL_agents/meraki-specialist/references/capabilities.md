# Reference: capabilities

## Propósito
Matrix de capacidades por modelo/modo/licença.
Consultado pelo pre-task hook e pelo LLM para determinar o que é possível configurar.

---

## Catalyst vs MS — Capability Matrix

### Por Modelo e Modo

| Modelo | Meraki Mode | API Read | API Write | Dashboard Config | CLI Config | Firmware |
|--------|-------------|----------|-----------|------------------|-----------|----------|
| **MS120** | native | ✅ Full | ✅ Full | ✅ Full | ❌ | Meraki |
| **MS210** | native | ✅ Full | ✅ Full | ✅ Full | ❌ | Meraki |
| **MS225** | native | ✅ Full | ✅ Full | ✅ Full | ❌ | Meraki |
| **MS250** | native | ✅ Full | ✅ Full | ✅ Full | ❌ | Meraki |
| **MS350** | native | ✅ Full | ✅ Full | ✅ Full | ❌ | Meraki |
| **MS390** | native | ✅ Full | ✅ Full | ✅ Full | ✅ Limited | IOS-XE (managed) |
| **MS410** | native | ✅ Full | ✅ Full | ✅ Full | ❌ | Meraki |
| **MS425** | native | ✅ Full | ✅ Full | ✅ Full | ❌ | Meraki |
| **MS450** | native | ✅ Full | ✅ Full | ✅ Full | ❌ | Meraki |
| **C9300** | managed | ✅ Full | ✅ Full* | ✅ Full | ✅ Limited | CS (Cloud Services) |
| **C9300** | monitored | ✅ Full | ❌ Blocked | ❌ Read-only | ✅ Full | IOS-XE |
| **C9200** | monitored | ✅ Full | ❌ Blocked | ❌ Read-only | ✅ Full | IOS-XE |
| **C9400** | managed | ✅ Full | ✅ Full* | ✅ Full | ✅ Limited | CS (Cloud Services) |
| **C9400** | monitored | ✅ Full | ❌ Blocked | ❌ Read-only | ✅ Full | IOS-XE |
| **C9500** | monitored | ✅ Full | ❌ Blocked | ❌ Read-only | ✅ Full | IOS-XE |
| **C9600** | monitored | ✅ Full | ❌ Blocked | ❌ Read-only | ✅ Full | IOS-XE |

**\* Full com restrição:** Portas com SGT/TrustSec peering via ISE são read-only.

---

## Como Identificar o Modo

### Via API Response
```python
device = api.get_device(serial)

# Campos relevantes:
device['model']      # "MS225-48LP", "C9300-48P", "C9200-48T"
device['firmware']   # "switch-15-21-1", "CS17.9.4a", "17.9.4a"
device['productType'] # "switch", "appliance", "wireless", "camera"
```

### Regras de Detecção
```
Model starts with "MS"  → native_meraki
Model starts with "C93" AND firmware starts with "CS" → managed
Model starts with "C93" AND firmware does NOT start with "CS" → monitored
Model starts with "C92" → monitored (sempre)
Model starts with "C95" → monitored (sempre)
Model starts with "C96" → monitored (sempre)
Model starts with "C94" AND firmware starts with "CS" → managed
Model starts with "C94" AND firmware does NOT start with "CS" → monitored
```

---

## Licenciamento — Feature Matrix

### Meraki MS Licenses

| Feature | MS Enterprise | MS Advanced |
|---------|:------------:|:-----------:|
| VLANs | ✅ | ✅ |
| ACLs (L3) | ✅ | ✅ |
| QoS / CoS | ✅ | ✅ |
| Port Config | ✅ | ✅ |
| STP Settings | ✅ | ✅ |
| DHCP Server | ✅ | ✅ |
| Storm Control | ✅ | ✅ |
| Port Schedules | ✅ | ✅ |
| Adaptive Policy (SGT) | ❌ | ✅ |
| RADIUS CoA | ❌ | ✅ |
| Dynamic VLAN Assignment | ❌ | ✅ |
| Access Policy (802.1X advanced) | ❌ | ✅ |

### Catalyst Managed Licenses

| Feature | Essentials | Advantage | Premier |
|---------|:----------:|:---------:|:-------:|
| Basic Switching | ✅ | ✅ | ✅ |
| VLANs/ACLs/QoS | ✅ | ✅ | ✅ |
| Adaptive Policy (SGT) | ❌ | ✅ | ✅ |
| DNA Analytics | ❌ | ✅ | ✅ |
| SD-Access | ❌ | ❌ | ✅ |

---

## C9300 Managed Mode — Detalhes

O C9300 em managed mode é tratado pela API como se fosse um **MS390**.
Os endpoints são os mesmos. As diferenças são:

### O que funciona igual MS nativo
- Configuração de portas (type, vlan, name, tags, PoE)
- VLANs
- ACLs
- QoS rules
- STP
- DHCP

### O que é diferente
- **SGT/TrustSec:** Se ISE está integrado, portas com SGT peering ficam read-only
- **Stacking:** C9300 stack aparece como device único, portas numeradas sequencialmente
- **CLI access:** Ainda possível via console/SSH (diferente do MS nativo que não tem CLI)
- **Firmware:** Atualizações são CS (Cloud Services), não Meraki firmware

### O que NÃO funciona
- **Portas SGT-locked:** Retorna erro 400 "Peer SGT capable is read-only"
- **Features que requerem IOS-XE CLI:** Configurações avançadas não expostas na API Meraki
- **Netflow/SPAN avançado:** Configuração limitada via API

---

## SGT/TrustSec — Referência Rápida

### O que é SGT (Security Group Tag)
- Cisco TrustSec atribui tags (SGTs) a tráfego baseado em identidade
- ISE (Identity Services Engine) é o controlador de políticas
- Portas participando do TrustSec fabric têm peering com ISE
- Essas portas são gerenciadas pelo ISE, NÃO pelo Meraki Dashboard

### Por que portas ficam read-only
- Quando ISE atribui SGT a uma porta, o Meraki Dashboard respeita essa configuração
- A API retorna erro ao tentar modificar: `"Peer SGT capable is read-only"`
- Isso é BY DESIGN — não é bug, é proteção de política

### Como resolver
1. **Remover TrustSec da porta no ISE** → porta fica writable no Meraki
2. **Modificar política no ISE diretamente** → sem mudar via Meraki
3. **Usar porta diferente** → se há portas writable disponíveis

### Detecção via pre-task hook
```
sgt_preflight_check(serial) → retorna lista de portas writable vs read-only
```

---

## Rate Limits por Endpoint

| Categoria | Limite | Notas |
|-----------|--------|-------|
| Organização (geral) | 10 req/s | Shared entre todos os endpoints |
| Burst | 30 req/2s | Primeiros 2 segundos permitem burst |
| Action batches | 20 batch/s | Para operações batch |
| Config templates | 1 req/s | Mais restritivo |

### Implicação para batch operations
- Configurar 10 portas = 10 PUT calls = 10 segundos mínimo
- Configurar 50 switches = planejamento de rate limiting obrigatório
- Usar action batches quando possível para reduzir calls
