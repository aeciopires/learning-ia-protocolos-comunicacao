# Laboratórios de protocolos de comunicação para sistemas de IA.
# Rode `make help` para ver os alvos. Sistemas suportados: veja REQUIREMENTS.md.

SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

MISE ?= $(shell command -v mise 2>/dev/null || echo $(HOME)/.local/bin/mise)
UV := $(MISE) exec -- uv

# LAB=09 localiza labs/lab-09-*. O projeto Compose leva o número, para evitar colisão entre labs.
LAB ?=
LAB_DIR = $(wildcard labs/lab-$(LAB)-*)
PROJECT = lab-$(LAB)
export LAB_ID = lab-$(LAB)
COMPOSE = docker compose --env-file .env -p $(PROJECT) -f $(LAB_DIR)/compose.yaml
SERVICE ?=

##@ Ajuda
.PHONY: help
help: ## Mostra esta ajuda
	@awk 'BEGIN {FS = ":.*##"; printf "Uso: make \033[36m<alvo>\033[0m [LAB=NN]\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Ambiente
.PHONY: check-os
check-os: ## Recusa sistema ou arquitetura sem suporte
	@./scripts/check_os.sh

.PHONY: check-dependencies
check-dependencies: check-os ## Confere mise, Python, uv, Node.js, Docker, Compose, buildx e o daemon
	@./scripts/check_deps.sh

.PHONY: install-dependencies
install-dependencies: check-os ## Instala as dependências do sistema (DRY_RUN=1 só exibe os comandos)
	@./scripts/install_deps.sh

.PHONY: install
install: check-os ## Instala as ferramentas do mise.toml e o workspace uv, e cria o .env
	@$(MISE) trust --quiet mise.toml
	@$(MISE) install
	@$(UV) sync --locked --all-packages
	@./scripts/gen_secret.sh
	@echo "[ ok ] Installed. Next: make check-dependencies && make lab-list"

.PHONY: secret
secret: ## Cria o .env, se preciso, e gera os segredos locais marcados como CHANGEME
	@./scripts/gen_secret.sh

.PHONY: check-versions
check-versions: ## Compara as imagens da stack com as releases mais recentes
	@./scripts/check_versions.sh

##@ Laboratórios
.PHONY: lab-list
lab-list: ## Lista os laboratórios
	@./scripts/lab_list.sh

.PHONY: require-lab
require-lab:
	@if [ -z "$(LAB)" ] || [ -z "$(LAB_DIR)" ]; then \
		echo "[fail] Lab not found: '$(LAB)'. Use LAB=NN, for example: make lab-start LAB=09. See: make lab-list" >&2; exit 1; fi

.PHONY: check-env
check-env: require-lab ## Falha se um segredo exigido pelo lab estiver ausente ou como CHANGEME
	@./scripts/check_env.sh $(LAB_DIR)

.PHONY: lab-start
lab-start: check-env ## Valida o ambiente, sobe o lab e mostra as URLs (LAB=NN)
	@./scripts/check_ports.sh $(LAB_DIR)/compose.yaml $(PROJECT)
	@# Labs só com cenário não têm serviço contínuo: basta construir a imagem.
	@if [ -z "$$($(COMPOSE) config --services)" ]; then \
		$(COMPOSE) --profile scenario build; \
	else \
		$(COMPOSE) up -d --build --wait --wait-timeout 240 || { \
			echo "[fail] The lab did not become healthy. Check: make lab-logs LAB=$(LAB)" >&2; exit 1; }; \
	fi
	@./scripts/lab_urls.sh $(LAB_DIR)
	@./scripts/grafana_seed.sh $(LAB_DIR)

.PHONY: lab-run
lab-run: check-env ## Executa o cenário de demonstração do lab (LAB=NN)
	@$(COMPOSE) run --rm --build scenario

.PHONY: lab-logs
lab-logs: require-lab ## Acompanha os logs do lab (LAB=NN; SERVICE= filtra por serviço)
	@$(COMPOSE) logs -f $(SERVICE)

.PHONY: lab-status
lab-status: require-lab ## Mostra o estado dos containers do lab (LAB=NN)
	@$(COMPOSE) ps

.PHONY: lab-stop
lab-stop: require-lab ## Para o lab e mantém os volumes (LAB=NN)
	@$(COMPOSE) --profile scenario down --remove-orphans

.PHONY: lab-clean
lab-clean: require-lab ## Remove containers, volumes e imagens construídas pelo lab (LAB=NN)
	@$(COMPOSE) --profile scenario down --volumes --remove-orphans --rmi local

.PHONY: lab-test
lab-test: require-lab ## Executa os testes do lab, sem Docker (LAB=NN)
	@$(UV) run --locked --all-packages pytest -q $(LAB_DIR)

.PHONY: lab-smoke
lab-smoke: require-lab ## Sobe o lab, executa o cenário, confere a telemetria e derruba tudo (LAB=NN)
	@./scripts/lab_smoke.sh $(LAB)

##@ Qualidade
.PHONY: test
test: ## Executa os testes de todo o workspace
	@$(UV) run --locked --all-packages pytest -q

.PHONY: lint
lint: ## Executa ruff, mypy e shellcheck
	@$(UV) run --locked ruff check .
	@$(UV) run --locked ruff format --check .
	@$(UV) run --locked --all-packages mypy $$(ls -d labs/*/src/*/ | xargs -n1 basename | sed "s/^/-p /")
	@$(MISE) exec -- shellcheck -x -P scripts scripts/*.sh

.PHONY: fmt
fmt: ## Formata o código
	@$(UV) run --locked ruff format .
	@$(UV) run --locked ruff check --fix .

.PHONY: dashboards
dashboards: ## Regenera os dashboards do Grafana a partir de scripts/gen_dashboards.py
	@$(MISE) exec -- python scripts/gen_dashboards.py

.PHONY: clean
clean: ## Remove ambientes virtuais e caches (mantém o .env)
	@rm -rf .venv
	@find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +
	@echo "[ ok ] Clean."
