# Task: configure-wireless

## Metadata
- **ID:** T1
- **Trigger:** SSID, WiFi, wireless, splash page, captive portal, RF, bandwidth limit, air marshal, bluetooth
- **Scope:** MR (Access Points) + Wireless settings em nível de rede
- **Risk:** MODERATE (mudança em SSID pode derrubar conexões ativas)

---

## Steps

### Step 1 — Parse Intent
- **Type:** agent
- **Input:** mensagem do usuário ou handoff
- **Output:** `change-request` schema preenchido
- **LLM Action:** Interpretar o que o usuário quer e mapear para operação(ões) API
- **Exemplos de intent:**
  - "Cria um SSID para visitantes com captive portal" → create SSID + splash config
  - "Limita banda do Guest WiFi para 5Mbps" → update bandwidth limit
  - "Desabilita o SSID Corporate na filial SP" → update SSID enabled=false
  - "Muda a senha do WiFi escritório" → update PSK

### Step 2 — Resolve Targets
- **Type:** tool
- **Tools:** `get_networks`, `get_network_ssids`, `get_network_devices`
- **Action:** Identificar network_id, SSID number (0-14), devices afetados
- **Validation:**
  - Network existe?
  - SSID number disponível? (máximo 15 SSIDs por rede)
  - Devices MR presentes na rede?

### Step 3 — Generate Preview
- **Type:** agent
- **Input:** estado atual (GET) + mudança desejada
- **Output:** `change-preview` schema
- **Format:**
```
Vou configurar o seguinte SSID:

  Nome: Guest-WiFi
  Auth: WPA2-PSK
  Splash: Click-through
  Banda: 5Mbps up/down por cliente
  Status: Habilitado

  Rede: Escritório-SP
  APs afetados: 12

  [antes] SSID slot 3: vazio
  [depois] SSID slot 3: Guest-WiFi (WPA2-PSK, 5Mbps limit)

Confirma? (sim/não)
```

### Step 4 — Confirmation Gate
- **Type:** gate
- **Action:** Aguardar confirmação explícita do usuário
- **Se "não":** Perguntar o que ajustar, voltar ao Step 1
- **Se timeout:** Não aplicar, informar que mudança foi cancelada

### Step 5 — Apply Changes
- **Type:** tool
- **Tools:** `update_network_ssid`, `update_network_ssid_splash_settings`
- **Sequence:** (ordem importa)
  1. Configurar SSID base (nome, auth, encryption, PSK)
  2. Configurar splash page (se aplicável)
  3. Configurar bandwidth limits (se aplicável)
  4. Configurar IP assignment (bridge/NAT/layer3)
  5. Habilitar SSID (enabled=true) — SEMPRE por último
- **Rate limit:** Máximo 2 calls por segundo nesta task

### Step 6 — Verify
- **Type:** tool
- **Tools:** `get_network_ssid`
- **Action:** GET o SSID configurado e comparar com o esperado
- **Se divergir:** Alertar usuário, oferecer rollback

---

## Operações API Cobertas

| Operação | Endpoint | Método |
|----------|----------|--------|
| Listar SSIDs | `/networks/{id}/wireless/ssids` | GET |
| Atualizar SSID | `/networks/{id}/wireless/ssids/{number}` | PUT |
| Splash settings | `/networks/{id}/wireless/ssids/{number}/splash/settings` | PUT |
| RF profiles | `/networks/{id}/wireless/rfProfiles` | POST/PUT |
| Bluetooth settings | `/networks/{id}/wireless/bluetooth/settings` | PUT |
| Air Marshal rules | `/networks/{id}/wireless/airMarshal/rules` | PUT |

---

## Campos Configuráveis (SSID)

```yaml
name: string              # Nome do SSID (obrigatório)
enabled: boolean          # Ativo/inativo
authMode: enum            # open | psk | 8021x-meraki | 8021x-radius
encryptionMode: enum      # wep | wpa
psk: string               # Pre-shared key (se authMode=psk)
wpaEncryptionMode: enum   # WPA1 only | WPA1 and WPA2 | WPA2 only | WPA3 only
splashPage: enum          # None | Click-through | Billing | Password | etc
bandSelection: enum       # Dual band | 5 GHz only | Dual band with band steering
perClientBandwidthLimitUp: integer    # Kbps (0 = unlimited)
perClientBandwidthLimitDown: integer  # Kbps (0 = unlimited)
ipAssignmentMode: enum    # Bridge mode | NAT mode | Layer 3 roaming
visible: boolean          # Broadcast SSID?
availableOnAllAps: boolean
radiusServers: array      # Se 8021x
```

---

## Regras de Segurança

1. **PSK mínima:** 8 caracteres, sugerir 12+ com complexidade
2. **Open SSID:** Alertar SEMPRE — "SSID sem autenticação. Recomendo WPA2 mínimo."
3. **WPA1:** Alertar deprecação — "WPA1 é vulnerável. Recomendo WPA2 ou WPA3."
4. **Splash sem HTTPS:** Alertar risco de interceptação
5. **Bandwidth 0 (unlimited):** Alertar se for guest SSID — "Sem limite de banda em guest pode saturar o link"
