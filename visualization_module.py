"""
Pakistan Banking Compliance & Complaint Analysis System (PBCCAS)
Bank Records Visualization and Reporting Module

This module provides comprehensive visualization capabilities for bank records,
compliance monitoring, and investigation reports with export in multiple formats.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import io
import base64
from pathlib import Path
import openpyxl
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from jinja2 import Template
import networkx as nx
from geopy.geocoders import Nominatim
import folium
from sqlalchemy import create_engine
import asyncio

@dataclass
class TransactionNode:
    """Node in transaction flow network"""
    account_id: str
    bank_name: str
    account_holder: str
    location: str
    account_type: str
    balance: float
    risk_score: float

@dataclass
class TransactionEdge:
    """Edge in transaction flow network"""
    from_account: str
    to_account: str
    amount: float
    timestamp: datetime
    transaction_type: str
    reference: str
    fees: float
    is_suspicious: bool

@dataclass
class ComplianceMetric:
    """Compliance monitoring metric"""
    metric_name: str
    current_value: float
    threshold: float
    status: str  # 'compliant', 'warning', 'violation'
    last_updated: datetime
    description: str

class BankRecordsVisualizer:
    """Main visualization engine for bank records and compliance monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine = create_engine(config['database_url'])
        self.geolocator = Nominatim(user_agent="pbccas_visualizer")
        
        # Pakistan-specific styling
        self.pakistan_colors = {
            'primary': '#1B4F3A',    # Pakistan flag green
            'secondary': '#FFFFFF',   # White
            'accent': '#C8102E',      # Pakistani red
            'warning': '#FFA500',     # Orange
            'danger': '#DC3545',      # Red
            'success': '#28A745',     # Green
            'info': '#17A2B8'         # Blue
        }
        
        # Setup plotting styles
        self.setup_plotting_style()

    def setup_plotting_style(self):
        """Configure consistent styling for all visualizations"""
        plt.style.use('seaborn-v0_8')
        sns.set_palette([self.pakistan_colors['primary'], 
                        self.pakistan_colors['accent'],
                        self.pakistan_colors['info'],
                        self.pakistan_colors['warning']])

    async def create_transaction_flow_diagram(self, 
                                           transactions: List[TransactionEdge],
                                           accounts: List[TransactionNode]) -> Dict[str, Any]:
        """Create interactive transaction flow network visualization"""
        
        # Create network graph
        G = nx.DiGraph()
        
        # Add nodes
        for account in accounts:
            G.add_node(account.account_id, 
                      bank_name=account.bank_name,
                      account_holder=account.account_holder,
                      balance=account.balance,
                      risk_score=account.risk_score,
                      location=account.location)
        
        # Add edges
        for transaction in transactions:
            G.add_edge(transaction.from_account, 
                      transaction.to_account,
                      amount=transaction.amount,
                      timestamp=transaction.timestamp,
                      is_suspicious=transaction.is_suspicious,
                      fees=transaction.fees)
        
        # Calculate layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Create edge traces
        edge_traces = []
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            # Color based on suspicion level
            color = self.pakistan_colors['danger'] if edge[2]['is_suspicious'] else self.pakistan_colors['primary']
            width = min(max(edge[2]['amount'] / 100000, 1), 10)  # Scale line width by amount
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=width, color=color),
                hoverinfo='none',
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        for node in G.nodes(data=True):
            x, y = pos[node[0]]
            node_x.append(x)
            node_y.append(y)
            
            # Node info
            info = f"Account: {node[0]}<br>"
            info += f"Bank: {node[1]['bank_name']}<br>"
            info += f"Holder: {node[1]['account_holder']}<br>"
            info += f"Balance: PKR {node[1]['balance']:,.2f}<br>"
            info += f"Risk Score: {node[1]['risk_score']:.2f}"
            node_text.append(info)
            
            # Color by risk score
            if node[1]['risk_score'] > 0.7:
                node_color.append(self.pakistan_colors['danger'])
            elif node[1]['risk_score'] > 0.4:
                node_color.append(self.pakistan_colors['warning'])
            else:
                node_color.append(self.pakistan_colors['success'])
            
            # Size by balance
            size = min(max(node[1]['balance'] / 1000000 * 20, 10), 50)
            node_size.append(size)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[node[1]['account_holder'][:10] for node in G.nodes(data=True)],
            textposition="middle center",
            hovertext=node_text,
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='white')
            )
        )
        
        # Create figure
        fig = go.Figure(data=[node_trace] + edge_traces,
                       layout=go.Layout(
                           title=dict(
                               text='Transaction Flow Analysis',
                               x=0.5,
                               font=dict(size=20, color=self.pakistan_colors['primary'])
                           ),
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Node size = Account Balance | Color = Risk Level | Line width = Transaction Amount",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color=self.pakistan_colors['primary'], size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='white'
                       ))
        
        return {
            'plotly_json': fig.to_json(),
            'html': fig.to_html(include_plotlyjs=True),
            'network_stats': {
                'total_nodes': G.number_of_nodes(),
                'total_edges': G.number_of_edges(),
                'suspicious_transactions': sum(1 for _, _, d in G.edges(data=True) if d['is_suspicious']),
                'total_amount': sum(d['amount'] for _, _, d in G.edges(data=True)),
                'high_risk_accounts': sum(1 for _, d in G.nodes(data=True) if d['risk_score'] > 0.7)
            }
        }

    async def create_compliance_dashboard(self, 
                                        compliance_metrics: List[ComplianceMetric],
                                        time_period: str = '30d') -> Dict[str, Any]:
        """Create comprehensive compliance monitoring dashboard"""
        
        # Create subplot layout
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'Compliance Status Overview',
                'Risk Trend Analysis',
                'Violation Types Distribution',
                'Geographic Risk Distribution',
                'Regulatory Timeline Compliance',
                'Financial Impact Assessment'
            ],
            specs=[
                [{"type": "indicator"}, {"type": "scatter"}],
                [{"type": "pie"}, {"type": "mapbox"}],
                [{"type": "bar"}, {"type": "bar"}]
            ]
        )
        
        # 1. Compliance Status Gauge
        compliant_count = sum(1 for m in compliance_metrics if m.status == 'compliant')
        total_count = len(compliance_metrics)
        compliance_percentage = (compliant_count / total_count) * 100 if total_count > 0 else 0
        
        gauge_color = (self.pakistan_colors['success'] if compliance_percentage >= 90 
                      else self.pakistan_colors['warning'] if compliance_percentage >= 70 
                      else self.pakistan_colors['danger'])
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=compliance_percentage,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Overall Compliance"},
                delta={'reference': 95, 'increasing': {'color': self.pakistan_colors['success']}},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': gauge_color},
                    'steps': [
                        {'range': [0, 70], 'color': self.pakistan_colors['danger']},
                        {'range': [70, 90], 'color': self.pakistan_colors['warning']},
                        {'range': [90, 100], 'color': self.pakistan_colors['success']}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 95
                    }
                }
            ),
            row=1, col=1
        )
        
        # 2. Risk Trend (sample data)
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), 
                             end=datetime.now(), freq='D')
        risk_scores = np.random.uniform(0.2, 0.8, len(dates))
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=risk_scores,
                mode='lines+markers',
                name='Risk Score',
                line=dict(color=self.pakistan_colors['accent'], width=3)
            ),
            row=1, col=2
        )
        
        # 3. Violation Types Pie Chart
        violation_counts = {
            'AML Violations': 5,
            'Late Reporting': 12,
            'Documentation Issues': 8,
            'Customer Complaints': 15,
            'Interest Rate Violations': 3
        }
        
        fig.add_trace(
            go.Pie(
                labels=list(violation_counts.keys()),
                values=list(violation_counts.values()),
                hole=0.4,
                marker_colors=[self.pakistan_colors['danger'], 
                              self.pakistan_colors['warning'],
                              self.pakistan_colors['info'],
                              self.pakistan_colors['accent'],
                              self.pakistan_colors['primary']]
            ),
            row=2, col=1
        )
        
        # 4. Geographic Risk Map (Pakistan cities)
        pakistan_cities = [
            {'city': 'Karachi', 'lat': 24.8607, 'lon': 67.0011, 'risk': 0.7, 'violations': 25},
            {'city': 'Lahore', 'lat': 31.5804, 'lon': 74.3587, 'risk': 0.5, 'violations': 18},
            {'city': 'Islamabad', 'lat': 33.6844, 'lon': 73.0479, 'risk': 0.3, 'violations': 8},
            {'city': 'Faisalabad', 'lat': 31.4504, 'lon': 73.1350, 'risk': 0.6, 'violations': 12},
            {'city': 'Rawalpindi', 'lat': 33.5956, 'lon': 73.0393, 'risk': 0.4, 'violations': 10}
        ]
        
        fig.add_trace(
            go.Scattermapbox(
                lat=[city['lat'] for city in pakistan_cities],
                lon=[city['lon'] for city in pakistan_cities],
                mode='markers',
                marker=dict(
                    size=[city['violations'] for city in pakistan_cities],
                    color=[city['risk'] for city in pakistan_cities],
                    colorscale='Reds',
                    sizemode='diameter',
                    sizeref=0.5,
                    sizemin=5
                ),
                text=[f"{city['city']}<br>Risk: {city['risk']}<br>Violations: {city['violations']}" 
                      for city in pakistan_cities],
                hovertemplate='%{text}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # 5. Regulatory Timeline Compliance
        regulations = ['SBP Reporting', 'NAB Compliance', 'AML Filing', 'CRPC Requirements']
        compliance_days = [2, 5, 1, 8]  # Days overdue (negative = early)
        required_days = [3, 7, 3, 10]
        
        colors_timeline = [self.pakistan_colors['success'] if days <= 0 
                          else self.pakistan_colors['warning'] if days <= req/2 
                          else self.pakistan_colors['danger'] 
                          for days, req in zip(compliance_days, required_days)]
        
        fig.add_trace(
            go.Bar(
                x=regulations,
                y=compliance_days,
                marker_color=colors_timeline,
                text=[f"{days} days" for days in compliance_days],
                textposition='outside'
            ),
            row=3, col=1
        )
        
        # 6. Financial Impact
        impact_categories = ['Fines', 'Penalties', 'Lost Revenue', 'Remediation Costs']
        impact_amounts = [5000000, 2000000, 8000000, 3000000]  # PKR
        
        fig.add_trace(
            go.Bar(
                x=impact_categories,
                y=impact_amounts,
                marker_color=self.pakistan_colors['accent'],
                text=[f"PKR {amount/1000000:.1f}M" for amount in impact_amounts],
                textposition='outside'
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=1200,
            title_text="Pakistan Banking Compliance Dashboard",
            title_x=0.5,
            title_font=dict(size=24, color=self.pakistan_colors['primary']),
            showlegend=False,
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=30.3753, lon=69.3451),  # Pakistan center
                zoom=5
            )
        )
        
        return {
            'plotly_json': fig.to_json(),
            'html': fig.to_html(include_plotlyjs=True),
            'summary_stats': {
                'overall_compliance': compliance_percentage,
                'total_violations': sum(violation_counts.values()),
                'financial_impact': sum(impact_amounts),
                'high_risk_cities': len([c for c in pakistan_cities if c['risk'] > 0.6])
            }
        }

    async def create_investigation_timeline(self, 
                                          investigation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create timeline visualization for investigation progress"""
        
        # Sample investigation timeline data
        timeline_events = [
            {'date': '2024-01-15', 'event': 'Complaint Received', 'status': 'completed', 'responsible': 'Customer Service'},
            {'date': '2024-01-16', 'event': 'Initial Assessment', 'status': 'completed', 'responsible': 'Investigation Team'},
            {'date': '2024-01-18', 'event': 'Document Collection', 'status': 'completed', 'responsible': 'Investigation Team'},
            {'date': '2024-01-22', 'event': 'SBP Notification', 'status': 'completed', 'responsible': 'Compliance Officer'},
            {'date': '2024-01-25', 'event': 'Witness Statements', 'status': 'in_progress', 'responsible': 'Investigation Team'},
            {'date': '2024-02-01', 'event': 'Technical Analysis', 'status': 'pending', 'responsible': 'IT Forensics'},
            {'date': '2024-02-10', 'event': 'Legal Review', 'status': 'pending', 'responsible': 'Legal Department'},
            {'date': '2024-02-20', 'event': 'Final Report', 'status': 'pending', 'responsible': 'Investigation Team'}
        ]
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(timeline_events)
        df['date'] = pd.to_datetime(df['date'])
        df['days_from_start'] = (df['date'] - df['date'].min()).dt.days
        
        # Create Gantt-style timeline
        fig = go.Figure()
        
        # Color mapping for status
        status_colors = {
            'completed': self.pakistan_colors['success'],
            'in_progress': self.pakistan_colors['warning'],
            'pending': self.pakistan_colors['info']
        }
        
        # Add timeline bars
        for i, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['date'], row['date']],
                y=[i-0.4, i+0.4],
                mode='lines',
                line=dict(color=status_colors[row['status']], width=20),
                showlegend=False,
                hovertemplate=f"<b>{row['event']}</b><br>" +
                             f"Date: {row['date'].strftime('%Y-%m-%d')}<br>" +
                             f"Status: {row['status']}<br>" +
                             f"Responsible: {row['responsible']}<extra></extra>"
            ))
            
            # Add event labels
            fig.add_annotation(
                x=row['date'],
                y=i,
                text=row['event'],
                showarrow=False,
                font=dict(color='white', size=10),
                bgcolor=status_colors[row['status']],
                bordercolor='white',
                borderwidth=1
            )
        
        # Add today's date line
        today = datetime.now()
        fig.add_vline(
            x=today,
            line_dash="dash",
            line_color=self.pakistan_colors['accent'],
            annotation_text="Today",
            annotation_position="top"
        )
        
        fig.update_layout(
            title="Investigation Timeline",
            xaxis_title="Date",
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(df))),
                ticktext=df['responsible'].tolist(),
                title="Responsible Team"
            ),
            height=600,
            hovermode='closest'
        )
        
        return {
            'plotly_json': fig.to_json(),
            'html': fig.to_html(include_plotlyjs=True),
            'timeline_stats': {
                'total_events': len(timeline_events),
                'completed_events': len([e for e in timeline_events if e['status'] == 'completed']),
                'progress_percentage': len([e for e in timeline_events if e['status'] == 'completed']) / len(timeline_events) * 100,
                'estimated_completion': max(df['date']).strftime('%Y-%m-%d')
            }
        }

    async def export_to_excel(self, data: Dict[str, Any], filename: str) -> str:
        """Export visualization data to Excel format"""
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([{
                'Report Type': 'Banking Compliance Analysis',
                'Generated Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Total Records': len(data.get('transactions', [])),
                'Compliance Status': data.get('compliance_percentage', 0),
                'Total Violations': data.get('total_violations', 0)
            }])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Transactions sheet
            if 'transactions' in data:
                transactions_df = pd.DataFrame(data['transactions'])
                transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Compliance metrics sheet
            if 'compliance_metrics' in data:
                compliance_df = pd.DataFrame(data['compliance_metrics'])
                compliance_df.to_excel(writer, sheet_name='Compliance', index=False)
            
            # Violations sheet
            if 'violations' in data:
                violations_df = pd.DataFrame(data['violations'])
                violations_df.to_excel(writer, sheet_name='Violations', index=False)
        
        return filename

    async def export_to_pdf(self, data: Dict[str, Any], filename: str) -> str:
        """Export comprehensive report to PDF format"""
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(self.pakistan_colors['primary']),
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Title
        story.append(Paragraph("Pakistan Banking Compliance Report", title_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_text = f"""
        This report provides a comprehensive analysis of banking compliance and complaint investigation
        for the period under review. The analysis covers {len(data.get('transactions', []))} transactions
        with an overall compliance rate of {data.get('compliance_percentage', 0):.1f}%.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Key Findings
        story.append(Paragraph("Key Findings", styles['Heading2']))
        findings = [
            f"Total Compliance Violations: {data.get('total_violations', 0)}",
            f"High-Risk Transactions: {data.get('high_risk_transactions', 0)}",
            f"Regulatory Notifications Required: {data.get('regulatory_notifications', 0)}",
            f"Estimated Financial Impact: PKR {data.get('financial_impact', 0):,.2f}"
        ]
        
        for finding in findings:
            story.append(Paragraph(f"• {finding}", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Legal Compliance Section
        story.append(Paragraph("Legal Compliance Analysis", styles['Heading2']))
        legal_text = """
        The analysis has been conducted in accordance with Pakistan's banking regulations including:
        • Code of Criminal Procedure (CRPC) - Sections 154, 161, 173
        • National Accountability Bureau (NAB) Ordinance - Sections 9, 15
        • State Bank of Pakistan (SBP) Banking Policies
        • Anti-Money Laundering (AML) Act 2010
        """
        story.append(Paragraph(legal_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return filename

    async def create_risk_heatmap(self, risk_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create geographic risk heatmap for Pakistan"""
        
        # Pakistan provinces and major cities
        pakistan_locations = {
            'Punjab': {'lat': 31.1471, 'lon': 72.7478, 'risk': 0.6},
            'Sindh': {'lat': 25.8943, 'lon': 68.5247, 'risk': 0.8},
            'KPK': {'lat': 34.0151, 'lon': 71.5249, 'risk': 0.4},
            'Balochistan': {'lat': 28.8160, 'lon': 65.7831, 'risk': 0.3},
            'Gilgit-Baltistan': {'lat': 35.9042, 'lon': 74.3989, 'risk': 0.2},
        }
        
        # Create folium map
        pak_map = folium.Map(
            location=[30.3753, 69.3451],  # Pakistan center
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Add risk indicators
        for location, data in pakistan_locations.items():
            color = ('red' if data['risk'] > 0.7 
                    else 'orange' if data['risk'] > 0.5 
                    else 'green')
            
            folium.CircleMarker(
                location=[data['lat'], data['lon']],
                radius=data['risk'] * 50,
                popup=f"{location}<br>Risk Score: {data['risk']:.2f}",
                color=color,
                fill=True,
                opacity=0.7
            ).add_to(pak_map)
        
        # Save map to HTML string
        map_html = pak_map._repr_html_()
        
        return {
            'folium_map': pak_map,
            'html': map_html,
            'risk_summary': {
                'highest_risk_province': max(pakistan_locations.items(), 
                                           key=lambda x: x[1]['risk'])[0],
                'average_risk': sum(data['risk'] for data in pakistan_locations.values()) / len(pakistan_locations),
                'provinces_above_threshold': len([loc for loc, data in pakistan_locations.items() 
                                                if data['risk'] > 0.5])
            }
        }

    async def generate_multi_format_report(self, 
                                         complaint_data: Dict[str, Any],
                                         output_dir: str = "./reports/") -> Dict[str, str]:
        """Generate reports in multiple formats (PDF, Excel, HTML, JSON)"""
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        report_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"banking_compliance_report_{timestamp}"
        
        # 1. JSON Export
        json_file = f"{output_dir}{base_filename}.json"
        with open(json_file, 'w') as f:
            json.dump(complaint_data, f, indent=2, default=str)
        report_files['json'] = json_file
        
        # 2. Excel Export
        excel_file = f"{output_dir}{base_filename}.xlsx"
        await self.export_to_excel(complaint_data, excel_file)
        report_files['excel'] = excel_file
        
        # 3. PDF Export
        pdf_file = f"{output_dir}{base_filename}.pdf"
        await self.export_to_pdf(complaint_data, pdf_file)
        report_files['pdf'] = pdf_file
        
        # 4. HTML Dashboard
        html_file = f"{output_dir}{base_filename}.html"
        dashboard_html = await self.create_html_dashboard(complaint_data)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        report_files['html'] = html_file
        
        # 5. CSV Exports
        csv_dir = f"{output_dir}csv/"
        Path(csv_dir).mkdir(parents=True, exist_ok=True)
        
        if 'transactions' in complaint_data:
            transactions_csv = f"{csv_dir}transactions_{timestamp}.csv"
            pd.DataFrame(complaint_data['transactions']).to_csv(transactions_csv, index=False)
            report_files['transactions_csv'] = transactions_csv
        
        if 'compliance_metrics' in complaint_data:
            compliance_csv = f"{csv_dir}compliance_{timestamp}.csv"
            pd.DataFrame(complaint_data['compliance_metrics']).to_csv(compliance_csv, index=False)
            report_files['compliance_csv'] = compliance_csv
        
        return report_files

    async def create_html_dashboard(self, data: Dict[str, Any]) -> str:
        """Create comprehensive HTML dashboard"""
        
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Pakistan Banking Compliance Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .header {
                    background: linear-gradient(135deg, #1B4F3A, #2E7D57);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }
                .dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .chart-container {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .summary-stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 30px;
                }
                .stat-card {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .stat-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #1B4F3A;
                }
                .footer {
                    text-align: center;
                    color: #666;
                    margin-top: 30px;
                    padding: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🇵🇰 Pakistan Banking Compliance & Complaint Analysis System</h1>
                <p>Generated on {{ current_date }}</p>
            </div>
            
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-value">{{ total_complaints }}</div>
                    <div>Total Complaints</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ compliance_rate }}%</div>
                    <div>Compliance Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ total_violations }}</div>
                    <div>Total Violations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">PKR {{ financial_impact }}M</div>
                    <div>Financial Impact</div>
                </div>
            </div>
            
            <div class="dashboard-grid">
                <div class="chart-container">
                    <div id="compliance-chart"></div>
                </div>
                <div class="chart-container">
                    <div id="transaction-flow"></div>
                </div>
                <div class="chart-container">
                    <div id="risk-analysis"></div>
                </div>
                <div class="chart-container">
                    <div id="timeline-chart"></div>
                </div>
            </div>
            
            <div class="footer">
                <p>Generated by Pakistan Banking Compliance & Complaint Analysis System (PBCCAS)</p>
                <p>In compliance with CRPC, NAB Ordinance, and SBP Banking Policies</p>
            </div>
            
            <script>
                // Placeholder for chart rendering
                // Charts would be rendered here using the data
            </script>
        </body>
        </html>
        """
        
        template = Template(html_template)
        return template.render(
            current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_complaints=data.get('total_complaints', 0),
            compliance_rate=data.get('compliance_percentage', 0),
            total_violations=data.get('total_violations', 0),
            financial_impact=data.get('financial_impact', 0) / 1000000  # Convert to millions
        )

# Example usage
if __name__ == "__main__":
    import asyncio
    
    config = {
        'database_url': 'postgresql://user:password@localhost/pbccas'
    }
    
    visualizer = BankRecordsVisualizer(config)
    
    # Sample data
    sample_transactions = [
        TransactionEdge(
            from_account="12345678901234",
            to_account="98765432109876",
            amount=1500000,
            timestamp=datetime.now(),
            transaction_type="wire_transfer",
            reference="REF123456",
            fees=1500,
            is_suspicious=True
        )
    ]
    
    sample_accounts = [
        TransactionNode(
            account_id="12345678901234",
            bank_name="HBL",
            account_holder="Muhammad Ali",
            location="Lahore",
            account_type="savings",
            balance=5000000,
            risk_score=0.8
        )
    ]
    
    async def test_visualization():
        # Test transaction flow
        flow_result = await visualizer.create_transaction_flow_diagram(
            sample_transactions, sample_accounts
        )
        print("Transaction flow created")
        
        # Test compliance dashboard
        sample_metrics = [
            ComplianceMetric("AML_Compliance", 95.0, 90.0, "compliant", 
                           datetime.now(), "Anti-Money Laundering compliance")
        ]
        dashboard_result = await visualizer.create_compliance_dashboard(sample_metrics)
        print("Compliance dashboard created")
        
        # Generate multi-format reports
        sample_data = {
            'transactions': [t.__dict__ for t in sample_transactions],
            'compliance_percentage': 85.5,
            'total_violations': 15,
            'financial_impact': 18000000
        }
        
        report_files = await visualizer.generate_multi_format_report(sample_data)
        print("Reports generated:", report_files)
    
    # asyncio.run(test_visualization())