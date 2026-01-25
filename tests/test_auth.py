"""
Testes para scripts/auth.py
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.auth import (
    MerakiProfile,
    load_profile,
    list_profiles,
    validate_credentials,
    parse_credentials_file,
    get_credentials_path,
    CredentialsNotFoundError,
    InvalidProfileError,
)


class TestMerakiProfile:
    """Testes para a classe MerakiProfile."""

    def test_profile_creation(self):
        """Teste criacao de profile."""
        profile = MerakiProfile(
            name="test",
            api_key="12345678901234567890123456789012",
            org_id="123456"
        )

        assert profile.name == "test"
        assert profile.api_key == "12345678901234567890123456789012"
        assert profile.org_id == "123456"

    def test_profile_repr_masks_api_key(self):
        """Teste que repr mascara a API key."""
        profile = MerakiProfile(
            name="test",
            api_key="12345678901234567890123456789012",
            org_id="123456"
        )

        repr_str = repr(profile)
        assert "12345678901234567890123456789012" not in repr_str
        assert "12345678" in repr_str  # Mostra inicio
        assert "9012" in repr_str  # Mostra fim

    def test_profile_is_valid_with_valid_key(self):
        """Teste validacao com key valida."""
        profile = MerakiProfile(
            name="test",
            api_key="12345678901234567890123456789012",  # 32 chars
            org_id="123456"
        )
        assert profile.is_valid() is True

    def test_profile_is_valid_with_short_key(self):
        """Teste validacao com key muito curta."""
        profile = MerakiProfile(
            name="test",
            api_key="short",
            org_id="123456"
        )
        assert profile.is_valid() is False

    def test_profile_optional_org_id(self):
        """Teste que org_id e opcional."""
        profile = MerakiProfile(
            name="test",
            api_key="12345678901234567890123456789012"
        )
        assert profile.org_id is None


class TestParseCredentialsFile:
    """Testes para parse de arquivo de credenciais."""

    def test_parse_default_profile(self, mock_credentials_file):
        """Teste parse do profile default."""
        profile = parse_credentials_file(mock_credentials_file, "default")

        assert profile.name == "default"
        assert "test_default" in profile.api_key
        assert profile.org_id == "123456"

    def test_parse_named_profile(self, mock_credentials_file):
        """Teste parse de profile nomeado."""
        profile = parse_credentials_file(mock_credentials_file, "cliente-acme")

        assert profile.name == "cliente-acme"
        assert "test_acme" in profile.api_key
        assert profile.org_id == "789012"

    def test_parse_invalid_profile_raises(self, mock_credentials_file):
        """Teste que profile inexistente levanta erro."""
        with pytest.raises(InvalidProfileError) as exc_info:
            parse_credentials_file(mock_credentials_file, "nao-existe")

        assert "nao-existe" in str(exc_info.value)
        assert "cliente-acme" in str(exc_info.value)  # Lista disponiveis


class TestLoadProfile:
    """Testes para load_profile."""

    def test_load_from_env_vars(self, mock_env_credentials):
        """Teste carregamento via variaveis de ambiente."""
        profile = load_profile()

        assert profile.api_key == "env_api_key_12345678901234567890123456"
        assert profile.org_id == "env_org_123"
        assert profile.name == "env-profile"

    def test_load_from_credentials_file(self, mock_credentials_file, monkeypatch):
        """Teste carregamento via arquivo de credenciais."""
        # Limpar variaveis de ambiente
        monkeypatch.delenv("MERAKI_API_KEY", raising=False)
        monkeypatch.delenv("MERAKI_ORG_ID", raising=False)

        # Mock do path de credenciais
        with patch("scripts.auth.get_credentials_path") as mock_path:
            mock_path.return_value = mock_credentials_file

            profile = load_profile("cliente-acme")

            assert profile.name == "cliente-acme"
            assert "test_acme" in profile.api_key

    def test_load_raises_when_no_credentials(self, monkeypatch, tmp_path):
        """Teste que levanta erro quando nao ha credenciais."""
        # Limpar variaveis de ambiente
        monkeypatch.delenv("MERAKI_API_KEY", raising=False)
        monkeypatch.delenv("MERAKI_ORG_ID", raising=False)

        # Mock path inexistente
        with patch("scripts.auth.get_credentials_path") as mock_path:
            mock_path.return_value = tmp_path / "nao_existe"

            with pytest.raises(CredentialsNotFoundError):
                load_profile()


class TestListProfiles:
    """Testes para list_profiles."""

    def test_list_profiles_from_file(self, mock_credentials_file):
        """Teste listagem de profiles do arquivo."""
        with patch("scripts.auth.get_credentials_path") as mock_path:
            mock_path.return_value = mock_credentials_file

            profiles = list_profiles()

            assert "default" in profiles
            assert "cliente-acme" in profiles

    def test_list_profiles_empty_when_no_file(self, tmp_path):
        """Teste que retorna lista vazia sem arquivo."""
        with patch("scripts.auth.get_credentials_path") as mock_path:
            mock_path.return_value = tmp_path / "nao_existe"

            profiles = list_profiles()

            assert profiles == []


class TestValidateCredentials:
    """Testes para validate_credentials."""

    def test_validate_invalid_short_key(self):
        """Teste que key curta falha validacao."""
        profile = MerakiProfile(name="test", api_key="short")

        valid, msg = validate_credentials(profile)

        assert valid is False
        assert "curta" in msg

    def test_validate_valid_credentials(self, mock_meraki_dashboard):
        """Teste validacao com mock da API."""
        profile = MerakiProfile(
            name="test",
            api_key="12345678901234567890123456789012"
        )

        valid, msg = validate_credentials(profile)

        assert valid is True
        assert "Valido" in msg

    def test_validate_with_invalid_org_id(self, mock_meraki_dashboard):
        """Teste validacao com org_id inexistente."""
        profile = MerakiProfile(
            name="test",
            api_key="12345678901234567890123456789012",
            org_id="999999"  # Nao existe no mock
        )

        valid, msg = validate_credentials(profile)

        assert valid is False
        assert "999999" in msg
