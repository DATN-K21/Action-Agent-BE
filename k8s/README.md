# Kubernetes Deployment

This directory provides the Helm chart used to deploy the Action-Agent backend.
Traditional manifests were removed in favour of a single chart.

## Quick start

```bash
# install the chart into a cluster
make deploy ENV=dev
```

Use `ENV=stg` or `ENV=prod` to deploy staging or production values.

## Repository layout

```
k8s/
├── helm/            # Helm chart (Chart.yaml, templates and values files)
├── helm-deploy.sh   # Wrapper script used by the Makefile
└── Makefile         # Convenience targets for Helm
```

The default values in `helm/values.yaml` target a local development setup.
Production specific configuration is provided in `values-stg.yaml` and
`values-prod.yaml`.
