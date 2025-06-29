# Action-Agent Backend

This repository contains the backend code for the Action-Agent system, implemented as a set of microservices.

## Microservices Overview

### 1. API Gateway
- **Port**: `https://:15000` (Notice the SSL)
- **Technology**: Node.js
- **Description**: Acts as the entry point for all API requests. Routes requests like `API_GATEWAY/ai/haha` to `AI_SERVICE/haha`, or `API_GATEWAY/user/haha` to `USER_SERVICE/haha` and so on.
- If the request contains an `Authorization` header, the API Gateway will parse the JWT token and add the following headers to the request before forwarding it to the inner services:
  - `x-user-id`: The user ID extracted from the token.
  - `x-user-role`: The user role extracted from the token.
  - `x-user-email`: The user email extracted from the token.

### 2. User Service
- **Port**: `http://:15100`
- **Technology**: NestJS
- **Database**: MongoDB (can be online or offline via `user-db` in `docker-compose`)
- **Description**: Manages user-related operations.

### 3. AI Service
- **Port**: `http://:15200`
- **Technology**: FastAPI
- **Database**: PostgreSQL (can be online or offline via `ai-db` in `docker-compose`)
- **Description**: Handles AI-related operations.

### 4. Extension Service
- **Port**: `http://:15300`
- **Technology**: NestJS
- **Description**: Manages browser extension operations and web crawling functionality.

### 5. Voice Service
- **Port**: `http://:15400`
- **Technology**: .NET Core (C#)
- **Description**: Handles speech recognition and voice-related operations.

## 6. Other services
The following services are planned or required for the system:
- **RabbitMQ**: A message broker required for asynchronous communication between services (required to turn on).
- **Redis**: A key-value store required for caching and session management (required to turn on).
- **Fluentd**: A log collector for aggregating logs from various services.
- **Elasticsearch**: A search and analytics engine for storing and querying logs.
- **Kibana**: A visualization tool for Elasticsearch, used to monitor and analyze logs.

## Ping endpoints
Each service provides a `/ping` endpoint to check its health:
- **API Gateway**: `https://:15000/ping`
- **User Service**: `http://:15100/ping` (from inside) or `https://:15000/user/ping`
- **AI Service**: `http://:15200/ping` (from inside) or `https://:15000/ai/ping`
- **Extension Service**: `http://:15300/ping` (from inside) or `https://:15000/extension/ping`

## Running the Services

### Localhost with Docker Compose
To run all services using Docker Compose:
1. Login to Docker Hub:
   ```bash
   docker login --username <your-username> --password <your-password>
   ```
   (You need to have a Docker Hub account and the credentials from NDA)
2. Copy the `docker-compose.override.yaml` file from NDA (to have the correct environment variables).
3. Run the following command:
   ```bash
   docker-compose up --pull always -d api-gateway ai-service user-service extension-service voice-service ai-db user-db
   ```
   (Currently we develop with these core services)
4. Whenever there is a new build, you can run:
   ```bash
   docker-compose up --pull always -d api-gateway ai-service user-service extension-service voice-service ai-db user-db
   ```
   to pull the latest images and restart the services.

### Localhost with Native Applications
For easier development, you can run the services natively:
1. Copy the relevant `.env` files into each service directory.
2. Start each service using its specific commands.

### Production
In the production environment:
1. Whenever code is updated on the `dev` branch, a pipeline is triggered.
2. The pipeline builds new Docker images and pushes them to the production environment.

### Kubernetes with Helm Charts
The project includes Helm charts for deploying services to Kubernetes across different environments. Charts are located in the `k8s-helm/` directory.

#### Available Services
- `aiservice/`: AI Service Helm chart
- `apigateway/`: API Gateway Helm chart  
- `extensionservice/`: Extension Service Helm chart
- `userservice/`: User Service Helm chart
- `voiceservice/`: Voice Service Helm chart
- `postgresql/`: PostgreSQL database Helm chart
- `rabbitmq/`: RabbitMQ message broker Helm chart
- `redis/`: Redis cache Helm chart
- `cert-manager/`: Certificate manager for SSL/TLS

#### Environment-specific Values
Each service has environment-specific configuration files:
- `values.dev.yaml`: Development environment
- `values.stg.yaml`: Staging environment  
- `values.prod.yaml`: Production environment
- `values.yaml`: Default values

#### Deployment Commands
To deploy to different environments:

**Development:**
```bash
cd k8s-helm
make install-dev
```

**Staging:**
```bash
cd k8s-helm
make install-stg
```

**Production:**
```bash
cd k8s-helm
make install-prod
```

**Individual service deployment:**
```bash
# Install a specific service for development
helm install ai-service ./aiservice -f ./aiservice/values.dev.yaml

# Upgrade a service
helm upgrade ai-service ./aiservice -f ./aiservice/values.dev.yaml
```

### Kubernetes (Legacy)
Legacy Kubernetes manifests for the services live in the `k8s/` folder. To deploy them run:

```bash
kubectl apply -f k8s/
```

Some `ConfigMap` values may need to be adjusted before applying them to your cluster.

## Notes
- Ensure all the environment variables are setup correctly.

