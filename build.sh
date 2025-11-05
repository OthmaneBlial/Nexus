#!/usr/bin/env bash
# Build and deploy the Nexus stack to Google Cloud Run.

set -euo pipefail

trap 'echo "Deployment failed. Review the output above for details." >&2; exit 1' ERR

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required command '${cmd}' not found on PATH." >&2
    exit 1
  fi
}

ensure_env() {
  local name="$1"
  local value="$2"
  if [[ -z "${value}" ]]; then
    echo "Environment variable ${name} is required. Export ${name}=... and retry." >&2
    exit 1
  fi
}

enable_api() {
  local api="$1"
  if ! gcloud services list --enabled --format="value(config.name)" | grep -Fxq "${api}"; then
    echo "Enabling ${api}..."
    gcloud services enable "${api}" --quiet
  else
    echo "${api} already enabled."
  fi
}

require_command gcloud

if [[ -z "${PROJECT_ID:-}" ]]; then
  PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
  [[ "${PROJECT_ID}" == "(unset)" ]] && PROJECT_ID=""
fi

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-nexus}"
IMAGE_NAME="${IMAGE_NAME:-nexus}"
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d-%H%M%S)}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-gcr.io}"
CLOUD_RUN_PLATFORM="${CLOUD_RUN_PLATFORM:-managed}"
CLOUD_RUN_PORT="${CLOUD_RUN_PORT:-8080}"
CLOUD_RUN_MEMORY="${CLOUD_RUN_MEMORY:-1Gi}"
CLOUD_RUN_CPU="${CLOUD_RUN_CPU:-1}"
CLOUD_RUN_CONCURRENCY="${CLOUD_RUN_CONCURRENCY:-80}"
CLOUD_RUN_MIN_INSTANCES="${CLOUD_RUN_MIN_INSTANCES:-0}"
CLOUD_RUN_MAX_INSTANCES="${CLOUD_RUN_MAX_INSTANCES:-3}"
ALLOW_UNAUTH="${ALLOW_UNAUTH:-true}"
CLOUD_RUN_ENV_VARS="${CLOUD_RUN_ENV_VARS:-NEXUS_ALLOWED_ROOT=/workspace,NEXUS_TASK_MODE=inline}"
EXTRA_DEPLOY_ARGS="${EXTRA_DEPLOY_ARGS:-}"

ensure_env "PROJECT_ID" "${PROJECT_ID}"
ensure_env "REGION" "${REGION}"

IMAGE_URI="${IMAGE_REGISTRY}/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Configuration:"
echo "  PROJECT_ID       = ${PROJECT_ID}"
echo "  REGION           = ${REGION}"
echo "  SERVICE_NAME     = ${SERVICE_NAME}"
echo "  IMAGE_URI        = ${IMAGE_URI}"
echo "  CLOUD_RUN_PORT   = ${CLOUD_RUN_PORT}"
echo "  CLOUD_RUN_MEMORY = ${CLOUD_RUN_MEMORY}"
echo "  CLOUD_RUN_CPU    = ${CLOUD_RUN_CPU}"
echo "  CLOUD_RUN_ENV    = ${CLOUD_RUN_ENV_VARS:-<none>}"
echo

echo "Checking gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q '.'; then
  echo "No active gcloud account. Run 'gcloud auth login' and retry." >&2
  exit 1
fi

echo "Setting active project..."
gcloud config set project "${PROJECT_ID}" >/dev/null

echo "Ensuring required APIs are enabled..."
enable_api cloudbuild.googleapis.com
enable_api run.googleapis.com

echo "Submitting build to Cloud Build..."
gcloud builds submit "${ROOT_DIR}" \
  --tag "${IMAGE_URI}" \
  --project "${PROJECT_ID}"

echo "Deploying service to Cloud Run..."
deploy_args=(
  "${SERVICE_NAME}"
  --image "${IMAGE_URI}"
  --platform "${CLOUD_RUN_PLATFORM}"
  --region "${REGION}"
  --port "${CLOUD_RUN_PORT}"
  --memory "${CLOUD_RUN_MEMORY}"
  --cpu "${CLOUD_RUN_CPU}"
  --concurrency "${CLOUD_RUN_CONCURRENCY}"
  --min-instances "${CLOUD_RUN_MIN_INSTANCES}"
  --max-instances "${CLOUD_RUN_MAX_INSTANCES}"
  --timeout "3600"
  --project "${PROJECT_ID}"
)

if [[ -n "${CLOUD_RUN_ENV_VARS}" ]]; then
  deploy_args+=(--set-env-vars "${CLOUD_RUN_ENV_VARS}")
fi

if [[ "${ALLOW_UNAUTH}" == "true" ]]; then
  deploy_args+=(--allow-unauthenticated)
fi

if [[ -n "${EXTRA_DEPLOY_ARGS}" ]]; then
  # shellcheck disable=SC2206
  extra_args=( ${EXTRA_DEPLOY_ARGS} )
  deploy_args+=("${extra_args[@]}")
fi

gcloud run deploy "${deploy_args[@]}"

SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" \
  --platform "${CLOUD_RUN_PLATFORM}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format="value(status.url)")"

echo
echo "Deployment complete."
echo "Service URL: ${SERVICE_URL}"
echo "API health: ${SERVICE_URL}/health"
echo "API base:   ${SERVICE_URL}/api"
echo "Docs:       ${SERVICE_URL}/docs"
