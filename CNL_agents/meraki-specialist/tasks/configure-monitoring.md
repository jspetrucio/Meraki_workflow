# Task: configure-monitoring

## Metadata
- **ID:** T4
- **Trigger:** alert, SNMP, syslog, camera, MV, tag, firmware, notification, webhook, motion zone, retention, analytics
- **Scope:** Cross-device (MX, MS, MR, MV) + configurações de nível organizacional
- **Risk:** LOW-MODERATE (monitoring changes raramente causam disrupção)

---

## Steps

### Step 1 — Parse Intent
- **Type:** agent
- **Input:** mensagem do usuário ou handoff
- **Output:** `change-request` schema preenchido
- **Exemplos de intent:**
  - "Configura alertas de queda de link por email" → alert settings
  - "Habilita SNMP v3 para monitoramento" → SNMP config
  - "Envia logs para syslog 10.0.1.50" → syslog server
  - "Configura zona de movimento na câmera da entrada" → MV motion zone
  - "Muda retenção de vídeo para 30 dias" → MV retention
  - "Adiciona tag 'critical' nos switches core" → device tags
  - "Agenda firmware update para sábado 2AM" → firmware schedule

### Step 2 — Resolve Targets
- **Type:** tool
- **Tools:** `get_networks`, `get_devices`, `get_network_alerts_settings`
- **Action:** Identificar network/org/device alvo
- **Validation:**
  - Para SNMP: network-level ou org-level?
  - Para syslog: IP do servidor acessível?
  - Para cameras (MV): device tem licença MV?
  - Para firmware: versão alvo disponível?

### Step 3 — Generate Preview
- **Type:** agent
- **Output:** `change-preview` schema
- **Formato mais simples** que tasks de alto risco — monitoring é geralmente aditivo

### Step 4 — Confirmation Gate
- **Type:** gate
- **Nível:** Confirmação simples para maioria das operações
- **Exceção:** Firmware update requer confirmação + janela de manutenção explícita

### Step 5 — Apply Changes
- **Type:** tool
- **Sequence por tipo:**

**Alerts:**
  1. GET alert settings atuais
  2. Adicionar/modificar alert type
  3. PUT settings atualizados
  4. Configurar destinatários (email, webhook, SMS)

**SNMP:**
  1. PUT SNMP settings (community string ou v3 users)
  2. Verificar que polling funciona

**Syslog:**
  1. GET syslog servers atuais
  2. Adicionar novo servidor
  3. PUT servers atualizados

**Cameras (MV):**
  1. GET quality/retention settings
  2. PUT com novos valores
  3. Para motion zones: PUT zone config

**Tags:**
  1. GET device tags atuais
  2. Append nova tag
  3. PUT tags atualizadas

**Firmware:**
  1. GET available firmware versions
  2. Schedule upgrade (PUT)
  3. Informar janela e expected downtime

### Step 6 — Verify
- **Type:** tool
- **Action:** GET configuração atualizada e confirmar

---

## Operações API Cobertas

| Operação | Endpoint | Método |
|----------|----------|--------|
| Alert settings | `/networks/{id}/alerts/settings` | GET/PUT |
| SNMP | `/networks/{id}/snmp` | GET/PUT |
| Syslog | `/networks/{id}/syslogServers` | GET/PUT |
| MV quality | `/devices/{serial}/camera/qualityAndRetention` | GET/PUT |
| MV motion zones | `/devices/{serial}/camera/analytics/zones` | GET |
| MV sense | `/devices/{serial}/camera/sense` | GET/PUT |
| Device tags | `/networks/{id}/devices` | GET + claim/update |
| Firmware upgrades | `/networks/{id}/firmwareUpgrades` | GET/PUT |
| Webhooks | `/networks/{id}/webhooks/httpServers` | GET/POST |
| Webhook payload templates | `/networks/{id}/webhooks/payloadTemplates` | GET/POST |

---

## Regras de Segurança

1. **SNMP community string:** Nunca usar "public" ou "private" — sugerir string complexa
2. **SNMP v2 vs v3:** Alertar que v2 não tem criptografia — recomendar v3
3. **Syslog sem TLS:** Informar que logs viajam em texto plano
4. **Firmware em horário comercial:** Alertar impacto e sugerir janela noturna
5. **Retenção de câmera < 7 dias:** Alertar que pode não atender compliance
6. **Webhook para URL externa:** Alertar sobre segurança do endpoint receptor
