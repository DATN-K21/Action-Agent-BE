# Kubernetes Deployment Documentation

This document describes the organized structure for the Action-Agent backend Kubernetes deployment.

## Directory Structure

```
k8s/
├── secrets/
│   ├── infrastructure-secrets.yaml    # Redis, RabbitMQ, Elasticsearch secrets
│   └── application-secrets.yaml       # JWT, API keys, connection URLs, email
├── infrastructure/
│   ├── redis.yaml                     # Redis deployment and service
│   ├── rabbitmq.yaml                  # RabbitMQ deployment and service
│   ├── elasticsearch.yaml             # Elasticsearch deployment and service
│   └── kibana.yaml                     # Kibana deployment and service
├── api-gateway/
│   ├── deployment.yaml
│   └── secret.yaml
├── user-service/
│   ├── deployment.yaml
│   ├── db-deployment.yaml
│   └── db-secret.yaml
├── ai-service/
│   ├── deployment.yaml
│   ├── db-deployment.yaml
│   └── db-secret.yaml
├── extension-service/
│   └── deployment.yaml
└── SECRETS.md                          # This documentation
```

## Secrets Organization

### Infrastructure Secrets (`secrets/infrastructure-secrets.yaml`)
Contains authentication credentials for core infrastructure services:
- **Redis Secret**: `REDIS_PASSWORD`, `REDIS_USER`
- **RabbitMQ Secret**: `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS`
- **Elasticsearch Secret**: `ELASTIC_PASSWORD`, `ELASTICSEARCH_USERNAME`

### Application Secrets (`secrets/application-secrets.yaml`)
Contains application-level secrets organized into three separate secrets:

#### 1. App Secrets
- `JWT_SECRET`: Secret key for JWT token signing
- `COMPOSIO_API_KEY`: API key for Composio service integration

#### 2. Connection URLs
- `REDIS_URL`: Complete Redis connection URL
- `RABBITMQ_URL`: Complete RabbitMQ connection URL
- `ELASTICSEARCH_URL`: Complete Elasticsearch connection URL

#### 3. Email Secret
- `EMAIL_USERNAME`: SMTP username for sending emails
- `EMAIL_PASSWORD`: SMTP password for sending emails

## Service-Specific Secrets

### User Service
- `user-service-secret`: Contains MongoDB connection string, JWT secret, and Redis password
- `user-db-secret`: Contains MongoDB root credentials

### AI Service
- `ai-db-secret`: Contains PostgreSQL database credentials

### API Gateway
- `api-gateway-secret`: Contains SSL certificates and other gateway-specific secrets

## Security Best Practices

1. **Never commit secrets to version control**: All secret values should be replaced with actual values during deployment
2. **Use base64 encoding for binary data**: When storing certificates or binary data
3. **Rotate secrets regularly**: Implement a secret rotation strategy
4. **Limit access**: Use RBAC to control who can view/modify secrets
5. **Use external secret management**: Consider using tools like HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault for production

## Deployment Instructions

### Quick Deployment
Use the provided script to deploy everything in the correct order:

```bash
# Make the script executable
chmod +x k8s/deploy.sh

# Deploy all resources
./k8s/deploy.sh
```

### Manual Deployment (Step by Step)

1. **Deploy Secrets First**:
   ```bash
   kubectl apply -f k8s/secrets/
   ```

2. **Deploy Infrastructure Services**:
   ```bash
   kubectl apply -f k8s/infrastructure/
   ```

3. **Deploy Application Services**:
   ```bash
   kubectl apply -f k8s/api-gateway/
   kubectl apply -f k8s/user-service/
   kubectl apply -f k8s/ai-service/
   kubectl apply -f k8s/extension-service/
   ```

4. **Verify Deployment**:
   ```bash
   kubectl get pods
   kubectl get services
   kubectl get secrets
   ```

### Environment-Specific Configuration

For different environments, create environment-specific secret files:

```
k8s/
├── secrets/
│   ├── base/
│   │   ├── infrastructure-secrets.yaml
│   │   └── application-secrets.yaml
│   ├── dev/
│   │   ├── infrastructure-secrets.yaml
│   │   └── application-secrets.yaml
│   ├── staging/
│   │   └── ...
│   └── prod/
│       └── ...
```

## Security Best Practices

1. **Never commit actual secrets**: Replace placeholder values with real credentials
2. **Use external secret management**: Consider HashiCorp Vault, AWS Secrets Manager, etc.
3. **Rotate secrets regularly**: Implement automated secret rotation
4. **Limit access**: Use RBAC to control secret access
5. **Monitor secret usage**: Track who accesses secrets and when

## Troubleshooting

### Check Secret Status
```bash
kubectl get secrets
kubectl describe secret <secret-name>
```

### View Secret Values (base64 decoded)
```bash
kubectl get secret <secret-name> -o jsonpath='{.data}' | base64 -d
```

### Update Secret Values
```bash
kubectl edit secret <secret-name>
# or
kubectl delete secret <secret-name>
kubectl apply -f k8s/secrets/
```
