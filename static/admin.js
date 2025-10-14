// CyberTech Admin Dashboard JavaScript

const API_BASE_URL = window.location.origin;
let currentPage = 1;
const itemsPerPage = 20;
let totalScans = 0;
let currentSearch = '';

// Chart instances
let dailyScansChart = null;
let avgScoresChart = null;
let riskTrendsChart = null;
let currentTrendDays = 30;

// Mobile Menu Toggle
function initializeMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            this.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking on a nav link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                mobileMenuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.nav') && !event.target.closest('.mobile-menu-toggle')) {
                mobileMenuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeMobileMenu();
    loadStatistics();
    loadTrends(30);
    loadScans();
    setupEventListeners();
});

function setupEventListeners() {
    // Search on Enter key
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchScans();
        }
    });

    // Close modal on outside click
    document.getElementById('scanModal').addEventListener('click', (e) => {
        if (e.target.id === 'scanModal') {
            closeModal();
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/statistics`);
        const data = await response.json();

        if (data.status === 'success') {
            const stats = data.statistics;
            
            document.getElementById('totalScans').textContent = stats.total_scans || 0;
            document.getElementById('avgScore').textContent = stats.average_score ? `${stats.average_score}/100` : '0/100';
            
            const riskDist = stats.risk_level_distribution || {};
            document.getElementById('highRiskScans').textContent = riskDist.HIGH || 0;
            document.getElementById('criticalScans').textContent = riskDist.CRITICAL || 0;
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

async function loadScans(page = 1) {
    try {
        const offset = (page - 1) * itemsPerPage;
        let url = `${API_BASE_URL}/api/admin/scans?limit=${itemsPerPage}&offset=${offset}`;
        
        if (currentSearch) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.status === 'success') {
            totalScans = data.total;
            displayScans(data.scans);
            updatePagination(page);
        } else {
            showError('Failed to load scans');
        }
    } catch (error) {
        console.error('Error loading scans:', error);
        showError('Network error. Please try again.');
    }
}

function displayScans(scans) {
    const tableContent = document.getElementById('tableContent');
    
    if (scans.length === 0) {
        tableContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>No Scans Found</h3>
                <p>There are no scan reports to display.</p>
            </div>
        `;
        document.getElementById('pagination').style.display = 'none';
        return;
    }

    let tableHTML = `
        <table class="scans-table">
            <thead>
                <tr>
                    <th>Scan ID</th>
                    <th>Target</th>
                    <th>Type</th>
                    <th>Security Score</th>
                    <th>Risk Level</th>
                    <th>Date</th>
                    <th>Duration</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    scans.forEach(scan => {
        const date = new Date(scan.start_time).toLocaleString();
        const scoreClass = getScoreClass(scan.security_score);
        
        tableHTML += `
            <tr onclick="viewScanDetails('${scan.scan_id}')">
                <td><strong>${scan.scan_id}</strong></td>
                <td>${escapeHtml(scan.target)}</td>
                <td><span style="text-transform: uppercase;">${scan.scan_type}</span></td>
                <td><span class="score-badge ${scoreClass}">${scan.security_score}/100</span></td>
                <td><span class="risk-badge ${scan.risk_level}">${scan.risk_level}</span></td>
                <td>${date}</td>
                <td>${scan.duration.toFixed(2)}s</td>
                <td onclick="event.stopPropagation()">
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="downloadReport('${scan.scan_id}')" title="Download Report">📄</button>
                        <button class="btn-icon delete" onclick="confirmDelete('${scan.scan_id}')" title="Delete">🗑️</button>
                    </div>
                </td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    tableContent.innerHTML = tableHTML;
    document.getElementById('pagination').style.display = 'flex';
}

function getScoreClass(score) {
    if (score >= 80) return 'high';
    if (score >= 60) return 'medium';
    return 'low';
}

function updatePagination(page) {
    currentPage = page;
    const totalPages = Math.ceil(totalScans / itemsPerPage);
    
    document.getElementById('paginationInfo').textContent = 
        `Page ${page} of ${totalPages} (${totalScans} total scans)`;
    
    document.getElementById('prevBtn').disabled = page === 1;
    document.getElementById('nextBtn').disabled = page >= totalPages;
}

function previousPage() {
    if (currentPage > 1) {
        loadScans(currentPage - 1);
    }
}

function nextPage() {
    const totalPages = Math.ceil(totalScans / itemsPerPage);
    if (currentPage < totalPages) {
        loadScans(currentPage + 1);
    }
}

function searchScans() {
    currentSearch = document.getElementById('searchInput').value.trim();
    currentPage = 1;
    loadScans(1);
}

function clearSearch() {
    currentSearch = '';
    document.getElementById('searchInput').value = '';
    currentPage = 1;
    loadScans(1);
}

function refreshScans() {
    loadStatistics();
    loadScans(currentPage);
}

async function viewScanDetails(scanId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/scan/${scanId}`);
        const data = await response.json();

        if (data.status === 'success') {
            displayScanDetails(data.scan);
        } else {
            showError('Failed to load scan details');
        }
    } catch (error) {
        console.error('Error loading scan details:', error);
        showError('Network error. Please try again.');
    }
}

function displayScanDetails(scan) {
    const modalBody = document.getElementById('modalBody');
    const results = scan.full_results || {};
    const scanResults = results.results || {};

    let detailsHTML = `
        <div class="detail-section">
            <h3>Overview</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Scan ID</div>
                    <div class="detail-value">${scan.scan_id}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Target</div>
                    <div class="detail-value">${escapeHtml(scan.target)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Scan Type</div>
                    <div class="detail-value" style="text-transform: uppercase;">${scan.scan_type}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Security Score</div>
                    <div class="detail-value" style="color: ${getScoreColor(scan.security_score)};">
                        ${scan.security_score}/100
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Risk Level</div>
                    <div class="detail-value">
                        <span class="risk-badge ${scan.risk_level}">${scan.risk_level}</span>
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Duration</div>
                    <div class="detail-value">${scan.duration.toFixed(2)}s</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Start Time</div>
                    <div class="detail-value">${new Date(scan.start_time).toLocaleString()}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value" style="text-transform: uppercase;">${scan.status}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3>Actions</h3>
            <div style="display: flex; gap: 1rem;">
                <button class="btn btn-primary" onclick="downloadReport('${scan.scan_id}')">
                    📄 Download PDF Report
                </button>
                <button class="btn btn-secondary" onclick="closeModal()">
                    Close
                </button>
            </div>
        </div>
    `;

    // Add detailed results for each category
    if (Object.keys(scanResults).length > 0) {
        detailsHTML += '<div class="detail-section"><h3>Detailed Results</h3>';

        for (const [category, categoryData] of Object.entries(scanResults)) {
            if (typeof categoryData === 'object') {
                detailsHTML += buildCategoryDetails(category, categoryData);
            }
        }

        detailsHTML += '</div>';
    }

    modalBody.innerHTML = detailsHTML;
    document.getElementById('scanModal').classList.add('active');
}

function buildCategoryDetails(category, data) {
    const categoryName = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    let html = `
        <div class="category-results">
            <div class="category-title">${categoryName}</div>
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
        html += `<p style="margin-bottom: 1rem;"><strong>Summary:</strong> ${escapeHtml(data.summary)}</p>`;
    }

    // Issues
    if (data.issues && data.issues.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Issues Found:</strong></div>';
        html += '<ul class="issue-list">';
        data.issues.forEach(issue => {
            const severity = (issue.severity || 'low').toLowerCase();
            html += `
                <li class="issue-item ${severity}">
                    <strong style="color: ${getSeverityColor(severity)};">
                        [${severity.toUpperCase()}]
                    </strong>
                    ${escapeHtml(issue.description || issue.issue || 'No description')}
                </li>
            `;
        });
        html += '</ul>';
    }

    // Vulnerabilities
    if (data.vulnerabilities && data.vulnerabilities.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Vulnerabilities:</strong></div>';
        html += '<ul class="issue-list">';
        data.vulnerabilities.forEach(vuln => {
            const severity = (vuln.severity || 'low').toLowerCase();
            html += `
                <li class="issue-item ${severity}">
                    <strong style="color: ${getSeverityColor(severity)};">
                        [${severity.toUpperCase()}]
                    </strong>
                    ${escapeHtml(vuln.type)}: ${escapeHtml(vuln.description)}
                </li>
            `;
        });
        html += '</ul>';
    }

    // Open Ports
    if (data.open_ports && data.open_ports.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Open Ports:</strong></div>';
        html += '<ul class="issue-list">';
        data.open_ports.forEach(port => {
            html += `
                <li class="issue-item">
                    Port <strong>${port.port}</strong>: ${escapeHtml(port.service)} (${port.state})
                </li>
            `;
        });
        html += '</ul>';
    }

    // Missing Headers
    if (data.missing_headers && data.missing_headers.length > 0) {
        html += '<div style="margin-top: 1rem;"><strong>Missing Security Headers:</strong></div>';
        html += '<ul class="issue-list">';
        data.missing_headers.forEach(header => {
            html += `
                <li class="issue-item">
                    <strong>${escapeHtml(header.header)}</strong> (${header.importance} importance)
                    ${header.description ? `<br><small>${escapeHtml(header.description)}</small>` : ''}
                </li>
            `;
        });
        html += '</ul>';
    }

    // SSL/TLS Certificate info
    if (data.certificate) {
        const cert = data.certificate;
        html += `
            <div style="margin-top: 1rem;">
                <strong>Certificate Information:</strong>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                    <li>Valid: ${cert.valid ? '✓ Yes' : '✗ No'}</li>
                    <li>Expires: ${escapeHtml(cert.expires || 'Unknown')}</li>
                    <li>Days Until Expiry: ${cert.days_until_expiry || 'Unknown'}</li>
                    <li>Issuer: ${escapeHtml(cert.issuer || 'Unknown')}</li>
                </ul>
            </div>
        `;
    }

    // Error
    if (data.error) {
        html += `
            <div style="margin-top: 1rem; padding: 1rem; background: #f8d7da; border-radius: 5px; color: #721c24;">
                <strong>Error:</strong> ${escapeHtml(data.error)}
            </div>
        `;
    }

    html += '</div>';
    return html;
}

function closeModal() {
    document.getElementById('scanModal').classList.remove('active');
}

function downloadReport(scanId) {
    window.open(`${API_BASE_URL}/api/report/${scanId}`, '_blank');
}

async function confirmDelete(scanId) {
    if (confirm(`Are you sure you want to delete scan ${scanId}? This action cannot be undone.`)) {
        await deleteScan(scanId);
    }
}

async function deleteScan(scanId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/scan/${scanId}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.status === 'success') {
            showSuccess('Scan deleted successfully');
            refreshScans();
        } else {
            showError('Failed to delete scan: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error deleting scan:', error);
        showError('Network error. Please try again.');
    }
}

function getScoreColor(score) {
    if (score >= 80) return '#27ae60';
    if (score >= 60) return '#f39c12';
    if (score >= 40) return '#e67e22';
    return '#e74c3c';
}

function getSeverityColor(severity) {
    const colors = {
        'low': '#3498db',
        'medium': '#f39c12',
        'high': '#e67e22',
        'critical': '#e74c3c'
    };
    return colors[severity.toLowerCase()] || '#95a5a6';
}

function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    alert('Success: ' + message);
}

// Trend Analysis Functions

async function loadTrends(days = 30) {
    try {
        currentTrendDays = days;
        const response = await fetch(`${API_BASE_URL}/api/admin/trends?days=${days}`);
        const data = await response.json();

        if (data.status === 'success') {
            displayTrends(data.trends);
        } else {
            showError('Failed to load trends');
        }
    } catch (error) {
        console.error('Error loading trends:', error);
        showError('Network error while loading trends.');
    }
}

function displayTrends(trends) {
    // Daily Scans Chart
    const dailyData = trends.daily_scans || [];
    const dates = dailyData.map(d => d._id);
    const scanCounts = dailyData.map(d => d.count);
    const avgScores = dailyData.map(d => d.avg_score || 0);

    // Create/Update Daily Scans Chart
    const dailyCtx = document.getElementById('dailyScansChart');
    if (dailyScansChart) {
        dailyScansChart.destroy();
    }
    dailyScansChart = new Chart(dailyCtx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Scans',
                data: scanCounts,
                backgroundColor: 'rgba(52, 152, 219, 0.6)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Create/Update Average Scores Chart
    const scoresCtx = document.getElementById('avgScoresChart');
    if (avgScoresChart) {
        avgScoresChart.destroy();
    }
    avgScoresChart = new Chart(scoresCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Avg Score',
                data: avgScores,
                fill: true,
                backgroundColor: 'rgba(46, 204, 113, 0.2)',
                borderColor: 'rgba(46, 204, 113, 1)',
                borderWidth: 2,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Risk Trends Chart
    const riskData = trends.risk_trends || [];
    const riskByDate = {};
    
    riskData.forEach(item => {
        const date = item._id.date;
        const risk = item._id.risk_level;
        if (!riskByDate[date]) {
            riskByDate[date] = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
        }
        riskByDate[date][risk] = item.count;
    });

    const riskDates = Object.keys(riskByDate).sort();
    const riskLevels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
    const riskColors = {
        'LOW': 'rgba(46, 204, 113, 0.8)',
        'MEDIUM': 'rgba(243, 156, 18, 0.8)',
        'HIGH': 'rgba(230, 126, 34, 0.8)',
        'CRITICAL': 'rgba(231, 76, 60, 0.8)'
    };

    const datasets = riskLevels.map(level => ({
        label: level,
        data: riskDates.map(date => riskByDate[date][level] || 0),
        backgroundColor: riskColors[level],
        borderColor: riskColors[level].replace('0.8', '1'),
        borderWidth: 1
    }));

    const riskCtx = document.getElementById('riskTrendsChart');
    if (riskTrendsChart) {
        riskTrendsChart.destroy();
    }
    riskTrendsChart = new Chart(riskCtx, {
        type: 'bar',
        data: {
            labels: riskDates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Top Targets List
    const topTargets = trends.top_targets || [];
    const topTargetsList = document.getElementById('topTargetsList');
    
    if (topTargets.length === 0) {
        topTargetsList.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 2rem;">No data available for this period</p>';
        return;
    }

    let html = '<div style="display: flex; flex-direction: column; gap: 0.5rem;">';
    topTargets.forEach((target, index) => {
        const scoreColor = getScoreColor(target.avg_score);
        html += `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.8rem; background: #f8f9fa; border-radius: 5px; cursor: pointer;"
                 onclick="viewTargetTrend('${escapeHtml(target._id)}')">
                <div style="flex: 1;">
                    <strong>${index + 1}. ${escapeHtml(target._id)}</strong>
                    <div style="font-size: 0.85rem; color: #7f8c8d;">
                        ${target.scan_count} scan${target.scan_count !== 1 ? 's' : ''}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; color: ${scoreColor};">
                        ${target.avg_score.toFixed(1)}/100
                    </div>
                    <div style="font-size: 0.85rem; color: #7f8c8d;">
                        Avg Score
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    topTargetsList.innerHTML = html;
}

async function viewTargetTrend(target) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/target/${encodeURIComponent(target)}/improvement`);
        const data = await response.json();

        if (data.status === 'success') {
            displayTargetTrendModal(data.improvement);
        } else {
            showError('Failed to load target trend');
        }
    } catch (error) {
        console.error('Error loading target trend:', error);
        showError('Network error while loading target trend.');
    }
}

function displayTargetTrendModal(improvement) {
    const modalBody = document.getElementById('modalBody');
    const scans = improvement.scans || [];

    let html = `
        <div class="detail-section">
            <h3>Target: ${escapeHtml(improvement.target)}</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Total Scans</div>
                    <div class="detail-value">${improvement.total_scans}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">First Score</div>
                    <div class="detail-value" style="color: ${getScoreColor(improvement.first_score)};">
                        ${improvement.first_score}/100
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Latest Score</div>
                    <div class="detail-value" style="color: ${getScoreColor(improvement.latest_score)};">
                        ${improvement.latest_score}/100
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Improvement</div>
                    <div class="detail-value" style="color: ${improvement.improvement >= 0 ? '#27ae60' : '#e74c3c'};">
                        ${improvement.improvement >= 0 ? '+' : ''}${improvement.improvement}
                    </div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3>Score History</h3>
            <div style="background: white; padding: 1.5rem; border-radius: 8px;">
                <canvas id="targetTrendChart"></canvas>
            </div>
        </div>

        <div class="detail-section">
            <h3>Scan History</h3>
            <div style="max-height: 300px; overflow-y: auto;">
    `;

    scans.forEach((scan, index) => {
        const date = new Date(scan.start_time).toLocaleString();
        html += `
            <div style="padding: 1rem; margin-bottom: 0.5rem; background: #f8f9fa; border-radius: 5px; cursor: pointer;"
                 onclick="closeModal(); viewScanDetails('${scan.scan_id}')">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${index + 1}. Scan ${scan.scan_id}</strong>
                        <div style="font-size: 0.85rem; color: #7f8c8d;">${date}</div>
                    </div>
                    <div>
                        <span class="score-badge ${getScoreClass(scan.security_score)}">
                            ${scan.security_score}/100
                        </span>
                        <span class="risk-badge ${scan.risk_level}">${scan.risk_level}</span>
                    </div>
                </div>
            </div>
        `;
    });

    html += `
            </div>
        </div>
    `;

    modalBody.innerHTML = html;
    document.getElementById('scanModal').classList.add('active');

    // Create trend chart
    const ctx = document.getElementById('targetTrendChart');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: scans.map((s, i) => `Scan ${i + 1}`),
            datasets: [{
                label: 'Security Score',
                data: scans.map(s => s.security_score),
                fill: true,
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Score: ${context.parsed.y}/100`;
                        }
                    }
                }
            }
        }
    });
}

