#!/usr/bin/env python3
"""
Exemplo de uso do modulo scripts.report

Demonstra:
- Criacao de reports usando ReportBuilder
- Geracao de HTML e PDF
- Templates pre-definidos
"""

import sys
from pathlib import Path

# Adicionar scripts ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.report import (
    ReportBuilder,
    ReportType,
    save_html,
    render_pdf,
    dict_to_html_table,
    format_issue_html,
)


def example_custom_report():
    """Exemplo de report customizado usando builder."""
    print("\n=== Exemplo 1: Report Customizado ===\n")

    # Dados de exemplo
    devices_data = [
        {"Nome": "Switch-Core-01", "Status": "Online", "IP": "10.0.0.1"},
        {"Nome": "Switch-Core-02", "Status": "Online", "IP": "10.0.0.2"},
        {"Nome": "AP-Floor1-01", "Status": "Offline", "IP": "10.0.1.10"},
        {"Nome": "MX-Gateway", "Status": "Alerting", "IP": "10.0.0.254"},
    ]

    issues_data = [
        {
            "type": "device_offline",
            "severity": "high",
            "message": "1 device offline detectado",
        },
        {
            "type": "device_alerting",
            "severity": "medium",
            "message": "1 device em estado de alerta",
        },
    ]

    # Criar report
    report = (
        ReportBuilder("Analise Mensal - Janeiro 2024", ReportType.CUSTOM, "exemplo-corp")
        .add_summary(
            """
            Relatorio mensal da rede Meraki mostrando o estado atual dos devices
            e identificando problemas que necessitam atencao.
            """
        )
        .add_section("Visao Geral", "<p>Total de <strong>4 devices</strong> na rede.</p>")
        .add_section("Devices", dict_to_html_table(devices_data))
        .add_section(
            "Problemas",
            "<ul>" + "".join(f"<li>{format_issue_html(i)}</li>" for i in issues_data) + "</ul>",
        )
        .build()
    )

    # Salvar
    html_path = save_html(report)
    print(f"✓ HTML salvo: {html_path}")

    pdf_path = render_pdf(report)
    if pdf_path:
        print(f"✓ PDF salvo: {pdf_path}")
    else:
        print("⚠ PDF nao gerado (WeasyPrint nao instalado)")

    return report


def example_discovery_report():
    """Exemplo de report de discovery (simulado)."""
    print("\n=== Exemplo 2: Discovery Report (Simulado) ===\n")

    # Simular discovery result
    from datetime import datetime
    from scripts.discovery import (
        DiscoveryResult,
        NetworkInfo,
        DeviceInfo,
    )

    networks = [
        NetworkInfo(
            id="N_123",
            name="Filial-SP",
            organization_id="ORG_456",
            product_types=["switch", "wireless", "appliance"],
            tags=["producao"],
        ),
    ]

    devices = [
        DeviceInfo(
            serial="Q2XX-AAAA-BBBB",
            name="Switch-Core",
            model="MS350-24",
            network_id="N_123",
            status="online",
            lan_ip="10.0.0.1",
        ),
        DeviceInfo(
            serial="Q2XX-CCCC-DDDD",
            name="AP-01",
            model="MR46",
            network_id="N_123",
            status="offline",
            lan_ip="10.0.1.10",
        ),
    ]

    discovery = DiscoveryResult(
        timestamp=datetime.now(),
        org_id="ORG_456",
        org_name="Exemplo Corp",
        networks=networks,
        devices=devices,
        configurations={},
        issues=[
            {
                "type": "devices_offline",
                "severity": "high",
                "message": "1 device offline",
                "count": 1,
            }
        ],
        suggestions=[
            {
                "issue_type": "devices_offline",
                "priority": "high",
                "action": "Verificar conectividade do AP-01",
                "description": "Access Point esta offline ha mais de 24h",
            }
        ],
    )

    # Gerar report
    from scripts.report import generate_discovery_report

    report = generate_discovery_report(discovery, "exemplo-corp")

    # Salvar
    html_path = save_html(report)
    print(f"✓ HTML salvo: {html_path}")

    pdf_path = render_pdf(report)
    if pdf_path:
        print(f"✓ PDF salvo: {pdf_path}")
    else:
        print("⚠ PDF nao gerado (WeasyPrint nao instalado)")

    return report


def example_compliance_report():
    """Exemplo de report de compliance."""
    print("\n=== Exemplo 3: Compliance Report ===\n")

    from scripts.report import generate_compliance_report

    # Dados de compliance
    checks = [
        {
            "name": "SSID com WPA2/WPA3",
            "status": "pass",
            "description": "Todos os SSIDs usam autenticacao segura",
        },
        {
            "name": "Firewall rules definidas",
            "status": "pass",
            "description": "Regras de firewall configuradas corretamente",
        },
        {
            "name": "Devices atualizados",
            "status": "fail",
            "description": "2 devices com firmware desatualizado",
        },
        {
            "name": "Backup de configuracao",
            "status": "pass",
            "description": "Backup automatico habilitado",
        },
    ]

    report = generate_compliance_report("exemplo-corp", checks)

    # Salvar
    html_path = save_html(report)
    print(f"✓ HTML salvo: {html_path}")

    pdf_path = render_pdf(report)
    if pdf_path:
        print(f"✓ PDF salvo: {pdf_path}")
    else:
        print("⚠ PDF nao gerado (WeasyPrint nao instalado)")

    return report


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("EXEMPLOS DE USO DO MODULO scripts.report")
    print("=" * 60)

    # Executar exemplos
    example_custom_report()
    example_discovery_report()
    example_compliance_report()

    print("\n" + "=" * 60)
    print("Exemplos concluidos!")
    print("=" * 60 + "\n")

    print("Para visualizar os reports gerados:")
    print("  cd clients/exemplo-corp/reports/")
    print("  open *.html")
    print()
