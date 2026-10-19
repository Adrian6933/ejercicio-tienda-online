#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VERSION="$(git describe --always --dirty 2>/dev/null || echo local)"
mkdir -p .artifacts
(cd backend && python -m pytest)
(cd frontend && npm ci && npm test && npm run build)
printf '%s\n' "$VERSION" > .artifacts/version.txt
tar -czf .artifacts/frontend.tar.gz -C frontend/dist .
sha256sum .artifacts/frontend.tar.gz > .artifacts/frontend.tar.gz.sha256
sha256sum -c .artifacts/frontend.tar.gz.sha256
printf 'Build completado: %s\n' "$VERSION"
