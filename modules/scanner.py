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
from .sqli_scanner import SQLInjectionScanner
from .xss_scanner import XSSScanner
from .quick_wins_scanner import QuickWinsScanner
from .directory_enum_scanner import DirectoryEnumerationScanner

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Main security scanner class"""
    
    def __init__(self, target, scan_type='full', options=None):
        self.original_target = target
        self.scan_type = scan_type
        self.options = options or {}
        self.scan_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.utcnow()
        
        # Parse and normalize target
        self.parsed_url = self._parse_target(target)
        self.normalized_target = self._normalize_target(target)
        
    def _parse_target(self, target):
        """Parse and validate target - handles both IP addresses and URLs"""
        # Clean and normalize the target
        normalized_target = self._normalize_target(target)
        
        # Validate the target
        self._validate_target(target, normalized_target)
        
        if not validators.url(normalized_target):
            logger.warning(f"Invalid URL format: {target}")
        
        return urlparse(normalized_target)
    
    def _validate_target(self, original_target, normalized_target):
        """Validate target to prevent scanning localhost or problematic addresses"""
        blocked_targets = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1',
            'localhost.localdomain',
            '127.0.0.0/8',
            '10.0.0.0/8',
            '172.16.0.0/12',
            '192.168.0.0/16',
            '169.254.0.0/16',
        ]
        
        # Check for blocked targets
        for blocked in blocked_targets:
            if blocked in original_target.lower() or blocked in normalized_target.lower():
                raise ValueError(f"Scanning localhost or private network addresses ({blocked}) is not allowed")
        
        # Check for localhost in hostname
        parsed = urlparse(normalized_target)
        hostname = parsed.hostname or original_target
        
        if hostname and any(local in hostname.lower() for local in ['localhost', '127.', '0.0.0.0', '::1']):
            raise ValueError("Scanning localhost addresses is not allowed for security reasons")
        
        # Check if it's a private IP address
        if self._is_private_ip(hostname):
            raise ValueError("Scanning private IP addresses is not allowed")
    
    def _normalize_target(self, target):
        """Normalize target by adding protocol and www prefix when necessary"""
        # Remove any whitespace
        target = target.strip()
        
        # Check if it's already a full URL
        if target.startswith(('http://', 'https://')):
            return target
        
        # Check if it's an IP address (IPv4 or IPv6)
        if self._is_ip_address(target):
            return f'https://{target}'
        
        # It's a domain/URL without protocol
        # Check if it already has www prefix
        if target.startswith('www.'):
            return f'https://{target}'
        
        # Check if it needs www prefix (if no subdomain present)
        if not self._has_subdomain(target):
            # Add www prefix
            return f'https://www.{target}'
        
        # Has subdomain, just add https://
        return f'https://{target}'
    
    def _is_ip_address(self, target):
        """Check if target is an IP address (IPv4 or IPv6)"""
        import ipaddress
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            return False
    
    def _has_subdomain(self, target):
        """Check if target already has a subdomain (excluding www)"""
        # Remove any potential protocol if present
        clean_target = target.replace('http://', '').replace('https://', '')
        
        # Remove www. prefix if present for subdomain detection
        clean_target = clean_target.replace('www.', '')
        
        # For IP addresses, consider them as having "subdomain" to avoid adding www
        if self._is_ip_address(clean_target):
            return True
        
        # Split by dots and check if there are at least 2 parts (domain.tld)
        parts = clean_target.split('.')
        if len(parts) >= 3:
            return True
        
        # Check for common multi-part TLDs
        multi_part_tlds = ['.co.uk', '.co.za', '.com.au', '.org.uk', '.net.au']
        for tld in multi_part_tlds:
            if clean_target.endswith(tld):
                # If the domain has more than just the domain name before the TLD
                domain_part = clean_target[:-len(tld)]
                if '.' in domain_part:
                    return True
        
        return False
    
    def _is_private_ip(self, ip_address):
        """Check if IP address is in private range"""
        import ipaddress
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private
        except ValueError:
            return False
    
    def scan(self):
        """Perform comprehensive security scan"""
        logger.info(f"Starting {self.scan_type} scan for {self.original_target} -> {self.normalized_target}")
        
        results = {
            'scan_id': self.scan_id,
            'target': self.original_target,
            'normalized_target': self.normalized_target,
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
                vuln_scanner = VulnerabilityScanner(self.normalized_target)
                results['results']['vulnerabilities'] = vuln_scanner.scan()
            
            # SSL/TLS Check
            if scan_config.get('ssl_check'):
                logger.info("Starting SSL/TLS check...")
                ssl_checker = SSLChecker(self.parsed_url.hostname or self.original_target)
                results['results']['ssl_tls'] = ssl_checker.check()
            
            # HTTP Headers Analysis
            if scan_config.get('headers_check'):
                logger.info("Starting headers analysis...")
                header_analyzer = HeaderAnalyzer(self.normalized_target)
                results['results']['headers'] = header_analyzer.analyze()
            
            # Password Security Check
            if scan_config.get('password_check'):
                logger.info("Starting password security check...")
                password_checker = PasswordChecker(self.normalized_target)
                results['results']['passwords'] = password_checker.check()
            
            # Database Security Check
            if scan_config.get('database_check'):
                logger.info("Starting database security check...")
                db_checker = DatabaseChecker(self.normalized_target)
                results['results']['database'] = db_checker.check()
            
            # SQL Injection Scanner
            if scan_config.get('sql_injection_check'):
                logger.info("Starting SQL injection scan...")
                sqli_scanner = SQLInjectionScanner(self.normalized_target)
                results['results']['sql_injection'] = sqli_scanner.scan()
            
            # XSS Scanner
            if scan_config.get('xss_check'):
                logger.info("Starting XSS scan...")
                xss_scanner = XSSScanner(self.normalized_target)
                results['results']['xss'] = xss_scanner.scan()
            
            # Quick Wins Scanner
            if scan_config.get('quick_wins_check'):
                logger.info("Starting quick wins scan...")
                quick_scanner = QuickWinsScanner(self.normalized_target)
                results['results']['quick_wins'] = quick_scanner.scan()
            
            # Directory Enumeration
            if scan_config.get('directory_enum_check'):
                logger.info("Starting directory enumeration...")
                dir_scanner = DirectoryEnumerationScanner(self.normalized_target)
                results['results']['directory_enum'] = dir_scanner.scan()
            
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
        logger.info(f"Starting quick check for {self.original_target} -> {self.normalized_target}")
        
        results = {
            'target': self.original_target,
            'normalized_target': self.normalized_target,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        try:
            # Quick SSL check
            ssl_checker = SSLChecker(self.parsed_url.hostname or self.original_target)
            results['checks']['ssl'] = ssl_checker.quick_check()
            
            # Quick headers check
            header_analyzer = HeaderAnalyzer(self.normalized_target)
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
                'database_check': self.options.get('database_check', False),
                'sql_injection_check': self.options.get('sql_injection_check', True),
                'xss_check': self.options.get('xss_check', True),
                'quick_wins_check': self.options.get('quick_wins_check', True),
                'directory_enum_check': self.options.get('directory_enum_check', True)
            }
        elif self.scan_type == 'quick':
            return {
                'port_scan': False,
                'vulnerability_scan': False,
                'ssl_check': True,
                'headers_check': True,
                'password_check': False,
                'database_check': False,
                'sql_injection_check': False,
                'xss_check': False,
                'quick_wins_check': True,  # Quick wins are fast, keep them
                'directory_enum_check': False
            }
        else:  # custom
            return self.options
    
    def _calculate_security_score(self, results):
        """Calculate overall security score (0-100)"""
        scores = []
        weights = {
            'ssl_tls': 0.15,
            'headers': 0.10,
            'vulnerabilities': 0.15,
            'passwords': 0.10,
            'port_scan': 0.05,
            'sql_injection': 0.20,  # Critical - high weight
            'xss': 0.15,  # High - medium-high weight
            'quick_wins': 0.05,
            'directory_enum': 0.05
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

