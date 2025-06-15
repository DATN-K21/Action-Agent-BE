#!/usr/bin/env bash

# ---------------------------------------------------------------------------
# Helm‑based Action‑Agent Deployment Helper
# ---------------------------------------------------------------------------
# ▸ Smart wrapper around `helm upgrade --install`                                      
# ▸ Works idempotently in CI and from your laptop                                     
# ▸ Automatically handles namespaces, env‑specific values, and FAILED releases        
# ---------------------------------------------------------------------------
# Usage examples
#   ./helm-deploy.sh -e dev               # fresh dev deploy (namespace = default)
#   ./helm-deploy.sh -e stg               # deploy to stg namespace action-agent-stg
#   ./helm-deploy.sh -e stg --dry-run     # render manifests only
#   ./helm-deploy.sh -e prod --atomic     # prod rollout with automatic rollback
# ---------------------------------------------------------------------------

set -euo pipefail

# ───────────────────────── Colors ─────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}    $*"; }
ok()      { echo -e "${GREEN}[OK]${NC}      $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
err()     { echo -e "${RED}[ERROR]${NC}   $*" >&2; }

# ──────────────────────── Defaults ────────────────────────
ENVIRONMENT=dev
NAMESPACE="default"
RELEASE="action-agent"
CHART_PATH="./helm"
VALUES_FILE=""
DRY_RUN=false
ATOMIC=false
TIMEOUT="600s"

# ─────────────────────── Argument parse ───────────────────
print_help() {
  cat <<EOF
Usage: $(basename "$0") [options]
Options:
  -e, --environment ENV   dev|stg|prod   (default: dev)
  -n, --namespace   NS    override namespace (default derived from env)
  -r, --release     NAME  helm release name (default: action-agent)
  -c, --chart       PATH  chart directory (default: ./helm)
  -t, --timeout     DUR   helm --timeout duration (default: 600s)
      --dry-run            render only, no apply
      --atomic             rollback on failed upgrade (prod safe)
  -h, --help               show this help and exit
EOF
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--environment) ENVIRONMENT=$2; shift 2;;
    -n|--namespace)   NAMESPACE=$2;   shift 2;;
    -r|--release)     RELEASE=$2;     shift 2;;
    -c|--chart)       CHART_PATH=$2;  shift 2;;
    -t|--timeout)     TIMEOUT=$2;     shift 2;;
    --dry-run)        DRY_RUN=true;   shift;;
    --atomic)         ATOMIC=true;    shift;;
    -h|--help)        print_help; exit 0;;
    *) err "Unknown option $1"; print_help; exit 1;;
  esac
done

# ───────────────── Namespace & values derivation ──────────
if [[ "$NAMESPACE" == "default" ]]; then
  case $ENVIRONMENT in
    stg)  NAMESPACE="action-agent-stg";;
    prod) NAMESPACE="action-agent-prod";;
  esac
fi
RELEASE="${RELEASE}-${ENVIRONMENT}"

DEFAULT_VALUES="${CHART_PATH}/values.yaml"
ENV_VALUES="${CHART_PATH}/values-${ENVIRONMENT}.yaml"
if [[ -f "$ENV_VALUES" ]]; then VALUES_FILE=$ENV_VALUES; else VALUES_FILE=$DEFAULT_VALUES; fi

# ───────────────── Prerequisite checks ────────────────────
command -v helm >/dev/null || { err "Helm not found"; exit 1; }
command -v kubectl >/dev/null || { err "kubectl not found"; exit 1; }

kubectl cluster-info >/dev/null || { err "Cannot reach Kubernetes cluster"; exit 1; }
ok "Connected to cluster"

kubectl get ns "$NAMESPACE" >/dev/null 2>&1 || {
  info "Creating namespace $NAMESPACE"; kubectl create ns "$NAMESPACE"; }

# ─────────────── FAILED release auto‑cleanup ──────────────
if helm status "$RELEASE" -n "$NAMESPACE" >/dev/null 2>&1; then
  CURRENT_STATUS=$(helm status "$RELEASE" -n "$NAMESPACE" -o json | jq -r .info.status)
  if [[ "$CURRENT_STATUS" == "failed" ]]; then
    warn "Release exists in FAILED state → uninstalling"
    helm uninstall "$RELEASE" -n "$NAMESPACE" --no-hooks || true
  fi
fi

# ───────────────────── Helm command build ─────────────────
set +u  # values file may be unset but we still rely on var expansion below
HELM_ARGS=( upgrade --install "$RELEASE" "$CHART_PATH" \
  --namespace "$NAMESPACE" \
  --values "$VALUES_FILE" \
  --set "global.environment=$ENVIRONMENT" \
  --set "global.namespace=$NAMESPACE" \
  --timeout "$TIMEOUT" )

$DRY_RUN   && HELM_ARGS+=( --dry-run --debug )
$ATOMIC    && HELM_ARGS+=( --atomic )

info "Helm cmd ➜ helm ${HELM_ARGS[*]}"
helm "${HELM_ARGS[@]}"

if $DRY_RUN; then ok "Dry‑run complete"; exit 0; fi

# ────────────────────── Summary output ────────────────────
helm status "$RELEASE" -n "$NAMESPACE"
echo
kubectl get pods,svc -n "$NAMESPACE"

echo -e "${BLUE}Useful:
  ✦ Logs:     kubectl logs -f deployment/${RELEASE}-action-agent-backend-api-gateway -n ${NAMESPACE}
  ✦ Port‑fw:  kubectl port-forward svc/${RELEASE}-action-agent-backend-api-gateway 15000:15000 -n ${NAMESPACE}
${NC}"

ok "Deployment finished"
