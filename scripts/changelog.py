"""
Gestao de changelog de mudancas em clientes Meraki.

Registra todas as mudancas feitas na rede (discovery, configs, workflows)
e faz auto-commit no Git para rastreabilidade.

Formato do changelog:
    clients/{nome}/changelog.md - markdown estruturado

Uso:
    from scripts.changelog import log_change, auto_commit_change, ChangeType

    # Registrar mudanca
    entry = log_change(
        client_name="cliente-acme",
        change_type=ChangeType.CONFIG_SSID,
        action="enabled",
        resource="SSID 0 - Guest WiFi",
        details={"auth_mode": "psk", "vlan_id": 100}
    )

    # Auto-commit
    success, msg = auto_commit_change(
        client_name="cliente-acme",
        change_entry=entry
    )
"""

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Tipos de mudancas rastreadas no changelog."""

    DISCOVERY = "discovery"
    CONFIG_SSID = "config_ssid"
    CONFIG_VLAN = "config_vlan"
    CONFIG_FIREWALL = "config_firewall"
    CONFIG_ACL = "config_acl"
    CONFIG_SWITCH = "config_switch"
    CONFIG_CAMERA = "config_camera"
    CONFIG_QOS = "config_qos"
    WORKFLOW = "workflow"
    REPORT = "report"
    ROLLBACK = "rollback"
    OTHER = "other"


@dataclass
class ChangeEntry:
    """Entrada de changelog representando uma mudanca."""

    timestamp: datetime
    change_type: ChangeType
    action: str  # created, updated, deleted, enabled, disabled, etc
    resource: str  # ex: "SSID 0 - Guest WiFi"
    details: dict = field(default_factory=dict)
    user: str = "claude"  # quem fez a mudanca

    def to_markdown(self) -> str:
        """
        Converte a entrada para formato markdown.

        Returns:
            String markdown formatada
        """
        lines = []

        # Timestamp como header
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M")
        lines.append(f"## {timestamp_str}\n")

        # Metadados
        lines.append(f"**Tipo:** {self.change_type.value}")
        lines.append(f"**Acao:** {self.action}")
        lines.append(f"**Recurso:** {self.resource}")

        # Detalhes (se houver)
        if self.details:
            lines.append("\n**Detalhes:**")
            for key, value in self.details.items():
                lines.append(f"- {key}: {value}")

        # Usuario
        lines.append(f"\n**Usuario:** {self.user}")

        # Separador
        lines.append("\n---\n")

        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, text: str) -> Optional["ChangeEntry"]:
        """
        Parse entrada de changelog do formato markdown.

        Args:
            text: Texto markdown da entrada

        Returns:
            ChangeEntry ou None se parse falhar
        """
        # Implementacao simplificada - pode ser expandida
        # Para agora, retornamos None pois o focus e escrever
        return None


class ChangelogError(Exception):
    """Erro geral de changelog."""
    pass


class GitError(Exception):
    """Erro ao executar comandos Git."""
    pass


# ==================== Path Management ====================

def get_clients_dir() -> Path:
    """Retorna o diretorio base de clientes."""
    # Assumir que estamos em meraki-workspace/
    return Path.cwd() / "clients"


def get_changelog_path(client_name: str) -> Path:
    """
    Retorna o path do arquivo changelog para um cliente.

    Args:
        client_name: Nome do cliente

    Returns:
        Path para changelog.md
    """
    return get_clients_dir() / client_name / "changelog.md"


def get_client_dir(client_name: str) -> Path:
    """
    Retorna o diretorio do cliente.

    Args:
        client_name: Nome do cliente

    Returns:
        Path do diretorio do cliente
    """
    return get_clients_dir() / client_name


def init_changelog(client_name: str) -> Path:
    """
    Inicializa arquivo de changelog para um cliente.

    Cria o diretorio do cliente e arquivo changelog.md se nao existirem.

    Args:
        client_name: Nome do cliente

    Returns:
        Path para o changelog criado
    """
    client_dir = get_client_dir(client_name)
    changelog_path = get_changelog_path(client_name)

    # Criar diretorio se nao existir
    client_dir.mkdir(parents=True, exist_ok=True)

    # Criar changelog se nao existir
    if not changelog_path.exists():
        header = f"""# Changelog - {client_name}

> Historico de mudancas realizadas na rede Meraki

---

"""
        changelog_path.write_text(header)
        logger.info(f"Changelog inicializado: {changelog_path}")

    return changelog_path


# ==================== Changelog Operations ====================

def append_to_changelog(client_name: str, entry: ChangeEntry) -> None:
    """
    Adiciona entrada ao changelog do cliente.

    Args:
        client_name: Nome do cliente
        entry: ChangeEntry a adicionar

    Raises:
        ChangelogError: Se houver erro ao escrever
    """
    changelog_path = get_changelog_path(client_name)

    # Garantir que changelog existe
    if not changelog_path.exists():
        init_changelog(client_name)

    try:
        # Append entrada formatada
        with open(changelog_path, "a") as f:
            f.write(entry.to_markdown())

        logger.info(f"Entrada adicionada ao changelog: {client_name}")

    except IOError as e:
        raise ChangelogError(f"Erro ao escrever changelog: {e}")


def log_change(
    client_name: str,
    change_type: ChangeType,
    action: str,
    resource: str,
    details: Optional[dict] = None,
    user: str = "claude"
) -> ChangeEntry:
    """
    Registra uma mudanca no changelog do cliente.

    Args:
        client_name: Nome do cliente
        change_type: Tipo de mudanca (enum ChangeType)
        action: Acao realizada (created, updated, deleted, etc)
        resource: Recurso afetado (ex: "SSID 0 - Guest WiFi")
        details: Dicionario com detalhes adicionais
        user: Usuario que fez a mudanca (default: "claude")

    Returns:
        ChangeEntry criado

    Example:
        entry = log_change(
            client_name="cliente-acme",
            change_type=ChangeType.CONFIG_SSID,
            action="enabled",
            resource="SSID 0 - Guest WiFi",
            details={"auth_mode": "psk", "vlan_id": 100}
        )
    """
    entry = ChangeEntry(
        timestamp=datetime.now(),
        change_type=change_type,
        action=action,
        resource=resource,
        details=details or {},
        user=user
    )

    append_to_changelog(client_name, entry)

    return entry


def get_changelog(client_name: str) -> list[ChangeEntry]:
    """
    Retorna todas as entradas do changelog do cliente.

    Args:
        client_name: Nome do cliente

    Returns:
        Lista de ChangeEntry (vazia se nao houver changelog)

    Note:
        Implementacao simplificada - retorna lista vazia.
        Parse completo de markdown pode ser implementado depois.
    """
    changelog_path = get_changelog_path(client_name)

    if not changelog_path.exists():
        return []

    # TODO: Implementar parse completo do markdown
    # Por agora, retornar lista vazia
    logger.debug(f"Parse completo de changelog ainda nao implementado")
    return []


def get_recent_changes(client_name: str, count: int = 10) -> list[ChangeEntry]:
    """
    Retorna as ultimas N mudancas do changelog.

    Args:
        client_name: Nome do cliente
        count: Numero de mudancas a retornar (default: 10)

    Returns:
        Lista de ChangeEntry (vazia se nao houver changelog)
    """
    all_changes = get_changelog(client_name)
    return all_changes[:count] if all_changes else []


# ==================== Git Operations ====================

def is_git_repo() -> bool:
    """
    Verifica se o diretorio atual e um repositorio Git.

    Returns:
        True se for repositorio Git, False caso contrario
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        logger.warning("Git nao encontrado no sistema")
        return False


def git_add(paths: list[str]) -> bool:
    """
    Adiciona arquivos ao staging do Git.

    Args:
        paths: Lista de paths para adicionar

    Returns:
        True se sucesso, False caso contrario

    Raises:
        GitError: Se Git nao estiver disponivel
    """
    if not is_git_repo():
        logger.warning("Nao e um repositorio Git - pulando git add")
        return False

    try:
        for path in paths:
            subprocess.run(
                ["git", "add", path],
                check=True,
                capture_output=True,
                text=True
            )

        logger.debug(f"Git add executado: {paths}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Erro no git add: {e.stderr}")
        return False


def git_commit(message: str, paths: Optional[list[str]] = None) -> tuple[bool, str]:
    """
    Faz commit de mudancas no Git.

    Args:
        message: Mensagem de commit
        paths: Paths especificos para commitar (opcional)

    Returns:
        Tupla (sucesso: bool, mensagem/erro: str)

    Raises:
        GitError: Se Git nao estiver disponivel
    """
    if not is_git_repo():
        msg = "Nao e um repositorio Git - pulando commit"
        logger.warning(msg)
        return False, msg

    try:
        # Add paths se fornecidos
        if paths:
            git_add(paths)

        # Verificar se ha mudancas para commitar
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        if not status_result.stdout.strip():
            msg = "Nenhuma mudanca para commitar"
            logger.info(msg)
            return True, msg

        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            check=True
        )

        logger.info(f"Commit realizado: {message[:50]}...")
        return True, result.stdout.strip()

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() or e.stdout.strip()
        logger.error(f"Erro no git commit: {error_msg}")
        return False, error_msg


def git_status() -> dict:
    """
    Retorna status do Git.

    Returns:
        Dicionario com informacoes de status:
            - is_git_repo: bool
            - has_changes: bool
            - staged: list[str]
            - unstaged: list[str]
    """
    if not is_git_repo():
        return {
            "is_git_repo": False,
            "has_changes": False,
            "staged": [],
            "unstaged": []
        }

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        staged = []
        unstaged = []

        for line in lines:
            if not line:
                continue

            status = line[:2]
            filepath = line[3:]

            # M = modified, A = added, D = deleted
            if status[0] != " " and status[0] != "?":
                staged.append(filepath)
            if status[1] != " ":
                unstaged.append(filepath)

        return {
            "is_git_repo": True,
            "has_changes": len(lines) > 0,
            "staged": staged,
            "unstaged": unstaged
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao obter git status: {e}")
        return {
            "is_git_repo": True,
            "has_changes": False,
            "staged": [],
            "unstaged": []
        }


# ==================== Auto-Commit Helper ====================

def auto_commit_change(
    client_name: str,
    change_entry: ChangeEntry,
    files: Optional[list[str]] = None
) -> tuple[bool, str]:
    """
    Faz auto-commit de uma mudanca registrada.

    Args:
        client_name: Nome do cliente
        change_entry: ChangeEntry que foi registrado
        files: Arquivos adicionais para commitar (alem do changelog)

    Returns:
        Tupla (sucesso: bool, mensagem: str)

    Example:
        entry = log_change(...)
        success, msg = auto_commit_change(
            client_name="cliente-acme",
            change_entry=entry
        )
    """
    if not is_git_repo():
        msg = "Nao e um repositorio Git - auto-commit desabilitado"
        logger.warning(msg)
        return False, msg

    # Arquivos para commitar
    commit_files = [str(get_changelog_path(client_name))]

    if files:
        commit_files.extend(files)

    # Gerar mensagem de commit
    commit_message = _generate_commit_message(client_name, change_entry)

    # Executar commit
    return git_commit(commit_message, commit_files)


def _generate_commit_message(client_name: str, entry: ChangeEntry) -> str:
    """
    Gera mensagem de commit formatada a partir de ChangeEntry.

    Args:
        client_name: Nome do cliente
        entry: ChangeEntry

    Returns:
        Mensagem de commit formatada
    """
    # Primeira linha: [cliente] tipo: acao recurso
    title = f"[{client_name}] {entry.change_type.value}: {entry.action} {entry.resource}"

    # Detalhes
    details_lines = []
    if entry.details:
        details_lines.append("\nDetalhes:")
        for key, value in entry.details.items():
            details_lines.append(f"- {key}: {value}")

    # Usuario e timestamp
    timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M")
    details_lines.append(f"\nUsuario: {entry.user}")
    details_lines.append(f"Timestamp: {timestamp_str}")

    return title + "".join(details_lines)


# ==================== Bulk Operations ====================

def log_discovery_change(
    client_name: str,
    networks_count: int,
    devices_count: int,
    issues_count: int = 0
) -> ChangeEntry:
    """
    Helper para registrar discovery de rede.

    Args:
        client_name: Nome do cliente
        networks_count: Numero de networks descobertas
        devices_count: Numero de devices descobertos
        issues_count: Numero de issues encontrados

    Returns:
        ChangeEntry criado
    """
    return log_change(
        client_name=client_name,
        change_type=ChangeType.DISCOVERY,
        action="created",
        resource="Snapshot completo da rede",
        details={
            "networks": networks_count,
            "devices": devices_count,
            "issues": issues_count
        }
    )


def log_config_change(
    client_name: str,
    config_type: ChangeType,
    action: str,
    resource: str,
    **details
) -> ChangeEntry:
    """
    Helper para registrar mudancas de configuracao.

    Args:
        client_name: Nome do cliente
        config_type: Tipo de configuracao (SSID, VLAN, etc)
        action: Acao realizada
        resource: Recurso afetado
        **details: Detalhes adicionais

    Returns:
        ChangeEntry criado
    """
    return log_change(
        client_name=client_name,
        change_type=config_type,
        action=action,
        resource=resource,
        details=details
    )


def log_workflow_change(
    client_name: str,
    workflow_name: str,
    workflow_type: str
) -> ChangeEntry:
    """
    Helper para registrar criacao de workflow.

    Args:
        client_name: Nome do cliente
        workflow_name: Nome do workflow
        workflow_type: Tipo do workflow (remediation, compliance, etc)

    Returns:
        ChangeEntry criado
    """
    return log_change(
        client_name=client_name,
        change_type=ChangeType.WORKFLOW,
        action="created",
        resource=workflow_name,
        details={"type": workflow_type}
    )


def log_report_change(
    client_name: str,
    report_name: str,
    report_format: str = "html"
) -> ChangeEntry:
    """
    Helper para registrar geracao de relatorio.

    Args:
        client_name: Nome do cliente
        report_name: Nome do relatorio
        report_format: Formato (html, pdf)

    Returns:
        ChangeEntry criado
    """
    return log_change(
        client_name=client_name,
        change_type=ChangeType.REPORT,
        action="created",
        resource=report_name,
        details={"format": report_format}
    )


# ==================== Main (Testing) ====================

if __name__ == "__main__":
    # Teste rapido
    import sys

    logging.basicConfig(level=logging.DEBUG)

    try:
        # Teste: criar changelog
        test_client = "test-client"

        print(f"\n=== Testando changelog para '{test_client}' ===\n")

        # Inicializar
        path = init_changelog(test_client)
        print(f"Changelog criado: {path}")

        # Logar mudanca
        entry = log_change(
            client_name=test_client,
            change_type=ChangeType.CONFIG_SSID,
            action="enabled",
            resource="SSID 0 - Guest WiFi",
            details={"auth_mode": "psk", "vlan_id": 100}
        )
        print(f"\nEntrada registrada:")
        print(entry.to_markdown())

        # Status Git
        status = git_status()
        print(f"Git status: {status}")

        # Auto-commit (se for repo Git)
        if status["is_git_repo"]:
            success, msg = auto_commit_change(test_client, entry)
            print(f"\nAuto-commit: {success}")
            print(f"Mensagem: {msg}")

        print("\n=== Teste concluido com sucesso ===\n")

    except Exception as e:
        print(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
