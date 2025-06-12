#!/bin/bash

# Helm-based Action-Agent Kubernetes Deployment Script
# This script deploys the Action-Agent backend services using Helm

set -e

echo "🚀 Starting Action-Agent Helm Deployment..."

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

# Default values
ENVIRONMENT="dev"
NAMESPACE="default"
RELEASE_NAME="action-agent"
CHART_PATH="./helm-chart"
DRY_RUN=false
UPGRADE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--release)
            RELEASE_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --upgrade)
            UPGRADE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --environment    Environment (dev, stg, prod) [default: dev]"
            echo "  -n, --namespace      Kubernetes namespace [default: default]"
            echo "  -r, --release        Helm release name [default: action-agent]"
            echo "  --dry-run           Perform a dry run"
            echo "  --upgrade           Upgrade existing release"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option $1"
            exit 1
            ;;
    esac
done

# Set namespace based on environment if not explicitly provided
if [[ "$NAMESPACE" == "default" ]]; then
    case $ENVIRONMENT in
        stg)
            NAMESPACE="action-agent-stg"
            ;;
        prod)
            NAMESPACE="action-agent-prod"
            ;;
        *)
            NAMESPACE="default"
            ;;
    esac
fi

# Update release name with environment
RELEASE_NAME="${RELEASE_NAME}-${ENVIRONMENT}"

print_status "Deployment Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Namespace: $NAMESPACE"
echo "  Release: $RELEASE_NAME"
echo "  Chart: $CHART_PATH"
echo ""

# Check if helm is available
if ! command -v helm &> /dev/null; then
    print_error "Helm is not installed or not in PATH"
    exit 1
fi

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

# Create namespace if it doesn't exist
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    print_status "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# Determine values file
VALUES_FILE="$CHART_PATH/values.yaml"
if [[ "$ENVIRONMENT" != "dev" ]]; then
    ENV_VALUES_FILE="$CHART_PATH/values-${ENVIRONMENT}.yaml"
    if [[ -f "$ENV_VALUES_FILE" ]]; then
        VALUES_FILE="$ENV_VALUES_FILE"
        print_status "Using environment-specific values: $ENV_VALUES_FILE"
    else
        print_warning "Environment values file not found: $ENV_VALUES_FILE"
        print_warning "Using default values file: $VALUES_FILE"
    fi
fi

# Build helm command
HELM_CMD="helm"
if [[ "$UPGRADE" == "true" ]]; then
    HELM_CMD="$HELM_CMD upgrade --install"
else
    HELM_CMD="$HELM_CMD install"
fi

HELM_CMD="$HELM_CMD $RELEASE_NAME $CHART_PATH"
HELM_CMD="$HELM_CMD --namespace $NAMESPACE"
HELM_CMD="$HELM_CMD --values $VALUES_FILE"
HELM_CMD="$HELM_CMD --set global.environment=$ENVIRONMENT"
HELM_CMD="$HELM_CMD --set global.namespace=$NAMESPACE"

if [[ "$DRY_RUN" == "true" ]]; then
    HELM_CMD="$HELM_CMD --dry-run --debug"
    print_status "Performing dry run..."
else
    HELM_CMD="$HELM_CMD --wait --timeout=600s"
fi

# Execute helm command
print_status "Executing: $HELM_CMD"
eval $HELM_CMD

if [[ "$DRY_RUN" == "false" ]]; then
    print_success "🎉 Action-Agent backend deployment completed successfully!"
    
    # Display deployment status
    echo ""
    print_status "Deployment Summary:"
    helm status $RELEASE_NAME -n $NAMESPACE
    echo ""
    kubectl get pods -n $NAMESPACE
    echo ""
    kubectl get services -n $NAMESPACE
    echo ""
    
    print_status "Useful commands:"
    echo "  - Check status: helm status $RELEASE_NAME -n $NAMESPACE"
    echo "  - View pods: kubectl get pods -n $NAMESPACE"
    echo "  - View logs: kubectl logs -f deployment/action-agent-$ENVIRONMENT-api-gateway -n $NAMESPACE"
    echo "  - Port forward: kubectl port-forward service/action-agent-$ENVIRONMENT-api-gateway 15000:15000 -n $NAMESPACE"
    echo "  - Upgrade: $0 --environment $ENVIRONMENT --upgrade"
    echo "  - Uninstall: helm uninstall $RELEASE_NAME -n $NAMESPACE"
    
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        print_warning "Remember to update secret values with your actual credentials!"
    fi
else
    print_success "Dry run completed successfully!"
fi
