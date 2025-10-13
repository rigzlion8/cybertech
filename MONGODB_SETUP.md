# MongoDB Integration Guide

## Overview

The CyberTech Security Scanner now supports MongoDB for storing scan data, providing better scalability and powerful trend analysis capabilities. The system can use either MongoDB or JSON file storage, with automatic fallback to JSON if MongoDB is unavailable.

## Features with MongoDB

✅ **Scalable Storage**: Handle millions of scans without performance degradation
✅ **Fast Queries**: Indexed searches for instant results  
✅ **Trend Analysis**: Advanced aggregation pipelines for trend data
✅ **Target History**: Track scan history for specific targets
✅ **Score Improvement**: Monitor security score changes over time
✅ **Flexible Filtering**: Complex queries with multiple criteria

## Setup MongoDB

### Option 1: Local MongoDB

1. **Install MongoDB** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mongodb

   # macOS
   brew install mongodb-community

   # Or use Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

2. **Start MongoDB**:
   ```bash
   sudo systemctl start mongodb
   # or
   brew services start mongodb-community
   # or for Docker
   docker start mongodb
   ```

3. **Verify MongoDB is running**:
   ```bash
   mongosh --eval "db.version()"
   ```

### Option 2: MongoDB Atlas (Cloud)

1. **Create a free MongoDB Atlas account** at https://www.mongodb.com/cloud/atlas

2. **Create a cluster**:
   - Choose the free tier (M0)
   - Select your preferred region
   - Create cluster

3. **Get your connection string**:
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database password

4. **Whitelist your IP address**:
   - Go to Network Access
   - Add your IP address or allow access from anywhere (0.0.0.0/0)

## Configuration

### Enable MongoDB Storage

Create or update your `.env` file:

```bash
# Use MongoDB for storage
USE_MONGODB=true

# MongoDB Connection String
# For local MongoDB:
MONGODB_URI=mongodb://localhost:27017/

# For MongoDB Atlas:
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/cybertech?retryWrites=true&w=majority

# Other settings
PORT=5000
FLASK_ENV=production
FLASK_DEBUG=False
```

### Environment Variables

- `USE_MONGODB`: Set to `true` to enable MongoDB storage
- `MONGODB_URI`: MongoDB connection string (defaults to `mongodb://localhost:27017/`)

If these are not set, the system will automatically use JSON file storage.

## Database Structure

### Database Name
- Default: `cybertech`
- Can be customized in `modules/mongodb_storage.py`

### Collections

#### `scans` Collection

Document structure:
```json
{
  "scan_id": "abc123",
  "target": "https://example.com",
  "scan_type": "full",
  "security_score": 85.5,
  "risk_level": "LOW",
  "start_time": "2025-10-12T10:30:00",
  "end_time": "2025-10-12T10:31:00",
  "duration": 45.3,
  "status": "completed",
  "created_at": ISODate("2025-10-12T10:31:00Z"),
  "results_summary": {
    "total_categories": 5,
    "categories_checked": [...]
  },
  "full_results": {...}
}
```

### Indexes

The following indexes are automatically created for optimal performance:

1. **scan_id** (unique): Quick lookup by scan ID
2. **target**: Search by target URL/IP
3. **start_time** (descending): Sort by date
4. **risk_level**: Filter by risk level
5. **Compound (target, start_time)**: Trend queries for specific targets

## Usage

### Automatic Selection

The system automatically chooses the storage backend:

```python
# In app.py, this automatically uses MongoDB if configured
from modules.scan_storage import ScanStorage

scan_storage = ScanStorage()  # Auto-detects MongoDB or JSON
```

### Manual Selection

Force a specific backend:

```python
from modules.scan_storage import get_storage_backend

# Force MongoDB
storage = get_storage_backend('mongodb')

# Force JSON
storage = get_storage_backend('json')

# Auto-detect (default)
storage = get_storage_backend('auto')
```

## Trend Analysis Features

### 1. Daily Scan Activity

View the number of scans performed each day:

**API Endpoint**: `GET /api/admin/trends?days=30`

```json
{
  "status": "success",
  "trends": {
    "period_days": 30,
    "daily_scans": [
      {
        "_id": "2025-10-12",
        "count": 15,
        "avg_score": 75.5
      }
    ]
  }
}
```

### 2. Risk Level Trends

Track how risk levels change over time:

```json
{
  "risk_trends": [
    {
      "_id": {
        "date": "2025-10-12",
        "risk_level": "HIGH"
      },
      "count": 5
    }
  ]
}
```

### 3. Top Scanned Targets

See which targets are scanned most frequently:

```json
{
  "top_targets": [
    {
      "_id": "https://example.com",
      "scan_count": 25,
      "avg_score": 82.3,
      "last_scan": "2025-10-12T15:30:00"
    }
  ]
}
```

### 4. Target Scan History

Get complete scan history for a specific target:

**API Endpoint**: `GET /api/admin/target/<target>/history?limit=10`

**Example**: `GET /api/admin/target/https://example.com/history`

### 5. Score Improvement Tracking

Monitor security score improvements for a target:

**API Endpoint**: `GET /api/admin/target/<target>/improvement`

```json
{
  "status": "success",
  "improvement": {
    "target": "https://example.com",
    "total_scans": 10,
    "first_score": 65.0,
    "latest_score": 85.5,
    "improvement": 20.5,
    "scans": [...]
  }
}
```

## Admin Dashboard Visualization

The admin dashboard includes interactive charts powered by Chart.js:

### Charts Available

1. **Daily Scan Activity** (Bar Chart)
   - Shows number of scans per day
   - Helps identify scanning patterns

2. **Average Security Scores** (Line Chart)
   - Tracks average scores over time
   - Shows overall security improvement trends

3. **Risk Level Distribution** (Stacked Bar Chart)
   - Visualizes LOW/MEDIUM/HIGH/CRITICAL distribution
   - Color-coded for easy identification

4. **Most Scanned Targets** (Interactive List)
   - Click any target to view detailed trend
   - Shows scan count and average score

### Time Period Filters

Switch between different time periods:
- **7 Days**: Recent activity
- **30 Days**: Monthly trends (default)
- **90 Days**: Quarterly analysis

## Migration from JSON to MongoDB

If you're switching from JSON to MongoDB, you can migrate existing data:

### Migration Script

Create `migrate_to_mongodb.py`:

```python
#!/usr/bin/env python3
import json
from modules.mongodb_storage import MongoDBStorage

def migrate():
    # Read JSON data
    with open('data/scans.json', 'r') as f:
        data = json.load(f)
    
    # Connect to MongoDB
    mongo = MongoDBStorage()
    
    # Migrate each scan
    scans = data.get('scans', [])
    print(f"Migrating {len(scans)} scans...")
    
    for i, scan in enumerate(scans, 1):
        full_results = scan.get('full_results', {})
        if full_results:
            mongo.save_scan(full_results)
            print(f"Migrated {i}/{len(scans)}: {scan['scan_id']}")
    
    print("Migration complete!")

if __name__ == '__main__':
    migrate()
```

Run migration:
```bash
python migrate_to_mongodb.py
```

## Performance Considerations

### MongoDB vs JSON

| Feature | MongoDB | JSON File |
|---------|---------|-----------|
| Small datasets (<1000 scans) | Good | Good |
| Large datasets (>10000 scans) | Excellent | Slow |
| Search performance | Fast (indexed) | Linear scan |
| Concurrent access | Excellent | Limited |
| Trend analysis | Native aggregation | Custom code |
| Scalability | Horizontal | Vertical |

### Optimization Tips

1. **Use indexes**: Already configured automatically
2. **Limit result sets**: Use pagination
3. **Project only needed fields**: Exclude `full_results` when not needed
4. **Connection pooling**: Handled by PyMongo automatically
5. **Regular backups**: Use `mongodump`

## Backup and Restore

### Backup

```bash
# Backup entire database
mongodump --uri="mongodb://localhost:27017/cybertech" --out=/backup/cybertech

# Backup with compression
mongodump --uri="mongodb://localhost:27017/cybertech" --gzip --out=/backup/cybertech
```

### Restore

```bash
# Restore database
mongorestore --uri="mongodb://localhost:27017/cybertech" /backup/cybertech/cybertech

# Restore with compression
mongorestore --uri="mongodb://localhost:27017/cybertech" --gzip /backup/cybertech/cybertech
```

## Troubleshooting

### Connection Errors

**Error**: `ConnectionFailure: [Errno 111] Connection refused`

**Solution**:
- Ensure MongoDB is running: `sudo systemctl status mongodb`
- Check connection string in `.env`
- Verify MongoDB is listening on correct port: `netstat -an | grep 27017`

### Authentication Errors

**Error**: `OperationFailure: Authentication failed`

**Solution**:
- Check username and password in connection string
- Ensure user has proper permissions
- For Atlas, verify IP whitelist

### Index Errors

**Error**: `IndexError` or slow queries

**Solution**:
- Manually rebuild indexes:
  ```python
  from modules.mongodb_storage import MongoDBStorage
  mongo = MongoDBStorage()
  mongo._ensure_indexes()
  ```

### Falling Back to JSON

If MongoDB connection fails, the system automatically falls back to JSON storage. Check logs for:
```
WARNING - Failed to initialize MongoDB, falling back to JSON
INFO - Using JSON storage backend
```

## Monitoring

### Check MongoDB Stats

```javascript
// Connect to MongoDB shell
mongosh

// Use database
use cybertech

// Collection stats
db.scans.stats()

// Count documents
db.scans.countDocuments()

// Check indexes
db.scans.getIndexes()

// Most recent scans
db.scans.find().sort({start_time: -1}).limit(5)
```

### Performance Monitoring

```javascript
// Enable profiling
db.setProfilingLevel(1, { slowms: 100 })

// View slow queries
db.system.profile.find().sort({ts: -1}).limit(5)
```

## Security Best Practices

1. **Use authentication**: Don't run MongoDB without auth in production
2. **Use SSL/TLS**: Encrypt connections, especially for Atlas
3. **Limit access**: Use firewall rules and IP whitelisting
4. **Regular backups**: Automate daily backups
5. **Update regularly**: Keep MongoDB and PyMongo updated
6. **Use read-only users**: For reporting/analytics

## Support

### Check Configuration

```bash
# In your project directory
python3 -c "from modules.scan_storage import get_storage_backend; storage = get_storage_backend(); print(f'Using: {storage.__class__.__name__}')"
```

### Test MongoDB Connection

```python
from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✓ MongoDB is accessible")
except Exception as e:
    print(f"✗ MongoDB error: {e}")
```

## Additional Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [MongoDB Compass](https://www.mongodb.com/products/compass) - GUI for MongoDB

