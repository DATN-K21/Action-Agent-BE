# Kubernetes Manifests

This directory contains Kubernetes manifests for running the Action-Agent microservices and their dependencies.
Each service now loads its environment variables from a `ConfigMap` and a `Secret` for readability and to keep sensitive data out of the manifests.
Apply the files in any order or all together:

```bash
kubectl apply -f ./k8s
```

> **Note:** The ConfigMaps and Secrets still contain placeholder values such as `<YOUR_OPENAI_API_KEY>`.
Replace them with real values before deploying.
