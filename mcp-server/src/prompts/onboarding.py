"""
MCP Prompt: onboarding

Guia interativo de setup inicial para novos usuários.
"""

ONBOARDING_PROMPT = """
# Meraki Workflow - Setup Inicial

Bem-vindo ao Meraki Workflow! Vou te guiar no setup inicial.

## Passo 1: API Key do Meraki Dashboard

Para começar, preciso da sua API Key do Meraki:

1. Acesse o Meraki Dashboard: https://dashboard.meraki.com
2. Vá em **Organization > Settings**
3. Role até **Dashboard API access**
4. Clique em **Generate new API key**
5. Copie a chave gerada (ela só aparece uma vez!)

**Sua API Key:** [aguardando input]

## Passo 2: Organization ID

Agora preciso do ID da sua organização:

1. Na URL do Dashboard, procure: `dashboard.meraki.com/o/XXXXXX/...`
2. O `XXXXXX` é seu Organization ID
3. Ou acesse **Organization > Settings** e copie o ID

**Seu Org ID:** [aguardando input]

## Passo 3: Nome do Cliente

Como você quer identificar este cliente/ambiente?
(Usado para organizar arquivos em `clients/{nome}/`)

**Nome do cliente:** [aguardando input]

---

Após coletar essas informações, vou:
1. Configurar as credenciais em `~/.meraki/credentials`
2. Criar a estrutura do cliente em `clients/{nome}/`
3. Executar um discovery inicial da rede
4. Gerar um relatório HTML com o estado atual

Pronto para começar?
"""


def onboarding_prompt() -> dict:
    """
    Retorna o prompt de onboarding e argumentos esperados.

    Returns:
        dict com estrutura do prompt MCP:
        {
            "name": str,
            "description": str,
            "arguments": list
        }
    """
    return {
        "name": "onboarding",
        "description": "Interactive setup guide for new Meraki Workflow users. Collects API key, Org ID, and client name.",
        "arguments": [
            {
                "name": "api_key",
                "description": "Meraki Dashboard API Key",
                "required": True,
            },
            {
                "name": "org_id",
                "description": "Meraki Organization ID",
                "required": True,
            },
            {
                "name": "client_name",
                "description": "Name to identify this client/environment",
                "required": True,
            },
        ],
    }


# Prompt template para MCP
PROMPT_SCHEMA = {
    "name": "onboarding",
    "description": "Interactive setup guide for new Meraki Workflow users. Walks through API key configuration, organization setup, and initial discovery.",
    "arguments": [
        {
            "name": "api_key",
            "description": "Meraki Dashboard API Key (generate at Organization > Settings > Dashboard API access)",
            "required": True,
        },
        {
            "name": "org_id",
            "description": "Meraki Organization ID (found in Dashboard URL: dashboard.meraki.com/o/XXXXXX/...)",
            "required": True,
        },
        {
            "name": "client_name",
            "description": "Identifier for this client/environment (e.g., 'acme', 'customer-abc')",
            "required": True,
        },
    ],
}
