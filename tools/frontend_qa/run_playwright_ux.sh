#!/usr/bin/env bash
# Study-os frontend QA — Playwright UX + vision pass (SOS-0017 gate + e2e).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WEB="${ROOT}/web"

echo "Mandate: docs/AGENT_FRONTEND_QA.md"
echo "Specs: web/e2e/ (player-vision-gate.spec.ts)"
echo "CI twin: .github/workflows/ci.yml job 'playwright'"

# Optional fuller live UX defect pass (lands with Ultrafast-CI / local-runner work).
LIVE_PASS="${ROOT}/tools/ux-defect/ux-defect-pass.cjs"
if [[ "${PLAYWRIGHT_UX_DEFECT_PASS:-}" == "1" && -f "${LIVE_PASS}" ]]; then
  echo "PLAYWRIGHT_UX_DEFECT_PASS=1 → running tools/ux-defect/ux-defect-pass.cjs"
  cd "${ROOT}"
  exec node "${LIVE_PASS}" "$@"
fi

cd "${WEB}"

if [[ ! -d node_modules/@playwright ]]; then
  npm ci
fi

npx playwright install chromium >/dev/null

if [[ -n "${PLAYWRIGHT_BASE_URL:-}" ]]; then
  echo "PLAYWRIGHT_BASE_URL=${PLAYWRIGHT_BASE_URL}"
fi
if [[ -z "${INFERHUB_API_KEY:-}" ]]; then
  echo "NOTE: INFERHUB_API_KEY unset → vision records VISION_NOT_RUN (not a perceptual green)."
fi

exec npx playwright test "$@"
