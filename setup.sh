#!/bin/bash
# setup.sh - Configuracao inicial do ambiente Meraki Workflow

set -e

echo "=== Meraki Workflow Setup ==="
echo ""

# 1. Verificar Python
echo "[1/6] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 nao encontrado. Instale primeiro."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "      Python $PYTHON_VERSION encontrado"

# 2. Criar virtualenv
echo "[2/6] Configurando virtualenv..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "      Virtualenv criado"
else
    echo "      Virtualenv ja existe"
fi

# 3. Ativar e instalar deps
echo "[3/6] Instalando dependencias..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "      Dependencias instaladas"

# 4. Criar estrutura de diretorios
echo "[4/6] Criando estrutura de diretorios..."
mkdir -p clients scripts/templates/workflows tests docs
echo "      Diretorios criados"

# 5. Configurar credenciais
echo "[5/6] Verificando credenciais..."
if [ ! -f ~/.meraki/credentials ]; then
    mkdir -p ~/.meraki
    chmod 700 ~/.meraki
    cat > ~/.meraki/credentials << 'EOF'
[default]
api_key = YOUR_API_KEY_HERE
org_id = YOUR_ORG_ID_HERE

# Adicione profiles adicionais para cada cliente:
# [cliente-acme]
# api_key = ACME_API_KEY
# org_id = ACME_ORG_ID
EOF
    chmod 600 ~/.meraki/credentials
    echo "      Arquivo de credenciais criado em ~/.meraki/credentials"
    echo "      IMPORTANTE: Edite com suas credenciais reais!"
else
    echo "      Credenciais ja configuradas"
fi

# 6. Copiar .env.example
echo "[6/6] Configurando .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "      .env criado a partir do template"
else
    echo "      .env ja existe"
fi

echo ""
echo "=== Setup completo! ==="
echo ""
echo "Proximos passos:"
echo "  1. Ative o ambiente:  source venv/bin/activate"
echo "  2. Edite credenciais: ~/.meraki/credentials"
echo "  3. Teste conexao:     python -c 'from scripts.auth import load_profile; print(load_profile())'"
echo ""
