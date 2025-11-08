# Fix All Cognito Clients - Enable USER_SRP_AUTH for all PennyGadget/ElevareAI pools
param(
    [string]$Region = "us-east-1",
    [string]$Profile = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix All Cognito Clients" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }

# List all user pools
Write-Host "Finding relevant User Pools..." -ForegroundColor Green
$ListPoolsCommand = "aws cognito-idp list-user-pools --max-results 60 --region $Region --output json"
if ($ProfileArg) {
    $ListPoolsCommand += " $ProfileArg"
}

try {
    $Pools = Invoke-Expression $ListPoolsCommand | ConvertFrom-Json
    
    # Filter for relevant pools (pennygadget, elevareai)
    $RelevantPools = $Pools.UserPools | Where-Object { 
        $_.Name -like "*pennygadget*" -or 
        $_.Name -like "*elevareai*" 
    }
    
    if ($RelevantPools.Count -eq 0) {
        Write-Host "No relevant User Pools found." -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host "Found $($RelevantPools.Count) relevant User Pool(s):" -ForegroundColor Cyan
    foreach ($Pool in $RelevantPools) {
        Write-Host "  - $($Pool.Name): $($Pool.Id)" -ForegroundColor White
    }
    Write-Host ""
    
    # Fix each pool
    foreach ($Pool in $RelevantPools) {
        Write-Host "Processing: $($Pool.Name) ($($Pool.Id))" -ForegroundColor Yellow
        Write-Host "  Listing clients..." -ForegroundColor Gray
        
        $ListClientsCommand = "aws cognito-idp list-user-pool-clients --user-pool-id '$($Pool.Id)' --region $Region --output json"
        if ($ProfileArg) {
            $ListClientsCommand += " $ProfileArg"
        }
        
        try {
            $Clients = Invoke-Expression $ListClientsCommand | ConvertFrom-Json
            
            if ($Clients.UserPoolClients.Count -eq 0) {
                Write-Host "  [SKIP] No clients found" -ForegroundColor Yellow
                continue
            }
            
            foreach ($Client in $Clients.UserPoolClients) {
                Write-Host "  Fixing client: $($Client.ClientName) ($($Client.ClientId))" -ForegroundColor Cyan
                
                # Check if USER_SRP_AUTH is already enabled
                if ($Client.ExplicitAuthFlows -contains "ALLOW_USER_SRP_AUTH") {
                    Write-Host "    [SKIP] USER_SRP_AUTH already enabled" -ForegroundColor Green
                    continue
                }
                
                # Update the client
                $UpdateClientCommand = "aws cognito-idp update-user-pool-client " +
                    "--user-pool-id '$($Pool.Id)' " +
                    "--client-id '$($Client.ClientId)' " +
                    "--explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH " +
                    "--region $Region " +
                    "--output json"
                
                if ($ProfileArg) {
                    $UpdateClientCommand += " $ProfileArg"
                }
                
                try {
                    Invoke-Expression $UpdateClientCommand | Out-Null
                    Write-Host "    [OK] Client updated successfully" -ForegroundColor Green
                } catch {
                    Write-Host "    [ERROR] Failed to update: $_" -ForegroundColor Red
                }
            }
        } catch {
            Write-Host "  [ERROR] Failed to list clients: $_" -ForegroundColor Red
        }
        
        Write-Host ""
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Fix Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    
} catch {
    Write-Host "ERROR: Failed to list user pools: $_" -ForegroundColor Red
    exit 1
}

