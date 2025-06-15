# Action-Agent Helm Chart

This chart deploys the backend microservices and optional infrastructure used by
Action-Agent.

Choose the appropriate values file for the environment:

- `values-dev.yaml` for local development
- `values-stg.yaml` for staging on AKS
- `values-prod.yaml` for production on AKS

Secrets are either created from `localSecrets` values or pulled from Azure Key
Vault when `secretProvider` is set to `azure`.
