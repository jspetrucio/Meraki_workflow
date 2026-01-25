"""
Testes para scripts.changelog.

Testa funcionalidades de logging de mudancas e integracao com Git.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from scripts.changelog import (
    ChangeEntry,
    ChangeType,
    append_to_changelog,
    auto_commit_change,
    get_changelog_path,
    get_client_dir,
    git_status,
    init_changelog,
    log_change,
    log_config_change,
    log_discovery_change,
    log_report_change,
    log_workflow_change,
)


# ==================== Fixtures ====================

@pytest.fixture
def temp_workspace(monkeypatch, tmp_path):
    """Cria workspace temporario para testes."""
    # Criar estrutura de diretorios
    clients_dir = tmp_path / "clients"
    clients_dir.mkdir()

    # Mudar CWD para tmp_path
    monkeypatch.chdir(tmp_path)

    yield tmp_path

    # Cleanup e automatico pelo pytest


@pytest.fixture
def test_client_name():
    """Nome de cliente para testes."""
    return "test-client"


# ==================== Tests: ChangeEntry ====================

def test_change_entry_creation():
    """Testa criacao de ChangeEntry."""
    entry = ChangeEntry(
        timestamp=datetime(2024, 1, 24, 14, 30),
        change_type=ChangeType.CONFIG_SSID,
        action="enabled",
        resource="SSID 0 - Guest WiFi",
        details={"auth_mode": "psk", "vlan_id": 100},
        user="claude"
    )

    assert entry.change_type == ChangeType.CONFIG_SSID
    assert entry.action == "enabled"
    assert entry.resource == "SSID 0 - Guest WiFi"
    assert entry.details["auth_mode"] == "psk"
    assert entry.user == "claude"


def test_change_entry_to_markdown():
    """Testa conversao de ChangeEntry para markdown."""
    entry = ChangeEntry(
        timestamp=datetime(2024, 1, 24, 14, 30),
        change_type=ChangeType.CONFIG_SSID,
        action="enabled",
        resource="SSID 0 - Guest WiFi",
        details={"auth_mode": "psk"},
        user="claude"
    )

    markdown = entry.to_markdown()

    assert "## 2024-01-24 14:30" in markdown
    assert "**Tipo:** config_ssid" in markdown
    assert "**Acao:** enabled" in markdown
    assert "**Recurso:** SSID 0 - Guest WiFi" in markdown
    assert "**Detalhes:**" in markdown
    assert "- auth_mode: psk" in markdown
    assert "**Usuario:** claude" in markdown


def test_change_entry_to_markdown_no_details():
    """Testa conversao sem detalhes."""
    entry = ChangeEntry(
        timestamp=datetime(2024, 1, 24, 14, 30),
        change_type=ChangeType.DISCOVERY,
        action="created",
        resource="Snapshot",
        user="claude"
    )

    markdown = entry.to_markdown()

    assert "**Detalhes:**" not in markdown or markdown.count("**Detalhes:**") == 0


# ==================== Tests: Path Management ====================

def test_get_changelog_path(temp_workspace, test_client_name):
    """Testa get_changelog_path."""
    path = get_changelog_path(test_client_name)

    assert path == temp_workspace / "clients" / test_client_name / "changelog.md"
    assert path.parent == get_client_dir(test_client_name)


def test_init_changelog(temp_workspace, test_client_name):
    """Testa inicializacao de changelog."""
    path = init_changelog(test_client_name)

    assert path.exists()
    assert path.is_file()

    content = path.read_text()
    assert f"# Changelog - {test_client_name}" in content
    assert "Historico de mudancas" in content


def test_init_changelog_idempotent(temp_workspace, test_client_name):
    """Testa que init_changelog e idempotente."""
    path1 = init_changelog(test_client_name)
    content1 = path1.read_text()

    path2 = init_changelog(test_client_name)
    content2 = path2.read_text()

    assert path1 == path2
    assert content1 == content2  # Nao duplica header


# ==================== Tests: Changelog Operations ====================

def test_append_to_changelog(temp_workspace, test_client_name):
    """Testa append_to_changelog."""
    init_changelog(test_client_name)

    entry = ChangeEntry(
        timestamp=datetime(2024, 1, 24, 14, 30),
        change_type=ChangeType.CONFIG_SSID,
        action="enabled",
        resource="SSID 0",
        user="claude"
    )

    append_to_changelog(test_client_name, entry)

    path = get_changelog_path(test_client_name)
    content = path.read_text()

    assert "## 2024-01-24 14:30" in content
    assert "**Tipo:** config_ssid" in content


def test_log_change(temp_workspace, test_client_name):
    """Testa log_change."""
    entry = log_change(
        client_name=test_client_name,
        change_type=ChangeType.CONFIG_SSID,
        action="enabled",
        resource="SSID 0",
        details={"vlan_id": 100},
        user="test-user"
    )

    assert entry.change_type == ChangeType.CONFIG_SSID
    assert entry.action == "enabled"
    assert entry.user == "test-user"

    # Verificar que foi escrito
    path = get_changelog_path(test_client_name)
    assert path.exists()

    content = path.read_text()
    assert "**Tipo:** config_ssid" in content
    assert "- vlan_id: 100" in content


def test_log_multiple_changes(temp_workspace, test_client_name):
    """Testa multiplos logs."""
    log_change(test_client_name, ChangeType.DISCOVERY, "created", "Snapshot 1")
    log_change(test_client_name, ChangeType.CONFIG_SSID, "enabled", "SSID 0")
    log_change(test_client_name, ChangeType.CONFIG_VLAN, "created", "VLAN 100")

    path = get_changelog_path(test_client_name)
    content = path.read_text()

    # Deve ter 3 entries (cada um com separador ---)
    assert content.count("---") >= 4  # Header + 3 entries


# ==================== Tests: Helper Functions ====================

def test_log_discovery_change(temp_workspace, test_client_name):
    """Testa log_discovery_change helper."""
    entry = log_discovery_change(
        client_name=test_client_name,
        networks_count=5,
        devices_count=23,
        issues_count=3
    )

    assert entry.change_type == ChangeType.DISCOVERY
    assert entry.action == "created"
    assert entry.details["networks"] == 5
    assert entry.details["devices"] == 23
    assert entry.details["issues"] == 3


def test_log_config_change(temp_workspace, test_client_name):
    """Testa log_config_change helper."""
    entry = log_config_change(
        client_name=test_client_name,
        config_type=ChangeType.CONFIG_FIREWALL,
        action="created",
        resource="L3 Rule: Block Telnet",
        protocol="tcp",
        dest_port=23
    )

    assert entry.change_type == ChangeType.CONFIG_FIREWALL
    assert entry.details["protocol"] == "tcp"
    assert entry.details["dest_port"] == 23


def test_log_workflow_change(temp_workspace, test_client_name):
    """Testa log_workflow_change helper."""
    entry = log_workflow_change(
        client_name=test_client_name,
        workflow_name="Device Offline Alert",
        workflow_type="monitoring"
    )

    assert entry.change_type == ChangeType.WORKFLOW
    assert entry.action == "created"
    assert entry.resource == "Device Offline Alert"
    assert entry.details["type"] == "monitoring"


def test_log_report_change(temp_workspace, test_client_name):
    """Testa log_report_change helper."""
    entry = log_report_change(
        client_name=test_client_name,
        report_name="Network Health",
        report_format="pdf"
    )

    assert entry.change_type == ChangeType.REPORT
    assert entry.details["format"] == "pdf"


# ==================== Tests: Git Integration ====================

def test_git_status_not_git_repo(temp_workspace):
    """Testa git_status quando nao e repositorio Git."""
    status = git_status()

    assert status["is_git_repo"] is False
    assert status["has_changes"] is False
    assert status["staged"] == []
    assert status["unstaged"] == []


def test_auto_commit_change_not_git_repo(temp_workspace, test_client_name):
    """Testa auto_commit_change quando nao e repo Git."""
    entry = log_change(
        test_client_name,
        ChangeType.CONFIG_SSID,
        "enabled",
        "SSID 0"
    )

    success, msg = auto_commit_change(test_client_name, entry)

    assert success is False
    assert "Nao e um repositorio Git" in msg


# Nota: Testes de integracao Git real requerem setup mais complexo
# Podemos adicionar depois se necessario


# ==================== Tests: Edge Cases ====================

def test_changelog_with_special_characters(temp_workspace, test_client_name):
    """Testa changelog com caracteres especiais."""
    entry = log_change(
        test_client_name,
        ChangeType.CONFIG_SSID,
        "created",
        "SSID: Guest & Visitors (10.0.0.0/24)",
        details={"comment": "Allow access with special chars: @#$%"}
    )

    path = get_changelog_path(test_client_name)
    content = path.read_text()

    assert "SSID: Guest & Visitors (10.0.0.0/24)" in content
    assert "special chars: @#$%" in content


def test_changelog_empty_details(temp_workspace, test_client_name):
    """Testa changelog com details vazio."""
    entry = log_change(
        test_client_name,
        ChangeType.DISCOVERY,
        "created",
        "Snapshot"
    )

    assert entry.details == {}

    path = get_changelog_path(test_client_name)
    content = path.read_text()
    assert "Snapshot" in content


# ==================== Parametrized Tests ====================

@pytest.mark.parametrize("change_type", [
    ChangeType.DISCOVERY,
    ChangeType.CONFIG_SSID,
    ChangeType.CONFIG_VLAN,
    ChangeType.CONFIG_FIREWALL,
    ChangeType.CONFIG_ACL,
    ChangeType.WORKFLOW,
    ChangeType.REPORT,
    ChangeType.ROLLBACK
])
def test_all_change_types(temp_workspace, test_client_name, change_type):
    """Testa todos os tipos de mudanca."""
    entry = log_change(
        test_client_name,
        change_type,
        "test_action",
        "test_resource"
    )

    assert entry.change_type == change_type

    path = get_changelog_path(test_client_name)
    content = path.read_text()
    assert f"**Tipo:** {change_type.value}" in content
