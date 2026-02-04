"""
Testes unitários para template_loader.py.

Cobertura alvo: 80%+
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.template_loader import (
    TemplateLoader,
    TemplateWorkflow,
    TemplateInfo,
    TemplateNotFoundError,
    TemplateValidationError,
    WorkflowBuildError,
    generate_unique_id,
    update_references,
    validate_workflow,
    create_workflow_from_template,
    ID_PREFIX_WORKFLOW,
    ID_PREFIX_VARIABLE,
    ID_PREFIX_ACTIVITY,
    ID_PREFIX_CATEGORY,
    ID_LENGTH,
)


# ==================== Fixtures ====================


@pytest.fixture
def sample_workflow_data():
    """Workflow válido para testes."""
    return {
        "workflow": {
            "unique_name": "definition_workflow_02ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
            "name": "Test Workflow",
            "title": "Test Workflow",
            "type": "generic.workflow",
            "base_type": "workflow",
            "object_type": "definition_workflow",
            "variables": [
                {
                    "schema_id": "datatype.string",
                    "properties": {
                        "value": "",
                        "scope": "input",
                        "name": "test_var",
                        "type": "datatype.string",
                        "is_required": True,
                    },
                    "unique_name": "variable_workflow_02ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
                    "object_type": "variable_workflow",
                }
            ],
            "properties": {
                "atomic": {"is_atomic": False},
                "delete_workflow_instance": False,
                "description": "Test description",
                "display_name": "Test Workflow",
                "runtime_user": {"target_default": True},
                "target": {"no_target": True},
            },
            "actions": [
                {
                    "unique_name": "definition_activity_02ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
                    "name": "Sleep",
                    "title": "Sleep",
                    "type": "core.sleep",
                    "base_type": "activity",
                    "properties": {
                        "sleep_interval": 60,
                        "continue_on_failure": False,
                    },
                    "object_type": "definition_activity",
                }
            ],
            "categories": ["category_02ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"],
        },
        "categories": {
            "category_02ABCDEFGHIJKLMNOPQRSTUVWXYZ012345": {
                "unique_name": "category_02ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
                "name": "Test Category",
                "title": "Test Category",
                "type": "basic.category",
                "base_type": "category",
                "category_type": "custom",
                "object_type": "category",
            }
        },
    }


@pytest.fixture
def temp_templates_dir(sample_workflow_data):
    """Diretório temporário com templates de teste."""
    with tempfile.TemporaryDirectory() as tmpdir:
        templates_dir = Path(tmpdir) / "templates" / "workflows"
        templates_dir.mkdir(parents=True)

        # Criar template de teste
        template_path = templates_dir / "test-workflow.json"
        template_path.write_text(json.dumps(sample_workflow_data, indent=2))

        # Criar segundo template
        second_data = sample_workflow_data.copy()
        second_data["workflow"] = sample_workflow_data["workflow"].copy()
        second_data["workflow"]["name"] = "Second Workflow"
        second_data["workflow"]["title"] = "Second Workflow"
        (templates_dir / "second-workflow.json").write_text(
            json.dumps(second_data, indent=2)
        )

        yield templates_dir


@pytest.fixture
def temp_clients_dir():
    """Diretório temporário para clientes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        clients_dir = Path(tmpdir) / "clients"
        clients_dir.mkdir(parents=True)
        yield clients_dir


# ==================== Tests: ID Generation ====================


class TestGenerateUniqueId:
    """Testes para generate_unique_id."""

    def test_generates_correct_length(self):
        """ID deve ter tamanho correto após o prefixo."""
        id_str = generate_unique_id(ID_PREFIX_WORKFLOW)
        id_part = id_str.replace(ID_PREFIX_WORKFLOW, "")
        assert len(id_part) == ID_LENGTH

    def test_starts_with_02(self):
        """ID deve começar com '02'."""
        id_str = generate_unique_id(ID_PREFIX_WORKFLOW)
        id_part = id_str.replace(ID_PREFIX_WORKFLOW, "")
        assert id_part.startswith("02")

    def test_includes_prefix(self):
        """ID deve incluir o prefixo fornecido."""
        id_str = generate_unique_id(ID_PREFIX_VARIABLE)
        assert id_str.startswith(ID_PREFIX_VARIABLE)

    def test_generates_unique_ids(self):
        """IDs gerados devem ser únicos."""
        ids = [generate_unique_id(ID_PREFIX_WORKFLOW) for _ in range(100)]
        assert len(set(ids)) == 100

    def test_all_prefixes(self):
        """Todos os prefixos devem funcionar."""
        for prefix in [ID_PREFIX_WORKFLOW, ID_PREFIX_VARIABLE, ID_PREFIX_ACTIVITY, ID_PREFIX_CATEGORY]:
            id_str = generate_unique_id(prefix)
            assert id_str.startswith(prefix)
            id_part = id_str.replace(prefix, "")
            assert len(id_part) == ID_LENGTH


class TestUpdateReferences:
    """Testes para update_references."""

    def test_updates_string_values(self):
        """Deve atualizar valores string."""
        data = {"key": "old_id_123"}
        result = update_references(data, "old_id_123", "new_id_456")
        assert result["key"] == "new_id_456"

    def test_updates_nested_dicts(self):
        """Deve atualizar dicionários aninhados."""
        data = {"level1": {"level2": {"id": "old_id"}}}
        result = update_references(data, "old_id", "new_id")
        assert result["level1"]["level2"]["id"] == "new_id"

    def test_updates_lists(self):
        """Deve atualizar listas."""
        data = {"items": ["old_id", "other", "old_id"]}
        result = update_references(data, "old_id", "new_id")
        assert result["items"] == ["new_id", "other", "new_id"]

    def test_updates_workflow_references(self):
        """Deve atualizar referências $workflow.XXX$."""
        data = {
            "input": "$workflow.old_wf.input.old_var$"
        }
        result = update_references(
            data, "old_var", "new_var", "old_wf", "new_wf"
        )
        assert result["input"] == "$workflow.new_wf.input.new_var$"

    def test_preserves_non_strings(self):
        """Deve preservar valores não-string."""
        data = {"number": 42, "bool": True, "null": None}
        result = update_references(data, "old", "new")
        assert result == data


# ==================== Tests: Validation ====================


class TestValidateWorkflow:
    """Testes para validate_workflow."""

    def test_valid_workflow(self, sample_workflow_data):
        """Workflow válido deve passar na validação."""
        is_valid, errors = validate_workflow(sample_workflow_data)
        assert is_valid is True
        assert errors == []

    def test_missing_workflow_object(self):
        """Deve detectar falta do objeto workflow."""
        is_valid, errors = validate_workflow({})
        assert is_valid is False
        assert any("workflow" in e for e in errors)

    def test_missing_required_fields(self, sample_workflow_data):
        """Deve detectar campos obrigatórios faltando."""
        del sample_workflow_data["workflow"]["unique_name"]
        is_valid, errors = validate_workflow(sample_workflow_data)
        assert is_valid is False
        assert any("unique_name" in e for e in errors)

    def test_invalid_workflow_type(self, sample_workflow_data):
        """Deve detectar type inválido."""
        sample_workflow_data["workflow"]["type"] = "wrong.type"
        is_valid, errors = validate_workflow(sample_workflow_data)
        assert is_valid is False
        assert any("type" in e and "generic.workflow" in e for e in errors)

    def test_invalid_id_prefix(self, sample_workflow_data):
        """Deve detectar prefixo de ID inválido."""
        sample_workflow_data["workflow"]["unique_name"] = "wrong_prefix_123"
        is_valid, errors = validate_workflow(sample_workflow_data)
        assert is_valid is False
        assert any("definition_workflow_" in e for e in errors)

    def test_invalid_id_length(self, sample_workflow_data):
        """Deve detectar ID com tamanho incorreto."""
        sample_workflow_data["workflow"]["unique_name"] = "definition_workflow_short"
        is_valid, errors = validate_workflow(sample_workflow_data)
        assert is_valid is False
        assert any(str(ID_LENGTH) in e for e in errors)


# ==================== Tests: TemplateWorkflow ====================


class TestTemplateWorkflow:
    """Testes para TemplateWorkflow."""

    def test_init(self, sample_workflow_data):
        """Deve inicializar corretamente."""
        wf = TemplateWorkflow(sample_workflow_data)
        assert wf.original_name == "Test Workflow"
        assert wf.original_id == sample_workflow_data["workflow"]["unique_name"]

    def test_clone(self, sample_workflow_data):
        """clone() deve criar cópia independente."""
        wf = TemplateWorkflow(sample_workflow_data)
        wf.clone()

        # Modificar o clone não deve afetar o original
        wf._data["workflow"]["name"] = "Modified"
        assert sample_workflow_data["workflow"]["name"] == "Test Workflow"

    def test_set_name(self, sample_workflow_data):
        """set_name() deve atualizar name, title e display_name."""
        wf = TemplateWorkflow(sample_workflow_data).clone()
        wf.set_name("New Name")

        assert wf._data["workflow"]["name"] == "New Name"
        assert wf._data["workflow"]["title"] == "New Name"
        assert wf._data["workflow"]["properties"]["display_name"] == "New Name"

    def test_set_description(self, sample_workflow_data):
        """set_description() deve atualizar a descrição."""
        wf = TemplateWorkflow(sample_workflow_data).clone()
        wf.set_description("New description")

        assert wf._data["workflow"]["properties"]["description"] == "New description"

    def test_set_variable(self, sample_workflow_data):
        """set_variable() deve definir valor da variável."""
        wf = TemplateWorkflow(sample_workflow_data).clone()
        wf.set_variable("test_var", "new_value")

        var = wf._data["workflow"]["variables"][0]
        assert var["properties"]["value"] == "new_value"

    def test_set_variable_case_insensitive(self, sample_workflow_data):
        """set_variable() deve ser case-insensitive."""
        wf = TemplateWorkflow(sample_workflow_data).clone()
        wf.set_variable("TEST_VAR", "new_value")

        var = wf._data["workflow"]["variables"][0]
        assert var["properties"]["value"] == "new_value"

    def test_set_variable_not_found(self, sample_workflow_data):
        """set_variable() deve lançar erro se variável não existe."""
        wf = TemplateWorkflow(sample_workflow_data).clone()

        with pytest.raises(WorkflowBuildError) as exc_info:
            wf.set_variable("nonexistent", "value")

        assert "not found" in str(exc_info.value)

    def test_set_variables(self, sample_workflow_data):
        """set_variables() deve definir múltiplas variáveis."""
        wf = TemplateWorkflow(sample_workflow_data).clone()
        wf.set_variables({"test_var": "value1"})

        var = wf._data["workflow"]["variables"][0]
        assert var["properties"]["value"] == "value1"

    def test_get_variables(self, sample_workflow_data):
        """get_variables() deve retornar lista de variáveis."""
        wf = TemplateWorkflow(sample_workflow_data)
        variables = wf.get_variables()

        assert len(variables) == 1
        assert variables[0]["name"] == "test_var"
        assert variables[0]["type"] == "datatype.string"

    def test_build_generates_new_ids(self, sample_workflow_data):
        """build() deve gerar novos IDs únicos."""
        wf = TemplateWorkflow(sample_workflow_data).clone().build()

        new_workflow_id = wf._data["workflow"]["unique_name"]
        original_id = sample_workflow_data["workflow"]["unique_name"]

        assert new_workflow_id != original_id
        assert new_workflow_id.startswith(ID_PREFIX_WORKFLOW)

    def test_build_updates_references(self, sample_workflow_data):
        """build() deve atualizar referências internas."""
        # Adicionar referência interna
        sample_workflow_data["workflow"]["actions"][0]["properties"]["ref"] = (
            "$workflow.definition_workflow_02ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
            ".input.variable_workflow_02ABCDEFGHIJKLMNOPQRSTUVWXYZ012345$"
        )

        wf = TemplateWorkflow(sample_workflow_data).clone().build()

        ref = wf._data["workflow"]["actions"][0]["properties"]["ref"]
        new_wf_id = wf._data["workflow"]["unique_name"]
        new_var_id = wf._data["workflow"]["variables"][0]["unique_name"]

        assert new_wf_id in ref
        assert new_var_id in ref

    def test_method_chaining(self, sample_workflow_data):
        """Métodos devem suportar encadeamento."""
        wf = (TemplateWorkflow(sample_workflow_data)
              .clone()
              .set_name("Chained")
              .set_description("Desc")
              .set_variable("test_var", "val")
              .build())

        assert wf.name == "Chained"

    def test_to_dict_requires_build(self, sample_workflow_data):
        """to_dict() deve exigir que build() seja chamado."""
        wf = TemplateWorkflow(sample_workflow_data).clone()

        with pytest.raises(WorkflowBuildError):
            wf.to_dict()

    def test_to_json(self, sample_workflow_data):
        """to_json() deve retornar JSON válido."""
        wf = TemplateWorkflow(sample_workflow_data).clone().build()
        json_str = wf.to_json()

        # Deve ser JSON válido
        data = json.loads(json_str)
        assert "workflow" in data

    def test_validate(self, sample_workflow_data):
        """validate() deve validar o workflow."""
        wf = TemplateWorkflow(sample_workflow_data).clone().build()
        is_valid, errors = wf.validate()

        assert is_valid is True
        assert errors == []

    def test_save(self, sample_workflow_data, temp_clients_dir):
        """save() deve salvar o arquivo JSON."""
        with patch("scripts.template_loader.CLIENTS_DIR", temp_clients_dir):
            wf = TemplateWorkflow(sample_workflow_data).clone().build()
            path = wf.save("test-client", "my-workflow")

            assert path.exists()
            assert path.name == "my-workflow.json"

            # Verificar conteúdo
            data = json.loads(path.read_text())
            assert "workflow" in data

    def test_save_requires_build(self, sample_workflow_data, temp_clients_dir):
        """save() deve exigir que build() seja chamado."""
        wf = TemplateWorkflow(sample_workflow_data).clone()

        with pytest.raises(WorkflowBuildError):
            wf.save("client", "name")

    def test_ensure_cloned_error(self, sample_workflow_data):
        """Operações sem clone() devem lançar erro."""
        wf = TemplateWorkflow(sample_workflow_data)

        with pytest.raises(WorkflowBuildError) as exc_info:
            wf.set_name("Test")

        assert "clone()" in str(exc_info.value)


# ==================== Tests: TemplateLoader ====================


class TestTemplateLoader:
    """Testes para TemplateLoader."""

    def test_init_default_path(self):
        """Deve usar caminho padrão se não especificado."""
        loader = TemplateLoader()
        assert loader.templates_dir == Path("templates/workflows")

    def test_init_custom_path(self, temp_templates_dir):
        """Deve aceitar caminho customizado."""
        loader = TemplateLoader(temp_templates_dir)
        assert loader.templates_dir == temp_templates_dir

    def test_list_templates(self, temp_templates_dir):
        """list_templates() deve retornar templates disponíveis."""
        loader = TemplateLoader(temp_templates_dir)
        templates = loader.list_templates()

        assert len(templates) == 2
        assert all(isinstance(t, TemplateInfo) for t in templates)

    def test_list_templates_info(self, temp_templates_dir):
        """TemplateInfo deve conter informações corretas."""
        loader = TemplateLoader(temp_templates_dir)
        templates = loader.list_templates()

        # Encontrar o primeiro template
        template = next(t for t in templates if t.name == "Test Workflow")

        assert template.name == "Test Workflow"
        assert template.description == "Test description"
        assert "test_var" in template.variables
        assert template.actions_count == 1

    def test_list_templates_empty_dir(self):
        """list_templates() deve retornar lista vazia se diretório não existe."""
        loader = TemplateLoader(Path("/nonexistent"))
        templates = loader.list_templates()

        assert templates == []

    def test_load_by_workflow_name(self, temp_templates_dir):
        """load() deve encontrar template pelo nome do workflow."""
        loader = TemplateLoader(temp_templates_dir)
        wf = loader.load("Test Workflow")

        assert wf.original_name == "Test Workflow"

    def test_load_by_filename(self, temp_templates_dir):
        """load() deve encontrar template pelo nome do arquivo."""
        loader = TemplateLoader(temp_templates_dir)
        wf = loader.load("test-workflow")

        assert wf.original_name == "Test Workflow"

    def test_load_case_insensitive(self, temp_templates_dir):
        """load() deve ser case-insensitive."""
        loader = TemplateLoader(temp_templates_dir)
        wf = loader.load("test workflow")

        assert wf.original_name == "Test Workflow"

    def test_load_not_found(self, temp_templates_dir):
        """load() deve lançar erro se template não existe."""
        loader = TemplateLoader(temp_templates_dir)

        with pytest.raises(TemplateNotFoundError) as exc_info:
            loader.load("Nonexistent Template")

        assert "not found" in str(exc_info.value).lower()

    def test_load_from_path(self, temp_templates_dir):
        """load_from_path() deve carregar de caminho específico."""
        loader = TemplateLoader(temp_templates_dir)
        path = temp_templates_dir / "test-workflow.json"
        wf = loader.load_from_path(path)

        assert wf.original_name == "Test Workflow"

    def test_load_from_path_not_found(self, temp_templates_dir):
        """load_from_path() deve lançar erro se arquivo não existe."""
        loader = TemplateLoader(temp_templates_dir)

        with pytest.raises(TemplateNotFoundError):
            loader.load_from_path(Path("/nonexistent.json"))


# ==================== Tests: Convenience Function ====================


class TestCreateWorkflowFromTemplate:
    """Testes para create_workflow_from_template."""

    def test_basic_usage(self, temp_templates_dir, temp_clients_dir):
        """Deve criar workflow com parâmetros básicos."""
        with patch("scripts.template_loader.TEMPLATES_DIR", temp_templates_dir):
            with patch("scripts.template_loader.CLIENTS_DIR", temp_clients_dir):
                path = create_workflow_from_template(
                    template_name="Test Workflow",
                    client="acme",
                    workflow_name="ACME Test"
                )

                assert path.exists()
                assert "acme" in str(path)

                data = json.loads(path.read_text())
                assert data["workflow"]["name"] == "ACME Test"

    def test_with_description(self, temp_templates_dir, temp_clients_dir):
        """Deve incluir descrição customizada."""
        with patch("scripts.template_loader.TEMPLATES_DIR", temp_templates_dir):
            with patch("scripts.template_loader.CLIENTS_DIR", temp_clients_dir):
                path = create_workflow_from_template(
                    template_name="Test Workflow",
                    client="acme",
                    workflow_name="Test",
                    description="Custom description"
                )

                data = json.loads(path.read_text())
                assert data["workflow"]["properties"]["description"] == "Custom description"

    def test_with_variables(self, temp_templates_dir, temp_clients_dir):
        """Deve definir variáveis customizadas."""
        with patch("scripts.template_loader.TEMPLATES_DIR", temp_templates_dir):
            with patch("scripts.template_loader.CLIENTS_DIR", temp_clients_dir):
                path = create_workflow_from_template(
                    template_name="Test Workflow",
                    client="acme",
                    workflow_name="Test",
                    variables={"test_var": "custom_value"}
                )

                data = json.loads(path.read_text())
                var = data["workflow"]["variables"][0]
                assert var["properties"]["value"] == "custom_value"


# ==================== Tests: Edge Cases ====================


class TestEdgeCases:
    """Testes para casos de borda."""

    def test_workflow_with_nested_blocks(self, sample_workflow_data):
        """Deve gerar IDs para blocos aninhados."""
        # Adicionar bloco com ações aninhadas
        sample_workflow_data["workflow"]["actions"].append({
            "unique_name": "definition_activity_02NESTED000000000000000000000000001",
            "name": "Condition Block",
            "title": "Condition",
            "type": "logic.condition_block",
            "base_type": "activity",
            "object_type": "definition_activity",
            "blocks": [
                {
                    "unique_name": "definition_activity_02NESTED000000000000000000000000002",
                    "name": "Branch",
                    "title": "If True",
                    "type": "logic.condition_branch",
                    "base_type": "activity",
                    "object_type": "definition_activity",
                    "actions": [
                        {
                            "unique_name": "definition_activity_02NESTED000000000000000000000000003",
                            "name": "Sleep",
                            "title": "Inner Sleep",
                            "type": "core.sleep",
                            "base_type": "activity",
                            "object_type": "definition_activity",
                        }
                    ]
                }
            ]
        })

        wf = TemplateWorkflow(sample_workflow_data).clone().build()

        # Verificar que IDs aninhados foram gerados
        assert len(wf._id_mapping) >= 4  # workflow + 3 activities

    def test_special_characters_in_name(self, sample_workflow_data, temp_clients_dir):
        """Deve sanitizar caracteres especiais no nome do arquivo."""
        with patch("scripts.template_loader.CLIENTS_DIR", temp_clients_dir):
            wf = TemplateWorkflow(sample_workflow_data).clone()
            wf.set_name("Test / Workflow & Special <chars>")
            wf.build()

            path = wf.save("client", "test / workflow & special")

            # Nome deve ser sanitizado
            assert "/" not in path.name
            assert "&" not in path.name
            assert "<" not in path.name

    def test_empty_variables(self, sample_workflow_data):
        """Deve funcionar sem variáveis."""
        sample_workflow_data["workflow"]["variables"] = []

        wf = TemplateWorkflow(sample_workflow_data).clone().build()

        is_valid, errors = wf.validate()
        assert is_valid is True

    def test_empty_actions(self, sample_workflow_data):
        """Deve funcionar sem ações."""
        sample_workflow_data["workflow"]["actions"] = []

        wf = TemplateWorkflow(sample_workflow_data).clone().build()

        is_valid, errors = wf.validate()
        assert is_valid is True


# ==================== Run Tests ====================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
