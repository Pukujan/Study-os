<#
.SYNOPSIS
  Local Playwright UX defect scout against live Study-os (default: https://study.design-bakery.com).

.DESCRIPTION
  Thin wrapper around tools/ux-defect/ux-defect-pass.cjs.
  Writes timestamped artifacts under artifacts/ux-defect-playwright/<stamp>/
  including schema-shaped summary.json (docs/schemas/ux-defect-report.v1.json).

  Local = scout while fixing. CI Playwright specs are the merge gate.
  Any P0/P1 in summary.json fails this script (exit 1). Low-confidence notes
  stay in summary.detail.json — agents should re-check those manually.
#>
[CmdletBinding()]
param(
  [string]$BaseUrl = $(if ($env:E2E_BASE_URL) { $env:E2E_BASE_URL } else { "https://study.design-bakery.com" }),
  [string]$RepoRoot = "",
  [switch]$Headed
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$art = Join-Path $RepoRoot "artifacts\ux-defect-playwright\$stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $art "screenshots") | Out-Null

$harness = Join-Path $RepoRoot "tools\ux-defect\ux-defect-pass.cjs"
if (-not (Test-Path $harness)) { throw "Missing harness: $harness" }

# Prefer repo-local Playwright if present; else global npx.
$webDir = Join-Path $RepoRoot "web"
$env:E2E_BASE_URL = $BaseUrl
$env:ART_DIR = $art
$env:RUN_STARTED = (Get-Date).ToUniversalTime().ToString("o")
$env:RUN_ID = "pw-$stamp"
if ($Headed) { $env:HEADED = "1" } else { Remove-Item Env:HEADED -ErrorAction SilentlyContinue }

Write-Host "Playwright UX defect scout"
Write-Host "  BASE_URL = $BaseUrl"
Write-Host "  ART_DIR  = $art"

Push-Location $webDir
try {
  if (-not (Test-Path (Join-Path $webDir "node_modules\playwright"))) {
    Write-Host "Installing web deps (npm ci) so Playwright is available..."
    npm ci
  }
  # Ensure chromium is present for the standalone require("playwright") harness.
  npx playwright install chromium | Out-Host
  node $harness
  $code = $LASTEXITCODE
} finally {
  Pop-Location
}

Write-Host "Done. summary.json => $(Join-Path $art 'summary.json')"
if ($code -ne 0) { exit $code }
