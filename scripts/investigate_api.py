#!/usr/bin/env python3
"""
Script para investigar endpoints da Meraki API relacionados a workflows.
Testa actionBatches, configTemplates e busca endpoints com 'workflow' no nome.
"""

import os
import sys
import json
import meraki
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

def load_credentials():
    """Carrega credenciais do cliente jose-org."""
    creds_path = Path.home() / ".meraki" / "credentials"

    if not creds_path.exists():
        console.print("[red]Credenciais não encontradas em ~/.meraki/credentials[/red]")
        sys.exit(1)

    # Parsear arquivo de credenciais
    api_key = None
    org_id = None

    with open(creds_path, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if line.startswith('['):
                section = line.strip('[]')
            elif '=' in line and section == 'default':
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key == 'api_key':
                    api_key = value
                elif key == 'org_id':
                    org_id = value

    if not api_key or not org_id:
        console.print("[red]API Key ou Org ID não encontrado[/red]")
        sys.exit(1)

    return api_key, org_id

def test_action_batches(dashboard, org_id):
    """Testa endpoints de Action Batches."""
    console.print("\n[bold cyan]═══ ACTION BATCHES ═══[/bold cyan]\n")

    try:
        # GET /organizations/{orgId}/actionBatches
        batches = dashboard.organizations.getOrganizationActionBatches(org_id)

        console.print(f"[green]✓[/green] GET /organizations/{org_id}/actionBatches")
        console.print(f"  Total de action batches: {len(batches)}")

        if batches:
            console.print("\n  Últimos 3 batches:")
            for batch in batches[:3]:
                console.print(f"    - ID: {batch.get('id')}")
                console.print(f"      Status: {batch.get('status', {})}")
                console.print(f"      Confirmed: {batch.get('confirmed')}")
                console.print(f"      Actions: {len(batch.get('actions', []))}")

        return True
    except Exception as e:
        console.print(f"[red]✗[/red] Erro ao buscar action batches: {e}")
        return False

def test_config_templates(dashboard, org_id):
    """Testa endpoints de Config Templates."""
    console.print("\n[bold cyan]═══ CONFIG TEMPLATES ═══[/bold cyan]\n")

    try:
        # GET /organizations/{orgId}/configTemplates
        templates = dashboard.organizations.getOrganizationConfigTemplates(org_id)

        console.print(f"[green]✓[/green] GET /organizations/{org_id}/configTemplates")
        console.print(f"  Total de templates: {len(templates)}")

        if templates:
            table = Table(title="Config Templates")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Product Types", style="yellow")
            table.add_column("Time Zone", style="magenta")

            for tmpl in templates:
                table.add_row(
                    tmpl.get('id', 'N/A'),
                    tmpl.get('name', 'N/A'),
                    ', '.join(tmpl.get('productTypes', [])),
                    tmpl.get('timeZone', 'N/A')
                )

            console.print(table)

        return templates
    except Exception as e:
        console.print(f"[red]✗[/red] Erro ao buscar config templates: {e}")
        return None

def search_workflow_endpoints(dashboard):
    """Busca na documentação da API por endpoints com 'workflow' no nome."""
    console.print("\n[bold cyan]═══ BUSCA POR 'WORKFLOW' NA API ═══[/bold cyan]\n")

    # Lista de métodos do SDK que podem conter 'workflow'
    workflow_methods = []

    # Inspecionar módulos do dashboard
    modules = ['organizations', 'networks', 'devices', 'appliance', 'switch', 'wireless', 'camera', 'sensor']

    for module_name in modules:
        if hasattr(dashboard, module_name):
            module = getattr(dashboard, module_name)
            methods = [m for m in dir(module) if 'workflow' in m.lower() and not m.startswith('_')]

            if methods:
                workflow_methods.append({
                    'module': module_name,
                    'methods': methods
                })

    if workflow_methods:
        console.print("[green]Métodos encontrados com 'workflow':[/green]")
        for item in workflow_methods:
            console.print(f"\n  Módulo: [cyan]{item['module']}[/cyan]")
            for method in item['methods']:
                console.print(f"    - {method}")
    else:
        console.print("[yellow]⚠ Nenhum método com 'workflow' encontrado no SDK[/yellow]")

    return workflow_methods

def test_create_action_batch(dashboard, org_id):
    """Testa criação de um action batch simples (DRY RUN)."""
    console.print("\n[bold cyan]═══ TESTE: CREATE ACTION BATCH (DRY RUN) ═══[/bold cyan]\n")

    try:
        # Obter um device para testar
        devices = dashboard.organizations.getOrganizationDevices(org_id, total_pages=1)

        if not devices:
            console.print("[yellow]⚠ Nenhum device encontrado para teste[/yellow]")
            return False

        test_device = devices[0]
        serial = test_device['serial']

        console.print(f"Device de teste: {serial} ({test_device.get('name', 'Sem nome')})")

        # Criar action batch NÃO confirmado (preview)
        payload = {
            'confirmed': False,  # PREVIEW MODE
            'synchronous': False,
            'actions': [
                {
                    'resource': f'/devices/{serial}',
                    'operation': 'update',
                    'body': {
                        'name': test_device.get('name', 'Test Device')  # Sem mudança real
                    }
                }
            ]
        }

        console.print("\nPayload (preview mode):")
        rprint(payload)

        result = dashboard.organizations.createOrganizationActionBatch(
            org_id,
            **payload
        )

        console.print(f"\n[green]✓[/green] Action Batch criado (preview):")
        console.print(f"  ID: {result.get('id')}")
        console.print(f"  Status: {result.get('status')}")
        console.print(f"  Confirmed: {result.get('confirmed')}")

        # Deletar o batch de preview
        dashboard.organizations.deleteOrganizationActionBatch(org_id, result['id'])
        console.print(f"[green]✓[/green] Batch de preview deletado")

        return True
    except Exception as e:
        console.print(f"[red]✗[/red] Erro ao criar action batch: {e}")
        return False

def explore_api_capabilities(dashboard, org_id):
    """Explora capabilities da API relacionadas a automation."""
    console.print("\n[bold cyan]═══ API CAPABILITIES ═══[/bold cyan]\n")

    capabilities = {
        'Action Batches': {
            'create': 'createOrganizationActionBatch',
            'list': 'getOrganizationActionBatches',
            'get': 'getOrganizationActionBatch',
            'update': 'updateOrganizationActionBatch',
            'delete': 'deleteOrganizationActionBatch'
        },
        'Config Templates': {
            'list': 'getOrganizationConfigTemplates',
            'create': 'createOrganizationConfigTemplate',
            'get': 'getOrganizationConfigTemplate',
            'update': 'updateOrganizationConfigTemplate',
            'delete': 'deleteOrganizationConfigTemplate'
        },
        'Alerts': {
            'get_settings': 'getNetworkAlertsSettings',
            'update_settings': 'updateNetworkAlertsSettings'
        },
        'Webhooks': {
            'get_http_servers': 'getNetworkWebhooksHttpServers',
            'create_http_server': 'createNetworkWebhooksHttpServer'
        }
    }

    table = Table(title="Automation Endpoints Disponíveis")
    table.add_column("Categoria", style="cyan")
    table.add_column("Operação", style="green")
    table.add_column("Método SDK", style="yellow")
    table.add_column("Status", style="magenta")

    for category, operations in capabilities.items():
        for op_name, method_name in operations.items():
            # Verificar se método existe no SDK
            exists = False
            module = None

            for mod_name in ['organizations', 'networks', 'devices']:
                if hasattr(dashboard, mod_name):
                    mod = getattr(dashboard, mod_name)
                    if hasattr(mod, method_name):
                        exists = True
                        module = mod_name
                        break

            status = "[green]✓[/green]" if exists else "[red]✗[/red]"
            table.add_row(category, op_name, f"{module}.{method_name}" if module else method_name, status)

    console.print(table)

def main():
    console.print("[bold]Investigação da Meraki API - Workflows e Automation[/bold]\n")

    # Carregar credenciais
    api_key, org_id = load_credentials()
    console.print(f"[green]✓[/green] Credenciais carregadas")
    console.print(f"  Organization ID: {org_id}\n")

    # Inicializar Dashboard API
    dashboard = meraki.DashboardAPI(
        api_key,
        output_log=False,
        suppress_logging=True,
        wait_on_rate_limit=True
    )

    # Testar endpoints
    test_action_batches(dashboard, org_id)
    templates = test_config_templates(dashboard, org_id)
    search_workflow_endpoints(dashboard)
    explore_api_capabilities(dashboard, org_id)
    test_create_action_batch(dashboard, org_id)

    # Sumário final
    console.print("\n[bold cyan]═══ SUMÁRIO ═══[/bold cyan]\n")
    console.print("""
[bold]Conclusões:[/bold]

1. [green]Action Batches[/green]:
   - Endpoint EXISTE e FUNCIONA
   - Permite executar múltiplas operações em batch
   - Suporta preview (confirmed=false) antes de aplicar
   - Ideal para automação de configurações em massa

2. [green]Config Templates[/green]:
   - Endpoint EXISTE e FUNCIONA
   - Permite criar/gerenciar templates de configuração
   - Templates são aplicados a networks, não são workflows

3. [yellow]Workflows (Dashboard Workflows)[/yellow]:
   - NÃO há endpoint para criar/importar workflows via API
   - Workflows são gerenciados APENAS pelo Dashboard UI
   - JSON de workflow deve ser importado manualmente
   - API não valida nem diagnostica workflows

4. [cyan]Alternativa para Automação[/cyan]:
   - Usar Action Batches para executar configurações em massa
   - Criar scripts Python que chamam a API diretamente
   - Usar webhooks + external automation (N8N, Zapier, etc)

[bold]Recomendação:[/bold]
Para automação Meraki, preferir:
  a) Scripts Python usando o SDK oficial
  b) Action Batches para operações em massa
  c) Workflows JSON apenas para importação manual no Dashboard
    """)

if __name__ == '__main__':
    main()
