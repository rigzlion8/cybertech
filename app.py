#!/usr/bin/env python3
"""
CyberTech Security Scanner
Main Flask Application
"""

import os
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from datetime import datetime
import json

from modules.scanner import SecurityScanner
from modules.report_generator import ReportGenerator
from modules.email_sender import EmailSender
from modules.scan_storage import ScanStorage
from modules.mpesa_payment import MPesaPayment
from modules.payment_manager import PaymentManager
from modules.resend_email import ResendEmail
from modules.paystack_payment import PaystackPayment

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cybertech.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create reports directory if it doesn't exist
os.makedirs('reports', exist_ok=True)

# Initialize scan storage
scan_storage = ScanStorage()

# Initialize payment systems
mpesa_environment = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
mpesa_payment = MPesaPayment(environment=mpesa_environment)
paystack_payment = PaystackPayment()
payment_manager = PaymentManager()

# Initialize email system (Resend)
resend_email = ResendEmail()


@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/scan', methods=['POST'])
def perform_scan():
    """
    Perform comprehensive security scan
    Expected JSON body:
    {
        "target": "https://example.com",
        "scan_type": "full",  # Options: full, quick, custom
        "email": "user@example.com",
        "options": {
            "port_scan": true,
            "vulnerability_scan": true,
            "ssl_check": true,
            "password_check": true,
            "database_check": false,
            "headers_check": true
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'target' not in data:
            return jsonify({
                'error': 'Target URL/IP is required',
                'status': 'error'
            }), 400
        
        target = data.get('target')
        scan_type = data.get('scan_type', 'full')
        email = data.get('email')
        options = data.get('options', {})
        
        logger.info(f"Starting security scan for target: {target}")
        
        # Initialize scanner
        scanner = SecurityScanner(target, scan_type, options)
        
        # Perform scan
        scan_results = scanner.scan()
        scan_id = scan_results.get('scan_id')
        
        # Generate report
        report_path = None
        try:
            logger.info(f"Generating PDF report for scan {scan_id}")
            report_gen = ReportGenerator(scan_results)
            report_path = report_gen.generate_pdf_report()
            logger.info(f"PDF report generated successfully: {report_path}")
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {str(e)}", exc_info=True)
            # Continue even if PDF generation fails
        
        # Send email if provided (using Resend for better delivery)
        email_result = {'success': False}
        if email and report_path:
            logger.info(f"Sending report to: {email}")
            try:
                # Try Resend first (modern, better delivery)
                email_result = resend_email.send_report(
                    recipient=email,
                    report_path=report_path,
                    scan_results=scan_results
                )
                
                # Fallback to original EmailSender if Resend fails
                if not email_result['success']:
                    logger.warning(f"Resend failed, trying fallback: {email_result.get('error')}")
                    try:
                        email_sender = EmailSender()
                        email_result = email_sender.send_report(
                            recipient=email,
                            report_path=report_path,
                            scan_results=scan_results
                        )
                    except:
                        pass
                
                if not email_result['success']:
                    logger.warning(f"Failed to send email: {email_result.get('error')}")
            except Exception as e:
                logger.error(f"Email sending error: {str(e)}")
        
        # Save scan to storage
        try:
            scan_storage.save_scan(scan_results)
            logger.info(f"Scan {scan_id} saved to storage")
        except Exception as e:
            logger.error(f"Failed to save scan to storage: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'scan_id': scan_id,
            'results': scan_results,
            'report_url': f'/api/report/{scan_id}' if report_path else None,
            'report_available': bool(report_path),
            'email_sent': email_result.get('success', False),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Scan error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/report/<scan_id>', methods=['GET'])
def get_report(scan_id):
    """Download scan report (requires payment or subscription)"""
    try:
        # Check if payment is required
        email = request.args.get('email')
        
        # If email provided, check payment status
        if email:
            # Check if user has paid for this report or has subscription
            has_paid = payment_manager.check_report_payment_by_email(scan_id, email)
            
            if not has_paid:
                return jsonify({
                    'error': 'Payment required',
                    'status': 'error',
                    'payment_required': True,
                    'message': 'Pay 100 KSH to download this report or subscribe for unlimited access'
                }), 402  # Payment Required status code
        
        report_path = f'reports/scan_{scan_id}.pdf'
        
        if not os.path.exists(report_path):
            return jsonify({
                'error': 'Report not found',
                'status': 'error'
            }), 404
        
        return send_file(
            report_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'security_report_{scan_id}.pdf'
        )
        
    except Exception as e:
        logger.error(f"Report retrieval error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/quick-check', methods=['POST'])
def quick_check():
    """Perform a quick security check (no full scan)"""
    try:
        data = request.get_json()
        
        if not data or 'target' not in data:
            return jsonify({
                'error': 'Target URL/IP is required',
                'status': 'error'
            }), 400
        
        target = data.get('target')
        
        scanner = SecurityScanner(target, 'quick', {})
        results = scanner.quick_check()
        
        return jsonify({
            'status': 'success',
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Quick check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/admin')
def admin_page():
    """Serve the admin page"""
    return send_from_directory('static', 'admin.html')


@app.route('/api/admin/scans', methods=['GET'])
def get_all_scans():
    """
    Get all scans with pagination
    Query params:
        - limit: Max number of scans (default: 100)
        - offset: Number of scans to skip (default: 0)
        - search: Search query string (optional)
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '').strip()
        
        if search:
            scans = scan_storage.search_scans(search, limit=limit)
            total = len(scans)
        else:
            scans = scan_storage.get_all_scans(limit=limit, offset=offset)
            total = scan_storage.get_scan_count()
        
        return jsonify({
            'status': 'success',
            'scans': scans,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting scans: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/admin/scan/<scan_id>', methods=['GET'])
def get_scan_details(scan_id):
    """Get detailed scan information by ID"""
    try:
        scan = scan_storage.get_scan(scan_id)
        
        if not scan:
            return jsonify({
                'status': 'error',
                'error': 'Scan not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'scan': scan
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting scan {scan_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/admin/scan/<scan_id>', methods=['DELETE'])
def delete_scan(scan_id):
    """Delete a scan by ID"""
    try:
        success = scan_storage.delete_scan(scan_id)
        
        if not success:
            return jsonify({
                'status': 'error',
                'error': 'Scan not found or could not be deleted'
            }), 404
        
        # Also try to delete the PDF report
        report_path = f'reports/scan_{scan_id}.pdf'
        if os.path.exists(report_path):
            os.remove(report_path)
        
        return jsonify({
            'status': 'success',
            'message': 'Scan deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting scan {scan_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/admin/statistics', methods=['GET'])
def get_statistics():
    """Get overall scan statistics"""
    try:
        stats = scan_storage.get_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/admin/trends', methods=['GET'])
def get_trends():
    """
    Get trend data for the specified period
    Query params:
        - days: Number of days to analyze (default: 30)
    """
    try:
        days = int(request.args.get('days', 30))
        trend_data = scan_storage.get_trend_data(days=days)
        
        return jsonify({
            'status': 'success',
            'trends': trend_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/admin/target/<path:target>/history', methods=['GET'])
def get_target_scan_history(target):
    """Get scan history for a specific target"""
    try:
        limit = int(request.args.get('limit', 10))
        history = scan_storage.get_target_history(target, limit=limit)
        
        return jsonify({
            'status': 'success',
            'target': target,
            'history': history
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting target history: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/admin/target/<path:target>/improvement', methods=['GET'])
def get_target_improvement(target):
    """Get security score improvement trend for a specific target"""
    try:
        improvement_data = scan_storage.get_score_improvement_trend(target)
        
        return jsonify({
            'status': 'success',
            'improvement': improvement_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting score improvement: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/pricing')
def pricing_page():
    """Serve the pricing/subscription page"""
    return send_from_directory('static', 'pricing.html')


@app.route('/api/payment/test-config', methods=['GET'])
def test_payment_config():
    """Test if payment systems are configured"""
    try:
        mpesa_configured = bool(mpesa_payment.consumer_key and mpesa_payment.consumer_secret)
        paystack_configured = bool(paystack_payment.secret_key)
        
        return jsonify({
            'status': 'success',
            'mpesa_configured': mpesa_configured,
            'paystack_configured': paystack_configured,
            'mpesa_environment': mpesa_payment.environment,
            'mpesa_shortcode': mpesa_payment.business_short_code
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/payment/initiate-report', methods=['POST'])
def initiate_report_payment():
    """
    Initiate payment for report download (100 KSH)
    Expected JSON: {"phone_number": "254XXXXXXXXX", "scan_id": "abc123"}
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        scan_id = data.get('scan_id')
        
        if not phone_number or not scan_id:
            return jsonify({
                'status': 'error',
                'error': 'Phone number and scan ID are required'
            }), 400
        
        # Check if already paid
        if payment_manager.check_report_payment(scan_id, phone_number):
            return jsonify({
                'status': 'success',
                'already_paid': True,
                'message': 'Report already paid for or you have an active subscription'
            }), 200
        
        # Initiate M-Pesa payment
        logger.info(f"Initiating M-Pesa payment: phone={phone_number}, amount=100, scan_id={scan_id}")
        
        result = mpesa_payment.initiate_stk_push(
            phone_number=phone_number,
            amount=100,
            account_reference=f"REPORT-{scan_id}",
            transaction_desc="CyberTech Report Download"
        )
        
        logger.info(f"M-Pesa result: {result}")
        
        if result.get('success'):
            # Save payment record
            payment_manager.create_payment_record({
                'checkout_request_id': result['checkout_request_id'],
                'merchant_request_id': result['merchant_request_id'],
                'phone_number': phone_number,
                'amount': 100,
                'payment_type': 'report_download',
                'scan_id': scan_id
            })
            
            logger.info(f"Payment record created for {phone_number}")
            
            return jsonify({
                'status': 'success',
                'checkout_request_id': result['checkout_request_id'],
                'message': result.get('customer_message', 'Payment request sent to your phone')
            }), 200
        else:
            logger.error(f"M-Pesa payment failed: {result.get('error')}")
            return jsonify({
                'status': 'error',
                'error': result.get('error', 'Failed to initiate payment'),
                'details': result
            }), 500
            
    except Exception as e:
        logger.error(f"Error initiating report payment: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/payment/initiate-subscription', methods=['POST'])
def initiate_subscription_payment():
    """
    Initiate subscription payment (2000 KSH/month)
    Expected JSON: {"phone_number": "254XXXXXXXXX", "plan": "pro"}
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        plan = data.get('plan', 'pro')
        
        if not phone_number:
            return jsonify({
                'status': 'error',
                'error': 'Phone number is required'
            }), 400
        
        # Get plan details
        plan_details = payment_manager.PLANS.get(plan)
        if not plan_details:
            return jsonify({
                'status': 'error',
                'error': 'Invalid plan'
            }), 400
        
        amount = plan_details['price']
        
        # Initiate M-Pesa payment
        result = mpesa_payment.initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=f"SUB-{plan.upper()}",
            transaction_desc=f"CyberTech {plan_details['name']}"
        )
        
        if result.get('success'):
            # Save payment record
            payment_manager.create_payment_record({
                'checkout_request_id': result['checkout_request_id'],
                'merchant_request_id': result['merchant_request_id'],
                'phone_number': phone_number,
                'amount': amount,
                'payment_type': 'subscription',
                'metadata': {'plan': plan}
            })
            
            return jsonify({
                'status': 'success',
                'checkout_request_id': result['checkout_request_id'],
                'message': result.get('customer_message', 'Payment request sent to your phone')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'error': result.get('error', 'Failed to initiate payment')
            }), 500
            
    except Exception as e:
        logger.error(f"Error initiating subscription payment: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/payment/callback', methods=['POST'])
def mpesa_callback():
    """
    M-Pesa payment callback endpoint
    Receives payment confirmation from Safaricom
    """
    try:
        callback_data = request.get_json()
        logger.info(f"M-Pesa callback received: {json.dumps(callback_data)}")
        
        # Validate and parse callback
        parsed_data = mpesa_payment.validate_callback(callback_data)
        
        if parsed_data.get('checkout_request_id'):
            # Update payment status
            payment_manager.update_payment_status(
                parsed_data['checkout_request_id'],
                parsed_data
            )
        
        # Always return success to M-Pesa
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}")
        return jsonify({
            'ResultCode': 1,
            'ResultDesc': 'Failed'
        }), 200


@app.route('/api/payment/status/<checkout_request_id>', methods=['GET'])
def check_payment_status(checkout_request_id):
    """Check payment status"""
    try:
        status = payment_manager.check_payment_status(checkout_request_id)
        
        return jsonify({
            'status': 'success',
            'payment': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/subscription/check', methods=['POST'])
def check_subscription():
    """
    Check if phone number has active subscription
    Expected JSON: {"phone_number": "254XXXXXXXXX"}
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({
                'status': 'error',
                'error': 'Phone number is required'
            }), 400
        
        subscription = payment_manager.get_subscription(phone_number)
        
        return jsonify({
            'status': 'success',
            'has_subscription': subscription is not None,
            'subscription': subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking subscription: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/payment/paystack/initialize', methods=['POST'])
def initialize_paystack_payment():
    """
    Initialize Paystack payment (for international users or card payments)
    Expected JSON: {"email": "user@example.com", "amount": 100, "type": "report", "scan_id": "abc123"}
    """
    try:
        data = request.get_json()
        email = data.get('email')
        amount = data.get('amount', 100)
        payment_type = data.get('type', 'report')
        scan_id = data.get('scan_id')
        
        if not email:
            return jsonify({
                'status': 'error',
                'error': 'Email address is required'
            }), 400
        
        # Generate reference
        import uuid
        reference = f"CYBERTECH-{uuid.uuid4().hex[:12].upper()}"
        
        # Initialize Paystack transaction
        result = paystack_payment.initialize_transaction(
            email=email,
            amount=amount,
            reference=reference,
            metadata={
                'payment_type': payment_type,
                'scan_id': scan_id,
                'customer_email': email
            }
        )
        
        if result.get('success'):
            # Save payment record
            payment_manager.create_payment_record({
                'checkout_request_id': reference,
                'merchant_request_id': reference,
                'phone_number': email,  # Use email as identifier for Paystack
                'amount': amount,
                'payment_type': payment_type,
                'scan_id': scan_id,
                'metadata': {'provider': 'paystack', 'reference': reference}
            })
            
            return jsonify({
                'status': 'success',
                'authorization_url': result['authorization_url'],
                'reference': result['reference']
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'error': result.get('error', 'Failed to initialize payment')
            }), 500
            
    except Exception as e:
        logger.error(f"Error initializing Paystack payment: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/payment/paystack-callback', methods=['GET'])
def paystack_callback():
    """
    Paystack payment callback (redirect after payment)
    """
    try:
        reference = request.args.get('reference')
        
        if not reference:
            return "Payment verification failed", 400
        
        # Verify transaction
        result = paystack_payment.verify_transaction(reference)
        
        if result.get('success') and result.get('verified'):
            # Update payment status
            payment_manager.update_payment_status(
                reference,
                {
                    'success': True,
                    'mpesa_receipt': reference,
                    'transaction_date': result.get('paid_at'),
                    'amount': result.get('amount'),
                    'email': result.get('customer', {}).get('email')
                }
            )
            
            # Redirect to success page
            return f"""
            <html>
            <head>
                <title>Payment Successful</title>
                <meta http-equiv="refresh" content="3;url=/" />
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; }}
                    .success {{ color: #27ae60; font-size: 24px; }}
                </style>
            </head>
            <body>
                <div class="success">✓ Payment Successful!</div>
                <p>Thank you for your payment. Redirecting...</p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <head>
                <title>Payment Failed</title>
                <meta http-equiv="refresh" content="3;url=/pricing" />
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; }}
                    .error {{ color: #e74c3c; font-size: 24px; }}
                </style>
            </head>
            <body>
                <div class="error">✗ Payment Failed</div>
                <p>Please try again. Redirecting...</p>
            </body>
            </html>
            """
            
    except Exception as e:
        logger.error(f"Error processing Paystack callback: {str(e)}")
        return "Error processing payment", 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found', 'status': 'error'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error', 'status': 'error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )

