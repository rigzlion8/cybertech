# 📡 API Documentation

Complete API reference for CyberTech Security Scanner.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, the API does not require authentication. For production use, implement API key authentication.

## Endpoints

### 1. Health Check

Check if the API is operational.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T12:00:00.000000"
}
```

**cURL Example:**
```bash
curl http://localhost:5000/api/health
```

---

### 2. Full Security Scan

Perform a comprehensive security assessment.

**Endpoint:** `POST /api/scan`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "target": "https://example.com",
  "email": "user@example.com",
  "scan_type": "full",
  "options": {
    "port_scan": true,
    "vulnerability_scan": true,
    "ssl_check": true,
    "headers_check": true,
    "password_check": true,
    "database_check": false
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target | string | Yes | Target URL or IP address |
| email | string | Yes | Email for report delivery |
| scan_type | string | No | Scan type: "full", "quick", or "custom" (default: "full") |
| options | object | No | Custom scan options (required if scan_type is "custom") |

**Options Object:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| port_scan | boolean | true | Enable port scanning |
| vulnerability_scan | boolean | true | Enable vulnerability testing |
| ssl_check | boolean | true | Enable SSL/TLS analysis |
| headers_check | boolean | true | Enable HTTP headers analysis |
| password_check | boolean | true | Enable password security checks |
| database_check | boolean | false | Enable database security checks |

**Response:**
```json
{
  "status": "success",
  "scan_id": "a1b2c3d4",
  "results": {
    "scan_id": "a1b2c3d4",
    "target": "https://example.com",
    "scan_type": "full",
    "security_score": 75.5,
    "risk_level": "MEDIUM",
    "start_time": "2025-01-10T12:00:00",
    "end_time": "2025-01-10T12:05:30",
    "duration": 330.5,
    "results": {
      "port_scan": {
        "score": 85,
        "open_ports": [
          {
            "port": 80,
            "service": "HTTP",
            "state": "open"
          },
          {
            "port": 443,
            "service": "HTTPS",
            "state": "open"
          }
        ],
        "summary": "Found 2 open ports"
      },
      "ssl_tls": {
        "score": 90,
        "certificate": {
          "valid": true,
          "expires": "2025-12-31",
          "days_until_expiry": 355
        }
      },
      "vulnerabilities": {
        "score": 70,
        "vulnerabilities": [
          {
            "type": "Missing CSRF Protection",
            "severity": "medium",
            "description": "Form lacks CSRF token protection"
          }
        ]
      }
    }
  },
  "report_url": "/api/report/a1b2c3d4",
  "email_sent": true,
  "timestamp": "2025-01-10T12:05:30"
}
```

**Status Codes:**
- `200 OK` - Scan completed successfully
- `400 Bad Request` - Invalid input
- `500 Internal Server Error` - Scan failed

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com",
    "email": "user@example.com",
    "scan_type": "full"
  }'
```

---

### 3. Quick Security Check

Perform a fast security check (SSL and headers only).

**Endpoint:** `POST /api/quick-check`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "target": "https://example.com"
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "target": "https://example.com",
    "timestamp": "2025-01-10T12:00:00",
    "checks": {
      "ssl": {
        "valid": true,
        "expires": "2025-12-31",
        "days_until_expiry": 355,
        "score": 100
      },
      "headers": {
        "status_code": 200,
        "missing_critical_headers": [
          "Content-Security-Policy",
          "Strict-Transport-Security"
        ],
        "score": 60
      }
    },
    "quick_score": 76
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/quick-check \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com"}'
```

---

### 4. Download Report

Download PDF security report for a completed scan.

**Endpoint:** `GET /api/report/<scan_id>`

**Parameters:**
- `scan_id` (path parameter): The scan ID from the scan response

**Response:**
- Content-Type: `application/pdf`
- File download

**Status Codes:**
- `200 OK` - Report found and returned
- `404 Not Found` - Report not found

**cURL Example:**
```bash
curl -O http://localhost:5000/api/report/a1b2c3d4
```

**Browser:**
```
http://localhost:5000/api/report/a1b2c3d4
```

---

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

## Error Responses

All error responses follow this format:

```json
{
  "status": "error",
  "error": "Error description"
}
```

**Example:**
```json
{
  "status": "error",
  "error": "Target URL/IP is required"
}
```

## Security Score

Scores range from 0-100:
- **80-100**: Low Risk
- **60-79**: Medium Risk
- **40-59**: High Risk
- **0-39**: Critical Risk

## Risk Levels

- `LOW` - Minimal security concerns
- `MEDIUM` - Some issues require attention
- `HIGH` - Significant security vulnerabilities
- `CRITICAL` - Severe security problems

## Rate Limiting

Currently, no rate limiting is implemented. For production use, implement rate limiting to prevent abuse.

**Recommended limits:**
- 10 scans per hour per IP
- 100 API calls per hour per IP

## Best Practices

1. **Always use HTTPS** in production
2. **Implement authentication** for production APIs
3. **Rate limit** API endpoints
4. **Validate input** before scanning
5. **Log all scan requests** for audit purposes
6. **Only scan authorized targets**

## Integration Examples

### Python
```python
import requests
import json

url = "http://localhost:5000/api/scan"
payload = {
    "target": "https://example.com",
    "email": "user@example.com",
    "scan_type": "full"
}

response = requests.post(url, json=payload)
data = response.json()

if data['status'] == 'success':
    print(f"Scan ID: {data['scan_id']}")
    print(f"Security Score: {data['results']['security_score']}")
    print(f"Risk Level: {data['results']['risk_level']}")
```

### JavaScript (Node.js)
```javascript
const axios = require('axios');

async function scanTarget() {
  try {
    const response = await axios.post('http://localhost:5000/api/scan', {
      target: 'https://example.com',
      email: 'user@example.com',
      scan_type: 'full'
    });
    
    console.log('Scan ID:', response.data.scan_id);
    console.log('Security Score:', response.data.results.security_score);
    console.log('Risk Level:', response.data.results.risk_level);
  } catch (error) {
    console.error('Scan failed:', error.message);
  }
}

scanTarget();
```

### Bash
```bash
#!/bin/bash

# Perform scan
RESPONSE=$(curl -s -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com",
    "email": "user@example.com",
    "scan_type": "full"
  }')

# Extract scan ID
SCAN_ID=$(echo $RESPONSE | jq -r '.scan_id')

echo "Scan ID: $SCAN_ID"

# Download report
curl -O "http://localhost:5000/api/report/$SCAN_ID"
```

## Webhook Support (Future)

Future versions will support webhooks for asynchronous notifications:

```json
{
  "target": "https://example.com",
  "webhook_url": "https://your-server.com/webhook",
  "scan_type": "full"
}
```

## Versioning

Current API version: `v1`

Future versions will use URL versioning:
- `/api/v1/scan`
- `/api/v2/scan`

## Support

For API issues or questions:
- Review this documentation
- Check application logs
- Test with cURL examples
- Verify JSON formatting

---

**API Version:** 1.0.0  
**Last Updated:** 2025-01-10

