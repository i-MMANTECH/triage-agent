#!/usr/bin/env pwsh
# Triage — deploy the FastAPI backend to Cloud Run.
#
# Uses `gcloud run deploy --source` so the container is built remotely by
# Cloud Build (no local Docker required). The service runs as the
# `triage-runtime` service account created by bootstrap.ps1.
#
# Usage:
#   ./scripts/deploy-server.ps1 -ProjectId my-project-id [-Region us-central1]

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter()]
    [string]$Region = "us-central1",

    [Parameter()]
    [string]$ServiceName = "triage-server",

    [Parameter()]
    [string]$ServiceAccount = "triage-runtime",

    [Parameter()]
    [string]$GeminiModel = "gemini-3.0-pro",

    [Parameter()]
    [switch]$MockMode = $true,

    [Parameter()]
    [string]$DynatraceTenantUrl = "",

    [Parameter()]
    [string]$DynatraceApiToken = "",

    [Parameter()]
    [string]$WebOrigin = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$serverDir = Join-Path $repoRoot "server"

$saEmail = "$ServiceAccount@$ProjectId.iam.gserviceaccount.com"

$envVars = @(
    "GOOGLE_CLOUD_PROJECT=$ProjectId",
    "GOOGLE_CLOUD_LOCATION=$Region",
    "GEMINI_MODEL=$GeminiModel",
    "TRIAGE_MOCK_MODE=$($MockMode.ToString().ToLower())"
)
if ($WebOrigin) { $envVars += "WEB_ORIGIN=$WebOrigin" }
if ($DynatraceTenantUrl) { $envVars += "DYNATRACE_TENANT_URL=$DynatraceTenantUrl" }

$envVarsArg = ($envVars -join ",")

$deployArgs = @(
    "run", "deploy", $ServiceName,
    "--source", $serverDir,
    "--region", $Region,
    "--project", $ProjectId,
    "--service-account", $saEmail,
    "--platform", "managed",
    "--allow-unauthenticated",
    "--port", "8080",
    "--memory", "1Gi",
    "--cpu", "1",
    "--min-instances", "0",
    "--max-instances", "3",
    "--timeout", "300",
    "--set-env-vars", $envVarsArg
)

# Secrets are passed separately so they live in Secret Manager rather than
# plain env-var config.
if ($DynatraceApiToken) {
    Write-Host "==> Storing Dynatrace API token in Secret Manager" -ForegroundColor Cyan
    $existing = gcloud secrets describe triage-dt-token --format="value(name)" 2>$null
    if (-not $existing) {
        $DynatraceApiToken | gcloud secrets create triage-dt-token --data-file=- --replication-policy=automatic
    } else {
        $DynatraceApiToken | gcloud secrets versions add triage-dt-token --data-file=-
    }
    $deployArgs += @("--set-secrets", "DYNATRACE_API_TOKEN=triage-dt-token:latest")
}

Write-Host "==> Deploying $ServiceName to Cloud Run in $Region" -ForegroundColor Cyan
gcloud @deployArgs

$url = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"
Write-Host ""
Write-Host "Deployed: $url" -ForegroundColor Green
Write-Host ""
Write-Host "Next:"
Write-Host "  ./scripts/deploy-web.ps1 -ProjectId $ProjectId -Region $Region -ApiUrl $url"
