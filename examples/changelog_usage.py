"""
Exemplos de uso do modulo changelog.

Demonstra os diferentes casos de uso para rastreamento de mudancas
e auto-commit no Git.
"""

import logging
from scripts.changelog import (
    log_change,
    log_discovery_change,
    log_config_change,
    log_workflow_change,
    log_report_change,
    auto_commit_change,
    get_changelog_path,
    git_status,
    ChangeType
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def example_discovery():
    """Exemplo: Registrar discovery de rede."""
    print("\n=== Exemplo: Discovery ===")

    client = "cliente-acme"

    entry = log_discovery_change(
        client_name=client,
        networks_count=5,
        devices_count=23,
        issues_count=3
    )

    print(f"Entry criado: {entry.resource}")
    print(f"Changelog: {get_changelog_path(client)}")


def example_ssid_config():
    """Exemplo: Configurar SSID."""
    print("\n=== Exemplo: Configurar SSID ===")

    client = "cliente-acme"

    # Habilitar Guest WiFi
    entry = log_config_change(
        client_name=client,
        config_type=ChangeType.CONFIG_SSID,
        action="enabled",
        resource="SSID 0 - Guest WiFi",
        auth_mode="psk",
        encryption="wpa2",
        vlan_id=100,
        psk="super-secret-key"
    )

    # Auto-commit
    success, msg = auto_commit_change(client, entry)
    print(f"Auto-commit: {success}")
    print(f"Mensagem: {msg}")


def example_firewall_config():
    """Exemplo: Configurar Firewall."""
    print("\n=== Exemplo: Configurar Firewall ===")

    client = "cliente-globex"

    # Bloquear Telnet
    entry = log_config_change(
        client_name=client,
        config_type=ChangeType.CONFIG_FIREWALL,
        action="created",
        resource="L3 Rule: Block Telnet",
        protocol="tcp",
        dest_port=23,
        policy="deny",
        comment="Block insecure Telnet access"
    )

    print(f"Entry criado: {entry.resource}")
    print(entry.to_markdown())


def example_vlan_config():
    """Exemplo: Criar VLAN."""
    print("\n=== Exemplo: Criar VLAN ===")

    client = "cliente-acme"

    entry = log_config_change(
        client_name=client,
        config_type=ChangeType.CONFIG_VLAN,
        action="created",
        resource="VLAN 100 - Guest Network",
        subnet="10.100.0.0/24",
        appliance_ip="10.100.0.1",
        dhcp_enabled=True
    )

    print(f"Entry criado: {entry.resource}")


def example_workflow_creation():
    """Exemplo: Criar Workflow."""
    print("\n=== Exemplo: Criar Workflow ===")

    client = "cliente-acme"

    entry = log_workflow_change(
        client_name=client,
        workflow_name="Device Offline Remediation",
        workflow_type="remediation"
    )

    # Incluir arquivo do workflow no commit
    workflow_file = f"clients/{client}/workflows/device_offline_remediation.json"

    success, msg = auto_commit_change(
        client,
        entry,
        files=[workflow_file]
    )

    print(f"Workflow criado e commitado: {success}")


def example_report_generation():
    """Exemplo: Gerar Relatorio."""
    print("\n=== Exemplo: Gerar Relatorio ===")

    client = "cliente-globex"

    entry = log_report_change(
        client_name=client,
        report_name="Network Health Report",
        report_format="pdf"
    )

    print(f"Relatorio registrado: {entry.resource}")


def example_rollback():
    """Exemplo: Rollback de configuracao."""
    print("\n=== Exemplo: Rollback ===")

    client = "cliente-acme"

    entry = log_change(
        client_name=client,
        change_type=ChangeType.ROLLBACK,
        action="reverted",
        resource="SSID 0 - Guest WiFi configuration",
        details={
            "reason": "Security concern - PSK too weak",
            "reverted_to": "previous config",
            "timestamp": "2024-01-24 14:30"
        }
    )

    print(f"Rollback registrado: {entry.resource}")


def example_git_status():
    """Exemplo: Verificar status Git."""
    print("\n=== Exemplo: Git Status ===")

    status = git_status()

    print(f"E repositorio Git: {status['is_git_repo']}")
    print(f"Tem mudancas: {status['has_changes']}")
    print(f"Arquivos staged: {status['staged']}")
    print(f"Arquivos unstaged: {status['unstaged']}")


def example_multiple_changes():
    """Exemplo: Multiplas mudancas em sequencia."""
    print("\n=== Exemplo: Multiplas Mudancas ===")

    client = "cliente-acme"

    # 1. Discovery
    log_discovery_change(client, networks_count=5, devices_count=23, issues_count=3)

    # 2. Configurar SSID
    log_config_change(
        client,
        ChangeType.CONFIG_SSID,
        "enabled",
        "SSID 0 - Guest WiFi",
        auth_mode="psk"
    )

    # 3. Criar ACL
    log_config_change(
        client,
        ChangeType.CONFIG_ACL,
        "created",
        "Switch ACL: Block Telnet",
        protocol="tcp",
        port=23
    )

    # 4. Gerar workflow
    log_workflow_change(client, "Device Offline Alert", "monitoring")

    # 5. Gerar relatorio
    log_report_change(client, "Initial Assessment Report", "html")

    print(f"5 mudancas registradas para {client}")
    print(f"Changelog: {get_changelog_path(client)}")


# ==================== Main ====================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Exemplos de Uso - scripts.changelog")
    print("="*60)

    # Executar exemplos
    try:
        example_discovery()
        example_ssid_config()
        example_firewall_config()
        example_vlan_config()
        example_workflow_creation()
        example_report_generation()
        example_rollback()
        example_git_status()
        example_multiple_changes()

        print("\n" + "="*60)
        print("Todos os exemplos executados com sucesso!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"Erro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()
