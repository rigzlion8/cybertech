# 🚀 Quick Start Guide

Get CyberTech Security Scanner running in 5 minutes!

## ⚡ Fast Setup

### 1. Prerequisites Check
```bash
python3 --version  # Should be 3.8+
```

### 2. One-Line Setup (Linux/macOS)
```bash
cd /home/rigz/projects/cybertech && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cp .env.example .env
```

### 3. Run the Application
```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python app.py
```

### 4. Open in Browser
```
http://localhost:5000
```

## 🎯 First Scan

1. Enter a target URL (e.g., `https://example.com`)
2. Enter your email address
3. Select "Quick Scan" for a fast test
4. Click "Start Security Scan"
5. Wait for results and check your email for the PDF report

## 📧 Email Setup (Optional)

Edit `.env` file:
```env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Gmail Users**: [Get App Password](https://myaccount.google.com/apppasswords)

## 🔧 Common Commands

**Start Server:**
```bash
python app.py
```

**Test API:**
```bash
curl http://localhost:5000/api/health
```

**Quick Scan via API:**
```bash
curl -X POST http://localhost:5000/api/quick-check \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com"}'
```

**Full Scan via API:**
```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com",
    "email": "your@email.com",
    "scan_type": "full"
  }'
```

## 🐛 Quick Troubleshooting

**Port 5000 already in use?**
```bash
# Use different port
export PORT=5001
python app.py
```

**Import errors?**
```bash
pip install -r requirements.txt
```

**Permission errors?**
```bash
chmod +x run.sh
```

**Email not working?**
- Check `.env` configuration
- Verify SMTP credentials
- Use App Password for Gmail

## 📚 Next Steps

- Read full [README.md](README.md) for detailed documentation
- Check [INSTALL.md](INSTALL.md) for comprehensive installation guide
- Review security best practices
- Configure custom scan options

## ⚖️ Legal Notice

**Only scan systems you own or have permission to test!**

## 🆘 Need Help?

- Check `cybertech.log` for errors
- Review [INSTALL.md](INSTALL.md) troubleshooting section
- Verify all dependencies are installed

---

**Happy Scanning! 🛡️**

