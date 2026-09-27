<#
.SYNOPSIS
  Local Jev Ultrafast guest UX defect scout against live Study-os.

.DESCRIPTION
  Uses the jev-ultrafast checkout at D:\claude\jev-ultrafast (or $env:JEV_ULTRAFAST_ROOT),
  cloning/pinning https://github.com/Pukujan/jev-ultrafast if missing.
  Writes artifacts under artifacts/ux-defect-ultrafast/<stamp>/ with schema-shaped
  summary.json (docs/schemas/ux-defect-report.v1.json).

  Requires OPENROUTER_API_KEY (Decisions). Local = scout; CI = merge gate.
  P0/P1 fails the script. Low confidence => agents re-check manually.
#>
[CmdletBinding()]
param(
  [string]$BaseUrl = $(if ($env:BASE_URL) { $env:BASE_URL } elseif ($env:E2E_BASE_URL) { $env:E2E_BASE_URL } else { "https://study.design-bakery.com" }),
  [string]$RepoRoot = "",
  [string]$UltrafastRoot = $(if ($env:JEV_ULTRAFAST_ROOT) { $env:JEV_ULTRAFAST_ROOT } else { "D:\claude\jev-ultrafast" }),
  [int]$MaxActions = 40
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

if (-not $env:OPENROUTER_API_KEY) {
  throw "OPENROUTER_API_KEY is required for Ultrafast Decisions (typesafe/jev-1.13 via OpenRouter)."
}

if (-not (Test-Path $UltrafastRoot)) {
  Write-Host "Cloning Pukujan/jev-ultrafast -> $UltrafastRoot"
  New-Item -ItemType Directory -Force -Path (Split-Path $UltrafastRoot) | Out-Null
  git clone --depth 1 https://github.com/Pukujan/jev-ultrafast.git $UltrafastRoot
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$art = Join-Path $RepoRoot "artifacts\ux-defect-ultrafast\$stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $art "screenshots") | Out-Null

$scoutPy = Join-Path $RepoRoot "tools\ux-defect\run_ultrafast_scout.py"
if (-not (Test-Path $scoutPy)) { throw "Missing $scoutPy" }

Write-Host "Ultrafast UX defect scout"
Write-Host "  BASE_URL        = $BaseUrl"
Write-Host "  JEV_ULTRAFAST   = $UltrafastRoot"
Write-Host "  ART_DIR         = $art"
Write-Host "  MAX_ACTIONS     = $MaxActions"

$env:BASE_URL = $BaseUrl
$env:ART_DIR = $art
$env:JEV_ULTRAFAST_ROOT = $UltrafastRoot
$env:MAX_ACTIONS = "$MaxActions"
$env:RUN_ID = "jev-$stamp"

Push-Location $UltrafastRoot
try {
  if (Get-Command uv -ErrorAction SilentlyContinue) {
    if (-not (Test-Path (Join-Path $UltrafastRoot ".venv"))) {
      uv sync | Out-Host
    }
    uv run python $scoutPy
  } else {
    $py = Join-Path $UltrafastRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) {
      throw "uv not found and $py missing. Install uv or create the jev-ultrafast venv."
    }
    & $py $scoutPy
  }
  $code = $LASTEXITCODE
} finally {
  Pop-Location
}

Write-Host "Done. summary.json => $(Join-Path $art 'summary.json')"
if ($code -ne 0) { exit $code }
