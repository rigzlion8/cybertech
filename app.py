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
        
        # Send email if provided
        email_result = {'success': False}
        if email and report_path:
            logger.info(f"Sending report to: {email}")
            try:
                email_sender = EmailSender()
                email_result = email_sender.send_report(
                    recipient=email,
                    report_path=report_path,
                    scan_results=scan_results
                )
                
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

