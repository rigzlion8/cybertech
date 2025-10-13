#!/usr/bin/env python3
"""
Test MongoDB connection
"""

import os
from dotenv import load_dotenv
from modules.mongodb_storage import MongoDBStorage

# Load environment variables
load_dotenv()

def test_connection():
    """Test MongoDB connection"""
    print("Testing MongoDB connection...")
    print(f"MONGODB_URI: {os.getenv('MONGODB_URI', 'Not set')}")
    print(f"USE_MONGODB: {os.getenv('USE_MONGODB', 'Not set')}")
    print()
    
    try:
        # Try to connect
        storage = MongoDBStorage()
        print("✓ Successfully connected to MongoDB!")
        
        # Test basic operations
        count = storage.get_scan_count()
        print(f"✓ Current scans in database: {count}")
        
        # Get statistics
        stats = storage.get_statistics()
        print(f"✓ Statistics retrieved successfully")
        print(f"  Total scans: {stats.get('total_scans', 0)}")
        print(f"  Average score: {stats.get('average_score', 0)}")
        
        print("\n✅ MongoDB is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your MONGODB_URI in .env file")
        print("2. Ensure MongoDB is running (if local)")
        print("3. Check network connectivity (if Atlas)")
        print("4. Verify credentials are correct")
        return False

if __name__ == '__main__':
    test_connection()

