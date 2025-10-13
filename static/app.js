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
            
            // Always enable download button - payment modal will handle access
            const downloadBtn = document.getElementById('downloadBtn');
            downloadBtn.disabled = false;
            downloadBtn.style.opacity = '1';
            
            showAlert('Scan completed successfully! Click download to get your full report.', 'success');
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
    
    // Build detailed results - Show only 2 critical issues preview
    let detailsHTML = '<h4 style="margin-bottom: 1rem;">Security Assessment Results</h4>';
    
    const scanResults = results.results || {};
    
    // Collect all critical/high severity issues
    const criticalIssues = [];
    let totalIssuesCount = 0;
    
    for (const [category, categoryResults] of Object.entries(scanResults)) {
        if (typeof categoryResults === 'object') {
            // Check if scan found any vulnerabilities (vulnerable flag)
            if (categoryResults.vulnerable === true || categoryResults.risk_level === 'CRITICAL' || categoryResults.risk_level === 'HIGH') {
                // Add a generic critical issue for this category
                const categoryName = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                criticalIssues.push({
                    category: category,
                    type: `${categoryName} Vulnerability`,
                    severity: categoryResults.risk_level || 'HIGH',
                    description: `Critical security issues detected in ${categoryName}. Full details in report.`
                });
            }
            
            // Check vulnerabilities
            if (categoryResults.vulnerabilities && Array.isArray(categoryResults.vulnerabilities)) {
                categoryResults.vulnerabilities.forEach(vuln => {
                    const severity = vuln.severity || 'MEDIUM';
                    if (severity === 'CRITICAL' || severity === 'HIGH') {
                        totalIssuesCount++;
                        criticalIssues.push({
                            category: category,
                            type: vuln.type || 'Security Vulnerability',
                            severity: severity,
                            description: vuln.description || 'Critical vulnerability detected'
                        });
                    }
                });
            }
            
            // Check issues
            if (categoryResults.issues && Array.isArray(categoryResults.issues)) {
                categoryResults.issues.forEach(issue => {
                    const severity = issue.severity || 'MEDIUM';
                    if (severity === 'CRITICAL' || severity === 'HIGH') {
                        totalIssuesCount++;
                        criticalIssues.push({
                            category: category,
                            type: issue.type || 'Security Issue',
                            severity: severity,
                            description: issue.description || issue.issue || 'Security issue detected'
                        });
                    }
                });
            }
            
            // Check sensitive files
            if (categoryResults.sensitive_files_found && Array.isArray(categoryResults.sensitive_files_found)) {
                categoryResults.sensitive_files_found.forEach(file => {
                    const severity = file.severity || 'HIGH';
                    if (severity === 'CRITICAL' || severity === 'HIGH') {
                        totalIssuesCount++;
                        criticalIssues.push({
                            category: 'directory_enum',
                            type: file.type || 'Exposed File',
                            severity: severity,
                            description: file.description || `Critical file exposed: ${file.path}`
                        });
                    }
                });
            }
            
            // Check admin panels
            if (categoryResults.admin_panels_found && Array.isArray(categoryResults.admin_panels_found) && categoryResults.admin_panels_found.length > 0) {
                totalIssuesCount += categoryResults.admin_panels_found.length;
                criticalIssues.push({
                    category: 'directory_enum',
                    type: 'Admin Panel Exposed',
                    severity: 'HIGH',
                    description: `${categoryResults.admin_panels_found.length} admin panel(s) found accessible to public`
                });
            }
        }
    }
    
    // Use the count from critical issues if we collected detailed ones
    if (totalIssuesCount === 0) {
        totalIssuesCount = criticalIssues.length;
    }
    
    // Show only top 2 critical issues
    if (criticalIssues.length > 0) {
        detailsHTML += '<div style="background: #fff3cd; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; border-left: 4px solid #f39c12;">';
        detailsHTML += '<p style="margin: 0; font-weight: 600; color: #856404;">⚠️ We found critical security vulnerabilities in your website!</p>';
        detailsHTML += '</div>';
        
        const issuesToShow = criticalIssues.slice(0, 2);
        
        issuesToShow.forEach((issue, index) => {
            const severityColor = getSeverityColor(issue.severity);
            detailsHTML += `
                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid ${severityColor};">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="background: ${severityColor}; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.85rem; font-weight: bold;">
                            ${issue.severity}
                        </span>
                        <strong style="color: #2c3e50; font-size: 1.1rem;">${issue.type}</strong>
                    </div>
                    <p style="margin: 0; color: #555;">${issue.description}</p>
                </div>
            `;
        });
        
        if (totalIssuesCount > 2) {
            detailsHTML += `
                <div style="background: #e74c3c; color: white; padding: 1rem; border-radius: 8px; text-align: center; margin-top: 1.5rem;">
                    <strong>+ ${totalIssuesCount - 2} more critical issues found!</strong>
                </div>
            `;
        }
        
        detailsHTML += `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; text-align: center; margin-top: 2rem; color: white;">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.5rem;">🔒 Get Your Complete Security Report</h3>
                <p style="margin: 0 0 1.5rem 0; opacity: 0.9;">Download the full PDF report with detailed findings, remediation steps, and security recommendations</p>
                <ul style="text-align: left; max-width: 400px; margin: 0 auto 1.5rem auto; list-style: none; padding: 0;">
                    <li style="padding: 0.5rem 0;">✓ Comprehensive vulnerability analysis</li>
                    <li style="padding: 0.5rem 0;">✓ Step-by-step remediation guide</li>
                    <li style="padding: 0.5rem 0;">✓ All ${totalIssuesCount} security issues detailed</li>
                    <li style="padding: 0.5rem 0;">✓ Professional security report</li>
                </ul>
            </div>
        `;
    } else {
        detailsHTML += `
            <div style="background: #d4edda; padding: 1.5rem; border-radius: 8px; text-align: center; color: #155724; margin-bottom: 1.5rem;">
                <h3 style="margin: 0 0 0.5rem 0;">✓ Great News!</h3>
                <p style="margin: 0;">No critical security issues found. Your website appears to be well-protected.</p>
            </div>
            
            <div style="background: linear-gradient(135deg, #27ae60 0%, #229954 100%); padding: 2rem; border-radius: 12px; text-align: center; color: white;">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.5rem;">🔒 Get Your Detailed Security Report</h3>
                <p style="margin: 0 0 1.5rem 0; opacity: 0.9;">Download the complete PDF report with comprehensive analysis and security recommendations</p>
                <ul style="text-align: left; max-width: 400px; margin: 0 auto 1.5rem auto; list-style: none; padding: 0;">
                    <li style="padding: 0.5rem 0;">✓ Complete security assessment</li>
                    <li style="padding: 0.5rem 0;">✓ Best practices recommendations</li>
                    <li style="padding: 0.5rem 0;">✓ Security score breakdown</li>
                    <li style="padding: 0.5rem 0;">✓ Professional documentation</li>
                </ul>
            </div>
        `;
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
        const issueId = 'issues_' + Math.random().toString(36).substr(2, 9);
        const showLimit = 3;
        const hasMore = data.issues.length > showLimit;
        
        html += `<div style="margin-top: 1rem;"><strong>Issues Found (${data.issues.length}):</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">`;
        
        data.issues.forEach((issue, index) => {
            const severity = issue.severity || 'MEDIUM';
            const severityColor = getSeverityColor(severity);
            const hideClass = index >= showLimit ? 'hidden-item' : '';
            html += `
                <li class="${hideClass}" data-parent="${issueId}" style="margin-bottom: 0.5rem; ${index >= showLimit ? 'display: none;' : ''}">
                    <span style="color: ${severityColor}; font-weight: bold;">
                        [${severity.toUpperCase()}]
                    </span>
                    ${issue.description || issue.issue || issue.type || 'No description'}
                </li>
            `;
        });
        
        html += '</ul>';
        
        if (hasMore) {
            html += `
                <button onclick="toggleDetails('${issueId}')" id="btn_${issueId}" 
                    style="margin-top: 0.5rem; padding: 0.4rem 1rem; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem;">
                    Show ${data.issues.length - showLimit} More
                </button>
            `;
        }
        
        html += '</div>';
    }
    
    // Vulnerabilities
    if (data.vulnerabilities && data.vulnerabilities.length > 0) {
        const vulnId = 'vuln_' + Math.random().toString(36).substr(2, 9);
        const showLimit = 3;
        const hasMore = data.vulnerabilities.length > showLimit;
        
        html += `<div style="margin-top: 1rem;"><strong>Vulnerabilities (${data.vulnerabilities.length}):</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">`;
        
        data.vulnerabilities.forEach((vuln, index) => {
            const severity = vuln.severity || 'HIGH';
            const severityColor = getSeverityColor(severity);
            const hideClass = index >= showLimit ? 'hidden-item' : '';
            html += `
                <li class="${hideClass}" data-parent="${vulnId}" style="margin-bottom: 0.5rem; ${index >= showLimit ? 'display: none;' : ''}">
                    <span style="color: ${severityColor}; font-weight: bold;">
                        [${severity.toUpperCase()}]
                    </span>
                    ${vuln.type || 'Vulnerability'}: ${vuln.description || 'No description'}
                </li>
            `;
        });
        
        html += '</ul>';
        
        if (hasMore) {
            html += `
                <button onclick="toggleDetails('${vulnId}')" id="btn_${vulnId}" 
                    style="margin-top: 0.5rem; padding: 0.4rem 1rem; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem;">
                    Show ${data.vulnerabilities.length - showLimit} More
                </button>
            `;
        }
        
        html += '</div>';
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
        const fileId = 'files_' + Math.random().toString(36).substr(2, 9);
        const showLimit = 3;
        const hasMore = data.sensitive_files_found.length > showLimit;
        
        html += `<div style="margin-top: 1rem;"><strong>Sensitive Files Exposed (${data.sensitive_files_found.length}):</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">`;
        
        data.sensitive_files_found.forEach((file, index) => {
            const severity = file.severity || 'HIGH';
            const severityColor = getSeverityColor(severity);
            const hideClass = index >= showLimit ? 'hidden-item' : '';
            html += `
                <li class="${hideClass}" data-parent="${fileId}" style="margin-bottom: 0.5rem; ${index >= showLimit ? 'display: none;' : ''}">
                    <span style="color: ${severityColor}; font-weight: bold;">[${severity}]</span>
                    ${file.path || file.url || 'Unknown file'}
                    ${file.description ? `<br><small>${file.description}</small>` : ''}
                </li>
            `;
        });
        
        html += '</ul>';
        
        if (hasMore) {
            html += `
                <button onclick="toggleDetails('${fileId}')" id="btn_${fileId}" 
                    style="margin-top: 0.5rem; padding: 0.4rem 1rem; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem;">
                    Show ${data.sensitive_files_found.length - showLimit} More
                </button>
            `;
        }
        
        html += '</div>';
    }
    
    // Admin Panels Found
    if (data.admin_panels_found && data.admin_panels_found.length > 0) {
        const panelId = 'panels_' + Math.random().toString(36).substr(2, 9);
        const showLimit = 5;
        const hasMore = data.admin_panels_found.length > showLimit;
        
        html += `<div style="margin-top: 1rem;"><strong>Admin Panels Discovered (${data.admin_panels_found.length}):</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">`;
        
        data.admin_panels_found.forEach((panel, index) => {
            const hideClass = index >= showLimit ? 'hidden-item' : '';
            html += `
                <li class="${hideClass}" data-parent="${panelId}" style="color: #e67e22; font-weight: bold; margin-bottom: 0.5rem; ${index >= showLimit ? 'display: none;' : ''}">
                    🔐 ${panel.path || panel.url || 'Unknown path'}
                    ${panel.description ? `<br><small style="color: #7f8c8d; font-weight: normal;">${panel.description}</small>` : ''}
                </li>
            `;
        });
        
        html += '</ul>';
        
        if (hasMore) {
            html += `
                <button onclick="toggleDetails('${panelId}')" id="btn_${panelId}" 
                    style="margin-top: 0.5rem; padding: 0.4rem 1rem; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem;">
                    Show ${data.admin_panels_found.length - showLimit} More
                </button>
            `;
        }
        
        html += '</div>';
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

async function downloadReport() {
    if (!currentScanId) {
        showAlert('No scan ID available.', 'error');
        return;
    }
    
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn && downloadBtn.disabled) {
        showAlert('PDF report is not available for this scan.', 'error');
        return;
    }
    
    // Show payment modal
    showPaymentModal();
}

function showPaymentModal() {
    const modal = document.createElement('div');
    modal.id = 'paymentModal';
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h2 class="modal-title">Download Complete Security Report</h2>
                <button class="modal-close" onclick="closePaymentModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div id="paymentStatusDiv" style="display: none; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;"></div>
                
                <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; text-align: center;">
                    <h3 style="margin: 0 0 0.5rem 0; color: #1976d2; font-size: 1.8rem;">100 KSH</h3>
                    <p style="margin: 0; color: #555; font-size: 0.95rem;">One-time payment for full report access</p>
                </div>
                
                <h4 style="margin-bottom: 1rem; color: #2c3e50;">Choose Payment Method:</h4>
                
                <!-- M-Pesa Option -->
                <div id="mpesaSection" style="margin-bottom: 1.5rem;">
                    <div style="background: #27ae60; color: white; padding: 1rem 1.5rem; border-radius: 8px; cursor: pointer; margin-bottom: 1rem; transition: all 0.3s;" onclick="selectPaymentMethod('mpesa')">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 1rem;">
                                <span style="font-size: 2rem;">📱</span>
                                <div>
                                    <div style="font-weight: 700; font-size: 1.1rem;">Pay via M-Pesa</div>
                                    <div style="font-size: 0.9rem; opacity: 0.9;">Recommended for Kenyan users</div>
                                </div>
                            </div>
                            <span style="font-size: 1.5rem;">→</span>
                        </div>
                    </div>
                    
                    <div id="mpesaForm" style="display: none; padding: 1.5rem; background: #f8f9fa; border-radius: 8px;">
                        <div class="form-group" style="margin-bottom: 1rem;">
                            <label for="paymentPhone" style="display: block; margin-bottom: 0.5rem; font-weight: 600;">M-Pesa Phone Number</label>
                            <input 
                                type="tel" 
                                id="paymentPhone" 
                                placeholder="0712345678 or 254712345678"
                                style="width: 100%; padding: 0.75rem; border: 2px solid #ddd; border-radius: 8px; font-size: 1rem;"
                            >
                        </div>
                        <button onclick="processPayment('mpesa')" class="btn btn-primary" id="mpesaPayBtn" style="width: 100%; padding: 1rem; font-size: 1.1rem;">
                            💳 Pay 100 KSH via M-Pesa
                        </button>
                        <p style="font-size: 0.85rem; color: #7f8c8d; margin-top: 0.5rem; text-align: center;">You'll receive an STK push to complete payment</p>
                    </div>
                </div>
                
                <!-- Paystack Option -->
                <div id="paystackSection">
                    <div style="background: #3498db; color: white; padding: 1rem 1.5rem; border-radius: 8px; cursor: pointer; margin-bottom: 1rem; transition: all 0.3s;" onclick="selectPaymentMethod('paystack')">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 1rem;">
                                <span style="font-size: 2rem;">💳</span>
                                <div>
                                    <div style="font-weight: 700; font-size: 1.1rem;">Pay via Card (Paystack)</div>
                                    <div style="font-size: 0.9rem; opacity: 0.9;">Visa, Mastercard, International</div>
                                </div>
                            </div>
                            <span style="font-size: 1.5rem;">→</span>
                        </div>
                    </div>
                    
                    <div id="paystackForm" style="display: none; padding: 1.5rem; background: #f8f9fa; border-radius: 8px;">
                        <div class="form-group" style="margin-bottom: 1rem;">
                            <label for="paymentEmail" style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Email Address</label>
                            <input 
                                type="email" 
                                id="paymentEmail" 
                                placeholder="your@email.com"
                                style="width: 100%; padding: 0.75rem; border: 2px solid #ddd; border-radius: 8px; font-size: 1rem;"
                            >
                        </div>
                        <button onclick="processPayment('paystack')" class="btn btn-primary" id="paystackPayBtn" style="width: 100%; padding: 1rem; font-size: 1.1rem; background: #3498db;">
                            💳 Pay with Card
                        </button>
                        <p style="font-size: 0.85rem; color: #7f8c8d; margin-top: 0.5rem; text-align: center;">Secure payment via Paystack</p>
                    </div>
                </div>
                
                <hr style="margin: 1.5rem 0; border: none; border-top: 1px solid #ddd;">
                
                <div style="background: #fff3cd; padding: 1.2rem; border-radius: 8px; text-align: center;">
                    <strong style="color: #856404;">💎 Upgrade to Professional</strong>
                    <p style="margin: 0.5rem 0; color: #856404;">Get unlimited reports + advanced scans for 2,000 KSH/month</p>
                    <a href="/pricing" style="color: #3498db; font-weight: 600; text-decoration: none;">View Pricing →</a>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function selectPaymentMethod(method) {
    // Hide all forms
    document.getElementById('mpesaForm').style.display = 'none';
    document.getElementById('paystackForm').style.display = 'none';
    
    // Show selected form
    if (method === 'mpesa') {
        document.getElementById('mpesaForm').style.display = 'block';
        setTimeout(() => document.getElementById('paymentPhone').focus(), 100);
    } else if (method === 'paystack') {
        document.getElementById('paystackForm').style.display = 'block';
        setTimeout(() => document.getElementById('paymentEmail').focus(), 100);
    }
}

function closePaymentModal() {
    const modal = document.getElementById('paymentModal');
    if (modal) {
        modal.remove();
    }
    
    if (window.paymentStatusInterval) {
        clearInterval(window.paymentStatusInterval);
        window.paymentStatusInterval = null;
    }
}

async function processPayment(method) {
    const statusDiv = document.getElementById('paymentStatusDiv');
    let payBtn, identifier;
    
    if (method === 'mpesa') {
        identifier = document.getElementById('paymentPhone').value;
        payBtn = document.getElementById('mpesaPayBtn');
        
        if (!identifier) {
            showAlert('Please enter your M-Pesa phone number', 'error');
            return;
        }
    } else if (method === 'paystack') {
        identifier = document.getElementById('paymentEmail').value;
        payBtn = document.getElementById('paystackPayBtn');
        
        if (!identifier) {
            showAlert('Please enter your email address', 'error');
            return;
        }
    }
    
    statusDiv.style.display = 'block';
    statusDiv.style.background = '#fff3cd';
    statusDiv.style.color = '#856404';
    statusDiv.textContent = 'Initiating payment...';
    payBtn.disabled = true;
    
    try {
        let response;
        
        if (method === 'mpesa') {
            // M-Pesa payment
            response = await fetch(`${API_BASE_URL}/api/payment/initiate-report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    phone_number: identifier,
                    scan_id: currentScanId
                })
            });
        } else if (method === 'paystack') {
            // Paystack payment
            response = await fetch(`${API_BASE_URL}/api/payment/paystack/initialize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: identifier,
                    amount: 100,
                    type: 'report',
                    scan_id: currentScanId
                })
            });
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            if (data.already_paid) {
                statusDiv.style.background = '#d4edda';
                statusDiv.style.color = '#155724';
                statusDiv.textContent = '✓ Already paid! Downloading...';
                
                setTimeout(() => {
                    window.location.href = `${API_BASE_URL}/api/report/${currentScanId}?phone=${identifier}`;
                    closePaymentModal();
                }, 1000);
                return;
            }
            
            if (method === 'mpesa') {
                // M-Pesa flow: STK Push
                const checkoutId = data.checkout_request_id;
                
                statusDiv.style.background = '#e3f2fd';
                statusDiv.style.color = '#1976d2';
                statusDiv.innerHTML = `
                    <div>📱 Check your phone for M-Pesa prompt</div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem;">Enter your PIN to complete payment</div>
                    <div class="loading-spinner" style="margin: 1rem auto;"></div>
                `;
                
                // Start checking payment status
                startPaymentStatusCheck(checkoutId, identifier);
                
            } else if (method === 'paystack') {
                // Paystack flow: Redirect to payment page
                const authUrl = data.authorization_url;
                
                statusDiv.style.background = '#e3f2fd';
                statusDiv.style.color = '#1976d2';
                statusDiv.textContent = 'Redirecting to secure payment page...';
                
                setTimeout(() => {
                    window.location.href = authUrl;
                }, 1000);
            }
            
        } else {
            statusDiv.style.background = '#f8d7da';
            statusDiv.style.color = '#721c24';
            statusDiv.textContent = `Error: ${data.error || 'Failed to initiate payment'}`;
            payBtn.disabled = false;
        }
        
    } catch (error) {
        console.error('Payment error:', error);
        statusDiv.style.background = '#f8d7da';
        statusDiv.style.color = '#721c24';
        statusDiv.textContent = 'Network error. Please try again.';
        payBtn.disabled = false;
    }
}

function startPaymentStatusCheck(checkoutId, phoneNumber) {
    let attempts = 0;
    const maxAttempts = 60;
    
    window.paymentStatusInterval = setInterval(async () => {
        attempts++;
        
        if (attempts > maxAttempts) {
            clearInterval(window.paymentStatusInterval);
            const statusDiv = document.getElementById('paymentStatusDiv');
            statusDiv.style.background = '#f8d7da';
            statusDiv.style.color = '#721c24';
            statusDiv.textContent = 'Payment timeout. Please try again.';
            document.getElementById('payNowBtn').disabled = false;
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/payment/status/${checkoutId}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.payment.found) {
                const paymentStatus = data.payment.status;
                const statusDiv = document.getElementById('paymentStatusDiv');
                
                if (paymentStatus === 'completed') {
                    clearInterval(window.paymentStatusInterval);
                    
                    statusDiv.style.background = '#d4edda';
                    statusDiv.style.color = '#155724';
                    statusDiv.innerHTML = `
                        <div>✓ Payment Successful!</div>
                        <div style="margin-top: 0.5rem;">Receipt: ${data.payment.mpesa_receipt || 'Processing'}</div>
                        <div style="margin-top: 0.5rem; font-size: 0.9rem;">Downloading report...</div>
                    `;
                    
                    // Download report
                    setTimeout(() => {
                        window.location.href = `${API_BASE_URL}/api/report/${currentScanId}?phone=${phoneNumber}`;
                        setTimeout(() => closePaymentModal(), 1000);
                    }, 1000);
                    
                } else if (paymentStatus === 'failed') {
                    clearInterval(window.paymentStatusInterval);
                    
                    statusDiv.style.background = '#f8d7da';
                    statusDiv.style.color = '#721c24';
                    statusDiv.textContent = 'Payment failed or was cancelled. Please try again.';
                    document.getElementById('payNowBtn').disabled = false;
                }
            }
            
        } catch (error) {
            console.error('Status check error:', error);
        }
        
    }, 2000);
}

function openSubscriptionModal() {
    document.getElementById('subscriptionModal').classList.add('active');
}

function closeSubscriptionModal() {
    document.getElementById('subscriptionModal').classList.remove('active');
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

// Show all category sections
function showAllCategories() {
    const hiddenCategories = document.querySelectorAll('.hidden-category');
    const readMoreBtn = document.getElementById('readMoreBtn');
    
    hiddenCategories.forEach(category => {
        category.style.display = 'block';
        category.style.animation = 'fadeIn 0.3s ease-in';
    });
    
    if (readMoreBtn) {
        readMoreBtn.style.display = 'none';
    }
}

// Toggle details for issues/vulnerabilities within a category
function toggleDetails(parentId) {
    const hiddenItems = document.querySelectorAll(`[data-parent="${parentId}"]`);
    const button = document.getElementById(`btn_${parentId}`);
    
    if (!button) return;
    
    const isExpanded = button.textContent.includes('Show Less');
    
    hiddenItems.forEach(item => {
        if (isExpanded) {
            item.style.display = 'none';
        } else {
            item.style.display = 'list-item';
            item.style.animation = 'fadeIn 0.2s ease-in';
        }
    });
    
    if (isExpanded) {
        const hiddenCount = hiddenItems.length;
        button.textContent = `Show ${hiddenCount} More`;
        button.style.background = '#3498db';
    } else {
        button.textContent = 'Show Less';
        button.style.background = '#95a5a6';
    }
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

