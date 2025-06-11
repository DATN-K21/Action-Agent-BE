# Kubernetes Management Makefile for Action-Agent Backend

.PHONY: help deploy cleanup status secrets infra apps logs port-forward

# Default target
help:
	@echo "Action-Agent Kubernetes Management"
	@echo ""
	@echo "Available commands:"
	@echo "  deploy       - Deploy all services in correct order"
	@echo "  cleanup      - Remove all Action-Agent resources"
	@echo "  status       - Show deployment status"
	@echo "  secrets      - Deploy only secrets"
	@echo "  infra        - Deploy only infrastructure services"
	@echo "  apps         - Deploy only application services"
	@echo "  logs         - Show logs for all services"
	@echo "  port-forward - Forward API Gateway port to localhost"
	@echo "  help         - Show this help message"

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
