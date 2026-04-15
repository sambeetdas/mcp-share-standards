<#
.SYNOPSIS
    Deploy MCP Enterprise Standards Server to Azure App Service.

.DESCRIPTION
    1. Creates the resource group (if it doesn't exist)
    2. Deploys Bicep (ACR + App Service Plan + Web App)
    3. Builds & pushes the Docker image to ACR
    4. Restarts the Web App to pull the latest image

.PARAMETER ResourceGroupName
    Name of the Azure resource group.

.PARAMETER Location
    Azure region (default: eastus).

.PARAMETER AppName
    Base name for resources (default: mcp-standards).

.PARAMETER ImageTag
    Docker image tag (default: latest).
#>

param(
    [string]$ResourceGroupName = "rg-mcp-standards",
    [string]$Location = "eastus",
    [string]$AppName = "mcp-standards",
    [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"

Write-Host "=== MCP Standards Server - Azure Deployment ===" -ForegroundColor Cyan

# 1. Ensure logged in
Write-Host "`n[1/5] Checking Azure CLI login..." -ForegroundColor Yellow
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in. Running 'az login'..."
    az login
}
Write-Host "Using subscription: $($account.name) ($($account.id))"

# 2. Create resource group
Write-Host "`n[2/5] Creating resource group '$ResourceGroupName'..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location --output none

# 3. Deploy Bicep
Write-Host "`n[3/5] Deploying Bicep template..." -ForegroundColor Yellow
$infraDir = Join-Path $PSScriptRoot "infra"
$deployOutput = az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file (Join-Path $infraDir "main.bicep") `
    --parameters appName=$AppName location=$Location imageTag=$ImageTag `
    --output json | ConvertFrom-Json

$acrLoginServer = $deployOutput.properties.outputs.acrLoginServer.value
$acrName = $deployOutput.properties.outputs.acrName.value
$webAppName = $deployOutput.properties.outputs.webAppName.value
$webAppUrl = $deployOutput.properties.outputs.webAppUrl.value

Write-Host "  ACR:     $acrLoginServer"
Write-Host "  Web App: $webAppName"
Write-Host "  URL:     $webAppUrl"

# 4. Build & push Docker image to ACR
Write-Host "`n[4/5] Building and pushing Docker image to ACR..." -ForegroundColor Yellow
az acr build `
    --registry $acrName `
    --image "mcp-standards-server:$ImageTag" `
    --file (Join-Path $PSScriptRoot "Dockerfile") `
    $PSScriptRoot

# 5. Restart web app to pick up new image
Write-Host "`n[5/5] Restarting web app..." -ForegroundColor Yellow
az webapp restart --name $webAppName --resource-group $ResourceGroupName

Write-Host "`n=== Deployment complete ===" -ForegroundColor Green
Write-Host "MCP SSE endpoint: $webAppUrl/sse" -ForegroundColor Cyan
Write-Host "`nTo connect from VS Code, add this to your MCP settings:"
Write-Host "  Server URL: $webAppUrl/mcp"
