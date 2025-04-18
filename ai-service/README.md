# AI Service
## 1. Introduction
This project is a web application that provides a service to send emails using the Gmail API. 
The application is built using the Fastapi, Langchain (Using Langgraph) and Composio Frameworks.

This service is designed to provide APIs for asking and answering AI. 
It supports multiple purposes such as chatting with LLM, retrieving information 
from given knowledge or searching on Wikipedia.

## 2. Setup environment
You should copy .env.example and rename it to .env. 
Then you can modify the environment variables in the .env file.

### 2.1. Get api key for LLMs
#### 2.1.1. Get api key for OpenAI (Required)
You can get the api key from https://platform.openai.com/account/api-keys
#### 2.1.2. Get api key for AzureOpenAI (required)
You can get the api key from https://portal.azure.com/

### 2.2 Get api key for langchain (Required)
You can get the api key from https://langchain.com/

### 2.3 Get api key for search tool (Required)
Tavily search tool is used to search on wikipedia. You can get the api key from https://tavily.com/

### 2.4 Setup OAuth 2 (Optional - Currently not used)
Setup OAuth for initializing connection of Composio tools (Currently use composio OAuth).
- Go to https://console.cloud.google.com/
- Create a new project
- Enable Gmail API
- Create OAuth 2.0 Client ID
- Download the credentials.json file and place it in the root directory of the project
- Rename the credentials.json file to client_secrets.json and put into /private/auth folder
- Add redirect uri to the OAuth 2.0 Client ID (http://localhost:5001/gmail/auth/callback)
- Configure OAuth consent screen:
  - Add Test Users to Consent Screen
  - Add restricted scopes to the OAuth 2.0 Client ID

### 2.5 Make cert for https (Optional - Setup for local running - using self-signed certificate)
**Notice:** If you want to run with http, you can skip this step.

To receive access token from OAuth 2, the application must run on https.

- Download chocolatey:
  - Run powershell as administrator
  - Run the following command:
    ```bash
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```
- Install mkcert:
  - Run the following command:
    ```bash
    choco install mkcert
    ```
- Create a certificate:
  - Run the following command:
    ```bash
    mkcert -install
    mkcert localhost
    ```
  - Copy the certificate to the project:
    ```bash
    cp localhost.pem private/cert/localhost-key.pem
    cp localhost-key.pem private/cert/localhost-key.pem
    ```

## 3. Run the application directly using IDE

### Step 1. Install poetry (if you haven't installed it yet):
* Install poetry using the following command:
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```
* To verify the installation, run:
  ```bash
  poetry --version
  ```

### Step 2. Setup virtual environment:
* Create a virtual environment using the following command:
  ```bash
  poetry install
  ```
* Activate the virtual environment:
  ```bash
    poetry shell
    ```
* Exit the virtual environment:
  ```bash
    exit
    ```
  
### Step 3. Run the application:
* Run the application using the following command:
  ```bash
    poetry run python run.py
  ```

## 4. Deployment by container
### Step 1. Turn off Postgres database on the local machine
* If you have installed Postgres on your local machine, you should turn it off to avoid conflict with the Postgres container.
* To turn off Postgres, run the following command:
  * For linux:
    ```bash
    sudo service postgresql stop
    ```
  * For Windows (run as administrator, on powershell or cmd):
      ```bash
      net stop postgresql-x64-16
      ```
**Notice:** For windows, you must replace 16 with your Postgres version number if different.
To get the version number, you can run the following command:
```bash
psql --version
```

### Step 2. Build and run the application using docker-compose
* Build and run the application using the following command:
  ```bash
  docker-compose up --build
  ```

## 5. Hosted service