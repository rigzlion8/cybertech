# 🛡️ CyberTech Security Scanner

A comprehensive cybersecurity application for detecting data leaks, performing penetration tests, and analyzing security vulnerabilities in web applications and infrastructure.

## 🌟 Features

- **🔍 Vulnerability Scanning**
  - SQL Injection detection
  - Cross-Site Scripting (XSS) testing
  - CSRF protection analysis
  - Directory traversal detection
  - Information disclosure checks

- **🔐 SSL/TLS Security Analysis**
  - Certificate validity verification
  - Protocol version checking
  - Cipher suite analysis
  - Expiration monitoring

- **🌐 Port Scanning**
  - Common port identification
  - Service detection
  - Risk assessment for exposed ports

- **🔑 Password Security**
  - Breach detection using HaveIBeenPwned API
  - Password policy analysis
  - Autocomplete configuration checks

- **📊 HTTP Security Headers**
  - Missing security headers detection
  - Cookie security analysis
  - Information disclosure prevention

- **💾 Database Security**
  - Error exposure detection
  - NoSQL injection testing
  - Connection string leak detection

- **📧 Automated Reporting**
  - Professional PDF reports
  - Email delivery
  - Comprehensive security scores
  - Actionable recommendations

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Optional: nmap (for advanced port scanning)

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd /home/rigz/projects/cybertech
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your configuration:
   ```env
   # Email Configuration (for report delivery)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM_EMAIL=your-email@gmail.com
   
   # Application Configuration
   FLASK_ENV=development
   FLASK_DEBUG=True
   SECRET_KEY=your-secret-key-here
   
   # Optional: HaveIBeenPwned API Key
   HAVEIBEENPWNED_API_KEY=your-api-key
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and navigate to: `http://localhost:5000`

## 📖 Usage

### Web Interface

1. Navigate to `http://localhost:5000`
2. Enter the target URL or IP address
3. Provide your email address for report delivery
4. Select scan type:
   - **Full Scan**: Comprehensive security assessment
   - **Quick Scan**: Fast SSL and headers check
   - **Custom Scan**: Choose specific tests
5. Click "Start Security Scan"
6. Review results and download the PDF report

### API Usage

#### Perform a Security Scan

```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com",
    "email": "user@example.com",
    "scan_type": "full",
    "options": {
      "port_scan": true,
      "vulnerability_scan": true,
      "ssl_check": true,
      "headers_check": true,
      "password_check": true,
      "database_check": false
    }
  }'
```

#### Quick Security Check

```bash
curl -X POST http://localhost:5000/api/quick-check \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com"
  }'
```

#### Download Report

```bash
curl -O http://localhost:5000/api/report/{scan_id}
```

#### Health Check

```bash
curl http://localhost:5000/api/health
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve web interface |
| `/api/scan` | POST | Perform comprehensive security scan |
| `/api/quick-check` | POST | Perform quick security check |
| `/api/report/<scan_id>` | GET | Download PDF report |
| `/api/health` | GET | Health check endpoint |

## 🏗️ Project Structure

```
cybertech/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # Documentation
├── modules/                   # Core security modules
│   ├── __init__.py
│   ├── scanner.py            # Main scanner orchestrator
│   ├── port_scanner.py       # Port scanning module
│   ├── vulnerability_scanner.py  # Vulnerability testing
│   ├── ssl_checker.py        # SSL/TLS analysis
│   ├── header_analyzer.py    # HTTP headers analysis
│   ├── password_checker.py   # Password security
│   ├── database_checker.py   # Database security
│   ├── report_generator.py   # PDF report generation
│   └── email_sender.py       # Email delivery
├── static/                    # Frontend files
│   ├── index.html            # Main HTML page
│   ├── styles.css            # Styling
│   └── app.js                # Frontend JavaScript
└── reports/                   # Generated reports (auto-created)
```

## 🔧 Configuration

### Email Setup (Gmail Example)

1. Enable 2-Factor Authentication in your Google account
2. Generate an App Password:
   - Go to Google Account Settings → Security
   - Select "2-Step Verification"
   - Select "App passwords"
   - Generate a new app password
3. Use the generated password in your `.env` file

### Security Considerations

- Never commit `.env` file to version control
- Use strong secret keys in production
- Implement rate limiting for API endpoints
- Run scans only on systems you own or have permission to test
- Consider firewall rules for production deployment

## ⚖️ Legal & Ethical Use

**IMPORTANT**: This tool is intended for:
- Security testing on systems you own
- Authorized penetration testing engagements
- Educational purposes
- Security research with proper authorization

**DO NOT USE** this tool to:
- Test systems without explicit permission
- Perform unauthorized security assessments
- Attack or exploit vulnerabilities maliciously

Unauthorized security testing may be illegal in your jurisdiction. Always obtain proper authorization before scanning any systems.

## 🔒 Security Ratings

The application provides security scores on a scale of 0-100:

- **80-100**: Low Risk ✅
- **60-79**: Medium Risk ⚠️
- **40-59**: High Risk ⚠️
- **0-39**: Critical Risk ❌

## 🛠️ Advanced Configuration

### Custom Port Ranges

Edit `modules/port_scanner.py` to modify the `COMMON_PORTS` dictionary.

### Scan Timeouts

Adjust timeout values in individual modules or set global timeout in `.env`:

```env
REQUEST_TIMEOUT=30
MAX_SCAN_THREADS=5
```

### Custom Vulnerability Payloads

Modify payload lists in `modules/vulnerability_scanner.py` for specific testing needs.

## 📝 Report Features

Generated PDF reports include:

- Executive summary
- Security score and risk level
- Detailed findings by category
- Port scan results
- Vulnerability assessments
- SSL/TLS configuration
- Missing security headers
- Password security issues
- Database security findings
- Prioritized recommendations

## 🐛 Troubleshooting

### Port Scanning Issues

If port scanning fails:
```bash
# Install nmap (optional but recommended)
sudo apt-get install nmap  # Ubuntu/Debian
brew install nmap          # macOS
```

### SSL Certificate Errors

If SSL checks fail with certificate errors:
- Ensure the target uses HTTPS
- Check if the certificate is valid
- Verify system time is correct

### Email Sending Issues

If emails fail to send:
- Verify SMTP credentials in `.env`
- Check firewall rules for port 587
- Enable "Less secure app access" (Gmail) or use App Password
- Check application logs: `cybertech.log`

### Permission Denied Errors

Some scans may require elevated privileges:
```bash
sudo python app.py  # Use with caution
```

## 🚀 Deployment

### Production Deployment

1. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Use a reverse proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Enable HTTPS**
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

4. **Set production environment variables**
   ```env
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is provided for educational and authorized security testing purposes only.

## 🙏 Acknowledgments

- HaveIBeenPwned API for password breach checking
- OWASP for security testing guidelines
- ReportLab for PDF generation
- Flask framework and community

## 📞 Support

For issues, questions, or contributions:
- Check the troubleshooting section
- Review application logs: `cybertech.log`
- Open an issue on GitHub

## 🔄 Version History

### Version 1.0.0 (2025-01-10)
- Initial release
- Full vulnerability scanning suite
- PDF report generation
- Email delivery
- Modern web interface
- RESTful API

## 🎯 Roadmap

Future enhancements:
- [ ] Multi-threaded scanning
- [ ] Scheduled scans
- [ ] Historical scan comparison
- [ ] Custom vulnerability signatures
- [ ] API key authentication
- [ ] Webhook notifications
- [ ] Docker containerization
- [ ] Cloud deployment templates

---

**Made with ❤️ for security professionals and developers**

