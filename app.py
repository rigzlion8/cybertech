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
        
        # Generate report
        report_gen = ReportGenerator(scan_results)
        report_path = report_gen.generate_pdf_report()
        scan_id = scan_results.get('scan_id')
        
        # Send email if provided
        if email:
            logger.info(f"Sending report to: {email}")
            email_sender = EmailSender()
            email_result = email_sender.send_report(
                recipient=email,
                report_path=report_path,
                scan_results=scan_results
            )
            
            if not email_result['success']:
                logger.warning(f"Failed to send email: {email_result.get('error')}")
        
        return jsonify({
            'status': 'success',
            'scan_id': scan_id,
            'results': scan_results,
            'report_url': f'/api/report/{scan_id}',
            'email_sent': bool(email and email_result.get('success')),
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
    """Download scan report"""
    try:
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

