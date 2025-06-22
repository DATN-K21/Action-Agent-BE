# Infrastructure Helm Charts

This directory contains Helm charts for the infrastructure components (PostgreSQL, Redis, RabbitMQ) that have been split from the original k8s-helm/infra directory.

## Charts Created

### 1. PostgreSQL Chart (`k8s-helm/postgresql/`)
- **Purpose**: PostgreSQL database with pgvector extension for AI service
- **Environments**: dev, stg, prod
- **Features**: 
  - Persistent storage (configurable per environment)
  - Environment-specific naming (postgresdev, postgresstg, postgresprod)
  - Resource limits (configured for prod)

### 2. Redis Chart (`k8s-helm/redis/`)
- **Purpose**: Redis cache for session storage and caching
- **Environments**: dev, stg, prod
- **Features**:
  - Optional persistence (enabled for stg/prod)
  - Environment-specific naming (redisdev, redisstg, redisprod)
  - Resource limits (configured for prod)

### 3. RabbitMQ Chart (`k8s-helm/rabbitmq/`)
- **Purpose**: Message broker for inter-service communication
- **Environments**: dev, stg, prod
- **Features**:
  - Management UI enabled
  - Optional persistence (enabled for stg/prod)
  - Environment-specific naming (rabbitmqdev, rabbitmqstg, rabbitmqprod)
  - Resource limits (configured for prod)

## Deployment Commands

### Development Environment
```bash
# PostgreSQL
helm install postgresdev ./k8s-helm/postgresql -f ./k8s-helm/postgresql/values.dev.yaml --namespace dev --create-namespace

# Redis
helm install redisdev ./k8s-helm/redis -f ./k8s-helm/redis/values.dev.yaml --namespace dev --create-namespace

# RabbitMQ
helm install rabbitmqdev ./k8s-helm/rabbitmq -f ./k8s-helm/rabbitmq/values.dev.yaml --namespace dev --create-namespace
```

### Staging Environment
```bash
# PostgreSQL
helm install postgresstg ./k8s-helm/postgresql -f ./k8s-helm/postgresql/values.stg.yaml --namespace stg --create-namespace

# Redis
helm install redisstg ./k8s-helm/redis -f ./k8s-helm/redis/values.stg.yaml --namespace stg --create-namespace

# RabbitMQ
helm install rabbitmqstg ./k8s-helm/rabbitmq -f ./k8s-helm/rabbitmq/values.stg.yaml --namespace stg --create-namespace
```

### Production Environment
```bash
# PostgreSQL
helm install postgresprod ./k8s-helm/postgresql -f ./k8s-helm/postgresql/values.prod.yaml --namespace prod --create-namespace

# Redis
helm install redisprod ./k8s-helm/redis -f ./k8s-helm/redis/values.prod.yaml --namespace prod --create-namespace

# RabbitMQ
helm install rabbitmqprod ./k8s-helm/rabbitmq -f ./k8s-helm/rabbitmq/values.prod.yaml --namespace prod --create-namespace
```

## Upgrade Commands

To upgrade existing deployments:

```bash
# Development
helm upgrade postgresdev ./k8s-helm/postgresql -f ./k8s-helm/postgresql/values.dev.yaml --namespace dev
helm upgrade redisdev ./k8s-helm/redis -f ./k8s-helm/redis/values.dev.yaml --namespace dev
helm upgrade rabbitmqdev ./k8s-helm/rabbitmq -f ./k8s-helm/rabbitmq/values.dev.yaml --namespace dev

# Staging
helm upgrade postgresstg ./k8s-helm/postgresql -f ./k8s-helm/postgresql/values.stg.yaml --namespace stg
helm upgrade redisstg ./k8s-helm/redis -f ./k8s-helm/redis/values.stg.yaml --namespace stg
helm upgrade rabbitmqstg ./k8s-helm/rabbitmq -f ./k8s-helm/rabbitmq/values.stg.yaml --namespace stg

# Production
helm upgrade postgresprod ./k8s-helm/postgresql -f ./k8s-helm/postgresql/values.prod.yaml --namespace prod
helm upgrade redisprod ./k8s-helm/redis -f ./k8s-helm/redis/values.prod.yaml --namespace prod
helm upgrade rabbitmqprod ./k8s-helm/rabbitmq -f ./k8s-helm/rabbitmq/values.prod.yaml --namespace prod
```

## Environment-Specific Configurations

### Development
- **Storage**: Minimal storage requirements
- **Persistence**: Disabled for Redis and RabbitMQ
- **Resources**: No resource limits

### Staging
- **Storage**: Moderate storage (2-5Gi)
- **Persistence**: Enabled for all components
- **Resources**: Basic resource limits

### Production
- **Storage**: Higher storage (5-10Gi)
- **Persistence**: Enabled for all components
- **Resources**: Proper resource limits and requests
- **Security**: Production-ready configurations

## Service Names and Ports

After deployment, the services will be available at:

### Development
- PostgreSQL: `postgresdev:5432`
- Redis: `redisdev:6379`
- RabbitMQ: `rabbitmqdev:5672` (Management UI: `rabbitmqdev:15672`)

### Staging
- PostgreSQL: `postgresstg:5432`
- Redis: `redisstg:6379`
- RabbitMQ: `rabbitmqstg:5672` (Management UI: `rabbitmqstg:15672`)

### Production
- PostgreSQL: `postgresprod:5432`
- Redis: `redisprod:6379`
- RabbitMQ: `rabbitmqprod:5672` (Management UI: `rabbitmqprod:15672`)

## Migration from Original k8s-helm/infra

The original YAML files in `k8s-helm/infra/` have been converted to proper Helm charts with:

1. **Template variables** for environment-specific values
2. **Helm helper functions** for consistent naming and labeling
3. **Values files** for each environment (dev, stg, prod)
4. **Configurable resources** and persistence options
5. **Proper Kubernetes labels** and selectors

You can safely remove the original `k8s-helm/infra/` directory after migrating to these Helm charts.
