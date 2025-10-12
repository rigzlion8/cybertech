"""
Password Security Checker Module
Checks for password breaches and encryption
"""

import requests
import hashlib
import logging
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PasswordChecker:
    """Password security checker"""
    
    HIBP_API = "https://api.pwnedpasswords.com/range/"
    
    def __init__(self, target, timeout=10):
        self.target = target
        self.timeout = timeout
        
    def check(self):
        """Perform password security checks"""
        results = {
            'target': self.target,
            'password_fields': [],
            'security_issues': [],
            'recommendations': [],
            'score': 100
        }
        
        try:
            # Check for password fields
            password_fields = self._find_password_fields()
            results['password_fields'] = password_fields
            
            # Check if passwords are transmitted over HTTPS
            parsed_url = urlparse(self.target)
            if parsed_url.scheme != 'https':
                results['security_issues'].append({
                    'severity': 'critical',
                    'issue': 'Passwords transmitted over HTTP',
                    'description': 'Login forms should only be served over HTTPS'
                })
            
            # Check for password policy indicators
            policy_check = self._check_password_policy()
            results['password_policy'] = policy_check
            
            if not policy_check.get('has_policy_indicators'):
                results['security_issues'].append({
                    'severity': 'medium',
                    'issue': 'No visible password policy',
                    'description': 'No password requirements displayed to users'
                })
            
            # Check for autocomplete on password fields
            autocomplete_issues = self._check_autocomplete(password_fields)
            if autocomplete_issues:
                results['security_issues'].extend(autocomplete_issues)
            
            # Check for password visibility toggle
            if not self._has_password_visibility_toggle(password_fields):
                results['recommendations'].append({
                    'priority': 'low',
                    'recommendation': 'Add password visibility toggle for better UX'
                })
            
            # Calculate score
            results['score'] = self._calculate_password_score(results)
            results['summary'] = f"Found {len(password_fields)} password fields with {len(results['security_issues'])} issues"
            
            return results
            
        except Exception as e:
            logger.error(f"Password check error: {str(e)}")
            return {
                'error': str(e),
                'score': 50
            }
    
    def check_breach(self, password):
        """
        Check if password has been breached using Have I Been Pwned API
        Uses k-anonymity model - only sends first 5 chars of hash
        """
        try:
            # Hash the password
            sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]
            
            # Query HIBP API
            response = requests.get(
                f"{self.HIBP_API}{prefix}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # Check if hash suffix is in response
                hashes = response.text.splitlines()
                for line in hashes:
                    hash_suffix, count = line.split(':')
                    if hash_suffix == suffix:
                        return {
                            'breached': True,
                            'breach_count': int(count),
                            'severity': 'critical'
                        }
                
                return {
                    'breached': False,
                    'breach_count': 0
                }
            else:
                return {
                    'error': 'Unable to check password breach',
                    'breached': None
                }
                
        except Exception as e:
            logger.error(f"Password breach check error: {str(e)}")
            return {
                'error': str(e),
                'breached': None
            }
    
    def _find_password_fields(self):
        """Find password input fields on the page"""
        password_fields = []
        
        try:
            response = requests.get(self.target, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find password input fields
            password_inputs = soup.find_all('input', {'type': 'password'})
            
            for input_field in password_inputs:
                field_info = {
                    'name': input_field.get('name', 'unnamed'),
                    'id': input_field.get('id', ''),
                    'autocomplete': input_field.get('autocomplete', ''),
                    'required': input_field.has_attr('required'),
                    'form': input_field.find_parent('form').get('action', '') if input_field.find_parent('form') else ''
                }
                password_fields.append(field_info)
                
        except Exception as e:
            logger.error(f"Error finding password fields: {str(e)}")
        
        return password_fields
    
    def _check_password_policy(self):
        """Check for password policy indicators"""
        try:
            response = requests.get(self.target, timeout=self.timeout)
            
            # Look for password policy keywords
            policy_keywords = [
                'password must',
                'minimum length',
                'at least',
                'uppercase',
                'lowercase',
                'special character',
                'number',
                'digit'
            ]
            
            has_policy = any(keyword in response.text.lower() for keyword in policy_keywords)
            
            return {
                'has_policy_indicators': has_policy,
                'found_keywords': [kw for kw in policy_keywords if kw in response.text.lower()]
            }
            
        except Exception as e:
            logger.error(f"Password policy check error: {str(e)}")
            return {'has_policy_indicators': False}
    
    def _check_autocomplete(self, password_fields):
        """Check autocomplete settings on password fields"""
        issues = []
        
        for field in password_fields:
            autocomplete = field.get('autocomplete', '').lower()
            
            # Check if autocomplete is not properly disabled
            if autocomplete not in ['off', 'new-password', 'current-password']:
                issues.append({
                    'severity': 'low',
                    'issue': f'Autocomplete not properly configured for field: {field["name"]}',
                    'description': 'Password fields should use appropriate autocomplete values'
                })
        
        return issues
    
    def _has_password_visibility_toggle(self, password_fields):
        """Check if password visibility toggle is present"""
        try:
            response = requests.get(self.target, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for common patterns of password visibility toggles
            toggle_patterns = [
                'show password',
                'hide password',
                'toggle password',
                'eye icon'
            ]
            
            return any(pattern in response.text.lower() for pattern in toggle_patterns)
            
        except:
            return False
    
    def _calculate_password_score(self, results):
        """Calculate password security score"""
        score = 100
        
        for issue in results['security_issues']:
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

