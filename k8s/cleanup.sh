#!/bin/bash

# Action-Agent Kubernetes Cleanup Script
# This script removes all Action-Agent resources from the cluster

set -e

echo "🧹 Starting Action-Agent Kubernetes Cleanup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Confirmation prompt
read -p "Are you sure you want to delete all Action-Agent resources? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Cleanup cancelled"
    exit 0
fi

print_status "Removing application services..."
kubectl delete -f k8s/extension-service/ --ignore-not-found=true
kubectl delete -f k8s/ai-service/ --ignore-not-found=true
kubectl delete -f k8s/user-service/ --ignore-not-found=true
kubectl delete -f k8s/api-gateway/ --ignore-not-found=true

print_status "Removing infrastructure services..."
kubectl delete -f k8s/infrastructure/ --ignore-not-found=true

print_status "Removing secrets..."
kubectl delete -f k8s/secrets/ --ignore-not-found=true

print_status "Checking for any remaining resources..."
kubectl get pods | grep -E "(redis|rabbitmq|elasticsearch|kibana|api-gateway|user-service|ai-service|extension-service)" || true

print_success "🗑️  Action-Agent cleanup completed!"
print_warning "Note: Persistent volumes may still exist. Remove them manually if needed."
