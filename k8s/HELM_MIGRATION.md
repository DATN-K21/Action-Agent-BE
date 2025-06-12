# Helm Migration Guide

## 🎯 Overview

The Action-Agent backend has been successfully migrated from plain Kubernetes manifests to Helm charts, providing:

- **Multi-environment support** (dev, staging, production)
- **Secure secret management** with external secret stores
- **Templating and configuration management**
- **Easy deployment and upgrades**
- **Environment-specific customization**

## 📁 New Structure

```
k8s/
├── helm-chart/                        # Main Helm chart
│   ├── Chart.yaml                     # Chart metadata
│   ├── values.yaml                    # Default values (dev)
│   ├── values-stg.yaml               # Staging environment values
│   ├── values-prod.yaml              # Production environment values
│   └── templates/                     # Kubernetes templates
│       ├── _helpers.tpl              # Template helpers
│       ├── serviceaccount.yaml       # Service account
│       ├── ingress.yaml              # Ingress configuration
│       ├── hpa.yaml                  # Horizontal Pod Autoscaler
│       ├── secrets/                  # Secret templates
│       │   ├── application-secrets.yaml
│       │   ├── service-secrets.yaml
│       │   └── external-secrets.yaml
│       ├── infrastructure/           # Infrastructure services
│       │   ├── redis.yaml
│       │   ├── rabbitmq.yaml
│       │   ├── elasticsearch.yaml
│       │   └── kibana.yaml
│       └── services/                 # Application services
│           ├── api-gateway.yaml
│           ├── user-service.yaml
│           ├── ai-service.yaml
│           └── extension-service.yaml
├── environments/                      # Environment-specific configs
│   ├── dev/values.yaml
│   ├── stg/values.yaml
│   └── prod/values.yaml
└── helm-deploy.sh                    # Helm deployment script
```

## 🚀 Quick Start

### Deploy Development Environment
```bash
# Using Helm script
./helm-deploy.sh --environment dev

# Using Makefile
make helm-deploy ENV=dev

# Using Helm directly
helm install action-agent-dev ./helm-chart -f ./helm-chart/values.yaml
```

### Deploy Staging Environment
```bash
# Using Helm script
./helm-deploy.sh --environment stg --namespace action-agent-stg

# Using Makefile
make helm-deploy ENV=stg NAMESPACE=action-agent-stg

# Using Helm directly
helm install action-agent-stg ./helm-chart -f ./helm-chart/values-stg.yaml --namespace action-agent-stg
```

### Deploy Production Environment
```bash
# Using Helm script
./helm-deploy.sh --environment prod --namespace action-agent-prod

# Using Makefile
make helm-deploy ENV=prod NAMESPACE=action-agent-prod

# Using Helm directly
helm install action-agent-prod ./helm-chart -f ./helm-chart/values-prod.yaml --namespace action-agent-prod
```

## 🔐 Secret Management

### Development (createSecrets: true)
In development, secrets are created directly from values in the Helm chart:

```yaml
secrets:
  createSecrets: true
config:
  jwt:
    secret: "dev-jwt-secret"
  email:
    username: "dev@example.com"
    password: "dev-password"
```

### Production (External Secrets)
In staging/production, secrets are fetched from external secret stores:

```yaml
secrets:
  createSecrets: false
  external:
    provider: "external-secrets"  # or "vault"
    secretStore: "production-vault-store"
```

### Supported Secret Providers
- **External Secrets Operator** (Recommended)
- **HashiCorp Vault**
- **AWS Secrets Manager**
- **Azure Key Vault**

## 🌍 Environment Configuration

### Environment-Specific Features

| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| Infrastructure | Local (in-cluster) | Local + Persistence | External Managed |
| Secrets | Helm values | External Secrets | External Secrets |
| Replicas | 1 | 2 | 3+ |
| Autoscaling | Disabled | Enabled | Enabled |
| Ingress | Optional | Enabled | Enabled with SSL |
| Resource Limits | Low | Medium | High |

### Infrastructure Services by Environment

#### Development
- Redis: In-cluster, no persistence
- RabbitMQ: In-cluster, no persistence  
- Elasticsearch: In-cluster, no persistence
- MongoDB: In-cluster, no persistence
- PostgreSQL: In-cluster, no persistence

#### Staging
- Redis: In-cluster with persistence
- RabbitMQ: In-cluster with persistence
- Elasticsearch: In-cluster with persistence
- MongoDB: In-cluster with persistence
- PostgreSQL: In-cluster with persistence

#### Production
- All infrastructure services: External managed services
- Connection details via external secrets

## 📊 Management Commands

### Deployment
```bash
# Deploy new release
make helm-deploy ENV=prod

# Upgrade existing release
make helm-upgrade ENV=prod

# Dry run (validate without deploying)
make helm-dry-run ENV=stg
```

### Monitoring
```bash
# Check status
make helm-status ENV=prod

# View logs
make logs

# Port forward for local access
make port-forward
```

### Cleanup
```bash
# Uninstall specific environment
make helm-uninstall ENV=stg

# Uninstall all (traditional kubectl)
make cleanup
```

## 🔄 Migration from kubectl

If you're migrating from the previous kubectl-based setup:

1. **Backup existing deployments**:
   ```bash
   kubectl get all -o yaml > backup.yaml
   ```

2. **Clean up old resources** (optional):
   ```bash
   make cleanup
   ```

3. **Deploy with Helm**:
   ```bash
   make helm-deploy ENV=dev
   ```

## 🛠️ Customization

### Custom Values File
Create a custom values file for your specific needs:

```bash
# Create custom values
cp helm-chart/values.yaml my-custom-values.yaml

# Deploy with custom values
helm install my-release ./helm-chart -f my-custom-values.yaml
```

### Override Specific Values
```bash
# Override image tags
helm install action-agent-dev ./helm-chart \
  --set apiGateway.image.tag=v1.2.3 \
  --set userService.image.tag=v1.2.3
```

### Environment Variables
```bash
# Set environment via environment variable
ENV=stg make helm-deploy

# Set namespace via environment variable  
NAMESPACE=my-namespace make helm-deploy
```

## 🚨 Troubleshooting

### Common Issues

1. **Helm not found**:
   ```bash
   # Install Helm
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```

2. **Namespace issues**:
   ```bash
   # Create namespace manually
   kubectl create namespace action-agent-stg
   ```

3. **Secret issues**:
   ```bash
   # Check if secrets are created
   kubectl get secrets -n your-namespace
   
   # Debug external secrets
   kubectl describe externalsecret -n your-namespace
   ```

4. **Template validation**:
   ```bash
   # Validate templates
   helm template ./helm-chart --debug
   ```

### Useful Debug Commands
```bash
# Render templates without installing
helm template action-agent ./helm-chart -f values-stg.yaml

# Show computed values
helm get values action-agent-prod -n action-agent-prod

# Show all resources in release
helm get manifest action-agent-dev
```

## 🎉 Benefits of Helm Migration

### ✅ **Achieved Benefits**

1. **Multi-Environment Support**: Easy deployment to dev/stg/prod with different configurations
2. **Secret Management**: Support for external secret stores in production
3. **Templating**: DRY principle with reusable templates
4. **Version Control**: Track deployments and rollback capabilities
5. **Configuration Management**: Centralized configuration with environment overrides
6. **Production Ready**: Auto-scaling, ingress, persistence, and monitoring
7. **Easy Management**: Simple commands for deploy/upgrade/rollback

### 🚀 **Next Steps**

- Set up CI/CD pipelines with Helm
- Configure external secret stores
- Implement monitoring and alerting
- Set up backup strategies for persistent data

The Action-Agent backend is now fully Helm-ified and production-ready! 🎉
