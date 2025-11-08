# Add HTTPS Listener to ALB
# This script adds an HTTPS listener to the ALB for secure API access

param(
    [string]$CertificateArn = "",
    [string]$Region = "us-east-1",
    [string]$Profile = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Add HTTPS to ALB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Load deployment variables
if (-not (Test-Path "aws-deployment-vars.json")) {
    Write-Host "ERROR: aws-deployment-vars.json not found!" -ForegroundColor Red
    exit 1
}

$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json
$ALB_ARN = $vars.ALB_ARN
$TG_ARN = $vars.TG_ARN

if (-not $ALB_ARN -or -not $TG_ARN) {
    Write-Host "ERROR: Missing ALB_ARN or TG_ARN in aws-deployment-vars.json!" -ForegroundColor Red
    exit 1
}

$ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }

# Check existing listeners
Write-Host "Checking existing listeners..." -ForegroundColor Green
$ListenersCommand = "aws elbv2 describe-listeners --load-balancer-arn '$ALB_ARN' --region $Region --output json"
if ($ProfileArg) {
    $ListenersCommand += " $ProfileArg"
}

$Listeners = Invoke-Expression $ListenersCommand | ConvertFrom-Json

Write-Host "Current listeners:" -ForegroundColor Cyan
foreach ($Listener in $Listeners.Listeners) {
    Write-Host "  Port $($Listener.Port): $($Listener.Protocol)" -ForegroundColor White
}

# Check if HTTPS already exists
$HasHTTPS = $Listeners.Listeners | Where-Object { $_.Port -eq 443 -and $_.Protocol -eq "HTTPS" }
if ($HasHTTPS) {
    Write-Host ""
    Write-Host "HTTPS listener already exists on port 443!" -ForegroundColor Green
    exit 0
}

Write-Host ""

# If no certificate provided, list available certificates
if (-not $CertificateArn) {
    Write-Host "No certificate ARN provided. Checking for available ACM certificates..." -ForegroundColor Yellow
    
    $ListCertsCommand = "aws acm list-certificates --region $Region --output json"
    if ($ProfileArg) {
        $ListCertsCommand += " $ProfileArg"
    }
    
    try {
        $Certs = Invoke-Expression $ListCertsCommand | ConvertFrom-Json
        
        if ($Certs.CertificateSummaryList.Count -eq 0) {
            Write-Host "  No certificates found." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "To add HTTPS, you need an ACM certificate." -ForegroundColor Yellow
            Write-Host "Options:" -ForegroundColor Yellow
            Write-Host "  1. Request a certificate for your domain:" -ForegroundColor Cyan
            Write-Host "     aws acm request-certificate --domain-name api.yourdomain.com --validation-method DNS --region us-east-1" -ForegroundColor White
            Write-Host ""
            Write-Host "  2. Or use a self-signed certificate (not recommended for production)" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "  3. For testing, you can use the S3 HTTP URL instead of CloudFront HTTPS" -ForegroundColor Yellow
            exit 1
        } else {
            Write-Host "  Available certificates:" -ForegroundColor Cyan
            foreach ($Cert in $Certs.CertificateSummaryList) {
                Write-Host "    - $($Cert.DomainName): $($Cert.CertificateArn)" -ForegroundColor White
            }
            Write-Host ""
            Write-Host "Please provide a certificate ARN:" -ForegroundColor Yellow
            Write-Host "  .\scripts\add-https-to-alb.ps1 -CertificateArn <arn>" -ForegroundColor Cyan
            exit 1
        }
    } catch {
        Write-Host "  Could not list certificates: $_" -ForegroundColor Red
        exit 1
    }
}

# Add HTTPS listener
Write-Host "Adding HTTPS listener (port 443)..." -ForegroundColor Green

$CreateListenerCommand = "aws elbv2 create-listener " +
    "--load-balancer-arn '$ALB_ARN' " +
    "--protocol HTTPS " +
    "--port 443 " +
    "--certificates CertificateArn=$CertificateArn " +
    "--default-actions Type=forward,TargetGroupArn=$TG_ARN " +
    "--region $Region " +
    "--output json"

if ($ProfileArg) {
    $CreateListenerCommand += " $ProfileArg"
}

try {
    $Result = Invoke-Expression $CreateListenerCommand | ConvertFrom-Json
    Write-Host "  [OK] HTTPS listener created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Listener ARN: $($Result.Listeners[0].ListenerArn)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "HTTPS Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Update deploy-frontend.ps1 to use HTTPS API URL" -ForegroundColor Cyan
    Write-Host "  2. Rebuild and deploy the frontend" -ForegroundColor Cyan
    Write-Host "  3. Test the API at: https://$($vars.ALB_DNS)/health" -ForegroundColor Cyan
} catch {
    Write-Host "  [ERROR] Failed to create HTTPS listener: $_" -ForegroundColor Red
    exit 1
}

