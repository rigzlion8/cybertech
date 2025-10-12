"""
SSL/TLS Security Checker Module
Checks SSL certificate validity and configuration
"""

import ssl
import socket
import logging
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import requests

logger = logging.getLogger(__name__)


class SSLChecker:
    """SSL/TLS security checker"""
    
    def __init__(self, hostname, port=443):
        self.hostname = hostname
        self.port = port
        
    def check(self):
        """Perform comprehensive SSL/TLS check"""
        results = {
            'hostname': self.hostname,
            'port': self.port,
            'certificate': {},
            'protocol': {},
            'issues': [],
            'score': 100
        }
        
        try:
            # Get certificate information
            cert_info = self._get_certificate_info()
            results['certificate'] = cert_info
            
            # Check certificate validity
            if cert_info.get('valid'):
                if cert_info.get('days_until_expiry', 0) < 30:
                    results['issues'].append({
                        'severity': 'high',
                        'description': f'Certificate expires in {cert_info.get("days_until_expiry")} days'
                    })
                elif cert_info.get('days_until_expiry', 0) < 90:
                    results['issues'].append({
                        'severity': 'medium',
                        'description': f'Certificate expires in {cert_info.get("days_until_expiry")} days'
                    })
            else:
                results['issues'].append({
                    'severity': 'critical',
                    'description': 'Invalid or expired certificate'
                })
            
            # Check protocol version
            protocol_info = self._check_protocol_version()
            results['protocol'] = protocol_info
            
            if protocol_info.get('uses_old_tls'):
                results['issues'].append({
                    'severity': 'high',
                    'description': 'Server supports old TLS versions (TLS 1.0/1.1)'
                })
            
            # Check cipher suites
            cipher_info = self._check_cipher_suites()
            results['cipher_suites'] = cipher_info
            
            if cipher_info.get('weak_ciphers'):
                results['issues'].append({
                    'severity': 'medium',
                    'description': 'Weak cipher suites detected'
                })
            
            # Calculate score
            results['score'] = self._calculate_ssl_score(results)
            results['summary'] = f"SSL/TLS security level: {self._get_ssl_grade(results['score'])}"
            
            return results
            
        except Exception as e:
            logger.error(f"SSL check error: {str(e)}")
            return {
                'error': str(e),
                'score': 0,
                'issues': [{'severity': 'critical', 'description': 'SSL/TLS not available or misconfigured'}]
            }
    
    def quick_check(self):
        """Perform quick SSL check"""
        try:
            cert_info = self._get_certificate_info()
            return {
                'valid': cert_info.get('valid', False),
                'expires': cert_info.get('expires'),
                'days_until_expiry': cert_info.get('days_until_expiry'),
                'score': 100 if cert_info.get('valid') else 0
            }
        except Exception as e:
            logger.error(f"Quick SSL check error: {str(e)}")
            return {'error': str(e), 'score': 0}
    
    def _get_certificate_info(self):
        """Get SSL certificate information"""
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((self.hostname, self.port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_pem = ssock.getpeercert()
                    
                    # Parse certificate
                    cert = x509.load_der_x509_certificate(cert_der, default_backend())
                    
                    # Get certificate details
                    not_after = cert.not_valid_after
                    not_before = cert.not_valid_before
                    days_until_expiry = (not_after - datetime.utcnow()).days
                    
                    return {
                        'subject': cert.subject.rfc4514_string(),
                        'issuer': cert.issuer.rfc4514_string(),
                        'version': cert.version.name,
                        'serial_number': str(cert.serial_number),
                        'not_before': not_before.isoformat(),
                        'not_after': not_after.isoformat(),
                        'expires': not_after.strftime('%Y-%m-%d'),
                        'days_until_expiry': days_until_expiry,
                        'valid': datetime.utcnow() < not_after,
                        'signature_algorithm': cert.signature_algorithm_oid._name
                    }
                    
        except Exception as e:
            logger.error(f"Certificate info error: {str(e)}")
            return {
                'error': str(e),
                'valid': False
            }
    
    def _check_protocol_version(self):
        """Check TLS protocol versions"""
        supported_protocols = []
        uses_old_tls = False
        
        # Try different TLS versions
        protocols = [
            ('TLS 1.0', ssl.PROTOCOL_TLSv1),
            ('TLS 1.1', ssl.PROTOCOL_TLSv1_1),
            ('TLS 1.2', ssl.PROTOCOL_TLSv1_2),
        ]
        
        # Try TLS 1.3 if available
        if hasattr(ssl, 'PROTOCOL_TLSv1_3'):
            protocols.append(('TLS 1.3', ssl.PROTOCOL_TLSv1_3))
        
        for name, protocol in protocols:
            try:
                context = ssl.SSLContext(protocol)
                with socket.create_connection((self.hostname, self.port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                        supported_protocols.append(name)
                        if name in ['TLS 1.0', 'TLS 1.1']:
                            uses_old_tls = True
            except:
                pass
        
        return {
            'supported_protocols': supported_protocols,
            'uses_old_tls': uses_old_tls
        }
    
    def _check_cipher_suites(self):
        """Check cipher suites"""
        weak_ciphers = []
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.hostname, self.port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cipher = ssock.cipher()
                    
                    # Check for weak ciphers
                    cipher_name = cipher[0] if cipher else ''
                    
                    weak_patterns = ['DES', 'RC4', 'MD5', 'NULL', 'EXPORT', 'anon']
                    for pattern in weak_patterns:
                        if pattern in cipher_name:
                            weak_ciphers.append(cipher_name)
                    
                    return {
                        'current_cipher': cipher_name,
                        'weak_ciphers': weak_ciphers
                    }
        except:
            return {
                'weak_ciphers': []
            }
    
    def _calculate_ssl_score(self, results):
        """Calculate SSL security score"""
        score = 100
        
        for issue in results['issues']:
            severity = issue.get('severity', 'low')
            if severity == 'critical':
                score -= 30
            elif severity == 'high':
                score -= 20
            elif severity == 'medium':
                score -= 10
            else:
                score -= 5
        
        return max(0, score)
    
    def _get_ssl_grade(self, score):
        """Get SSL grade based on score"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

