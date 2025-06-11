# Kubernetes Manifests

This directory contains all Kubernetes manifests for the Action-Agent backend deployment.

## Quick Start

```bash
# Option 1: Using deployment script
./deploy.sh

# Option 2: Using Makefile
make deploy

# Option 3: Using kubectl directly
kubectl apply -f secrets/ && kubectl apply -f infrastructure/ && kubectl apply -f .
```

## Directory Structure

```
k8s/
├── deploy.sh                          # Automated deployment script
├── cleanup.sh                         # Automated cleanup script
├── Makefile                           # Make commands for easy management
├── README.md                          # This file
├── SECRETS.md                         # Detailed documentation
├── secrets/                           # All secrets organized by type
│   ├── infrastructure-secrets.yaml   # Redis, RabbitMQ, Elasticsearch
│   └── application-secrets.yaml      # JWT, API keys, connections, email
├── infrastructure/                    # Core infrastructure services
│   ├── redis.yaml
│   ├── rabbitmq.yaml
│   ├── elasticsearch.yaml
│   └── kibana.yaml
├── api-gateway/                       # API Gateway service
├── user-service/                      # User management service
├── ai-service/                        # AI operations service
└── extension-service/                 # Extensions and integrations
```

## Key Features

- **Organized Structure**: Logical grouping of related resources
- **Consolidated Secrets**: Related secrets merged for easier management
- **Automated Deployment**: One-command deployment with proper ordering
- **Multiple Interfaces**: Deploy via script, Makefile, or kubectl
- **Easy Cleanup**: Automated teardown of all resources
- **Environment Ready**: Structured for multi-environment deployments
- **Documentation**: Comprehensive guides and troubleshooting

## Management Commands

```bash
# Using Makefile (recommended)
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
