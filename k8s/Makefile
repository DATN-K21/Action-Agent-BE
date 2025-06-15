#-------------------------------------------------------------------------------
#  Action-Agent – Helm workflow
#-------------------------------------------------------------------------------
#  • Single entry-point (deploy) now calls helm-deploy.sh, which already handles
#    fresh installs, upgrades, FAILED release cleanup, --dry-run, etc.
#  • Namespace and release name are derived from ENV unless you override them.
#  • Extra helpers: lint, diff, kind-up / kind-down for local smoke-tests.
#-------------------------------------------------------------------------------

.PHONY: help deploy uninstall status diff lint kind-up kind-down

## -------- Configurable knobs -------------------------------------------------
ENV           ?= stg                         # dev | stg | prod …
RELEASE_NAME  ?= action-agent                # base release name (env will be appended by script)
NAMESPACE     ?= action-agent-$(ENV)         # keep chart objects isolated
CHART_PATH    ?= ./helm
VALUES_FILE   ?= $(CHART_PATH)/values-$(ENV).yaml

## -------- Safety: bail if no kube-context ------------------------------------
require-context:
	@kubectl config current-context >/dev/null 2>&1 || \
	  (echo '❌  No kube-context set. Run "az aks get-credentials" or kind-up first.' && exit 1)

## -------- Public targets -----------------------------------------------------
help:
	@echo 'Action-Agent Helm Makefile'
	@echo '  make deploy         → upgrade --install (idempotent)'
	@echo '  make uninstall      → helm uninstall'
	@echo '  make status         → helm status'
	@echo '  make diff           → helm diff upgrade (no changes applied)'
	@echo '  make lint           → helm lint + kubeconform'
	@echo '  make kind-up        → start local Kind cluster'
	@echo '  make kind-down      → delete local Kind cluster'

deploy: require-context               ## upgrade or fresh install
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

lint:                                 ## static checks
	helm lint $(CHART_PATH)
	helm template $(CHART_PATH) -f $(VALUES_FILE) | kubeconform -strict -

## -------- Local Kind helpers -------------------------------------------------
kind-up:
	kind create cluster --name action-agent --config ./kind/registry-config.yaml

kind-down:
	kind delete cluster --name action-agent
