# Makefile for Helm-based multi-environment deployments

ENVS := dev stg prod
SERVICES := apigateway userservice aiservice extensionservice
REGISTRY := myaagent.azurecr.io

.PHONY: all install uninstall lint dryrun secrets install-cert-manager uninstall-cert-manager build-apigateway push-apigateway build-and-push-apigateway

# TAG should be passed via CLI, e.g., make install ENV=dev TAG=BuildID
TAG ?= latest

# Install cert-manager (run this first before installing services)
install-cert-manager:
	@echo "Installing cert-manager..."
	kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.13.0/cert-manager.yaml
	@echo "Waiting for cert-manager to be ready..."
	kubectl wait --for=condition=Available --timeout=300s -n cert-manager deployment/cert-manager
	kubectl wait --for=condition=Available --timeout=300s -n cert-manager deployment/cert-manager-cainjector
	kubectl wait --for=condition=Available --timeout=300s -n cert-manager deployment/cert-manager-webhook
	@echo "Installing cert-manager configuration..."
	helm upgrade --install cert-manager-config ./cert-manager \
	  -f ./cert-manager/values.yaml \
	  -f ./cert-manager/values.$(ENV).yaml

# Uninstall cert-manager configuration
uninstall-cert-manager:
	helm uninstall cert-manager-config || true
	kubectl delete -f https://github.com/jetstack/cert-manager/releases/download/v1.13.0/cert-manager.yaml || true

# Loop through services to install
install:
	@for svc in $(SERVICES); do \
	  helm upgrade --install $$svc ./$$svc \
	    -n $(ENV) \
	    -f ./$$svc/values.yaml \
	    -f ./$$svc/values.$(ENV).yaml \
	    --set image.tag=$(TAG) ; \
	done

# Uninstall all services
uninstall:
	@for svc in $(SERVICES); do \
	  helm uninstall $$svc -n $(ENV) ; \
	done

# Lint all services
lint:
	@for svc in $(SERVICES); do \
	  helm lint ./$$svc -f ./$$svc/values.$(ENV).yaml ; \
	done

# Dry-run install with debug output
dryrun:
	@mkdir -p ./_tests
	@for svc in $(SERVICES); do \
	  helm upgrade --install $$svc ./$$svc \
	    -n $(ENV) \
	    -f ./$$svc/values.yaml \
	    -f ./$$svc/values.$(ENV).yaml \
	    --set image.tag=$(TAG) \
	    --dry-run --debug > ./_tests/$$svc.$(ENV).log ; \
	done

# Create Kubernetes secrets from env file
secrets:
	kubectl create namespace $(ENV) --dry-run=client -o yaml | kubectl apply -f -
	kubectl delete secret env-secret -n $(ENV) --ignore-not-found
	kubectl create secret generic env-secret \
	  --from-env-file=./secrets/.env.$(ENV) \
	  -n $(ENV)
