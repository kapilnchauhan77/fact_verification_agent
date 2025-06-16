"""
HTML Report Generator for Fact Check Agent
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

class ReportGenerator:
    """Generate comprehensive HTML and JSON reports"""
    
    def __init__(self):
        """Initialize report generator"""
        self.html_template = self._get_html_template()
    
    def generate_json_report(self, results: Dict[str, Any], output_path: str = None) -> str:
        """
        Generate structured JSON report
        
        Args:
            results: Analysis results
            output_path: Optional output file path
            
        Returns:
            JSON report string
        """
        # Add metadata
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_version": "1.0",
                "generator": "Google ADK Fact Check Agent"
            },
            **results
        }
        
        json_report = json.dumps(report, indent=2, ensure_ascii=False)
        
        if output_path:
            Path(output_path).write_text(json_report, encoding='utf-8')
        
        return json_report
    
    def generate_html_report(self, results: Dict[str, Any], output_path: str = None) -> str:
        """
        Generate human-readable HTML report
        
        Args:
            results: Analysis results
            output_path: Optional output file path
            
        Returns:
            HTML report string
        """
        # Extract data for template
        template_data = self._prepare_template_data(results)
        
        # Generate HTML
        html_report = self.html_template.format(**template_data)
        
        if output_path:
            Path(output_path).write_text(html_report, encoding='utf-8')
        
        return html_report
    
    def _prepare_template_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for HTML template"""
        if not results.get('success', False):
            error_section = f'''
            <div class="error-message">
                <h2>Error Processing Document</h2>
                <p>{results.get('error', 'Unknown error')}</p>
            </div>
            '''
            return {
                'title': 'Fact Check Report - Error',
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_section': error_section,
                'content_section': ''
            }
        
        document_info = results.get('document_info', {})
        summary = results.get('summary', {})
        claims = results.get('claims', [])
        
        # Generate claims HTML
        claims_html = self._generate_claims_html(claims)
        
        # Determine overall score class for styling
        overall_score = summary.get('overall_authenticity_score', 0)
        if overall_score >= 0.8:
            score_class = 'highly-authentic'
        elif overall_score >= 0.6:
            score_class = 'mostly-authentic'
        elif overall_score >= 0.4:
            score_class = 'mixed-authenticity'
        elif overall_score >= 0.2:
            score_class = 'low-authenticity'
        else:
            score_class = 'unreliable'
        
        # Generate content section
        doc_info_html = ''
        if document_info:
            doc_info_html = f'''
            <div class="document-info">
                <h3>Document Information</h3>
                <p><strong>File:</strong> {document_info.get('file_name', 'N/A')}</p>
                <p><strong>Pages:</strong> {document_info.get('pages', 'N/A')}</p>
                <p><strong>Processing Method:</strong> {document_info.get('processing_method', 'N/A')}</p>
            </div>
            '''
        
        content_section = f'''
        <div class="summary-card">
            <h2>Analysis Summary</h2>
            
            {doc_info_html}
            
            <div class="overall-score {score_class}">
                <h3>Overall Authenticity</h3>
                <div class="score-number">{overall_score:.2f}</div>
                <p><strong>{summary.get('overall_authenticity_level', 'N/A')}</strong></p>
                <p>{summary.get('recommendation', 'No recommendation available')}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">{len(claims)}</div>
                    <div>Total Claims</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in claims if c.get('verification', {}).get('status') == 'verified'])}</div>
                    <div>Verified</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in claims if c.get('verification', {}).get('status') == 'disputed'])}</div>
                    <div>Disputed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len([c for c in claims if c.get('verification', {}).get('status') == 'unverified'])}</div>
                    <div>Unverified</div>
                </div>
            </div>
        </div>
        
        <div class="charts-section">
            <h2>Analytics & Visualizations</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <canvas id="statusChart"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="domainChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="claims-section">
            <h2>Detailed Claim Analysis</h2>
            {claims_html}
        </div>
        '''
        
        # Generate visualization data
        viz_scripts = self._generate_visualization_scripts(claims, summary)
        
        return {
            'title': f"Fact Check Report - {document_info.get('file_name', 'Text Analysis')}",
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_section': '',
            'content_section': content_section,
            'visualization_scripts': viz_scripts
        }
    
    def _generate_claims_html(self, claims: List[Dict[str, Any]]) -> str:
        """Generate HTML for claims section"""
        if not claims:
            return '<p class="no-claims">No claims found to analyze.</p>'
        
        claims_html = []
        
        for i, claim_data in enumerate(claims, 1):
            claim = claim_data.get('claim', {})
            verification = claim_data.get('verification', {})
            sources = claim_data.get('sources', [])
            
            # Determine status class
            status = verification.get('status', 'unknown')
            status_class = {
                'verified': 'status-verified',
                'disputed': 'status-disputed',
                'unverified': 'status-unverified',
                'error': 'status-error'
            }.get(status, 'status-unknown')
            
            # Generate sources HTML
            sources_html = self._generate_sources_html(sources)
            
            # Generate scoring breakdown HTML
            scoring_html = self._generate_scoring_html(claim_data.get('scoring_breakdown', {}))
            
            claim_html = f"""
            <div class="claim-card">
                <div class="claim-header">
                    <h3>Claim {i}</h3>
                    <span class="claim-status {status_class}">{status.upper()}</span>
                </div>
                
                <div class="claim-content">
                    <p class="claim-text">"{claim.get('text', 'N/A')}"</p>
                    
                    <div class="claim-details">
                        <div class="detail-row">
                            <strong>Type:</strong> {claim.get('type', 'N/A')}
                        </div>
                        <div class="detail-row">
                            <strong>Priority:</strong> {claim.get('priority', 'N/A')}
                        </div>
                        <div class="detail-row">
                            <strong>Confidence:</strong> {claim.get('confidence', 0):.2f}
                        </div>
                    </div>
                    
                    <div class="verification-section">
                        <h4>Verification Results</h4>
                        <div class="authenticity-score">
                            <strong>Authenticity Score:</strong> 
                            <span class="score">{verification.get('authenticity_score', 0):.2f}</span>
                        </div>
                        <p class="explanation">{verification.get('explanation', 'No explanation available')}</p>
                        
                        {scoring_html}
                        {sources_html}
                    </div>
                </div>
            </div>
            """
            
            claims_html.append(claim_html)
        
        return '\n'.join(claims_html)
    
    def _generate_sources_html(self, sources: List[Dict[str, Any]]) -> str:
        """Generate HTML for sources section"""
        if not sources:
            return '<p class="no-sources">No sources found.</p>'
        
        sources_html = ['<div class="sources-section"><h5>Sources:</h5><ul class="sources-list">']
        
        for source in sources:
            source_html = f"""
            <li class="source-item">
                <a href="{source.get('url', '#')}" target="_blank">{source.get('domain', 'Unknown domain')}</a>
                <span class="credibility-score">Credibility: {source.get('credibility_score', 0):.2f}</span>
                <span class="relevance-score">Relevance: {source.get('relevance_score', 0):.2f}</span>
            </li>
            """
            sources_html.append(source_html)
        
        sources_html.append('</ul></div>')
        return '\n'.join(sources_html)
    
    def _generate_scoring_html(self, scoring: Dict[str, Any]) -> str:
        """Generate HTML for scoring breakdown"""
        if not scoring:
            return ''
        
        scoring_html = ['<div class="scoring-breakdown"><h5>Scoring Breakdown:</h5><ul class="scoring-list">']
        
        scoring_labels = {
            'source_credibility': 'Source Credibility',
            'cross_reference': 'Cross Reference',
            'evidence_quality': 'Evidence Quality',
            'publication_date': 'Publication Date',
            'expert_consensus': 'Expert Consensus'
        }
        
        for key, value in scoring.items():
            label = scoring_labels.get(key, key.replace('_', ' ').title())
            scoring_html.append(f'<li><strong>{label}:</strong> {value:.2f}</li>')
        
        scoring_html.append('</ul></div>')
        return '\n'.join(scoring_html)
    
    def _generate_visualization_scripts(self, claims: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
        """Generate JavaScript for visualizations using Chart.js"""
        if not claims:
            return ''
        
        # Prepare data for charts
        status_counts = {}
        domain_scores = {}
        
        for claim_data in claims:
            # Count by status
            status = claim_data.get('verification', {}).get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Average scores by domain
            domain = claim_data.get('claim', {}).get('type', 'general')
            score = claim_data.get('verification', {}).get('authenticity_score', 0)
            if domain not in domain_scores:
                domain_scores[domain] = []
            domain_scores[domain].append(score)
        
        # Calculate average scores per domain
        domain_averages = {
            domain: sum(scores) / len(scores) 
            for domain, scores in domain_scores.items()
        }
        
        return f'''
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        // Status Distribution Chart
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {{
            type: 'doughnut',
            data: {{
                labels: {list(status_counts.keys())},
                datasets: [{{
                    data: {list(status_counts.values())},
                    backgroundColor: [
                        '#28a745', // verified - green
                        '#dc3545', // disputed - red  
                        '#ffc107', // unverified - yellow
                        '#6c757d'  // error/unknown - gray
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Claim Status Distribution'
                    }}
                }}
            }}
        }});
        
        // Domain Scores Chart
        const domainCtx = document.getElementById('domainChart').getContext('2d');
        new Chart(domainCtx, {{
            type: 'bar',
            data: {{
                labels: {list(domain_averages.keys())},
                datasets: [{{
                    label: 'Average Authenticity Score',
                    data: {list(domain_averages.values())},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 1.0
                    }}
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Average Authenticity Score by Domain'
                    }}
                }}
            }}
        }});
        </script>
        '''
    
    def _get_html_template(self) -> str:
        """Get HTML template"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        
        .generated-at {{
            margin-top: 10px;
            opacity: 0.9;
        }}
        
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .overall-score {{
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        
        .highly-authentic {{ background: linear-gradient(135deg, #4CAF50, #8BC34A); color: white; }}
        .mostly-authentic {{ background: linear-gradient(135deg, #8BC34A, #CDDC39); color: white; }}
        .mixed-authenticity {{ background: linear-gradient(135deg, #FF9800, #FFC107); color: white; }}
        .low-authenticity {{ background: linear-gradient(135deg, #FF5722, #FF9800); color: white; }}
        .unreliable {{ background: linear-gradient(135deg, #F44336, #FF5722); color: white; }}
        .error {{ background: linear-gradient(135deg, #9E9E9E, #607D8B); color: white; }}
        
        .score-number {{
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .charts-section {{
            margin-top: 30px;
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }}
        
        .chart-container {{
            position: relative;
            height: 300px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .claims-section {{
            margin-top: 30px;
        }}
        
        .claim-card {{
            background: white;
            margin-bottom: 25px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .claim-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .claim-header h3 {{
            margin: 0;
            color: #495057;
        }}
        
        .claim-status {{
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.8em;
        }}
        
        .status-verified {{ background: #d4edda; color: #155724; }}
        .status-disputed {{ background: #f8d7da; color: #721c24; }}
        .status-unverified {{ background: #fff3cd; color: #856404; }}
        .status-error {{ background: #f5c6cb; color: #721c24; }}
        
        .claim-content {{
            padding: 20px;
        }}
        
        .claim-text {{
            font-size: 1.1em;
            font-style: italic;
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin-bottom: 20px;
        }}
        
        .claim-details {{
            margin-bottom: 20px;
        }}
        
        .detail-row {{
            margin-bottom: 8px;
        }}
        
        .verification-section {{
            border-top: 1px solid #e9ecef;
            padding-top: 20px;
        }}
        
        .authenticity-score {{
            font-size: 1.2em;
            margin-bottom: 15px;
        }}
        
        .score {{
            font-weight: bold;
            color: #667eea;
        }}
        
        .explanation {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }}
        
        .scoring-breakdown, .sources-section {{
            margin-top: 15px;
        }}
        
        .scoring-list, .sources-list {{
            list-style: none;
            padding: 0;
        }}
        
        .scoring-list li {{
            padding: 5px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .source-item {{
            padding: 10px;
            background: #f8f9fa;
            margin-bottom: 5px;
            border-radius: 5px;
        }}
        
        .source-item a {{
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
        }}
        
        .credibility-score, .relevance-score {{
            margin-left: 10px;
            font-size: 0.9em;
            color: #6c757d;
        }}
        
        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            font-size: 1.1em;
        }}
        
        .no-claims, .no-sources {{
            text-align: center;
            color: #6c757d;
            font-style: italic;
        }}
        
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .header {{ padding: 20px; }}
            .header h1 {{ font-size: 2em; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="generated-at">Generated on {generated_at}</div>
    </div>
    
    {error_section}
    {content_section}
    {visualization_scripts}
</body>
</html>'''