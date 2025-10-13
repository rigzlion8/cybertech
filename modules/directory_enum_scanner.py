"""
Directory and File Enumeration Scanner Module
Discovers sensitive files, directories, and admin panels
"""

import logging
import urllib.parse
from typing import Dict, List, Set
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class DirectoryEnumerationScanner:
    """Directory and file enumeration scanner"""
    
    # Sensitive files to check
    SENSITIVE_FILES = [
        # Version control
        '.git/HEAD',
        '.git/config',
        '.gitignore',
        '.svn/entries',
        '.hg/requires',
        
        # Configuration files
        '.env',
        '.env.local',
        '.env.production',
        'config.php',
        'configuration.php',
        'database.yml',
        'db.php',
        'settings.php',
        'wp-config.php',
        'web.config',
        'app.config',
        'config.json',
        'config.xml',
        
        # Backup files
        'backup.zip',
        'backup.sql',
        'backup.tar.gz',
        'database.sql',
        'dump.sql',
        'site.tar.gz',
        'www.zip',
        'backup.bak',
        
        # Database files
        'database.db',
        'db.sqlite',
        'data.db',
        
        # Log files
        'error.log',
        'access.log',
        'debug.log',
        'application.log',
        'error_log',
        
        # Development files
        'composer.json',
        'package.json',
        'package-lock.json',
        'yarn.lock',
        'Gemfile',
        'requirements.txt',
        'phpinfo.php',
        'test.php',
        'info.php',
        
        # System files
        '.DS_Store',
        'Thumbs.db',
        'desktop.ini',
        '.htaccess',
        '.htpasswd',
        
        # Documentation
        'README.md',
        'CHANGELOG.md',
        'TODO.txt',
        'notes.txt',
        
        # API/Swagger
        'swagger.json',
        'swagger.yaml',
        'openapi.json',
        'api-docs.json',
    ]
    
    # Admin panels and sensitive directories
    ADMIN_PATHS = [
        'admin',
        'administrator',
        'admin.php',
        'admin/',
        'administrator/',
        'wp-admin',
        'wp-admin/',
        'phpmyadmin',
        'phpmyadmin/',
        'pma',
        'mysql',
        'cpanel',
        'cpanel/',
        'plesk',
        'webmail',
        'panel',
        'dashboard',
        'dashboard/',
        'console',
        'console/',
        'manager',
        'backend',
        'backend/',
        'controlpanel',
        'adminpanel',
        'user/admin',
        'admin/login',
        'admin-login',
        'login/admin',
    ]
    
    # Common directories
    COMMON_DIRS = [
        'backup',
        'backups',
        'old',
        'temp',
        'tmp',
        'cache',
        'logs',
        'log',
        'test',
        'tests',
        'dev',
        'development',
        'staging',
        'beta',
        'demo',
        'private',
        'secret',
        'hidden',
        'internal',
        'files',
        'uploads',
        'images',
        'assets',
        'includes',
        'inc',
        'src',
        'lib',
        'data',
        'db',
        'sql',
        'api',
    ]
    
    def __init__(self, target_url, timeout=5, max_threads=10):
        """
        Initialize Directory Enumeration Scanner
        
        Args:
            target_url: Target URL to scan
            timeout: Request timeout in seconds
            max_threads: Maximum concurrent threads
        """
        self.target = target_url
        self.timeout = timeout
        self.max_threads = max_threads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.found_items: Set[str] = set()
        
    def scan(self) -> Dict:
        """
        Perform directory enumeration scan
        
        Returns:
            Dict containing scan results
        """
        logger.info(f"Starting directory enumeration for {self.target}")
        
        results = {
            'sensitive_files_found': [],
            'admin_panels_found': [],
            'directories_found': [],
            'total_found': 0,
            'score': 100,
            'risk_level': 'LOW'
        }
        
        # Check for sensitive files
        logger.info(f"Scanning for {len(self.SENSITIVE_FILES)} sensitive files...")
        sensitive_files = self._check_files(self.SENSITIVE_FILES)
        results['sensitive_files_found'] = sensitive_files
        
        # Check for admin panels
        logger.info(f"Scanning for {len(self.ADMIN_PATHS)} admin panels...")
        admin_panels = self._check_paths(self.ADMIN_PATHS, is_admin=True)
        results['admin_panels_found'] = admin_panels
        
        # Check for common directories (limited scan)
        logger.info(f"Scanning for common directories...")
        directories = self._check_paths(self.COMMON_DIRS[:20], is_directory=True)  # Limit to 20
        results['directories_found'] = directories
        
        # Calculate total and score
        results['total_found'] = len(sensitive_files) + len(admin_panels) + len(directories)
        
        # Scoring based on what was found
        critical_files = ['env', 'config', 'database', '.git']
        critical_count = sum(1 for f in sensitive_files if any(c in f['path'].lower() for c in critical_files))
        
        if critical_count > 0:
            results['score'] = max(0, 100 - (critical_count * 30))
            results['risk_level'] = 'CRITICAL'
        elif len(admin_panels) > 0:
            results['score'] = max(0, 100 - (len(admin_panels) * 15))
            results['risk_level'] = 'HIGH'
        elif len(sensitive_files) > 0:
            results['score'] = max(0, 100 - (len(sensitive_files) * 10))
            results['risk_level'] = 'MEDIUM'
        
        logger.info(f"Directory enumeration completed. Found {results['total_found']} items")
        return results
    
    def _check_files(self, file_list: List[str]) -> List[Dict]:
        """
        Check for existence of sensitive files
        
        Args:
            file_list: List of file paths to check
            
        Returns:
            List of found files with details
        """
        found_files = []
        parsed = urllib.parse.urlparse(self.target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {}
            for file_path in file_list:
                url = urllib.parse.urljoin(base_url + '/', file_path)
                future = executor.submit(self._check_url, url, file_path)
                futures[future] = file_path
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found_files.append(result)
                    self.found_items.add(result['path'])
        
        return found_files
    
    def _check_paths(self, path_list: List[str], is_admin=False, is_directory=False) -> List[Dict]:
        """
        Check for existence of paths (admin panels or directories)
        
        Args:
            path_list: List of paths to check
            is_admin: Whether these are admin panel paths
            is_directory: Whether these are directory paths
            
        Returns:
            List of found paths with details
        """
        found_paths = []
        parsed = urllib.parse.urlparse(self.target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {}
            for path in path_list:
                url = urllib.parse.urljoin(base_url + '/', path)
                future = executor.submit(self._check_url, url, path, is_admin, is_directory)
                futures[future] = path
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found_paths.append(result)
                    self.found_items.add(result['path'])
        
        return found_paths
    
    def _check_url(self, url: str, path: str, is_admin=False, is_directory=False) -> Dict:
        """
        Check if a URL exists and is accessible
        
        Args:
            url: Full URL to check
            path: Relative path
            is_admin: Whether this is an admin panel
            is_directory: Whether this is a directory
            
        Returns:
            Dict with details if found, None otherwise
        """
        try:
            # Use HEAD request first (faster)
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            # If HEAD fails, try GET
            if response.status_code >= 400:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=False)
            
            # Consider it found if status is 200-399
            if 200 <= response.status_code < 400:
                result = {
                    'path': path,
                    'url': url,
                    'status_code': response.status_code,
                    'size': len(response.content) if hasattr(response, 'content') else 0,
                }
                
                # Determine severity and type
                if is_admin:
                    result['type'] = 'Admin Panel'
                    result['severity'] = 'HIGH'
                    result['description'] = f'Admin panel accessible at {path}'
                    result['recommendation'] = 'Ensure admin panel is properly protected with strong authentication'
                elif path.endswith(('.git', '.env', 'config', 'database')):
                    result['type'] = 'Critical File'
                    result['severity'] = 'CRITICAL'
                    result['description'] = f'Critical file exposed: {path}'
                    result['recommendation'] = 'Remove or restrict access to this file immediately'
                elif path.endswith(('.log', '.sql', '.bak', '.backup')):
                    result['type'] = 'Sensitive File'
                    result['severity'] = 'HIGH'
                    result['description'] = f'Sensitive file exposed: {path}'
                    result['recommendation'] = 'Remove or restrict access to backup/log files'
                elif is_directory:
                    result['type'] = 'Directory'
                    result['severity'] = 'MEDIUM'
                    result['description'] = f'Directory listing or accessible directory: {path}'
                    result['recommendation'] = 'Review if this directory should be publicly accessible'
                else:
                    result['type'] = 'File'
                    result['severity'] = 'MEDIUM'
                    result['description'] = f'File found: {path}'
                    result['recommendation'] = 'Review if this file should be publicly accessible'
                
                return result
            
            return None
            
        except requests.RequestException as e:
            logger.debug(f"Error checking {url}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error checking {url}: {e}")
            return None
    
    def scan_specific_paths(self, custom_paths: List[str]) -> List[Dict]:
        """
        Scan for custom/specific paths
        
        Args:
            custom_paths: List of custom paths to check
            
        Returns:
            List of found items
        """
        logger.info(f"Scanning {len(custom_paths)} custom paths")
        return self._check_paths(custom_paths)

