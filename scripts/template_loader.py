"""
Template Loader - Clone + Patch System para Cisco Workflows.

Permite criar novos workflows Meraki baseados em templates exportados,
substituindo variáveis e gerando IDs únicos para evitar conflitos.

Uso:
    from scripts.template_loader import TemplateLoader, TemplateWorkflow

    loader = TemplateLoader()
    templates = loader.list_templates()

    workflow = loader.load("Device Offline Handler")
    new_wf = (workflow.clone()
              .set_name("ACME - Device Offline")
              .set_description("Handler customizado para ACME")
              .set_variable("slack_channel", "#acme-alerts")
              .build())

    new_wf.save("acme", "device-offline-handler")
"""

import json
import logging
import random
import re
import string
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ==================== Constants ====================

TEMPLATES_DIR = Path("templates/workflows")
CLIENTS_DIR = Path("clients")

# Cisco Workflow ID format: prefix + 37 alphanumeric chars starting with "02"
ID_PREFIX_WORKFLOW = "definition_workflow_"
ID_PREFIX_VARIABLE = "variable_workflow_"
ID_PREFIX_ACTIVITY = "definition_activity_"
ID_PREFIX_CATEGORY = "category_"

ID_LENGTH = 37  # Length of the ID after the prefix
ID_CHARS = string.ascii_letters + string.digits


# ==================== Exceptions ====================


class TemplateNotFoundError(Exception):
    """Template não encontrado."""
    pass


class TemplateValidationError(Exception):
    """Erro de validação do template/workflow."""
    pass


class WorkflowBuildError(Exception):
    """Erro durante o build do workflow."""
    pass


# ==================== ID Generation ====================


def generate_unique_id(prefix: str = "") -> str:
    """
    Gera um ID único no padrão Cisco Workflows.

    IDs têm 37 caracteres alfanuméricos, começando com "02".

    Args:
        prefix: Prefixo do ID (ex: "definition_workflow_", "variable_workflow_")

    Returns:
        ID completo com prefixo

    Example:
        >>> generate_unique_id("definition_workflow_")
        'definition_workflow_02ABc3XyZ789...' (37 chars after prefix)
    """
    # Começa com "02" (padrão Cisco)
    id_body = "02"

    # Gera o resto do ID (35 chars restantes)
    remaining = ID_LENGTH - 2
    id_body += "".join(random.choices(ID_CHARS, k=remaining))

    return f"{prefix}{id_body}"


def update_references(
    data: dict,
    old_id: str,
    new_id: str,
    workflow_id_old: Optional[str] = None,
    workflow_id_new: Optional[str] = None
) -> dict:
    """
    Atualiza todas as referências a um ID dentro do JSON.

    Trata referências no formato:
    - Diretas: "unique_name": "old_id"
    - Em strings: "$workflow.old_workflow_id.input.old_variable_id$"

    Args:
        data: Dicionário JSON a ser atualizado
        old_id: ID antigo a ser substituído
        new_id: Novo ID
        workflow_id_old: ID antigo do workflow (para referências $workflow.XXX$)
        workflow_id_new: Novo ID do workflow

    Returns:
        Dicionário com referências atualizadas
    """
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_data[key] = update_references(
                value, old_id, new_id, workflow_id_old, workflow_id_new
            )
        return new_data
    elif isinstance(data, list):
        return [
            update_references(item, old_id, new_id, workflow_id_old, workflow_id_new)
            for item in data
        ]
    elif isinstance(data, str):
        # Substituição direta do ID
        result = data.replace(old_id, new_id)

        # Substituição em referências $workflow.XXX$
        if workflow_id_old and workflow_id_new:
            result = result.replace(workflow_id_old, workflow_id_new)

        return result
    else:
        return data


def validate_workflow(data: dict) -> tuple[bool, list[str]]:
    """
    Valida a estrutura de um workflow JSON.

    Args:
        data: Dicionário JSON do workflow

    Returns:
        Tupla (is_valid, errors) onde errors é lista de mensagens de erro
    """
    errors = []

    # Verificar estrutura raiz
    if "workflow" not in data:
        errors.append("Missing 'workflow' object at root")
        return False, errors

    workflow = data["workflow"]

    # Campos obrigatórios
    required_fields = [
        "unique_name",
        "name",
        "title",
        "type",
        "base_type",
        "object_type",
        "variables",
        "properties",
        "actions",
    ]

    for field_name in required_fields:
        if field_name not in workflow:
            errors.append(f"Missing required field: workflow.{field_name}")

    # Validar unique_name
    if "unique_name" in workflow:
        unique_name = workflow["unique_name"]
        if not unique_name.startswith("definition_workflow_"):
            errors.append(
                f"unique_name must start with 'definition_workflow_', got: {unique_name[:30]}..."
            )

        # Verificar tamanho do ID
        id_part = unique_name.replace("definition_workflow_", "")
        if len(id_part) != ID_LENGTH:
            errors.append(
                f"ID part of unique_name must be {ID_LENGTH} chars, got {len(id_part)}"
            )

    # Validar type e base_type
    if workflow.get("type") != "generic.workflow":
        errors.append(f"workflow.type must be 'generic.workflow', got: {workflow.get('type')}")

    if workflow.get("base_type") != "workflow":
        errors.append(f"workflow.base_type must be 'workflow', got: {workflow.get('base_type')}")

    if workflow.get("object_type") != "definition_workflow":
        errors.append(
            f"workflow.object_type must be 'definition_workflow', got: {workflow.get('object_type')}"
        )

    # Validar variáveis
    if "variables" in workflow and isinstance(workflow["variables"], list):
        for i, var in enumerate(workflow["variables"]):
            if "unique_name" not in var:
                errors.append(f"Variable {i} missing unique_name")
            elif not var["unique_name"].startswith("variable_workflow_"):
                errors.append(
                    f"Variable {i} unique_name must start with 'variable_workflow_'"
                )

            if var.get("object_type") != "variable_workflow":
                errors.append(f"Variable {i} object_type must be 'variable_workflow'")

    # Validar ações
    if "actions" in workflow and isinstance(workflow["actions"], list):
        for i, action in enumerate(workflow["actions"]):
            if "unique_name" not in action:
                errors.append(f"Action {i} missing unique_name")
            elif not action["unique_name"].startswith("definition_activity_"):
                errors.append(
                    f"Action {i} unique_name must start with 'definition_activity_'"
                )

            if action.get("object_type") != "definition_activity":
                errors.append(f"Action {i} object_type must be 'definition_activity'")

    return len(errors) == 0, errors


# ==================== Data Classes ====================


@dataclass
class TemplateInfo:
    """Informações sobre um template disponível."""
    name: str
    path: Path
    description: str = ""
    variables: list[str] = field(default_factory=list)
    actions_count: int = 0

    def __str__(self) -> str:
        return f"{self.name} ({len(self.variables)} vars, {self.actions_count} actions)"


# ==================== TemplateWorkflow ====================


class TemplateWorkflow:
    """
    Representa um workflow carregado de um template.

    Permite clonar, modificar e construir um novo workflow
    com IDs únicos para importação no Meraki Dashboard.
    """

    def __init__(self, data: dict, template_path: Optional[Path] = None):
        """
        Inicializa com dados do template.

        Args:
            data: JSON do workflow template
            template_path: Caminho do arquivo template (opcional)
        """
        self._original_data = data
        self._data: Optional[dict] = None
        self._template_path = template_path
        self._is_built = False
        self._id_mapping: dict[str, str] = {}  # old_id -> new_id

        # Extrair info do workflow original
        workflow = data.get("workflow", {})
        self.original_name = workflow.get("name", "Unknown")
        self.original_id = workflow.get("unique_name", "")

    def clone(self) -> "TemplateWorkflow":
        """
        Cria uma cópia do workflow para modificação.

        Returns:
            Self para encadeamento de métodos
        """
        self._data = deepcopy(self._original_data)
        self._is_built = False
        self._id_mapping = {}
        return self

    def set_name(self, name: str) -> "TemplateWorkflow":
        """
        Define o nome do novo workflow.

        Args:
            name: Nome para o workflow

        Returns:
            Self para encadeamento
        """
        self._ensure_cloned()
        self._data["workflow"]["name"] = name
        self._data["workflow"]["title"] = name
        self._data["workflow"]["properties"]["display_name"] = name
        return self

    def set_description(self, description: str) -> "TemplateWorkflow":
        """
        Define a descrição do workflow.

        Args:
            description: Descrição do workflow

        Returns:
            Self para encadeamento
        """
        self._ensure_cloned()
        self._data["workflow"]["properties"]["description"] = description
        return self

    def set_variable(self, name: str, value: Any) -> "TemplateWorkflow":
        """
        Define o valor de uma variável do workflow.

        Args:
            name: Nome da variável (campo 'name' em properties)
            value: Valor a definir

        Returns:
            Self para encadeamento

        Raises:
            WorkflowBuildError: Se variável não encontrada
        """
        self._ensure_cloned()

        found = False
        for var in self._data["workflow"].get("variables", []):
            var_name = var.get("properties", {}).get("name", "")
            if var_name.lower() == name.lower() or var_name == name:
                var["properties"]["value"] = value
                found = True
                logger.debug(f"Set variable '{name}' = {value}")
                break

        if not found:
            # Listar variáveis disponíveis
            available = [
                v.get("properties", {}).get("name", "?")
                for v in self._data["workflow"].get("variables", [])
            ]
            raise WorkflowBuildError(
                f"Variable '{name}' not found. Available: {available}"
            )

        return self

    def set_variables(self, variables: dict[str, Any]) -> "TemplateWorkflow":
        """
        Define múltiplas variáveis de uma vez.

        Args:
            variables: Dicionário {nome: valor}

        Returns:
            Self para encadeamento
        """
        for name, value in variables.items():
            self.set_variable(name, value)
        return self

    def get_variables(self) -> list[dict]:
        """
        Retorna lista de variáveis do workflow.

        Returns:
            Lista com info de cada variável
        """
        data = self._data or self._original_data
        variables = []

        for var in data.get("workflow", {}).get("variables", []):
            props = var.get("properties", {})
            variables.append({
                "name": props.get("name", ""),
                "type": props.get("type", ""),
                "scope": props.get("scope", ""),
                "value": props.get("value", ""),
                "required": props.get("is_required", False),
                "description": props.get("description", ""),
            })

        return variables

    def build(self) -> "TemplateWorkflow":
        """
        Constrói o workflow final com novos IDs únicos.

        Gera novos IDs para:
        - Workflow (definition_workflow_)
        - Variáveis (variable_workflow_)
        - Ações (definition_activity_)
        - Categorias (category_)

        Atualiza todas as referências internas ($workflow.XXX$).

        Returns:
            Self para encadeamento

        Raises:
            WorkflowBuildError: Se workflow não foi clonado
        """
        self._ensure_cloned()

        workflow = self._data["workflow"]
        old_workflow_id = workflow["unique_name"]

        # 1. Gerar novo ID do workflow
        new_workflow_id = generate_unique_id(ID_PREFIX_WORKFLOW)
        self._id_mapping[old_workflow_id] = new_workflow_id

        # 2. Gerar novos IDs para variáveis
        for var in workflow.get("variables", []):
            old_id = var["unique_name"]
            new_id = generate_unique_id(ID_PREFIX_VARIABLE)
            self._id_mapping[old_id] = new_id

        # 3. Gerar novos IDs para ações (recursivamente para blocos aninhados)
        self._generate_action_ids(workflow.get("actions", []))

        # 4. Gerar novos IDs para categorias
        if "categories" in self._data:
            new_categories = {}
            old_category_ids = list(self._data["categories"].keys())

            for old_cat_id in old_category_ids:
                cat = self._data["categories"][old_cat_id]
                new_cat_id = generate_unique_id(ID_PREFIX_CATEGORY)
                self._id_mapping[old_cat_id] = new_cat_id

                # Atualizar unique_name da categoria
                cat["unique_name"] = new_cat_id
                new_categories[new_cat_id] = cat

            self._data["categories"] = new_categories

        # 5. Atualizar todas as referências
        for old_id, new_id in self._id_mapping.items():
            self._data = update_references(
                self._data,
                old_id,
                new_id,
                old_workflow_id,
                new_workflow_id
            )

        self._is_built = True
        logger.info(f"Workflow built with {len(self._id_mapping)} new IDs")

        return self

    def _generate_action_ids(self, actions: list) -> None:
        """Gera novos IDs para ações, incluindo blocos aninhados."""
        for action in actions:
            old_id = action.get("unique_name", "")
            if old_id:
                new_id = generate_unique_id(ID_PREFIX_ACTIVITY)
                self._id_mapping[old_id] = new_id

            # Processar blocos aninhados (condition blocks, loops, etc.)
            if "blocks" in action:
                self._generate_action_ids(action["blocks"])
            if "actions" in action:
                self._generate_action_ids(action["actions"])

    def to_dict(self) -> dict:
        """
        Retorna o workflow como dicionário.

        Returns:
            Dicionário JSON do workflow
        """
        if not self._is_built:
            raise WorkflowBuildError("Workflow not built. Call build() first.")
        return self._data

    def to_json(self, indent: int = 2) -> str:
        """
        Retorna o workflow como string JSON.

        Args:
            indent: Indentação do JSON

        Returns:
            String JSON formatada
        """
        return json.dumps(self.to_dict(), indent=indent)

    def validate(self) -> tuple[bool, list[str]]:
        """
        Valida o workflow construído.

        Returns:
            Tupla (is_valid, errors)
        """
        data = self._data if self._is_built else self._original_data
        return validate_workflow(data)

    def save(self, client: str, name: str) -> Path:
        """
        Salva o workflow em clients/{client}/workflows/{name}.json.

        Args:
            client: Nome do cliente
            name: Nome do arquivo (sem extensão)

        Returns:
            Path do arquivo salvo

        Raises:
            WorkflowBuildError: Se workflow não foi construído
            TemplateValidationError: Se validação falhar
        """
        if not self._is_built:
            raise WorkflowBuildError("Workflow not built. Call build() first.")

        # Validar antes de salvar
        is_valid, errors = self.validate()
        if not is_valid:
            raise TemplateValidationError(
                f"Workflow validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        # Criar diretório se não existir
        output_dir = CLIENTS_DIR / client / "workflows"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitizar nome do arquivo
        safe_name = re.sub(r'[^\w\-]', '-', name.lower())
        output_path = output_dir / f"{safe_name}.json"

        # Salvar
        output_path.write_text(self.to_json(), encoding="utf-8")
        logger.info(f"Workflow saved to {output_path}")

        return output_path

    def _ensure_cloned(self) -> None:
        """Garante que clone() foi chamado."""
        if self._data is None:
            raise WorkflowBuildError("Workflow not cloned. Call clone() first.")

    @property
    def name(self) -> str:
        """Nome atual do workflow."""
        data = self._data or self._original_data
        return data.get("workflow", {}).get("name", "")

    @property
    def description(self) -> str:
        """Descrição atual do workflow."""
        data = self._data or self._original_data
        return data.get("workflow", {}).get("properties", {}).get("description", "")


# ==================== TemplateLoader ====================


class TemplateLoader:
    """
    Carrega templates de workflows de templates/workflows/.

    Example:
        loader = TemplateLoader()

        # Listar templates
        for template in loader.list_templates():
            print(template)

        # Carregar template específico
        workflow = loader.load("Device Offline Handler")
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Inicializa o loader.

        Args:
            templates_dir: Diretório de templates (default: templates/workflows/)
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR

        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")

    def list_templates(self) -> list[TemplateInfo]:
        """
        Lista todos os templates disponíveis.

        Returns:
            Lista de TemplateInfo com informações de cada template
        """
        if not self.templates_dir.exists():
            return []

        templates = []

        for path in self.templates_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                workflow = data.get("workflow", {})

                # Skip se não tem estrutura de workflow válida
                if not workflow or not workflow.get("name"):
                    logger.debug(f"Skipping {path}: not a valid workflow template")
                    continue

                # Extrair variáveis (com proteção para None)
                raw_variables = workflow.get("variables") or []
                variables = [
                    v.get("properties", {}).get("name", "")
                    for v in raw_variables
                    if isinstance(v, dict)
                ]

                # Extrair ações (com proteção para None)
                raw_actions = workflow.get("actions") or []

                templates.append(TemplateInfo(
                    name=workflow.get("name", path.stem),
                    path=path,
                    description=workflow.get("properties", {}).get("description", ""),
                    variables=variables,
                    actions_count=len(raw_actions),
                ))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse template {path}: {e}")

        return sorted(templates, key=lambda t: t.name)

    def load(self, name: str) -> TemplateWorkflow:
        """
        Carrega um template pelo nome.

        Args:
            name: Nome do template (ou nome do arquivo sem extensão)

        Returns:
            TemplateWorkflow pronto para clonagem

        Raises:
            TemplateNotFoundError: Se template não encontrado
        """
        if not self.templates_dir.exists():
            raise TemplateNotFoundError(
                f"Templates directory not found: {self.templates_dir}"
            )

        # Tentar encontrar pelo nome exato do workflow
        for path in self.templates_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                workflow_name = data.get("workflow", {}).get("name", "")

                # Match por nome do workflow ou nome do arquivo
                if (workflow_name.lower() == name.lower() or
                    path.stem.lower() == name.lower() or
                    workflow_name == name):
                    logger.info(f"Loaded template: {path}")
                    return TemplateWorkflow(data, template_path=path)

            except (json.JSONDecodeError, KeyError):
                continue

        # Listar templates disponíveis na mensagem de erro
        available = [t.name for t in self.list_templates()]
        raise TemplateNotFoundError(
            f"Template '{name}' not found. Available: {available}"
        )

    def load_from_path(self, path: Path) -> TemplateWorkflow:
        """
        Carrega um template de um caminho específico.

        Args:
            path: Caminho do arquivo JSON

        Returns:
            TemplateWorkflow

        Raises:
            TemplateNotFoundError: Se arquivo não existir
            TemplateValidationError: Se JSON inválido
        """
        if not path.exists():
            raise TemplateNotFoundError(f"File not found: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise TemplateValidationError(f"Invalid JSON in {path}: {e}")

        return TemplateWorkflow(data, template_path=path)


# ==================== CLI Integration ====================


def create_workflow_from_template(
    template_name: str,
    client: str,
    workflow_name: str,
    description: Optional[str] = None,
    variables: Optional[dict[str, Any]] = None,
) -> Path:
    """
    Função de conveniência para criar workflow a partir de template.

    Args:
        template_name: Nome do template
        client: Nome do cliente
        workflow_name: Nome do novo workflow
        description: Descrição (opcional)
        variables: Variáveis a definir (opcional)

    Returns:
        Path do arquivo salvo

    Example:
        path = create_workflow_from_template(
            template_name="Device Offline Handler",
            client="acme",
            workflow_name="ACME - Device Offline",
            description="Handler customizado para ACME",
            variables={"slack_channel": "#acme-alerts"}
        )
    """
    loader = TemplateLoader()
    template = loader.load(template_name)

    builder = template.clone().set_name(workflow_name)

    if description:
        builder.set_description(description)

    if variables:
        builder.set_variables(variables)

    workflow = builder.build()

    # Gerar nome do arquivo a partir do workflow_name
    file_name = re.sub(r'[^\w\-]', '-', workflow_name.lower())

    return workflow.save(client, file_name)


# ==================== Main (Demo) ====================


if __name__ == "__main__":
    # Demo: listar templates e criar workflow
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    loader = TemplateLoader()

    print("=" * 60)
    print("Templates Disponíveis:")
    print("=" * 60)

    templates = loader.list_templates()
    if not templates:
        print("Nenhum template encontrado em templates/workflows/")
        sys.exit(1)

    for i, t in enumerate(templates, 1):
        print(f"\n{i}. {t.name}")
        if t.description:
            print(f"   Descrição: {t.description[:60]}...")
        print(f"   Variáveis: {', '.join(t.variables) or 'Nenhuma'}")
        print(f"   Ações: {t.actions_count}")

    print("\n" + "=" * 60)
    print("Demo: Criando workflow customizado")
    print("=" * 60)

    # Carregar primeiro template para demo
    template = loader.load(templates[0].name)
    print(f"\nTemplate carregado: {template.original_name}")
    print(f"Variáveis disponíveis:")
    for var in template.get_variables():
        print(f"  - {var['name']} ({var['type']}, {var['scope']})")

    # Construir novo workflow
    workflow = (template
                .clone()
                .set_name("Demo - Test Workflow")
                .set_description("Workflow criado via template_loader")
                .build())

    # Validar
    is_valid, errors = workflow.validate()
    print(f"\nValidação: {'✓ OK' if is_valid else '✗ FALHOU'}")
    if errors:
        for err in errors:
            print(f"  - {err}")

    print(f"\nWorkflow construído com {len(workflow._id_mapping)} novos IDs")
    print("\nPara salvar: workflow.save('cliente', 'nome-do-workflow')")
