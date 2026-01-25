# Meraki Workflow

> Sistema de automacao para Cisco Meraki via linguagem natural usando Claude Code

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Meraki](https://img.shields.io/badge/meraki-SDK%201.53+-green.svg)](https://developer.cisco.com/meraki/)

---

## Quick Start (Para seu colega)

### 1. Clone o Repositorio

```bash
git clone https://github.com/SEU_USUARIO/Meraki_workflow.git
cd Meraki_workflow
```

### 2. Abra com Claude Code

```bash
claude
```

**Claude vai automaticamente:**
1. Instalar todas as dependencias necessarias
2. Perguntar sua API Key do Meraki Dashboard
3. Perguntar seu Organization ID
4. Criar a estrutura do cliente
5. Executar discovery completo da rede
6. Gerar relatorio HTML com todos os devices, SSIDs, VLANs, problemas encontrados

**Voce so precisa fornecer a API Key e Org ID!**

---

## O que este projeto faz?

| Funcionalidade | Descricao |
|----------------|-----------|
| **Discovery** | Analise completa de redes (networks, devices, SSIDs, VLANs, firewall) |
| **Configuracao** | Aplicar configs via linguagem natural (ACL, Firewall, SSID, Switch) |
| **Workflows** | Gerar JSON de automacao para importar no Dashboard |
| **Relatorios** | HTML/PDF profissionais para apresentar ao cliente |
| **Multi-cliente** | Suporte a multiplas organizacoes Meraki isoladas |

---

## Como Obter API Key e Org ID

### API Key

1. Acesse [Meraki Dashboard](https://dashboard.meraki.com)
2. Va em **Organization > Settings**
3. Role ate **Dashboard API access**
4. Marque **Enable access to the Cisco Meraki Dashboard API**
5. Clique em **Generate new API key**
6. **COPIE A CHAVE IMEDIATAMENTE** (ela so aparece uma vez!)

### Organization ID

**Opcao 1 - Via URL:**
Na URL do Dashboard, o Org ID aparece assim:
```
https://dashboard.meraki.com/o/123456/...
                               ^^^^^^
                               Org ID
```

**Opcao 2 - Via API:**
```bash
curl -H "X-Cisco-Meraki-API-Key: SUA_API_KEY" \
     https://api.meraki.com/api/v1/organizations
```

---

## Instalacao Manual (se necessario)

Se Claude nao conseguir instalar automaticamente:

```bash
# Criar virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install meraki python-dotenv pydantic pyyaml click rich jinja2

# Instalar o pacote
pip install -e .
```

### Dependencias

| Pacote | Versao | Uso |
|--------|--------|-----|
| meraki | >= 1.53.0 | SDK oficial Cisco Meraki |
| python-dotenv | >= 1.0.0 | Variaveis de ambiente |
| click | >= 8.1.0 | CLI framework |
| rich | >= 13.0.0 | Output formatado no terminal |
| jinja2 | >= 3.1.0 | Templates HTML para relatorios |
| pydantic | >= 2.0.0 | Validacao de dados |
| pyyaml | >= 6.0.0 | Parsing YAML |

---

## Comandos CLI Disponiveis

### Discovery (Analise de Rede)

```bash
# Discovery completo
meraki discover full --client NOME_CLIENTE

# Listar snapshots salvos
meraki discover list --client NOME_CLIENTE
```

### Configuracao

```bash
# Configurar SSID
meraki config ssid -n NETWORK_ID --number 0 --name "Guest WiFi" --enabled -c CLIENTE

# Configurar Firewall L3 (bloquear telnet)
meraki config firewall -n NETWORK_ID --policy deny --protocol tcp --port 23 -c CLIENTE

# Configurar VLAN
meraki config vlan -n NETWORK_ID --vlan-id 100 --name "Servers" --subnet 10.0.100.0/24 -c CLIENTE
```

### Workflows

```bash
# Criar workflow
meraki workflow create -t device-offline -c CLIENTE

# Listar templates disponiveis
meraki workflow list-templates
```

### Relatorios

```bash
# Gerar relatorio HTML
meraki report discovery -c CLIENTE

# Gerar em PDF (requer weasyprint)
meraki report discovery -c CLIENTE --pdf
```

---

## Usando com Claude Code (Linguagem Natural)

### Exemplos de comandos

```
"Analise a rede deste cliente"
→ Executa discovery completo e mostra resumo

"Quais problemas voce encontrou?"
→ Lista issues de seguranca e performance

"Configure ACL para bloquear telnet no switch core"
→ Aplica regras de firewall via API

"Crie um workflow para alertar quando device ficar offline"
→ Gera JSON para importar no Dashboard

"Gere um relatorio executivo para o cliente"
→ Cria HTML/PDF com visao geral da rede
```

### Agentes Especializados

| Agente | Quando Usar |
|--------|-------------|
| `network-analyst` | Discovery, diagnostico, analise de problemas |
| `meraki-specialist` | Configurar ACL, Firewall, SSID, Switch, Camera, QoS |
| `workflow-creator` | Criar workflows JSON para automacao |

---

## Estrutura do Projeto

```
Meraki_workflow/
├── CLAUDE.md              # Instrucoes para Claude Code
├── README.md              # Este arquivo
├── setup.py               # Instalacao do pacote
├── requirements.txt       # Dependencias
│
├── scripts/               # Modulos Python
│   ├── auth.py            # Autenticacao multi-profile
│   ├── api.py             # Wrapper Meraki API
│   ├── discovery.py       # Analise de rede
│   ├── config.py          # Aplicar configuracoes
│   ├── workflow.py        # Gerador de workflows JSON
│   ├── report.py          # Relatorios HTML/PDF
│   └── cli.py             # Interface de linha de comando
│
├── .claude/
│   ├── agents/            # Agentes especializados
│   │   ├── meraki-specialist.md
│   │   ├── network-analyst.md
│   │   └── workflow-creator.md
│   └── knowledge/         # Base de conhecimento
│
├── clients/               # Dados por cliente
│   └── {nome}/
│       ├── .env           # Profile do cliente
│       ├── discovery/     # Snapshots da rede
│       ├── workflows/     # Workflows criados
│       └── reports/       # Relatorios gerados
│
└── tests/                 # Testes unitarios
```

---

## Workflows Disponiveis

| Template | Descricao |
|----------|-----------|
| `device-offline` | Notifica quando device fica offline por X minutos |
| `firmware-compliance` | Verifica se devices tem firmware atualizado |
| `scheduled-report` | Gera relatorio automatico agendado |
| `security-alert` | Handler de alertas de seguranca (IDS/IPS) |

**Nota:** Workflows NAO podem ser criados via API. O sistema gera JSON para voce importar manualmente no Dashboard.

---

## Issues Detectados Automaticamente

O discovery identifica automaticamente:

| Issue | Severidade | Descricao |
|-------|------------|-----------|
| `devices_offline` | HIGH | Devices com status offline |
| `insecure_ssid` | HIGH | SSIDs sem autenticacao |
| `devices_alerting` | MEDIUM | Devices em estado de alerta |
| `permissive_firewall` | MEDIUM | Regras allow any any |
| `empty_networks` | LOW | Networks sem devices |

---

## Troubleshooting

### Erro: "API rate limit exceeded"

O Meraki tem limite de 10 requests/segundo. O SDK gerencia isso automaticamente, mas operacoes grandes podem demorar.

### Erro: "Invalid API key"

1. Verifique se a API key esta correta (copie novamente do Dashboard)
2. Confirme que API esta habilitada: **Organization > Settings > Dashboard API access**

### Erro: "Module not found"

```bash
pip install -e .
# ou instale dependencias individualmente:
pip install meraki python-dotenv click rich jinja2 pydantic pyyaml
```

### Claude nao esta instalando dependencias

Execute manualmente:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## Limitacoes Conhecidas

1. **Workflows**: NAO podem ser criados via API - geramos JSON para import manual
2. **Rate Limit**: 10 req/s por organizacao (SDK gerencia automaticamente)
3. **PDF**: Requer WeasyPrint instalado (opcional)
4. **Alguns endpoints**: Requerem licencas especificas (ex: Camera API)

---

## Links Uteis

- [Meraki Dashboard API Docs](https://developer.cisco.com/meraki/api-v1/)
- [Meraki Python SDK](https://github.com/meraki/dashboard-api-python)
- [Meraki Workflows Docs](https://documentation.meraki.com/Platform_Management/Workflows)

---

## Licenca

Projeto privado - uso interno.

---

**Desenvolvido com Claude Code (Opus 4.5)**
