# Installation Guide

## System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.8 or higher
- **RAM**: Minimum 2GB, Recommended 4GB
- **Disk Space**: Minimum 500MB
- **Network**: Internet connection required for scanning and API access

## Step-by-Step Installation

### 1. System Preparation

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
# Optional: Install nmap for advanced port scanning
sudo apt-get install -y nmap
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Optional: Install nmap
brew install nmap
```

#### Windows (WSL2)
```bash
# Open Ubuntu on WSL2
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
```

### 2. Download/Clone the Project

```bash
cd /home/rigz/projects/cybertech
# Or if cloning from a repository:
# git clone <repository-url> cybertech
# cd cybertech
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
```

### 4. Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you encounter any errors, try installing dependencies individually:
```bash
pip install flask flask-cors requests beautifulsoup4 dnspython
pip install cryptography validators reportlab Pillow
pip install pymongo psycopg2-binary sqlparse python-dotenv
pip install passlib bcrypt werkzeug jinja2
```

### 6. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your preferred text editor:
```bash
nano .env
# or
vim .env
# or
code .env
```

**Minimum Required Configuration:**
```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-random-secret-key-here
```

**For Email Functionality (Optional but Recommended):**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

### 7. Test Installation

```bash
python app.py
```

You should see output similar to:
```
* Running on http://127.0.0.1:5000
* Running on http://0.0.0.0:5000
```

### 8. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

## Email Configuration Guide

### Gmail Setup

1. **Enable 2-Factor Authentication**
   - Go to https://myaccount.google.com/security
   - Click "2-Step Verification" and enable it

2. **Create App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "CyberTech Scanner"
   - Copy the generated 16-character password

3. **Update .env File**
   ```env
   SMTP_USERNAME=your-gmail@gmail.com
   SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # The app password
   ```

### Other Email Providers

#### Outlook/Hotmail
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
```

#### Yahoo
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```

#### Custom SMTP Server
```env
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USERNAME=your-email@yourdomain.com
SMTP_PASSWORD=your-password
```

## Quick Start Script

For easier startup, you can use the provided run script:

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

## Verification Steps

### 1. Check API Health
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T12:00:00.000000"
}
```

### 2. Test Quick Scan
```bash
curl -X POST http://localhost:5000/api/quick-check \
  -H "Content-Type: application/json" \
  -d '{"target": "https://google.com"}'
```

### 3. Access Web Interface
Open browser to `http://localhost:5000` and verify the page loads.

## Troubleshooting Installation

### Python Version Issues
```bash
python3 --version  # Should be 3.8 or higher
```

If you have multiple Python versions:
```bash
python3.9 -m venv venv  # Replace 3.9 with your version
```

### Permission Errors

**Linux/macOS:**
```bash
sudo chown -R $USER:$USER /home/rigz/projects/cybertech
```

### Port Already in Use

If port 5000 is already in use, edit `app.py`:
```python
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))  # Change to 5001 or another port
    app.run(host='0.0.0.0', port=port, debug=True)
```

Or set environment variable:
```bash
export PORT=5001
python app.py
```

### Missing Dependencies

If a specific module is missing:
```bash
pip install <module-name>
```

### SSL Certificate Errors

If you encounter SSL errors during installation:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Virtual Environment Issues

If virtual environment is not activating:
```bash
deactivate  # If already in a venv
rm -rf venv
python3 -m venv venv --clear
source venv/bin/activate
pip install -r requirements.txt
```

## Uninstallation

To completely remove CyberTech:

```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -rf cybertech
```

## Next Steps

After successful installation:

1. Read the [README.md](README.md) for usage instructions
2. Configure your email settings in `.env`
3. Review the legal and ethical use guidelines
4. Run your first security scan
5. Check the generated reports in the `reports/` directory

## Support

If you encounter issues during installation:

1. Check the error messages carefully
2. Review the troubleshooting section above
3. Check application logs: `cybertech.log`
4. Ensure all system requirements are met
5. Try running with elevated privileges (use with caution):
   ```bash
   sudo python app.py
   ```

## Security Notes

- Never share your `.env` file
- Use strong, unique secret keys
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Review firewall rules before exposing to network
- Use HTTPS in production environments

---

**Installation complete! 🎉**

You're now ready to start scanning for security vulnerabilities.

