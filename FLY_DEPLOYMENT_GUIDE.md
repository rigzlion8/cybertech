# Fly.io Deployment Guide

This guide provides specific instructions for deploying the CyberTech Security Scanner to Fly.io.

## Prerequisites

- Fly.io account and CLI installed
- Git repository of your project

## Deployment Steps

### 1. Install Fly.io CLI

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Or use package manager
# macOS: brew install flyctl
# Windows: winget install flyctl
```

### 2. Login to Fly.io

```bash
flyctl auth login
```

### 3. Deploy the Application

```bash
# From your project directory
flyctl deploy

# Or if you need to create a new app first
flyctl launch
```

### 4. Set Environment Variables

```bash
# Set required environment variables
flyctl secrets set FLASK_ENV=production
flyctl secrets set FLASK_DEBUG=False
flyctl secrets set SECRET_KEY=your-secure-secret-key-here

# Optional: Set email configuration if using report delivery
flyctl secrets set SMTP_SERVER=smtp.gmail.com
flyctl secrets set SMTP_PORT=587
flyctl secrets set SMTP_USERNAME=your-email@gmail.com
flyctl secrets set SMTP_PASSWORD=your-app-password
```

### 5. Scale the Application (Optional)

```bash
# Scale to multiple instances for better performance
flyctl scale count 2

# Scale memory if needed
flyctl scale memory 2048
```

## Configuration Details

### fly.toml

The `fly.toml` file is already configured with:

- **App Name**: `cybertech-security-scanner`
- **Primary Region**: `iad` (Virginia, USA)
- **Memory**: 1024MB
- **CPU**: 1 shared core
- **Port**: 8080 (internal), 80/443 (external)
- **HTTPS**: Enabled with automatic SSL
- **Health Checks**: Configured for `/api/health`

### Environment Variables

Required for production:
- `FLASK_ENV=production`
- `FLASK_DEBUG=False`
- `SECRET_KEY` (secure random string)

Optional for email functionality:
- SMTP configuration variables

## Performance Optimization

### 1. Enable Auto-Scaling

```bash
# Enable auto-scaling based on requests
flyctl autoscale set min=1 max=3
```

### 2. Configure Persistent Storage

For scan reports and logs:

```bash
# Create a volume for persistent storage
flyctl volumes create scan_data --size 10 --region iad

# Mount the volume in your app
# Add to fly.toml:
# [[mounts]]
#   source = "scan_data"
#   destination = "/data"
```

### 3. Set Resource Limits

```bash
# Increase memory if needed
flyctl scale memory 2048

# Add more CPU if needed
flyctl scale vm shared-cpu-2x
```

## Monitoring and Logs

### View Application Logs

```bash
flyctl logs
```

### Monitor Application Metrics

```bash
flyctl dashboard
```

### Check Application Status

```bash
flyctl status
```

## Troubleshooting

### Common Issues

1. **Port Binding Issues**
   - Ensure app binds to `0.0.0.0` and port `8080`
   - Check `fly.toml` internal_port matches your app

2. **Memory Issues**
   - Increase memory: `flyctl scale memory 2048`
   - Check logs for memory errors

3. **Database Connection Issues**
   - Ensure MongoDB connection string is correct
   - Check if MongoDB service is accessible from Fly.io

### Health Checks

The app includes a health check endpoint at `/api/health` that:
- Returns application status
- Includes timestamp
- Used by Fly.io for monitoring

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to git
   - Use `flyctl secrets set` for sensitive data

2. **Rate Limiting**
   - Built-in rate limiting prevents abuse
   - Configure limits in `app.py`

3. **Input Validation**
   - Blocks localhost and private IP scanning
   - Validates all input targets

## Cost Optimization

1. **Auto-Stop Machines**
   - Configured to stop machines when not in use
   - Saves costs during low traffic periods

2. **Resource Scaling**
   - Start with minimal resources
   - Scale up based on usage

3. **Region Selection**
   - Choose regions close to your users
   - Consider cost differences between regions

## Updates and Maintenance

### Deploy Updates

```bash
# Deploy latest changes
flyctl deploy

# With specific version
flyctl deploy --image your-image:tag
```

### Rollback Deployment

```bash
flyctl deployments list
flyctl deploy --image flyio/your-app:deployment-id
```

### Database Backups

If using MongoDB:
```bash
# Schedule regular backups
flyctl postgres connect
# Run backup commands
```

## Support

For Fly.io specific issues:
- [Fly.io Documentation](https://fly.io/docs/)
- [Fly.io Community](https://community.fly.io/)
- [Fly.io Status](https://status.fly.io/)

For application issues:
- Check application logs: `flyctl logs`
- Review deployment configuration
- Verify environment variables