# Helm Chart for Action-Agent-BE Microservices

This chart deploys the Action-Agent-BE stack on Kubernetes using best practices. It includes:
- api-gateway
- user-service
- ai-service
- ai-database (Postgres)
- user-database (MongoDB)
- elasticsearch
- kibana
- rabbitmq
- redis

## Structure

- `Chart.yaml` - Chart metadata
- `values.yaml` - Configurable values (images, env, secrets, ports, etc.)
- `templates/` - Kubernetes manifests (Deployment, Service, PVC, ConfigMap, Secret, Ingress)
- `templates/secrets.yaml` - Example for sensitive data
- `templates/configmap.yaml` - Example for non-sensitive config

## Best Practices
- Use `values.yaml` for all configuration
- Use Kubernetes Secrets for passwords/API keys
- Use PVCs for persistent data
- Use Ingress for external access (with TLS)
- Avoid hardcoding sensitive data
- Use resource requests/limits

---

## Getting Started

1. Install Helm: https://helm.sh/docs/intro/install/
2. Package and deploy the chart:
   ```bash
   helm install action-agent-be ./action-agent-be
   ```
3. Edit `values.yaml` to fit your environment (especially secrets)

---

## Directory Structure

```
action-agent-be/
  Chart.yaml
  values.yaml
  templates/
    deployment.yaml
    service.yaml
    pvc.yaml
    configmap.yaml
    secrets.yaml
    ingress.yaml
```

---

## Next Steps
- Fill in `values.yaml` with your configuration
- Add secrets to your cluster (or use Helm's `--set`/`--values`)
- Deploy to k3s and test
