# Refactored version of AI Service

## 1. Poetry Installation
```bash
pip install poetry
```

## 2. Install Dependencies
```bash
poetry install
```

## 3. Build and Migration
```bash
docker-compose up
```

## 4. Setup google cloud console for gmail api
- Go to https://console.cloud.google.com/
- Create a new project
- Enable Gmail API
- Create OAuth 2.0 Client ID
- Download the credentials.json file and place it in the root directory of the project
- Rename the credentials.json file to client_secrets.json and put into /private/auth folder
- Add redirect uri to the OAuth 2.0 Client ID (https://localhost:5001/gmail/auth/callback)
- Configure OAuth consent screen:
  - Add Test Users to Consent Screen
  - Add restricted scopes to the OAuth 2.0 Client ID (https://gmail.google.com/)

## 5. Make cert for https
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
## 6. Run the project
```bash
python run.py
```