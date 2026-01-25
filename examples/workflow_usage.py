#!/usr/bin/env python3
"""
Exemplos de uso do scripts/workflow.py

Este script demonstra como criar workflows para o Meraki Dashboard.
"""

import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.workflow import (
    WorkflowBuilder,
    TriggerType,
    ActionType,
    save_workflow,
    create_device_offline_handler,
    create_firmware_compliance_check,
    create_scheduled_report,
    create_security_alert_handler,
    workflow_to_diagram,
    generate_import_instructions,
    validate_workflow
)


def example_custom_workflow():
    """Exemplo: Criar workflow customizado com builder."""
    print("\n=== Exemplo 1: Workflow Customizado ===\n")

    workflow = (
        WorkflowBuilder(
            unique_name="port-security-violation",
            name="Port Security Violation Handler",
            description="Desabilita porta quando detecta violacao de seguranca"
        )
        # Trigger: Webhook de violacao
        .add_trigger(
            TriggerType.WEBHOOK,
            event="switch.port.security_violation"
        )
        # Input: Serial do switch e numero da porta
        .add_input_variable("switch_serial", "string", required=True)
        .add_input_variable("port_number", "string", required=True)
        # Acao 1: Desabilitar porta
        .add_action(
            "disable_port",
            ActionType.MERAKI_UPDATE_PORT,
            serial="$input.switch_serial$",
            port_id="$input.port_number$",
            enabled=False
        )
        # Acao 2: Notificar no Slack
        .add_action(
            "notify_slack",
            ActionType.SLACK_POST,
            channel="#security-alerts",
            message=":warning: Porta $input.port_number$ no switch $input.switch_serial$ desabilitada por violacao de seguranca"
        )
        # Acao 3: Criar ticket no Jira
        .add_action(
            "create_jira_ticket",
            ActionType.JIRA_ISSUE,
            project="NET",
            issue_type="Incident",
            summary="Port Security Violation - $input.switch_serial$:$input.port_number$",
            description="Porta automaticamente desabilitada por violacao de seguranca"
        )
        .build()
    )

    # Validar
    errors = validate_workflow(workflow)
    if errors:
        print(f"Erros: {errors}")
        return

    print(workflow_to_diagram(workflow))

    # Salvar
    path = save_workflow(workflow, "exemplo")
    print(f"\nWorkflow salvo em: {path}")

    return workflow


def example_using_templates():
    """Exemplo: Usar templates pre-definidos."""
    print("\n=== Exemplo 2: Templates Pre-definidos ===\n")

    # Template 1: Device Offline Handler
    print("1. Device Offline Handler")
    workflow1 = create_device_offline_handler(
        slack_channel="#network-alerts",
        wait_minutes=10
    )
    path1 = save_workflow(workflow1, "exemplo")
    print(f"   Salvo em: {path1}")

    # Template 2: Firmware Compliance
    print("\n2. Firmware Compliance Check")
    workflow2 = create_firmware_compliance_check(
        target_version="MX 18.211",
        email_recipients=["network-team@example.com", "ops@example.com"]
    )
    path2 = save_workflow(workflow2, "exemplo")
    print(f"   Salvo em: {path2}")

    # Template 3: Scheduled Report
    print("\n3. Scheduled Report")
    workflow3 = create_scheduled_report(
        report_type="discovery",
        schedule_cron="0 8 * * 1",  # Segundas as 8h
        email_recipients=["cto@example.com"]
    )
    path3 = save_workflow(workflow3, "exemplo")
    print(f"   Salvo em: {path3}")

    # Template 4: Security Alert Handler
    print("\n4. Security Alert Handler")
    workflow4 = create_security_alert_handler(
        slack_channel="#security",
        pagerduty_enabled=True
    )
    path4 = save_workflow(workflow4, "exemplo")
    print(f"   Salvo em: {path4}")


def example_conditional_actions():
    """Exemplo: Acoes condicionais."""
    print("\n=== Exemplo 3: Acoes Condicionais ===\n")

    workflow = (
        WorkflowBuilder(
            unique_name="smart-device-reboot",
            name="Smart Device Reboot",
            description="Reboot device apenas se offline por muito tempo"
        )
        .add_trigger(TriggerType.WEBHOOK, event="device.status.check")
        .add_input_variable("device_serial", "string", required=True)
        # Variavel para contar tentativas
        .add_variable("reboot_attempts", "number", 0, "Numero de tentativas de reboot")
        # Acao 1: Get device status
        .add_action(
            "get_status",
            ActionType.MERAKI_GET_DEVICE_STATUS,
            serial="$input.device_serial$"
        )
        # Acao 2: Reboot SE offline E tentativas < 3
        .add_action(
            "reboot_device",
            ActionType.MERAKI_REBOOT_DEVICE,
            condition="$actions.get_status.status$ == 'offline' AND $vars.reboot_attempts$ < 3",
            serial="$input.device_serial$"
        )
        # Acao 3: Incrementar contador
        .add_action(
            "increment_counter",
            ActionType.CORE_SET_VARIABLE,
            condition="$actions.reboot_device.executed$ == true",
            variable="reboot_attempts",
            value="$vars.reboot_attempts$ + 1"
        )
        # Acao 4: Notificar SE ainda offline apos 3 tentativas
        .add_action(
            "escalate",
            ActionType.PAGERDUTY_INCIDENT,
            condition="$vars.reboot_attempts$ >= 3 AND $actions.get_status.status$ == 'offline'",
            title="Device $input.device_serial$ nao responde apos 3 reboots",
            urgency="high"
        )
        .build()
    )

    print(workflow_to_diagram(workflow))

    path = save_workflow(workflow, "exemplo")
    print(f"\nWorkflow salvo em: {path}")


def example_loop_actions():
    """Exemplo: Loop sobre multiplos recursos."""
    print("\n=== Exemplo 4: Loop sobre Devices ===\n")

    workflow = (
        WorkflowBuilder(
            unique_name="bulk-port-config",
            name="Bulk Port Configuration",
            description="Configura multiplas portas em batch"
        )
        .add_trigger(TriggerType.API_CALL)
        .add_input_variable("switch_serial", "string", required=True)
        .add_input_variable("port_list", "array", required=True, description="Lista de portas a configurar")
        .add_input_variable("vlan_id", "number", required=True)
        # Loop sobre cada porta
        .add_action(
            "configure_ports",
            ActionType.CORE_LOOP,
            items="$input.port_list$",
            actions=[
                {
                    "name": "update_port",
                    "type": ActionType.MERAKI_UPDATE_PORT.value,
                    "properties": {
                        "serial": "$input.switch_serial$",
                        "port_id": "$item$",
                        "vlan": "$input.vlan_id$",
                        "type": "access"
                    }
                }
            ]
        )
        # Notificar ao concluir
        .add_action(
            "notify_completion",
            ActionType.SLACK_POST,
            channel="#network-ops",
            message="Configuracao em batch concluida: $len(input.port_list)$ portas atualizadas no switch $input.switch_serial$"
        )
        .build()
    )

    print(workflow_to_diagram(workflow))

    path = save_workflow(workflow, "exemplo")
    print(f"\nWorkflow salvo em: {path}")


def example_import_instructions():
    """Exemplo: Gerar instrucoes de importacao."""
    print("\n=== Exemplo 5: Instrucoes de Importacao ===\n")

    workflow = create_device_offline_handler()

    instructions = generate_import_instructions(workflow, "exemplo")
    print(instructions)

    # Salvar instrucoes em arquivo
    instructions_path = Path("clients/exemplo/workflows/IMPORT_INSTRUCTIONS.md")
    instructions_path.parent.mkdir(parents=True, exist_ok=True)
    instructions_path.write_text(instructions)

    print(f"\nInstrucoes salvas em: {instructions_path}")


def main():
    """Executa todos os exemplos."""
    print("=" * 60)
    print("EXEMPLOS DE USO - scripts/workflow.py")
    print("=" * 60)

    # Exemplo 1: Workflow customizado
    example_custom_workflow()

    # Exemplo 2: Templates
    example_using_templates()

    # Exemplo 3: Acoes condicionais
    example_conditional_actions()

    # Exemplo 4: Loop
    example_loop_actions()

    # Exemplo 5: Instrucoes de importacao
    example_import_instructions()

    print("\n" + "=" * 60)
    print("TODOS OS EXEMPLOS CONCLUIDOS")
    print("=" * 60)
    print("\nWorkflows gerados em: clients/exemplo/workflows/")
    print("\nProximos passos:")
    print("1. Revisar os arquivos JSON gerados")
    print("2. Importar no Meraki Dashboard")
    print("3. Configurar credenciais (Slack, Jira, PagerDuty, etc)")
    print("4. Ativar os workflows")


if __name__ == "__main__":
    main()
