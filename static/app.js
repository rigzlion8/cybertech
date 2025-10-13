// CyberTech Security Scanner - Frontend JavaScript

const API_BASE_URL = window.location.origin;
let currentScanId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
});

function initializeForm() {
    const form = document.getElementById('scanForm');
    const scanTypeSelect = document.getElementById('scanType');
    const customOptions = document.getElementById('customOptions');
    
    // Handle scan type change
    scanTypeSelect.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
            customOptions.style.display = 'grid';
        } else {
            customOptions.style.display = 'none';
        }
    });
    
    // Handle form submission
    form.addEventListener('submit', handleScanSubmit);
}

async function handleScanSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    const target = formData.get('target');
    const email = formData.get('email');
    const scanType = formData.get('scanType');
    
    // Build scan options
    const options = {};
    if (scanType === 'custom') {
        options.port_scan = formData.get('port_scan') === 'on';
        options.vulnerability_scan = formData.get('vulnerability_scan') === 'on';
        options.ssl_check = formData.get('ssl_check') === 'on';
        options.headers_check = formData.get('headers_check') === 'on';
        options.password_check = formData.get('password_check') === 'on';
        options.database_check = formData.get('database_check') === 'on';
    }
    
    const payload = {
        target,
        email,
        scan_type: scanType,
        options
    };
    
    // Update UI
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            currentScanId = data.scan_id;
            displayResults(data.results);
            showAlert('Scan completed successfully! Report sent to your email.', 'success');
        } else {
            showAlert(data.error || 'Scan failed. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Scan error:', error);
        showAlert('Network error. Please check your connection and try again.', 'error');
    } finally {
        showLoading(false);
    }
}

function showLoading(loading) {
    const button = document.getElementById('scanButton');
    const buttonText = document.getElementById('buttonText');
    const buttonLoader = document.getElementById('buttonLoader');
    
    if (loading) {
        button.disabled = true;
        buttonText.textContent = 'Scanning...';
        buttonLoader.style.display = 'inline-block';
    } else {
        button.disabled = false;
        buttonText.textContent = 'Start Security Scan';
        buttonLoader.style.display = 'none';
    }
}

function displayResults(results) {
    const resultsContainer = document.getElementById('resultsContainer');
    const securityScore = document.getElementById('securityScore');
    const riskLevel = document.getElementById('riskLevel');
    const scanDuration = document.getElementById('scanDuration');
    const resultsDetails = document.getElementById('resultsDetails');
    
    // Update summary
    securityScore.textContent = `${results.security_score}/100`;
    securityScore.style.color = getScoreColor(results.security_score);
    
    riskLevel.textContent = results.risk_level;
    riskLevel.style.color = getRiskColor(results.risk_level);
    
    scanDuration.textContent = `${results.duration.toFixed(2)}s`;
    
    // Build detailed results
    let detailsHTML = '<h4 style="margin-bottom: 1rem;">Detailed Findings</h4>';
    
    const scanResults = results.results || {};
    
    for (const [category, categoryResults] of Object.entries(scanResults)) {
        if (typeof categoryResults === 'object') {
            detailsHTML += buildCategorySection(category, categoryResults);
        }
    }
    
    resultsDetails.innerHTML = detailsHTML;
    
    // Show results container
    resultsContainer.style.display = 'block';
    
    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function buildCategorySection(category, data) {
    const categoryName = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    let html = `
        <div style="margin-bottom: 2rem; padding: 1.5rem; background: #f8f9fa; border-radius: 8px;">
            <h5 style="margin-bottom: 1rem; color: #2c3e50; font-size: 1.2rem;">
                ${categoryName}
            </h5>
    `;
    
    // Score
    if (data.score !== undefined) {
        html += `
            <div style="margin-bottom: 1rem;">
                <strong>Score:</strong> 
                <span style="color: ${getScoreColor(data.score)}; font-size: 1.2rem; font-weight: bold;">
                    ${data.score}/100
                </span>
            </div>
        `;
    }
    
    // Summary
    if (data.summary) {
        html += `<p style="margin-bottom: 1rem;"><strong>Summary:</strong> ${data.summary}</p>`;
    }
    
    // Issues
    if (data.issues && data.issues.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Issues Found:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">';
        data.issues.forEach(issue => {
            const severity = issue.severity || 'MEDIUM';
            const severityColor = getSeverityColor(severity);
            html += `
                <li style="margin-bottom: 0.5rem;">
                    <span style="color: ${severityColor}; font-weight: bold;">
                        [${severity.toUpperCase()}]
                    </span>
                    ${issue.description || issue.issue || issue.type || 'No description'}
                </li>
            `;
        });
        html += '</ul></div>';
    }
    
    // Vulnerabilities
    if (data.vulnerabilities && data.vulnerabilities.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Vulnerabilities:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">';
        data.vulnerabilities.forEach(vuln => {
            const severity = vuln.severity || 'HIGH';
            const severityColor = getSeverityColor(severity);
            html += `
                <li style="margin-bottom: 0.5rem;">
                    <span style="color: ${severityColor}; font-weight: bold;">
                        [${severity.toUpperCase()}]
                    </span>
                    ${vuln.type || 'Vulnerability'}: ${vuln.description || 'No description'}
                </li>
            `;
        });
        html += '</ul></div>';
    }
    
    // Open Ports
    if (data.open_ports && data.open_ports.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Open Ports:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">';
        data.open_ports.forEach(port => {
            html += `<li>Port ${port.port}: ${port.service} (${port.state})</li>`;
        });
        html += '</ul></div>';
    }
    
    // Missing Headers
    if (data.missing_headers && data.missing_headers.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Missing Security Headers:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">';
        data.missing_headers.forEach(header => {
            html += `<li>${header.header} (${header.importance} importance)</li>`;
        });
        html += '</ul></div>';
    }
    
    // SQL Injection Points
    if (data.injection_points && data.injection_points.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Injection Points Found:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">';
        data.injection_points.forEach(point => {
            html += `<li style="color: #e74c3c; font-weight: bold;">⚠️ ${point}</li>`;
        });
        html += '</ul></div>';
    }
    
    // Sensitive Files Found (Directory Enumeration)
    if (data.sensitive_files_found && data.sensitive_files_found.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Sensitive Files Exposed:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">';
        data.sensitive_files_found.forEach(file => {
            const severity = file.severity || 'HIGH';
            const severityColor = getSeverityColor(severity);
            html += `
                <li style="margin-bottom: 0.5rem;">
                    <span style="color: ${severityColor}; font-weight: bold;">[${severity}]</span>
                    ${file.path || file.url || 'Unknown file'}
                    ${file.description ? `<br><small>${file.description}</small>` : ''}
                </li>
            `;
        });
        html += '</ul></div>';
    }
    
    // Admin Panels Found
    if (data.admin_panels_found && data.admin_panels_found.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Admin Panels Discovered:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">';
        data.admin_panels_found.forEach(panel => {
            html += `<li style="color: #e67e22; font-weight: bold;">🔐 ${panel.path || panel.url || 'Unknown path'}</li>`;
        });
        html += '</ul></div>';
    }
    
    // Directories Found
    if (data.directories_found && data.directories_found.length > 0 && data.directories_found.length <= 10) {
        html += '<div style="margin-top: 1rem;"><strong>Directories Found:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">';
        data.directories_found.forEach(dir => {
            html += `<li>📁 ${dir.path || dir.url || 'Unknown directory'}</li>`;
        });
        html += '</ul></div>';
    }
    
    // Risk Level Summary
    if (data.risk_level) {
        const riskColor = getRiskColor(data.risk_level);
        html += `
            <div style="margin-top: 1.5rem; padding: 1rem; background: rgba(${data.risk_level === 'CRITICAL' ? '231, 76, 60' : data.risk_level === 'HIGH' ? '230, 126, 34' : data.risk_level === 'MEDIUM' ? '243, 156, 18' : '39, 174, 96'}, 0.1); border-left: 4px solid ${riskColor}; border-radius: 4px;">
                <strong>Risk Level:</strong> <span style="color: ${riskColor}; font-weight: bold; font-size: 1.1rem;">${data.risk_level}</span>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

function getScoreColor(score) {
    if (score >= 80) return '#27ae60';
    if (score >= 60) return '#f39c12';
    if (score >= 40) return '#e67e22';
    return '#e74c3c';
}

function getRiskColor(risk) {
    const colors = {
        'LOW': '#27ae60',
        'MEDIUM': '#f39c12',
        'HIGH': '#e67e22',
        'CRITICAL': '#e74c3c'
    };
    return colors[risk] || '#95a5a6';
}

function getSeverityColor(severity) {
    // Handle undefined, null, or non-string values
    if (!severity || typeof severity !== 'string') {
        return '#95a5a6'; // Default gray color
    }
    
    const colors = {
        'low': '#3498db',
        'medium': '#f39c12',
        'high': '#e67e22',
        'critical': '#e74c3c'
    };
    return colors[severity.toLowerCase()] || '#95a5a6';
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const form = document.getElementById('scanForm');
    form.insertBefore(alertDiv, form.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function downloadReport() {
    if (currentScanId) {
        window.location.href = `${API_BASE_URL}/api/report/${currentScanId}`;
    }
}

function resetForm() {
    document.getElementById('scanForm').reset();
    document.getElementById('resultsContainer').style.display = 'none';
    currentScanId = null;
    
    // Scroll back to form
    document.getElementById('scan').scrollIntoView({ behavior: 'smooth' });
}

function scrollToScan() {
    document.getElementById('scan').scrollIntoView({ behavior: 'smooth' });
}

function scrollToFeatures() {
    document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
}

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

