# Makefile for Helm-based multi-environment deployments

ENVS := dev stg prod
SERVICES := apigateway userservice aiservice extensionservice

.PHONY: all install uninstall lint dryrun secrets

# TAG should be passed via CLI, e.g., make install ENV=dev TAG=BuildID
TAG ?= latest

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
	  --from-env-file=./secrets/env \
	  -n $(ENV)
