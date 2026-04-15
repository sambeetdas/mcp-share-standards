<#
.SYNOPSIS
    Deploy MCP Standards Server to Fly.io

.DESCRIPTION
    This project is configured for Fly.io deployment using GitHub Actions.
    There's no manual deployment script needed — just push to GitHub and the
    workflow handles everything automatically.

.NOTES
    For manual deployment:
    - Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
    - Login: flyctl auth login
    - Deploy: flyctl deploy
    - Status: flyctl status
    - Logs: flyctl logs
#>

Write-Host "=== MCP Standards Server - Fly.io Deployment ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This project uses GitHub Actions for automated deployment." -ForegroundColor Yellow
Write-Host ""
Write-Host "Setup (one-time):" -ForegroundColor Green
Write-Host "  1. Sign up at https://fly.io (free tier)"
Write-Host "  2. Run: flyctl auth login"
Write-Host "  3. Generate token: flyctl tokens create deploy --read-write-machines"
Write-Host "  4. Add FLY_API_TOKEN to GitHub Secrets"
Write-Host ""
Write-Host "Deploy:" -ForegroundColor Green
Write-Host "  - Automatic: Just push to master branch"
Write-Host "  - Manual: flyctl deploy"
Write-Host ""
Write-Host "View status:" -ForegroundColor Green
Write-Host "  - Logs: flyctl logs"
Write-Host "  - Status: flyctl status"
Write-Host "  - Live URL: https://mcp-standards-server.fly.dev/sse"
