"""
Email Sender Module
Sends security reports via email
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class EmailSender:
    """Email sender for security reports"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', self.smtp_username)
        
    def send_report(self, recipient, report_path, scan_results):
        """Send security report via email"""
        try:
            # Validate configuration
            if not all([self.smtp_username, self.smtp_password]):
                logger.warning("Email configuration not complete. Skipping email send.")
                return {
                    'success': False,
                    'error': 'Email configuration incomplete. Please set SMTP credentials in .env file.'
                }
            
            # Create message
            message = self._create_message(recipient, scan_results)
            
            # Attach PDF report
            if os.path.exists(report_path):
                with open(report_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=f'security_report_{scan_results.get("scan_id", "unknown")}.pdf'
                    )
                    message.attach(pdf_attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Security report sent to {recipient}")
            
            return {
                'success': True,
                'message': f'Report sent to {recipient}'
            }
            
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_message(self, recipient, scan_results):
        """Create email message"""
        message = MIMEMultipart()
        message['From'] = self.from_email
        message['To'] = recipient
        message['Subject'] = f"CyberTech Security Report - {scan_results.get('target', 'Unknown Target')}"
        
        # Create HTML body
        body = self._create_email_body(scan_results)
        
        # Attach HTML body
        html_part = MIMEText(body, 'html')
        message.attach(html_part)
        
        return message
    
    def _create_email_body(self, scan_results):
        """Create HTML email body"""
        target = scan_results.get('target', 'Unknown')
        security_score = scan_results.get('security_score', 0)
        risk_level = scan_results.get('risk_level', 'UNKNOWN')
        scan_id = scan_results.get('scan_id', 'unknown')
        
        # Determine risk color
        risk_colors = {
            'LOW': '#27ae60',
            'MEDIUM': '#f39c12',
            'HIGH': '#e67e22',
            'CRITICAL': '#c0392b'
        }
        risk_color = risk_colors.get(risk_level, '#95a5a6')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 0 0 5px 5px;
                }}
                .score-box {{
                    background-color: white;
                    padding: 15px;
                    margin: 15px 0;
                    border-left: 4px solid {risk_color};
                    border-radius: 3px;
                }}
                .metric {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 10px;
                    background-color: white;
                    border-radius: 3px;
                }}
                .metric-label {{
                    font-weight: bold;
                    color: #555;
                }}
                .metric-value {{
                    color: #2c3e50;
                }}
                .risk-badge {{
                    display: inline-block;
                    padding: 5px 15px;
                    background-color: {risk_color};
                    color: white;
                    border-radius: 20px;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #777;
                    font-size: 12px;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ CyberTech Security Report</h1>
            </div>
            
            <div class="content">
                <h2>Security Assessment Complete</h2>
                <p>A comprehensive security scan has been performed on your target:</p>
                
                <div class="score-box">
                    <h3>Target: {target}</h3>
                    <p><strong>Scan ID:</strong> {scan_id}</p>
                    <p><strong>Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                
                <h3>Results Summary</h3>
                
                <div class="metric">
                    <span class="metric-label">Security Score:</span>
                    <span class="metric-value">{security_score}/100</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Risk Level:</span>
                    <span class="risk-badge">{risk_level}</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Scan Duration:</span>
                    <span class="metric-value">{scan_results.get('duration', 0):.2f} seconds</span>
                </div>
                
                <h3>What's Next?</h3>
                <p>Please review the attached PDF report for detailed findings and recommendations. 
                The report includes:</p>
                <ul>
                    <li>Comprehensive vulnerability assessment</li>
                    <li>SSL/TLS configuration analysis</li>
                    <li>Security headers evaluation</li>
                    <li>Port scan results</li>
                    <li>Password security checks</li>
                    <li>Actionable recommendations</li>
                </ul>
                
                <p>If you have any questions or need assistance addressing the findings, 
                please don't hesitate to reach out.</p>
            </div>
            
            <div class="footer">
                <p>This is an automated message from CyberTech Security Scanner</p>
                <p>© {datetime.utcnow().year} CyberTech. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return html

