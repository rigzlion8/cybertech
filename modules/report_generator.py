"""
Report Generator Module
Generates PDF and HTML security reports
"""

import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage
)
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Security report generator"""
    
    def __init__(self, scan_results):
        self.scan_results = scan_results
        self.scan_id = scan_results.get('scan_id', 'unknown')
        
    def generate_pdf_report(self):
        """Generate PDF security report"""
        try:
            # Create reports directory if it doesn't exist
            os.makedirs('reports', exist_ok=True)
            
            report_path = f'reports/scan_{self.scan_id}.pdf'
            
            # Create PDF document
            doc = SimpleDocTemplate(
                report_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build report content
            story = []
            styles = getSampleStyleSheet()
            
            # Add custom styles
            self._add_custom_styles(styles)
            
            # Title Page
            story.extend(self._create_title_page(styles))
            story.append(PageBreak())
            
            # Executive Summary
            story.extend(self._create_executive_summary(styles))
            story.append(Spacer(1, 0.2 * inch))
            
            # Security Score
            story.extend(self._create_security_score_section(styles))
            story.append(Spacer(1, 0.3 * inch))
            
            # Detailed Findings
            story.extend(self._create_detailed_findings(styles))
            
            # Recommendations
            story.append(PageBreak())
            story.extend(self._create_recommendations(styles))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            raise
    
    def _add_custom_styles(self, styles):
        """Add custom paragraph styles"""
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=HexColor('#7f8c8d'),
            alignment=TA_CENTER,
            spaceAfter=12
        ))
    
    def _create_title_page(self, styles):
        """Create title page"""
        elements = []
        
        # Title
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph(
            "CyberTech Security Report",
            styles['CustomTitle']
        ))
        
        # Target
        elements.append(Paragraph(
            f"Target: {self.scan_results.get('target', 'N/A')}",
            styles['Subtitle']
        ))
        
        # Date
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(
            f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            styles['Subtitle']
        ))
        
        # Scan ID
        elements.append(Paragraph(
            f"Scan ID: {self.scan_id}",
            styles['Subtitle']
        ))
        
        return elements
    
    def _create_executive_summary(self, styles):
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", styles['SectionHeader']))
        
        summary_text = f"""
        This report presents the findings of a comprehensive security assessment 
        performed on {self.scan_results.get('target')}. The assessment included 
        port scanning, vulnerability testing, SSL/TLS configuration review, 
        HTTP security headers analysis, and password security checks.
        """
        
        elements.append(Paragraph(summary_text, styles['Normal']))
        
        # Key findings table
        security_score = self.scan_results.get('security_score', 0)
        risk_level = self.scan_results.get('risk_level', 'UNKNOWN')
        
        # Determine color based on risk level
        risk_color = self._get_risk_color(risk_level)
        
        data = [
            ['Metric', 'Value'],
            ['Security Score', f'{security_score}/100'],
            ['Risk Level', risk_level],
            ['Scan Duration', f"{self.scan_results.get('duration', 0):.2f} seconds"],
            ['Scan Type', self.scan_results.get('scan_type', 'N/A').upper()]
        ]
        
        table = Table(data, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f0f0f0')])
        ]))
        
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(table)
        
        return elements
    
    def _create_security_score_section(self, styles):
        """Create security score visualization section"""
        elements = []
        
        elements.append(Paragraph("Security Assessment Overview", styles['SectionHeader']))
        
        results = self.scan_results.get('results', {})
        
        # Create scores table
        data = [['Category', 'Score', 'Status']]
        
        for category, category_results in results.items():
            if isinstance(category_results, dict) and 'score' in category_results:
                score = category_results.get('score', 0)
                status = self._get_status_from_score(score)
                data.append([
                    category.replace('_', ' ').title(),
                    f'{score}/100',
                    status
                ])
        
        if len(data) > 1:
            table = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 2 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#ecf0f1')])
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph("No detailed scores available.", styles['Normal']))
        
        return elements
    
    def _create_detailed_findings(self, styles):
        """Create detailed findings section"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Detailed Security Findings", styles['SectionHeader']))
        
        results = self.scan_results.get('results', {})
        
        # Port Scan Results
        if 'port_scan' in results:
            elements.extend(self._create_port_scan_section(results['port_scan'], styles))
        
        # Vulnerability Scan Results
        if 'vulnerabilities' in results:
            elements.extend(self._create_vulnerability_section(results['vulnerabilities'], styles))
        
        # SSL/TLS Results
        if 'ssl_tls' in results:
            elements.extend(self._create_ssl_section(results['ssl_tls'], styles))
        
        # Headers Results
        if 'headers' in results:
            elements.extend(self._create_headers_section(results['headers'], styles))
        
        # Password Security Results
        if 'passwords' in results:
            elements.extend(self._create_password_section(results['passwords'], styles))
        
        # Database Security Results
        if 'database' in results:
            elements.extend(self._create_database_section(results['database'], styles))
        
        return elements
    
    def _create_port_scan_section(self, port_results, styles):
        """Create port scan findings section"""
        elements = []
        
        elements.append(Paragraph("Port Scan Results", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))
        
        open_ports = port_results.get('open_ports', [])
        
        if open_ports:
            elements.append(Paragraph(
                f"Found {len(open_ports)} open ports:",
                styles['Normal']
            ))
            
            data = [['Port', 'Service', 'State']]
            for port_info in open_ports:
                data.append([
                    str(port_info.get('port', '')),
                    port_info.get('service', 'Unknown'),
                    port_info.get('state', 'open')
                ])
            
            table = Table(data, colWidths=[1.5 * inch, 2 * inch, 1.5 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#95a5a6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#ecf0f1')])
            ]))
            
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(table)
        else:
            elements.append(Paragraph("No open ports detected.", styles['Normal']))
        
        elements.append(Spacer(1, 0.2 * inch))
        return elements
    
    def _create_vulnerability_section(self, vuln_results, styles):
        """Create vulnerability findings section"""
        elements = []
        
        elements.append(Paragraph("Vulnerability Assessment", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))
        
        vulnerabilities = vuln_results.get('vulnerabilities', [])
        
        if vulnerabilities:
            elements.append(Paragraph(
                f"Found {len(vulnerabilities)} potential vulnerabilities:",
                styles['Normal']
            ))
            elements.append(Spacer(1, 0.1 * inch))
            
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'unknown').upper()
                severity_color = self._get_severity_color(severity)
                
                vuln_text = f"""
                <b>Type:</b> {vuln.get('type', 'Unknown')}<br/>
                <b>Severity:</b> <font color="{severity_color}">{severity}</font><br/>
                <b>Description:</b> {vuln.get('description', 'No description')}
                """
                
                elements.append(Paragraph(vuln_text, styles['Normal']))
                elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph(
                "No vulnerabilities detected.",
                styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.2 * inch))
        return elements
    
    def _create_ssl_section(self, ssl_results, styles):
        """Create SSL/TLS findings section"""
        elements = []
        
        elements.append(Paragraph("SSL/TLS Configuration", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))
        
        if 'error' not in ssl_results:
            cert = ssl_results.get('certificate', {})
            
            cert_text = f"""
            <b>Certificate Valid:</b> {cert.get('valid', 'Unknown')}<br/>
            <b>Expires:</b> {cert.get('expires', 'Unknown')}<br/>
            <b>Days Until Expiry:</b> {cert.get('days_until_expiry', 'Unknown')}<br/>
            <b>Issuer:</b> {cert.get('issuer', 'Unknown')}
            """
            
            elements.append(Paragraph(cert_text, styles['Normal']))
        else:
            elements.append(Paragraph(
                f"SSL/TLS Error: {ssl_results.get('error')}",
                styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.2 * inch))
        return elements
    
    def _create_headers_section(self, headers_results, styles):
        """Create headers findings section"""
        elements = []
        
        elements.append(Paragraph("HTTP Security Headers", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))
        
        missing_headers = headers_results.get('missing_headers', [])
        
        if missing_headers:
            elements.append(Paragraph(
                f"Missing {len(missing_headers)} security headers:",
                styles['Normal']
            ))
            
            for header in missing_headers:
                header_text = f"""
                <b>{header.get('header', 'Unknown')}</b> ({header.get('importance', 'unknown')} importance)<br/>
                {header.get('description', 'No description')}
                """
                elements.append(Paragraph(header_text, styles['Normal']))
                elements.append(Spacer(1, 0.05 * inch))
        else:
            elements.append(Paragraph(
                "All recommended security headers are present.",
                styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.2 * inch))
        return elements
    
    def _create_password_section(self, password_results, styles):
        """Create password security findings section"""
        elements = []
        
        elements.append(Paragraph("Password Security", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))
        
        security_issues = password_results.get('security_issues', [])
        
        if security_issues:
            for issue in security_issues:
                issue_text = f"""
                <b>Severity:</b> {issue.get('severity', 'unknown').upper()}<br/>
                <b>Issue:</b> {issue.get('issue', 'Unknown')}<br/>
                <b>Description:</b> {issue.get('description', 'No description')}
                """
                elements.append(Paragraph(issue_text, styles['Normal']))
                elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph(
                "No password security issues detected.",
                styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.2 * inch))
        return elements
    
    def _create_database_section(self, db_results, styles):
        """Create database security findings section"""
        elements = []
        
        elements.append(Paragraph("Database Security", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))
        
        security_issues = db_results.get('security_issues', [])
        
        if security_issues:
            for issue in security_issues:
                issue_text = f"""
                <b>Severity:</b> {issue.get('severity', 'unknown').upper()}<br/>
                <b>Issue:</b> {issue.get('issue', 'Unknown')}<br/>
                <b>Description:</b> {issue.get('description', 'No description')}
                """
                elements.append(Paragraph(issue_text, styles['Normal']))
                elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph(
                "No database security issues detected.",
                styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.2 * inch))
        return elements
    
    def _create_recommendations(self, styles):
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Recommendations", styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))
        
        recommendations = self._generate_recommendations()
        
        for i, rec in enumerate(recommendations, 1):
            rec_text = f"""
            <b>{i}. {rec['title']}</b><br/>
            Priority: {rec['priority']}<br/>
            {rec['description']}
            """
            elements.append(Paragraph(rec_text, styles['Normal']))
            elements.append(Spacer(1, 0.15 * inch))
        
        return elements
    
    def _generate_recommendations(self):
        """Generate prioritized recommendations based on findings"""
        recommendations = [
            {
                'title': 'Enable HTTPS with Strong SSL/TLS Configuration',
                'priority': 'HIGH',
                'description': 'Ensure all traffic is encrypted using TLS 1.2 or higher with strong cipher suites.'
            },
            {
                'title': 'Implement Security Headers',
                'priority': 'HIGH',
                'description': 'Add missing security headers including CSP, HSTS, and X-Frame-Options.'
            },
            {
                'title': 'Regular Security Audits',
                'priority': 'MEDIUM',
                'description': 'Conduct periodic security assessments to identify and remediate vulnerabilities.'
            },
            {
                'title': 'Password Policy Enhancement',
                'priority': 'MEDIUM',
                'description': 'Implement strong password policies and consider multi-factor authentication.'
            },
            {
                'title': 'Database Security Hardening',
                'priority': 'HIGH',
                'description': 'Use parameterized queries, disable error messages, and encrypt sensitive data.'
            }
        ]
        
        return recommendations
    
    def _get_risk_color(self, risk_level):
        """Get color for risk level"""
        colors_map = {
            'LOW': '#27ae60',
            'MEDIUM': '#f39c12',
            'HIGH': '#e67e22',
            'CRITICAL': '#c0392b'
        }
        return colors_map.get(risk_level, '#95a5a6')
    
    def _get_severity_color(self, severity):
        """Get color for severity"""
        colors_map = {
            'LOW': 'blue',
            'MEDIUM': 'orange',
            'HIGH': 'darkorange',
            'CRITICAL': 'red'
        }
        return colors_map.get(severity.upper(), 'gray')
    
    def _get_status_from_score(self, score):
        """Get status text from score"""
        if score >= 80:
            return '✓ Good'
        elif score >= 60:
            return '⚠ Fair'
        elif score >= 40:
            return '⚠ Poor'
        else:
            return '✗ Critical'

