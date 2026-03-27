param(
    [Parameter(Mandatory = $true)]
    [string]$BackendUrl,

    [Parameter(Mandatory = $true)]
    [string]$FrontendUrl,

    [int]$TimeoutSec = 30
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor Cyan
}

function Write-Pass {
    param([string]$Message)
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Normalize-Url {
    param([string]$Url)
    return $Url.TrimEnd('/')
}

$backend = Normalize-Url $BackendUrl
$frontend = Normalize-Url $FrontendUrl

Write-Step "Checking backend health endpoint"
$healthUrl = "$backend/health"
$healthResponse = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec $TimeoutSec
if (-not $healthResponse.status -or $healthResponse.status -ne "ok") {
    Write-Fail "Backend health check failed: unexpected payload from $healthUrl"
    exit 1
}
Write-Pass "Backend health check passed: $healthUrl"

Write-Step "Checking backend chat endpoint"
$chatUrl = "$backend/chat"
$chatPayload = @{
    message = "Hello. Reply with one short insurance tip."
    language = "English"
    include_audio = $false
} | ConvertTo-Json

$chatResponse = Invoke-RestMethod -Method Post -Uri $chatUrl -ContentType "application/json" -Body $chatPayload -TimeoutSec $TimeoutSec
if (-not $chatResponse.response) {
    Write-Fail "Backend chat check failed: empty response from $chatUrl"
    exit 1
}
Write-Pass "Backend chat check passed: received non-empty response"

Write-Step "Checking frontend root URL"
$frontendResponse = Invoke-WebRequest -Method Get -Uri $frontend -TimeoutSec $TimeoutSec
if ($frontendResponse.StatusCode -ne 200) {
    Write-Fail "Frontend check failed: $frontend returned status $($frontendResponse.StatusCode)"
    exit 1
}
Write-Pass "Frontend check passed: $frontend returned HTTP 200"

Write-Step "Checking frontend build references backend URL manually"
Write-Host "Open $frontend and send a chat message. If chat works without CORS/network errors, integration is healthy." -ForegroundColor Yellow

Write-Host ""
Write-Pass "Smoke tests completed successfully"
Write-Host "Backend:  $backend" -ForegroundColor Gray
Write-Host "Frontend: $frontend" -ForegroundColor Gray
