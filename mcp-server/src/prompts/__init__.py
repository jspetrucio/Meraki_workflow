"""
MCP Prompts para Meraki Workflow.

Prompts disponíveis:
- onboarding: Guia de setup inicial
- select_agent: Seleção de agente especializado
- troubleshoot: Diagnóstico guiado de problemas
"""

from .onboarding import onboarding_prompt, PROMPT_SCHEMA as ONBOARDING_SCHEMA
from .select_agent import select_agent_prompt, get_agent_recommendation, PROMPT_SCHEMA as SELECT_AGENT_SCHEMA
from .troubleshoot import troubleshoot_prompt, get_troubleshoot_guide, format_troubleshoot_response, PROMPT_SCHEMA as TROUBLESHOOT_SCHEMA

__all__ = [
    # Prompts
    "onboarding_prompt",
    "select_agent_prompt",
    "troubleshoot_prompt",
    # Helpers
    "get_agent_recommendation",
    "get_troubleshoot_guide",
    "format_troubleshoot_response",
    # Schemas
    "ONBOARDING_SCHEMA",
    "SELECT_AGENT_SCHEMA",
    "TROUBLESHOOT_SCHEMA",
    "ALL_PROMPT_SCHEMAS",
]

# Lista de todos os schemas para facilitar registro
ALL_PROMPT_SCHEMAS = [
    ONBOARDING_SCHEMA,
    SELECT_AGENT_SCHEMA,
    TROUBLESHOOT_SCHEMA,
]
