.PHONY: setup test lint format clean new-client help

# Cores para output
GREEN := \033[0;32m
NC := \033[0m

help:
	@echo "Comandos disponiveis:"
	@echo "  make setup      - Configura ambiente de desenvolvimento"
	@echo "  make test       - Executa testes com coverage"
	@echo "  make lint       - Verifica codigo com ruff"
	@echo "  make format     - Formata codigo com ruff"
	@echo "  make clean      - Limpa arquivos temporarios"
	@echo "  make new-client - Cria estrutura para novo cliente"

setup:
	@chmod +x setup.sh
	@./setup.sh

test:
	@echo "$(GREEN)Executando testes...$(NC)"
	pytest tests/ -v --cov=scripts --cov-report=term-missing

lint:
	@echo "$(GREEN)Verificando codigo...$(NC)"
	ruff check scripts/ tests/
	ruff format scripts/ tests/ --check

format:
	@echo "$(GREEN)Formatando codigo...$(NC)"
	ruff format scripts/ tests/
	ruff check scripts/ tests/ --fix

clean:
	@echo "$(GREEN)Limpando arquivos temporarios...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache

new-client:
	@read -p "Nome do cliente (sem espacos): " name; \
	if [ -d "clients/$$name" ]; then \
		echo "Cliente $$name ja existe!"; \
		exit 1; \
	fi; \
	mkdir -p clients/$$name/{discovery,workflows,reports}; \
	echo "MERAKI_PROFILE=$$name" > clients/$$name/.env; \
	echo "# Changelog - $$name" > clients/$$name/changelog.md; \
	echo ""; \
	echo "Cliente $$name criado em clients/$$name/"; \
	echo "Adicione o profile [$$name] em ~/.meraki/credentials"
