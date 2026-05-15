#!/usr/bin/env pwsh
# Triage — deploy the Next.js dashboard to Cloud Run.
#
# Usage:
#   ./scripts/deploy-web.ps1 -ProjectId my-project-id -ApiUrl https://triage-server-xxx.run.app

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [string]$ApiUrl,

    [Parameter()]
    [string]$Region = "us-central1",

    [Parameter()]
    [string]$ServiceName = "triage-web"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$webDir = Join-Path $repoRoot "web"

$envVars = @(
    "NEXT_PUBLIC_API_URL=$ApiUrl"
)

Write-Host "==> Deploying $ServiceName to Cloud Run in $Region" -ForegroundColor Cyan
gcloud run deploy $ServiceName `
    --source $webDir `
    --region $Region `
    --project $ProjectId `
    --platform managed `
    --allow-unauthenticated `
    --port 3000 `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 3 `
    --set-env-vars ($envVars -join ",")

$url = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"
Write-Host ""
Write-Host "Deployed: $url" -ForegroundColor Green
Write-Host ""
Write-Host "Important: re-run deploy-server.ps1 with -WebOrigin $url so CORS allows the dashboard origin."
