# Action-Agent Helm Chart

This chart packages all backend services required by the project. The default
`values.yaml` file is geared towards local development. For staging or
production, use `values-stg.yaml` or `values-prod.yaml` respectively.

A typical install looks like:

```bash
helm install action-agent ./helm 
```

The `helm-deploy.sh` script and the Makefile in the parent directory wrap this
command and set the appropriate environment values.
