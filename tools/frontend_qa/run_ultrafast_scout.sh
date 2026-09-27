#!/usr/bin/env bash
# Study-os frontend QA — LOCAL Ultrafast scout (QA harness only).
# Ultrafast runs FIRST for agent FE claims. Not a GitHub Actions job.
# Does not import Jev/OpenRouter into product code.
set -euo pipefail

TARGET_URL="${1:-https://study.design-bakery.com}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export ULTRAFAST_BASE_URL="${ULTRAFAST_BASE_URL:-$TARGET_URL}"

echo "Mandate: docs/AGENT_FRONTEND_QA.md (Ultrafast-first, local/scout — NOT CI)"
echo "Target: ${TARGET_URL}"
echo "Contract: docs/PDD_UX_DEFECT_EXPLORATION.md + docs/schemas/ux-defect-report.v1.json"
echo "Note: OpenRouter Decisions misconfig ≠ Ultrafast flake. P0/P1 fails claim regardless of confidence."

SCOUT="${ROOT}/tools/ux-defect/run_ultrafast_scout.py"
if [[ -f "${SCOUT}" ]]; then
  echo "Using in-repo scout: tools/ux-defect/run_ultrafast_scout.py"
  export BASE_URL="${TARGET_URL}"
  # Prefer an explicit ART_DIR; otherwise stamp under this repo (ignore leaked env from other worktrees).
  if [[ -z "${ART_DIR:-}" || "${ART_DIR}" != "${ROOT}"* ]]; then
    export ART_DIR="${ROOT}/artifacts/ux-defect-ultrafast/$(date -u +%Y%m%d-%H%M%S)"
  fi
  mkdir -p "${ART_DIR}/screenshots"
  if [[ -z "${JEV_ULTRAFAST_ROOT:-}" ]]; then
    for c in \
      "${ROOT}/../jev-ultrafast" \
      "/workspace/jev-ultrafast" \
      "D:/claude/jev-ultrafast" \
      "/mnt/d/claude/jev-ultrafast"
    do
      [[ -d "$c" ]] && export JEV_ULTRAFAST_ROOT="$c" && break
    done
  fi
  if [[ -z "${JEV_ULTRAFAST_ROOT:-}" ]]; then
    cat <<HINT >&2
Ultrafast root not found.
  Clone https://github.com/Pukujan/jev-ultrafast
  or set JEV_ULTRAFAST_ROOT
  Teresa-Pujan Windows default: D:\\claude\\jev-ultrafast
  Target URL: ${TARGET_URL}
HINT
    exit 2
  fi
  if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
    echo "WARN: OPENROUTER_API_KEY unset — Decisions will fail (config), not an Ultrafast flake." >&2
  fi
  echo "JEV_ULTRAFAST_ROOT=${JEV_ULTRAFAST_ROOT}"
  echo "ART_DIR=${ART_DIR}"
  cd "${ROOT}"
  exec python3 "${SCOUT}"
fi

cat <<HINT >&2
Missing tools/ux-defect/run_ultrafast_scout.py — unexpected for this checkout.
  Teresa-Pujan: powershell -File tools/ux-defect/Run-UltrafastScout.ps1
  Or restore the scout from main / docs/AGENT_FRONTEND_QA.md
HINT
exit 2
