# Task: configure-security

## Metadata
- **ID:** T3
- **Trigger:** firewall, regra, NAT, port forwarding, VPN, site-to-site, client VPN, content filter, threat protection, IPS, IDS, malware, L3, L7, traffic shaping
- **Scope:** MX (Security Appliance) + regras de firewall em nível de rede
- **Risk:** CRITICAL (mudança em firewall pode bloquear tráfego legítimo)
- **Nota:** Mudanças de firewall aplicam imediatamente — NÃO há commit/rollback nativo

---

## Steps

### Step 1 — Parse Intent
- **Type:** agent
- **Input:** mensagem do usuário ou handoff
- **Output:** `change-request` schema preenchido
- **LLM Action:** Interpretar e classificar tipo de operação de segurança
- **Exemplos de intent:**
  - "Bloqueia telnet em toda a rede" → L3 firewall rule deny TCP:23
  - "Libera acesso da VLAN 100 para o servidor 10.0.1.5" → L3 rule allow
  - "Bloqueia Facebook e YouTube" → L7 firewall rule
  - "Configura NAT 1:1 para o servidor web" → 1:1 NAT mapping
  - "Cria VPN site-to-site com a filial" → S2S VPN config
  - "Habilita traffic shaping para VoIP" → shaping rule
  - "Configura port forwarding da porta 443 para 10.0.1.10" → port forwarding

### Step 2 — Resolve Targets
- **Type:** tool
- **Tools:** `get_networks`, `get_network_appliance_firewall_l3_rules`, `get_network_appliance_vlans`
- **Action:**
  1. Identificar network_id e MX appliance
  2. GET regras atuais (para posicionamento correto)
  3. Validar CIDRs, portas, protocolos mencionados
- **Validation:**
  - Network tem MX appliance?
  - CIDRs são válidos? (não aceitar "any" sem confirmar)
  - Porta é numérica e no range válido?
  - Protocolo é válido? (tcp, udp, icmp, any)

### Step 3 — Generate Preview
- **Type:** agent
- **Input:** regras atuais + nova regra + posição
- **Output:** `change-preview` schema
- **CRÍTICO — Mostrar contexto completo:**
```text
Regras L3 atuais (MX-HQ):
  1. ALLOW TCP 10.0.0.0/8 → any:443     [HTTPS interno]
  2. ALLOW UDP any → any:53              [DNS]
  3. DENY  TCP any → any:23              [Telnet blocked] ← NOVA
  4. ALLOW any any → any                 [Default allow]

Nova regra será inserida na posição 3.
A regra default allow (posição 4) continua ativa.

Impacto: Todo tráfego Telnet (TCP:23) será bloqueado em toda a rede.
Dispositivos afetados: ~150 endpoints na rede HQ.

Confirma? (sim/não)
```
- **SEMPRE mostrar a regra no contexto das demais** — nunca mostrar isolada

### Step 4 — Confirmation Gate
- **Type:** gate
- **Nível de confirmação:**
  - Allow rule → confirmação simples
  - Deny rule → confirmação + resumo do impacto + aviso "aplica imediatamente"
  - Deny all/broad CIDR → confirmação DUPLA + countdown de impacto
  - NAT/VPN → confirmação + teste sugerido

### Step 5 — Apply Changes
- **Type:** tool
- **IMPORTANTE:** Firewall rules no Meraki são substituição completa (PUT), não append.
  Sempre GET all rules → inserir nova na posição correta → PUT all rules.
- **Sequence por tipo:**

**Firewall L3:**
  1. GET todas as regras atuais
  2. Inserir nova regra na posição correta (antes do default allow)
  3. PUT o array completo de regras
  4. **NUNCA remover o default allow sem confirmação explícita**

**Firewall L7:**
  1. GET L7 rules atuais
  2. Append nova regra (L7 é por aplicação/categoria)
  3. PUT regras atualizadas

**NAT 1:1:**
  1. GET 1:1 NAT rules
  2. Append nova mapping
  3. PUT rules atualizadas

**Port Forwarding:**
  1. GET port forwarding rules
  2. Append nova regra
  3. PUT rules atualizadas

**VPN Site-to-Site:**
  1. GET VPN config atual
  2. Adicionar novo peer
  3. PUT config atualizada
  4. **Informar que o peer remoto também precisa configurar**

**Traffic Shaping:**
  1. GET shaping rules
  2. Adicionar/modificar regra
  3. PUT rules atualizadas

### Step 6 — Verify
- **Type:** tool
- **Action:** GET regras e confirmar posição e conteúdo
- **Para firewall:** Verificar que regra está na posição esperada
- **Para NAT:** Verificar mapping está ativo
- **Para VPN:** Verificar status do túnel (pode levar 30-60s para estabelecer)

---

## Operações API Cobertas

| Operação | Endpoint | Método |
|----------|----------|--------|
| L3 Firewall rules | `/networks/{id}/appliance/firewall/l3FirewallRules` | GET/PUT |
| L7 Firewall rules | `/networks/{id}/appliance/firewall/l7FirewallRules` | GET/PUT |
| 1:1 NAT | `/networks/{id}/appliance/firewall/oneToOneNatRules` | GET/PUT |
| 1:Many NAT | `/networks/{id}/appliance/firewall/oneToManyNatRules` | GET/PUT |
| Port Forwarding | `/networks/{id}/appliance/firewall/portForwardingRules` | GET/PUT |
| S2S VPN | `/organizations/{id}/appliance/vpn/thirdPartyVPNPeers` | GET/PUT |
| Client VPN | `/networks/{id}/appliance/vpn/clientVpn` | GET/PUT |
| Traffic Shaping | `/networks/{id}/appliance/trafficShaping/rules` | GET/PUT |
| Content Filtering | `/networks/{id}/appliance/contentFiltering` | GET/PUT |
| Threat Protection | `/networks/{id}/appliance/security/intrusion` | GET/PUT |
| Malware Protection | `/networks/{id}/appliance/security/malware` | GET/PUT |

---

## Regras de Segurança

1. **Deny any any:** NUNCA sem confirmação tripla — "Isso vai bloquear TODO o tráfego"
2. **Remover default allow:** NUNCA sem deny-all explícito e confirmação que é intencional
3. **Firewall é PUT total:** Alertar que qualquer erro no array pode sobrescrever TODAS as regras
4. **VPN PSK:** Mínimo 20 caracteres, sugerir geração automática
5. **NAT sem firewall:** Alertar que NAT sem regra de firewall correspondente pode expor serviço
6. **L7 + aplicação desconhecida:** Se usuário menciona app que não está no catálogo Meraki L7, informar
7. **Traffic shaping sem QoS:** Alertar que shaping sem marking pode não funcionar como esperado
