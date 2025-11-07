# Stop AI Study Companion API Server
# Usage: .\STOP_SERVER.ps1

Write-Host "Stopping AI Study Companion API Server..." -ForegroundColor Yellow
Write-Host ""

# Method 1: Kill processes on port 8000
Write-Host "Finding processes on port 8000..." -ForegroundColor Cyan
$processes = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    foreach ($processId in $processes) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Stopping process: $($proc.ProcessName) (PID: $processId)" -ForegroundColor Yellow
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "[OK] Stopped all processes on port 8000" -ForegroundColor Green
} else {
    Write-Host "[INFO] No processes found on port 8000" -ForegroundColor Cyan
}

# Method 2: Kill all uvicorn processes
Write-Host ""
Write-Host "Finding uvicorn processes..." -ForegroundColor Cyan
$uvicornProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or $_.MainWindowTitle -like "*uvicorn*"
}

if ($uvicornProcs) {
    foreach ($proc in $uvicornProcs) {
        Write-Host "Stopping uvicorn process: PID $($proc.Id)" -ForegroundColor Yellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Stopped all uvicorn processes" -ForegroundColor Green
} else {
    Write-Host "[INFO] No uvicorn processes found" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green

