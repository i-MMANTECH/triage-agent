#!/usr/bin/env pwsh
# Triage — Google Cloud bootstrap.
#
# Enables the APIs we depend on, provisions Firestore in Native mode, and
# creates a service account with the IAM roles the deployed services need.
# Safe to re-run — every operation is idempotent.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (`gcloud auth login`)
#   - Billing enabled on the target project
#
# Usage:
#   ./scripts/bootstrap.ps1 -ProjectId my-project-id [-Region us-central1]

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter()]
    [string]$Region = "us-central1",

    [Parameter()]
    [string]$ServiceAccount = "triage-runtime"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Setting active project to $ProjectId" -ForegroundColor Cyan
gcloud config set project $ProjectId | Out-Null

Write-Host "==> Enabling required APIs (this can take a minute)" -ForegroundColor Cyan
$apis = @(
    "run.googleapis.com",
    "aiplatform.googleapis.com",
    "firestore.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
)
gcloud services enable @apis

Write-Host "==> Ensuring Firestore (Native mode) exists in $Region" -ForegroundColor Cyan
$existing = gcloud firestore databases list --format="value(name)" 2>$null
if (-not $existing) {
    gcloud firestore databases create --location=$Region --type=firestore-native
} else {
    Write-Host "    Firestore already provisioned: $existing"
}

Write-Host "==> Ensuring service account '$ServiceAccount' exists" -ForegroundColor Cyan
$saEmail = "$ServiceAccount@$ProjectId.iam.gserviceaccount.com"
$saList = gcloud iam service-accounts list --filter="email:$saEmail" --format="value(email)" 2>$null
if (-not $saList) {
    gcloud iam service-accounts create $ServiceAccount `
        --display-name="Triage runtime"
} else {
    Write-Host "    Service account already exists: $saEmail"
}

Write-Host "==> Granting IAM roles to $saEmail" -ForegroundColor Cyan
$roles = @(
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
)
foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$saEmail" `
        --role="$role" `
        --condition=None `
        --quiet | Out-Null
}

Write-Host "==> Ensuring Artifact Registry repo 'triage' exists in $Region" -ForegroundColor Cyan
$repo = gcloud artifacts repositories list --location=$Region --filter="name:triage" --format="value(name)" 2>$null
if (-not $repo) {
    gcloud artifacts repositories create triage `
        --repository-format=docker `
        --location=$Region `
        --description="Triage container images"
} else {
    Write-Host "    Repository already exists."
}

Write-Host ""
Write-Host "Done. Next:" -ForegroundColor Green
Write-Host "  ./scripts/deploy-server.ps1 -ProjectId $ProjectId -Region $Region"
Write-Host "  ./scripts/deploy-web.ps1    -ProjectId $ProjectId -Region $Region -ApiUrl <server-url>"
