"""
Scan Storage Module
Handles persistence of scan metadata and results
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ScanStorage:
    """Storage handler for scan metadata and results"""
    
    def __init__(self, storage_path='data/scans.json'):
        self.storage_path = storage_path
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Ensure storage directory and file exist"""
        storage_dir = os.path.dirname(self.storage_path)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
        
        if not os.path.exists(self.storage_path):
            self._write_data({'scans': []})
    
    def _read_data(self) -> Dict:
        """Read all data from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading storage: {e}")
            return {'scans': []}
    
    def _write_data(self, data: Dict):
        """Write data to storage"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing storage: {e}")
            raise
    
    def save_scan(self, scan_results: Dict) -> bool:
        """
        Save scan metadata and results
        
        Args:
            scan_results: Complete scan results dictionary
            
        Returns:
            bool: True if saved successfully
        """
        try:
            data = self._read_data()
            
            # Create scan metadata entry
            scan_entry = {
                'scan_id': scan_results.get('scan_id'),
                'target': scan_results.get('target'),
                'scan_type': scan_results.get('scan_type'),
                'security_score': scan_results.get('security_score', 0),
                'risk_level': scan_results.get('risk_level', 'UNKNOWN'),
                'start_time': scan_results.get('start_time'),
                'end_time': scan_results.get('end_time'),
                'duration': scan_results.get('duration', 0),
                'status': scan_results.get('status', 'completed'),
                'created_at': datetime.utcnow().isoformat(),
                'results_summary': self._create_results_summary(scan_results.get('results', {})),
                'full_results': scan_results  # Store complete results
            }
            
            # Add to scans list (newest first)
            data['scans'].insert(0, scan_entry)
            
            # Keep only last 1000 scans to prevent file from growing too large
            if len(data['scans']) > 1000:
                data['scans'] = data['scans'][:1000]
            
            self._write_data(data)
            logger.info(f"Saved scan {scan_entry['scan_id']} to storage")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scan: {e}", exc_info=True)
            return False
    
    def _create_results_summary(self, results: Dict) -> Dict:
        """Create a summary of scan results"""
        summary = {
            'total_categories': len(results),
            'categories_checked': []
        }
        
        for category, category_results in results.items():
            if isinstance(category_results, dict):
                category_info = {
                    'name': category,
                    'score': category_results.get('score', 0)
                }
                
                # Count issues/vulnerabilities
                if 'issues' in category_results:
                    category_info['issues_count'] = len(category_results['issues'])
                if 'vulnerabilities' in category_results:
                    category_info['vulnerabilities_count'] = len(category_results['vulnerabilities'])
                if 'open_ports' in category_results:
                    category_info['open_ports_count'] = len(category_results['open_ports'])
                if 'missing_headers' in category_results:
                    category_info['missing_headers_count'] = len(category_results['missing_headers'])
                
                summary['categories_checked'].append(category_info)
        
        return summary
    
    def get_scan(self, scan_id: str) -> Optional[Dict]:
        """
        Get scan by ID
        
        Args:
            scan_id: Scan ID to retrieve
            
        Returns:
            Dict or None: Scan data if found
        """
        try:
            data = self._read_data()
            for scan in data['scans']:
                if scan['scan_id'] == scan_id:
                    return scan
            return None
        except Exception as e:
            logger.error(f"Error getting scan {scan_id}: {e}")
            return None
    
    def get_all_scans(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get all scans with pagination
        
        Args:
            limit: Maximum number of scans to return
            offset: Number of scans to skip
            
        Returns:
            List of scan metadata (without full results)
        """
        try:
            data = self._read_data()
            scans = data['scans'][offset:offset + limit]
            
            # Return scans without full_results to reduce payload size
            return [
                {
                    'scan_id': scan['scan_id'],
                    'target': scan['target'],
                    'scan_type': scan['scan_type'],
                    'security_score': scan['security_score'],
                    'risk_level': scan['risk_level'],
                    'start_time': scan['start_time'],
                    'end_time': scan['end_time'],
                    'duration': scan['duration'],
                    'status': scan['status'],
                    'created_at': scan['created_at'],
                    'results_summary': scan.get('results_summary', {})
                }
                for scan in scans
            ]
        except Exception as e:
            logger.error(f"Error getting all scans: {e}")
            return []
    
    def get_scan_count(self) -> int:
        """Get total number of scans"""
        try:
            data = self._read_data()
            return len(data['scans'])
        except Exception as e:
            logger.error(f"Error getting scan count: {e}")
            return 0
    
    def search_scans(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search scans by target, scan_id, or other fields
        
        Args:
            query: Search query string
            limit: Maximum results to return
            
        Returns:
            List of matching scans
        """
        try:
            data = self._read_data()
            query_lower = query.lower()
            
            matching_scans = []
            for scan in data['scans']:
                if (query_lower in scan['scan_id'].lower() or
                    query_lower in scan['target'].lower() or
                    query_lower in scan.get('risk_level', '').lower()):
                    matching_scans.append({
                        'scan_id': scan['scan_id'],
                        'target': scan['target'],
                        'scan_type': scan['scan_type'],
                        'security_score': scan['security_score'],
                        'risk_level': scan['risk_level'],
                        'start_time': scan['start_time'],
                        'end_time': scan['end_time'],
                        'duration': scan['duration'],
                        'status': scan['status'],
                        'created_at': scan['created_at'],
                        'results_summary': scan.get('results_summary', {})
                    })
                    
                    if len(matching_scans) >= limit:
                        break
            
            return matching_scans
        except Exception as e:
            logger.error(f"Error searching scans: {e}")
            return []
    
    def delete_scan(self, scan_id: str) -> bool:
        """
        Delete a scan by ID
        
        Args:
            scan_id: Scan ID to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            data = self._read_data()
            original_length = len(data['scans'])
            
            data['scans'] = [s for s in data['scans'] if s['scan_id'] != scan_id]
            
            if len(data['scans']) < original_length:
                self._write_data(data)
                logger.info(f"Deleted scan {scan_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting scan {scan_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get overall statistics about scans"""
        try:
            data = self._read_data()
            scans = data['scans']
            
            if not scans:
                return {
                    'total_scans': 0,
                    'average_score': 0,
                    'risk_level_distribution': {},
                    'scan_type_distribution': {}
                }
            
            total_score = sum(s.get('security_score', 0) for s in scans)
            avg_score = total_score / len(scans) if scans else 0
            
            risk_levels = {}
            scan_types = {}
            
            for scan in scans:
                risk = scan.get('risk_level', 'UNKNOWN')
                risk_levels[risk] = risk_levels.get(risk, 0) + 1
                
                stype = scan.get('scan_type', 'unknown')
                scan_types[stype] = scan_types.get(stype, 0) + 1
            
            return {
                'total_scans': len(scans),
                'average_score': round(avg_score, 2),
                'risk_level_distribution': risk_levels,
                'scan_type_distribution': scan_types
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

