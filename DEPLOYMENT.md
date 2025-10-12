# 🚀 Deploying CyberTech to Railway

## Why Railway?

This application is designed for **Railway** deployment because:
- ✅ Supports long-running security scans
- ✅ Allows system dependencies (nmap)
- ✅ Provides persistent file storage for reports
- ✅ Handles Flask apps natively
- ✅ Supports background workers

**Note:** Vercel is NOT recommended as it's designed for serverless functions with strict timeouts and no system package support.

## Quick Deploy to Railway

### Prerequisites
- A Railway account ([railway.app](https://railway.app))
- Railway CLI (optional but recommended)

### Method 1: Deploy via Railway Dashboard (Easiest)

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Create a new project on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**
   
   In Railway dashboard, go to your project → Variables, and add:
   
   ```env
   # Application
   PORT=5000
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=<generate-a-strong-secret-key>
   
   # Email Configuration
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=<your-email@gmail.com>
   SMTP_PASSWORD=<your-app-password>
   SMTP_FROM_EMAIL=<your-email@gmail.com>
   
   # Optional
   HAVEIBEENPWNED_API_KEY=<your-api-key>
   REQUEST_TIMEOUT=30
   MAX_SCAN_THREADS=5
   ```

4. **Deploy**
   - Railway will automatically detect the Python app
   - It will install nmap (via railway.toml)
   - It will start gunicorn server
   - Your app will be live at: `<your-app>.railway.app`

### Method 2: Deploy via Railway CLI

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   # or
   brew install railway
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Initialize Railway project**
   ```bash
   railway init
   ```

4. **Set environment variables**
   ```bash
   railway variables set FLASK_ENV=production
   railway variables set FLASK_DEBUG=False
   railway variables set SECRET_KEY=your-secret-key
   railway variables set SMTP_SERVER=smtp.gmail.com
   railway variables set SMTP_PORT=587
   railway variables set SMTP_USERNAME=your-email@gmail.com
   railway variables set SMTP_PASSWORD=your-app-password
   railway variables set SMTP_FROM_EMAIL=your-email@gmail.com
   ```

5. **Deploy**
   ```bash
   railway up
   ```

6. **Get your deployment URL**
   ```bash
   railway domain
   ```

## Configuration Files Explained

### `Procfile`
Tells Railway how to start your app:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 300
```
- Uses Gunicorn production server
- 4 workers for handling concurrent requests
- 300s timeout for long-running scans

### `railway.toml`
Railway-specific configuration:
```toml
[nixpacks]
aptPkgs = ["nmap"]
```
- Installs nmap system package
- Configures restart policies
- Sets build and deploy commands

### `requirements.txt`
Python dependencies including:
- `gunicorn` - Production WSGI server
- All your app dependencies

## Post-Deployment Steps

### 1. Test the Deployment
```bash
# Health check
curl https://<your-app>.railway.app/api/health

# Test quick scan
curl -X POST https://<your-app>.railway.app/api/quick-check \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com"}'
```

### 2. Set Up Custom Domain (Optional)
In Railway dashboard:
1. Go to Settings → Domains
2. Add your custom domain
3. Configure DNS records as shown

### 3. Monitor Logs
```bash
# Via CLI
railway logs

# Via Dashboard
Go to your project → View Logs
```

### 4. Set Up Persistent Storage (For Reports)

Railway provides ephemeral storage by default. For persistent reports:

**Option A: Use Railway Volumes** (Recommended)
```bash
railway volume create reports
railway volume attach reports /app/reports
```

**Option B: Use External Storage**
- AWS S3
- Google Cloud Storage
- Cloudflare R2

Modify `modules/report_generator.py` to save to cloud storage instead of local filesystem.

## Scaling & Performance

### Increase Workers
Edit `Procfile` or `railway.toml`:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 8 --timeout 600
```

### Add Background Workers
For async scan processing:
```bash
# Install Celery
pip install celery redis

# Add to Procfile
worker: celery -A app.celery worker --loglevel=info
```

### Enable Auto-scaling
In Railway dashboard:
- Go to Settings → Scale
- Configure replica count

## Security Considerations

### 1. Rate Limiting
Add rate limiting to prevent abuse:
```bash
pip install flask-limiter
```

### 2. Authentication
Add API key authentication:
```python
# In app.py
from functools import wraps
from flask import request

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

### 3. HTTPS Only
Railway provides HTTPS by default. Enforce it:
```python
# In app.py
@app.before_request
def force_https():
    if not request.is_secure and os.getenv('FLASK_ENV') == 'production':
        return redirect(request.url.replace('http://', 'https://'), code=301)
```

### 4. CORS Configuration
Update CORS for production:
```python
# In app.py
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

## Troubleshooting

### Build Fails
```bash
# Check logs
railway logs

# Common issues:
# 1. Missing nmap - Check railway.toml aptPkgs
# 2. Wrong Python version - Add runtime.txt with "python-3.11"
# 3. Dependencies conflict - Update requirements.txt
```

### App Crashes on Start
```bash
# Check environment variables
railway variables

# Verify PORT is set correctly
railway variables set PORT=5000
```

### Scans Timeout
```bash
# Increase timeout in Procfile
web: gunicorn app:app --timeout 900

# Or set in railway.toml
[deploy]
healthcheckTimeout = 300
```

### Reports Not Persisting
```bash
# Set up Railway Volume
railway volume create reports
railway volume attach reports /app/reports
```

## Cost Estimation

Railway pricing (as of 2025):
- **Free Trial**: $5 credit (good for testing)
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage

Estimated monthly cost for moderate use:
- Small app: $5-10/month
- Medium traffic: $15-25/month
- High traffic: $30-50/month

## Monitoring & Maintenance

### 1. Set Up Logging
```python
# Enhanced logging for production
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'cybertech.log', 
    maxBytes=10000000, 
    backupCount=5
)
```

### 2. Health Checks
Railway automatically monitors `/api/health` endpoint

### 3. Alerts
Set up Railway notifications:
- Deploy failures
- Crash alerts
- Resource usage alerts

## Alternative: Docker Deployment

If you prefer Docker, Railway also supports:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install nmap
RUN apt-get update && apt-get install -y nmap && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 300
```

Deploy with:
```bash
railway up --dockerfile
```

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: Check application logs

---

**Ready to deploy?**
```bash
git add .
git commit -m "Ready for Railway deployment"
git push
railway up
```

🎉 Your CyberTech Security Scanner will be live in minutes!

