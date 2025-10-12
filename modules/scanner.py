"""
Main Security Scanner Module
Orchestrates all security checks
"""

import logging
import uuid
from datetime import datetime
from urllib.parse import urlparse
import validators

from .port_scanner import PortScanner
from .vulnerability_scanner import VulnerabilityScanner
from .ssl_checker import SSLChecker
from .password_checker import PasswordChecker
from .header_analyzer import HeaderAnalyzer
from .database_checker import DatabaseChecker

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Main security scanner class"""
    
    def __init__(self, target, scan_type='full', options=None):
        self.target = target
        self.scan_type = scan_type
        self.options = options or {}
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.utcnow()
        
        # Parse target
        self.parsed_url = self._parse_target(target)
        
    def _parse_target(self, target):
        """Parse and validate target"""
        if not target.startswith(('http://', 'https://')):
            target = 'https://' + target
        
        if not validators.url(target):
            logger.warning(f"Invalid URL format: {target}")
        
        return urlparse(target)
    
    def scan(self):
        """Perform comprehensive security scan"""
        logger.info(f"Starting {self.scan_type} scan for {self.target}")
        
        results = {
            'scan_id': self.scan_id,
            'target': self.target,
            'scan_type': self.scan_type,
            'start_time': self.start_time.isoformat(),
            'results': {}
        }
        
        try:
            # Determine what scans to perform
            scan_config = self._get_scan_config()
            
            # Port Scanning
            if scan_config.get('port_scan'):
                logger.info("Starting port scan...")
                port_scanner = PortScanner(self.parsed_url.hostname or self.target)
                results['results']['port_scan'] = port_scanner.scan()
            
            # Vulnerability Scanning
            if scan_config.get('vulnerability_scan'):
                logger.info("Starting vulnerability scan...")
                vuln_scanner = VulnerabilityScanner(self.target)
                results['results']['vulnerabilities'] = vuln_scanner.scan()
            
            # SSL/TLS Check
            if scan_config.get('ssl_check'):
                logger.info("Starting SSL/TLS check...")
                ssl_checker = SSLChecker(self.parsed_url.hostname or self.target)
                results['results']['ssl_tls'] = ssl_checker.check()
            
            # HTTP Headers Analysis
            if scan_config.get('headers_check'):
                logger.info("Starting headers analysis...")
                header_analyzer = HeaderAnalyzer(self.target)
                results['results']['headers'] = header_analyzer.analyze()
            
            # Password Security Check
            if scan_config.get('password_check'):
                logger.info("Starting password security check...")
                password_checker = PasswordChecker(self.target)
                results['results']['passwords'] = password_checker.check()
            
            # Database Security Check
            if scan_config.get('database_check'):
                logger.info("Starting database security check...")
                db_checker = DatabaseChecker(self.target)
                results['results']['database'] = db_checker.check()
            
            # Calculate overall security score
            results['security_score'] = self._calculate_security_score(results['results'])
            results['risk_level'] = self._get_risk_level(results['security_score'])
            
            results['end_time'] = datetime.utcnow().isoformat()
            results['duration'] = (datetime.utcnow() - self.start_time).total_seconds()
            
            logger.info(f"Scan completed. Score: {results['security_score']}/100")
            
            return results
            
        except Exception as e:
            logger.error(f"Scan error: {str(e)}", exc_info=True)
            results['error'] = str(e)
            results['status'] = 'failed'
            return results
    
    def quick_check(self):
        """Perform quick security check"""
        logger.info(f"Starting quick check for {self.target}")
        
        results = {
            'target': self.target,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        try:
            # Quick SSL check
            ssl_checker = SSLChecker(self.parsed_url.hostname or self.target)
            results['checks']['ssl'] = ssl_checker.quick_check()
            
            # Quick headers check
            header_analyzer = HeaderAnalyzer(self.target)
            results['checks']['headers'] = header_analyzer.quick_analyze()
            
            # Calculate quick score
            results['quick_score'] = self._calculate_quick_score(results['checks'])
            
            return results
            
        except Exception as e:
            logger.error(f"Quick check error: {str(e)}")
            results['error'] = str(e)
            return results
    
    def _get_scan_config(self):
        """Get scan configuration based on scan type and options"""
        if self.scan_type == 'full':
            return {
                'port_scan': self.options.get('port_scan', True),
                'vulnerability_scan': self.options.get('vulnerability_scan', True),
                'ssl_check': self.options.get('ssl_check', True),
                'headers_check': self.options.get('headers_check', True),
                'password_check': self.options.get('password_check', True),
                'database_check': self.options.get('database_check', False)
            }
        elif self.scan_type == 'quick':
            return {
                'port_scan': False,
                'vulnerability_scan': False,
                'ssl_check': True,
                'headers_check': True,
                'password_check': False,
                'database_check': False
            }
        else:  # custom
            return self.options
    
    def _calculate_security_score(self, results):
        """Calculate overall security score (0-100)"""
        scores = []
        weights = {
            'ssl_tls': 0.25,
            'headers': 0.20,
            'vulnerabilities': 0.30,
            'passwords': 0.15,
            'port_scan': 0.10
        }
        
        for category, weight in weights.items():
            if category in results:
                category_score = results[category].get('score', 50)
                scores.append(category_score * weight)
        
        total_score = sum(scores) if scores else 50
        return round(total_score, 2)
    
    def _calculate_quick_score(self, checks):
        """Calculate quick score"""
        ssl_score = checks.get('ssl', {}).get('score', 50)
        headers_score = checks.get('headers', {}).get('score', 50)
        return round((ssl_score * 0.6 + headers_score * 0.4), 2)
    
    def _get_risk_level(self, score):
        """Get risk level based on score"""
        if score >= 80:
            return 'LOW'
        elif score >= 60:
            return 'MEDIUM'
        elif score >= 40:
            return 'HIGH'
        else:
            return 'CRITICAL'

