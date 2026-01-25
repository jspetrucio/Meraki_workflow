#!/usr/bin/env python3
"""
CLI para executar discovery de redes Meraki.

Uso:
    # Discovery simples
    python scripts/cli_discovery.py

    # Discovery de cliente específico
    python scripts/cli_discovery.py --client cliente-acme

    # Salvar snapshot
    python scripts/cli_discovery.py --client cliente-acme --save

    # Comparar com snapshot anterior
    python scripts/cli_discovery.py --client cliente-acme --compare

    # Apenas exibir issues
    python scripts/cli_discovery.py --issues-only

    # Debug mode
    python scripts/cli_discovery.py --debug
"""

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from scripts.discovery import (
    full_discovery,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    compare_snapshots,
)
from scripts.api import get_client

console = Console()


def setup_logging(debug: bool = False):
    """Configura logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def display_summary(result):
    """Exibe resumo do discovery."""
    summary = result.summary()

    console.print(
        Panel.fit(
            f"[bold]{summary['organization']}[/bold]\n"
            f"Timestamp: {summary['timestamp']}\n\n"
            f"[cyan]Networks:[/cyan] {summary['networks_count']}\n"
            f"[cyan]Devices:[/cyan] {summary['devices_count']}\n"
            f"[cyan]Issues:[/cyan] {summary['issues_count']}",
            title="Discovery Summary",
            border_style="green",
        )
    )


def display_issues_table(result):
    """Exibe issues em formato de tabela."""
    if not result.issues:
        console.print("\n[green]Nenhum issue encontrado![/green]\n")
        return

    table = Table(title="Issues Encontrados", box=box.ROUNDED)
    table.add_column("Severidade", style="bold")
    table.add_column("Tipo")
    table.add_column("Mensagem")
    table.add_column("Qtd", justify="right")

    for issue in result.issues:
        severity = issue["severity"]
        severity_color = {
            "high": "red",
            "medium": "yellow",
            "low": "blue",
        }.get(severity, "white")

        table.add_row(
            f"[{severity_color}]{severity.upper()}[/{severity_color}]",
            issue["type"],
            issue["message"],
            str(issue["count"]),
        )

    console.print()
    console.print(table)
    console.print()


def display_suggestions(result):
    """Exibe sugestões."""
    if not result.suggestions:
        return

    console.print("[bold]Sugestões:[/bold]\n")

    for i, suggestion in enumerate(result.suggestions, 1):
        priority = suggestion["priority"]
        priority_color = {
            "high": "red",
            "medium": "yellow",
            "low": "blue",
        }.get(priority, "white")

        automated = "✓" if suggestion["automated"] else "✗"

        console.print(
            f"[{priority_color}]{i}. [{priority.upper()}][/{priority_color}] "
            f"{suggestion['action']} {automated}"
        )


def display_comparison(diff):
    """Exibe comparação entre snapshots."""
    console.print("\n[bold cyan]Comparação com Snapshot Anterior[/bold cyan]\n")

    changes = 0

    # Networks
    if diff["networks"]["added"]:
        console.print(f"[green]+ {len(diff['networks']['added'])} network(s) adicionada(s)[/green]")
        changes += len(diff["networks"]["added"])

    if diff["networks"]["removed"]:
        console.print(f"[red]- {len(diff['networks']['removed'])} network(s) removida(s)[/red]")
        changes += len(diff["networks"]["removed"])

    # Devices
    if diff["devices"]["added"]:
        console.print(f"[green]+ {len(diff['devices']['added'])} device(s) adicionado(s)[/green]")
        changes += len(diff["devices"]["added"])

    if diff["devices"]["removed"]:
        console.print(f"[red]- {len(diff['devices']['removed'])} device(s) removido(s)[/red]")
        changes += len(diff["devices"]["removed"])

    if diff["devices"]["changed_status"]:
        console.print(
            f"[yellow]~ {len(diff['devices']['changed_status'])} device(s) mudou de status[/yellow]"
        )
        changes += len(diff["devices"]["changed_status"])

        # Detalhar mudanças de status
        for dev in diff["devices"]["changed_status"]:
            old_color = "green" if dev["old_status"] == "online" else "red"
            new_color = "green" if dev["new_status"] == "online" else "red"
            console.print(
                f"  {dev['name']}: [{old_color}]{dev['old_status']}[/{old_color}] → "
                f"[{new_color}]{dev['new_status']}[/{new_color}]"
            )

    # Issues
    if diff["issues"]["resolved"]:
        console.print(f"[green]✓ {len(diff['issues']['resolved'])} issue(s) resolvido(s)[/green]")
        changes += len(diff["issues"]["resolved"])

    if diff["issues"]["new"]:
        console.print(f"[red]✗ {len(diff['issues']['new'])} novo(s) issue(s)[/red]")
        changes += len(diff["issues"]["new"])

    if changes == 0:
        console.print("[blue]Nenhuma mudança detectada[/blue]")

    console.print()


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Discovery de redes Meraki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                                    # Discovery simples
  %(prog)s --client cliente-acme --save       # Salvar snapshot
  %(prog)s --client cliente-acme --compare    # Comparar com anterior
  %(prog)s --issues-only                      # Apenas issues
        """,
    )

    parser.add_argument(
        "--client",
        help="Nome do cliente (para salvar snapshot)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Salvar snapshot do discovery",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Comparar com snapshot anterior",
    )
    parser.add_argument(
        "--issues-only",
        action="store_true",
        help="Exibir apenas issues",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativar modo debug",
    )

    args = parser.parse_args()

    # Setup
    setup_logging(args.debug)

    try:
        # Discovery
        console.print("\n[bold cyan]═══ Meraki Discovery ═══[/bold cyan]\n")

        with console.status("[bold green]Executando discovery..."):
            result = full_discovery()

        # Exibir resultados
        if not args.issues_only:
            display_summary(result)

        display_issues_table(result)

        if not args.issues_only:
            display_suggestions(result)

        # Salvar snapshot
        if args.save:
            if not args.client:
                console.print(
                    "[red]Erro:[/red] --client é obrigatório com --save"
                )
                sys.exit(1)

            console.print(f"\n[bold]Salvando snapshot para '{args.client}'...[/bold]")
            path = save_snapshot(result, args.client)
            console.print(f"[green]Snapshot salvo:[/green] {path}\n")

        # Comparar
        if args.compare:
            if not args.client:
                console.print(
                    "[red]Erro:[/red] --client é obrigatório com --compare"
                )
                sys.exit(1)

            snapshots = list_snapshots(args.client)

            if len(snapshots) < 2:
                console.print(
                    "[yellow]Aviso:[/yellow] Menos de 2 snapshots disponíveis "
                    "(sem comparação)\n"
                )
            else:
                old_snapshot = load_snapshot(snapshots[1])
                diff = compare_snapshots(old_snapshot, result)
                display_comparison(diff)

        console.print("[bold cyan]═══ Discovery Completo ═══[/bold cyan]\n")

        # Exit code baseado em issues
        if result.issues:
            high_issues = [i for i in result.issues if i["severity"] == "high"]
            if high_issues:
                sys.exit(2)  # Issues críticos
            else:
                sys.exit(1)  # Issues não-críticos
        else:
            sys.exit(0)  # Sem issues

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompido pelo usuário[/yellow]")
        sys.exit(130)

    except Exception as e:
        console.print(f"\n[bold red]Erro:[/bold red] {e}")
        if args.debug:
            logging.exception("Erro na execução")
        sys.exit(1)


if __name__ == "__main__":
    main()
