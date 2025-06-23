# Cert-Manager Configuration for Let's Encrypt SSL

This Helm chart configures cert-manager ClusterIssuers for automatic SSL certificate provisioning using Let's Encrypt.

## Prerequisites

1. **cert-manager** must be installed in your Kubernetes cluster:
   ```bash
   kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

2. **NGINX Ingress Controller** must be installed and configured.

## Installation

### Development Environment
```bash
helm install cert-manager-config ./cert-manager -f ./cert-manager/values.dev.yaml
```

### Staging Environment
```bash
helm install cert-manager-config ./cert-manager -f ./cert-manager/values.stg.yaml
```

### Production Environment
```bash
helm install cert-manager-config ./cert-manager -f ./cert-manager/values.prod.yaml
```

## Configuration

### ClusterIssuers Created

1. **letsencrypt-prod**: Production Let's Encrypt certificates
   - Used for production domains
   - Rate limits apply (50 certificates per week per domain)

2. **letsencrypt-staging**: Staging Let's Encrypt certificates
   - Used for testing and development
   - Higher rate limits
   - Certificates are not trusted by browsers

### Automatic Certificate Management

Once the ClusterIssuers are deployed, certificates will be automatically:
- Requested from Let's Encrypt when an Ingress with the proper annotations is created
- Renewed before expiration (30 days before)
- Stored as Kubernetes secrets

### Ingress Configuration

The API Gateway ingress is configured with:
- `cert-manager.io/cluster-issuer`: Specifies which ClusterIssuer to use
- `nginx.ingress.kubernetes.io/ssl-redirect`: Forces HTTP to HTTPS redirect
- `nginx.ingress.kubernetes.io/force-ssl-redirect`: Ensures SSL enforcement

## Troubleshooting

### Check Certificate Status
```bash
kubectl get certificates
kubectl describe certificate <certificate-name>
```

### Check ClusterIssuer Status
```bash
kubectl get clusterissuer
kubectl describe clusterissuer letsencrypt-prod
```

### Check cert-manager Logs
```bash
kubectl logs -n cert-manager deployment/cert-manager
```

### Common Issues

1. **DNS not pointing to cluster**: Ensure your domain DNS points to the cluster's ingress IP
2. **Rate limits**: Use staging issuer for testing
3. **ACME challenge failures**: Check that HTTP-01 challenge can reach your ingress

## Environment-Specific Configuration

- **Development**: Uses staging Let's Encrypt server for testing
- **Staging**: Uses staging Let's Encrypt server for pre-production testing
- **Production**: Uses production Let's Encrypt server for live certificates

## Security Notes

- Let's Encrypt certificates are valid for 90 days
- Automatic renewal happens at 60 days
- Private keys are stored securely in Kubernetes secrets
- Only domains you control can get certificates (domain validation required)
