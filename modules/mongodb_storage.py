"""
MongoDB Storage Module
Handles persistence of scan metadata and results in MongoDB
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
import urllib.parse

logger = logging.getLogger(__name__)


class MongoDBStorage:
    """MongoDB storage handler for scan metadata and results"""
    
    def __init__(self, connection_string=None, database_name='cybertech'):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string (defaults to env var or localhost)
            database_name: Database name to use
        """
        if connection_string is None:
            # Try to get from environment
            connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        self.scans_collection = None
        
        self._connect()
        self._ensure_indexes()
    
    def _connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[self.database_name]
            self.scans_collection = self.db['scans']
            
            logger.info(f"Connected to MongoDB: {self.database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            raise
    
    def _ensure_indexes(self):
        """Create necessary indexes for performance"""
        try:
            # Index on scan_id for quick lookups
            self.scans_collection.create_index('scan_id', unique=True)
            
            # Index on target for searching
            self.scans_collection.create_index('target')
            
            # Index on start_time for sorting and trend analysis
            self.scans_collection.create_index([('start_time', DESCENDING)])
            
            # Index on risk_level for filtering
            self.scans_collection.create_index('risk_level')
            
            # Compound index for trend queries
            self.scans_collection.create_index([
                ('target', ASCENDING),
                ('start_time', DESCENDING)
            ])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def save_scan(self, scan_results: Dict) -> bool:
        """
        Save scan metadata and results
        
        Args:
            scan_results: Complete scan results dictionary
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Create scan document
            scan_doc = {
                'scan_id': scan_results.get('scan_id'),
                'target': scan_results.get('target'),
                'scan_type': scan_results.get('scan_type'),
                'security_score': scan_results.get('security_score', 0),
                'risk_level': scan_results.get('risk_level', 'UNKNOWN'),
                'start_time': scan_results.get('start_time'),
                'end_time': scan_results.get('end_time'),
                'duration': scan_results.get('duration', 0),
                'status': scan_results.get('status', 'completed'),
                'created_at': datetime.utcnow(),
                'results_summary': self._create_results_summary(scan_results.get('results', {})),
                'full_results': scan_results  # Store complete results
            }
            
            # Upsert (insert or update)
            result = self.scans_collection.update_one(
                {'scan_id': scan_doc['scan_id']},
                {'$set': scan_doc},
                upsert=True
            )
            
            logger.info(f"Saved scan {scan_doc['scan_id']} to MongoDB")
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
            scan = self.scans_collection.find_one(
                {'scan_id': scan_id},
                {'_id': 0}  # Exclude MongoDB _id field
            )
            return scan
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
            cursor = self.scans_collection.find(
                {},
                {
                    '_id': 0,
                    'full_results': 0  # Exclude full results to reduce payload
                }
            ).sort('start_time', DESCENDING).skip(offset).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Error getting all scans: {e}")
            return []
    
    def get_scan_count(self) -> int:
        """Get total number of scans"""
        try:
            return self.scans_collection.count_documents({})
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
            # Create regex pattern for case-insensitive search
            search_pattern = {'$regex': query, '$options': 'i'}
            
            cursor = self.scans_collection.find(
                {
                    '$or': [
                        {'scan_id': search_pattern},
                        {'target': search_pattern},
                        {'risk_level': search_pattern}
                    ]
                },
                {
                    '_id': 0,
                    'full_results': 0
                }
            ).sort('start_time', DESCENDING).limit(limit)
            
            return list(cursor)
            
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
            result = self.scans_collection.delete_one({'scan_id': scan_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted scan {scan_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting scan {scan_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get overall statistics about scans"""
        try:
            total_scans = self.scans_collection.count_documents({})
            
            if total_scans == 0:
                return {
                    'total_scans': 0,
                    'average_score': 0,
                    'risk_level_distribution': {},
                    'scan_type_distribution': {}
                }
            
            # Calculate average score
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'avg_score': {'$avg': '$security_score'}
                    }
                }
            ]
            avg_result = list(self.scans_collection.aggregate(pipeline))
            avg_score = avg_result[0]['avg_score'] if avg_result else 0
            
            # Risk level distribution
            risk_pipeline = [
                {
                    '$group': {
                        '_id': '$risk_level',
                        'count': {'$sum': 1}
                    }
                }
            ]
            risk_dist = {
                item['_id']: item['count']
                for item in self.scans_collection.aggregate(risk_pipeline)
            }
            
            # Scan type distribution
            type_pipeline = [
                {
                    '$group': {
                        '_id': '$scan_type',
                        'count': {'$sum': 1}
                    }
                }
            ]
            type_dist = {
                item['_id']: item['count']
                for item in self.scans_collection.aggregate(type_pipeline)
            }
            
            return {
                'total_scans': total_scans,
                'average_score': round(avg_score, 2),
                'risk_level_distribution': risk_dist,
                'scan_type_distribution': type_dist
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
            cursor = self.scans_collection.find(
                {'target': target},
                {
                    '_id': 0,
                    'full_results': 0
                }
            ).sort('start_time', DESCENDING).limit(limit)
            
            return list(cursor)
            
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
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily scan counts
            daily_pipeline = [
                {
                    '$match': {
                        'start_time': {'$gte': start_date.isoformat()}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': {'$dateFromString': {'dateString': '$start_time'}}
                            }
                        },
                        'count': {'$sum': 1},
                        'avg_score': {'$avg': '$security_score'}
                    }
                },
                {
                    '$sort': {'_id': 1}
                }
            ]
            
            daily_data = list(self.scans_collection.aggregate(daily_pipeline))
            
            # Risk level trends
            risk_trend_pipeline = [
                {
                    '$match': {
                        'start_time': {'$gte': start_date.isoformat()}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'date': {
                                '$dateToString': {
                                    'format': '%Y-%m-%d',
                                    'date': {'$dateFromString': {'dateString': '$start_time'}}
                                }
                            },
                            'risk_level': '$risk_level'
                        },
                        'count': {'$sum': 1}
                    }
                },
                {
                    '$sort': {'_id.date': 1}
                }
            ]
            
            risk_trend_data = list(self.scans_collection.aggregate(risk_trend_pipeline))
            
            # Most scanned targets
            top_targets_pipeline = [
                {
                    '$match': {
                        'start_time': {'$gte': start_date.isoformat()}
                    }
                },
                {
                    '$group': {
                        '_id': '$target',
                        'scan_count': {'$sum': 1},
                        'avg_score': {'$avg': '$security_score'},
                        'last_scan': {'$max': '$start_time'}
                    }
                },
                {
                    '$sort': {'scan_count': -1}
                },
                {
                    '$limit': 10
                }
            ]
            
            top_targets = list(self.scans_collection.aggregate(top_targets_pipeline))
            
            return {
                'period_days': days,
                'daily_scans': daily_data,
                'risk_trends': risk_trend_data,
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
            cursor = self.scans_collection.find(
                {'target': target},
                {
                    '_id': 0,
                    'scan_id': 1,
                    'start_time': 1,
                    'security_score': 1,
                    'risk_level': 1
                }
            ).sort('start_time', ASCENDING)
            
            scans = list(cursor)
            
            if not scans:
                return {'target': target, 'scans': []}
            
            # Calculate improvement
            if len(scans) > 1:
                first_score = scans[0]['security_score']
                last_score = scans[-1]['security_score']
                improvement = last_score - first_score
            else:
                improvement = 0
            
            return {
                'target': target,
                'total_scans': len(scans),
                'first_score': scans[0]['security_score'],
                'latest_score': scans[-1]['security_score'],
                'improvement': round(improvement, 2),
                'scans': scans
            }
            
        except Exception as e:
            logger.error(f"Error getting score improvement: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

