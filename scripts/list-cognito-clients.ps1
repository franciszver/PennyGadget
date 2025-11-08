# List Cognito Clients for a User Pool
param(
    [Parameter(Mandatory=$true)]
    [string]$UserPoolId,
    [string]$Region = "us-east-1",
    [string]$Profile = ""
)

$ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }

Write-Host "Listing clients for User Pool: $UserPoolId" -ForegroundColor Cyan
Write-Host ""

$ListClientsCommand = "aws cognito-idp list-user-pool-clients --user-pool-id '$UserPoolId' --region $Region --output json"
if ($ProfileArg) {
    $ListClientsCommand += " $ProfileArg"
}

try {
    $Clients = Invoke-Expression $ListClientsCommand | ConvertFrom-Json
    
    if ($Clients.UserPoolClients.Count -eq 0) {
        Write-Host "No clients found for this User Pool." -ForegroundColor Yellow
    } else {
        Write-Host "Found $($Clients.UserPoolClients.Count) client(s):" -ForegroundColor Green
        Write-Host ""
        foreach ($Client in $Clients.UserPoolClients) {
            Write-Host "  Client Name: $($Client.ClientName)" -ForegroundColor White
            Write-Host "  Client ID: $($Client.ClientId)" -ForegroundColor Cyan
            Write-Host "  Auth Flows: $($Client.ExplicitAuthFlows -join ', ')" -ForegroundColor Gray
            Write-Host ""
        }
    }
} catch {
    Write-Host "ERROR: Failed to list clients: $_" -ForegroundColor Red
    exit 1
}

