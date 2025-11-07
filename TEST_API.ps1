# Test API Endpoints for Demo Accounts
# Usage: .\TEST_API.ps1

Write-Host "Testing API Endpoints for Demo Accounts" -ForegroundColor Green
Write-Host ""

$baseUrl = "http://localhost:8000/api/v1"
$token = "mock-token-123"

# Demo account UUIDs
$accounts = @{
    "demo_goal_complete@demo.com" = "180bcad6-380e-4a2f-809b-032677fcc721"
    "demo_sat_complete@demo.com" = "0281a3c5-e9aa-4d65-ad33-f49a80a77a23"
    "demo_chemistry@demo.com" = "063009da-20a4-4f53-8f67-f06573f7195e"
    "demo_low_sessions@demo.com" = "e8bf67c3-57e6-405b-a1b5-80ac75aaf034"
    "demo_multi_goal@demo.com" = "c02cb7f8-e63c-4945-9406-320e1d9046f3"
}

Write-Host "Testing Health Endpoint..." -ForegroundColor Cyan
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
    Write-Host "[OK] Health check: $($health.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($health.Content)" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Testing Progress Endpoint for demo_goal_complete..." -ForegroundColor Cyan
$userId = $accounts["demo_goal_complete@demo.com"]
try {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    $progress = Invoke-WebRequest -Uri "$baseUrl/progress/$userId?include_suggestions=true" -Method GET -Headers $headers
    Write-Host "[OK] Progress endpoint: $($progress.StatusCode)" -ForegroundColor Green
    $data = $progress.Content | ConvertFrom-Json
    Write-Host "Goals found: $($data.data.goals.Count)" -ForegroundColor Gray
    Write-Host "Suggestions found: $($data.data.suggestions.Count)" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Progress endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Testing Gamification Endpoint..." -ForegroundColor Cyan
try {
    $gamification = Invoke-WebRequest -Uri "$baseUrl/gamification/users/$userId" -Method GET -Headers $headers
    Write-Host "[OK] Gamification endpoint: $($gamification.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Gamification endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green

