"""
Port Scanner Module
Scans common ports and identifies open services
"""

import socket
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

logger = logging.getLogger(__name__)


class PortScanner:
    """Port scanner for network security assessment"""
    
    # Common ports to scan
    COMMON_PORTS = {
        21: 'FTP',
        22: 'SSH',
        23: 'Telnet',
        25: 'SMTP',
        53: 'DNS',
        80: 'HTTP',
        110: 'POP3',
        143: 'IMAP',
        443: 'HTTPS',
        445: 'SMB',
        3306: 'MySQL',
        3389: 'RDP',
        5432: 'PostgreSQL',
        5900: 'VNC',
        6379: 'Redis',
        8080: 'HTTP-Alt',
        8443: 'HTTPS-Alt',
        27017: 'MongoDB'
    }
    
    RISKY_PORTS = [21, 23, 445, 3389, 5900]  # Ports that are commonly exploited
    
    def __init__(self, target, timeout=2):
        self.target = target
        self.timeout = timeout
        self.open_ports = []
        self.closed_ports = []
        
    def scan(self, ports=None):
        """Perform port scan"""
        if ports is None:
            ports = list(self.COMMON_PORTS.keys())
        
        logger.info(f"Scanning {len(ports)} ports on {self.target}")
        
        results = {
            'target': self.target,
            'scan_time': datetime.utcnow().isoformat(),
            'open_ports': [],
            'total_scanned': len(ports),
            'issues': [],
            'score': 100
        }
        
        try:
            # Scan ports concurrently
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_port = {
                    executor.submit(self._scan_port, port): port 
                    for port in ports
                }
                
                for future in as_completed(future_to_port):
                    port = future_to_port[future]
                    try:
                        is_open, service = future.result()
                        if is_open:
                            port_info = {
                                'port': port,
                                'service': service,
                                'state': 'open'
                            }
                            results['open_ports'].append(port_info)
                            
                            # Check if it's a risky port
                            if port in self.RISKY_PORTS:
                                results['issues'].append({
                                    'severity': 'high',
                                    'port': port,
                                    'service': service,
                                    'description': f'Potentially risky port {port} ({service}) is open'
                                })
                    except Exception as e:
                        logger.error(f"Error scanning port {port}: {str(e)}")
            
            # Calculate score based on findings
            results['score'] = self._calculate_port_score(results)
            results['summary'] = f"Found {len(results['open_ports'])} open ports"
            
            return results
            
        except Exception as e:
            logger.error(f"Port scan error: {str(e)}")
            return {
                'error': str(e),
                'score': 50
            }
    
    def _scan_port(self, port):
        """Scan a single port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.target, port))
            sock.close()
            
            if result == 0:
                service = self.COMMON_PORTS.get(port, 'Unknown')
                return True, service
            return False, None
            
        except socket.gaierror:
            logger.error(f"Hostname could not be resolved: {self.target}")
            return False, None
        except socket.error as e:
            logger.error(f"Could not connect to {self.target}:{port} - {str(e)}")
            return False, None
    
    def _calculate_port_score(self, results):
        """Calculate security score based on open ports"""
        score = 100
        
        # Deduct points for risky ports
        for issue in results['issues']:
            if issue['severity'] == 'high':
                score -= 15
            elif issue['severity'] == 'medium':
                score -= 10
        
        # Deduct points for too many open ports
        open_count = len(results['open_ports'])
        if open_count > 10:
            score -= 10
        elif open_count > 5:
            score -= 5
        
        return max(0, score)

