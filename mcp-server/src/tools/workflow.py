"""
MCP Tool: meraki_create_workflow

Cria workflows Meraki a partir de templates usando Clone + Patch.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Adicionar path do projeto para imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


async def meraki_create_workflow(
    template: str,
    client: str,
    name: str,
    description: Optional[str] = None,
    variables: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Cria novo workflow Meraki a partir de template (Clone + Patch).

    Usa o sistema de templates em templates/workflows/ para criar
    workflows customizados com IDs únicos.

    Args:
        template: Nome do template (ex: "Device Offline Handler")
        client: Nome do cliente (salva em clients/{client}/workflows/)
        name: Nome do novo workflow
        description: Descrição do workflow (opcional)
        variables: Dicionário de variáveis a substituir (opcional)

    Returns:
        dict com resultado:
        {
            "success": bool,
            "workflow_name": str,
            "template_used": str,
            "output_path": str,
            "variables_set": dict,
            "import_instructions": str
        }

    Example:
        result = await meraki_create_workflow(
            template="Device Offline Handler",
            client="acme",
            name="ACME - Device Offline Alert",
            description="Alerta customizado para ACME",
            variables={"webhook_body": '{"channel": "#acme-alerts"}'}
        )
    """
    try:
        # Import do template loader
        from scripts.template_loader import (
            TemplateLoader,
            create_workflow_from_template,
            TemplateNotFoundError,
        )

        logger.info(f"Creating workflow '{name}' from template '{template}'")

        # Listar templates disponíveis para referência
        loader = TemplateLoader()
        available_templates = [t.name for t in loader.list_templates()]

        # Verificar se template existe
        if template not in available_templates:
            # Tentar match parcial
            matches = [t for t in available_templates if template.lower() in t.lower()]
            if matches:
                return {
                    "success": False,
                    "error": f"Template '{template}' not found",
                    "suggestion": f"Did you mean: {matches[0]}?",
                    "available_templates": available_templates,
                }
            return {
                "success": False,
                "error": f"Template '{template}' not found",
                "available_templates": available_templates,
            }

        # Criar workflow usando o template loader
        output_path = create_workflow_from_template(
            template_name=template,
            client=client,
            workflow_name=name,
            description=description,
            variables=variables,
        )

        # Instruções de import
        import_instructions = f"""
Para importar o workflow no Meraki Dashboard:

1. Acesse: https://dashboard.meraki.com
2. Vá em: Organization > Configure > Workflows
3. Clique em: Import Workflow
4. Selecione o arquivo: {output_path}
5. Revise as configurações e ative o workflow

Arquivo gerado: {output_path}
"""

        return {
            "success": True,
            "workflow_name": name,
            "template_used": template,
            "output_path": str(output_path),
            "variables_set": variables or {},
            "import_instructions": import_instructions.strip(),
        }

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {
            "success": False,
            "error": f"Module import failed: {e}",
            "hint": "Ensure scripts/template_loader.py exists",
        }

    except Exception as e:
        logger.error(f"Workflow creation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


async def meraki_list_workflow_templates() -> dict[str, Any]:
    """
    Lista templates de workflow disponíveis.

    Returns:
        dict com lista de templates:
        {
            "success": bool,
            "templates_count": int,
            "templates": [
                {
                    "name": str,
                    "description": str,
                    "variables": list,
                    "actions_count": int
                },
                ...
            ]
        }
    """
    try:
        from scripts.template_loader import TemplateLoader

        loader = TemplateLoader()
        templates = loader.list_templates()

        return {
            "success": True,
            "templates_count": len(templates),
            "templates": [
                {
                    "name": t.name,
                    "description": t.description[:100] + "..." if len(t.description) > 100 else t.description,
                    "variables": t.variables,
                    "actions_count": t.actions_count,
                }
                for t in templates
            ],
        }

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Schema para MCP
TOOL_SCHEMA = {
    "name": "meraki_create_workflow",
    "description": "Create a new Meraki workflow from a template using Clone + Patch. Generates unique IDs and saves to client folder.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "template": {
                "type": "string",
                "description": "Template name (e.g., 'Device Offline Handler'). Use meraki_list_workflow_templates to see available templates.",
            },
            "client": {
                "type": "string",
                "description": "Client name for organizing output (saves to clients/{client}/workflows/)",
            },
            "name": {
                "type": "string",
                "description": "Name for the new workflow",
            },
            "description": {
                "type": "string",
                "description": "Description for the workflow (optional)",
            },
            "variables": {
                "type": "object",
                "description": "Variables to set in the workflow (optional). Keys are variable names, values are the values to set.",
            },
        },
        "required": ["template", "client", "name"],
    },
}
