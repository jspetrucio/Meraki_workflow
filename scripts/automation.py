#!/usr/bin/env python3
"""
Action Batches Manager - Automação em massa via Meraki API.

Este módulo fornece wrapper para Action Batches da Meraki API,
permitindo executar múltiplas configurações de forma eficiente.
"""

import meraki
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ActionBatchResult:
    """Resultado de um Action Batch."""
    batch_id: str
    status: Dict[str, Any]
    confirmed: bool
    synchronous: bool
    total_actions: int
    completed: bool
    failed: bool
    errors: List[str]
    created_resources: List[Dict]


class ActionBatchManager:
    """Gerenciador de Action Batches para automação em massa."""

    def __init__(self, dashboard: meraki.DashboardAPI, org_id: str):
        """
        Inicializa o gerenciador.

        Args:
            dashboard: Instância do DashboardAPI
            org_id: Organization ID
        """
        self.dashboard = dashboard
        self.org_id = org_id

    def preview_batch(self, actions: List[Dict]) -> ActionBatchResult:
        """
        Executa batch em preview mode (dry-run).

        Args:
            actions: Lista de ações a executar

        Returns:
            ActionBatchResult com resultados do preview
        """
        result = self.dashboard.organizations.createOrganizationActionBatch(
            self.org_id,
            confirmed=False,  # Preview mode
            synchronous=True,  # Aguardar resultado
            actions=actions
        )

        return self._parse_result(result)

    def execute_batch(
        self,
        actions: List[Dict],
        synchronous: bool = False,
        auto_confirm: bool = True
    ) -> ActionBatchResult:
        """
        Executa batch confirmado.

        Args:
            actions: Lista de ações a executar
            synchronous: Se True, aguarda conclusão (max 20 actions)
            auto_confirm: Se False, cria em preview mode

        Returns:
            ActionBatchResult com resultados
        """
        # Validar número de ações
        if synchronous and len(actions) > 20:
            raise ValueError(
                f"Synchronous batches limitados a 20 actions. "
                f"Recebido: {len(actions)}"
            )

        if len(actions) > 100:
            raise ValueError(
                f"Action batches limitados a 100 actions. "
                f"Recebido: {len(actions)}"
            )

        result = self.dashboard.organizations.createOrganizationActionBatch(
            self.org_id,
            confirmed=auto_confirm,
            synchronous=synchronous,
            actions=actions
        )

        return self._parse_result(result)

    def get_batch_status(self, batch_id: str) -> ActionBatchResult:
        """
        Verifica status de um batch.

        Args:
            batch_id: ID do batch

        Returns:
            ActionBatchResult atualizado
        """
        result = self.dashboard.organizations.getOrganizationActionBatch(
            self.org_id,
            batch_id
        )

        return self._parse_result(result)

    def list_batches(self, status: Optional[str] = None) -> List[Dict]:
        """
        Lista action batches da organização.

        Args:
            status: Filtrar por status (pending, completed, failed)

        Returns:
            Lista de batches
        """
        params = {}
        if status:
            params['status'] = status

        return self.dashboard.organizations.getOrganizationActionBatches(
            self.org_id,
            **params
        )

    def delete_batch(self, batch_id: str) -> bool:
        """
        Deleta um batch (apenas se não confirmado).

        Args:
            batch_id: ID do batch

        Returns:
            True se deletado com sucesso
        """
        try:
            self.dashboard.organizations.deleteOrganizationActionBatch(
                self.org_id,
                batch_id
            )
            return True
        except Exception as e:
            print(f"Erro ao deletar batch {batch_id}: {e}")
            return False

    def _parse_result(self, result: Dict) -> ActionBatchResult:
        """Parseia resultado da API para ActionBatchResult."""
        status = result.get('status', {})

        return ActionBatchResult(
            batch_id=result.get('id'),
            status=status,
            confirmed=result.get('confirmed'),
            synchronous=result.get('synchronous'),
            total_actions=len(result.get('actions', [])),
            completed=status.get('completed', False),
            failed=status.get('failed', False),
            errors=status.get('errors', []),
            created_resources=status.get('createdResources', [])
        )

    # ============================================================
    # HELPERS PARA CASOS COMUNS
    # ============================================================

    def bulk_update_switch_ports(
        self,
        devices: List[Dict],
        port_config: Dict,
        port_filter: Optional[callable] = None
    ) -> ActionBatchResult:
        """
        Atualiza portas de múltiplos switches.

        Args:
            devices: Lista de devices (serials)
            port_config: Configuração a aplicar (ex: {'vlan': 100})
            port_filter: Função para filtrar portas (opcional)

        Returns:
            ActionBatchResult

        Example:
            # Atualizar VLAN de todas as portas access
            manager.bulk_update_switch_ports(
                devices,
                {'vlan': 100},
                lambda p: p['type'] == 'access'
            )
        """
        actions = []

        for device in devices:
            try:
                ports = self.dashboard.switch.getDeviceSwitchPorts(device['serial'])

                for port in ports:
                    # Aplicar filtro se fornecido
                    if port_filter and not port_filter(port):
                        continue

                    actions.append({
                        'resource': f'/devices/{device["serial"]}/switchPorts/{port["portId"]}',
                        'operation': 'update',
                        'body': port_config
                    })
            except Exception as e:
                print(f"Erro ao processar device {device['serial']}: {e}")

        return self.execute_batch(actions)

    def bulk_create_vlans(
        self,
        networks: List[str],
        vlan_config: Dict
    ) -> ActionBatchResult:
        """
        Cria mesma VLAN em múltiplas networks.

        Args:
            networks: Lista de network IDs
            vlan_config: Configuração da VLAN (id, name, subnet, etc)

        Returns:
            ActionBatchResult

        Example:
            manager.bulk_create_vlans(
                ['N_123', 'N_456'],
                {
                    'id': 100,
                    'name': 'Data',
                    'subnet': '10.0.100.0/24',
                    'applianceIp': '10.0.100.1'
                }
            )
        """
        actions = []

        for network_id in networks:
            actions.append({
                'resource': f'/networks/{network_id}/appliance/vlans',
                'operation': 'create',
                'body': vlan_config
            })

        return self.execute_batch(actions)

    def bulk_update_ssids(
        self,
        networks: List[str],
        ssid_number: int,
        ssid_config: Dict
    ) -> ActionBatchResult:
        """
        Atualiza SSID em múltiplas networks.

        Args:
            networks: Lista de network IDs
            ssid_number: Número do SSID (0-14)
            ssid_config: Configuração do SSID

        Returns:
            ActionBatchResult

        Example:
            manager.bulk_update_ssids(
                ['N_123', 'N_456'],
                0,
                {'name': 'CorpWiFi', 'enabled': True, 'authMode': 'psk'}
            )
        """
        actions = []

        for network_id in networks:
            actions.append({
                'resource': f'/networks/{network_id}/wireless/ssids/{ssid_number}',
                'operation': 'update',
                'body': ssid_config
            })

        return self.execute_batch(actions)

    def bulk_update_firewall_rules(
        self,
        networks: List[str],
        rules: List[Dict]
    ) -> ActionBatchResult:
        """
        Atualiza regras de firewall em múltiplas networks.

        Args:
            networks: Lista de network IDs
            rules: Lista de regras de firewall

        Returns:
            ActionBatchResult

        Example:
            manager.bulk_update_firewall_rules(
                ['N_123', 'N_456'],
                [
                    {
                        'comment': 'Block Telnet',
                        'policy': 'deny',
                        'protocol': 'tcp',
                        'destPort': '23'
                    }
                ]
            )
        """
        actions = []

        for network_id in networks:
            actions.append({
                'resource': f'/networks/{network_id}/appliance/firewall/l3FirewallRules',
                'operation': 'update',
                'body': {'rules': rules}
            })

        return self.execute_batch(actions)

    def bulk_reboot_devices(
        self,
        serials: List[str]
    ) -> ActionBatchResult:
        """
        Reinicia múltiplos devices.

        Args:
            serials: Lista de serials

        Returns:
            ActionBatchResult

        Example:
            manager.bulk_reboot_devices(['Q2XX-XXXX-XXXX', 'Q2YY-YYYY-YYYY'])
        """
        actions = []

        for serial in serials:
            actions.append({
                'resource': f'/devices/{serial}/reboot',
                'operation': 'create',
                'body': {}
            })

        return self.execute_batch(actions)

    def bulk_blink_leds(
        self,
        serials: List[str],
        duration: int = 20
    ) -> ActionBatchResult:
        """
        Blink LEDs de múltiplos devices.

        Args:
            serials: Lista de serials
            duration: Duração em segundos

        Returns:
            ActionBatchResult
        """
        actions = []

        for serial in serials:
            actions.append({
                'resource': f'/devices/{serial}/blinkLeds',
                'operation': 'create',
                'body': {'duration': duration}
            })

        return self.execute_batch(actions)


# ============================================================
# EXEMPLO DE USO
# ============================================================

def example_usage():
    """Exemplo de uso do ActionBatchManager."""
    import os
    from pathlib import Path

    # Carregar credenciais
    creds_path = Path.home() / ".meraki" / "credentials"
    # ... (carregar api_key e org_id)

    # Inicializar
    dashboard = meraki.DashboardAPI("YOUR_API_KEY")
    manager = ActionBatchManager(dashboard, "YOUR_ORG_ID")

    # Exemplo 1: Preview antes de aplicar
    actions = [
        {
            'resource': '/devices/SERIAL/switchPorts/1',
            'operation': 'update',
            'body': {'vlan': 100, 'enabled': True}
        }
    ]

    preview = manager.preview_batch(actions)
    print(f"Preview: {preview}")

    if not preview.failed:
        # Aplicar
        result = manager.execute_batch(actions)
        print(f"Resultado: {result}")

    # Exemplo 2: Atualizar VLAN em todos os switches
    devices = dashboard.organizations.getOrganizationDevices(
        "ORG_ID",
        productTypes=['switch']
    )

    result = manager.bulk_update_switch_ports(
        devices,
        {'vlan': 200},
        lambda p: p['type'] == 'access'  # Apenas portas access
    )

    # Exemplo 3: Criar VLAN em múltiplas networks
    networks = ['N_123', 'N_456', 'N_789']
    result = manager.bulk_create_vlans(
        networks,
        {
            'id': 100,
            'name': 'DataVLAN',
            'subnet': '10.0.100.0/24',
            'applianceIp': '10.0.100.1'
        }
    )


if __name__ == '__main__':
    example_usage()
