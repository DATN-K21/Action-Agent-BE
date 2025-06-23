# User Service

## Introduction
This service manages authentication, user profiles and roles for the Action-Agent system. It is built with Node.js and MongoDB.

## Setup
1. Copy `.env.example` to `.env` and update the values for your environment.
2. Install dependencies:
   ```bash
   npm install
   ```

## Running locally
Start the application in watch mode:
```bash
npm run dev
```
The server listens on `http://localhost:15100` by default.

## Testing
After installing dependencies you can run the Jest test suite with:
```bash
npm test
```
