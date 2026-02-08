# Task: configure-switching

## Metadata

- **ID:** T2
- **Trigger:** VLAN, ACL, switch port, QoS, CoS, STP, DHCP, storm control, port schedule, trunk, access port, PoE
- **Scope:** MS (Switches) + Catalyst C9300 managed mode
- **Risk:** HIGH (mudança em VLAN/ACL pode causar perda de conectividade)
- **Pre-task obrigatório:** `detect_catalyst_mode` + SGT preflight (ver `hooks/pre-task.md`)

---

## Steps

### Step 1 — Parse Intent
- **Type:** agent
- **Input:** mensagem do usuário ou handoff
- **Output:** `change-request` schema preenchido
- **LLM Action:** Interpretar e mapear para operação(ões) API
- **Exemplos de intent:**
  - "Cria VLAN 100 para IoT" → create VLAN
  - "Bloqueia porta 23 em todos os switches" → create/update ACL
  - "Configura porta 5 como trunk" → update switch port
  - "Habilita QoS para VoIP" → update QoS rules
  - "Muda porta 12 para VLAN 200" → update switch port

### Step 2 — Resolve Targets + Catalyst Detection
- **Type:** tool
- **Tools:** `get_devices`, `get_device`, `get_device_switch_ports`
- **Action:**
  1. Identificar switches afetados (serial, model, name)
  2. **EXECUTAR `detect_catalyst_mode(serial)`** para cada switch
  3. Se `monitored` → PARAR, informar "Device read-only, não configurável via API"
  4. Se `managed` → ativar SGT preflight check
  5. Se `native_meraki` → prosseguir normalmente
- **Validation:**
  - Switch existe na rede?
  - Porta existe no switch? (verificar range do modelo)
  - VLAN ID válido? (1-4094, exceto reservadas)

### Step 2b — SGT Preflight (Condicional)
- **Type:** tool
- **Condition:** Só roda se detect_catalyst_mode retornou `managed`
- **Tools:** `get_device_switch_ports` (todas as portas)
- **Action:** Testar writeability de cada porta alvo
- **Output:** Lista de portas writable vs read-only (SGT locked)
- **Se porta alvo é read-only:**

```text
⚠️ ALERTA: Porta {port_id} no switch {name} ({model}) está protegida por TrustSec/SGT.

  Status: READ-ONLY via API
  Causa: Cisco ISE Security Group Tag peering
  Ação: Modificar política SGT no ISE ou escolher porta diferente

  Portas disponíveis (writable): {lista}
```

### Step 3 — Generate Preview
- **Type:** agent
- **Input:** estado atual + mudança desejada + catalyst mode info
- **Output:** `change-preview` schema
- **Incluir no preview:**
  - Device model e mode (MS nativo / C9300 managed)
  - Estado antes vs depois
  - Número de devices/portas afetados
  - Warnings de SGT se aplicável

### Step 4 — Confirmation Gate
- **Type:** gate
- **Action:** Aguardar confirmação explícita
- **Nível de confirmação por risco:**
  - VLAN create → confirmação simples
  - ACL deny rule → confirmação + resumo do impacto
  - Port trunk/access change → confirmação + aviso de possível drop
  - Batch (>5 switches) → confirmação + contagem explícita

### Step 5 — Apply Changes
- **Type:** tool
- **Tools:** varia por operação (ver tabela abaixo)
- **Sequence por tipo:**

**VLAN:**
  1. Criar VLAN (`POST /networks/{id}/vlans`)
  2. Configurar subnet/gateway
  3. Configurar DHCP (se solicitado)

**ACL:**
  1. GET ACLs atuais
  2. Append/replace regras
  3. PUT ACLs atualizadas
  4. **SEMPRE incluir allow-all como última regra** (implicit deny é perigoso)

**Switch Port:**
  1. GET estado atual da porta
  2. PUT com mudanças (type, vlan, name, etc)
  3. Se batch → loop com rate limit (1 req/s para ports)

**QoS:**
  1. GET QoS rules atuais
  2. PUT com novas regras
  3. Verificar se CoS mapping está correto

### Step 6 — Verify
- **Type:** tool
- **Action:** GET recurso configurado e comparar
- **Para ACLs:** GET e validar que todas as regras estão na ordem correta
- **Para portas:** GET e validar type, vlan, name
- **Para VLANs:** GET e validar subnet, gateway, DHCP

---

## Operações API Cobertas

| Operação | Endpoint | Método |
|----------|----------|--------|
| Listar VLANs | `/networks/{id}/vlans` | GET |
| Criar VLAN | `/networks/{id}/vlans` | POST |
| Atualizar VLAN | `/networks/{id}/vlans/{vlanId}` | PUT |
| Deletar VLAN | `/networks/{id}/vlans/{vlanId}` | DELETE |
| Listar ACLs | `/networks/{id}/switch/accessControlLists` | GET |
| Atualizar ACLs | `/networks/{id}/switch/accessControlLists` | PUT |
| Listar ports | `/devices/{serial}/switch/ports` | GET |
| Atualizar port | `/devices/{serial}/switch/ports/{portId}` | PUT |
| QoS rules | `/networks/{id}/switch/qosRules` | GET/POST/PUT |
| QoS order | `/networks/{id}/switch/qosRules/order` | PUT |
| DHCP server | `/devices/{serial}/switch/routing/interfaces/{id}/dhcp` | PUT |
| STP settings | `/networks/{id}/switch/stp` | GET/PUT |
| Storm control | `/networks/{id}/switch/stormControl` | GET/PUT |
| Port schedules | `/networks/{id}/switch/portSchedules` | GET/POST |

---

## Regras de Segurança

1. **ACL sem allow-all final:** NUNCA criar ACL que não termine com allow-all (a menos que
   o usuário EXPLICITAMENTE peça implicit deny e confirme o risco)
2. **VLAN 1:** Alertar se tentarem configurar na VLAN 1 — "VLAN 1 é default, recomendo VLAN dedicada"
3. **Trunk port:** Alertar se porta for uplink — "Esta porta parece ser uplink, tem certeza?"
4. **Batch > 10 devices:** Alertar impacto e sugerir rollout gradual
5. **Port shutdown:** Confirmação dupla — "Desabilitar porta pode derrubar dispositivo conectado"
6. **SGT locked port:** NUNCA tentar write em porta SGT — falha silenciosa é pior que erro explícito
