# Payment System Setup Guide

## 🔐 Security Note

Payment credentials are **NOT** stored in Git for security. They are loaded via:
1. Environment variables (local development)
2. `fly secrets` (production deployment)

## 🚀 Local Development Setup

### Option 1: Using the Startup Script (Recommended)

1. **Create your local script** (already done for you):
   ```bash
   cp start_with_payments.sh.template start_with_payments.sh
   ```

2. **Edit `start_with_payments.sh`** with your actual credentials:
   - M-Pesa credentials
   - Paystack keys
   - Resend API key

3. **Start the app**:
   ```bash
   ./start_with_payments.sh
   ```

### Option 2: Using .env File

Your `.env` file already has the credentials loaded. Just run:
```bash
source venv/bin/activate
python app.py
```

## 📱 Testing Payment Systems

Check if payments are configured:
```bash
curl http://localhost:5000/api/payment/test-config
```

Expected response:
```json
{
  "mpesa_configured": true,
  "paystack_configured": true,
  "mpesa_environment": "sandbox"
}
```

## 🚀 Production Deployment

Credentials are already set on Fly.dev via `fly secrets`. No additional setup needed.

```bash
fly deploy
```

## 🛠️ Current Setup

- **M-Pesa**: Sandbox mode, STK Push enabled
- **Paystack**: Live mode, card payments enabled
- **Resend**: Email delivery for reports

## 📋 Files NOT in Git (for security)

- `start_with_payments.sh` - Contains actual credentials
- `env_production.txt` - Backup of production credentials
- `.env` - Local environment variables

These are in `.gitignore` to prevent accidental commits of sensitive data.

