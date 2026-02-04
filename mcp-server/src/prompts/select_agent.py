"""
MCP Prompt: select_agent

Ajuda o usuário a escolher o agente especializado correto.
"""

AGENTS_INFO = {
    "meraki-specialist": {
        "icon": "🔧",
        "name": "Meraki Specialist",
        "description": "Especialista em configuração Meraki via API",
        "use_cases": [
            "Configurar ACL em switches",
            "Configurar Firewall L3/L7",
            "Configurar SSIDs wireless",
            "Configurar VLANs",
            "Configurar QoS",
            "Gerenciar câmeras MV",
        ],
        "commands": ["*configure", "*show-config", "*backup"],
    },
    "network-analyst": {
        "icon": "📊",
        "name": "Network Analyst",
        "description": "Analista de rede para discovery e diagnóstico",
        "use_cases": [
            "Executar discovery de rede",
            "Analisar topologia",
            "Identificar problemas",
            "Comparar snapshots",
            "Sugerir melhorias",
        ],
        "commands": ["*discover", "*analyze", "*compare"],
    },
    "workflow-creator": {
        "icon": "🔄",
        "name": "Workflow Creator",
        "description": "Criador de automações Meraki/N8N",
        "use_cases": [
            "Criar alertas de device offline",
            "Criar checks de compliance",
            "Criar relatórios agendados",
            "Migrar para N8N",
        ],
        "commands": ["*create-workflow", "*list-templates", "*validate"],
    },
}


def select_agent_prompt(task_description: str = "") -> dict:
    """
    Retorna prompt para seleção de agente.

    Args:
        task_description: Descrição da tarefa do usuário (opcional)

    Returns:
        dict com estrutura do prompt MCP
    """
    prompt_text = """# Selecione o Agente Especializado

Com base na sua tarefa, escolha o agente mais adequado:

"""
    for agent_id, info in AGENTS_INFO.items():
        prompt_text += f"""
## {info['icon']} {info['name']} (`@{agent_id}`)

{info['description']}

**Quando usar:**
"""
        for use_case in info['use_cases']:
            prompt_text += f"- {use_case}\n"

        prompt_text += f"\n**Comandos principais:** `{'`, `'.join(info['commands'])}`\n"

    if task_description:
        prompt_text += f"""
---

**Sua tarefa:** {task_description}

**Recomendação:** Baseado na descrição, o agente recomendado é...
"""

    return {
        "name": "select_agent",
        "description": "Help user select the right specialized agent for their task",
        "arguments": [
            {
                "name": "task_description",
                "description": "Brief description of what the user wants to accomplish",
                "required": False,
            },
        ],
    }


# Prompt schema para MCP
PROMPT_SCHEMA = {
    "name": "select_agent",
    "description": "Interactive guide to help users select the right specialized agent (meraki-specialist, network-analyst, workflow-creator) based on their task.",
    "arguments": [
        {
            "name": "task_description",
            "description": "Brief description of what the user wants to accomplish (e.g., 'configure firewall rules', 'analyze network topology')",
            "required": False,
        },
    ],
}


def get_agent_recommendation(task: str) -> str:
    """
    Retorna recomendação de agente baseada na tarefa.

    Args:
        task: Descrição da tarefa

    Returns:
        ID do agente recomendado
    """
    task_lower = task.lower()

    # Keywords para cada agente
    specialist_keywords = [
        "configurar", "config", "ssid", "firewall", "acl", "vlan",
        "switch", "camera", "qos", "wireless", "port", "rule"
    ]
    analyst_keywords = [
        "analisar", "analyze", "discovery", "descobrir", "topologia",
        "problema", "issue", "diagnóstico", "comparar", "snapshot"
    ]
    workflow_keywords = [
        "workflow", "automação", "automation", "alerta", "alert",
        "agendar", "schedule", "n8n", "compliance"
    ]

    # Contar matches
    specialist_score = sum(1 for kw in specialist_keywords if kw in task_lower)
    analyst_score = sum(1 for kw in analyst_keywords if kw in task_lower)
    workflow_score = sum(1 for kw in workflow_keywords if kw in task_lower)

    # Retornar o de maior score
    scores = {
        "meraki-specialist": specialist_score,
        "network-analyst": analyst_score,
        "workflow-creator": workflow_score,
    }

    return max(scores, key=scores.get)
