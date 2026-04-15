# Fly.io Deployment

This directory previously contained Bicep (Azure IaC) templates. Fly.io deployments use a different approach:

## Deployment Files

- **`fly.toml`** (project root) — Fly.io configuration (app name, region, build, port, etc.)
- **`.github/workflows/deploy.yml`** — GitHub Actions workflow for automatic deployment on push

## How It Works

1. **Push to GitHub** — Commit changes and push to `master`
2. **GitHub Actions triggers** — The workflow in `.github/workflows/deploy.yml` runs
3. **Fly CLI deploys** — Builds the Docker image and deploys to Fly.io
4. **Server is live** — Available at `https://mcp-standards-server.fly.dev/sse`

## Setup (One-time)

### 1. Create Fly.io Account
Sign up at https://fly.io (free tier available)

### 2. Generate Fly API Token
```bash
flyctl auth login
flyctl tokens create deploy --read-write-machines
```

### 3. Add to GitHub Secrets
1. Go to your repo Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `FLY_API_TOKEN`
4. Value: Paste the token from step 2

### 4. Update App Name (Optional)
Edit `fly.toml` and change:
```toml
app = "mcp-standards-server"
```

## Deployment

Once setup is complete, deployments happen automatically on every push to `master`.

## Manual Deployment

To deploy manually:

```bash
flyctl deploy
```

## Logs

View deployment logs:
```bash
flyctl logs
```

View app status:
```bash
flyctl status
```

## No Infrastructure-as-Code Needed

Fly.io handles infrastructure provisioning automatically. You only need:
- `fly.toml` — App configuration
- `Dockerfile` — Container definition
- GitHub Actions workflow — CI/CD automation
output webAppHostName string = webApp.properties.defaultHostName
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
