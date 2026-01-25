"""
Gestao de credenciais Meraki.

Suporta multiplos profiles para diferentes clientes:
- Via arquivo ~/.meraki/credentials (formato INI)
- Via variaveis de ambiente (.env)
- Via .env em diretorio de cliente (clients/{nome}/.env)

Exemplo de ~/.meraki/credentials:
    [default]
    api_key = YOUR_API_KEY
    org_id = YOUR_ORG_ID

    [cliente-acme]
    api_key = ACME_API_KEY
    org_id = ACME_ORG_ID
"""

import os
import logging
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class MerakiProfile:
    """Credenciais de um profile Meraki."""

    name: str
    api_key: str
    org_id: Optional[str] = None

    def __repr__(self) -> str:
        """Representacao segura (sem expor API key)."""
        masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 12 else "****"
        return f"MerakiProfile(name='{self.name}', api_key='{masked_key}', org_id='{self.org_id}')"

    def is_valid(self) -> bool:
        """Verifica se o profile tem os campos minimos."""
        return bool(self.api_key and len(self.api_key) >= 32)


class CredentialsNotFoundError(Exception):
    """Nenhuma credencial Meraki encontrada."""
    pass


class InvalidProfileError(Exception):
    """Profile solicitado nao existe."""
    pass


def get_credentials_path() -> Path:
    """Retorna o path do arquivo de credenciais."""
    return Path.home() / ".meraki" / "credentials"


def parse_credentials_file(path: Path, profile_name: str = "default") -> MerakiProfile:
    """
    Parse arquivo de credenciais no formato INI.

    Args:
        path: Caminho para o arquivo de credenciais
        profile_name: Nome do profile a carregar

    Returns:
        MerakiProfile com as credenciais

    Raises:
        InvalidProfileError: Se o profile nao existir
    """
    parser = ConfigParser()
    parser.read(path)

    if profile_name not in parser.sections() and profile_name != "default":
        available = parser.sections()
        raise InvalidProfileError(
            f"Profile '{profile_name}' nao encontrado. "
            f"Disponiveis: {available}"
        )

    # DEFAULT e tratado diferente pelo ConfigParser
    if profile_name == "default" and "default" not in parser.sections():
        if parser.defaults():
            return MerakiProfile(
                name="default",
                api_key=parser.defaults().get("api_key", ""),
                org_id=parser.defaults().get("org_id")
            )
        raise InvalidProfileError("Profile 'default' nao encontrado")

    section = parser[profile_name]
    return MerakiProfile(
        name=profile_name,
        api_key=section.get("api_key", ""),
        org_id=section.get("org_id")
    )


def load_profile(name: Optional[str] = None) -> MerakiProfile:
    """
    Carrega um profile de credenciais Meraki.

    Ordem de precedencia:
    1. Variaveis de ambiente (MERAKI_API_KEY, MERAKI_ORG_ID)
    2. .env no diretorio atual
    3. Arquivo ~/.meraki/credentials

    Args:
        name: Nome do profile a carregar. Se None, usa MERAKI_PROFILE ou 'default'

    Returns:
        MerakiProfile com as credenciais

    Raises:
        CredentialsNotFoundError: Se nenhuma credencial for encontrada
        InvalidProfileError: Se o profile solicitado nao existir
    """
    # Carregar .env se existir
    load_dotenv()

    # Determinar profile name
    profile_name = name or os.getenv("MERAKI_PROFILE", "default")
    logger.debug(f"Carregando profile: {profile_name}")

    # 1. Tentar variaveis de ambiente
    env_api_key = os.getenv("MERAKI_API_KEY")
    if env_api_key:
        logger.debug("Credenciais encontradas em variaveis de ambiente")
        return MerakiProfile(
            name=profile_name,
            api_key=env_api_key,
            org_id=os.getenv("MERAKI_ORG_ID")
        )

    # 2. Tentar arquivo de credenciais
    creds_path = get_credentials_path()
    if creds_path.exists():
        logger.debug(f"Carregando de {creds_path}")
        return parse_credentials_file(creds_path, profile_name)

    # Nenhuma credencial encontrada
    raise CredentialsNotFoundError(
        "Nenhuma credencial Meraki encontrada. Configure:\n"
        f"  1. Variaveis de ambiente MERAKI_API_KEY e MERAKI_ORG_ID\n"
        f"  2. Arquivo {creds_path}\n"
        "  3. Arquivo .env no diretorio atual"
    )


def list_profiles() -> list[str]:
    """
    Lista todos os profiles disponiveis.

    Returns:
        Lista de nomes de profiles
    """
    creds_path = get_credentials_path()

    if not creds_path.exists():
        return []

    parser = ConfigParser()
    parser.read(creds_path)

    profiles = parser.sections()

    # Adicionar 'default' se existir nas defaults
    if parser.defaults():
        profiles = ["default"] + profiles

    return profiles


def validate_credentials(profile: MerakiProfile) -> tuple[bool, str]:
    """
    Valida se as credenciais sao validas fazendo uma chamada de teste.

    Args:
        profile: Profile a validar

    Returns:
        Tupla (sucesso: bool, mensagem: str)
    """
    if not profile.is_valid():
        return False, "API key invalida (muito curta)"

    try:
        import meraki
        dashboard = meraki.DashboardAPI(
            profile.api_key,
            suppress_logging=True,
            output_log=False
        )
        orgs = dashboard.organizations.getOrganizations()

        if profile.org_id:
            # Verificar se org_id existe
            org_ids = [org["id"] for org in orgs]
            if profile.org_id not in org_ids:
                return False, f"org_id '{profile.org_id}' nao encontrado. Disponiveis: {org_ids}"

        return True, f"Valido! Acesso a {len(orgs)} organizacao(oes)"

    except meraki.exceptions.APIError as e:
        return False, f"Erro de API: {e}"
    except Exception as e:
        return False, f"Erro: {e}"


def get_organizations(profile: MerakiProfile) -> list[dict]:
    """
    Lista organizacoes acessiveis com o profile.

    Args:
        profile: Profile com credenciais

    Returns:
        Lista de organizacoes
    """
    import meraki
    dashboard = meraki.DashboardAPI(
        profile.api_key,
        suppress_logging=True,
        output_log=False
    )
    return dashboard.organizations.getOrganizations()


# CLI helper functions
def setup_credentials_interactive() -> None:
    """Setup interativo de credenciais (para uso em CLI)."""
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console()
    creds_path = get_credentials_path()

    console.print("\n[bold]Configuracao de Credenciais Meraki[/bold]\n")

    # Criar diretorio se nao existir
    creds_path.parent.mkdir(parents=True, exist_ok=True)

    profile_name = Prompt.ask("Nome do profile", default="default")
    api_key = Prompt.ask("API Key", password=True)
    org_id = Prompt.ask("Organization ID (opcional)", default="")

    # Ler arquivo existente ou criar novo
    parser = ConfigParser()
    if creds_path.exists():
        parser.read(creds_path)

    # Adicionar/atualizar profile
    if profile_name not in parser.sections():
        parser.add_section(profile_name)

    parser.set(profile_name, "api_key", api_key)
    if org_id:
        parser.set(profile_name, "org_id", org_id)

    # Salvar
    with open(creds_path, "w") as f:
        parser.write(f)

    # Definir permissoes restritas
    os.chmod(creds_path, 0o600)

    console.print(f"\n[green]Profile '{profile_name}' salvo em {creds_path}[/green]")


if __name__ == "__main__":
    # Teste rapido
    import sys

    logging.basicConfig(level=logging.DEBUG)

    try:
        profile = load_profile()
        print(f"Profile carregado: {profile}")

        valid, msg = validate_credentials(profile)
        print(f"Validacao: {msg}")

    except (CredentialsNotFoundError, InvalidProfileError) as e:
        print(f"Erro: {e}")
        sys.exit(1)
