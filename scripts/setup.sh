#!/usr/bin/env bash
# One-time / after-pull setup for a fresh machine.
#
# Usage:
#   ./scripts/setup.sh                 # backend + frontend
#   ./scripts/setup.sh --backend-only  # servers without Node.js
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
BACKEND_ONLY=0

if [[ "${1:-}" == "--backend-only" ]]; then
  BACKEND_ONLY=1
fi

echo "==> Backend"
cd "$BACKEND"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install Python 3.12+ first." >&2
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "Python 3.12+ is required. Found: $(python3 --version 2>&1)" >&2
  echo "Ubuntu 24.04 ships Python 3.12." >&2
  echo "On Ubuntu 22.04, install Python 3.12 via pyenv or the deadsnakes PPA." >&2
  exit 1
fi

if [[ ! -d venv ]]; then
  echo "Creating virtual environment..."
  if ! python3 -m venv venv; then
    echo "Could not create the venv. On Debian/Ubuntu run:" >&2
    echo "  sudo apt install python3-venv python3-pip" >&2
    exit 1
  fi
fi

./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example (SQLite by default)."
fi

./venv/bin/python manage.py migrate
./venv/bin/python manage.py check

echo "==> Database"
./venv/bin/python manage.py shell --verbosity 0 -c "
from django.conf import settings
from components.models import Component
default = settings.DATABASES['default']
engine = default['ENGINE'].rsplit('.', 1)[-1]
print('engine:', engine)
if engine == 'postgresql':
    print('host:', default.get('HOST'))
print('components:', Component.objects.count())
"
echo "Backend ready."

if [[ "$BACKEND_ONLY" -eq 0 ]]; then
  echo "==> Frontend"
  if command -v node >/dev/null 2>&1; then
    cd "$FRONTEND"
    if [[ ! -d node_modules ]]; then
      if [[ -f package-lock.json ]]; then
        npm ci
      else
        npm install
      fi
    fi
    echo "Frontend ready."
  else
    echo "Node.js not found; skipped frontend. Install Node 20+ or use --backend-only." >&2
  fi
fi

echo
echo "Done. Next:"
echo "  make backend    # http://localhost:8088"
echo "  make frontend   # http://localhost:5173"
echo "  make test"
