"""
Meraki Workflow Scripts

Automacao de configuracao Meraki via linguagem natural.
"""

__version__ = "1.0.0"

# Auth
from .auth import (
    MerakiProfile,
    load_profile,
    list_profiles,
    validate_credentials,
    CredentialsNotFoundError,
    InvalidProfileError,
)

# API Client
from .api import (
    MerakiClient,
    get_client,
)

# Discovery
from .discovery import (
    DiscoveryResult,
    NetworkInfo,
    DeviceInfo,
    full_discovery,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    compare_snapshots,
)

# Config
from .config import (
    ConfigAction,
    ConfigResult,
    configure_ssid,
    create_vlan,
    add_firewall_rule,
    backup_config,
)

# Changelog
from .changelog import (
    ChangeType,
    ChangeEntry,
    log_change,
    auto_commit_change,
    log_discovery_change,
    log_config_change,
    log_workflow_change,
    log_report_change,
)

# Workflow
from .workflow import (
    TriggerType,
    ActionType,
    WorkflowVariable,
    WorkflowAction,
    WorkflowTrigger,
    Workflow,
    WorkflowBuilder,
    export_workflow,
    save_workflow,
    load_workflow,
    list_workflows,
    validate_workflow,
    create_device_offline_handler,
    create_firmware_compliance_check,
    create_scheduled_report,
    create_security_alert_handler,
    workflow_to_diagram,
    generate_import_instructions,
    WorkflowError,
    WorkflowValidationError,
)

# Report
from .report import (
    ReportBuilder,
    Report,
    ReportType,
    ReportSection,
    generate_discovery_report,
    generate_changes_report,
    save_html,
    render_pdf,
)

# CLI
from .cli import cli, main

__all__ = [
    # Auth
    "MerakiProfile",
    "load_profile",
    "list_profiles",
    "validate_credentials",
    "CredentialsNotFoundError",
    "InvalidProfileError",
    # API
    "MerakiClient",
    "get_client",
    # Discovery
    "DiscoveryResult",
    "NetworkInfo",
    "DeviceInfo",
    "full_discovery",
    "save_snapshot",
    "load_snapshot",
    "list_snapshots",
    "compare_snapshots",
    # Config
    "ConfigAction",
    "ConfigResult",
    "configure_ssid",
    "create_vlan",
    "add_firewall_rule",
    "backup_config",
    # Changelog
    "ChangeType",
    "ChangeEntry",
    "log_change",
    "auto_commit_change",
    "log_discovery_change",
    "log_config_change",
    "log_workflow_change",
    "log_report_change",
    # Workflow
    "TriggerType",
    "ActionType",
    "WorkflowVariable",
    "WorkflowAction",
    "WorkflowTrigger",
    "Workflow",
    "WorkflowBuilder",
    "export_workflow",
    "save_workflow",
    "load_workflow",
    "list_workflows",
    "validate_workflow",
    "create_device_offline_handler",
    "create_firmware_compliance_check",
    "create_scheduled_report",
    "create_security_alert_handler",
    "workflow_to_diagram",
    "generate_import_instructions",
    "WorkflowError",
    "WorkflowValidationError",
    # Report
    "ReportBuilder",
    "Report",
    "ReportType",
    "ReportSection",
    "generate_discovery_report",
    "generate_changes_report",
    "save_html",
    "render_pdf",
    # CLI
    "cli",
    "main",
]
