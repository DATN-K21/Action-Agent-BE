#!/bin/bash

# Action-Agent Kubernetes Deployment Script
# This script deploys the Action-Agent backend services in the correct order

set -e

echo "🚀 Starting Action-Agent Kubernetes Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster"
    exit 1
fi

print_status "Connected to Kubernetes cluster"

# Step 1: Deploy Secrets
print_status "Deploying secrets..."
kubectl apply -f k8s/secrets/
print_success "Secrets deployed"

# Step 2: Deploy Infrastructure Services
print_status "Deploying infrastructure services..."
kubectl apply -f k8s/infrastructure/
print_success "Infrastructure services deployed"

# Step 3: Wait for infrastructure to be ready
print_status "Waiting for infrastructure services to be ready..."
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq --timeout=300s
kubectl wait --for=condition=ready pod -l app=elasticsearch --timeout=300s
print_success "Infrastructure services are ready"

# Step 4: Deploy Application Services
print_status "Deploying application services..."

# Deploy database services first
kubectl apply -f k8s/user-service/db-deployment.yaml
kubectl apply -f k8s/user-service/db-secret.yaml
kubectl apply -f k8s/ai-service/db-deployment.yaml
kubectl apply -f k8s/ai-service/db-secret.yaml

# Wait for databases
print_status "Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l app=user-database --timeout=300s
kubectl wait --for=condition=ready pod -l app=ai-database --timeout=300s
print_success "Databases are ready"

# Deploy application services
kubectl apply -f k8s/api-gateway/
kubectl apply -f k8s/user-service/deployment.yaml
kubectl apply -f k8s/ai-service/deployment.yaml
kubectl apply -f k8s/extension-service/

print_success "Application services deployed"

# Step 5: Wait for application services
print_status "Waiting for application services to be ready..."
kubectl wait --for=condition=ready pod -l app=api-gateway --timeout=300s
kubectl wait --for=condition=ready pod -l app=user-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=ai-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=extension-service --timeout=300s

print_success "All services are ready!"

# Step 6: Display status
echo ""
print_status "Deployment Summary:"
kubectl get pods
echo ""
kubectl get services
echo ""

print_success "🎉 Action-Agent backend deployment completed successfully!"
print_warning "Don't forget to update secret values with your actual credentials before production use!"

# Display useful commands
echo ""
print_status "Useful commands:"
echo "  - Check pod status: kubectl get pods"
echo "  - Check services: kubectl get services"
echo "  - View logs: kubectl logs <pod-name>"
echo "  - Port forward API Gateway: kubectl port-forward service/api-gateway 15000:15000"
