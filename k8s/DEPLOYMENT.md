# Action-Agent Kubernetes Deployment Configuration

## Overview

This repository contains Helm charts and configuration files for deploying the Action-Agent backend microservices to Kubernetes, specifically optimized for Azure Kubernetes Service (AKS).

## Environment Configurations

### Development (`values-dev.yaml`)
- **Location**: Gitignored (contains sensitive data)
- **Purpose**: Local development with Kind/Minikube
- **Features**:
  - Local secrets (similar to docker-compose.override.yaml)
  - Local databases (PostgreSQL, MongoDB, Redis)
  - Local infrastructure (Elasticsearch, Kibana, RabbitMQ)
  - NodePort services for external access
  - Minimal resource requests

### Staging (`values-stg.yaml`)
- **Purpose**: Pre-production testing environment
- **Features**:
  - Azure Key Vault integration for secrets
  - Azure Container Registry for images
  - External managed services (MongoDB Atlas, Azure PostgreSQL, etc.)
  - 3rd party Elasticsearch and RabbitMQ
  - Horizontal Pod Autoscaling
  - Ingress with SSL termination
  - 2 replicas per service

### Production (`values-prod.yaml`)
- **Purpose**: Production workloads
- **Features**:
  - Azure Key Vault integration with longer refresh intervals
  - Azure Container Registry for images
  - External managed services (MongoDB Atlas, Azure PostgreSQL, etc.)
  - 3rd party Elasticsearch and RabbitMQ
  - Advanced autoscaling with custom behaviors
  - Production-grade ingress with security headers
  - Pod disruption budgets
  - Network policies
  - Resource quotas
  - Security contexts
  - Node affinity for workload separation
  - 3-4 replicas per service

## Azure Integration

### Key Vault Setup
Both staging and production environments use Azure Key Vault for secret management:

1. **Create Key Vault**:
   ```bash
   az keyvault create --name action-agent-kv-stg --resource-group action-agent-rg --location eastus
   az keyvault create --name action-agent-kv-prod --resource-group action-agent-rg --location eastus
   ```

2. **Configure Workload Identity**:
   ```bash
   # Create managed identity
   az identity create --name action-agent-identity --resource-group action-agent-rg
   
   # Assign Key Vault access
   az keyvault set-policy --name action-agent-kv-stg --object-id <identity-principal-id> --secret-permissions get list
   ```

3. **Required Secrets in Key Vault**:
   - `stg-api-gateway-https-port`
   - `stg-mongodb-connection-string`
   - `stg-postgres-host`
   - `stg-llm-default-api-key`
   - And many more (see values-stg.yaml for complete list)

### Container Registry
Images are stored in Azure Container Registry:
```bash
az acr create --name actionagent --resource-group action-agent-rg --sku Standard
```

### External Services

#### Elasticsearch & Kibana
- Use Elastic Cloud or self-managed Elasticsearch
- Update URLs in values files:
  ```yaml
  external:
    elasticsearch:
      enabled: true
      url: "https://your-elastic-cloud.es.io:9243"
  ```

#### RabbitMQ
- Use CloudAMQP or self-managed RabbitMQ
- Update connection string in Key Vault

#### Databases
- **MongoDB**: MongoDB Atlas
- **PostgreSQL**: Azure Database for PostgreSQL
- **Redis**: Azure Cache for Redis

## Deployment

### Prerequisites
- kubectl configured for your AKS cluster
- Helm 3.x installed
- External Secrets Operator installed (for Azure Key Vault integration)

### Deploy to Staging
```bash
# Using the helm-deploy script
./helm-deploy.sh -e stg

# Or using Make
make deploy ENV=stg
```

### Deploy to Production
```bash
# Using the helm-deploy script with atomic rollback
./helm-deploy.sh -e prod --atomic

# Or using Make
make deploy ENV=prod ARGS="--atomic"
```

### Local Development
1. **Create values-dev.yaml** (not tracked in git):
   ```bash
   cp values-dev.yaml.example values-dev.yaml
   # Edit with your local secrets
   ```

2. **Setup Kind cluster**:
   ```bash
   make kind-up
   make build-load-images
   ```

3. **Deploy locally**:
   ```bash
   make dev-deploy
   ```

## Security Considerations

### Secrets Management
- **Development**: Local secrets in gitignored values-dev.yaml
- **Staging/Production**: Azure Key Vault with Workload Identity

### Network Security
- Production includes NetworkPolicies for traffic restriction
- Ingress configured with security headers
- Rate limiting on ingress

### Container Security
- Non-root containers
- Read-only root filesystem where possible
- Security contexts with appropriate capabilities

## Monitoring and Observability

### Health Checks
All services include:
- Liveness probes with appropriate delays
- Readiness probes for traffic routing
- Configurable timeouts and failure thresholds

### External Monitoring
- Elasticsearch for logging aggregation
- Kibana for log visualization
- Metrics collection via Prometheus (to be configured)

## Scaling

### Horizontal Pod Autoscaling
- CPU and memory-based scaling
- Different thresholds for staging vs production
- Custom scaling behaviors for graceful scaling

### Node Affinity
Production configuration includes:
- Application workloads on standard nodes
- AI workloads on specialized nodes (GPU/high-memory)
- Anti-affinity to spread pods across nodes

## Troubleshooting

### Common Issues
1. **Secrets not found**: Verify Key Vault permissions and secret names
2. **Image pull errors**: Check Azure Container Registry access
3. **External service connection**: Verify connection strings and network access

### Useful Commands
```bash
# Check deployment status
helm status action-agent-stg -n action-agent-stg

# View logs
kubectl logs -f deployment/action-agent-stg-api-gateway -n action-agent-stg

# Port forward for debugging
kubectl port-forward svc/action-agent-stg-api-gateway 15000:15000 -n action-agent-stg
```

## File Structure
```
k8s/
├── helm/
│   ├── Chart.yaml              # Helm chart metadata
│   ├── values.yaml             # Default values (local dev)
│   ├── values-base.yaml        # Base template for all environments
│   ├── values-stg.yaml         # Staging configuration
│   ├── values-prod.yaml        # Production configuration
│   └── templates/              # Kubernetes manifests
├── helm-deploy.sh              # Deployment script
├── Makefile                    # Automation targets
└── README.md                   # This file
```
