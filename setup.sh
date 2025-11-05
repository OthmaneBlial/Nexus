#!/usr/bin/env bash
# Bootstrap and launch the Nexus development stack (backend API, optional Celery worker).
# Usage: ./setup.sh [--no-install]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="${ROOT_DIR}/apps"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN=${PYTHON_BIN:-python3}
NO_INSTALL=false
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

API_PORT=${API_PORT:-8100}
BROKER_URL=${NEXUS_CELERY_BROKER:-redis://localhost:6379/0}

check_port_free() {
  local host=$1
  local port=$2
  python - "$host" "$port" <<'PY'
import socket, sys
host = sys.argv[1]
port = int(sys.argv[2])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.5)
    result = sock.connect_ex((host, port))
    sys.exit(0 if result != 0 else 1)
PY
}

ensure_redis_available() {
  python - "$BROKER_URL" <<'PY'
import socket, sys
from urllib.parse import urlparse

url = urlparse(sys.argv[1])
if url.scheme and not url.scheme.startswith("redis"):
    sys.exit(0)

host = url.hostname or "localhost"
port = url.port or 6379

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(1)
    if sock.connect_ex((host, port)) != 0:
        sys.exit(1)
sys.exit(0)
PY
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-install)
      NO_INSTALL=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$APPS_DIR"

if [ "$NO_INSTALL" = false ]; then
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"
  echo -n "Installing Python dependencies… "
  pip install --upgrade pip setuptools wheel >/dev/null 2>&1
  if pip install --quiet --no-input --progress-bar off -r "${ROOT_DIR}/backend/requirements.txt"; then
    echo "done."
  else
    echo "failed." >&2
    exit 1
  fi

  echo -n "Installing frontend dependencies… "
  if (cd "${ROOT_DIR}/frontend" && npm install --silent); then
    echo "done."
  else
    echo "failed." >&2
    exit 1
  fi
else
  if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found at $VENV_DIR. Re-run without --no-install." >&2
    exit 1
  fi
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"
fi

export PYTHONPATH="${ROOT_DIR}:${ROOT_DIR}/backend"
export NEXUS_ALLOWED_ROOT="${NEXUS_ALLOWED_ROOT:-${APPS_DIR}}"

if ! check_port_free "127.0.0.1" "${API_PORT}"; then
  echo "[setup] Port ${API_PORT} is already in use. Set API_PORT to a free port." >&2
  exit 1
fi


START_CELERY=true
if ensure_redis_available; then
  export NEXUS_TASK_MODE="${NEXUS_TASK_MODE:-celery}"
else
  echo "[setup] Redis broker not reachable at ${BROKER_URL}. Falling back to inline task mode." >&2
  export NEXUS_TASK_MODE="inline"
  START_CELERY=false
fi

echo -n "Building frontend assets… "
if (cd "${ROOT_DIR}/frontend" && npm run --silent build -- --logLevel error --clearScreen=false); then
  echo "done."
else
  echo "failed." >&2
  exit 1
fi

cleanup() {
  echo "Shutting down Nexus services…"
  [[ -n "${UVICORN_PID:-}" ]] && kill "${UVICORN_PID}" 2>/dev/null || true
  [[ -n "${CELERY_PID:-}" ]] && kill "${CELERY_PID}" 2>/dev/null || true
  wait || true
}

trap cleanup EXIT INT TERM

echo "Starting FastAPI backend on http://localhost:${API_PORT} …"
uvicorn backend.app.main:app --app-dir "${ROOT_DIR}" --host 0.0.0.0 --port "${API_PORT}" --log-level warning &
UVICORN_PID=$!

if [ "$START_CELERY" = true ]; then
  echo "Starting Celery worker…"
  celery -A backend.app.tasks.celery_app worker --loglevel=warning &
  CELERY_PID=$!
fi

echo ""
echo "Nexus is running:"
echo "  API & UI:  http://0.0.0.0:${API_PORT}"
echo "  Docs:      http://0.0.0.0:${API_PORT}/docs"
echo "  Workspace: ${APPS_DIR}"
echo ""
echo "Press Ctrl+C to stop all services."

wait
