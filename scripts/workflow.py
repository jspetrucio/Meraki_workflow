"""
Gerador de workflows JSON para Meraki Dashboard (formato SecureX/Cisco Workflows).

IMPORTANTE: Workflows NAO podem ser criados via API - apenas via Dashboard UI.
Este script gera arquivos JSON para importacao manual pelo usuario.

O formato JSON gerado e compativel com Cisco Workflows (SecureX Orchestration),
que e o motor usado pelo Meraki Dashboard Workflows.

Formato SecureX:
- unique_name: definition_workflow_<ID>
- type: generic.workflow
- base_type: workflow
- object_type: definition_workflow
- Variables: schema_id, properties (scope, name, type, is_required)
- Actions: definition_activity com object_type

Uso:
    from scripts.workflow import WorkflowBuilder, TriggerType, ActionType

    # Criar workflow com builder
    workflow = (
        WorkflowBuilder("device-offline-handler", "Device Offline Handler")
        .add_trigger(TriggerType.WEBHOOK, event="device.status.change")
        .add_action("check_status", ActionType.MERAKI_GET_DEVICE)
        .add_action("notify", ActionType.SLACK_POST, channel="#alerts")
        .build()
    )

    # Salvar
    path = save_workflow(workflow, "cliente-acme")

    # Ou usar template
    workflow = create_device_offline_handler(slack_channel="#alerts")
"""

import json
import logging
import secrets
import string
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

try:
    from .changelog import ChangeType, log_workflow_change
except ImportError:
    # Para execucao direta via __main__
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.changelog import ChangeType, log_workflow_change

logger = logging.getLogger(__name__)


# ==================== SecureX ID Generator ====================

def generate_securex_id(prefix: str = "workflow") -> str:
    """
    Gera um ID unico no formato SecureX/Cisco Workflows.

    Formato: definition_{prefix}_{ID} onde ID e 37 caracteres alfanumericos
    O ID comeca com "02" para identificar workflows criados externamente.

    Exemplos:
    - definition_workflow_02NXTSAQL5ZNK3kEJpVUecfDz1ZNss1zGXd
    - definition_activity_02NXTSATP1NXX3sJziA9MInu5AYQyZAqHjU
    - variable_workflow_02NXTSAR6KFTM0WBeVsIxZih1kDUiGd7aJw
    - category_02NXV6O12LF114DhKxx98npicaIPTPJql2v

    Args:
        prefix: Prefixo (workflow, activity, variable, trigger, category)

    Returns:
        ID unico no formato SecureX
    """
    # Gera ID alfanumerico de 35 caracteres + "02" prefix = 37 chars total
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    unique_id = "02" + ''.join(secrets.choice(chars) for _ in range(35))

    if prefix == "variable":
        return f"variable_workflow_{unique_id}"
    elif prefix == "activity":
        return f"definition_activity_{unique_id}"
    elif prefix == "trigger":
        return f"definition_trigger_{unique_id}"
    elif prefix == "category":
        return f"category_{unique_id}"
    else:
        return f"definition_{prefix}_{unique_id}"


def type_to_schema_id(var_type: str) -> str:
    """
    Converte tipo simples para schema_id SecureX.

    Args:
        var_type: Tipo simples (string, number, boolean, array, object)

    Returns:
        Schema ID no formato SecureX
    """
    type_mapping = {
        "string": "datatype.string",
        "number": "datatype.integer",
        "integer": "datatype.integer",
        "float": "datatype.decimal",
        "boolean": "datatype.boolean",
        "array": "datatype.string",  # Arrays geralmente serializados como string JSON
        "object": "datatype.string",  # Objects geralmente serializados como string JSON
        "date": "datatype.date",
        "secure_string": "datatype.secure_string"
    }
    return type_mapping.get(var_type, "datatype.string")


# ==================== Enums ====================

class TriggerType(Enum):
    """Tipos de triggers para workflows."""

    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    API_CALL = "api_call"
    EMAIL = "email"


class ActionType(Enum):
    """Tipos de acoes disponiveis em workflows."""

    # Meraki API
    MERAKI_GET_DEVICE = "meraki.get_device"
    MERAKI_GET_NETWORK = "meraki.get_network"
    MERAKI_UPDATE_DEVICE = "meraki.update_device"
    MERAKI_REBOOT_DEVICE = "meraki.reboot_device"
    MERAKI_GET_DEVICE_STATUS = "meraki.get_device_status"
    MERAKI_UPDATE_PORT = "meraki.update_port"
    MERAKI_GET_CLIENTS = "meraki.get_clients"

    # Notificacao
    SLACK_POST = "slack.post_message"
    TEAMS_POST = "teams.post_message"
    EMAIL_SEND = "email.send"
    PAGERDUTY_INCIDENT = "pagerduty.create_incident"
    WEBHOOK_POST = "webhook.post"

    # ITSM
    SERVICENOW_TICKET = "servicenow.create_ticket"
    JIRA_ISSUE = "jira.create_issue"

    # Logica de controle
    CORE_SLEEP = "core.sleep"
    CORE_CONDITION = "core.condition"
    CORE_LOOP = "core.loop"
    CORE_PARALLEL = "core.parallel"
    CORE_SET_VARIABLE = "core.set_variable"

    # Python
    PYTHON_EXECUTE = "python.execute"


# ==================== Data Classes ====================

@dataclass
class WorkflowVariable:
    """Variavel de workflow no formato SecureX."""

    name: str
    var_type: str  # string, number, boolean, array, object
    default_value: Any = None
    description: str = ""
    required: bool = False
    scope: str = "local"  # local, input, output
    unique_name: str = ""  # Gerado automaticamente se vazio

    def to_dict(self) -> dict:
        """Converte para dicionario no formato SecureX."""
        if not self.unique_name:
            self.unique_name = generate_securex_id("variable")

        schema_id = type_to_schema_id(self.var_type)

        return {
            "schema_id": schema_id,
            "properties": {
                "value": self.default_value if self.default_value is not None else "",
                "scope": self.scope,
                "name": self.name,
                "type": schema_id,
                "description": self.description,
                "is_required": self.required,
                "is_invisible": False
            },
            "unique_name": self.unique_name,
            "object_type": "variable_workflow"
        }

    def to_simple_dict(self) -> dict:
        """Formato simplificado (para compatibilidade)."""
        return {
            "name": self.name,
            "type": self.var_type,
            "default": self.default_value,
            "description": self.description,
            "required": self.required
        }


@dataclass
class WorkflowAction:
    """Acao de workflow no formato SecureX."""

    name: str
    action_type: ActionType
    properties: dict = field(default_factory=dict)
    condition: Optional[str] = None  # expressao condicional
    unique_name: str = ""  # Gerado automaticamente se vazio
    title: str = ""  # Titulo (display_name)

    def to_dict(self, workflow_id: str = "", variables: list = None) -> dict:
        """
        Converte para dicionario no formato SecureX.

        Args:
            workflow_id: ID unico do workflow (para referencias de variaveis)
            variables: Lista de variaveis do workflow
        """
        if not self.unique_name:
            self.unique_name = generate_securex_id("activity")

        if not self.title:
            self.title = self.name

        # Determina se e uma acao Meraki API
        is_meraki_action = self.action_type.value.startswith("meraki.")

        if is_meraki_action:
            return self._build_meraki_api_action(workflow_id, variables or [])
        else:
            return self._build_standard_action(workflow_id, variables or [])

    def _build_meraki_api_action(self, workflow_id: str, variables: list) -> dict:
        """Constroi acao Meraki no formato correto (meraki.api_request)."""
        api_config = self._get_api_config()

        # Substitui referencias de variaveis no formato correto
        api_url = self._resolve_variable_refs(api_config["url"], workflow_id, variables)
        api_body = self._resolve_variable_refs(
            json.dumps(api_config.get("body", {})) if api_config.get("body") else "",
            workflow_id,
            variables
        )

        return {
            "unique_name": self.unique_name,
            "name": "Generic Meraki API Request",
            "title": self.title,
            "type": "meraki.api_request",
            "base_type": "activity",
            "properties": {
                "action_timeout": 180,
                "api_body": api_body,
                "api_method": api_config["method"],
                "api_url": api_url,
                "continue_on_failure": False,
                "display_name": self.title,
                "runtime_user": {
                    "target_default": True
                },
                "skip_execution": False,
                "target": {
                    "use_workflow_target": True
                }
            },
            "object_type": "definition_activity"
        }

    def _build_standard_action(self, workflow_id: str, variables: list) -> dict:
        """Constroi acao padrao (non-Meraki)."""
        props = self._build_properties(workflow_id, variables)

        return {
            "unique_name": self.unique_name,
            "name": self.name,
            "title": self.title,
            "type": self._map_action_type(),
            "base_type": "activity",
            "properties": props,
            "object_type": "definition_activity"
        }

    def _get_api_config(self) -> dict:
        """Retorna configuracao da API para o tipo de acao Meraki."""
        api_configs = {
            "meraki.get_device": {
                "method": "GET",
                "url": "/api/v1/devices/{serial}",
                "body": None
            },
            "meraki.get_network": {
                "method": "GET",
                "url": "/api/v1/networks/{networkId}",
                "body": None
            },
            "meraki.update_device": {
                "method": "PUT",
                "url": "/api/v1/devices/{serial}",
                "body": {"name": "", "tags": []}
            },
            "meraki.reboot_device": {
                "method": "POST",
                "url": "/api/v1/devices/{serial}/reboot",
                "body": None
            },
            "meraki.get_device_status": {
                "method": "GET",
                "url": "/api/v1/organizations/{organizationId}/devices/statuses",
                "body": None
            },
            "meraki.update_port": {
                "method": "PUT",
                "url": "/api/v1/devices/{serial}/switch/ports/{portId}",
                "body": {}
            },
            "meraki.get_clients": {
                "method": "GET",
                "url": "/api/v1/networks/{networkId}/clients",
                "body": None
            }
        }

        config = api_configs.get(self.action_type.value, {
            "method": "GET",
            "url": "/api/v1/devices/{serial}",
            "body": None
        })

        # Substitui placeholders com valores das properties
        url = config["url"]
        for key, value in self.properties.items():
            url = url.replace(f"{{{key}}}", str(value))

        config["url"] = url
        return config

    def _resolve_variable_refs(self, text: str, workflow_id: str, variables: list) -> str:
        """
        Resolve referencias de variaveis para o formato SecureX.

        Converte:
        - $input.var_name$ -> $workflow.{workflow_id}.input.{var_unique_name}$
        - $vars.var_name$ -> $workflow.{workflow_id}.local.{var_unique_name}$
        """
        if not text or not workflow_id:
            return text

        # Cria mapa de nome -> unique_name
        var_map = {}
        for v in variables:
            props = v.get("properties", {})
            var_map[props.get("name", "")] = {
                "unique_name": v.get("unique_name", ""),
                "scope": props.get("scope", "local")
            }

        # Substitui $input.name$ e $vars.name$
        import re

        def replace_var(match):
            scope = match.group(1)
            var_name = match.group(2)

            if var_name in var_map:
                info = var_map[var_name]
                return f"$workflow.{workflow_id}.{info['scope']}.{info['unique_name']}$"
            return match.group(0)

        # Pattern: $input.name$ ou $vars.name$
        pattern = r'\$(input|vars)\.([a-zA-Z_][a-zA-Z0-9_]*)\$'
        return re.sub(pattern, replace_var, text)

    def _map_action_type(self) -> str:
        """Mapeia tipo de acao para formato SecureX."""
        type_mapping = {
            "slack.post_message": "slack.post_message",
            "teams.post_message": "teams.post_message",
            "email.send": "email.send_message",
            "pagerduty.create_incident": "pagerduty.create_incident",
            "webhook.post": "web-service.http_request",
            "servicenow.create_ticket": "servicenow.create_incident",
            "jira.create_issue": "jira.create_issue",
            "core.sleep": "core.sleep",
            "core.condition": "logic.condition_block",
            "core.loop": "logic.for_each",
            "core.parallel": "logic.parallel_block",
            "core.set_variable": "core.set_variable",
            "python.execute": "python3.script"
        }
        return type_mapping.get(self.action_type.value, self.action_type.value)

    def _build_properties(self, workflow_id: str = "", variables: list = None) -> dict:
        """Constroi propriedades no formato SecureX."""
        props = {}

        # Copia properties, resolvendo referencias de variaveis
        for key, value in self.properties.items():
            if isinstance(value, str):
                value = self._resolve_variable_refs(value, workflow_id, variables or [])
            props[key] = value

        # Adiciona conditional se existir
        if self.condition:
            condition_resolved = self._resolve_variable_refs(self.condition, workflow_id, variables or [])
            props["skip_execution"] = False
            props["condition"] = {
                "left_operand": condition_resolved.split("==")[0].strip() if "==" in condition_resolved else condition_resolved,
                "operator": "eq" if "==" in condition_resolved else "ne",
                "right_operand": condition_resolved.split("==")[1].strip().strip("'\"") if "==" in condition_resolved else ""
            }

        return props

    def to_simple_dict(self) -> dict:
        """Formato simplificado (para compatibilidade)."""
        result = {
            "name": self.name,
            "type": self.action_type.value,
            "properties": self.properties
        }
        if self.condition:
            result["condition"] = self.condition
        return result


@dataclass
class WorkflowTrigger:
    """Trigger de workflow no formato SecureX."""

    trigger_type: TriggerType
    properties: dict = field(default_factory=dict)
    unique_name: str = ""  # Gerado automaticamente se vazio

    def to_dict(self) -> dict:
        """Converte para dicionario no formato SecureX."""
        if not self.unique_name:
            self.unique_name = generate_securex_id("trigger")

        trigger_type_map = {
            "webhook": "trigger.webhook",
            "schedule": "trigger.schedule",
            "api_call": "trigger.api_call",
            "email": "trigger.email"
        }

        return {
            "unique_name": self.unique_name,
            "type": trigger_type_map.get(self.trigger_type.value, self.trigger_type.value),
            "base_type": "trigger",
            "properties": self.properties,
            "object_type": "definition_trigger"
        }

    def to_simple_dict(self) -> dict:
        """Formato simplificado."""
        return {
            "type": self.trigger_type.value,
            "properties": self.properties
        }


@dataclass
class Workflow:
    """Representacao completa de um workflow no formato SecureX/Cisco Workflows."""

    unique_name: str  # Nome legivel (sera prefixado com definition_workflow_)
    name: str
    description: str
    triggers: list[WorkflowTrigger]
    actions: list[WorkflowAction]
    variables: list[WorkflowVariable] = field(default_factory=list)
    input_variables: list[WorkflowVariable] = field(default_factory=list)
    _securex_id: str = ""  # ID SecureX gerado
    _category_id: str = ""  # ID da categoria

    def to_dict(self) -> dict:
        """
        Converte workflow para formato SecureX/Cisco Workflows.

        Este formato e compativel com Meraki Dashboard Workflows import.
        IMPORTANTE: Inclui objeto `categories` na raiz (OBRIGATORIO para import).
        """
        # Gera ID SecureX se nao existir
        if not self._securex_id:
            self._securex_id = generate_securex_id("workflow")

        # Gera ID da categoria
        if not self._category_id:
            self._category_id = generate_securex_id("category")

        # Combina variables e input_variables
        # Input variables tem scope="input"
        all_variables = []

        for var in self.input_variables:
            var.scope = "input"
            all_variables.append(var.to_dict())

        for var in self.variables:
            var.scope = "local"
            all_variables.append(var.to_dict())

        # Constroi actions com referencia ao workflow_id para variaveis
        actions_list = []
        for action in self.actions:
            action_dict = action.to_dict(self._securex_id, all_variables)
            actions_list.append(action_dict)

        # NOTA: Triggers NAO sao incluidos no JSON de import
        # Eles sao configurados manualmente no Dashboard apos importar
        # Mantemos internamente para documentacao/instrucoes

        return {
            "workflow": {
                "unique_name": self._securex_id,
                "name": self.name,
                "title": self.name,
                "type": "generic.workflow",
                "base_type": "workflow",
                "variables": all_variables,
                "properties": {
                    "atomic": {
                        "is_atomic": False
                    },
                    "delete_workflow_instance": False,
                    "description": self.description,
                    "display_name": self.name,
                    "runtime_user": {
                        "target_default": True
                    },
                    "target": {
                        "target_type": "meraki.endpoint",
                        "specify_on_workflow_start": True
                    }
                },
                "object_type": "definition_workflow",
                "actions": actions_list,
                "categories": [self._category_id]
            },
            "categories": {
                self._category_id: {
                    "unique_name": self._category_id,
                    "name": "Meraki Automation",
                    "title": "Meraki Automation",
                    "type": "basic.category",
                    "base_type": "category",
                    "category_type": "custom",
                    "object_type": "category"
                }
            }
        }

    def to_simple_dict(self) -> dict:
        """Formato simplificado (para debug/compatibilidade)."""
        return {
            "workflow": {
                "unique_name": self.unique_name,
                "name": self.name,
                "description": self.description,
                "type": "automation",
                "schema_version": "1.0.0"
            },
            "triggers": [t.to_simple_dict() for t in self.triggers],
            "actions": [a.to_simple_dict() for a in self.actions],
            "variables": [v.to_simple_dict() for v in self.variables],
            "input_variables": [v.to_simple_dict() for v in self.input_variables]
        }


# ==================== Exceptions ====================

class WorkflowError(Exception):
    """Erro geral de workflow."""
    pass


class WorkflowValidationError(Exception):
    """Erro de validacao de workflow."""
    pass


# ==================== Builder Pattern ====================

class WorkflowBuilder:
    """
    Builder para criar workflows de forma fluente.

    Example:
        workflow = (
            WorkflowBuilder("my-workflow", "My Workflow")
            .add_trigger(TriggerType.WEBHOOK, event="test")
            .add_action("step1", ActionType.MERAKI_GET_DEVICE)
            .add_variable("wait_time", "number", 300)
            .build()
        )
    """

    def __init__(self, unique_name: str, name: str, description: str = ""):
        """
        Inicializa o builder.

        Args:
            unique_name: Nome unico do workflow (usado como ID)
            name: Nome legivel do workflow
            description: Descricao do workflow
        """
        self.unique_name = unique_name
        self.name = name
        self.description = description
        self._triggers: list[WorkflowTrigger] = []
        self._actions: list[WorkflowAction] = []
        self._variables: list[WorkflowVariable] = []
        self._input_variables: list[WorkflowVariable] = []

    def add_trigger(
        self,
        trigger_type: TriggerType,
        **properties
    ) -> "WorkflowBuilder":
        """
        Adiciona um trigger ao workflow.

        Args:
            trigger_type: Tipo do trigger
            **properties: Propriedades do trigger

        Returns:
            Self para method chaining

        Example:
            .add_trigger(TriggerType.WEBHOOK, event="device.status.change")
            .add_trigger(TriggerType.SCHEDULE, cron="0 8 * * 1")
        """
        trigger = WorkflowTrigger(
            trigger_type=trigger_type,
            properties=properties
        )
        self._triggers.append(trigger)
        return self

    def add_action(
        self,
        name: str,
        action_type: ActionType,
        condition: Optional[str] = None,
        **properties
    ) -> "WorkflowBuilder":
        """
        Adiciona uma acao ao workflow.

        Args:
            name: Nome da acao (identificador unico no workflow)
            action_type: Tipo da acao
            condition: Condicao para executar a acao (opcional)
            **properties: Propriedades da acao

        Returns:
            Self para method chaining

        Example:
            .add_action("get_device", ActionType.MERAKI_GET_DEVICE, serial="$input.serial$")
            .add_action("notify", ActionType.SLACK_POST, channel="#alerts", message="Alert!")
        """
        action = WorkflowAction(
            name=name,
            action_type=action_type,
            properties=properties,
            condition=condition
        )
        self._actions.append(action)
        return self

    def add_variable(
        self,
        name: str,
        var_type: str,
        default_value: Any = None,
        description: str = ""
    ) -> "WorkflowBuilder":
        """
        Adiciona uma variavel interna ao workflow.

        Args:
            name: Nome da variavel
            var_type: Tipo (string, number, boolean, array, object)
            default_value: Valor padrao
            description: Descricao da variavel

        Returns:
            Self para method chaining

        Example:
            .add_variable("wait_time", "number", 300, "Tempo de espera em segundos")
        """
        variable = WorkflowVariable(
            name=name,
            var_type=var_type,
            default_value=default_value,
            description=description,
            required=False
        )
        self._variables.append(variable)
        return self

    def add_input_variable(
        self,
        name: str,
        var_type: str,
        required: bool = True,
        description: str = ""
    ) -> "WorkflowBuilder":
        """
        Adiciona uma variavel de input ao workflow.

        Input variables sao fornecidas quando o workflow e executado.

        Args:
            name: Nome da variavel
            var_type: Tipo (string, number, boolean, array, object)
            required: Se e obrigatorio
            description: Descricao da variavel

        Returns:
            Self para method chaining

        Example:
            .add_input_variable("device_serial", "string", required=True)
        """
        variable = WorkflowVariable(
            name=name,
            var_type=var_type,
            default_value=None,
            description=description,
            required=required
        )
        self._input_variables.append(variable)
        return self

    def build(self) -> Workflow:
        """
        Constroi o workflow final.

        Returns:
            Workflow completo

        Raises:
            WorkflowError: Se configuracao invalida
        """
        if not self._triggers:
            raise WorkflowError("Workflow precisa de pelo menos um trigger")

        if not self._actions:
            raise WorkflowError("Workflow precisa de pelo menos uma acao")

        return Workflow(
            unique_name=self.unique_name,
            name=self.name,
            description=self.description,
            triggers=self._triggers,
            actions=self._actions,
            variables=self._variables,
            input_variables=self._input_variables
        )


# ==================== Export / Import ====================

def export_workflow(workflow: Workflow) -> dict:
    """
    Converte Workflow para dict JSON do formato Meraki.

    Args:
        workflow: Workflow a exportar

    Returns:
        Dicionario no formato Meraki Dashboard
    """
    return workflow.to_dict()


def save_workflow(workflow: Workflow, client_name: str) -> Path:
    """
    Salva workflow em clients/{nome}/workflows/{unique_name}.json

    Args:
        workflow: Workflow a salvar
        client_name: Nome do cliente

    Returns:
        Path do arquivo salvo

    Raises:
        WorkflowError: Se houver erro ao salvar
    """
    # Criar diretorio de workflows do cliente
    workflows_dir = Path.cwd() / "clients" / client_name / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Path do arquivo
    filename = f"{workflow.unique_name}.json"
    filepath = workflows_dir / filename

    try:
        # Exportar e salvar
        workflow_dict = export_workflow(workflow)

        with open(filepath, "w") as f:
            json.dump(workflow_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Workflow salvo: {filepath}")

        # Registrar no changelog
        log_workflow_change(
            client_name=client_name,
            workflow_name=workflow.name,
            workflow_type="automation"
        )

        return filepath

    except IOError as e:
        raise WorkflowError(f"Erro ao salvar workflow: {e}")


def load_workflow(path: Path) -> Workflow:
    """
    Carrega workflow de arquivo JSON (suporta formato SecureX e simplificado).

    Args:
        path: Path do arquivo JSON

    Returns:
        Workflow carregado

    Raises:
        WorkflowError: Se houver erro ao carregar
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)

        # Parse do JSON
        workflow_info = data["workflow"]

        # Detectar formato (SecureX vs simplificado)
        is_securex = workflow_info.get("type") == "generic.workflow"

        if is_securex:
            return _load_securex_workflow(data)
        else:
            return _load_simple_workflow(data)

    except (IOError, json.JSONDecodeError, KeyError) as e:
        raise WorkflowError(f"Erro ao carregar workflow: {e}")


def _load_securex_workflow(data: dict) -> Workflow:
    """Carrega workflow no formato SecureX."""
    workflow_info = data["workflow"]

    # Parse triggers
    triggers = []
    for t in workflow_info.get("triggers", []):
        trigger_type_str = t.get("type", "").replace("trigger.", "")
        try:
            trigger = WorkflowTrigger(
                trigger_type=TriggerType(trigger_type_str),
                properties=t.get("properties", {}),
                unique_name=t.get("unique_name", "")
            )
            triggers.append(trigger)
        except ValueError:
            # Tipo desconhecido, usar webhook como fallback
            triggers.append(WorkflowTrigger(
                trigger_type=TriggerType.WEBHOOK,
                properties=t.get("properties", {}),
                unique_name=t.get("unique_name", "")
            ))

    # Parse actions
    actions = []
    for a in workflow_info.get("actions", []):
        action_type_str = a.get("type", "core.sleep")
        # Tentar encontrar no enum
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            # Usar PYTHON_EXECUTE como fallback
            action_type = ActionType.PYTHON_EXECUTE

        actions.append(WorkflowAction(
            name=a.get("name", ""),
            action_type=action_type,
            properties=a.get("properties", {}),
            unique_name=a.get("unique_name", ""),
            title=a.get("title", "")
        ))

    # Parse variables
    variables = []
    input_variables = []

    for v in workflow_info.get("variables", []):
        props = v.get("properties", {})
        var = WorkflowVariable(
            name=props.get("name", ""),
            var_type=props.get("type", "datatype.string").replace("datatype.", ""),
            default_value=props.get("value"),
            description=props.get("description", ""),
            required=props.get("is_required", False),
            scope=props.get("scope", "local"),
            unique_name=v.get("unique_name", "")
        )

        if props.get("scope") == "input":
            input_variables.append(var)
        else:
            variables.append(var)

    return Workflow(
        unique_name=workflow_info.get("name", ""),
        name=workflow_info.get("title", workflow_info.get("name", "")),
        description=workflow_info.get("properties", {}).get("description", ""),
        triggers=triggers,
        actions=actions,
        variables=variables,
        input_variables=input_variables,
        _securex_id=workflow_info.get("unique_name", "")
    )


def _load_simple_workflow(data: dict) -> Workflow:
    """Carrega workflow no formato simplificado (legado)."""
    workflow_info = data["workflow"]

    # Parse triggers
    triggers = [
        WorkflowTrigger(
            trigger_type=TriggerType(t["type"]),
            properties=t.get("properties", {})
        )
        for t in data.get("triggers", [])
    ]

    # Parse actions
    actions = [
        WorkflowAction(
            name=a["name"],
            action_type=ActionType(a["type"]),
            properties=a.get("properties", {}),
            condition=a.get("condition")
        )
        for a in data.get("actions", [])
    ]

    # Parse variables
    variables = [
        WorkflowVariable(
            name=v["name"],
            var_type=v["type"],
            default_value=v.get("default"),
            description=v.get("description", ""),
            required=v.get("required", False)
        )
        for v in data.get("variables", [])
    ]

    # Parse input variables
    input_variables = [
        WorkflowVariable(
            name=v["name"],
            var_type=v["type"],
            default_value=v.get("default"),
            description=v.get("description", ""),
            required=v.get("required", False)
        )
        for v in data.get("input_variables", [])
    ]

    return Workflow(
        unique_name=workflow_info["unique_name"],
        name=workflow_info["name"],
        description=workflow_info.get("description", ""),
        triggers=triggers,
        actions=actions,
        variables=variables,
        input_variables=input_variables
    )


def list_workflows(client_name: str) -> list[str]:
    """
    Lista workflows existentes do cliente.

    Args:
        client_name: Nome do cliente

    Returns:
        Lista de nomes de arquivos de workflows
    """
    workflows_dir = Path.cwd() / "clients" / client_name / "workflows"

    if not workflows_dir.exists():
        return []

    return [f.stem for f in workflows_dir.glob("*.json")]


# ==================== Validation ====================

def validate_workflow(workflow: Workflow) -> list[str]:
    """
    Valida workflow e retorna lista de erros (vazia se OK).

    Args:
        workflow: Workflow a validar

    Returns:
        Lista de mensagens de erro (vazia se valido)
    """
    errors = []

    # Validar unique_name
    if not workflow.unique_name:
        errors.append("unique_name nao pode ser vazio")
    elif not workflow.unique_name.replace("-", "").replace("_", "").isalnum():
        errors.append("unique_name deve conter apenas letras, numeros, - e _")

    # Validar name
    if not workflow.name:
        errors.append("name nao pode ser vazio")

    # Validar triggers
    if not workflow.triggers:
        errors.append("Workflow precisa de pelo menos um trigger")

    # Validar actions
    if not workflow.actions:
        errors.append("Workflow precisa de pelo menos uma acao")

    # Validar nomes de acoes (devem ser unicos)
    action_names = [a.name for a in workflow.actions]
    duplicates = [name for name in action_names if action_names.count(name) > 1]
    if duplicates:
        errors.append(f"Nomes de acao duplicados: {set(duplicates)}")

    # Validar nomes de variaveis (devem ser unicos)
    var_names = [v.name for v in workflow.variables]
    duplicates = [name for name in var_names if var_names.count(name) > 1]
    if duplicates:
        errors.append(f"Nomes de variavel duplicados: {set(duplicates)}")

    return errors


# ==================== Templates ====================

def create_device_offline_handler(
    slack_channel: str = "#network-alerts",
    wait_minutes: int = 5
) -> Workflow:
    """
    Template: Handler para device offline.

    Fluxo:
    1. Trigger: Webhook de status change
    2. Wait: Espera X minutos
    3. Get Device: Verifica status atual
    4. Condition: Se ainda offline
    5. Notify: Envia notificacao no Slack

    Args:
        slack_channel: Canal do Slack para notificacao
        wait_minutes: Minutos de espera antes de notificar

    Returns:
        Workflow configurado
    """
    wait_seconds = wait_minutes * 60

    return (
        WorkflowBuilder(
            unique_name="device-offline-handler",
            name="Device Offline Handler",
            description="Notifica quando device fica offline por mais de X minutos"
        )
        .add_trigger(
            TriggerType.WEBHOOK,
            event="device.status.change",
            status="offline"
        )
        .add_input_variable(
            "device_serial",
            "string",
            required=True,
            description="Serial do device que ficou offline"
        )
        .add_variable(
            "wait_time",
            "number",
            wait_seconds,
            "Tempo de espera em segundos antes de notificar"
        )
        .add_action(
            "wait",
            ActionType.CORE_SLEEP,
            duration="$vars.wait_time$"
        )
        .add_action(
            "check_status",
            ActionType.MERAKI_GET_DEVICE_STATUS,
            serial="$input.device_serial$"
        )
        .add_action(
            "notify_slack",
            ActionType.SLACK_POST,
            condition="$actions.check_status.status$ == 'offline'",
            channel=slack_channel,
            message=f"Device $input.device_serial$ offline por mais de {wait_minutes} minutos!"
        )
        .build()
    )


def create_firmware_compliance_check(
    target_version: str,
    email_recipients: list[str]
) -> Workflow:
    """
    Template: Verificacao de compliance de firmware.

    Fluxo:
    1. Trigger: Agendado (diariamente)
    2. Get Devices: Lista todos os devices
    3. Loop: Para cada device
    4. Check Firmware: Compara com versao alvo
    5. Email: Envia relatorio de nao-compliance

    Args:
        target_version: Versao de firmware alvo
        email_recipients: Lista de emails para receber relatorio

    Returns:
        Workflow configurado
    """
    return (
        WorkflowBuilder(
            unique_name="firmware-compliance-check",
            name="Firmware Compliance Check",
            description=f"Verifica devices sem firmware {target_version}"
        )
        .add_trigger(
            TriggerType.SCHEDULE,
            cron="0 8 * * *",  # Diariamente as 8h
            timezone="America/Sao_Paulo"
        )
        .add_variable(
            "target_version",
            "string",
            target_version,
            "Versao de firmware alvo"
        )
        .add_variable(
            "non_compliant_devices",
            "array",
            [],
            "Lista de devices nao-compliant"
        )
        .add_action(
            "get_org_devices",
            ActionType.MERAKI_GET_DEVICE_STATUS
        )
        .add_action(
            "check_compliance",
            ActionType.PYTHON_EXECUTE,
            code="""
# Filtrar devices com firmware diferente do alvo
non_compliant = [
    d for d in actions.get_org_devices.devices
    if d.get('firmware', '') != vars.target_version
]
vars.non_compliant_devices = non_compliant
"""
        )
        .add_action(
            "send_report",
            ActionType.EMAIL_SEND,
            condition="len($vars.non_compliant_devices$) > 0",
            to=",".join(email_recipients),
            subject=f"Firmware Compliance Report - {len([]) if not email_recipients else 'X'} devices nao-compliant",
            body="Lista de devices: $vars.non_compliant_devices$"
        )
        .build()
    )


def create_scheduled_report(
    report_type: str,
    schedule_cron: str,
    email_recipients: list[str]
) -> Workflow:
    """
    Template: Relatorio agendado.

    Args:
        report_type: Tipo de relatorio (discovery, compliance, capacity)
        schedule_cron: Expressao cron (ex: "0 8 * * 1" = segundas 8h)
        email_recipients: Lista de emails

    Returns:
        Workflow configurado
    """
    return (
        WorkflowBuilder(
            unique_name=f"scheduled-report-{report_type}",
            name=f"Scheduled {report_type.title()} Report",
            description=f"Gera relatorio {report_type} periodicamente"
        )
        .add_trigger(
            TriggerType.SCHEDULE,
            cron=schedule_cron,
            timezone="America/Sao_Paulo"
        )
        .add_variable(
            "report_type",
            "string",
            report_type,
            "Tipo de relatorio a gerar"
        )
        .add_action(
            "generate_report",
            ActionType.PYTHON_EXECUTE,
            code=f"""
# Gerar relatorio {report_type}
from scripts.report import generate_report
report_html = generate_report('{report_type}')
vars.report_content = report_html
"""
        )
        .add_action(
            "send_email",
            ActionType.EMAIL_SEND,
            to=",".join(email_recipients),
            subject=f"{report_type.title()} Report - {datetime.now().strftime('%Y-%m-%d')}",
            body="$vars.report_content$",
            content_type="text/html"
        )
        .build()
    )


def create_security_alert_handler(
    slack_channel: str,
    pagerduty_enabled: bool = False
) -> Workflow:
    """
    Template: Handler para alertas de seguranca.

    Args:
        slack_channel: Canal do Slack
        pagerduty_enabled: Se deve criar incidente no PagerDuty

    Returns:
        Workflow configurado
    """
    builder = (
        WorkflowBuilder(
            unique_name="security-alert-handler",
            name="Security Alert Handler",
            description="Processa alertas de seguranca (IDS, MX firewall)"
        )
        .add_trigger(
            TriggerType.WEBHOOK,
            event="security.alert",
            severity=["high", "critical"]
        )
        .add_input_variable(
            "alert_type",
            "string",
            required=True,
            description="Tipo de alerta"
        )
        .add_input_variable(
            "alert_message",
            "string",
            required=True,
            description="Mensagem do alerta"
        )
        .add_action(
            "notify_slack",
            ActionType.SLACK_POST,
            channel=slack_channel,
            message=":warning: Security Alert: $input.alert_type$ - $input.alert_message$"
        )
    )

    if pagerduty_enabled:
        builder.add_action(
            "create_incident",
            ActionType.PAGERDUTY_INCIDENT,
            title="Security Alert: $input.alert_type$",
            description="$input.alert_message$",
            urgency="high"
        )

    return builder.build()


# ==================== Diagram / Visualization ====================

def workflow_to_diagram(workflow: Workflow) -> str:
    """
    Gera representacao visual ASCII do workflow.

    Args:
        workflow: Workflow a visualizar

    Returns:
        String com diagrama ASCII
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append(f"Workflow: {workflow.name}")
    lines.append(f"ID: {workflow.unique_name}")
    lines.append("=" * 60)
    lines.append("")

    # Triggers
    lines.append("TRIGGERS:")
    for i, trigger in enumerate(workflow.triggers, 1):
        lines.append(f"  [{i}] {trigger.trigger_type.value}")
        for key, value in trigger.properties.items():
            lines.append(f"      - {key}: {value}")
    lines.append("")

    # Actions
    lines.append("ACTIONS:")
    for i, action in enumerate(workflow.actions, 1):
        arrow = "  |"
        lines.append(arrow)
        lines.append(f"  +---> [{i}] {action.name}")
        lines.append(f"         Type: {action.action_type.value}")

        if action.condition:
            lines.append(f"         Condition: {action.condition}")

        if action.properties:
            lines.append("         Properties:")
            for key, value in action.properties.items():
                lines.append(f"           - {key}: {value}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


# ==================== Import Instructions ====================

def generate_import_instructions(workflow: Workflow, client_name: str) -> str:
    """
    Gera instrucoes markdown de como importar o workflow.

    Args:
        workflow: Workflow a importar
        client_name: Nome do cliente

    Returns:
        String com instrucoes em markdown
    """
    filepath = Path.cwd() / "clients" / client_name / "workflows" / f"{workflow.unique_name}.json"

    instructions = f"""# Como Importar o Workflow: {workflow.name}

## 1. Localizar o Arquivo

O workflow foi salvo em:
```
{filepath}
```

## 2. Acessar Meraki Dashboard

1. Acesse https://dashboard.meraki.com
2. Selecione a organizacao: **{client_name}**
3. Va para **Organization > Workflows**

## 3. Importar o Workflow

1. Clique em **Import Workflow**
2. Selecione o arquivo `{workflow.unique_name}.json`
3. Revise as configuracoes:
   - Nome: {workflow.name}
   - Triggers: {len(workflow.triggers)} configurado(s)
   - Actions: {len(workflow.actions)} configurada(s)
4. Clique em **Import**

## 4. Configurar Credenciais (se necessario)

Este workflow pode precisar de credenciais para:
"""

    # Detectar servicos que precisam de credenciais
    services = set()
    for action in workflow.actions:
        if action.action_type.value.startswith("slack"):
            services.add("Slack (webhook URL)")
        elif action.action_type.value.startswith("teams"):
            services.add("Microsoft Teams (webhook URL)")
        elif action.action_type.value.startswith("pagerduty"):
            services.add("PagerDuty (API key)")
        elif action.action_type.value.startswith("servicenow"):
            services.add("ServiceNow (instance + credentials)")
        elif action.action_type.value.startswith("jira"):
            services.add("Jira (API token)")
        elif action.action_type.value.startswith("email"):
            services.add("Email (SMTP settings)")

    if services:
        for service in sorted(services):
            instructions += f"- {service}\n"
    else:
        instructions += "- Nenhuma credencial adicional necessaria\n"

    instructions += f"""
## 5. Ativar o Workflow

1. Apos importar, o workflow estara **desativado**
2. Clique no workflow para abrir detalhes
3. Clique em **Enable** para ativar
4. Teste o workflow com um trigger manual (se aplicavel)

## 6. Monitorar Execucoes

- Visualizar execucoes: **Organization > Workflows > Executions**
- Logs de cada execucao mostram sucesso/falha de cada acao

---

**Workflow criado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    return instructions


# ==================== Main (Testing) ====================

if __name__ == "__main__":
    # Teste rapido
    import sys

    logging.basicConfig(level=logging.DEBUG)

    try:
        print("\n=== Testando workflow.py ===\n")

        # Teste 1: Builder manual
        print("1. Criando workflow com builder...")
        workflow = (
            WorkflowBuilder("test-workflow", "Test Workflow", "Workflow de teste")
            .add_trigger(TriggerType.WEBHOOK, event="test.event")
            .add_input_variable("test_input", "string", required=True)
            .add_action("step1", ActionType.MERAKI_GET_DEVICE, serial="$input.test_input$")
            .add_action("step2", ActionType.SLACK_POST, channel="#test", message="Test!")
            .add_variable("counter", "number", 0)
            .build()
        )
        print(f"Workflow criado: {workflow.name}")

        # Validar
        print("\n2. Validando workflow...")
        errors = validate_workflow(workflow)
        if errors:
            print(f"Erros de validacao: {errors}")
        else:
            print("Workflow valido!")

        # Diagrama
        print("\n3. Diagrama do workflow:")
        print(workflow_to_diagram(workflow))

        # Teste 2: Template
        print("\n4. Testando template device_offline_handler...")
        template_workflow = create_device_offline_handler(
            slack_channel="#alerts",
            wait_minutes=10
        )
        print(f"Template criado: {template_workflow.name}")
        print(f"- Triggers: {len(template_workflow.triggers)}")
        print(f"- Actions: {len(template_workflow.actions)}")
        print(f"- Variables: {len(template_workflow.variables)}")

        # Export
        print("\n5. Exportando para JSON...")
        workflow_json = export_workflow(template_workflow)
        print(json.dumps(workflow_json, indent=2)[:500] + "...")

        print("\n=== Teste concluido com sucesso ===\n")

    except Exception as e:
        print(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
