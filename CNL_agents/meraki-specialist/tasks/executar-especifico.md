# Task: executar-especifico

## Metadata
- **ID:** T6
- **Trigger:** Qualquer pedido de configuração que não encaixa em T1-T5
- **Scope:** Qualquer endpoint da Meraki Dashboard API
- **Risk:** VARIABLE (depende da operação)
- **Nota:** Este é o fallback — se o Router não consegue classificar em T1-T5, cai aqui

---

## Quando Ativa

- Pedidos pontuais: "Qual o serial do switch core?"
- Operações raras: "Configura Bluetooth no AP da sala 5"
- Combinações: "Cria VLAN e configura firewall e SSID" (multi-task)
- Consultas API: "Lista todas as redes da org"

---

## Steps

### Step 1 — Classify Operation
- **Type:** agent
- **Input:** mensagem do usuário
- **Output:** Classificação: read-only | write-single | write-batch | multi-task
- **LLM Action:**
  - **read-only:** Só precisa GET → executa direto, sem preview/confirmação
  - **write-single:** Uma operação write → fluxo completo (preview + confirm)
  - **write-batch:** Múltiplas operações write → fluxo completo + batch warning
  - **multi-task:** Precisa de múltiplas tasks → decompose e executar sequencialmente

### Step 2 — Execute or Delegate
- **Type:** agent + tool
- **Se read-only:**
  1. Identificar endpoint correto (consultar `references/tools.md`)
  2. Executar GET
  3. Formatar resultado para o usuário
  4. **FIM — sem preview/confirm necessário**
- **Se write:**
  1. Seguir fluxo universal (parse → resolve → preview → confirm → apply → verify)
  2. Consultar `references/tools.md` para endpoint correto
- **Se multi-task:**
  1. Decompor em tarefas individuais
  2. Informar o plano ao usuário
  3. Executar cada task sequencialmente com confirmação individual
```
Identifiquei que seu pedido envolve 3 operações:

  1. Criar VLAN 100 (Task: configure-switching)
  2. Criar regra de firewall para VLAN 100 (Task: configure-security)
  3. Criar SSID que usa VLAN 100 (Task: configure-wireless)

Vou executar na ordem acima. Cada etapa terá seu preview e confirmação.
Começando pela VLAN...
```

### Step 3-6 — Fluxo Universal
- Segue o mesmo padrão de qualquer task quando write está envolvido
- Para read-only, pula steps 3-6

---

## Operações Read-Only Comuns

| Operação | Endpoint | Uso |
|----------|----------|-----|
| Listar organizações | `/organizations` | "Quais orgs tenho acesso?" |
| Listar redes | `/organizations/{id}/networks` | "Lista redes da org" |
| Listar devices | `/networks/{id}/devices` | "Quais devices nesta rede?" |
| Device status | `/organizations/{id}/devices/statuses` | "Status dos devices" |
| Clients | `/networks/{id}/clients` | "Quem está conectado?" |
| Uplink status | `/organizations/{id}/appliance/uplink/statuses` | "Status dos uplinks" |
| License info | `/organizations/{id}/licenses/overview` | "Situação das licenças" |

---

## Regras

1. **Read-only é sempre seguro** — executar sem confirmação
2. **Write segue o fluxo universal** — mesmo que pareça simples
3. **Multi-task executa sequencialmente** — nunca em paralelo (rate limits + dependências)
4. **Se não encontrar endpoint:** Informar limitação da API e sugerir Dashboard manual
5. **Se operação parece diagnóstico:** Sugerir handoff para Network Analyst
