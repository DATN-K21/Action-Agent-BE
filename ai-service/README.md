# AI Service

## 1. Introduction
AI Service is a comprehensive backend solution providing advanced AI capabilities through a RESTful API interface. 
The application is built using FastAPI, Langchain (with Langgraph), and integrates with various LLM providers.

This service provides a robust platform for:
- AI-powered conversations and assistants
- Multi-provider LLM integration (OpenAI, Anthropic, Azure, Google, Cohere, Mistral)
- Knowledge retrieval and RAG (Retrieval-Augmented Generation)
- Team and user management with fine-grained permissions
- API key management for various LLM providers

## 2. Setup Environment
Begin by copying the `.env.example` file to create a new `.env` file:
```bash
cp .env.example .env
```
Then configure the environment variables in the `.env` file according to your needs.

### 2.1. LLM Provider API Keys
The service supports multiple LLM providers. Configure the ones you intend to use:

#### 2.1.1. OpenAI API Key
Obtain an API key from [OpenAI Platform](https://platform.openai.com/account/api-keys)

#### 2.1.2. Azure OpenAI API Key
Get your Azure OpenAI API key from the [Azure Portal](https://portal.azure.com/)

#### 2.1.3. Other Supported Providers (Optional)
- Anthropic: [Anthropic Console](https://console.anthropic.com/)
- Google AI: [Google AI Studio](https://ai.google.dev/)
- Cohere: [Cohere Dashboard](https://dashboard.cohere.com/)
- Mistral AI: [Mistral AI Console](https://console.mistral.ai/)

### 2.2. Langchain API Key
Required for certain langchain features. Obtain from [Langchain Platform](https://langchain.com/)

### 2.3. Search Tools Configuration
The service uses Tavily for web searches and information retrieval. Get your API key from [Tavily](https://tavily.com/)

### 2.4. Database Configuration
The service uses PostgreSQL for data storage. Configure the following in your `.env` file:
```
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ai_service
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 2.5. Authentication Setup
Configure authentication settings in your `.env` file:
```
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2.6. OAuth 2 Integration (Optional)
For external service integration with OAuth2:

1. Create OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable necessary APIs (e.g., Gmail API)
   - Create OAuth 2.0 Client ID
   - Download credentials and save as `client_secrets.json` in `/private/auth` folder

2. Configure OAuth settings:
   - Add redirect URI: `http://localhost:5001/auth/callback`
   - Configure OAuth consent screen:
     - Add test users
     - Configure appropriate scopes

### 2.7. HTTPS Setup for Local Development (Optional)
For secure local development with HTTPS:

#### Windows:
1. Install Chocolatey (PowerShell as administrator):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. Install mkcert:
   ```powershell
   choco install mkcert
   ```

3. Generate certificates:
   ```powershell
   mkcert -install
   mkcert localhost
   ```

4. Copy certificates to project:
   ```powershell
   mkdir -p private/cert
   cp localhost.pem private/cert/localhost.pem
   cp localhost-key.pem private/cert/localhost-key.pem
   ```

#### Linux/macOS:
1. Install mkcert (examples):
   - Ubuntu: `apt install mkcert`
   - macOS: `brew install mkcert`

2. Generate and copy certificates:
   ```bash
   mkcert -install
   mkcert localhost
   mkdir -p private/cert
   cp localhost.pem private/cert/localhost.pem
   cp localhost-key.pem private/cert/localhost-key.pem
   ```

## 3. Installation and Running

### 3.1. Local Development Setup

#### Step 1. Install Poetry
Poetry is used for dependency management:

```bash
# For Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# For Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -
```

Verify the installation:
```bash
poetry --version
```

#### Step 2. Set Up Virtual Environment
Install dependencies and create virtual environment:
```bash
# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# When finished, exit the environment
exit
```

#### Step 3. Database Setup
Ensure PostgreSQL is running and initialize the database:
```bash
# Run migrations to set up database schema
python run_migrations.py
```

#### Step 4. Start the Application
```bash
# Development server
poetry run python -m app.main

# Or using Uvicorn directly
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3.2. Docker Deployment

#### Step 1. Prepare Environment
If running PostgreSQL locally, stop the service to avoid port conflicts:

**Linux:**
```bash
sudo service postgresql stop
```

**Windows (PowerShell/CMD as administrator):**
```powershell
net stop postgresql-x64-16  # Replace '16' with your PostgreSQL version
```

#### Step 2. Build and Run with Docker Compose
```bash
# Build and start services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# Stop services
docker-compose down
```

### 3.3. Production Deployment
For production deployment, additional configuration is recommended:

1. Use environment-specific configuration files
2. Configure proper logging and monitoring
3. Set up SSL/TLS certificates for HTTPS
4. Implement proper backup strategy for the database
5. Configure appropriate scaling based on expected load

## 4. API Documentation
The service provides comprehensive API documentation:

### 4.1. Swagger UI
Once the service is running, access the interactive API documentation:
- Local development: http://localhost:8000/docs
- Docker deployment: http://localhost:8000/docs

### 4.2. API Documentation Files
Detailed API documentation is available in the `/docs` directory:

- **Main APIs:**
  - User API: `docs/public_user_api.md`
  - Assistant API: `docs/public_assistant_api.md`
  - Thread API: `docs/public_thread_api.md`
  - Team API: `docs/public_team_api.md`

- **Advanced Features:**
  - Member API: `docs/public_member_api.md`
  - Skill API: `docs/public_skill_api.md`
  - Upload API: `docs/public_upload_api.md`
  - Statistics API: `docs/public_statistics_api.md`
  - Connected MCP API: `docs/public_connected_mcp_api.md`
  - Connected Extension API: `docs/public_connected_extension_api.md`

## 5. Architecture

### 5.1. Core Components
- **FastAPI Backend**: Provides RESTful API endpoints
- **PostgreSQL Database**: Stores user data, threads, and AI interactions
- **LLM Integration**: Connects to multiple AI providers
- **RAG System**: For knowledge-augmented responses
- **Celery Workers**: Handles background processing tasks

### 5.2. Key Features
- Multi-tenant architecture supporting teams and users
- Pluggable LLM provider system with API key management
- Thread-based conversation history
- Upload and ingest capabilities for knowledge bases
- Extensible tool framework for AI assistants

## 6. Contributing

### 6.1. Development Workflow
1. Fork the repository
2. Create a feature branch
3. Implement changes with appropriate tests
4. Submit a pull request

### 6.2. Code Style
- Follow PEP 8 guidelines for Python code
- Use type annotations
- Document functions and modules

### 6.3. Testing
Run tests using pytest:
```bash
poetry run pytest
```

## 7. License
This project is proprietary software. All rights reserved.

## 8. Support and Contact
For questions or support, please contact the development team at nguyentuandat2k3cmg@gmail.com.