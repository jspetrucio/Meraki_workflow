"""
Testes unitários para scripts/config.py

Para executar:
    pytest tests/test_config.py -v
ou:
    python -m pytest tests/test_config.py -v
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Importar o módulo a testar
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.config import (
    ConfigAction,
    ConfigResult,
    configure_ssid,
    enable_ssid,
    disable_ssid,
    create_vlan,
    update_vlan,
    delete_vlan,
    add_firewall_rule,
    remove_firewall_rule,
    get_firewall_rules,
    add_switch_acl,
    backup_config,
    rollback_config,
    validate_config_params
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_client():
    """Mock do MerakiClient."""
    client = Mock()
    client.get_network = Mock(return_value={"id": "N_123", "name": "Test Network"})
    client.safe_call = Mock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
    return client


@pytest.fixture
def mock_ssids():
    """SSIDs de exemplo."""
    return [
        {
            "number": 0,
            "name": "Corporate WiFi",
            "enabled": True,
            "authMode": "psk",
            "psk": "password123"
        },
        {
            "number": 1,
            "name": "Guest WiFi",
            "enabled": False,
            "authMode": "open"
        }
    ]


@pytest.fixture
def mock_vlans():
    """VLANs de exemplo."""
    return [
        {
            "id": "100",
            "name": "Data",
            "subnet": "192.168.100.0/24",
            "applianceIp": "192.168.100.1"
        },
        {
            "id": "200",
            "name": "Voice",
            "subnet": "192.168.200.0/24",
            "applianceIp": "192.168.200.1"
        }
    ]


@pytest.fixture
def mock_firewall_rules():
    """Regras de firewall de exemplo."""
    return [
        {
            "policy": "deny",
            "protocol": "tcp",
            "srcCidr": "any",
            "destCidr": "any",
            "destPort": "23",
            "comment": "Block Telnet"
        },
        {
            "policy": "allow",
            "protocol": "tcp",
            "srcCidr": "192.168.1.0/24",
            "destCidr": "any",
            "destPort": "443",
            "comment": "Allow HTTPS"
        }
    ]


# ==================== Testes ConfigResult ====================

def test_config_result_success():
    """Testa criação de ConfigResult bem-sucedido."""
    result = ConfigResult(
        success=True,
        action=ConfigAction.CREATE,
        resource_type="ssid",
        resource_id="N_123/ssid_0",
        message="SSID criado com sucesso"
    )

    assert result.success is True
    assert result.action == ConfigAction.CREATE
    assert result.resource_type == "ssid"
    assert result.error is None


def test_config_result_failure():
    """Testa criação de ConfigResult com erro."""
    result = ConfigResult(
        success=False,
        action=ConfigAction.UPDATE,
        resource_type="vlan",
        resource_id="100",
        message="Falha ao atualizar VLAN",
        error="Network not found"
    )

    assert result.success is False
    assert result.error == "Network not found"


# ==================== Testes SSID ====================

@patch('scripts.config.get_client')
def test_configure_ssid_success(mock_get_client, mock_client):
    """Testa configuração bem-sucedida de SSID."""
    mock_get_client.return_value = mock_client
    mock_client.update_ssid = Mock(return_value={
        "number": 0,
        "name": "Test SSID",
        "enabled": True
    })

    result = configure_ssid(
        network_id="N_123",
        ssid_number=0,
        name="Test SSID",
        enabled=True,
        backup=False
    )

    assert result.success is True
    assert result.action == ConfigAction.UPDATE
    assert result.resource_type == "ssid"
    assert "SSID 0 configurado" in result.message
    mock_client.update_ssid.assert_called_once()


@patch('scripts.config.get_client')
def test_enable_ssid(mock_get_client, mock_client):
    """Testa habilitação de SSID."""
    mock_get_client.return_value = mock_client
    mock_client.update_ssid = Mock(return_value={
        "number": 1,
        "name": "Guest",
        "enabled": True
    })

    result = enable_ssid(
        network_id="N_123",
        ssid_number=1,
        name="Guest",
        backup=False
    )

    assert result.success is True
    assert result.changes.get("enabled") is True
    assert result.changes.get("name") == "Guest"


@patch('scripts.config.get_client')
def test_disable_ssid(mock_get_client, mock_client):
    """Testa desabilitação de SSID."""
    mock_get_client.return_value = mock_client
    mock_client.update_ssid = Mock(return_value={
        "number": 2,
        "enabled": False
    })

    result = disable_ssid(
        network_id="N_123",
        ssid_number=2,
        backup=False
    )

    assert result.success is True
    assert result.changes.get("enabled") is False


# ==================== Testes VLAN ====================

@patch('scripts.config.get_client')
def test_create_vlan_success(mock_get_client, mock_client):
    """Testa criação bem-sucedida de VLAN."""
    mock_get_client.return_value = mock_client
    mock_client.create_vlan = Mock(return_value={
        "id": "100",
        "name": "Test VLAN",
        "subnet": "192.168.100.0/24"
    })

    result = create_vlan(
        network_id="N_123",
        vlan_id=100,
        name="Test VLAN",
        subnet="192.168.100.0/24",
        appliance_ip="192.168.100.1",
        backup=False
    )

    assert result.success is True
    assert result.action == ConfigAction.CREATE
    assert result.resource_type == "vlan"
    assert result.resource_id == "100"


@patch('scripts.config.get_client')
def test_update_vlan(mock_get_client, mock_client):
    """Testa atualização de VLAN."""
    mock_get_client.return_value = mock_client
    mock_client.update_vlan = Mock(return_value={
        "id": "100",
        "name": "Updated VLAN"
    })

    result = update_vlan(
        network_id="N_123",
        vlan_id="100",
        name="Updated VLAN",
        backup=False
    )

    assert result.success is True
    assert result.action == ConfigAction.UPDATE


@patch('scripts.config.get_client')
def test_delete_vlan(mock_get_client, mock_client):
    """Testa remoção de VLAN."""
    mock_get_client.return_value = mock_client
    mock_client.delete_vlan = Mock(return_value=None)

    result = delete_vlan(
        network_id="N_123",
        vlan_id="100",
        backup=False
    )

    assert result.success is True
    assert result.action == ConfigAction.DELETE


# ==================== Testes Firewall ====================

@patch('scripts.config.get_client')
def test_get_firewall_rules(mock_get_client, mock_client, mock_firewall_rules):
    """Testa listagem de regras de firewall."""
    mock_get_client.return_value = mock_client
    mock_client.get_l3_firewall_rules = Mock(return_value={
        "rules": mock_firewall_rules
    })

    rules = get_firewall_rules("N_123")

    assert len(rules) == 2
    assert rules[0]["policy"] == "deny"
    assert rules[1]["policy"] == "allow"


@patch('scripts.config.get_client')
def test_add_firewall_rule(mock_get_client, mock_client):
    """Testa adição de regra de firewall."""
    mock_get_client.return_value = mock_client
    mock_client.get_l3_firewall_rules = Mock(return_value={"rules": []})
    mock_client.update_l3_firewall_rules = Mock(return_value={"rules": []})

    result = add_firewall_rule(
        network_id="N_123",
        policy="deny",
        protocol="tcp",
        src_cidr="any",
        dest_cidr="any",
        dest_port="23",
        comment="Block Telnet",
        backup=False
    )

    assert result.success is True
    assert result.action == ConfigAction.CREATE
    assert result.resource_type == "firewall"


@patch('scripts.config.get_client')
def test_remove_firewall_rule(mock_get_client, mock_client, mock_firewall_rules):
    """Testa remoção de regra de firewall."""
    mock_get_client.return_value = mock_client
    mock_client.get_l3_firewall_rules = Mock(return_value={
        "rules": mock_firewall_rules
    })
    mock_client.update_l3_firewall_rules = Mock(return_value={"rules": []})

    result = remove_firewall_rule(
        network_id="N_123",
        rule_index=0,
        backup=False
    )

    assert result.success is True
    assert result.action == ConfigAction.DELETE


@patch('scripts.config.get_client')
def test_remove_firewall_rule_invalid_index(mock_get_client, mock_client):
    """Testa remoção com índice inválido."""
    mock_get_client.return_value = mock_client
    mock_client.get_l3_firewall_rules = Mock(return_value={"rules": []})

    result = remove_firewall_rule(
        network_id="N_123",
        rule_index=99,
        backup=False
    )

    assert result.success is False
    assert "fora do range" in result.message


# ==================== Testes Switch ACL ====================

@patch('scripts.config.get_client')
def test_add_switch_acl(mock_get_client, mock_client):
    """Testa adição de ACL de switch."""
    mock_get_client.return_value = mock_client
    mock_client.get_switch_acls = Mock(return_value={"rules": []})
    mock_client.update_switch_acls = Mock(return_value={"rules": []})

    result = add_switch_acl(
        network_id="N_123",
        policy="deny",
        protocol="tcp",
        src_cidr="any",
        src_port="any",
        dest_cidr="any",
        dest_port="23",
        backup=False
    )

    assert result.success is True
    assert result.action == ConfigAction.CREATE
    assert result.resource_type == "acl"


# ==================== Testes Backup/Rollback ====================

@patch('scripts.config.get_client')
def test_backup_config(mock_get_client, mock_client, mock_ssids, tmp_path):
    """Testa criação de backup."""
    mock_get_client.return_value = mock_client
    mock_client.safe_call = Mock(return_value=mock_ssids)

    # Criar diretório temporário para teste
    with patch('scripts.config.Path') as mock_path:
        mock_path.return_value = tmp_path / "clients" / "test" / "backups"

        # Executar backup
        backup_path = backup_config(
            network_id="N_123",
            client_name="test",
            resource_type="ssid"
        )

        # Verificar que arquivo foi criado
        assert backup_path is not None


@patch('scripts.config.get_client')
def test_validate_config_params(mock_get_client, mock_client):
    """Testa validação de parâmetros."""
    mock_get_client.return_value = mock_client
    mock_client.get_network = Mock(return_value={
        "id": "N_123",
        "name": "Test Network"
    })

    valid, msg = validate_config_params("N_123")

    assert valid is True
    assert "Test Network" in msg


# ==================== Testes de Integração ====================

@patch('scripts.config.get_client')
def test_ssid_workflow(mock_get_client, mock_client):
    """Testa workflow completo de SSID."""
    mock_get_client.return_value = mock_client
    mock_client.update_ssid = Mock(return_value={
        "number": 0,
        "name": "Test",
        "enabled": True
    })

    # 1. Configurar SSID
    result1 = configure_ssid(
        network_id="N_123",
        ssid_number=0,
        name="Test",
        enabled=True,
        backup=False
    )
    assert result1.success is True

    # 2. Desabilitar
    mock_client.update_ssid = Mock(return_value={
        "number": 0,
        "enabled": False
    })
    result2 = disable_ssid(
        network_id="N_123",
        ssid_number=0,
        backup=False
    )
    assert result2.success is True

    # 3. Habilitar novamente
    mock_client.update_ssid = Mock(return_value={
        "number": 0,
        "name": "Test",
        "enabled": True
    })
    result3 = enable_ssid(
        network_id="N_123",
        ssid_number=0,
        name="Test",
        backup=False
    )
    assert result3.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
