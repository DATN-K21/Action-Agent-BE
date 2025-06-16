# Database Connectivity Issues - Analysis and Fixes

## Issues Identified

### 1. **Credential Mismatches**
- **Problem**: Kubernetes configuration used different database credentials than Docker Compose
- **Docker**: `root:root` for MongoDB, `postgres:123456` for PostgreSQL, `root` for Redis
- **Kubernetes**: `admin:password` for MongoDB, `postgres:password` for PostgreSQL, no auth for Redis
- **Fix**: Updated `values.yaml` to match Docker Compose credentials

### 2. **Missing Environment Variables**
- **API Gateway** was missing several critical environment variables:
  - `USER_SERVICE_URL`
  - `AI_SERVICE_URL` 
  - `ELASTICSEARCH_URL`
  - `RABBITMQ_URL`
  - `REDIS_URL`
- **User Service** was missing Redis configuration:
  - `REDIS_HOST`
  - `REDIS_PORT`
  - `REDIS_USER`
  - `REDIS_PASSWORD`
  - `AI_SERVICE_URL`

### 3. **MongoDB Connection String Issues**
- **Extension Service**: Was incorrectly appending database name to pre-formatted connection string
- **User Service**: Needed specific database name (`user-service`) instead of default

### 4. **Redis Authentication Configuration**
- **Problem**: Redis deployment had malformed command structure for password authentication
- **Fix**: Corrected the YAML structure for Redis password setup

### 5. **Missing Configuration Values**
- **Global environment**: Missing `environment` field referenced in templates
- **RabbitMQ auth**: Missing authentication configuration for RabbitMQ

## Service IP Addresses and Connectivity

All services use Kubernetes internal DNS resolution with the following pattern:
```
<release-name>-<service-name>.<namespace>.svc.cluster.local
```

### Default Service Addresses (assuming release name "action-agent"):
- **API Gateway**: `action-agent-api-gateway:15000`
- **User Service**: `action-agent-user-service:15100`
- **AI Service**: `action-agent-ai-service:15200`
- **Extension Service**: `action-agent-extension-service:15300`
- **PostgreSQL**: `action-agent-postgresql:5432`
- **MongoDB**: `action-agent-mongodb:27017`
- **Redis**: `action-agent-redis:6379`

## Changes Made

### 1. Updated `k8s/helm/values.yaml`
- Changed PostgreSQL password from `password` to `123456`
- Changed MongoDB credentials from `admin:password` to `root:root`
- Added Redis authentication password `root`
- Added global environment value `dev`
- Added RabbitMQ authentication credentials

### 2. Updated `k8s/helm/templates/services/api-gateway.yaml`
- Added missing environment variables for service URLs
- Added Elasticsearch, RabbitMQ, and Redis connection strings

### 3. Updated `k8s/helm/templates/services/user-service.yaml`
- Added Redis connection environment variables
- Added AI service URL
- Updated MongoDB connection to use specific database name

### 4. Updated `k8s/helm/templates/services/extension-service.yaml`
- Fixed MongoDB connection string to use correct database name

### 5. Updated `k8s/helm/templates/infrastructure/redis.yaml`
- Fixed Redis authentication command structure

## How to Debug Further

1. **Run the diagnostic script**:
   ```bash
   cd /workspaces/Action-Agent-BE/k8s
   ./debug-connectivity.sh [release-name] [namespace]
   ```

2. **Check specific pod logs**:
   ```bash
   kubectl logs -f deployment/action-agent-ai-service
   kubectl logs -f deployment/action-agent-user-service
   ```

3. **Test database connectivity manually**:
   ```bash
   # Test PostgreSQL from AI service pod
   kubectl exec -it deployment/action-agent-ai-service -- nc -zv action-agent-postgresql 5432
   
   # Test MongoDB from User service pod  
   kubectl exec -it deployment/action-agent-user-service -- nc -zv action-agent-mongodb 27017
   
   # Test Redis from any service pod
   kubectl exec -it deployment/action-agent-user-service -- nc -zv action-agent-redis 6379
   ```

4. **Verify environment variables**:
   ```bash
   kubectl exec deployment/action-agent-ai-service -- printenv | grep DATABASE
   kubectl exec deployment/action-agent-user-service -- printenv | grep MONGODB
   ```

## Next Steps

1. **Redeploy** the Helm chart with the updated configurations
2. **Run the diagnostic script** to verify connectivity
3. **Check pod logs** for any remaining connection errors
4. **Verify** that all environment variables are correctly set

The main issue was likely the credential mismatches and missing environment variables that prevented services from finding and connecting to their respective databases.
