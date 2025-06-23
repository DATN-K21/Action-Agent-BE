# Kubernetes + Helm Cheatsheet
---

## Prerequisites

1. **Kubernetes cluster** with kubectl configured
2. **Helm 3.x** installed
3. **NGINX Ingress Controller** installed in your cluster
4. **DNS configured** to point your domains to the cluster ingress IP

---

## SSL Certificate Setup with Let's Encrypt

### 1. Install cert-manager and Configure Let's Encrypt

Before deploying any services, install cert-manager for automatic SSL certificate management:

```bash
# Install cert-manager and Let's Encrypt configuration
make install-cert-manager ENV=<environment>
```

This will:
- Install cert-manager in your cluster
- Create ClusterIssuers for Let's Encrypt (production and staging)
- Configure automatic certificate provisioning

### 2. Verify cert-manager Installation

```bash
# Check cert-manager pods
kubectl get pods -n cert-manager

# Check ClusterIssuers
kubectl get clusterissuer
```

You should see:
- `letsencrypt-prod` (for production certificates)
- `letsencrypt-staging` (for testing)

---

## Create Namespace

```bash
kubectl create namespace <namespace-name>
```
> Example:
```bash
kubectl create namespace dev
```

---

## Create Secret from `.env` File

```bash
kubectl create secret generic <secret-name> \
  --from-env-file=<path-to-env-file> \
  -n <namespace-name>
```
> Example:
```bash
kubectl create secret generic env-secret \
  --from-env-file=./secrets/env \
  -n dev
```

---

## Create Secret for Container Registry (e.g., ACR)

```bash
kubectl create secret docker-registry regcred \
  --namespace <namespace-name> \
  --docker-server=<registry-url> \
  --docker-username=<username> \
  --docker-password=<password>
```
> Example:
```bash
kubectl create secret docker-registry regcred \
  --namespace dev \
  --docker-server=testcontainerregistrydev.azurecr.io \
  --docker-username=testcontainerregistrydev \
  --docker-password=<your-password>
```

---

## Install Helm Chart (idempotent)

```bash
helm upgrade --install <release-name> <chart-path> \
  -n <namespace> \
  -f <values-file>
```
> Example:
```bash
helm upgrade --install apigateway ./apigateway \
  -n dev \
  -f ./apigateway/values.dev.yaml
```

---

## List Helm Releases

```bash
helm list -n <namespace>
```
> Example:
```bash
helm list -n dev
```

## Upgrade Helm Release

```bash
helm upgrade <release-name> <chart-path> \
  -n <namespace> \
  -f <values-file>
```
> Example:
```bash
helm upgrade apigateway ./apigateway \
  -n dev \
  -f ./apigateway/values.dev.yaml
```

---

## Uninstall Helm Release

```bash
helm uninstall <release-name> -n <namespace>
```
> Example:
```bash
helm uninstall apigateway -n dev
```

---

## Helm Lint

```bash
helm lint <chart-path> -f <values-file>
```
> Example:
```bash
helm lint ./apigateway -f ./apigateway/values.dev.yaml
```

---

## Helm Template

```bash
helm template <release-name> <chart-path> \
  -n <namespace> \
  -f <values-file>
```
> Example:
```bash
helm template apigateway ./apigateway \
  -n dev \
  -f ./apigateway/values.dev.yaml
```

---

## Helm Dry-Run

```bash
helm install <release-name> <chart-path> \
  -n <namespace> \
  -f <values-file> \
  --dry-run --debug
```
> Example:
```bash
helm install apigateway ./apigateway \
  -n dev \
  -f ./apigateway/values.dev.yaml \
  --dry-run --debug
```

---

