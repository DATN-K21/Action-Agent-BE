# Kubernetes Manifests - Now with Helm! 🎉

This directory contains both traditional Kubernetes manifests and modern Helm charts for the Action-Agent backend deployment.

## 🚀 Quick Start

### Helm Deployment (Recommended)
```bash
# Development
make helm-deploy ENV=dev

# Staging  
make helm-deploy ENV=stg

# Production
make helm-deploy ENV=prod
```

### Traditional kubectl
```bash
# Deploy everything
./deploy.sh

# Or using make
make deploy
```

## Directory Structure

```
k8s/
├── 🎯 HELM CHARTS (Recommended)
│   ├── helm-chart/                    # Main Helm chart
│   │   ├── Chart.yaml                # Chart metadata
│   │   ├── values.yaml               # Default values (dev)
│   │   ├── values-stg.yaml          # Staging environment
│   │   ├── values-prod.yaml         # Production environment
│   │   └── templates/               # Kubernetes templates
│   ├── environments/                # Environment-specific configs
│   │   ├── dev/values.yaml
│   │   ├── stg/values.yaml
│   │   └── prod/values.yaml
│   └── helm-deploy.sh              # Helm deployment script
│
├── 📄 TRADITIONAL MANIFESTS
│   ├── secrets/                     # Consolidated secrets
│   │   ├── infrastructure-secrets.yaml
│   │   └── application-secrets.yaml
│   ├── infrastructure/             # Core services
│   │   ├── redis.yaml
│   │   ├── rabbitmq.yaml
│   │   ├── elasticsearch.yaml
│   │   └── kibana.yaml
│   └── [service folders]/          # Application services
│
├── 🛠️ MANAGEMENT TOOLS
│   ├── deploy.sh                   # Traditional deployment
│   ├── cleanup.sh                  # Cleanup script
│   ├── Makefile                    # Make commands (supports both)
│   ├── README.md                   # This file
│   ├── HELM_MIGRATION.md          # Helm migration guide
│   └── SECRETS.md                  # Secret management docs
```

## Key Features

### 🎯 **Helm Charts (NEW!)**
- **Multi-environment support**: dev, staging, production configurations
- **Secure secret management**: External secret stores for production
- **Auto-scaling**: HPA support for production workloads
- **Ingress**: SSL-enabled ingress for external access
- **Templating**: DRY principle with reusable Kubernetes templates
- **Version control**: Track deployments and enable easy rollbacks

### 🔧 **Traditional Manifests** 
- **Organized Structure**: Logical grouping of related resources
- **Consolidated Secrets**: Related secrets merged for easier management
- **Automated Deployment**: One-command deployment with proper ordering
- **Easy Cleanup**: Automated teardown of all resources

### 🛠️ **Management Tools**
- **Multiple Interfaces**: Deploy via Helm, script, Makefile, or kubectl
- **Environment Ready**: Structured for multi-environment deployments
- **Documentation**: Comprehensive guides and troubleshooting

## Management Commands

### 🎯 **Helm Commands (Recommended)**
```bash
# Multi-environment deployment
make helm-deploy ENV=dev       # Development
make helm-deploy ENV=stg       # Staging  
make helm-deploy ENV=prod      # Production

# Management
make helm-upgrade ENV=prod     # Upgrade existing release
make helm-status ENV=stg       # Check release status
make helm-dry-run ENV=dev      # Validate before deploying
make helm-uninstall ENV=stg    # Remove release
```

### 🔧 **Traditional kubectl Commands**
```bash
# Using Makefile
make help          # Show all available commands
make deploy        # Deploy everything
make status        # Check deployment status
make logs          # View recent logs
make port-forward  # Access API Gateway locally
make cleanup       # Remove everything

# Using scripts directly
./deploy.sh        # Deploy everything
./cleanup.sh       # Remove everything
```

## Manual Deployment Order

1. Secrets
2. Infrastructure (Redis, RabbitMQ, Elasticsearch)
3. Databases
4. Application Services

See `SECRETS.md` for detailed instructions and best practices.
