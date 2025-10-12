# Admin Dashboard Guide

## Overview

The CyberTech Security Scanner now includes a comprehensive admin dashboard for viewing and managing scan reports. The admin dashboard provides a centralized interface to:

- View all scan reports with pagination and search
- Access detailed scan information
- Download PDF reports
- Delete scan records
- View overall statistics

## Features

### 1. Dashboard Overview

The admin dashboard (`/admin`) displays:
- **Statistics Cards**: Total scans, average security score, high-risk scans, and critical-risk scans
- **Scan List Table**: Paginated list of all scans with key information
- **Search Functionality**: Search by scan ID, target URL, or risk level
- **Detailed View**: Click any scan to view comprehensive details

### 2. Scan List

The scan list table shows:
- Scan ID (unique identifier)
- Target URL/IP
- Scan Type (full, quick, custom)
- Security Score (0-100)
- Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
- Date and Time
- Duration
- Action buttons (Download, Delete)

### 3. Search and Filter

- Use the search box to filter scans by:
  - Scan ID
  - Target URL
  - Risk level
- Real-time search updates
- Clear button to reset search

### 4. Detailed Scan View

Click on any scan row to view:
- Complete scan overview
- Security score and risk level
- Detailed category results:
  - Port scan results
  - Vulnerabilities found
  - SSL/TLS certificate information
  - HTTP security headers
  - Password security findings
  - Database security findings
- Download PDF report button
- All findings with severity levels

### 5. Pagination

- Navigate through scans with Previous/Next buttons
- Shows current page and total count
- 20 scans per page by default

## API Endpoints

### Admin Routes

#### 1. Get Admin Dashboard
```
GET /admin
```
Serves the admin HTML page.

#### 2. Get All Scans
```
GET /api/admin/scans?limit=100&offset=0&search=example
```
**Query Parameters:**
- `limit` (optional): Maximum number of scans to return (default: 100)
- `offset` (optional): Number of scans to skip (default: 0)
- `search` (optional): Search query string

**Response:**
```json
{
  "status": "success",
  "scans": [...],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

#### 3. Get Scan Details
```
GET /api/admin/scan/<scan_id>
```
Returns complete scan information including full results.

**Response:**
```json
{
  "status": "success",
  "scan": {
    "scan_id": "abc123",
    "target": "https://example.com",
    "security_score": 85,
    "risk_level": "LOW",
    "full_results": {...}
  }
}
```

#### 4. Delete Scan
```
DELETE /api/admin/scan/<scan_id>
```
Deletes a scan record and its PDF report.

**Response:**
```json
{
  "status": "success",
  "message": "Scan deleted successfully"
}
```

#### 5. Get Statistics
```
GET /api/admin/statistics
```
Returns overall scan statistics.

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_scans": 150,
    "average_score": 72.5,
    "risk_level_distribution": {
      "LOW": 50,
      "MEDIUM": 60,
      "HIGH": 30,
      "CRITICAL": 10
    },
    "scan_type_distribution": {
      "full": 100,
      "quick": 40,
      "custom": 10
    }
  }
}
```

## Data Storage

### Scan Storage System

Scan data is stored in a JSON file at `data/scans.json`. The storage system:

- Automatically creates the storage file if it doesn't exist
- Stores complete scan results including metadata
- Maintains up to 1000 most recent scans
- Provides fast search and retrieval
- Thread-safe for concurrent operations

### Storage Structure

```json
{
  "scans": [
    {
      "scan_id": "abc123",
      "target": "https://example.com",
      "scan_type": "full",
      "security_score": 85,
      "risk_level": "LOW",
      "start_time": "2025-10-12T10:30:00",
      "end_time": "2025-10-12T10:31:00",
      "duration": 45.3,
      "status": "completed",
      "created_at": "2025-10-12T10:31:00",
      "results_summary": {...},
      "full_results": {...}
    }
  ]
}
```

## Usage

### Accessing the Admin Dashboard

1. Start the CyberTech application:
   ```bash
   python app.py
   ```

2. Navigate to the admin dashboard:
   ```
   http://localhost:5000/admin
   ```

3. Or click the "Admin" link in the navigation menu

### Viewing Scan Details

1. Click on any row in the scan list table
2. A modal will open showing complete scan details
3. Use the "Download PDF Report" button to get the report
4. Click outside the modal or press ESC to close

### Searching Scans

1. Enter search term in the search box
2. Press Enter or click "Search" button
3. Results will update automatically
4. Click "Clear" to show all scans again

### Deleting Scans

1. Click the delete (🗑️) button in the Actions column
2. Confirm the deletion in the popup
3. The scan and its PDF report will be permanently deleted

## Technical Details

### Backend Components

1. **scan_storage.py**: Storage handler for scan data
   - JSON-based persistence
   - CRUD operations
   - Search and statistics functions

2. **app.py**: Flask application with admin routes
   - Admin page serving
   - API endpoints for scan management
   - Integration with existing scan system

### Frontend Components

1. **admin.html**: Admin dashboard UI
   - Responsive design
   - Modal for detailed views
   - Statistics cards
   - Searchable table

2. **admin.js**: Admin dashboard JavaScript
   - API communication
   - Dynamic content rendering
   - Event handling
   - Search and pagination logic

3. **styles.css**: Shared styling (extended with admin-specific styles)

## Security Considerations

⚠️ **Important**: The admin dashboard currently has no authentication. In a production environment, you should:

1. Add authentication middleware
2. Implement role-based access control
3. Add CSRF protection
4. Use HTTPS
5. Implement rate limiting
6. Add audit logging

Example authentication setup:
```python
from functools import wraps
from flask import session, redirect

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_page():
    return send_from_directory('static', 'admin.html')
```

## Troubleshooting

### Issue: No scans showing in dashboard
- Ensure at least one scan has been completed
- Check that `data/scans.json` exists and is readable
- Check browser console for errors

### Issue: Statistics not loading
- Verify the `/api/admin/statistics` endpoint is accessible
- Check server logs for errors
- Ensure scan storage is properly initialized

### Issue: Cannot delete scans
- Check file permissions on `data/scans.json` and `reports/` directory
- Verify the scan ID exists
- Check server logs for errors

### Issue: Modal not closing
- Press ESC key
- Click outside the modal area
- Refresh the page

## Future Enhancements

Potential improvements for the admin dashboard:

1. **Authentication & Authorization**
   - User login system
   - Role-based permissions
   - Session management

2. **Advanced Filtering**
   - Date range filters
   - Multi-criteria filtering
   - Saved filter presets

3. **Bulk Operations**
   - Bulk delete
   - Bulk export
   - Batch actions

4. **Enhanced Analytics**
   - Trend charts
   - Risk timeline
   - Comparison tools

5. **Export Functionality**
   - Export to CSV
   - Export to Excel
   - Export to JSON

6. **Real-time Updates**
   - WebSocket integration
   - Live scan monitoring
   - Auto-refresh

7. **Database Backend**
   - PostgreSQL/MySQL integration
   - Better performance at scale
   - Advanced querying

## Support

For issues or questions about the admin dashboard:
- Check application logs: `cybertech.log`
- Review API responses in browser developer tools
- Verify all dependencies are installed: `pip install -r requirements.txt`

