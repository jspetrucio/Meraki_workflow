"""
Geracao de relatorios HTML e PDF para apresentacao aos clientes.

Este modulo fornece:
- Builders para criar relatorios customizados
- Templates HTML usando Jinja2
- Exportacao para PDF usando WeasyPrint
- Relatorios pre-definidos (discovery, changes, compliance, executive)
- Helpers para formatar dados em tabelas HTML

Uso:
    from scripts.report import ReportBuilder, ReportType, save_html, render_pdf

    # Usando builder
    report = (
        ReportBuilder("Analise de Rede", ReportType.DISCOVERY, "cliente-acme")
        .add_summary("Rede estavel com 3 issues menores")
        .add_section("Overview", "<p>Total de 5 networks</p>")
        .build()
    )

    html_path = save_html(report)
    pdf_path = render_pdf(report)

    # Usando templates pre-definidos
    from scripts.discovery import full_discovery

    discovery = full_discovery(org_id="123")
    report = generate_discovery_report(discovery, "cliente-acme")
    save_html(report)
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, Template

logger = logging.getLogger(__name__)


# ==================== Enums and Dataclasses ====================


class ReportType(Enum):
    """Tipos de relatorios disponiveis."""

    DISCOVERY = "discovery"
    CHANGES = "changes"
    COMPLIANCE = "compliance"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


@dataclass
class ReportSection:
    """
    Secao de um relatorio.

    Attributes:
        title: Titulo da secao
        content: Conteudo HTML
        data: Dados estruturados opcionais (dict)
    """

    title: str
    content: str = ""
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return asdict(self)


@dataclass
class Report:
    """
    Relatorio completo.

    Attributes:
        title: Titulo do relatorio
        report_type: Tipo do relatorio
        client_name: Nome do cliente
        generated_at: Data/hora de geracao
        sections: Lista de secoes
        summary: Sumario executivo (opcional)
        logo_path: Caminho para logo (opcional)
    """

    title: str
    report_type: ReportType
    client_name: str
    generated_at: datetime
    sections: list[ReportSection]
    summary: str = ""
    logo_path: Optional[Path] = None

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "title": self.title,
            "report_type": self.report_type.value,
            "client_name": self.client_name,
            "generated_at": self.generated_at.isoformat(),
            "sections": [s.to_dict() for s in self.sections],
            "summary": self.summary,
            "logo_path": str(self.logo_path) if self.logo_path else None,
        }


# ==================== Builder ====================


class ReportBuilder:
    """
    Builder para criar relatorios de forma fluente.

    Exemplo:
        report = (
            ReportBuilder("Titulo", ReportType.CUSTOM, "cliente")
            .add_summary("Resumo aqui")
            .add_section("Secao 1", "<p>Conteudo</p>")
            .build()
        )
    """

    def __init__(self, title: str, report_type: ReportType, client_name: str):
        """
        Inicializa o builder.

        Args:
            title: Titulo do relatorio
            report_type: Tipo do relatorio
            client_name: Nome do cliente
        """
        self._title = title
        self._report_type = report_type
        self._client_name = client_name
        self._sections: list[ReportSection] = []
        self._summary = ""
        self._logo_path: Optional[Path] = None

    def add_section(
        self, title: str, content: str = "", data: Optional[dict] = None
    ) -> "ReportBuilder":
        """
        Adiciona uma secao ao relatorio.

        Args:
            title: Titulo da secao
            content: Conteudo HTML
            data: Dados estruturados opcionais

        Returns:
            Self para chaining
        """
        section = ReportSection(title=title, content=content, data=data or {})
        self._sections.append(section)
        return self

    def add_summary(self, summary: str) -> "ReportBuilder":
        """
        Define o sumario executivo.

        Args:
            summary: Texto do sumario

        Returns:
            Self para chaining
        """
        self._summary = summary
        return self

    def set_logo(self, logo_path: Path) -> "ReportBuilder":
        """
        Define o caminho para o logo.

        Args:
            logo_path: Path para o arquivo de logo

        Returns:
            Self para chaining
        """
        self._logo_path = logo_path
        return self

    def build(self) -> Report:
        """
        Constroi e retorna o relatorio.

        Returns:
            Report configurado
        """
        return Report(
            title=self._title,
            report_type=self._report_type,
            client_name=self._client_name,
            generated_at=datetime.now(),
            sections=self._sections,
            summary=self._summary,
            logo_path=self._logo_path,
        )


# ==================== Templates ====================

DEFAULT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report.title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            margin: 0;
            padding: 40px;
            background: #f8f9fa;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 3px solid #3498db;
            margin-bottom: 30px;
        }

        .header-logo img {
            height: 50px;
        }

        .header-info {
            text-align: right;
            color: #7f8c8d;
            font-size: 0.9em;
        }

        h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }

        h2 {
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.8em;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }

        h3 {
            color: #34495e;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 1.3em;
        }

        .client-name {
            color: #7f8c8d;
            font-size: 1.1em;
            margin-bottom: 30px;
        }

        .summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 30px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .summary h3 {
            color: white;
            margin-top: 0;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 10px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 3px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        th, td {
            border: 1px solid #e1e8ed;
            padding: 12px 15px;
            text-align: left;
        }

        th {
            background-color: #3498db;
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }

        tr:nth-child(even) {
            background-color: #f8f9fa;
        }

        tr:hover {
            background-color: #e3f2fd;
            transition: background-color 0.3s ease;
        }

        .issue-high {
            color: #e74c3c;
            font-weight: bold;
        }

        .issue-medium {
            color: #f39c12;
            font-weight: bold;
        }

        .issue-low {
            color: #3498db;
        }

        .status-online {
            color: #27ae60;
            font-weight: 600;
        }

        .status-offline {
            color: #e74c3c;
            font-weight: 600;
        }

        .status-alerting {
            color: #f39c12;
            font-weight: 600;
        }

        .status-dormant {
            color: #95a5a6;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-success {
            background-color: #d4edda;
            color: #155724;
        }

        .badge-danger {
            background-color: #f8d7da;
            color: #721c24;
        }

        .badge-warning {
            background-color: #fff3cd;
            color: #856404;
        }

        .badge-info {
            background-color: #d1ecf1;
            color: #0c5460;
        }

        .footer {
            margin-top: 60px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #95a5a6;
            font-size: 0.9em;
        }

        .section {
            margin-bottom: 40px;
        }

        p {
            margin-bottom: 15px;
            line-height: 1.8;
        }

        ul, ol {
            margin-left: 25px;
            margin-bottom: 15px;
        }

        li {
            margin-bottom: 8px;
        }

        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        pre {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
        }

        .metric-card {
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: 700;
            color: #3498db;
        }

        .metric-label {
            color: #7f8c8d;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }

            .container {
                box-shadow: none;
                padding: 20px;
            }

            .header {
                page-break-after: avoid;
            }

            h2 {
                page-break-after: avoid;
            }

            table {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-logo">
                {% if report.logo_path %}
                <img src="{{ report.logo_path }}" alt="Logo">
                {% endif %}
            </div>
            <div class="header-info">
                <div>Gerado em: {{ report.generated_at.strftime('%d/%m/%Y %H:%M') }}</div>
                <div>Tipo: {{ report.report_type.value }}</div>
            </div>
        </div>

        <h1>{{ report.title }}</h1>
        <p class="client-name"><strong>Cliente:</strong> {{ report.client_name }}</p>

        {% if report.summary %}
        <div class="summary">
            <h3>Resumo Executivo</h3>
            <div>{{ report.summary }}</div>
        </div>
        {% endif %}

        {% for section in report.sections %}
        <div class="section">
            <h2>{{ section.title }}</h2>
            {{ section.content | safe }}
        </div>
        {% endfor %}

        <div class="footer">
            <p>Relatorio gerado automaticamente pelo <strong>Meraki Workflow</strong></p>
            <p>Powered by Cisco Meraki Dashboard API</p>
        </div>
    </div>
</body>
</html>
"""


# ==================== HTML Rendering ====================


def get_template_path() -> Path:
    """
    Retorna o path do diretorio de templates.

    Returns:
        Path do diretorio templates/
    """
    return Path(__file__).parent.parent / "templates"


def render_html(report: Report, template_name: str = "default") -> str:
    """
    Renderiza report para HTML usando Jinja2.

    Args:
        report: Report a renderizar
        template_name: Nome do template ("default" usa template embutido)

    Returns:
        String HTML renderizada
    """
    logger.debug(f"Renderizando report '{report.title}' com template '{template_name}'")

    if template_name == "default":
        template = Template(DEFAULT_HTML_TEMPLATE)
    else:
        # Carregar template de arquivo
        template_path = get_template_path() / f"{template_name}.html.j2"
        if not template_path.exists():
            logger.warning(
                f"Template '{template_name}' nao encontrado, usando default"
            )
            template = Template(DEFAULT_HTML_TEMPLATE)
        else:
            with open(template_path, "r") as f:
                template = Template(f.read())

    # Renderizar
    html = template.render(report=report)
    logger.debug(f"HTML renderizado com sucesso ({len(html)} chars)")

    return html


def get_report_dir(client_name: str) -> Path:
    """
    Retorna o diretorio de reports para um cliente.

    Args:
        client_name: Nome do cliente

    Returns:
        Path do diretorio reports/
    """
    report_dir = Path("clients") / client_name / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def save_html(report: Report, output_path: Optional[Path] = None) -> Path:
    """
    Salva report como HTML.

    Args:
        report: Report a salvar
        output_path: Path de output (se None, gera automaticamente)

    Returns:
        Path do arquivo salvo
    """
    if output_path is None:
        # Gerar path automatico
        report_dir = get_report_dir(report.client_name)
        timestamp_str = report.generated_at.strftime("%Y-%m-%d")
        filename = f"{report.report_type.value}_{timestamp_str}.html"
        output_path = report_dir / filename

    logger.info(f"Salvando report HTML em {output_path}")

    # Renderizar HTML
    html = render_html(report)

    # Salvar
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Report salvo com sucesso")

    return output_path


def render_pdf(report: Report, output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Renderiza report para PDF usando WeasyPrint.

    Args:
        report: Report a renderizar
        output_path: Path de output (se None, gera automaticamente)

    Returns:
        Path do arquivo salvo ou None se WeasyPrint nao disponivel
    """
    # Verificar se WeasyPrint esta disponivel
    try:
        from weasyprint import HTML
    except ImportError:
        logger.warning(
            "WeasyPrint nao disponivel. Instale com: pip install weasyprint"
        )
        return None

    if output_path is None:
        # Gerar path automatico
        report_dir = get_report_dir(report.client_name)
        timestamp_str = report.generated_at.strftime("%Y-%m-%d")
        filename = f"{report.report_type.value}_{timestamp_str}.pdf"
        output_path = report_dir / filename

    logger.info(f"Renderizando report para PDF em {output_path}")

    # Renderizar HTML
    html = render_html(report)

    # Converter para PDF
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=html).write_pdf(output_path)
        logger.info(f"PDF gerado com sucesso")
        return output_path

    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        return None


def list_reports(client_name: str) -> list[Path]:
    """
    Lista todos os reports existentes de um cliente.

    Args:
        client_name: Nome do cliente

    Returns:
        Lista de paths de reports (HTML e PDF)
    """
    report_dir = get_report_dir(client_name)

    if not report_dir.exists():
        return []

    # Buscar arquivos HTML e PDF
    reports = sorted(
        list(report_dir.glob("*.html")) + list(report_dir.glob("*.pdf")),
        reverse=True,
    )

    return reports


# ==================== HTML Helpers ====================


def dict_to_html_table(data: list[dict], headers: Optional[list[str]] = None) -> str:
    """
    Converte lista de dicts para tabela HTML.

    Args:
        data: Lista de dicionarios
        headers: Headers customizados (se None, usa keys do primeiro dict)

    Returns:
        String HTML com a tabela
    """
    if not data:
        return "<p>Nenhum dado disponivel</p>"

    # Determinar headers
    if headers is None:
        headers = list(data[0].keys())

    # Construir tabela
    html = ["<table>", "<thead>", "<tr>"]

    for header in headers:
        html.append(f"<th>{header}</th>")

    html.extend(["</tr>", "</thead>", "<tbody>"])

    # Linhas
    for row in data:
        html.append("<tr>")
        for header in headers:
            value = row.get(header, "")
            html.append(f"<td>{value}</td>")
        html.append("</tr>")

    html.extend(["</tbody>", "</table>"])

    return "".join(html)


def format_issue_html(issue: dict) -> str:
    """
    Formata um issue com cor baseada em severidade.

    Args:
        issue: Dict com dados do issue

    Returns:
        String HTML formatada
    """
    severity = issue.get("severity", "unknown")
    issue_type = issue.get("type", "unknown")
    message = issue.get("message", "")

    severity_class = f"issue-{severity}"

    return f'<span class="{severity_class}">[{severity.upper()}]</span> {message}'


def format_device_status_html(device: dict) -> str:
    """
    Formata status de device com classe CSS apropriada.

    Args:
        device: Dict com dados do device

    Returns:
        String HTML formatada
    """
    status = device.get("status", "unknown")
    status_class = f"status-{status}"

    status_labels = {
        "online": "Online",
        "offline": "Offline",
        "alerting": "Em Alerta",
        "dormant": "Dormant",
    }

    label = status_labels.get(status, status.capitalize())

    return f'<span class="{status_class}">{label}</span>'


# ==================== Pre-defined Reports ====================


def generate_discovery_report(
    discovery_result,  # DiscoveryResult from scripts.discovery
    client_name: str,
    include_issues: bool = True,
    include_suggestions: bool = True,
) -> Report:
    """
    Gera relatorio de discovery da rede.

    Args:
        discovery_result: Resultado do discovery (DiscoveryResult)
        client_name: Nome do cliente
        include_issues: Se deve incluir secao de issues
        include_suggestions: Se deve incluir secao de sugestoes

    Returns:
        Report configurado
    """
    from .discovery import DiscoveryResult

    # Type hint para IDE
    discovery: DiscoveryResult = discovery_result

    logger.info(f"Gerando discovery report para {client_name}")

    # Criar builder
    builder = ReportBuilder(
        f"Relatorio de Discovery - {discovery.org_name}",
        ReportType.DISCOVERY,
        client_name,
    )

    # Summary
    summary_data = discovery.summary()
    summary_text = f"""
    <p><strong>Organizacao:</strong> {summary_data['organization']}</p>
    <p><strong>Data do Discovery:</strong> {summary_data['timestamp']}</p>
    <p><strong>Networks:</strong> {summary_data['networks_count']}</p>
    <p><strong>Devices:</strong> {summary_data['devices_count']}</p>
    <p><strong>Issues Encontrados:</strong> {summary_data['issues_count']}</p>
    """
    builder.add_summary(summary_text)

    # Secao: Overview
    devices_by_status = summary_data["devices_by_status"]
    status_rows = [
        {"Status": status.capitalize(), "Quantidade": count}
        for status, count in devices_by_status.items()
    ]
    status_table = dict_to_html_table(status_rows)

    overview_html = f"""
    <h3>Resumo de Devices por Status</h3>
    {status_table}
    """
    builder.add_section("Visao Geral", overview_html)

    # Secao: Networks
    networks_data = [
        {
            "Nome": net.name,
            "ID": net.id,
            "Produtos": ", ".join(net.product_types),
            "Tags": ", ".join(net.tags) if net.tags else "-",
        }
        for net in discovery.networks
    ]
    networks_table = dict_to_html_table(networks_data)
    builder.add_section("Networks", networks_table)

    # Secao: Devices
    devices_data = [
        {
            "Nome": dev.name or "Sem nome",
            "Serial": dev.serial,
            "Modelo": dev.model,
            "Status": format_device_status_html({"status": dev.status}),
            "IP": dev.lan_ip or "-",
        }
        for dev in discovery.devices
    ]
    devices_table = dict_to_html_table(devices_data)
    builder.add_section("Devices", devices_table)

    # Secao: Issues
    if include_issues and discovery.issues:
        issues_html = ["<ul>"]
        for issue in discovery.issues:
            issues_html.append(f"<li>{format_issue_html(issue)}</li>")
        issues_html.append("</ul>")

        builder.add_section("Problemas Identificados", "".join(issues_html))

    # Secao: Sugestoes
    if include_suggestions and discovery.suggestions:
        suggestions_html = ["<ol>"]
        for suggestion in discovery.suggestions:
            priority = suggestion.get("priority", "medium")
            action = suggestion.get("action", "")
            description = suggestion.get("description", "")

            badge_class = (
                "badge-danger"
                if priority == "high"
                else "badge-warning"
                if priority == "medium"
                else "badge-info"
            )

            suggestions_html.append(
                f'<li><span class="badge {badge_class}">{priority}</span> '
                f'<strong>{action}</strong><br>{description}</li>'
            )
        suggestions_html.append("</ol>")

        builder.add_section("Recomendacoes", "".join(suggestions_html))

    return builder.build()


def generate_changes_report(
    client_name: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> Report:
    """
    Gera relatorio de mudancas (changelog).

    Args:
        client_name: Nome do cliente
        from_date: Data inicial (se None, ultimos 30 dias)
        to_date: Data final (se None, hoje)

    Returns:
        Report configurado
    """
    from datetime import timedelta

    logger.info(f"Gerando changes report para {client_name}")

    # Definir datas
    if to_date is None:
        to_date = datetime.now()

    if from_date is None:
        from_date = to_date - timedelta(days=30)

    # Criar builder
    builder = ReportBuilder(
        f"Relatorio de Mudancas - {client_name}",
        ReportType.CHANGES,
        client_name,
    )

    summary_text = f"""
    <p><strong>Periodo:</strong> {from_date.strftime('%d/%m/%Y')} a {to_date.strftime('%d/%m/%Y')}</p>
    """
    builder.add_summary(summary_text)

    # Ler changelog
    changelog_path = Path("clients") / client_name / "changelog.md"

    if not changelog_path.exists():
        builder.add_section(
            "Changelog", "<p>Nenhuma mudanca registrada ainda.</p>"
        )
    else:
        with open(changelog_path, "r") as f:
            changelog_content = f.read()

        # Converter markdown para HTML basico
        changelog_html = f"<pre>{changelog_content}</pre>"
        builder.add_section("Historico de Mudancas", changelog_html)

    return builder.build()


def generate_compliance_report(
    client_name: str, checks: list[dict]
) -> Report:
    """
    Gera relatorio de compliance.

    Args:
        client_name: Nome do cliente
        checks: Lista de checks com pass/fail

    Returns:
        Report configurado
    """
    logger.info(f"Gerando compliance report para {client_name}")

    # Criar builder
    builder = ReportBuilder(
        f"Relatorio de Compliance - {client_name}",
        ReportType.COMPLIANCE,
        client_name,
    )

    # Calcular estatisticas
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c.get("status") == "pass")
    failed_checks = total_checks - passed_checks

    compliance_rate = (
        (passed_checks / total_checks * 100) if total_checks > 0 else 0
    )

    summary_text = f"""
    <div class="metric-card">
        <div class="metric-value">{compliance_rate:.1f}%</div>
        <div class="metric-label">Taxa de Compliance</div>
    </div>
    <p><strong>Total de Checks:</strong> {total_checks}</p>
    <p><strong>Aprovados:</strong> {passed_checks}</p>
    <p><strong>Reprovados:</strong> {failed_checks}</p>
    """
    builder.add_summary(summary_text)

    # Tabela de checks
    checks_data = [
        {
            "Check": check.get("name", ""),
            "Status": (
                '<span class="badge badge-success">PASS</span>'
                if check.get("status") == "pass"
                else '<span class="badge badge-danger">FAIL</span>'
            ),
            "Descricao": check.get("description", ""),
        }
        for check in checks
    ]

    checks_table = dict_to_html_table(checks_data)
    builder.add_section("Resultados dos Checks", checks_table)

    return builder.build()


def generate_executive_summary(
    client_name: str,
    discovery_result=None,
    include_charts: bool = True,
) -> Report:
    """
    Gera sumario executivo para gestao.

    Args:
        client_name: Nome do cliente
        discovery_result: Resultado do discovery (opcional)
        include_charts: Se deve incluir graficos (ainda nao implementado)

    Returns:
        Report configurado
    """
    logger.info(f"Gerando executive summary para {client_name}")

    # Criar builder
    builder = ReportBuilder(
        f"Sumario Executivo - {client_name}",
        ReportType.EXECUTIVE,
        client_name,
    )

    if discovery_result:
        from .discovery import DiscoveryResult

        discovery: DiscoveryResult = discovery_result

        summary_data = discovery.summary()

        # Summary
        summary_text = f"""
        <h3>Status Geral da Rede</h3>
        <p>A rede Meraki do cliente {client_name} esta em operacao com
        {summary_data['networks_count']} networks e {summary_data['devices_count']} devices.</p>

        <p><strong>Nivel de Saude:</strong>
        {_calculate_health_status(discovery)}</p>

        <p><strong>Issues Criticos:</strong> {_count_critical_issues(discovery)}</p>
        """
        builder.add_summary(summary_text)

        # Metricas principais
        metrics_html = f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
            <div class="metric-card">
                <div class="metric-value">{summary_data['networks_count']}</div>
                <div class="metric-label">Networks</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary_data['devices_count']}</div>
                <div class="metric-label">Devices</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary_data['issues_count']}</div>
                <div class="metric-label">Issues</div>
            </div>
        </div>
        """
        builder.add_section("Metricas Principais", metrics_html)

        # Recomendacoes de alto nivel
        if discovery.suggestions:
            high_priority_suggestions = [
                s for s in discovery.suggestions if s.get("priority") == "high"
            ]

            if high_priority_suggestions:
                rec_html = ["<ol>"]
                for suggestion in high_priority_suggestions:
                    rec_html.append(f"<li>{suggestion.get('action', '')}</li>")
                rec_html.append("</ol>")

                builder.add_section(
                    "Recomendacoes Prioritarias", "".join(rec_html)
                )

    else:
        summary_text = "<p>Nenhum dado de discovery disponivel.</p>"
        builder.add_summary(summary_text)

    return builder.build()


def _calculate_health_status(discovery) -> str:
    """
    Calcula status de saude da rede baseado em issues.

    Args:
        discovery: DiscoveryResult

    Returns:
        String com status (Excelente, Bom, Atencao, Critico)
    """
    high_issues = sum(1 for i in discovery.issues if i.get("severity") == "high")
    medium_issues = sum(
        1 for i in discovery.issues if i.get("severity") == "medium"
    )

    if high_issues > 0:
        return '<span class="badge badge-danger">Requer Atencao</span>'
    elif medium_issues > 2:
        return '<span class="badge badge-warning">Bom com Ressalvas</span>'
    elif medium_issues > 0:
        return '<span class="badge badge-info">Bom</span>'
    else:
        return '<span class="badge badge-success">Excelente</span>'


def _count_critical_issues(discovery) -> int:
    """
    Conta issues criticos (severity = high).

    Args:
        discovery: DiscoveryResult

    Returns:
        Numero de issues criticos
    """
    return sum(1 for i in discovery.issues if i.get("severity") == "high")


# ==================== Main ====================

if __name__ == "__main__":
    import sys
    from rich.console import Console

    logging.basicConfig(level=logging.INFO)

    console = Console()

    # Teste com report customizado
    console.print("\n[bold]Testando Report Builder[/bold]\n")

    report = (
        ReportBuilder("Relatorio de Teste", ReportType.CUSTOM, "cliente-teste")
        .add_summary("Este e um relatorio de teste do sistema.")
        .add_section("Secao 1", "<p>Conteudo da primeira secao</p>")
        .add_section(
            "Secao 2",
            dict_to_html_table(
                [
                    {"Nome": "Device 1", "Status": "Online"},
                    {"Nome": "Device 2", "Status": "Offline"},
                ]
            ),
        )
        .build()
    )

    # Salvar HTML
    html_path = save_html(report)
    console.print(f"[green]HTML salvo em:[/green] {html_path}")

    # Tentar PDF
    pdf_path = render_pdf(report)
    if pdf_path:
        console.print(f"[green]PDF salvo em:[/green] {pdf_path}")
    else:
        console.print(
            "[yellow]PDF nao gerado (WeasyPrint nao disponivel)[/yellow]"
        )

    console.print("\n[bold green]Teste concluido![/bold green]\n")
