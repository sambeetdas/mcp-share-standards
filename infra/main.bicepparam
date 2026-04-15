# Fly.io Parameters

This file previously contained Azure Bicep parameters. Fly.io deployments use `fly.toml` instead (see project root).

All deployment configuration is now in:
- `fly.toml` — App settings, region, port, etc.
- `.github/workflows/deploy.yml` — Automated GitHub Actions deployment
