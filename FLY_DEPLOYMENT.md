# 🚀 Deploying CyberTech to Fly.io

## Why Fly.io?

Perfect for this security scanner because:
- ✅ **Generous free tier** - 3 shared-cpu VMs + 160GB bandwidth/month
- ✅ Supports long-running processes (unlike Vercel)
- ✅ Docker-based deployment (full control)
- ✅ Persistent volumes for reports
- ✅ Global edge network
- ✅ No credit card required for free tier

## Prerequisites

1. **Fly.io account** - Sign up at [fly.io](https://fly.io)
2. **flyctl CLI** - Install the Fly.io CLI tool

### Install flyctl

**Linux/WSL:**
```bash
curl -L https://fly.io/install.sh | sh
```

**macOS:**
```bash
brew install flyctl
```

**Windows (PowerShell):**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

## Quick Deploy Steps

### 1. Login to Fly.io
```bash
flyctl auth login
```

### 2. Launch Your App
```bash
# This will create fly.toml if it doesn't exist
flyctl launch --no-deploy
```

**During launch, you'll be prompted:**
- Choose app name: `cybertech-security-scanner` (or your preference)
- Choose region: Pick one closest to you (e.g., `iad` for US East)
- Would you like to set up a Postgresql database? **No**
- Would you like to set up an Upstash Redis database? **No**
- Would you like to deploy now? **No** (we'll set secrets first)

### 3. Set Environment Variables (Secrets)

```bash
# Required secrets
flyctl secrets set SECRET_KEY=$(openssl rand -hex 32)
flyctl secrets set FLASK_ENV=production
flyctl secrets set FLASK_DEBUG=False

# Email configuration
flyctl secrets set SMTP_SERVER=smtp.gmail.com
flyctl secrets set SMTP_PORT=587
flyctl secrets set SMTP_USERNAME=your-email@gmail.com
flyctl secrets set SMTP_PASSWORD=your-app-password
flyctl secrets set SMTP_FROM_EMAIL=your-email@gmail.com

# Optional
flyctl secrets set HAVEIBEENPWNED_API_KEY=your-api-key
flyctl secrets set REQUEST_TIMEOUT=30
flyctl secrets set MAX_SCAN_THREADS=5
```

### 4. (Optional) Create Persistent Volume for Reports

```bash
# Create a 1GB volume for storing reports
flyctl volumes create cybertech_reports --region iad --size 1

# Add to fly.toml
cat >> fly.toml << 'EOF'

[mounts]
  source = "cybertech_reports"
  destination = "/app/reports"
EOF
```

### 5. Deploy!

```bash
flyctl deploy
```

### 6. Open Your App

```bash
flyctl open
```

Your app will be live at: `https://cybertech-security-scanner.fly.dev`

## Configuration Files Explained

### `Dockerfile`
- Uses Python 3.11 slim image
- Installs nmap system package
- Sets up Gunicorn with 4 workers
- 300s timeout for long-running scans

### `fly.toml`
- Configures app name and region
- Sets up HTTP/HTTPS handling
- Auto-start/stop for cost savings
- Health checks on `/api/health`
- Memory: 512MB (upgradeable)

### `.dockerignore`
- Excludes unnecessary files from Docker image
- Keeps image size small
- Protects sensitive files

## Post-Deployment

### View Logs
```bash
flyctl logs
```

### Check Status
```bash
flyctl status
```

### View App Info
```bash
flyctl info
```

### Scale Up/Down
```bash
# Increase memory
flyctl scale memory 1024

# Add more VMs
flyctl scale count 2

# View current scaling
flyctl scale show
```

### SSH into Your App
```bash
flyctl ssh console
```

## Testing Your Deployment

### Health Check
```bash
curl https://cybertech-security-scanner.fly.dev/api/health
```

### Quick Security Scan
```bash
curl -X POST https://cybertech-security-scanner.fly.dev/api/quick-check \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com"
  }'
```

### Full Scan
```bash
curl -X POST https://cybertech-security-scanner.fly.dev/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com",
    "email": "your-email@example.com",
    "scan_type": "full",
    "options": {
      "port_scan": true,
      "vulnerability_scan": true,
      "ssl_check": true,
      "headers_check": true
    }
  }'
```

## Fly.io Free Tier Limits

- **3 shared-cpu-1x VMs** with 256MB RAM each
- **160GB** outbound data transfer
- **3GB** persistent volume storage
- **Up to 10 apps**

### Staying Within Free Tier

1. **Auto-stop/start** (already configured)
   ```toml
   auto_stop_machines = true
   auto_start_machines = true
   min_machines_running = 0
   ```

2. **Monitor usage**
   ```bash
   flyctl status
   flyctl scale show
   ```

3. **Optimize image size**
   - Already using `slim` Python image
   - `.dockerignore` excludes unnecessary files

## Custom Domain (Optional)

### Add Your Domain
```bash
flyctl certs create yourdomain.com
flyctl certs show yourdomain.com
```

### Update DNS
Add the following records to your DNS provider:
```
A     @    <fly-ipv4-address>
AAAA  @    <fly-ipv6-address>
```

## Persistent Storage for Reports

By default, filesystem is ephemeral. For persistent reports:

### Option 1: Fly.io Volumes (Recommended for small scale)
```bash
flyctl volumes create cybertech_reports --size 1
```

Add to `fly.toml`:
```toml
[mounts]
  source = "cybertech_reports"
  destination = "/app/reports"
```

### Option 2: Cloud Storage (Recommended for production)
Use S3, GCS, or Cloudflare R2 for scalable storage:

```bash
# Install boto3 for S3
pip install boto3

# Add to requirements.txt
echo "boto3==1.34.0" >> requirements.txt
```

Update `modules/report_generator.py` to save to S3.

## Security Best Practices

### 1. Keep Secrets Secure
```bash
# Never commit secrets to git
# Use flyctl secrets for sensitive data
flyctl secrets list
```

### 2. Enable Rate Limiting
Add to `requirements.txt`:
```
Flask-Limiter==3.5.0
```

Add to `app.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/scan', methods=['POST'])
@limiter.limit("5 per hour")
def perform_scan():
    # existing code
```

### 3. HTTPS Only (Already Configured)
```toml
force_https = true
```

### 4. Monitor & Alerts
Set up Fly.io monitoring:
```bash
flyctl monitor
```

## Troubleshooting

### Build Fails
```bash
# View build logs
flyctl logs

# Common issues:
# 1. Dockerfile syntax - Check Dockerfile
# 2. Missing dependencies - Update requirements.txt
# 3. Large image size - Check .dockerignore
```

### App Crashes
```bash
# Check logs
flyctl logs

# Check health
flyctl checks list

# Restart app
flyctl apps restart cybertech-security-scanner
```

### Out of Memory
```bash
# Increase memory (may require paid plan)
flyctl scale memory 1024

# Or optimize code to use less memory
```

### Slow Performance
```bash
# Check metrics
flyctl metrics

# Scale up
flyctl scale count 2
flyctl scale memory 1024
```

### Volume Issues
```bash
# List volumes
flyctl volumes list

# Check volume status
flyctl volumes show <volume-id>

# Extend volume
flyctl volumes extend <volume-id> --size 2
```

## Monitoring & Maintenance

### View Metrics
```bash
flyctl metrics
```

### Check Health
```bash
flyctl checks list
```

### Update App
```bash
# Make changes to your code
git add .
git commit -m "Update feature"

# Deploy changes
flyctl deploy
```

### Rollback
```bash
# List releases
flyctl releases

# Rollback to previous version
flyctl releases rollback
```

## Cost Optimization

### Auto-scaling
Already configured in `fly.toml`:
```toml
auto_stop_machines = true
auto_start_machines = true
min_machines_running = 0
```

This means:
- App stops when idle (no requests)
- Starts automatically on new request
- Cold start: ~1-3 seconds
- **Saves costs** by not running 24/7

### Monitor Usage
```bash
flyctl status
flyctl scale show
```

## Upgrading

If you need more resources:

### Launch Plan ($1.94/month)
- 3GB persistent volume
- Better support

### Scale Plan ($29/month)
- More VMs
- More memory
- Priority support

Check pricing: https://fly.io/docs/about/pricing/

## Comparison: Fly.io vs Railway vs Vercel

| Feature | Fly.io | Railway | Vercel |
|---------|--------|---------|--------|
| Free Tier | ✅ Generous | ❌ Limited | ✅ Good |
| Docker Support | ✅ Yes | ✅ Yes | ❌ No |
| Long Scans | ✅ Yes | ✅ Yes | ❌ Timeouts |
| System Packages | ✅ Yes | ✅ Yes | ❌ Limited |
| Persistent Storage | ✅ Volumes | ✅ Volumes | ❌ Ephemeral |
| Best For | Long-running apps | Full-stack apps | Serverless |
| **This Project** | ✅ **Perfect** | ✅ Good (paid) | ❌ Not suitable |

## Support

- Fly.io Docs: https://fly.io/docs
- Fly.io Community: https://community.fly.io
- Status Page: https://status.flyio.net

## Quick Command Reference

```bash
# Deploy
flyctl deploy

# View logs
flyctl logs

# View status
flyctl status

# SSH into app
flyctl ssh console

# Scale
flyctl scale memory 1024
flyctl scale count 2

# Secrets
flyctl secrets list
flyctl secrets set KEY=value

# Volumes
flyctl volumes list
flyctl volumes create name --size 1

# Domain
flyctl certs create yourdomain.com

# Monitoring
flyctl monitor
flyctl metrics

# Restart
flyctl apps restart
```

---

## Ready to Deploy?

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Launch (create app)
flyctl launch --no-deploy

# 4. Set secrets
flyctl secrets set SECRET_KEY=$(openssl rand -hex 32)
flyctl secrets set SMTP_USERNAME=your-email@gmail.com
flyctl secrets set SMTP_PASSWORD=your-app-password

# 5. Deploy!
flyctl deploy

# 6. Open your app
flyctl open
```

🎉 Your CyberTech Security Scanner is now live on Fly.io!

**Free tier benefits:**
- No credit card required
- Auto-sleep when idle
- Wake on request
- 160GB bandwidth/month
- Perfect for this use case!

