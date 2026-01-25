"""
CLI principal do Meraki Workflow.

Uso:
    meraki --help
    meraki profiles list
    meraki discover --client acme --save
    meraki config ssid --network N_123 --number 0 --name "Guest"
    meraki workflow create --template device-offline --client acme
    meraki report discovery --client acme --pdf
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Imports dos modulos do projeto
from .api import MerakiClient
from .auth import (
    CredentialsNotFoundError,
    InvalidProfileError,
    list_profiles,
    load_profile,
    setup_credentials_interactive,
    validate_credentials,
)
from .changelog import ChangeType, log_change
from .config import (
    ConfigAction,
    add_firewall_rule,
    configure_ssid,
    create_vlan,
)
from .discovery import (
    compare_snapshots,
    full_discovery,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)
from .report import (
    ReportType,
    generate_changes_report,
    generate_discovery_report,
    render_pdf,
    save_html,
)
from .workflow import (
    create_device_offline_handler,
    create_firmware_compliance_check,
    create_scheduled_report,
    create_security_alert_handler,
    list_workflows,
    save_workflow,
)

console = Console()
logger = logging.getLogger(__name__)


# ==================== CLI Root ====================


@click.group()
@click.option("--debug/--no-debug", default=False, help="Ativar modo debug")
@click.option("--profile", "-p", default="default", help="Profile de credenciais")
@click.pass_context
def cli(ctx, debug, profile):
    """Meraki Workflow - Automacao de redes via linguagem natural."""
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["PROFILE"] = profile

    # Configurar logging
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")


# ==================== PROFILES ====================


@cli.group()
def profiles():
    """Gerenciar profiles de credenciais."""
    pass


@profiles.command("list")
def profiles_list():
    """Lista profiles disponiveis."""
    profs = list_profiles()

    if not profs:
        console.print("[yellow]Nenhum profile encontrado[/yellow]")
        console.print("\nCrie um profile com: meraki profiles setup")
        return

    table = Table(title="Profiles Meraki")
    table.add_column("Nome", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Organizacoes")

    for p in profs:
        try:
            profile = load_profile(p)
            valid, msg = validate_credentials(profile)
            if valid:
                status = "✓ Valido"
                # Extrair numero de orgs da mensagem
                orgs = msg.split("Acesso a ")[-1] if "Acesso a" in msg else "-"
            else:
                status = "✗ Invalido"
                orgs = "-"
        except Exception:
            status = "✗ Erro"
            orgs = "-"

        table.add_row(p, status, orgs)

    console.print(table)


@profiles.command("validate")
@click.argument("name", default="default")
def profiles_validate(name):
    """Valida um profile especifico."""
    try:
        profile = load_profile(name)
        valid, msg = validate_credentials(profile)

        if valid:
            console.print(f"[green]✓ Profile '{name}' valido![/green]")
            console.print(f"  {msg}")
        else:
            console.print(f"[red]✗ Profile '{name}' invalido[/red]")
            console.print(f"  {msg}")
    except (CredentialsNotFoundError, InvalidProfileError) as e:
        console.print(f"[red]Erro: {e}[/red]")


@profiles.command("setup")
def profiles_setup():
    """Setup interativo de credenciais."""
    try:
        setup_credentials_interactive()
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelado[/yellow]")
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


# ==================== DISCOVER ====================


@cli.group()
def discover():
    """Executar discovery de rede."""
    pass


@discover.command("full")
@click.option("--client", "-c", required=True, help="Nome do cliente")
@click.option("--save/--no-save", default=True, help="Salvar snapshot")
@click.pass_context
def discover_full(ctx, client, save):
    """Discovery completo da rede."""
    profile = ctx.obj["PROFILE"]

    try:
        with console.status("[bold green]Executando discovery..."):
            api = MerakiClient(profile)
            result = full_discovery(api.org_id, api)

        # Exibir resumo
        console.print(
            Panel(
                f"""[bold]Discovery Completo[/bold]

Organizacao: {result.org_name}
Networks: {len(result.networks)}
Devices: {len(result.devices)}
Issues: {len(result.issues)}
Sugestoes: {len(result.suggestions)}
""",
                title="Resultado",
            )
        )

        # Issues
        if result.issues:
            table = Table(title="Issues Encontrados")
            table.add_column("Tipo", style="red")
            table.add_column("Severidade")
            table.add_column("Detalhes")

            for issue in result.issues:
                table.add_row(
                    issue.get("type", ""),
                    issue.get("severity", ""),
                    str(issue.get("count", "")),
                )
            console.print(table)

        # Salvar
        if save:
            path = save_snapshot(result, client)
            console.print(f"\n[green]Snapshot salvo em: {path}[/green]")

            # Log no changelog
            log_change(
                client=client,
                change_type=ChangeType.DISCOVERY,
                action="full_discovery",
                details={
                    "networks": len(result.networks),
                    "devices": len(result.devices),
                    "issues": len(result.issues),
                },
            )

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        if ctx.obj["DEBUG"]:
            raise


@discover.command("list")
@click.option("--client", "-c", required=True, help="Nome do cliente")
def discover_list(client):
    """Lista snapshots existentes."""
    snapshots = list_snapshots(client)

    if not snapshots:
        console.print("[yellow]Nenhum snapshot encontrado[/yellow]")
        return

    table = Table(title=f"Snapshots - {client}")
    table.add_column("Arquivo", style="cyan")
    table.add_column("Data")
    table.add_column("Tamanho")

    for s in snapshots:
        # Extrair data do nome do arquivo
        parts = s.stem.split("_")
        date_str = parts[-2] if len(parts) >= 2 else "-"
        time_str = parts[-1] if len(parts) >= 1 else ""

        # Formatar data
        if date_str != "-" and len(date_str) == 8:
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            if len(time_str) == 6:
                formatted_date += f" {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        else:
            formatted_date = "-"

        # Tamanho do arquivo
        size_kb = s.stat().st_size / 1024
        size_str = f"{size_kb:.1f} KB"

        table.add_row(s.name, formatted_date, size_str)

    console.print(table)


@discover.command("compare")
@click.option("--client", "-c", required=True, help="Nome do cliente")
@click.option("--old", required=True, help="Snapshot antigo (nome do arquivo)")
@click.option("--new", required=True, help="Snapshot novo (nome do arquivo)")
def discover_compare(client, old, new):
    """Compara dois snapshots."""
    try:
        # Carregar snapshots
        base_path = Path("clients") / client / "discovery"
        old_snapshot = load_snapshot(base_path / old)
        new_snapshot = load_snapshot(base_path / new)

        # Comparar
        diff = compare_snapshots(old_snapshot, new_snapshot)

        # Exibir resultados
        console.print(Panel(f"[bold]Comparacao de Snapshots[/bold]", title="Analise"))

        if diff.get("devices_added"):
            console.print("\n[green]Devices Adicionados:[/green]")
            for dev in diff["devices_added"]:
                console.print(f"  + {dev['name']} ({dev['serial']})")

        if diff.get("devices_removed"):
            console.print("\n[red]Devices Removidos:[/red]")
            for dev in diff["devices_removed"]:
                console.print(f"  - {dev['name']} ({dev['serial']})")

        if diff.get("networks_added"):
            console.print(f"\n[green]Networks Adicionadas: {len(diff['networks_added'])}[/green]")

        if diff.get("networks_removed"):
            console.print(f"\n[red]Networks Removidas: {len(diff['networks_removed'])}[/red]")

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


# ==================== CONFIG ====================


@cli.group()
def config():
    """Aplicar configuracoes na rede."""
    pass


@config.command("ssid")
@click.option("--network", "-n", required=True, help="Network ID")
@click.option("--number", required=True, type=int, help="Numero do SSID (0-14)")
@click.option("--name", help="Nome do SSID")
@click.option("--enabled/--disabled", default=None, help="Habilitar/desabilitar")
@click.option(
    "--auth",
    type=click.Choice(["open", "psk", "8021x-meraki", "8021x-radius"]),
    help="Modo auth",
)
@click.option("--psk", help="Pre-shared key (para auth=psk)")
@click.option("--vlan", type=int, help="VLAN ID")
@click.option("--client-name", "-c", required=True, help="Nome do cliente")
@click.pass_context
def config_ssid(ctx, network, number, name, enabled, auth, psk, vlan, client_name):
    """Configurar um SSID wireless."""
    try:
        result = configure_ssid(
            network_id=network,
            ssid_number=number,
            name=name,
            enabled=enabled,
            auth_mode=auth,
            psk=psk,
            vlan_id=vlan,
            client_name=client_name,
        )

        if result.success:
            console.print(f"[green]✓ {result.message}[/green]")
            if result.backup_path:
                console.print(f"  Backup: {result.backup_path}")

            # Log no changelog
            log_change(
                client=client_name,
                change_type=ChangeType.CONFIG,
                action=f"ssid_{result.action.value}",
                details={
                    "network_id": network,
                    "ssid_number": number,
                    "changes": result.changes,
                },
            )
        else:
            console.print(f"[red]✗ {result.error or result.message}[/red]")

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        if ctx.obj["DEBUG"]:
            raise


@config.command("firewall")
@click.option("--network", "-n", required=True, help="Network ID")
@click.option(
    "--policy", type=click.Choice(["allow", "deny"]), required=True, help="Politica"
)
@click.option(
    "--protocol",
    type=click.Choice(["tcp", "udp", "icmp", "any"]),
    required=True,
    help="Protocolo",
)
@click.option("--src", default="any", help="Source CIDR")
@click.option("--dest", default="any", help="Destination CIDR")
@click.option("--port", default="any", help="Destination port")
@click.option("--comment", help="Comentario da regra")
@click.option("--client-name", "-c", required=True, help="Nome do cliente")
@click.pass_context
def config_firewall(ctx, network, policy, protocol, src, dest, port, comment, client_name):
    """Adicionar regra de firewall L3."""
    try:
        result = add_firewall_rule(
            network_id=network,
            policy=policy,
            protocol=protocol,
            src_cidr=src,
            dest_cidr=dest,
            dest_port=port,
            comment=comment,
            client_name=client_name,
        )

        if result.success:
            console.print(f"[green]✓ {result.message}[/green]")

            # Log no changelog
            log_change(
                client=client_name,
                change_type=ChangeType.CONFIG,
                action="firewall_rule_add",
                details={
                    "network_id": network,
                    "rule": {
                        "policy": policy,
                        "protocol": protocol,
                        "src": src,
                        "dest": dest,
                        "port": port,
                    },
                },
            )
        else:
            console.print(f"[red]✗ {result.error or result.message}[/red]")

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        if ctx.obj["DEBUG"]:
            raise


@config.command("vlan")
@click.option("--network", "-n", required=True, help="Network ID")
@click.option("--vlan-id", required=True, type=int, help="VLAN ID")
@click.option("--name", required=True, help="Nome da VLAN")
@click.option("--subnet", required=True, help="Subnet (ex: 192.168.10.0/24)")
@click.option("--gateway", required=True, help="Gateway IP")
@click.option("--client-name", "-c", required=True, help="Nome do cliente")
@click.pass_context
def config_vlan(ctx, network, vlan_id, name, subnet, gateway, client_name):
    """Criar uma nova VLAN."""
    try:
        result = create_vlan(
            network_id=network,
            vlan_id=vlan_id,
            name=name,
            subnet=subnet,
            appliance_ip=gateway,
            client_name=client_name,
        )

        if result.success:
            console.print(f"[green]✓ {result.message}[/green]")

            # Log no changelog
            log_change(
                client=client_name,
                change_type=ChangeType.CONFIG,
                action="vlan_create",
                details={
                    "network_id": network,
                    "vlan_id": vlan_id,
                    "name": name,
                    "subnet": subnet,
                },
            )
        else:
            console.print(f"[red]✗ {result.error or result.message}[/red]")

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        if ctx.obj["DEBUG"]:
            raise


# ==================== WORKFLOW ====================


@cli.group()
def workflow():
    """Gerenciar workflows de automacao."""
    pass


@workflow.command("create")
@click.option(
    "--template",
    "-t",
    type=click.Choice(
        ["device-offline", "firmware-compliance", "security-alert", "scheduled-report"]
    ),
    required=True,
    help="Template de workflow",
)
@click.option("--client", "-c", required=True, help="Nome do cliente")
@click.option("--slack-channel", default="#network-alerts", help="Canal Slack")
@click.option("--email", multiple=True, help="Emails para notificacao")
@click.pass_context
def workflow_create(ctx, template, client, slack_channel, email):
    """Criar workflow a partir de template."""
    try:
        # Criar workflow baseado no template
        if template == "device-offline":
            wf = create_device_offline_handler(slack_channel=slack_channel)
        elif template == "firmware-compliance":
            wf = create_firmware_compliance_check(
                target_version="MX 18.1", email_recipients=list(email) or ["admin@example.com"]
            )
        elif template == "security-alert":
            wf = create_security_alert_handler(
                slack_channel=slack_channel, email_recipients=list(email)
            )
        elif template == "scheduled-report":
            wf = create_scheduled_report(
                report_type="weekly", email_recipients=list(email) or ["admin@example.com"]
            )
        else:
            console.print(f"[yellow]Template '{template}' sera implementado em breve[/yellow]")
            return

        # Salvar workflow
        path = save_workflow(wf, client)
        console.print(f"[green]✓ Workflow criado: {path}[/green]")
        console.print("\n[yellow]Lembre-se: Importe o JSON no Dashboard Meraki[/yellow]")
        console.print("  Dashboard > Organization > Configure > Workflows\n")

        # Log no changelog
        log_change(
            client=client,
            change_type=ChangeType.WORKFLOW,
            action="workflow_create",
            details={"template": template, "name": wf.name},
        )

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        if ctx.obj["DEBUG"]:
            raise


@workflow.command("list")
@click.option("--client", "-c", required=True, help="Nome do cliente")
def workflow_list(client):
    """Lista workflows do cliente."""
    workflows = list_workflows(client)

    if not workflows:
        console.print("[yellow]Nenhum workflow encontrado[/yellow]")
        return

    table = Table(title=f"Workflows - {client}")
    table.add_column("Nome", style="cyan")
    table.add_column("Tamanho")

    for w in workflows:
        wf_path = Path("clients") / client / "workflows" / w
        size_kb = wf_path.stat().st_size / 1024 if wf_path.exists() else 0
        table.add_row(w, f"{size_kb:.1f} KB")

    console.print(table)


# ==================== REPORT ====================


@cli.group()
def report():
    """Gerar relatorios para clientes."""
    pass


@report.command("discovery")
@click.option("--client", "-c", required=True, help="Nome do cliente")
@click.option("--pdf/--html", default=False, help="Gerar PDF (requer WeasyPrint)")
@click.pass_context
def report_discovery(ctx, client, pdf):
    """Gerar relatorio de discovery."""
    profile = ctx.obj["PROFILE"]

    try:
        with console.status("[bold green]Gerando relatorio..."):
            # Executar discovery
            api = MerakiClient(profile)
            discovery = full_discovery(api.org_id, api)

            # Gerar report
            rep = generate_discovery_report(discovery, client)

            # Salvar HTML
            html_path = save_html(rep)
            console.print(f"[green]✓ HTML salvo: {html_path}[/green]")

            # Gerar PDF se solicitado
            if pdf:
                pdf_path = render_pdf(rep)
                if pdf_path:
                    console.print(f"[green]✓ PDF salvo: {pdf_path}[/green]")
                else:
                    console.print(
                        "[yellow]PDF nao gerado (WeasyPrint nao instalado)[/yellow]"
                    )

            # Log no changelog
            log_change(
                client=client,
                change_type=ChangeType.REPORT,
                action="report_discovery",
                details={"format": "pdf" if pdf else "html"},
            )

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        if ctx.obj["DEBUG"]:
            raise


@report.command("changes")
@click.option("--client", "-c", required=True, help="Nome do cliente")
@click.option("--days", default=30, help="Dias para incluir")
@click.pass_context
def report_changes(ctx, client, days):
    """Gerar relatorio de mudancas."""
    from datetime import datetime, timedelta

    try:
        from_date = datetime.now() - timedelta(days=days)
        rep = generate_changes_report(client, from_date=from_date)

        path = save_html(rep)
        console.print(f"[green]✓ Relatorio salvo: {path}[/green]")

        # Log no changelog
        log_change(
            client=client,
            change_type=ChangeType.REPORT,
            action="report_changes",
            details={"days": days},
        )

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        if ctx.obj["DEBUG"]:
            raise


# ==================== CLIENT ====================


@cli.group()
def client():
    """Gerenciar clientes."""
    pass


@client.command("new")
@click.argument("name")
@click.option("--profile", "-p", help="Profile de credenciais a usar")
def client_new(name, profile):
    """Criar estrutura para novo cliente."""
    base = Path("clients") / name

    if base.exists():
        console.print(f"[yellow]Cliente '{name}' ja existe em {base}[/yellow]")
        return

    # Criar diretorios
    (base / "discovery").mkdir(parents=True, exist_ok=True)
    (base / "workflows").mkdir(exist_ok=True)
    (base / "reports").mkdir(exist_ok=True)
    (base / "backups").mkdir(exist_ok=True)

    # Criar .env
    env_content = f"MERAKI_PROFILE={profile or 'default'}\n"
    (base / ".env").write_text(env_content)

    # Criar changelog inicial
    changelog = base / "changelog.md"
    changelog_content = f"""# Changelog - {name}

> Historico de mudancas

---

## {datetime.now().strftime('%Y-%m-%d')} - Cliente criado

**Acao:** Inicializacao
**Detalhes:**
- Profile: {profile or 'default'}
- Estrutura de diretorios criada
"""
    changelog.write_text(changelog_content)

    # Criar .gitignore
    gitignore = base / ".gitignore"
    gitignore.write_text("*.env\n*.env.local\n.DS_Store\n")

    console.print(f"[green]✓ Cliente '{name}' criado em {base}[/green]")
    console.print("\nEstrutura criada:")
    console.print(f"  {base}/")
    console.print(f"  ├── discovery/")
    console.print(f"  ├── workflows/")
    console.print(f"  ├── reports/")
    console.print(f"  ├── backups/")
    console.print(f"  ├── .env")
    console.print(f"  └── changelog.md")


@client.command("list")
def client_list():
    """Lista clientes existentes."""
    clients_dir = Path("clients")

    if not clients_dir.exists():
        console.print("[yellow]Nenhum cliente encontrado[/yellow]")
        console.print("\nCrie um cliente com: meraki client new <nome>")
        return

    table = Table(title="Clientes")
    table.add_column("Nome", style="cyan")
    table.add_column("Profile")
    table.add_column("Snapshots")
    table.add_column("Workflows")

    found_clients = False
    for c in clients_dir.iterdir():
        if c.is_dir() and not c.name.startswith("."):
            found_clients = True

            # Ler profile
            env_file = c / ".env"
            profile = "-"
            if env_file.exists():
                for line in env_file.read_text().split("\n"):
                    if line.startswith("MERAKI_PROFILE="):
                        profile = line.split("=")[1].strip()

            # Contar arquivos
            snapshots = (
                len(list((c / "discovery").glob("*.json")))
                if (c / "discovery").exists()
                else 0
            )
            workflows = (
                len(list((c / "workflows").glob("*.json")))
                if (c / "workflows").exists()
                else 0
            )

            table.add_row(c.name, profile, str(snapshots), str(workflows))

    if found_clients:
        console.print(table)
    else:
        console.print("[yellow]Nenhum cliente encontrado[/yellow]")
        console.print("\nCrie um cliente com: meraki client new <nome>")


@client.command("info")
@click.argument("name")
def client_info(name):
    """Exibe informacoes sobre um cliente."""
    base = Path("clients") / name

    if not base.exists():
        console.print(f"[red]Cliente '{name}' nao encontrado[/red]")
        return

    # Carregar .env
    env_file = base / ".env"
    profile = "default"
    if env_file.exists():
        for line in env_file.read_text().split("\n"):
            if line.startswith("MERAKI_PROFILE="):
                profile = line.split("=")[1].strip()

    # Contar arquivos
    snapshots = list((base / "discovery").glob("*.json")) if (base / "discovery").exists() else []
    workflows = list((base / "workflows").glob("*.json")) if (base / "workflows").exists() else []
    reports = list((base / "reports").glob("*.html")) if (base / "reports").exists() else []
    backups = list((base / "backups").glob("*.json")) if (base / "backups").exists() else []

    # Exibir info
    console.print(Panel(f"[bold]{name}[/bold]", title="Cliente"))
    console.print(f"\n[cyan]Profile:[/cyan] {profile}")
    console.print(f"[cyan]Path:[/cyan] {base}")
    console.print(f"\n[cyan]Snapshots:[/cyan] {len(snapshots)}")
    console.print(f"[cyan]Workflows:[/cyan] {len(workflows)}")
    console.print(f"[cyan]Reports:[/cyan] {len(reports)}")
    console.print(f"[cyan]Backups:[/cyan] {len(backups)}")

    # Ultimo snapshot
    if snapshots:
        latest = max(snapshots, key=lambda p: p.stat().st_mtime)
        console.print(f"\n[cyan]Ultimo snapshot:[/cyan] {latest.name}")


# ==================== Entry Point ====================


def main():
    """Entry point para o CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Operacao cancelada pelo usuario[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Erro fatal: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
