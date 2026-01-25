# CLAUDE.md - Meraki Workflow Project

> **Projeto**: Sistema de automacao Meraki via linguagem natural
> **Objetivo**: Configurar redes Meraki e criar workflows usando agentes especializados

---

## INICIO AUTOMATICO - PRIMEIRA EXECUCAO

**CRITICO**: Na primeira interacao com o usuario, voce DEVE executar este fluxo automaticamente:

### Passo 1: Verificar e Instalar Dependencias

```bash
# Verificar se virtual environment existe
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate

# Instalar dependencias
pip install meraki python-dotenv pydantic pyyaml click rich jinja2
pip install -e .
```

### Passo 2: Perguntar Credenciais ao Usuario

Use a ferramenta AskUserQuestion para obter:

1. **API Key do Meraki Dashboard**
   - Instrua: "Acesse Organization > Settings > Dashboard API access > Generate new API key"

2. **Organization ID**
   - Instrua: "Na URL do Dashboard: dashboard.meraki.com/o/XXXXXX/... o XXXXXX e seu Org ID"

3. **Nome para identificar o cliente** (usado para criar pastas)

### Passo 3: Configurar Credenciais

```bash
# Criar diretorio de credenciais
mkdir -p ~/.meraki

# Salvar credenciais (substituir com valores fornecidos)
cat > ~/.meraki/credentials << 'EOF'
[NOME_CLIENTE]
api_key = API_KEY_FORNECIDA
org_id = ORG_ID_FORNECIDO
EOF

# Criar estrutura do cliente
mkdir -p clients/NOME_CLIENTE/{discovery,workflows,reports}
echo "MERAKI_PROFILE=NOME_CLIENTE" > clients/NOME_CLIENTE/.env
```

### Passo 4: Executar Discovery Completo

```bash
meraki discover full --client NOME_CLIENTE
```

### Passo 5: Gerar Relatorio HTML

```bash
meraki report discovery --client NOME_CLIENTE
```

### Passo 6: Mostrar Resultados ao Usuario

Leia o relatorio HTML gerado em `clients/NOME_CLIENTE/reports/` e apresente:

- Nome da organizacao
- Total de networks
- Total de devices (quantos online, quantos offline)
- SSIDs configurados
- **Issues encontrados** (seguranca, performance)
- Recomendacoes de melhorias

---

## USO NORMAL (Apos Setup Inicial)

Quando o usuario ja tem credenciais configuradas:

```
"Analise a rede do cliente X"     → Usa network-analyst
"Configure ACL para bloquear Y"   → Usa meraki-specialist
"Crie workflow para Z"            → Usa workflow-creator
```

---

## Visao Geral do Projeto

Este projeto permite:
1. **Conectar** a qualquer cliente Meraki via API
2. **Analisar** a rede existente (discovery)
3. **Configurar** ACL, Firewall, SSID, Switch, etc via linguagem natural
4. **Criar Workflows** de automacao (remediation, compliance, etc)
5. **Gerar Relatorios** HTML/PDF para o cliente

---

## Sistema de Agentes

### Agentes Disponiveis

| Agente | Arquivo | Quando Usar |
|--------|---------|-------------|
| `meraki-specialist` | `.claude/agents/meraki-specialist.md` | Configurar ACL, Firewall, SSID, Switch, Camera, QoS |
| `network-analyst` | `.claude/agents/network-analyst.md` | Discovery, analise de rede, diagnostico |
| `workflow-creator` | `.claude/agents/workflow-creator.md` | Criar workflows JSON de automacao |

### Regra de Ouro

**SEMPRE leia o arquivo do agente antes de executar qualquer tarefa.**

```
Tarefa: "Configure uma ACL no switch core"

1. Ler .claude/agents/meraki-specialist.md
2. Seguir o fluxo definido no agente
3. Executar a configuracao
4. Documentar em changelog
```

---

## Estrutura do Projeto

```
Meraki_workflow/
├── CLAUDE.md              # [VOCE ESTA AQUI]
├── README.md              # Documentacao principal
├── setup.py               # Instalacao pip
├── requirements.txt       # Dependencias
│
├── .claude/
│   ├── agents/            # Agentes especializados
│   │   ├── meraki-specialist.md
│   │   ├── network-analyst.md
│   │   └── workflow-creator.md
│   └── knowledge/         # Base de conhecimento
│       └── cisco-workflows-schema.md
│
├── scripts/               # Modulos Python
│   ├── auth.py            # Gestao de credenciais
│   ├── api.py             # Wrapper Meraki API
│   ├── discovery.py       # Analise de rede
│   ├── config.py          # Aplicar configuracoes
│   ├── workflow.py        # Gerador de workflows
│   ├── report.py          # HTML/PDF
│   └── cli.py             # Interface CLI
│
├── clients/               # Dados por cliente
│   └── {nome-cliente}/
│       ├── .env           # MERAKI_PROFILE=nome
│       ├── discovery/     # Snapshots da rede
│       ├── workflows/     # Workflows criados
│       └── reports/       # Relatorios HTML/PDF
│
└── tests/                 # Testes unitarios
```

---

## Credenciais

Credenciais ficam em `~/.meraki/credentials`:

```ini
[default]
api_key = YOUR_API_KEY
org_id = YOUR_ORG_ID

[cliente-acme]
api_key = ACME_API_KEY
org_id = ACME_ORG_ID
```

---

## Fluxo Tipico de Visita ao Cliente

```
1. Claude pergunta API Key e Org ID
2. Claude configura credenciais e cria estrutura
3. Claude executa discovery automaticamente
4. Claude gera relatorio HTML
5. Usuario ve resumo da rede com issues
6. Usuario pede configuracoes especificas
   → "Bloqueie telnet em toda a rede"
   → Claude usa meraki-specialist
7. Usuario pede workflows
   → "Crie alerta para device offline"
   → Claude usa workflow-creator
```

---

## Regras Importantes

### Seguranca
- NUNCA commitar credenciais (elas ficam em ~/.meraki/)
- SEMPRE fazer backup antes de mudar config
- Rate limit: 10 req/s por org (SDK gerencia)

### Workflows
- Workflows NAO podem ser criados via API
- Gerar JSON → usuario importa no Dashboard manualmente
- Ver `.claude/knowledge/cisco-workflows-schema.md` para formato correto

---

## Comandos CLI Disponiveis

```bash
# Discovery
meraki discover full --client NOME

# Configuracao
meraki config ssid -n NETWORK_ID --number 0 --name "Guest" -c NOME
meraki config firewall -n NETWORK_ID --policy deny --protocol tcp --port 23 -c NOME

# Workflows
meraki workflow create -t device-offline -c NOME

# Relatorios
meraki report discovery -c NOME
meraki report discovery -c NOME --pdf
```

---

## Links Uteis

- Meraki Dashboard API: https://developer.cisco.com/meraki/api-v1/
- Meraki Workflows: https://documentation.meraki.com/Platform_Management/Workflows
- Python SDK: https://github.com/meraki/dashboard-api-python

---

**Desenvolvido com Claude Code (Opus 4.5)**
