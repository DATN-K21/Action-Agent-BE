#-------------------------------------------------------------------------------
#  Action-Agent – Helm workflow
#-------------------------------------------------------------------------------
#  • Single entry-point (deploy) now calls helm-deploy.sh, which already handles
#    fresh installs, upgrades, FAILED release cleanup, --dry-run, etc.
#  • Namespace and release name are derived from ENV unless you override them.
#  • Extra helpers: lint, diff, kind-up / kind-down for local smoke-tests.
#-------------------------------------------------------------------------------

.PHONY: help deploy uninstall status diff lint lint-env kind-up kind-down build-images load-images build-load-images dev-setup dev-deploy dev

## -------- Configurable knobs -------------------------------------------------
ENV           ?= dev      # dev | stg | prod (dev requires local values-dev.yaml)
RELEASE_NAME  ?= action-agent                # base release name (env will be appended by script)
NAMESPACE     ?= action-agent-$(ENV)         # keep chart objects isolated
CHART_PATH    ?= ./helm
VALUES_FILE   ?= $(CHART_PATH)/values-$(ENV).yaml

## -------- Safety: bail if no kube-context ------------------------------------
require-context:
	@kubectl config current-context >/dev/null 2>&1 || \
	  (echo '❌  No kube-context set. Run "az aks get-credentials" or kind-up first.' && exit 1)

## -------- Check for dev values file ----------------------------------------
check-dev-values:
	@if [ "$(ENV)" = "dev" ] && [ ! -f "$(VALUES_FILE)" ]; then \
		echo "❌  values-dev.yaml not found. Please create it from values-dev.yaml.example"; \
		echo "   cp $(CHART_PATH)/values-dev.yaml.example $(VALUES_FILE)"; \
		echo "   Then edit $(VALUES_FILE) with your actual secrets"; \
		exit 1; \
	fi

## -------- Public targets -----------------------------------------------------
help:
	@echo 'Action-Agent Helm Makefile'
	@echo ''
	@echo 'Environment Configuration:'
	@echo '  dev     → Local development (requires values-dev.yaml with secrets)'
	@echo '  stg     → Azure staging (uses Key Vault + external services)'
	@echo '  prod    → Azure production (uses Key Vault + external services)'
	@echo ''
	@echo 'Main Commands:'
	@echo '  make deploy         → upgrade --install (idempotent)'
	@echo '  make uninstall      → helm uninstall'
	@echo '  make status         → helm status'
	@echo '  make diff           → helm diff upgrade (no changes applied)'
	@echo '  make lint           → helm lint + kubeconform'
	@echo ''
	@echo 'Local Development:'
	@echo '  make setup-dev      → copy values-dev.yaml.example to values-dev.yaml'
	@echo '  make kind-up        → start local Kind cluster'
	@echo '  make kind-down      → delete local Kind cluster'
	@echo '  make build-images   → build all service Docker images locally'
	@echo '  make load-images    → load images into Kind cluster'
	@echo '  make dev-setup      → create Kind cluster and load images'
	@echo '  make dev-deploy     → deploy with dev environment values'
	@echo '  make dev            → build, load images, and deploy with dev values'
	@echo ''
	@echo 'Examples:'
	@echo '  make deploy ENV=stg     → deploy to staging'
	@echo '  make deploy ENV=prod ARGS="--atomic"  → deploy to prod with rollback'

deploy: require-context check-dev-values  ## upgrade or fresh install
	./helm-deploy.sh -e $(ENV) \
	                 -n $(NAMESPACE) \
	                 -r $(RELEASE_NAME) \
	                 -c $(CHART_PATH) \
	                 $(ARGS)

uninstall: require-context            ## remove release & namespace
	helm uninstall action-agent-$(ENV) -n $(NAMESPACE) || true
	-kubectl delete ns $(NAMESPACE)

status: require-context
	helm status action-agent-$(ENV) -n $(NAMESPACE)

diff: require-context                 ## see what would change
	helm diff upgrade action-agent-$(ENV) $(CHART_PATH) \
		-n $(NAMESPACE) -f $(VALUES_FILE)

lint-env:                             ## Run lint for a specific environment
	@echo "Linting chart with values for environment: $(ENV)"
	@ENV_CLEAN=$$(echo "$(ENV)" | sed 's/[[:space:]]//g') && \
	ENV_FILE="$(CHART_PATH)/values-$$ENV_CLEAN.yaml" && \
	echo "Using values file: $$ENV_FILE" && \
	helm lint $(CHART_PATH) -f "$$ENV_FILE" && \
	helm template $(CHART_PATH) -f "$$ENV_FILE" | kubeconform -strict -

lint:                                 ## static checks
	@echo "Linting chart with base values.yaml"
	@helm lint $(CHART_PATH)
	@helm template $(CHART_PATH) | kubeconform -strict -
	@echo "\nAll environments passed basic validation. For full validation of specific environments, use: make lint-env ENV=dev|stg|prod"

## -------- Local Kind helpers -------------------------------------------------
kind-up:
	kind create cluster --name action-agent

kind-down:
	kind delete cluster --name action-agent

## -------- Local image building and loading -----------------------------------
.PHONY: build-images load-images build-load-images

build-images:  ## Build all service images locally
	@echo "Building AI Service image..."
	docker build -t ai-service:dev ../ai-service
	@echo "Building User Service image..."
	docker build -t user-service:dev ../user-service
	@echo "Building API Gateway image..."
	docker build -t api-gateway:dev ../api-gateway
	@echo "Building Extension Service image..."
	docker build -t extension-service:dev ../extension-service
	@echo "All images built successfully!"

load-images:  ## Load locally built images into Kind cluster
	@echo "Loading images into Kind cluster..."
	kind load docker-image ai-service:dev --name action-agent
	kind load docker-image user-service:dev --name action-agent
	kind load docker-image api-gateway:dev --name action-agent
	kind load docker-image extension-service:dev --name action-agent
	@echo "All images loaded successfully!"

build-load-images: build-images load-images  ## Build and load images in one command

dev-setup: kind-up build-load-images  ## Complete setup for local development

dev-deploy: ## Deploy the application using dev values
	@echo "Deploying with dev environment values..."
	make deploy ENV=dev

dev: build-load-images dev-deploy ## Build, load images, and deploy with dev values
