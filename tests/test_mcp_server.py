"""
Testes de integração para o MCP Server do Meraki Workflow.

Testa:
- Carregamento do servidor
- Registro de tools
- Registro de prompts
- Execução de tools (mocked)
- Execução de prompts
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
MCP_SERVER_PATH = PROJECT_ROOT / "mcp-server"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(MCP_SERVER_PATH))

# Import local - ajustar caminho para mcp-server/src
sys.path.insert(0, str(MCP_SERVER_PATH / "src"))


# ==================== Fixtures ====================


@pytest.fixture
def mock_mcp_sdk():
    """Mock do MCP SDK para testes sem dependência real."""
    with patch.dict('sys.modules', {
        'mcp': MagicMock(),
        'mcp.server': MagicMock(),
        'mcp.server.stdio': MagicMock(),
        'mcp.types': MagicMock(),
    }):
        yield


# ==================== Test Tool Schemas ====================


class TestToolSchemas:
    """Testa schemas das tools MCP."""

    def test_all_tool_schemas_exist(self):
        """Verifica que todas as 6 tools têm schemas."""
        from tools import ALL_TOOL_SCHEMAS

        assert len(ALL_TOOL_SCHEMAS) == 6

        tool_names = [t["name"] for t in ALL_TOOL_SCHEMAS]
        expected = [
            "meraki_discover",
            "meraki_list_networks",
            "meraki_configure",
            "meraki_create_workflow",
            "meraki_report",
            "meraki_get_device_status",
        ]

        for name in expected:
            assert name in tool_names, f"Tool {name} not found in schemas"

    def test_tool_schema_structure(self):
        """Verifica estrutura correta dos schemas."""
        from tools import ALL_TOOL_SCHEMAS

        for schema in ALL_TOOL_SCHEMAS:
            assert "name" in schema
            assert "description" in schema
            assert "inputSchema" in schema

            input_schema = schema["inputSchema"]
            assert input_schema.get("type") == "object"
            assert "properties" in input_schema

    def test_meraki_discover_schema(self):
        """Testa schema da tool meraki_discover."""
        from tools import DISCOVER_SCHEMA

        assert DISCOVER_SCHEMA["name"] == "meraki_discover"
        assert "client" in DISCOVER_SCHEMA["inputSchema"]["properties"]
        assert "client" in DISCOVER_SCHEMA["inputSchema"]["required"]

    def test_meraki_configure_schema(self):
        """Testa schema da tool meraki_configure."""
        from tools import CONFIGURE_SCHEMA

        assert CONFIGURE_SCHEMA["name"] == "meraki_configure"
        props = CONFIGURE_SCHEMA["inputSchema"]["properties"]
        assert "network_id" in props
        assert "config_type" in props
        assert "params" in props
        assert "client" in props

    def test_meraki_create_workflow_schema(self):
        """Testa schema da tool meraki_create_workflow."""
        from tools import WORKFLOW_SCHEMA

        assert WORKFLOW_SCHEMA["name"] == "meraki_create_workflow"
        props = WORKFLOW_SCHEMA["inputSchema"]["properties"]
        assert "template" in props
        assert "client" in props
        assert "name" in props


# ==================== Test Prompt Schemas ====================


class TestPromptSchemas:
    """Testa schemas dos prompts MCP."""

    def test_all_prompt_schemas_exist(self):
        """Verifica que todos os 3 prompts têm schemas."""
        from prompts import ALL_PROMPT_SCHEMAS

        assert len(ALL_PROMPT_SCHEMAS) == 3

        prompt_names = [p["name"] for p in ALL_PROMPT_SCHEMAS]
        expected = ["onboarding", "select_agent", "troubleshoot"]

        for name in expected:
            assert name in prompt_names, f"Prompt {name} not found"

    def test_prompt_schema_structure(self):
        """Verifica estrutura correta dos schemas de prompt."""
        from prompts import ALL_PROMPT_SCHEMAS

        for schema in ALL_PROMPT_SCHEMAS:
            assert "name" in schema
            assert "description" in schema
            assert "arguments" in schema
            assert isinstance(schema["arguments"], list)

    def test_onboarding_prompt_arguments(self):
        """Testa argumentos do prompt onboarding."""
        from prompts import ONBOARDING_SCHEMA

        args = {a["name"]: a for a in ONBOARDING_SCHEMA["arguments"]}
        assert "api_key" in args
        assert "org_id" in args
        assert "client_name" in args

        # Todos são obrigatórios
        for arg in ONBOARDING_SCHEMA["arguments"]:
            assert arg.get("required") == True

    def test_troubleshoot_prompt_arguments(self):
        """Testa argumentos do prompt troubleshoot."""
        from prompts import TROUBLESHOOT_SCHEMA

        args = {a["name"]: a for a in TROUBLESHOOT_SCHEMA["arguments"]}
        assert "problem_type" in args
        assert "description" in args


# ==================== Test Prompt Functions ====================


class TestPromptFunctions:
    """Testa funções auxiliares dos prompts."""

    def test_get_agent_recommendation_config(self):
        """Testa recomendação para tarefas de configuração."""
        from prompts import get_agent_recommendation

        # Config keywords
        assert get_agent_recommendation("configurar firewall") == "meraki-specialist"
        assert get_agent_recommendation("criar ACL") == "meraki-specialist"
        assert get_agent_recommendation("setup SSID") == "meraki-specialist"

    def test_get_agent_recommendation_analysis(self):
        """Testa recomendação para tarefas de análise."""
        from prompts import get_agent_recommendation

        assert get_agent_recommendation("analisar rede") == "network-analyst"
        assert get_agent_recommendation("discovery completo") == "network-analyst"
        assert get_agent_recommendation("diagnosticar problema") == "network-analyst"

    def test_get_agent_recommendation_workflow(self):
        """Testa recomendação para tarefas de workflow."""
        from prompts import get_agent_recommendation

        assert get_agent_recommendation("criar workflow") == "workflow-creator"
        assert get_agent_recommendation("automação de alertas") == "workflow-creator"

    def test_troubleshoot_guide_device_offline(self):
        """Testa guia de troubleshooting para device offline."""
        from prompts import get_troubleshoot_guide

        guide = get_troubleshoot_guide("device_offline")
        assert guide["title"] == "Device Offline"
        assert len(guide["steps"]) == 8
        assert len(guide["commands"]) >= 1

    def test_troubleshoot_guide_unknown_type(self):
        """Testa guia de troubleshooting para tipo desconhecido."""
        from prompts import get_troubleshoot_guide

        guide = get_troubleshoot_guide("unknown_type")
        assert "error" in guide
        assert "available_types" in guide

    def test_format_troubleshoot_response(self):
        """Testa formatação de resposta de troubleshooting."""
        from prompts import format_troubleshoot_response

        response = format_troubleshoot_response("slow_network", "Rede lenta desde ontem")

        assert "Rede Lenta" in response
        assert "Rede lenta desde ontem" in response
        assert "Passos de Diagnóstico" in response
        assert "Comandos Úteis" in response


# ==================== Test Tool Functions ====================


class TestToolFunctions:
    """Testa funções das tools."""

    @pytest.mark.asyncio
    async def test_meraki_discover_returns_dict(self):
        """Testa que meraki_discover retorna um dict."""
        from tools import meraki_discover

        with patch('tools.discovery.run_discovery') as mock:
            mock.return_value = {
                "success": True,
                "organization": {"name": "Test Org"},
                "summary": {"total_networks": 5}
            }

            result = await meraki_discover(client="test")
            assert isinstance(result, dict)
            assert "success" in result

    @pytest.mark.asyncio
    async def test_meraki_list_networks_returns_dict(self):
        """Testa que meraki_list_networks retorna um dict."""
        from tools import meraki_list_networks

        with patch('tools.network.get_networks') as mock:
            mock.return_value = {
                "success": True,
                "networks": [{"name": "Network 1"}]
            }

            result = await meraki_list_networks()
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_meraki_create_workflow_returns_dict(self):
        """Testa que meraki_create_workflow retorna um dict."""
        from tools import meraki_create_workflow

        with patch('tools.workflow.create_workflow_from_template') as mock:
            mock.return_value = {
                "success": True,
                "workflow_path": "/path/to/workflow.json"
            }

            result = await meraki_create_workflow(
                template="Device Offline Handler",
                client="test",
                name="Test Workflow"
            )
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_meraki_configure_dry_run(self):
        """Testa meraki_configure em modo dry_run."""
        from tools import meraki_configure

        with patch('tools.config.apply_config') as mock:
            mock.return_value = {
                "success": True,
                "dry_run": True,
                "changes": ["Would update SSID"]
            }

            result = await meraki_configure(
                network_id="N_123",
                config_type="ssid",
                params={"name": "Guest"},
                client="test",
                dry_run=True
            )
            assert result.get("dry_run") == True


# ==================== Test MCP Manifest ====================


class TestMCPManifest:
    """Testa o arquivo mcp.json."""

    def test_mcp_json_exists(self):
        """Verifica que mcp.json existe."""
        mcp_json_path = PROJECT_ROOT / "mcp-server" / "mcp.json"
        assert mcp_json_path.exists()

    def test_mcp_json_valid(self):
        """Verifica que mcp.json é JSON válido."""
        mcp_json_path = PROJECT_ROOT / "mcp-server" / "mcp.json"

        with open(mcp_json_path) as f:
            manifest = json.load(f)

        assert "name" in manifest
        assert manifest["name"] == "meraki-workflow"

    def test_mcp_json_has_6_tools(self):
        """Verifica que mcp.json tem 6 tools."""
        mcp_json_path = PROJECT_ROOT / "mcp-server" / "mcp.json"

        with open(mcp_json_path) as f:
            manifest = json.load(f)

        assert "tools" in manifest
        assert len(manifest["tools"]) == 6

    def test_mcp_json_has_3_prompts(self):
        """Verifica que mcp.json tem 3 prompts."""
        mcp_json_path = PROJECT_ROOT / "mcp-server" / "mcp.json"

        with open(mcp_json_path) as f:
            manifest = json.load(f)

        assert "prompts" in manifest
        assert len(manifest["prompts"]) == 3

    def test_mcp_json_tool_names_match(self):
        """Verifica que nomes das tools no manifest batem com código."""
        mcp_json_path = PROJECT_ROOT / "mcp-server" / "mcp.json"

        with open(mcp_json_path) as f:
            manifest = json.load(f)

        manifest_tools = {t["name"] for t in manifest["tools"]}
        expected_tools = {
            "meraki_discover",
            "meraki_list_networks",
            "meraki_configure",
            "meraki_create_workflow",
            "meraki_report",
            "meraki_get_device_status",
        }

        assert manifest_tools == expected_tools


# ==================== Test Claude Desktop Integration ====================


class TestClaudeDesktopIntegration:
    """Testa aspectos de integração com Claude Desktop."""

    def test_readme_exists(self):
        """Verifica que README.md existe no mcp-server."""
        readme_path = PROJECT_ROOT / "mcp-server" / "README.md"
        assert readme_path.exists()

    def test_readme_has_installation_instructions(self):
        """Verifica que README tem instruções de instalação."""
        readme_path = PROJECT_ROOT / "mcp-server" / "README.md"

        with open(readme_path) as f:
            content = f.read()

        assert "instalação" in content.lower() or "installation" in content.lower()
        assert "claude" in content.lower()
        assert "mcpServers" in content

    def test_server_entry_point_exists(self):
        """Verifica que entry point do server existe."""
        server_path = PROJECT_ROOT / "mcp-server" / "src" / "server.py"
        assert server_path.exists()

    def test_server_has_main_function(self):
        """Verifica que server.py tem função main."""
        server_path = PROJECT_ROOT / "mcp-server" / "src" / "server.py"

        with open(server_path) as f:
            content = f.read()

        assert "async def main()" in content
        assert "def run():" in content


# ==================== Run Tests ====================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
