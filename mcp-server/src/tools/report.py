"""
MCP Tool: meraki_report

Gera relatórios HTML/PDF para clientes Meraki.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Literal, Optional

# Adicionar path do projeto para imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

ReportType = Literal["discovery", "changes", "inventory", "security"]
ReportFormat = Literal["html", "pdf"]


async def meraki_report(
    client: str,
    report_type: ReportType = "discovery",
    output_format: ReportFormat = "html",
    profile: str = "default",
    days: int = 30,
) -> dict[str, Any]:
    """
    Gera relatório para um cliente Meraki.

    Args:
        client: Nome do cliente
        report_type: Tipo de relatório
            - "discovery": Estado atual da rede
            - "changes": Mudanças recentes (usa days)
            - "inventory": Inventário de devices
            - "security": Análise de segurança
        output_format: Formato de saída ("html" ou "pdf")
        profile: Profile de credenciais (default: "default")
        days: Dias para incluir no relatório de changes (default: 30)

    Returns:
        dict com resultado:
        {
            "success": bool,
            "report_type": str,
            "output_path": str,
            "summary": {
                "org_name": str,
                "networks": int,
                "devices": int,
                "issues": int,
                ...
            }
        }

    Example:
        # Relatório de discovery
        result = await meraki_report(
            client="acme",
            report_type="discovery",
            output_format="html"
        )

        # Relatório de mudanças dos últimos 7 dias
        result = await meraki_report(
            client="acme",
            report_type="changes",
            days=7
        )
    """
    try:
        # Import dos módulos do projeto
        from scripts.api import MerakiClient
        from scripts.discovery import full_discovery
        from scripts.report import (
            generate_discovery_report,
            generate_changes_report,
            save_html,
            render_pdf,
        )
        from datetime import datetime, timedelta

        logger.info(f"Generating {report_type} report for client '{client}'")

        # Criar cliente API
        api = MerakiClient(profile)

        summary = {}
        output_path = None

        if report_type == "discovery":
            # Executar discovery e gerar relatório
            discovery = full_discovery(api.org_id, api)
            report = generate_discovery_report(discovery, client)

            summary = {
                "org_name": discovery.org_name,
                "networks": len(discovery.networks),
                "devices": len(discovery.devices),
                "devices_online": sum(1 for d in discovery.devices if d.get("status") == "online"),
                "issues": len(discovery.issues),
                "suggestions": len(discovery.suggestions),
            }

            # Salvar
            if output_format == "html":
                output_path = save_html(report)
            elif output_format == "pdf":
                pdf_path = render_pdf(report)
                output_path = pdf_path if pdf_path else save_html(report)
                if not pdf_path:
                    logger.warning("PDF generation failed, saved as HTML")

        elif report_type == "changes":
            # Relatório de mudanças
            from_date = datetime.now() - timedelta(days=days)
            report = generate_changes_report(client, from_date=from_date)

            summary = {
                "period_days": days,
                "from_date": from_date.isoformat(),
                "to_date": datetime.now().isoformat(),
            }

            output_path = save_html(report)

        elif report_type == "inventory":
            # Relatório de inventário
            discovery = full_discovery(api.org_id, api)

            # Agrupar por tipo de device
            device_types = {}
            for device in discovery.devices:
                model = device.get("model", "Unknown")
                device_type = model.split("-")[0] if "-" in model else model[:2]
                device_types[device_type] = device_types.get(device_type, 0) + 1

            summary = {
                "org_name": discovery.org_name,
                "total_devices": len(discovery.devices),
                "by_type": device_types,
                "networks": len(discovery.networks),
            }

            # Usar relatório de discovery como base
            report = generate_discovery_report(discovery, client)
            output_path = save_html(report)

        elif report_type == "security":
            # Relatório de segurança
            discovery = full_discovery(api.org_id, api)

            # Filtrar issues de segurança
            security_issues = [
                issue for issue in discovery.issues
                if issue.get("type") in ["security", "vulnerability", "compliance"]
                or "security" in issue.get("type", "").lower()
            ]

            summary = {
                "org_name": discovery.org_name,
                "total_issues": len(discovery.issues),
                "security_issues": len(security_issues),
                "severity_high": sum(1 for i in security_issues if i.get("severity") == "high"),
                "severity_medium": sum(1 for i in security_issues if i.get("severity") == "medium"),
                "severity_low": sum(1 for i in security_issues if i.get("severity") == "low"),
            }

            report = generate_discovery_report(discovery, client)
            output_path = save_html(report)

        else:
            return {
                "success": False,
                "error": f"Unknown report_type: {report_type}",
                "valid_types": ["discovery", "changes", "inventory", "security"],
            }

        return {
            "success": True,
            "report_type": report_type,
            "output_format": output_format,
            "output_path": str(output_path) if output_path else None,
            "summary": summary,
            "message": f"Report generated successfully: {output_path}",
        }

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {
            "success": False,
            "error": f"Module import failed: {e}",
            "hint": "Ensure scripts/ modules are properly installed",
        }

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


# Schema para MCP
TOOL_SCHEMA = {
    "name": "meraki_report",
    "description": "Generate reports for Meraki networks. Supports discovery, changes, inventory, and security reports in HTML or PDF format.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "client": {
                "type": "string",
                "description": "Client name for the report",
            },
            "report_type": {
                "type": "string",
                "enum": ["discovery", "changes", "inventory", "security"],
                "description": "Type of report to generate",
                "default": "discovery",
            },
            "output_format": {
                "type": "string",
                "enum": ["html", "pdf"],
                "description": "Output format (PDF requires WeasyPrint)",
                "default": "html",
            },
            "profile": {
                "type": "string",
                "description": "Credentials profile name",
                "default": "default",
            },
            "days": {
                "type": "integer",
                "description": "Days to include for changes report",
                "default": 30,
            },
        },
        "required": ["client"],
    },
}
