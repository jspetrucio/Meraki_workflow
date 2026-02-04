"""
MCP Prompt: troubleshoot

Diagnóstico guiado de problemas de rede Meraki.
"""

TROUBLESHOOT_STEPS = {
    "device_offline": {
        "title": "Device Offline",
        "description": "Um ou mais devices não estão respondendo",
        "steps": [
            "1. Verificar alimentação elétrica do device",
            "2. Verificar conectividade física (cabos, LEDs)",
            "3. Verificar status no Dashboard Meraki",
            "4. Executar ping para o IP do device",
            "5. Verificar se há alertas de manutenção na região",
            "6. Verificar logs de eventos no Dashboard",
            "7. Tentar reboot remoto (se possível)",
            "8. Verificar configurações de uplink",
        ],
        "commands": [
            "meraki_get_device_status serial=<SERIAL>",
            "meraki_discover client=<CLIENT>",
        ],
    },
    "slow_network": {
        "title": "Rede Lenta",
        "description": "Usuários reportando lentidão na rede",
        "steps": [
            "1. Identificar horário/local do problema",
            "2. Verificar utilização de banda no Dashboard",
            "3. Identificar top talkers (usuários/apps)",
            "4. Verificar se há traffic shaping ativo",
            "5. Analisar QoS configurado",
            "6. Verificar interferência wireless (se aplicável)",
            "7. Verificar status dos uplinks",
            "8. Comparar com baseline anterior",
        ],
        "commands": [
            "meraki_report client=<CLIENT> report_type=discovery",
            "meraki_get_device_status serial=<SERIAL> include_clients=true",
        ],
    },
    "connectivity": {
        "title": "Problemas de Conectividade",
        "description": "Usuários não conseguem acessar recursos",
        "steps": [
            "1. Identificar quais recursos estão inacessíveis",
            "2. Verificar se o problema é específico ou geral",
            "3. Verificar regras de firewall",
            "4. Verificar configurações de VLAN",
            "5. Verificar rotas e NAT",
            "6. Testar conectividade end-to-end",
            "7. Verificar DNS e DHCP",
            "8. Analisar logs de segurança",
        ],
        "commands": [
            "meraki_list_networks profile=<PROFILE>",
            "meraki_configure network_id=<NET_ID> config_type=firewall params={} client=<CLIENT> dry_run=true",
        ],
    },
    "wireless": {
        "title": "Problemas Wireless",
        "description": "Problemas com conexão WiFi",
        "steps": [
            "1. Verificar força do sinal no local",
            "2. Verificar interferência de canais",
            "3. Verificar configurações do SSID",
            "4. Verificar autenticação (PSK, 802.1X)",
            "5. Verificar VLAN associada ao SSID",
            "6. Verificar limite de clientes",
            "7. Analisar roaming entre APs",
            "8. Verificar firmware dos APs",
        ],
        "commands": [
            "meraki_discover client=<CLIENT>",
            "meraki_configure network_id=<NET_ID> config_type=ssid params={'number': 0} client=<CLIENT> dry_run=true",
        ],
    },
    "security": {
        "title": "Incidente de Segurança",
        "description": "Suspeita de atividade maliciosa ou violação",
        "steps": [
            "1. NÃO desligar equipamentos (preservar evidências)",
            "2. Isolar segmento afetado se necessário",
            "3. Documentar timeline do incidente",
            "4. Verificar logs de segurança no Dashboard",
            "5. Identificar dispositivos/IPs envolvidos",
            "6. Verificar regras de firewall ativas",
            "7. Bloquear tráfego suspeito",
            "8. Coletar evidências para análise",
        ],
        "commands": [
            "meraki_report client=<CLIENT> report_type=security",
            "meraki_configure network_id=<NET_ID> config_type=firewall params={'policy':'deny','protocol':'any','src_cidr':'<IP_SUSPEITO>/32'} client=<CLIENT>",
        ],
    },
}


def troubleshoot_prompt(problem_type: str = "", description: str = "") -> dict:
    """
    Retorna prompt de troubleshooting.

    Args:
        problem_type: Tipo de problema (device_offline, slow_network, etc.)
        description: Descrição adicional do problema

    Returns:
        dict com estrutura do prompt MCP
    """
    return {
        "name": "troubleshoot",
        "description": "Guided troubleshooting for common Meraki network issues",
        "arguments": [
            {
                "name": "problem_type",
                "description": "Type of problem: device_offline, slow_network, connectivity, wireless, security",
                "required": False,
            },
            {
                "name": "description",
                "description": "Additional description of the issue",
                "required": False,
            },
        ],
    }


def get_troubleshoot_guide(problem_type: str) -> dict:
    """
    Retorna guia de troubleshooting para um tipo de problema.

    Args:
        problem_type: Tipo de problema

    Returns:
        dict com título, passos e comandos sugeridos
    """
    if problem_type in TROUBLESHOOT_STEPS:
        return TROUBLESHOOT_STEPS[problem_type]

    # Retornar lista de tipos disponíveis
    return {
        "error": f"Unknown problem type: {problem_type}",
        "available_types": list(TROUBLESHOOT_STEPS.keys()),
        "hint": "Choose one of the available problem types",
    }


def format_troubleshoot_response(problem_type: str, description: str = "") -> str:
    """
    Formata resposta completa de troubleshooting.

    Args:
        problem_type: Tipo de problema
        description: Descrição adicional

    Returns:
        String formatada com guia de troubleshooting
    """
    if problem_type not in TROUBLESHOOT_STEPS:
        types_list = "\n".join(f"- `{t}`: {info['title']}" for t, info in TROUBLESHOOT_STEPS.items())
        return f"""# Troubleshooting Guide

Por favor, selecione um tipo de problema:

{types_list}

**Exemplo:** `troubleshoot problem_type="device_offline"`
"""

    guide = TROUBLESHOOT_STEPS[problem_type]

    response = f"""# 🔧 Troubleshooting: {guide['title']}

**Problema:** {guide['description']}
"""

    if description:
        response += f"\n**Contexto adicional:** {description}\n"

    response += "\n## Passos de Diagnóstico\n\n"
    for step in guide['steps']:
        response += f"{step}\n"

    response += "\n## Comandos Úteis\n\n```\n"
    for cmd in guide['commands']:
        response += f"{cmd}\n"
    response += "```\n"

    response += """
## Próximos Passos

1. Execute os comandos acima para coletar informações
2. Analise os resultados
3. Se o problema persistir, escale para suporte Meraki

**Precisa de ajuda com algum passo específico?**
"""

    return response


# Prompt schema para MCP
PROMPT_SCHEMA = {
    "name": "troubleshoot",
    "description": "Guided troubleshooting for common Meraki network issues. Provides step-by-step diagnosis and relevant MCP commands.",
    "arguments": [
        {
            "name": "problem_type",
            "description": "Type of problem: device_offline (device not responding), slow_network (performance issues), connectivity (can't access resources), wireless (WiFi issues), security (suspected breach)",
            "required": False,
        },
        {
            "name": "description",
            "description": "Additional context about the issue (e.g., 'started yesterday', 'affects building A')",
            "required": False,
        },
    ],
}
