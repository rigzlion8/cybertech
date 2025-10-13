"""
Resend Email Integration Module
Modern email sending using Resend API
"""

import os
import logging
import requests
from typing import Dict, List

logger = logging.getLogger(__name__)


class ResendEmail:
    """Email sender using Resend API"""
    
    API_URL = 'https://api.resend.com/emails'
    
    def __init__(self):
        """Initialize Resend email sender"""
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@maishatech.co.ke')
        
        if not self.api_key:
            logger.warning("RESEND_API_KEY not found in environment")
    
    def send_report(self, recipient: str, report_path: str, scan_results: Dict) -> Dict:
        """
        Send security report via email
        
        Args:
            recipient: Recipient email address
            report_path: Path to PDF report file
            scan_results: Scan results dictionary
            
        Returns:
            Dict with send status
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Resend API key not configured'
            }
        
        try:
            target = scan_results.get('target', 'Unknown')
            scan_id = scan_results.get('scan_id', 'Unknown')
            security_score = scan_results.get('security_score', 0)
            risk_level = scan_results.get('risk_level', 'UNKNOWN')
            
            # Read PDF file
            with open(report_path, 'rb') as f:
                pdf_content = f.read()
            
            # Prepare email
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Create HTML email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                    <h1 style="color: white; margin: 0;">🛡️ CyberTech Security Report</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #2c3e50;">Your Security Scan is Complete!</h2>
                    
                    <p>Thank you for using CyberTech Security Scanner. Your comprehensive security report is attached.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #2c3e50;">Scan Summary</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Target:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{target}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Scan ID:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{scan_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Security Score:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                                    <span style="color: {'#27ae60' if security_score >= 80 else '#e74c3c'}; font-weight: bold; font-size: 1.2em;">
                                        {security_score}/100
                                    </span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;"><strong>Risk Level:</strong></td>
                                <td style="padding: 10px;">
                                    <span style="background: {'#27ae60' if risk_level == 'LOW' else '#e74c3c'}; color: white; padding: 5px 15px; border-radius: 15px; font-weight: bold;">
                                        {risk_level}
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <p>The detailed security report is attached as a PDF file. Please review all findings and recommendations.</p>
                    
                    <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <strong>💡 Pro Tip:</strong> Subscribe to our Professional plan for unlimited scans and advanced features!
                        <br><a href="https://cybertech-security-scanner.fly.dev/pricing" style="color: #3498db;">View Pricing →</a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="color: #7f8c8d; font-size: 0.9em;">
                        Questions? Contact us or visit our <a href="https://cybertech-security-scanner.fly.dev">website</a>.
                    </p>
                    
                    <p style="color: #7f8c8d; font-size: 0.85em; margin-top: 20px;">
                        © 2025 CyberTech Security Scanner. All rights reserved.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Prepare attachments
            import base64
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            payload = {
                'from': self.from_email,
                'to': [recipient],
                'subject': f'🔒 Security Report for {target} - CyberTech',
                'html': html_body,
                'attachments': [
                    {
                        'filename': f'security_report_{scan_id}.pdf',
                        'content': pdf_base64
                    }
                ]
            }
            
            response = requests.post(self.API_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Email sent successfully to {recipient} via Resend")
            return {
                'success': True,
                'email_id': result.get('id'),
                'message': 'Email sent successfully'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Resend API error: {str(e)}")
            return {
                'success': False,
                'error': f'Resend API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_subscription_confirmation(self, recipient: str, subscription_data: Dict) -> Dict:
        """
        Send subscription confirmation email
        
        Args:
            recipient: Recipient email/phone (will be converted to email)
            subscription_data: Subscription details
            
        Returns:
            Dict with send status
        """
        if not self.api_key:
            return {'success': False, 'error': 'Resend API key not configured'}
        
        try:
            plan = subscription_data.get('plan', 'Professional')
            expires_at = subscription_data.get('expires_at', 'Unknown')
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #27ae60 0%, #229954 100%); padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="color: white; margin: 0;">🎉 Welcome to CyberTech Professional!</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; margin-top: 20px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Your Subscription is Active!</h2>
                    
                    <p>Thank you for subscribing to CyberTech Security Scanner {plan} Plan!</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #2c3e50;">Subscription Details</h3>
                        <p><strong>Plan:</strong> {plan}</p>
                        <p><strong>Price:</strong> 2,000 KSH/month</p>
                        <p><strong>Expires:</strong> {expires_at}</p>
                        <p><strong>Status:</strong> <span style="color: #27ae60; font-weight: bold;">Active ✓</span></p>
                    </div>
                    
                    <h3>Your Premium Features:</h3>
                    <ul style="line-height: 1.8;">
                        <li>✓ SQL Injection vulnerability scanning</li>
                        <li>✓ XSS (Cross-Site Scripting) detection</li>
                        <li>✓ Directory & file enumeration</li>
                        <li>✓ Unlimited security scans</li>
                        <li>✓ Unlimited report downloads</li>
                        <li>✓ Email report delivery</li>
                        <li>✓ Trend analysis & tracking</li>
                        <li>✓ Priority customer support</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://cybertech-security-scanner.fly.dev" 
                           style="display: inline-block; background: #3498db; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                            Start Scanning Now →
                        </a>
                    </div>
                    
                    <p style="color: #7f8c8d; font-size: 0.9em; margin-top: 30px;">
                        Need help? Contact us anytime!
                    </p>
                </div>
            </body>
            </html>
            """
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'from': self.from_email,
                'to': [recipient],
                'subject': '🎉 Welcome to CyberTech Professional!',
                'html': html_body
            }
            
            response = requests.post(self.API_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Subscription confirmation sent to {recipient}")
            return {
                'success': True,
                'email_id': result.get('id')
            }
            
        except Exception as e:
            logger.error(f"Error sending subscription confirmation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

