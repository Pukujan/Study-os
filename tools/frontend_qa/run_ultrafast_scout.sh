#!/usr/bin/env bash
# Study-os frontend QA — Ultrafast scout wrapper (QA harness only).
# Does not import Jev/OpenRouter into product code.
set -euo pipefail

TARGET_URL="${1:-https://study.design-bakery.com}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export ULTRAFAST_BASE_URL="${ULTRAFAST_BASE_URL:-$TARGET_URL}"

echo "Mandate: docs/AGENT_FRONTEND_QA.md"
echo "Target: ${TARGET_URL}"
echo "Contract: docs/PDD_UX_DEFECT_EXPLORATION.md + docs/schemas/ux-defect-report.v1.json"

# Prefer in-repo scout / crawl runners (local-scout PR + Ultrafast-CI).
SCOUT="${ROOT}/tools/ux-defect/run_ultrafast_scout.py"
IN_REPO="${ROOT}/tools/run_jev_ultrafast_ux_crawl.py"
if [[ -f "${SCOUT}" ]]; then
  echo "Using in-repo scout: tools/ux-defect/run_ultrafast_scout.py"
  export BASE_URL="${TARGET_URL}"
  export ART_DIR="${ART_DIR:-${ROOT}/artifacts/ux-defect-ultrafast/$(date -u +%Y%m%d-%H%M%S)}"
  mkdir -p "${ART_DIR}/screenshots"
  # Resolve Ultrafast root for imports
  if [[ -z "${JEV_ULTRAFAST_ROOT:-}" ]]; then
    for c in "${ROOT}/../jev-ultrafast" "/workspace/jev-ultrafast" "D:/claude/jev-ultrafast"; do
      [[ -d "$c" ]] && export JEV_ULTRAFAST_ROOT="$c" && break
    done
  fi
  cd "${ROOT}"
  exec python3 "${SCOUT}"
fi
if [[ -f "${IN_REPO}" ]]; then
  echo "Using in-repo runner: tools/run_jev_ultrafast_ux_crawl.py"
  cd "${ROOT}"
  exec python3 "${IN_REPO}"
fi

resolve_ultrafast() {
  if [[ -n "${JEV_ULTRAFAST_ROOT:-}" && -d "${JEV_ULTRAFAST_ROOT}" ]]; then
    printf '%s\n' "${JEV_ULTRAFAST_ROOT}"
    return 0
  fi
  local candidates=(
    "${ROOT}/../jev-ultrafast"
    "/workspace/jev-ultrafast"
    "D:/claude/jev-ultrafast"
    "/mnt/d/claude/jev-ultrafast"
  )
  local c
  for c in "${candidates[@]}"; do
    if [[ -d "${c}" ]]; then
      printf '%s\n' "${c}"
      return 0
    fi
  done
  return 1
}

if ! UF="$(resolve_ultrafast)"; then
  cat <<HINT >&2
Ultrafast root not found and tools/run_jev_ultrafast_ux_crawl.py not present yet.
  Clone https://github.com/Pukujan/jev-ultrafast
  or set JEV_ULTRAFAST_ROOT (Windows default: D:\\claude\\jev-ultrafast).
  Target URL would have been: ${TARGET_URL}
  Stack with the Ultrafast-CI / local-runner PR when it lands the in-repo crawl.
HINT
  exit 2
fi

echo "Ultrafast root: ${UF}"
if [[ -x "${UF}/bin/ultrafast" ]]; then
  exec "${UF}/bin/ultrafast" scout --url "${TARGET_URL}"
fi
echo "Open ${UF}/README.md and run the documented guest crawl against ${TARGET_URL}."
echo "After crawl: python tools/gate_ux_defect_report.py <summary.json>"
echo "Durable copy (optional): docs/benchmarks/ux-defect-jev-ultrafast/<date>/"
exit 0
