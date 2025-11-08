# AWS Deployment - Step 5.5: Create CloudFront Distribution for API
# This creates a CloudFront distribution that proxies API requests to the ALB
# Provides HTTPS without needing a custom domain

$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

$ALB_DNS = $vars.ALB_DNS
$REGION = $vars.REGION
$PROJECT_NAME = $vars.PROJECT_NAME

Write-Host "Step 5.5: Creating CloudFront distribution for API..." -ForegroundColor Cyan
Write-Host "ALB DNS: $ALB_DNS" -ForegroundColor Yellow

# Create CloudFront distribution configuration JSON
$CF_CONFIG_JSON = @{
    CallerReference = "$PROJECT_NAME-api-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Comment = "CloudFront distribution for ElevareAI API"
    DefaultCacheBehavior = @{
        TargetOriginId = "$PROJECT_NAME-api-origin"
        ViewerProtocolPolicy = "redirect-to-https"
        AllowedMethods = @{
            Quantity = 7
            Items = @("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT")
            CachedMethods = @{
                Quantity = 2
                Items = @("GET", "HEAD")
            }
        }
        ForwardedValues = @{
            QueryString = $true
            Cookies = @{
                Forward = "none"
            }
            Headers = @{
                Quantity = 1
                Items = @("*")
            }
        }
        MinTTL = 0
        DefaultTTL = 0
        MaxTTL = 0
        Compress = $false
    }
    Origins = @{
        Quantity = 1
        Items = @(
            @{
                Id = "$PROJECT_NAME-api-origin"
                DomainName = $ALB_DNS
                CustomOriginConfig = @{
                    HTTPPort = 80
                    HTTPSPort = 443
                    OriginProtocolPolicy = "http-only"
                    OriginSslProtocols = @{
                        Quantity = 1
                        Items = @("TLSv1.2")
                    }
                }
            }
        )
    }
    Enabled = $true
    PriceClass = "PriceClass_100"
} | ConvertTo-Json -Depth 10

# Write JSON without BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("$PWD\cf-api-config.json", $CF_CONFIG_JSON, $utf8NoBom)

Write-Host "Creating CloudFront distribution..." -ForegroundColor Yellow
$CF_DIST_RESULT = aws cloudfront create-distribution --distribution-config file://cf-api-config.json --region $REGION 2>&1

if ($LASTEXITCODE -eq 0) {
    $CF_API_DIST_ID = ($CF_DIST_RESULT | ConvertFrom-Json).Distribution.Id
    $CF_API_DOMAIN = ($CF_DIST_RESULT | ConvertFrom-Json).Distribution.DomainName
    Write-Host "✅ CloudFront API distribution created!" -ForegroundColor Green
    Write-Host "Distribution ID: $CF_API_DIST_ID" -ForegroundColor Green
    Write-Host "Domain: $CF_API_DOMAIN" -ForegroundColor Green
    
    # Save to vars file
    $vars | Add-Member -NotePropertyName "CF_API_DIST_ID" -NotePropertyValue $CF_API_DIST_ID -Force
    $vars | Add-Member -NotePropertyName "CF_API_DOMAIN" -NotePropertyValue $CF_API_DOMAIN -Force
    $vars | ConvertTo-Json | Out-File -FilePath "aws-deployment-vars.json" -Encoding UTF8
    
    Write-Host "`n⚠️ CloudFront distribution is deploying. This takes 10-15 minutes." -ForegroundColor Yellow
    Write-Host "API HTTPS URL will be: https://$CF_API_DOMAIN" -ForegroundColor Cyan
} else {
    Write-Host "Error creating CloudFront distribution: $CF_DIST_RESULT" -ForegroundColor Red
    exit 1
}

Remove-Item cf-api-config.json -ErrorAction SilentlyContinue

