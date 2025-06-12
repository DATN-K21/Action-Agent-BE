# Kubernetes Management Makefile for Action-Agent Backend
# Supports both traditional kubectl and Helm deployments

.PHONY: help deploy cleanup status secrets infra apps logs port-forward helm-deploy helm-upgrade helm-uninstall helm-status

# Default values
ENV ?= dev
NAMESPACE ?= default
RELEASE_NAME ?= action-agent

# Default target
help:
	@echo "Action-Agent Kubernetes Management"
	@echo ""
	@echo "Traditional kubectl commands:"
	@echo "  deploy       - Deploy all services using kubectl"
	@echo "  cleanup      - Remove all Action-Agent resources"
	@echo "  status       - Show deployment status"
	@echo "  secrets      - Deploy only secrets"
	@echo "  infra        - Deploy only infrastructure services"
	@echo "  apps         - Deploy only application services"
	@echo ""
	@echo "Helm commands:"
	@echo "  helm-deploy  - Deploy using Helm (ENV=dev|stg|prod)"
	@echo "  helm-upgrade - Upgrade existing Helm release"
	@echo "  helm-uninstall - Uninstall Helm release"
	@echo "  helm-status  - Show Helm release status"
	@echo "  helm-dry-run - Perform Helm dry run"
	@echo ""
	@echo "Other commands:"
	@echo "  logs         - Show logs for all services"
	@echo "  port-forward - Forward API Gateway port to localhost"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make helm-deploy ENV=dev"
	@echo "  make helm-deploy ENV=stg NAMESPACE=action-agent-stg"
	@echo "  make helm-upgrade ENV=prod"

# Deploy everything
deploy:
	@echo "🚀 Deploying Action-Agent backend..."
	./deploy.sh

# Cleanup all resources
cleanup:
	@echo "🧹 Cleaning up Action-Agent resources..."
	./cleanup.sh

# Show deployment status
status:
	@echo "📊 Deployment Status:"
	@echo ""
	@echo "Pods:"
	@kubectl get pods -o wide
	@echo ""
	@echo "Services:"
	@kubectl get services
	@echo ""
	@echo "Secrets:"
	@kubectl get secrets

# Deploy only secrets
secrets:
	@echo "🔐 Deploying secrets..."
	kubectl apply -f secrets/

# Deploy only infrastructure
infra:
	@echo "🏗️  Deploying infrastructure..."
	kubectl apply -f infrastructure/

# Deploy only application services
apps:
	@echo "📱 Deploying applications..."
	kubectl apply -f api-gateway/
	kubectl apply -f user-service/
	kubectl apply -f ai-service/
	kubectl apply -f extension-service/

# Show logs for all services
logs:
	@echo "📋 Recent logs for all services:"
	@echo ""
	@echo "=== API Gateway ==="
	-@kubectl logs -l app=api-gateway --tail=10
	@echo ""
	@echo "=== User Service ==="
	-@kubectl logs -l app=user-service --tail=10
	@echo ""
	@echo "=== AI Service ==="
	-@kubectl logs -l app=ai-service --tail=10
	@echo ""
	@echo "=== Extension Service ==="
	-@kubectl logs -l app=extension-service --tail=10

# Port forward API Gateway
port-forward:
	@echo "🌐 Port forwarding API Gateway to localhost:15000..."
	@echo "Access the API at: https://localhost:15000"
	@echo "Press Ctrl+C to stop"
	kubectl port-forward service/api-gateway 15000:15000

# Helm deployment commands
helm-deploy:
	@echo "🚀 Deploying with Helm (Environment: $(ENV))..."
	./helm-deploy.sh --environment $(ENV) --namespace $(NAMESPACE) --release $(RELEASE_NAME)

helm-upgrade:
	@echo "⬆️  Upgrading Helm release (Environment: $(ENV))..."
	./helm-deploy.sh --environment $(ENV) --namespace $(NAMESPACE) --release $(RELEASE_NAME) --upgrade

helm-uninstall:
	@echo "🗑️  Uninstalling Helm release..."
	helm uninstall $(RELEASE_NAME)-$(ENV) --namespace $(NAMESPACE)

helm-status:
	@echo "📊 Helm Release Status:"
	helm status $(RELEASE_NAME)-$(ENV) --namespace $(NAMESPACE)

helm-dry-run:
	@echo "🧪 Performing Helm dry run (Environment: $(ENV))..."
	./helm-deploy.sh --environment $(ENV) --namespace $(NAMESPACE) --release $(RELEASE_NAME) --dry-run
