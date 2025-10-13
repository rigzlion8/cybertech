"""
Cross-Site Scripting (XSS) Scanner Module
Detects reflected, stored, and DOM-based XSS vulnerabilities
"""

import logging
import re
import urllib.parse
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import hashlib

logger = logging.getLogger(__name__)


class XSSScanner:
    """Cross-Site Scripting vulnerability scanner"""
    
    # XSS payloads for different contexts
    XSS_PAYLOADS = [
        # Basic payloads
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        '<svg/onload=alert("XSS")>',
        '<iframe src="javascript:alert(\'XSS\')">',
        
        # Event handler payloads
        '" onclick="alert(\'XSS\')"',
        '\' onmouseover="alert(\'XSS\')"',
        '<body onload=alert("XSS")>',
        '<input onfocus=alert("XSS") autofocus>',
        
        # JavaScript context
        '";alert("XSS");//',
        '\';alert("XSS");//',
        '</script><script>alert("XSS")</script>',
        
        # Filter evasion
        '<scr<script>ipt>alert("XSS")</scr</script>ipt>',
        '<img src="x" onerror="&#97;&#108;&#101;&#114;&#116;&#40;&#39;&#88;&#83;&#83;&#39;&#41;">',
        '<svg><script>alert&#40"XSS"&#41</script>',
        
        # Advanced payloads
        '<details open ontoggle=alert("XSS")>',
        '<marquee onstart=alert("XSS")>',
        '<div style="width:expression(alert(\'XSS\'))">',
        'javascript:alert("XSS")',
        
        # Encoded payloads
        '%3Cscript%3Ealert("XSS")%3C/script%3E',
        '&lt;script&gt;alert("XSS")&lt;/script&gt;',
    ]
    
    # DOM-based XSS sinks
    DOM_SINKS = [
        'document.write',
        'document.writeln',
        'innerHTML',
        'outerHTML',
        'eval(',
        'setTimeout(',
        'setInterval(',
        'Function(',
        'location.href',
        'location.replace',
    ]
    
    def __init__(self, target_url, timeout=10):
        """
        Initialize XSS Scanner
        
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
        self.tested_payloads = set()
        
    def scan(self) -> Dict:
        """
        Perform comprehensive XSS scan
        
        Returns:
            Dict containing scan results
        """
        logger.info(f"Starting XSS scan for {self.target}")
        
        try:
            results = {
                'vulnerable': False,
                'vulnerabilities': [],
                'injection_points': [],
                'score': 100,
                'risk_level': 'LOW',
                'details': {}
            }
            
            # Find injectable parameters
            forms = self._find_forms()
            url_params = self._extract_url_parameters()
            
            # Test URL parameters
            if url_params:
                logger.info(f"Testing {len(url_params)} URL parameters for XSS")
                for param in url_params:
                    vulns = self._test_reflected_xss_param(param)
                    if vulns:
                        results['vulnerabilities'].extend(vulns)
                        results['injection_points'].append(f"URL parameter: {param}")
            
            # Test forms
            if forms:
                logger.info(f"Testing {len(forms)} forms for XSS")
                for form in forms:
                    vulns = self._test_reflected_xss_form(form)
                    if vulns:
                        results['vulnerabilities'].extend(vulns)
                        results['injection_points'].append(f"Form: {form.get('action', 'inline')}")
            
            # Check for DOM-based XSS
            dom_vulns = self._test_dom_xss()
            if dom_vulns:
                results['vulnerabilities'].extend(dom_vulns)
                results['injection_points'].append("DOM manipulation")
            
            # Update results
            if results['vulnerabilities']:
                results['vulnerable'] = True
                
                # Calculate score
                critical_count = sum(1 for v in results['vulnerabilities'] if v['severity'] == 'CRITICAL')
                high_count = sum(1 for v in results['vulnerabilities'] if v['severity'] == 'HIGH')
                medium_count = sum(1 for v in results['vulnerabilities'] if v['severity'] == 'MEDIUM')
                
                results['score'] = max(0, 100 - (critical_count * 30) - (high_count * 20) - (medium_count * 10))
                
                if critical_count > 0:
                    results['risk_level'] = 'CRITICAL'
                elif high_count > 0:
                    results['risk_level'] = 'HIGH'
                else:
                    results['risk_level'] = 'MEDIUM'
            
            results['details'] = {
                'forms_tested': len(forms),
                'parameters_tested': len(url_params),
                'payloads_tested': len(self.tested_payloads),
            }
            
            logger.info(f"XSS scan completed. Vulnerable: {results['vulnerable']}")
            return results
            
        except Exception as e:
            logger.error(f"XSS scan error: {str(e)}")
            return {
                'vulnerable': False,
                'vulnerabilities': [],
                'score': 50,
                'error': str(e)
            }
    
    def _find_forms(self) -> List[Dict]:
        """Find all forms on the target page"""
        try:
            response = self.session.get(self.target, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            forms = []
            for form in soup.find_all('form'):
                form_data = {
                    'action': form.get('action', ''),
                    'method': form.get('method', 'get').upper(),
                    'inputs': []
                }
                
                for input_tag in form.find_all(['input', 'textarea']):
                    input_name = input_tag.get('name')
                    input_type = input_tag.get('type', 'text')
                    if input_name:
                        form_data['inputs'].append({
                            'name': input_name,
                            'type': input_type
                        })
                
                if form_data['inputs']:
                    forms.append(form_data)
            
            return forms
            
        except Exception as e:
            logger.error(f"Error finding forms: {e}")
            return []
    
    def _extract_url_parameters(self) -> List[str]:
        """Extract parameters from URL"""
        try:
            parsed = urllib.parse.urlparse(self.target)
            params = urllib.parse.parse_qs(parsed.query)
            return list(params.keys())
        except Exception:
            return []
    
    def _test_reflected_xss_param(self, param: str) -> List[Dict]:
        """Test URL parameter for reflected XSS"""
        vulnerabilities = []
        
        try:
            parsed = urllib.parse.urlparse(self.target)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Test a subset of payloads
            for payload in self.XSS_PAYLOADS[:10]:
                # Create unique marker
                marker = hashlib.md5(payload.encode()).hexdigest()[:8]
                marked_payload = payload.replace('XSS', marker)
                
                # Inject payload
                test_params = params.copy()
                test_params[param] = [marked_payload]
                
                test_url = urllib.parse.urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urllib.parse.urlencode(test_params, doseq=True),
                    parsed.fragment
                ))
                
                response = self.session.get(test_url, timeout=self.timeout)
                self.tested_payloads.add(payload)
                
                # Check if payload is reflected unescaped
                if self._check_xss_reflection(response.text, marked_payload, marker):
                    context = self._detect_injection_context(response.text, marked_payload)
                    
                    vulnerabilities.append({
                        'type': 'Cross-Site Scripting (Reflected)',
                        'severity': 'HIGH',
                        'location': 'url_parameter',
                        'parameter': param,
                        'payload': payload,
                        'context': context,
                        'description': f'Reflected XSS vulnerability in URL parameter "{param}"',
                        'evidence': f'Payload reflected in {context} context',
                        'impact': 'Attackers can execute arbitrary JavaScript in victim browsers'
                    })
                    
                    # Found vulnerability, no need to test more payloads for this param
                    break
            
            return vulnerabilities
            
        except Exception as e:
            logger.debug(f"Error testing XSS on parameter {param}: {e}")
            return []
    
    def _test_reflected_xss_form(self, form: Dict) -> List[Dict]:
        """Test form for reflected XSS"""
        vulnerabilities = []
        
        try:
            # Build form action URL
            action = form['action']
            if not action.startswith('http'):
                parsed = urllib.parse.urlparse(self.target)
                if action.startswith('/'):
                    action = f"{parsed.scheme}://{parsed.netloc}{action}"
                else:
                    action = urllib.parse.urljoin(self.target, action)
            
            # Test each input field
            for input_field in form['inputs']:
                if input_field['type'] in ['submit', 'button', 'reset', 'file']:
                    continue
                
                # Test a subset of payloads
                for payload in self.XSS_PAYLOADS[:8]:
                    marker = hashlib.md5(payload.encode()).hexdigest()[:8]
                    marked_payload = payload.replace('XSS', marker)
                    
                    # Build form data
                    form_data = {inp['name']: 'test' for inp in form['inputs']}
                    form_data[input_field['name']] = marked_payload
                    
                    if form['method'] == 'POST':
                        response = self.session.post(action, data=form_data, timeout=self.timeout)
                    else:
                        response = self.session.get(action, params=form_data, timeout=self.timeout)
                    
                    self.tested_payloads.add(payload)
                    
                    # Check for reflection
                    if self._check_xss_reflection(response.text, marked_payload, marker):
                        context = self._detect_injection_context(response.text, marked_payload)
                        
                        vulnerabilities.append({
                            'type': 'Cross-Site Scripting (Reflected)',
                            'severity': 'HIGH',
                            'location': 'form',
                            'parameter': input_field['name'],
                            'payload': payload,
                            'context': context,
                            'description': f'Reflected XSS vulnerability in form field "{input_field["name"]}"',
                            'evidence': f'Payload reflected in {context} context',
                            'impact': 'Attackers can execute arbitrary JavaScript in victim browsers'
                        })
                        
                        break  # Found vulnerability, move to next field
            
            return vulnerabilities
            
        except Exception as e:
            logger.debug(f"Error testing XSS on form: {e}")
            return []
    
    def _test_dom_xss(self) -> List[Dict]:
        """Test for DOM-based XSS vulnerabilities"""
        vulnerabilities = []
        
        try:
            response = self.session.get(self.target, timeout=self.timeout)
            
            # Look for dangerous DOM sinks in JavaScript
            for sink in self.DOM_SINKS:
                if sink in response.text:
                    # Check if user input flows to this sink
                    if self._check_user_input_to_sink(response.text, sink):
                        vulnerabilities.append({
                            'type': 'Cross-Site Scripting (DOM-based)',
                            'severity': 'MEDIUM',
                            'location': 'client_side',
                            'sink': sink,
                            'description': f'Potential DOM-based XSS via {sink}',
                            'evidence': f'Found dangerous sink: {sink}',
                            'impact': 'User input may be processed unsafely in client-side JavaScript',
                            'recommendation': f'Sanitize data before passing to {sink}'
                        })
            
            # Check for location.hash or location.search usage
            if re.search(r'location\.(hash|search)', response.text):
                vulnerabilities.append({
                    'type': 'Cross-Site Scripting (DOM-based)',
                    'severity': 'MEDIUM',
                    'location': 'client_side',
                    'description': 'URL fragments used in client-side code',
                    'evidence': 'location.hash or location.search found in JavaScript',
                    'impact': 'URL parameters may be processed unsafely',
                    'recommendation': 'Validate and sanitize URL parameters before use'
                })
            
            return vulnerabilities
            
        except Exception as e:
            logger.debug(f"Error testing DOM XSS: {e}")
            return []
    
    def _check_xss_reflection(self, response_text: str, payload: str, marker: str) -> bool:
        """
        Check if XSS payload is reflected unescaped
        
        Args:
            response_text: HTTP response text
            payload: XSS payload
            marker: Unique marker in payload
            
        Returns:
            True if payload is reflected unescaped
        """
        # Check if marker is present (payload was reflected)
        if marker not in response_text:
            return False
        
        # Check if dangerous characters are unescaped
        dangerous_chars = ['<', '>', '"', "'", 'script', 'onerror', 'onload']
        
        # Extract context around marker
        marker_pos = response_text.find(marker)
        context_start = max(0, marker_pos - 50)
        context_end = min(len(response_text), marker_pos + 50)
        context = response_text[context_start:context_end]
        
        # Check if dangerous characters are present unescaped
        for char in dangerous_chars:
            if char in context.lower():
                return True
        
        return False
    
    def _detect_injection_context(self, response_text: str, payload: str) -> str:
        """
        Detect the context where payload was injected
        
        Returns:
            Context type (HTML, JavaScript, Attribute, etc.)
        """
        payload_pos = response_text.find(payload)
        if payload_pos == -1:
            return 'unknown'
        
        # Extract surrounding context
        context_start = max(0, payload_pos - 100)
        context_end = min(len(response_text), payload_pos + 100)
        context = response_text[context_start:context_end]
        
        # Detect context type
        if re.search(r'<script[^>]*>.*' + re.escape(payload), context, re.IGNORECASE):
            return 'JavaScript'
        elif re.search(r'<[^>]+' + re.escape(payload) + r'[^>]*>', context):
            return 'HTML Attribute'
        elif '<' in context[:50] and '>' in context[-50:]:
            return 'HTML'
        else:
            return 'Plain Text'
    
    def _check_user_input_to_sink(self, javascript_code: str, sink: str) -> bool:
        """
        Check if user input flows to dangerous sink
        
        Args:
            javascript_code: JavaScript code to analyze
            sink: Dangerous sink function
            
        Returns:
            True if user input likely flows to sink
        """
        # Common user input sources in JavaScript
        input_sources = [
            'location.hash',
            'location.search',
            'document.URL',
            'document.documentURI',
            'document.referrer',
            'window.name',
            'document.cookie',
        ]
        
        # Simple heuristic: check if input source and sink appear close together
        sink_pos = javascript_code.find(sink)
        if sink_pos == -1:
            return False
        
        # Check 200 characters before sink
        context_start = max(0, sink_pos - 200)
        context = javascript_code[context_start:sink_pos + 50]
        
        for source in input_sources:
            if source in context:
                return True
        
        return False

