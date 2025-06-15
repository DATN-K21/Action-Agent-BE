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
	@echo 'Azure Container Registry:'
	@echo '  make build-push-images → build and push all Docker images to ACR'
	@echo ''
	@echo 'Local Development:'
	@echo '  make setup-dev      → copy values-dev.yaml.example to values-dev.yaml'
	@echo '  make kind-up        → start local Kind cluster'
	@echo '  make kind-down      → delete local Kind cluster'
	@echo '  make dev-deploy     → deploy with dev environment values'
	@echo '  make dev            → deploy with dev values (uses Azure Container Registry)'
	@echo ''
	@echo 'Examples:'
	@echo '  make deploy ENV=stg     → deploy to staging'
	@echo '  make deploy ENV=prod ARGS="--atomic"  → deploy to prod with rollback'
	@echo '  make dev                → quick deploy to local cluster with dev values'

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

## -------- Azure Container Registry helpers ----------------------------------
.PHONY: build-push-images

build-push-images:  ## Build and push all service images to Azure Container Registry
	@echo "Building and pushing AI Service image..."
	docker build -t aagent.azurecr.io/ai-service:dev ../ai-service
	docker push aagent.azurecr.io/ai-service:dev
	@echo "Building and pushing User Service image..."
	docker build -t aagent.azurecr.io/user-service:dev ../user-service
	docker push aagent.azurecr.io/user-service:dev
	@echo "Building and pushing API Gateway image..."
	docker build -t aagent.azurecr.io/api-gateway:dev ../api-gateway
	docker push aagent.azurecr.io/api-gateway:dev
	@echo "Building and pushing Extension Service image..."
	docker build -t aagent.azurecr.io/extension-service:dev ../extension-service
	docker push aagent.azurecr.io/extension-service:dev
	@echo "All images built and pushed successfully to Azure Container Registry!"

## -------- Local image building and loading -----------------------------------
# NOTE: Images are now built and pushed to Azure Container Registry (aagent.azurecr.io)
# No longer needed for local development as all environments use ACR images
#
# If you need to build images locally for testing, use:
#   docker build -t aagent.azurecr.io/ai-service:dev ../ai-service
#   docker build -t aagent.azurecr.io/user-service:dev ../user-service  
#   docker build -t aagent.azurecr.io/api-gateway:dev ../api-gateway
#   docker build -t aagent.azurecr.io/extension-service:dev ../extension-service

dev-deploy: ## Deploy the application using dev values
	@echo "Deploying with dev environment values..."
	make deploy ENV=dev

dev: dev-deploy ## Deploy with dev values (uses Azure Container Registry images)
