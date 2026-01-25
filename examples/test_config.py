#!/usr/bin/env python3
"""
Exemplos de uso do modulo config.py

Este script demonstra como usar as funcoes de configuracao
para diferentes recursos Meraki.
"""

import sys
from pathlib import Path

# Adicionar scripts/ ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.config import (
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
    ConfigAction
)
from scripts.api import get_client


def example_ssid_config():
    """Exemplo: Configurar SSID"""
    print("\n=== Exemplo: Configurar SSID ===")

    # Configurar SSID para rede guest
    result = configure_ssid(
        network_id="N_123456789",
        ssid_number=1,
        name="Guest WiFi",
        enabled=True,
        auth_mode="psk",
        psk="senha_segura_123",
        vlan_id=100,
        backup=True,
        client_name="exemplo-cliente"
    )

    print(f"Resultado: {result}")
    if result.success:
        print(f"  Backup: {result.backup_path}")
        print(f"  Changes: {result.changes}")


def example_vlan_config():
    """Exemplo: Criar VLAN"""
    print("\n=== Exemplo: Criar VLAN ===")

    result = create_vlan(
        network_id="N_123456789",
        vlan_id=100,
        name="Guest Network",
        subnet="192.168.100.0/24",
        appliance_ip="192.168.100.1",
        backup=True,
        client_name="exemplo-cliente"
    )

    print(f"Resultado: {result}")


def example_firewall_config():
    """Exemplo: Adicionar regra de firewall"""
    print("\n=== Exemplo: Firewall Rules ===")

    # Bloquear Telnet
    result1 = add_firewall_rule(
        network_id="N_123456789",
        policy="deny",
        protocol="tcp",
        src_cidr="any",
        dest_cidr="any",
        dest_port="23",
        comment="Block Telnet - Security Policy",
        backup=True,
        client_name="exemplo-cliente"
    )
    print(f"Block Telnet: {result1}")

    # Permitir HTTPS para subnet especifico
    result2 = add_firewall_rule(
        network_id="N_123456789",
        policy="allow",
        protocol="tcp",
        src_cidr="192.168.1.0/24",
        dest_cidr="any",
        dest_port="443",
        comment="Allow HTTPS from internal network",
        position=0,  # Primeira regra
        backup=False,  # Ja fizemos backup
        client_name="exemplo-cliente"
    )
    print(f"Allow HTTPS: {result2}")

    # Listar regras atuais
    rules = get_firewall_rules("N_123456789")
    print(f"\nRegras atuais ({len(rules)}):")
    for i, rule in enumerate(rules):
        print(f"  {i}: {rule.get('policy')} {rule.get('protocol')} "
              f"{rule.get('srcCidr')} -> {rule.get('destCidr')}:{rule.get('destPort')} "
              f"// {rule.get('comment', '')}")


def example_acl_config():
    """Exemplo: Adicionar ACL de switch"""
    print("\n=== Exemplo: Switch ACL ===")

    result = add_switch_acl(
        network_id="N_123456789",
        policy="deny",
        protocol="tcp",
        src_cidr="any",
        src_port="any",
        dest_cidr="any",
        dest_port="23",
        vlan="100",
        comment="Block Telnet on VLAN 100",
        backup=True,
        client_name="exemplo-cliente"
    )

    print(f"Resultado: {result}")


def example_backup_rollback():
    """Exemplo: Backup e Rollback"""
    print("\n=== Exemplo: Backup & Rollback ===")

    # Fazer backup completo
    backup_path = backup_config(
        network_id="N_123456789",
        client_name="exemplo-cliente",
        resource_type="full"
    )
    print(f"Backup criado: {backup_path}")

    # Fazer uma mudanca
    result = configure_ssid(
        network_id="N_123456789",
        ssid_number=0,
        enabled=False,
        backup=False  # Ja fizemos backup acima
    )
    print(f"SSID desabilitado: {result}")

    # Rollback (restaurar do backup)
    rollback = rollback_config(backup_path)
    print(f"Rollback: {rollback}")


def example_real_world_scenario():
    """Exemplo: Cenario real de configuracao"""
    print("\n=== Cenario Real: Setup de Guest Network ===")

    network_id = "N_123456789"
    client_name = "acme-corp"

    # 1. Criar VLAN para guest
    print("\n1. Criando VLAN para guest network...")
    vlan_result = create_vlan(
        network_id=network_id,
        vlan_id=200,
        name="Guest Network",
        subnet="192.168.200.0/24",
        appliance_ip="192.168.200.1",
        client_name=client_name
    )
    print(f"   {vlan_result.message}")

    # 2. Configurar SSID
    print("\n2. Configurando SSID para guest...")
    ssid_result = configure_ssid(
        network_id=network_id,
        ssid_number=2,
        name="ACME Guest",
        enabled=True,
        auth_mode="psk",
        psk="GuestPass2024!",
        vlan_id=200,
        ip_assignment_mode="NAT mode",
        client_name=client_name
    )
    print(f"   {ssid_result.message}")

    # 3. Adicionar regras de firewall para guest
    print("\n3. Configurando firewall rules...")

    # Bloquear acesso a rede interna
    fw1 = add_firewall_rule(
        network_id=network_id,
        policy="deny",
        protocol="any",
        src_cidr="192.168.200.0/24",
        dest_cidr="192.168.0.0/16",
        comment="Block guest from internal network",
        client_name=client_name
    )
    print(f"   {fw1.message}")

    # Permitir DNS
    fw2 = add_firewall_rule(
        network_id=network_id,
        policy="allow",
        protocol="udp",
        src_cidr="192.168.200.0/24",
        dest_cidr="any",
        dest_port="53",
        comment="Allow DNS for guest",
        client_name=client_name
    )
    print(f"   {fw2.message}")

    # Permitir HTTP/HTTPS
    fw3 = add_firewall_rule(
        network_id=network_id,
        policy="allow",
        protocol="tcp",
        src_cidr="192.168.200.0/24",
        dest_cidr="any",
        dest_port="80,443",
        comment="Allow web browsing for guest",
        client_name=client_name
    )
    print(f"   {fw3.message}")

    print("\n=== Guest Network Setup Completo! ===")


if __name__ == "__main__":
    print("=== Exemplos de Uso do config.py ===")
    print("\nNOTA: Este script demonstra o uso. Para executar de verdade,")
    print("      substitua 'N_123456789' por um network_id real.")
    print("\nExemplos disponiveis:")
    print("  1. SSID Configuration")
    print("  2. VLAN Configuration")
    print("  3. Firewall Rules")
    print("  4. Switch ACL")
    print("  5. Backup & Rollback")
    print("  6. Real World Scenario (Guest Network Setup)")
    print("\nPara executar um exemplo real, use a CLI ou ajuste o codigo.")

    # Descomentar para executar exemplos (requer network_id valido)
    # example_ssid_config()
    # example_vlan_config()
    # example_firewall_config()
    # example_acl_config()
    # example_backup_rollback()
    # example_real_world_scenario()
