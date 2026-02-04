# N8N vs Meraki Workflows - Guia de Decisão

## Comparação Detalhada

| Aspecto | N8N | Meraki Workflows |
|---------|-----|------------------|
| **Hosting** | Self-hosted ou Cloud | Cloud (Dashboard integrado) |
| **Integrações Meraki** | Via HTTP Request (manual) | Nativas, otimizadas |
| **Integrações Cisco** | Requer desenvolvimento | ISE, DNA, SD-WAN nativas |
| **Nodes/Actions** | 1,084+ nodes | ~50 ações nativas |
| **Rate Limiting** | Você gerencia | Automático (20 starts/min) |
| **Curva de Aprendizado** | Médio (genérico) | Baixo (específico Meraki) |
| **Customização** | Alta (Code nodes JS/Python) | Média (Python support) |
| **Suporte** | Comunidade + Paid | Cisco TAC |
| **Custo** | Self-host: infra + manutenção | Incluído na licença Meraki |
| **Git Integration** | Possível com plugins | Nativo |
| **Audit/Compliance** | Manual | Built-in |
| **Interface** | Visual drag-and-drop | Visual drag-and-drop |
| **Webhooks** | Ilimitados | Incluídos |
| **Scheduling** | Flexível (cron) | Básico |

## Quando Usar N8N

### Cenários Ideais

1. **Ambiente Multi-Vendor**
   - Meraki + Fortinet
   - Meraki + Palo Alto
   - Meraki + qualquer outro vendor

2. **Rate Limiting é Problema**
   - Precisa de mais de 20 triggers/min
   - Operações em lote frequentes

3. **Integrações Complexas**
   - ServiceNow avançado
   - Jira com workflows complexos
   - Sistemas legados

4. **Controle Total**
   - Dados sensíveis não podem sair da rede
   - Requisitos de compliance específicos

5. **Automação além de rede**
   - HR systems
   - CRM
   - ERP

### Exemplo de Uso N8N

```
Trigger: Device offline (webhook de monitoring externo)
    ↓
N8N: HTTP Request → Meraki API (get device details)
    ↓
N8N: IF node → Verifica se é horário comercial
    ↓
N8N: HTTP Request → Fortinet (check redundant path)
    ↓
N8N: ServiceNow → Cria ticket
    ↓
N8N: Slack → Notifica NOC
    ↓
N8N: PagerDuty → Escala se crítico
```

## Quando Usar Meraki Workflows

### Cenários Ideais

1. **Ambiente 100% Cisco**
   - Meraki + ISE
   - Meraki + DNA Center
   - Meraki + SD-WAN

2. **Suporte TAC é Requisito**
   - Cliente exige suporte oficial
   - SLA de suporte crítico

3. **Compliance Nativo**
   - Precisa de audit trail built-in
   - Logs integrados ao Dashboard

4. **Simplicidade**
   - Equipe não técnica
   - Setup rápido sem infra

5. **Casos de Uso Padrão**
   - Device offline alerts
   - Firmware compliance
   - Config backup

### Exemplo de Uso Meraki Workflows

```
Trigger: Meraki Alert (device offline)
    ↓
Meraki Workflow: JSONPath Query (extract device info)
    ↓
Meraki Workflow: Sleep (5 min)
    ↓
Meraki Workflow: Meraki API Request (check status again)
    ↓
Meraki Workflow: Condition (still offline?)
    ↓
Meraki Workflow: HTTP Request (Slack webhook)
```

## Recomendação por Perfil de Cliente

| Perfil | Recomendação | Razão |
|--------|--------------|-------|
| Enterprise 100% Cisco | Meraki Workflows | Suporte TAC, integração nativa |
| MSP Multi-Vendor | N8N | Flexibilidade, multi-tenant |
| SMB Simples | Meraki Workflows | Sem infra adicional |
| Startup Técnica | N8N | Customização, self-hosted |
| Regulado (Saúde/Finanças) | Depende | Verificar requisitos específicos |

## Arquitetura Híbrida

Para o melhor dos dois mundos:

```
┌─────────────────────────────────────────────────────────┐
│                   Arquitetura Híbrida                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Meraki Workflows (Nativo)     N8N (Self-Hosted)       │
│  ┌───────────────────┐         ┌───────────────────┐   │
│  │ • Device alerts   │         │ • Multi-vendor    │   │
│  │ • Firmware check  │   →→→   │ • Complex logic   │   │
│  │ • Basic notify    │  webhook │ • ServiceNow     │   │
│  └───────────────────┘         │ • Custom code     │   │
│                                 └───────────────────┘   │
│                                                         │
│  Quando usar cada:                                      │
│  • Simples/Cisco → Meraki Workflows                    │
│  • Complexo/Multi → N8N                                │
│  • Híbrido → Meraki trigger → N8N process             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Recursos

### N8N
- Documentação: https://docs.n8n.io/
- GitHub: https://github.com/n8n-io/n8n
- MCP: https://github.com/czlonkowski/n8n-mcp
- Skills: https://github.com/czlonkowski/n8n-skills

### Meraki Workflows
- Documentação: https://documentation.meraki.com/Platform_Management/Workflows
- Exchange: Templates prontos no Dashboard
- API: https://developer.cisco.com/meraki/api/
