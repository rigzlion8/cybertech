"""
HTTP Security Headers Analyzer Module
Analyzes HTTP security headers
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HeaderAnalyzer:
    """HTTP security headers analyzer"""
    
    # Security headers to check
    SECURITY_HEADERS = {
        'Strict-Transport-Security': {
            'importance': 'high',
            'description': 'Enforces HTTPS connections'
        },
        'Content-Security-Policy': {
            'importance': 'high',
            'description': 'Prevents XSS and injection attacks'
        },
        'X-Frame-Options': {
            'importance': 'medium',
            'description': 'Prevents clickjacking attacks'
        },
        'X-Content-Type-Options': {
            'importance': 'medium',
            'description': 'Prevents MIME-type sniffing'
        },
        'X-XSS-Protection': {
            'importance': 'low',
            'description': 'Legacy XSS protection'
        },
        'Referrer-Policy': {
            'importance': 'medium',
            'description': 'Controls referrer information'
        },
        'Permissions-Policy': {
            'importance': 'medium',
            'description': 'Controls browser features'
        }
    }
    
    def __init__(self, target, timeout=10):
        self.target = target
        self.timeout = timeout
        
    def analyze(self):
        """Perform comprehensive header analysis"""
        results = {
            'target': self.target,
            'timestamp': datetime.utcnow().isoformat(),
            'headers': {},
            'missing_headers': [],
            'security_issues': [],
            'score': 100
        }
        
        try:
            # Fetch headers
            response = requests.get(
                self.target,
                timeout=self.timeout,
                allow_redirects=True,
                verify=True
            )
            
            results['status_code'] = response.status_code
            results['headers'] = dict(response.headers)
            
            # Check for security headers
            for header, info in self.SECURITY_HEADERS.items():
                if header not in response.headers:
                    results['missing_headers'].append({
                        'header': header,
                        'importance': info['importance'],
                        'description': info['description']
                    })
                    
                    results['security_issues'].append({
                        'severity': info['importance'],
                        'issue': f'Missing {header} header',
                        'description': info['description']
                    })
            
            # Check for information disclosure
            disclosure_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version']
            for header in disclosure_headers:
                if header in response.headers:
                    results['security_issues'].append({
                        'severity': 'low',
                        'issue': f'Information disclosure in {header} header',
                        'description': f'Header reveals: {response.headers[header]}'
                    })
            
            # Check cookies security
            cookies_issues = self._check_cookies_security(response)
            if cookies_issues:
                results['security_issues'].extend(cookies_issues)
                results['cookies_security'] = cookies_issues
            
            # Calculate score
            results['score'] = self._calculate_headers_score(results)
            results['summary'] = f"{len(results['missing_headers'])} security headers missing"
            
            return results
            
        except Exception as e:
            logger.error(f"Header analysis error: {str(e)}")
            return {
                'error': str(e),
                'score': 50
            }
    
    def quick_analyze(self):
        """Perform quick header analysis"""
        try:
            response = requests.get(self.target, timeout=self.timeout)
            
            missing_critical = []
            for header, info in self.SECURITY_HEADERS.items():
                if info['importance'] == 'high' and header not in response.headers:
                    missing_critical.append(header)
            
            score = 100 - (len(missing_critical) * 20)
            
            return {
                'status_code': response.status_code,
                'missing_critical_headers': missing_critical,
                'score': max(0, score)
            }
            
        except Exception as e:
            logger.error(f"Quick header analysis error: {str(e)}")
            return {'error': str(e), 'score': 50}
    
    def _check_cookies_security(self, response):
        """Check cookie security attributes"""
        issues = []
        
        cookies = response.cookies
        for cookie in cookies:
            cookie_issues = []
            
            if not cookie.secure:
                cookie_issues.append('Missing Secure flag')
            
            if not cookie.has_nonstandard_attr('HttpOnly'):
                cookie_issues.append('Missing HttpOnly flag')
            
            if not cookie.has_nonstandard_attr('SameSite'):
                cookie_issues.append('Missing SameSite attribute')
            
            if cookie_issues:
                issues.append({
                    'severity': 'medium',
                    'issue': f'Insecure cookie: {cookie.name}',
                    'description': ', '.join(cookie_issues)
                })
        
        return issues
    
    def _calculate_headers_score(self, results):
        """Calculate security score based on headers"""
        score = 100
        
        for issue in results['security_issues']:
            severity = issue.get('severity', 'low')
            if severity == 'critical':
                score -= 20
            elif severity == 'high':
                score -= 15
            elif severity == 'medium':
                score -= 10
            else:
                score -= 5
        
        return max(0, score)

