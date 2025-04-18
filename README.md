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
- **Database**: MongoDB (can be online or offline via `user-database` in `docker-compose`)
- **Description**: Manages user-related operations.

### 3. AI Service
- **Port**: `http://:15200`
- **Technology**: FastAPI
- **Database**: PostgreSQL (can be online or offline via `ai-database` in `docker-compose`)
- **Description**: Handles AI-related operations.

## 4. Other services
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

## Running the Services

### Localhost with Docker Compose
To run all services using Docker Compose:
1. Copy the `docker-compose.override.yaml` file from the NDA.
2. Run the following command:
   ```bash
   docker-compose up -d --build api-gateway ai-service user-service ai-database user-database
   ```
   (Currently we only develop apps with those services)

### Localhost with Native Applications
For easier development, you can run the services natively:
1. Copy the relevant `.env` files into each service directory.
2. Start each service using its specific commands.

### Production
In the production environment:
1. Whenever code is updated on the `dev` branch, a pipeline is triggered.
2. The pipeline builds new Docker images and pushes them to the production environment.

## Notes
- Ensure all the environment variables are setup correctly.

