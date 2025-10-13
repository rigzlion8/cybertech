"""
Quick Wins Security Scanner Module
Fast, easy-to-implement security checks with high value
Includes: Robots.txt, Clickjacking, HTTP Methods, Security.txt
"""

import logging
import urllib.parse
from typing import Dict, List
import requests

logger = logging.getLogger(__name__)


class QuickWinsScanner:
    """Quick security wins scanner"""
    
    # Dangerous HTTP methods
    DANGEROUS_METHODS = ['PUT', 'DELETE', 'TRACE', 'CONNECT', 'PATCH']
    
    # Sensitive paths often found in robots.txt
    SENSITIVE_INDICATORS = [
        'admin', 'backup', 'config', 'database', 'sql', 'dump',
        'private', 'secret', 'internal', 'test', 'dev', 'staging',
        '.git', '.env', '.ssh', 'wp-admin', 'phpmyadmin'
    ]
    
    def __init__(self, target_url, timeout=10):
        """
        Initialize Quick Wins Scanner
        
        Args:
            target_url: Target URL to scan
            timeout: Request timeout in seconds
        """
        self.target = target_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def scan(self) -> Dict:
        """
        Perform all quick win security checks
        
        Returns:
            Dict containing scan results
        """
        logger.info(f"Starting quick wins scan for {self.target}")
        
        results = {
            'issues': [],
            'score': 100,
            'checks_performed': 0,
            'issues_found': 0
        }
        
        # 1. Robots.txt Analysis
        robots_results = self.check_robots_txt()
        if robots_results['issues']:
            results['issues'].extend(robots_results['issues'])
        results['checks_performed'] += 1
        
        # 2. Clickjacking Test
        clickjacking_results = self.test_clickjacking()
        if clickjacking_results['vulnerable']:
            results['issues'].append(clickjacking_results)
        results['checks_performed'] += 1
        
        # 3. HTTP Methods Test
        http_methods_results = self.test_http_methods()
        if http_methods_results['issues']:
            results['issues'].extend(http_methods_results['issues'])
        results['checks_performed'] += 1
        
        # 4. Security.txt Check
        security_txt_results = self.check_security_txt()
        if security_txt_results['issue']:
            results['issues'].append(security_txt_results)
        results['checks_performed'] += 1
        
        # Calculate score
        results['issues_found'] = len(results['issues'])
        high_severity = sum(1 for i in results['issues'] if i.get('severity') == 'HIGH')
        medium_severity = sum(1 for i in results['issues'] if i.get('severity') == 'MEDIUM')
        low_severity = sum(1 for i in results['issues'] if i.get('severity') == 'LOW')
        
        results['score'] = max(0, 100 - (high_severity * 20) - (medium_severity * 10) - (low_severity * 5))
        
        logger.info(f"Quick wins scan completed. Issues found: {results['issues_found']}")
        return results
    
    def check_robots_txt(self) -> Dict:
        """
        Analyze robots.txt for sensitive paths disclosure
        
        Returns:
            Dict with robots.txt analysis results
        """
        logger.info("Checking robots.txt")
        
        result = {
            'exists': False,
            'sensitive_paths': [],
            'issues': [],
            'all_paths': []
        }
        
        try:
            parsed = urllib.parse.urlparse(self.target)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            response = self.session.get(robots_url, timeout=self.timeout)
            
            if response.status_code == 200:
                result['exists'] = True
                content = response.text
                
                # Parse Disallow and Allow directives
                for line in content.split('\n'):
                    line = line.strip()
                    
                    if line.startswith('Disallow:') or line.startswith('Allow:'):
                        path = line.split(':', 1)[1].strip()
                        if path and path != '/':
                            result['all_paths'].append(path)
                            
                            # Check for sensitive paths
                            path_lower = path.lower()
                            for indicator in self.SENSITIVE_INDICATORS:
                                if indicator in path_lower:
                                    result['sensitive_paths'].append(path)
                                    break
                
                # Create issues for sensitive paths
                if result['sensitive_paths']:
                    result['issues'].append({
                        'type': 'Information Disclosure',
                        'severity': 'MEDIUM',
                        'description': 'Robots.txt reveals sensitive paths',
                        'paths': result['sensitive_paths'][:10],  # Limit to 10
                        'total_sensitive_paths': len(result['sensitive_paths']),
                        'recommendation': 'Consider if these paths should be disclosed in robots.txt',
                        'impact': 'Attackers may discover sensitive directories and files'
                    })
                
                # Large robots.txt can also be an issue
                if len(result['all_paths']) > 50:
                    result['issues'].append({
                        'type': 'Information Disclosure',
                        'severity': 'LOW',
                        'description': f'Robots.txt contains {len(result["all_paths"])} paths',
                        'recommendation': 'Large robots.txt may reveal site structure',
                        'impact': 'Excessive path disclosure aids reconnaissance'
                    })
            
            return result
            
        except requests.RequestException as e:
            logger.debug(f"Error checking robots.txt: {e}")
            return result
    
    def test_clickjacking(self) -> Dict:
        """
        Test for clickjacking vulnerability
        
        Returns:
            Dict with clickjacking test results
        """
        logger.info("Testing for clickjacking vulnerability")
        
        result = {
            'vulnerable': False,
            'type': 'Clickjacking',
            'severity': 'MEDIUM',
            'protection_headers': {}
        }
        
        try:
            response = self.session.get(self.target, timeout=self.timeout)
            headers = response.headers
            
            # Check X-Frame-Options header
            x_frame_options = headers.get('X-Frame-Options', '').upper()
            result['protection_headers']['X-Frame-Options'] = x_frame_options or 'Not Set'
            
            # Check Content-Security-Policy for frame-ancestors
            csp = headers.get('Content-Security-Policy', '')
            has_frame_ancestors = 'frame-ancestors' in csp.lower()
            result['protection_headers']['CSP frame-ancestors'] = 'Present' if has_frame_ancestors else 'Not Set'
            
            # Determine if vulnerable
            if not x_frame_options and not has_frame_ancestors:
                result['vulnerable'] = True
                result['description'] = 'Site can be loaded in iframes (clickjacking vulnerability)'
                result['evidence'] = 'No X-Frame-Options header and no CSP frame-ancestors directive'
                result['impact'] = 'Attackers can trick users into clicking malicious content'
                result['recommendation'] = 'Add "X-Frame-Options: DENY" or "X-Frame-Options: SAMEORIGIN" header'
            elif x_frame_options in ['ALLOW', 'ALLOWALL']:
                result['vulnerable'] = True
                result['description'] = 'X-Frame-Options set to allow framing'
                result['severity'] = 'LOW'
                result['recommendation'] = 'Change X-Frame-Options to DENY or SAMEORIGIN'
            
            return result
            
        except requests.RequestException as e:
            logger.debug(f"Error testing clickjacking: {e}")
            return result
    
    def test_http_methods(self) -> Dict:
        """
        Test for dangerous HTTP methods enabled
        
        Returns:
            Dict with HTTP methods test results
        """
        logger.info("Testing HTTP methods")
        
        result = {
            'allowed_methods': [],
            'dangerous_methods': [],
            'issues': []
        }
        
        try:
            # Try OPTIONS method first to enumerate allowed methods
            try:
                options_response = self.session.options(self.target, timeout=self.timeout)
                allow_header = options_response.headers.get('Allow', '')
                
                if allow_header:
                    result['allowed_methods'] = [m.strip() for m in allow_header.split(',')]
            except:
                pass
            
            # Test each dangerous method individually
            for method in self.DANGEROUS_METHODS:
                try:
                    response = self.session.request(method, self.target, timeout=self.timeout)
                    
                    # If method returns 200-299 or 3xx, it might be allowed
                    if 200 <= response.status_code < 400:
                        result['dangerous_methods'].append(method)
                        
                        severity = 'HIGH' if method in ['PUT', 'DELETE'] else 'MEDIUM'
                        
                        result['issues'].append({
                            'type': 'Insecure HTTP Method',
                            'severity': severity,
                            'method': method,
                            'status_code': response.status_code,
                            'description': f'Dangerous HTTP method {method} appears to be enabled',
                            'impact': f'{method} method could allow unauthorized modifications' if method in ['PUT', 'DELETE'] else f'{method} method may pose security risks',
                            'recommendation': f'Disable {method} method if not required'
                        })
                
                except requests.RequestException:
                    continue
            
            # Check for TRACE method specifically (can bypass HTTPOnly)
            try:
                trace_response = self.session.request('TRACE', self.target, timeout=self.timeout)
                if 200 <= trace_response.status_code < 400:
                    if 'TRACE' not in result['dangerous_methods']:
                        result['dangerous_methods'].append('TRACE')
                        result['issues'].append({
                            'type': 'HTTP TRACE Method Enabled',
                            'severity': 'MEDIUM',
                            'method': 'TRACE',
                            'description': 'TRACE method is enabled (Cross-Site Tracing vulnerability)',
                            'impact': 'Can be used to bypass HTTPOnly cookie protection',
                            'recommendation': 'Disable TRACE method on the web server'
                        })
            except:
                pass
            
            return result
            
        except Exception as e:
            logger.debug(f"Error testing HTTP methods: {e}")
            return result
    
    def check_security_txt(self) -> Dict:
        """
        Check for security.txt file (RFC 9116)
        
        Returns:
            Dict with security.txt check results
        """
        logger.info("Checking for security.txt")
        
        result = {
            'exists': False,
            'location': None,
            'contacts': [],
            'issue': None
        }
        
        try:
            parsed = urllib.parse.urlparse(self.target)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Check both locations (RFC 9116 specifies /.well-known/)
            locations = [
                f"{base_url}/.well-known/security.txt",
                f"{base_url}/security.txt"
            ]
            
            for location in locations:
                try:
                    response = self.session.get(location, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        result['exists'] = True
                        result['location'] = location
                        
                        # Parse security.txt
                        for line in response.text.split('\n'):
                            line = line.strip()
                            if line.startswith('Contact:'):
                                contact = line.split(':', 1)[1].strip()
                                result['contacts'].append(contact)
                        
                        break
                except:
                    continue
            
            # Create issue if security.txt doesn't exist
            if not result['exists']:
                result['issue'] = {
                    'type': 'Missing security.txt',
                    'severity': 'LOW',
                    'description': 'No security.txt file found',
                    'recommendation': 'Consider adding a security.txt file to help security researchers contact you',
                    'impact': 'Researchers may have difficulty reporting vulnerabilities responsibly',
                    'reference': 'https://securitytxt.org/'
                }
            
            return result
            
        except Exception as e:
            logger.debug(f"Error checking security.txt: {e}")
            return result

