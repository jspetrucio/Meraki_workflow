"""
Meraki Workflow MCP Server.

Entry point para o servidor MCP que expõe funcionalidades do Meraki Workflow
para Claude Desktop e outros clientes MCP.

Uso:
    python -m mcp_server.src.server

    Ou via Claude Desktop config:
    {
        "mcpServers": {
            "meraki-workflow": {
                "command": "python",
                "args": ["-m", "mcp_server.src.server"],
                "cwd": "/path/to/Meraki_Workflow"
            }
        }
    }

Tools disponíveis (6):
    - meraki_discover: Discovery completo da rede
    - meraki_list_networks: Lista networks
    - meraki_configure: Aplica configurações
    - meraki_create_workflow: Cria workflow de template
    - meraki_report: Gera relatórios
    - meraki_get_device_status: Status de device

Prompts disponíveis (3):
    - onboarding: Setup inicial
    - select_agent: Escolha de agente
    - troubleshoot: Diagnóstico guiado
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("meraki-mcp")

# Adicionar path do projeto
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Tentar importar MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        GetPromptResult,
        Prompt,
        PromptArgument,
        PromptMessage,
        Resource,
        TextContent,
        Tool,
    )
    MCP_AVAILABLE = True
except ImportError:
    logger.warning("MCP SDK not installed. Run: pip install mcp")
    MCP_AVAILABLE = False

# Import dos tools
from .tools import (
    meraki_discover,
    meraki_list_networks,
    meraki_configure,
    meraki_create_workflow,
    meraki_report,
    meraki_get_device_status,
    ALL_TOOL_SCHEMAS,
)

# Import dos prompts
from .prompts import (
    get_agent_recommendation,
    get_troubleshoot_guide,
    format_troubleshoot_response,
    ALL_PROMPT_SCHEMAS,
)


# ==================== Server Setup ====================


def create_server() -> "Server":
    """Cria e configura o servidor MCP."""

    if not MCP_AVAILABLE:
        raise ImportError("MCP SDK not available. Install with: pip install mcp")

    server = Server("meraki-workflow")

    # ==================== Tools ====================

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Lista todas as tools disponíveis."""
        return [
            Tool(
                name=schema["name"],
                description=schema["description"],
                inputSchema=schema["inputSchema"],
            )
            for schema in ALL_TOOL_SCHEMAS
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Executa uma tool pelo nome."""
        logger.info(f"Calling tool: {name} with args: {list(arguments.keys())}")

        try:
            # Mapear nome para função
            tool_map = {
                "meraki_discover": meraki_discover,
                "meraki_list_networks": meraki_list_networks,
                "meraki_configure": meraki_configure,
                "meraki_create_workflow": meraki_create_workflow,
                "meraki_report": meraki_report,
                "meraki_get_device_status": meraki_get_device_status,
            }

            if name not in tool_map:
                result = {"error": f"Unknown tool: {name}", "available": list(tool_map.keys())}
            else:
                result = await tool_map[name](**arguments)

            # Formatar resultado como texto
            result_text = json.dumps(result, indent=2, ensure_ascii=False, default=str)

            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    # ==================== Prompts ====================

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """Lista prompts disponíveis."""
        return [
            Prompt(
                name=schema["name"],
                description=schema["description"],
                arguments=[
                    PromptArgument(
                        name=arg["name"],
                        description=arg["description"],
                        required=arg.get("required", False),
                    )
                    for arg in schema["arguments"]
                ],
            )
            for schema in ALL_PROMPT_SCHEMAS
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
        """Retorna um prompt pelo nome."""
        logger.info(f"Getting prompt: {name}")
        arguments = arguments or {}

        if name == "onboarding":
            # Prompt de onboarding
            api_key = arguments.get("api_key", "[não fornecido]")
            org_id = arguments.get("org_id", "[não fornecido]")
            client_name = arguments.get("client_name", "[não fornecido]")

            # Mascarar API key
            masked_key = '*' * 20 + api_key[-4:] if len(api_key) > 4 else '[não fornecido]'

            message = f"""# Setup Meraki Workflow

Vou configurar o ambiente com as seguintes informações:

- **API Key:** {masked_key}
- **Org ID:** {org_id}
- **Cliente:** {client_name}

## Próximos passos:

1. Configurar credenciais em `~/.meraki/credentials`
2. Criar estrutura em `clients/{client_name}/`
3. Executar discovery inicial
4. Gerar relatório HTML

Para continuar, execute:
```
meraki profiles setup
meraki client new {client_name}
meraki discover full -c {client_name}
meraki report discovery -c {client_name}
```
"""

            return GetPromptResult(
                description="Meraki Workflow onboarding setup",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=message),
                    )
                ],
            )

        elif name == "select_agent":
            # Prompt de seleção de agente
            task = arguments.get("task_description", "")

            if task:
                recommended = get_agent_recommendation(task)
                message = f"""# Seleção de Agente

**Sua tarefa:** {task}

**Agente recomendado:** `@{recommended}`

## Agentes Disponíveis

### 🔧 Meraki Specialist (`@meraki-specialist`)
Configuração via API: ACL, Firewall, SSID, VLAN, Switch, QoS

### 📊 Network Analyst (`@network-analyst`)
Discovery, análise de topologia, diagnóstico, comparação de snapshots

### 🔄 Workflow Creator (`@workflow-creator`)
Automações Meraki e N8N, alertas, compliance

**Para ativar:** Digite `@{recommended}` seguido da sua tarefa.
"""
            else:
                message = """# Seleção de Agente

## Agentes Disponíveis

### 🔧 Meraki Specialist (`@meraki-specialist`)
- Configurar ACL, Firewall, SSID, VLAN
- Gerenciar switches e câmeras
- Comandos: `*configure`, `*show-config`, `*backup`

### 📊 Network Analyst (`@network-analyst`)
- Discovery e análise de rede
- Identificar problemas e sugerir melhorias
- Comandos: `*discover`, `*analyze`, `*compare`

### 🔄 Workflow Creator (`@workflow-creator`)
- Criar automações e alertas
- Templates Meraki e N8N
- Comandos: `*create-workflow`, `*list-templates`

**Qual é sua tarefa?** Descreva o que você quer fazer e eu recomendarei o melhor agente.
"""

            return GetPromptResult(
                description="Agent selection guide",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=message),
                    )
                ],
            )

        elif name == "troubleshoot":
            # Prompt de troubleshooting
            problem_type = arguments.get("problem_type", "")
            description = arguments.get("description", "")

            message = format_troubleshoot_response(problem_type, description)

            return GetPromptResult(
                description="Guided troubleshooting",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=message),
                    )
                ],
            )

        else:
            raise ValueError(f"Unknown prompt: {name}")

    # ==================== Resources ====================

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """Lista recursos disponíveis (templates, docs, etc.)."""
        resources = []

        # Listar templates de workflow
        templates_dir = PROJECT_ROOT / "templates" / "workflows"
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                resources.append(
                    Resource(
                        uri=f"template://workflows/{template_file.name}",
                        name=template_file.stem,
                        description=f"Workflow template: {template_file.stem}",
                        mimeType="application/json",
                    )
                )

        # Listar agentes disponíveis
        agents_dir = PROJECT_ROOT / ".claude" / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                resources.append(
                    Resource(
                        uri=f"agent://{agent_file.stem}",
                        name=agent_file.stem,
                        description=f"Specialized agent: {agent_file.stem}",
                        mimeType="text/markdown",
                    )
                )

        return resources

    return server


# ==================== Main ====================


async def main():
    """Entry point do servidor MCP."""
    logger.info("Starting Meraki Workflow MCP Server v0.1.0...")
    logger.info(f"Tools: {len(ALL_TOOL_SCHEMAS)}, Prompts: {len(ALL_PROMPT_SCHEMAS)}")

    if not MCP_AVAILABLE:
        logger.error("MCP SDK not installed. Run: pip install mcp")
        sys.exit(1)

    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server running on stdio")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run():
    """Wrapper para executar o servidor."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
