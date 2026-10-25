# Automated PowerShell deployment script for Windows environments
# Usage: .\deploy.ps1 -Environment dev (or prod)

param (
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Starting Deployment: Environment = $Environment" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

if ($Environment -eq "prod" -or $Environment -eq "production") {
    $ComposeFile = "docker-compose.prod.yml"
    $Port = 80
} else {
    $ComposeFile = "docker-compose.dev.yml"
    $Port = 8080
}

Write-Host "[1/4] Starting services with $ComposeFile..." -ForegroundColor Yellow
docker compose -f $ComposeFile up -d --build

Write-Host "[2/4] Running database migrations inside web container..." -ForegroundColor Yellow
docker compose -f $ComposeFile exec -T web python manage.py migrate --noinput

Write-Host "[3/4] Collecting static files inside web container..." -ForegroundColor Yellow
docker compose -f $ComposeFile exec -T web python manage.py collectstatic --noinput

Write-Host "[4/4] Verifying health check on /health/..." -ForegroundColor Yellow
$MaxAttempts = 15
$HealthUrl = "http://localhost:$Port/health/"
$Healthy = $false

for ($i = 1; $i -le $MaxAttempts; $i++) {
    Write-Host "  Checking $HealthUrl (Attempt $i of $MaxAttempts)..."
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $Healthy = $true
            break
        }
    } catch {
        # Retry until timeout
    }
    Start-Sleep -Seconds 2
}

if ($Healthy) {
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host " Deployment SUCCESS: Application is healthy (HTTP 200)!" -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=====================================================" -ForegroundColor Red
    Write-Host " Deployment FAILED: Health check timed out without HTTP 200." -ForegroundColor Red
    Write-Host "=====================================================" -ForegroundColor Red
    exit 1
}
