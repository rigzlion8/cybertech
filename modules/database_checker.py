"""
Database Security Checker Module
Checks database security and configuration
"""

import logging
import re
import requests
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class DatabaseChecker:
    """Database security checker"""
    
    # Common database error patterns
    DB_ERRORS = {
        'mysql': [
            r"You have an error in your SQL syntax",
            r"MySQL server version",
            r"mysql_fetch",
            r"MySQLSyntaxErrorException"
        ],
        'postgresql': [
            r"PostgreSQL.*ERROR",
            r"pg_query\(\)",
            r"pg_exec\(\)",
            r"Npgsql\."
        ],
        'mssql': [
            r"Microsoft SQL Native Client",
            r"ODBC SQL Server Driver",
            r"SQLServer JDBC Driver",
            r"\[SQL Server\]"
        ],
        'oracle': [
            r"ORA-[0-9]+",
            r"Oracle.*Driver",
            r"oracle\.jdbc"
        ],
        'mongodb': [
            r"MongoException",
            r"mongodb://",
            r"mongo\.error"
        ]
    }
    
    def __init__(self, target, timeout=10):
        self.target = target
        self.timeout = timeout
        
    def check(self):
        """Perform database security checks"""
        results = {
            'target': self.target,
            'database_type': None,
            'exposed_errors': [],
            'security_issues': [],
            'recommendations': [],
            'score': 100
        }
        
        try:
            # Check for database error exposure
            db_type, errors = self._check_error_exposure()
            
            if db_type:
                results['database_type'] = db_type
                results['exposed_errors'] = errors
                results['security_issues'].append({
                    'severity': 'high',
                    'issue': f'{db_type} database errors exposed',
                    'description': 'Database error messages are visible to users'
                })
            
            # Check for database connection strings in source
            conn_strings = self._check_connection_strings()
            if conn_strings:
                results['security_issues'].append({
                    'severity': 'critical',
                    'issue': 'Database connection strings exposed',
                    'description': 'Connection strings found in client-side code'
                })
                results['exposed_connection_strings'] = True
            
            # Check for NoSQL injection vulnerabilities
            nosql_vulns = self._check_nosql_injection()
            if nosql_vulns:
                results['security_issues'].extend(nosql_vulns)
            
            # General recommendations
            results['recommendations'] = [
                {
                    'priority': 'high',
                    'recommendation': 'Use parameterized queries to prevent SQL injection'
                },
                {
                    'priority': 'high',
                    'recommendation': 'Disable detailed error messages in production'
                },
                {
                    'priority': 'medium',
                    'recommendation': 'Implement proper database access controls'
                },
                {
                    'priority': 'medium',
                    'recommendation': 'Encrypt sensitive data at rest'
                },
                {
                    'priority': 'low',
                    'recommendation': 'Regular database security audits'
                }
            ]
            
            # Calculate score
            results['score'] = self._calculate_db_score(results)
            results['summary'] = f"Database security check completed with {len(results['security_issues'])} issues"
            
            return results
            
        except Exception as e:
            logger.error(f"Database check error: {str(e)}")
            return {
                'error': str(e),
                'score': 50
            }
    
    def _check_error_exposure(self):
        """Check for exposed database errors"""
        try:
            # Try to trigger an error with invalid input
            test_payloads = ["'", "\"", "1'", "1\""]
            
            for payload in test_payloads:
                parsed_url = urlparse(self.target)
                params = parse_qs(parsed_url.query)
                
                if params:
                    # Add payload to first parameter
                    first_param = list(params.keys())[0]
                    params[first_param] = payload
                    
                    response = requests.get(
                        f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}",
                        params=params,
                        timeout=self.timeout
                    )
                    
                    # Check for database error patterns
                    for db_type, patterns in self.DB_ERRORS.items():
                        for pattern in patterns:
                            if re.search(pattern, response.text, re.IGNORECASE):
                                return db_type, [pattern]
            
            return None, []
            
        except Exception as e:
            logger.error(f"Error exposure check failed: {str(e)}")
            return None, []
    
    def _check_connection_strings(self):
        """Check for exposed database connection strings"""
        connection_patterns = [
            r"mongodb://[^'\"\s]+",
            r"mysql://[^'\"\s]+",
            r"postgresql://[^'\"\s]+",
            r"Server=.+;Database=.+;",
            r"Data Source=.+;Initial Catalog=.+;"
        ]
        
        try:
            response = requests.get(self.target, timeout=self.timeout)
            
            found_strings = []
            for pattern in connection_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    found_strings.extend(matches)
            
            return found_strings
            
        except Exception as e:
            logger.error(f"Connection string check error: {str(e)}")
            return []
    
    def _check_nosql_injection(self):
        """Check for NoSQL injection vulnerabilities"""
        vulnerabilities = []
        
        # NoSQL injection payloads
        nosql_payloads = [
            '{"$gt":""}',
            '{"$ne":null}',
            '{"$regex":".*"}'
        ]
        
        try:
            parsed_url = urlparse(self.target)
            params = parse_qs(parsed_url.query)
            
            for param in params:
                for payload in nosql_payloads:
                    test_params = params.copy()
                    test_params[param] = payload
                    
                    try:
                        response = requests.get(
                            f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}",
                            params=test_params,
                            timeout=self.timeout
                        )
                        
                        # Check for MongoDB errors or suspicious behavior
                        if 'mongo' in response.text.lower() or 'bson' in response.text.lower():
                            vulnerabilities.append({
                                'severity': 'high',
                                'issue': f'Possible NoSQL injection in parameter: {param}',
                                'description': 'Parameter may be vulnerable to NoSQL injection'
                            })
                            break
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"NoSQL injection check error: {str(e)}")
        
        return vulnerabilities
    
    def _calculate_db_score(self, results):
        """Calculate database security score"""
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

