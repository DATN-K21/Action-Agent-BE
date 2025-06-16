#!/bin/bash

echo "=== Action Agent K8s Connectivity Diagnostics ==="
echo ""

# Get the release name (assuming default)
RELEASE_NAME=${1:-"action-agent"}
NAMESPACE=${2:-"default"}

echo "Checking deployment status for release: $RELEASE_NAME in namespace: $NAMESPACE"
echo ""

# Check if pods are running
echo "1. Pod Status:"
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo ""
echo "2. Service Status:"
kubectl get services -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo ""
echo "3. Detailed Pod Status with Ready/Restart info:"
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME -o wide

echo ""
echo "4. Checking for any failed pods:"
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME --field-selector=status.phase!=Running

echo ""
echo "5. Database Connectivity Tests:"

# Get pod names
AI_POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=ai-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
USER_POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=user-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
POSTGRES_POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=postgresql -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
MONGO_POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=mongodb -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
REDIS_POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

echo "Found pods:"
echo "  AI Service: $AI_POD"
echo "  User Service: $USER_POD" 
echo "  PostgreSQL: $POSTGRES_POD"
echo "  MongoDB: $MONGO_POD"
echo "  Redis: $REDIS_POD"
echo ""

if [[ -n "$POSTGRES_POD" ]]; then
    echo "5a. Testing PostgreSQL connectivity:"
    kubectl exec -n $NAMESPACE $POSTGRES_POD -- pg_isready -U postgres -h localhost
    if [[ -n "$AI_POD" ]]; then
        echo "5b. Testing PostgreSQL from AI service:"
        kubectl exec -n $NAMESPACE $AI_POD -- nc -zv $RELEASE_NAME-postgresql 5432 2>&1 | head -1
    fi
fi

if [[ -n "$MONGO_POD" ]]; then
    echo "5c. Testing MongoDB connectivity:"
    kubectl exec -n $NAMESPACE $MONGO_POD -- mongosh --eval "db.adminCommand('ping')" --quiet
    if [[ -n "$USER_POD" ]]; then
        echo "5d. Testing MongoDB from User service:"
        kubectl exec -n $NAMESPACE $USER_POD -- nc -zv $RELEASE_NAME-mongodb 27017 2>&1 | head -1
    fi
fi

if [[ -n "$REDIS_POD" ]]; then
    echo "5e. Testing Redis connectivity:"
    kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli ping
    if [[ -n "$USER_POD" ]]; then
        echo "5f. Testing Redis from User service:"
        kubectl exec -n $NAMESPACE $USER_POD -- nc -zv $RELEASE_NAME-redis 6379 2>&1 | head -1
    fi
fi

echo ""
echo "6. Service DNS Resolution Test:"
kubectl run test-dns --image=busybox --rm -it --restart=Never -n $NAMESPACE -- nslookup $RELEASE_NAME-postgresql.$NAMESPACE.svc.cluster.local

echo ""
echo "7. Environment Variables (from AI Service):"
if [[ -n "$AI_POD" ]]; then
    echo "DATABASE_URL:"
    kubectl exec -n $NAMESPACE $AI_POD -- printenv DATABASE_URL
    echo "REDIS_URL:"
    kubectl exec -n $NAMESPACE $AI_POD -- printenv REDIS_URL
fi

echo ""
echo "8. Recent Pod Logs (last 20 lines):"
if [[ -n "$AI_POD" ]]; then
    echo "AI Service logs:"
    kubectl logs -n $NAMESPACE $AI_POD --tail=20
fi

if [[ -n "$USER_POD" ]]; then
    echo "User Service logs:"
    kubectl logs -n $NAMESPACE $USER_POD --tail=20
fi

echo ""
echo "=== Diagnostics Complete ==="
