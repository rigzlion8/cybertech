"""
Scan Storage Module
Factory for creating storage handlers (JSON or MongoDB)
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def get_storage_backend(backend='auto'):
    """
    Factory function to get appropriate storage backend
    
    Args:
        backend: 'auto', 'mongodb', or 'json'
        
    Returns:
        Storage instance (MongoDBStorage or JSONStorage)
    """
    if backend == 'auto':
        # Check if MongoDB is configured
        mongodb_uri = os.getenv('MONGODB_URI')
        use_mongodb = os.getenv('USE_MONGODB', 'false').lower() == 'true'
        
        if mongodb_uri or use_mongodb:
            backend = 'mongodb'
        else:
            backend = 'json'
    
    if backend == 'mongodb':
        try:
            from .mongodb_storage import MongoDBStorage
            logger.info("Using MongoDB storage backend")
            return MongoDBStorage()
        except Exception as e:
            logger.warning(f"Failed to initialize MongoDB, falling back to JSON: {e}")
            backend = 'json'
    
    if backend == 'json':
        logger.info("Using JSON storage backend")
        return JSONStorage()
    
    raise ValueError(f"Unknown storage backend: {backend}")


# Alias for backward compatibility
ScanStorage = get_storage_backend


class JSONStorage:
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
    
    def get_target_history(self, target: str, limit: int = 10) -> List[Dict]:
        """
        Get scan history for a specific target
        
        Args:
            target: Target URL/IP to get history for
            limit: Maximum number of results
            
        Returns:
            List of scans for the target, sorted by date (newest first)
        """
        try:
            data = self._read_data()
            target_scans = [
                s for s in data['scans']
                if s.get('target') == target
            ]
            return target_scans[:limit]
        except Exception as e:
            logger.error(f"Error getting target history: {e}")
            return []
    
    def get_trend_data(self, days: int = 30) -> Dict:
        """
        Get trend data for the specified number of days
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with trend information
        """
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict
            
            data = self._read_data()
            scans = data['scans']
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Filter scans within date range
            recent_scans = [
                s for s in scans
                if datetime.fromisoformat(s.get('start_time', '')) >= start_date
            ]
            
            # Daily scan counts and scores
            daily_data = defaultdict(lambda: {'count': 0, 'total_score': 0})
            risk_trends = defaultdict(lambda: defaultdict(int))
            target_counts = defaultdict(lambda: {'count': 0, 'total_score': 0, 'last_scan': None})
            
            for scan in recent_scans:
                scan_date = datetime.fromisoformat(scan['start_time']).strftime('%Y-%m-%d')
                
                # Daily counts
                daily_data[scan_date]['count'] += 1
                daily_data[scan_date]['total_score'] += scan.get('security_score', 0)
                
                # Risk trends
                risk_level = scan.get('risk_level', 'UNKNOWN')
                risk_trends[scan_date][risk_level] += 1
                
                # Target counts
                target = scan.get('target')
                target_counts[target]['count'] += 1
                target_counts[target]['total_score'] += scan.get('security_score', 0)
                if not target_counts[target]['last_scan'] or scan['start_time'] > target_counts[target]['last_scan']:
                    target_counts[target]['last_scan'] = scan['start_time']
            
            # Format daily data
            formatted_daily = [
                {
                    '_id': date,
                    'count': data['count'],
                    'avg_score': data['total_score'] / data['count'] if data['count'] > 0 else 0
                }
                for date, data in sorted(daily_data.items())
            ]
            
            # Format risk trends
            formatted_risk_trends = [
                {
                    '_id': {'date': date, 'risk_level': risk},
                    'count': count
                }
                for date, risks in sorted(risk_trends.items())
                for risk, count in risks.items()
            ]
            
            # Format top targets
            top_targets = [
                {
                    '_id': target,
                    'scan_count': data['count'],
                    'avg_score': data['total_score'] / data['count'] if data['count'] > 0 else 0,
                    'last_scan': data['last_scan']
                }
                for target, data in sorted(
                    target_counts.items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:10]
            ]
            
            return {
                'period_days': days,
                'daily_scans': formatted_daily,
                'risk_trends': formatted_risk_trends,
                'top_targets': top_targets
            }
            
        except Exception as e:
            logger.error(f"Error getting trend data: {e}")
            return {}
    
    def get_score_improvement_trend(self, target: str) -> Dict:
        """
        Get security score improvement trend for a specific target
        
        Args:
            target: Target URL/IP
            
        Returns:
            Dict with score history
        """
        try:
            data = self._read_data()
            target_scans = [
                {
                    'scan_id': s['scan_id'],
                    'start_time': s['start_time'],
                    'security_score': s['security_score'],
                    'risk_level': s['risk_level']
                }
                for s in data['scans']
                if s.get('target') == target
            ]
            
            # Sort by start_time
            target_scans.sort(key=lambda x: x['start_time'])
            
            if not target_scans:
                return {'target': target, 'scans': []}
            
            # Calculate improvement
            if len(target_scans) > 1:
                first_score = target_scans[0]['security_score']
                last_score = target_scans[-1]['security_score']
                improvement = last_score - first_score
            else:
                improvement = 0
            
            return {
                'target': target,
                'total_scans': len(target_scans),
                'first_score': target_scans[0]['security_score'],
                'latest_score': target_scans[-1]['security_score'],
                'improvement': round(improvement, 2),
                'scans': target_scans
            }
            
        except Exception as e:
            logger.error(f"Error getting score improvement: {e}")
            return {}
    
    def close(self):
        """Close connection (no-op for JSON storage)"""
        pass

