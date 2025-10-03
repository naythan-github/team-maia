#!/usr/bin/env python3
"""
ServiceDesk Operations Intelligence Dashboard
==============================================
Real-time operational intelligence for ServiceDesk ticket analysis.

Features:
- FCR performance by team
- Automation opportunity identification
- Alert pattern analysis
- Team performance metrics

Author: UI Systems Agent + Data Analyst Agent
Version: 1.0.0
Created: 2025-10-03
"""

import dash
from dash import dcc, html, dash_table
import plotly.graph_objs as go
import plotly.express as px
import sqlite3
import pandas as pd
from datetime import datetime

# Database connection
DB_PATH = "/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db"

# Design tokens
COLORS = {
    'critical': '#ef4444',
    'warning': '#f59e0b',
    'success': '#10b981',
    'primary': '#3b82f6',
    'bg': '#f8fafc',
    'card': '#ffffff',
    'text': '#1e293b'
}

def get_summary_metrics():
    """Get summary KPI metrics"""
    conn = sqlite3.connect(DB_PATH)

    # Total tickets
    total = pd.read_sql_query("SELECT COUNT(*) as count FROM tickets", conn).iloc[0]['count']

    # Overall FCR from timesheet data
    fcr_query = """
        SELECT
            COUNT(DISTINCT t."TKT-Ticket ID") as total,
            COUNT(DISTINCT CASE WHEN eng_count = 1 THEN t."TKT-Ticket ID" END) as fcr
        FROM tickets t
        LEFT JOIN (
            SELECT crm_id, COUNT(DISTINCT user_username) as eng_count
            FROM timesheets GROUP BY crm_id
        ) ts ON t."TKT-Ticket ID" = ts.crm_id
    """
    fcr_data = pd.read_sql_query(fcr_query, conn)
    fcr_rate = round(fcr_data.iloc[0]['fcr'] * 100.0 / fcr_data.iloc[0]['total'], 1) if fcr_data.iloc[0]['total'] > 0 else 0

    # Automation potential
    auto_query = """
        SELECT COUNT(*) as count
        FROM tickets
        WHERE "TKT-Title" LIKE '%Alert%' OR "TKT-Title" LIKE '%Sev%'
    """
    auto_count = pd.read_sql_query(auto_query, conn).iloc[0]['count']

    conn.close()

    return {
        'total_tickets': total,
        'fcr_rate': fcr_rate,
        'automation_count': auto_count,
        'hours_saved': round(auto_count * 0.25, 0)  # 15min per ticket
    }

def get_fcr_by_team():
    """Get FCR performance by team"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            t."TKT-Team" as team,
            COUNT(DISTINCT t."TKT-Ticket ID") as total,
            COUNT(DISTINCT CASE WHEN eng_count = 1 THEN t."TKT-Ticket ID" END) as fcr,
            ROUND(COUNT(DISTINCT CASE WHEN eng_count = 1 THEN t."TKT-Ticket ID" END) * 100.0 /
                  COUNT(DISTINCT t."TKT-Ticket ID"), 1) as fcr_rate
        FROM tickets t
        LEFT JOIN (
            SELECT crm_id, COUNT(DISTINCT user_username) as eng_count
            FROM timesheets GROUP BY crm_id
        ) ts ON t."TKT-Ticket ID" = ts.crm_id
        GROUP BY t."TKT-Team"
        HAVING total > 100
        ORDER BY fcr_rate DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Color code based on FCR rate
    df['color'] = df['fcr_rate'].apply(lambda x:
        COLORS['success'] if x >= 70 else
        COLORS['warning'] if x >= 40 else
        COLORS['critical']
    )

    return df

def get_automation_opportunities():
    """Get top automation opportunities"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            "TKT-Title" as pattern,
            COUNT(*) as volume,
            ROUND(COUNT(*) * 100.0 / 13252, 1) as pct_total,
            ROUND(COUNT(*) * 0.25, 0) as hours_saved
        FROM tickets
        WHERE ("TKT-Title" LIKE '%Alert%' OR "TKT-Title" LIKE '%Sev%')
        GROUP BY "TKT-Title"
        HAVING volume > 50
        ORDER BY volume DESC
        LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Get data
metrics = get_summary_metrics()
fcr_data = get_fcr_by_team()
auto_data = get_automation_opportunities()

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("ServiceDesk Operations Intelligence",
                style={'color': COLORS['text'], 'margin': '0'}),
        html.P(f"Analysis Period: July-Dec 2025 | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
               style={'color': '#64748b', 'margin': '0.5rem 0 0 0'})
    ], style={
        'padding': '2rem',
        'background': COLORS['card'],
        'borderBottom': '1px solid #e2e8f0'
    }),

    # Summary Cards
    html.Div([
        # Total Tickets Card
        html.Div([
            html.Div("Total Tickets", style={'fontSize': '0.875rem', 'color': '#64748b'}),
            html.Div(f"{metrics['total_tickets']:,}",
                    style={'fontSize': '2rem', 'fontWeight': 'bold', 'color': COLORS['text']}),
        ], style={'background': COLORS['card'], 'padding': '1.5rem', 'borderRadius': '0.5rem',
                 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)', 'flex': '1'}),

        # FCR Rate Card
        html.Div([
            html.Div("Overall FCR Rate", style={'fontSize': '0.875rem', 'color': '#64748b'}),
            html.Div(f"{metrics['fcr_rate']}%",
                    style={'fontSize': '2rem', 'fontWeight': 'bold',
                          'color': COLORS['critical'] if metrics['fcr_rate'] < 40 else COLORS['warning']}),
            html.Div("Target: 70%", style={'fontSize': '0.75rem', 'color': '#94a3b8', 'marginTop': '0.5rem'})
        ], style={'background': COLORS['card'], 'padding': '1.5rem', 'borderRadius': '0.5rem',
                 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)', 'flex': '1'}),

        # Automation Potential Card
        html.Div([
            html.Div("Automation Candidates", style={'fontSize': '0.875rem', 'color': '#64748b'}),
            html.Div(f"{metrics['automation_count']:,}",
                    style={'fontSize': '2rem', 'fontWeight': 'bold', 'color': COLORS['primary']}),
            html.Div(f"{round(metrics['automation_count']/metrics['total_tickets']*100, 1)}% of total",
                    style={'fontSize': '0.75rem', 'color': '#94a3b8', 'marginTop': '0.5rem'})
        ], style={'background': COLORS['card'], 'padding': '1.5rem', 'borderRadius': '0.5rem',
                 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)', 'flex': '1'}),

        # Hours Saved Card
        html.Div([
            html.Div("Potential Hours Saved/Month", style={'fontSize': '0.875rem', 'color': '#64748b'}),
            html.Div(f"{int(metrics['hours_saved']):,}",
                    style={'fontSize': '2rem', 'fontWeight': 'bold', 'color': COLORS['success']}),
            html.Div(f"≈ ${int(metrics['hours_saved'] * 75):,} @ $75/hr",
                    style={'fontSize': '0.75rem', 'color': '#94a3b8', 'marginTop': '0.5rem'})
        ], style={'background': COLORS['card'], 'padding': '1.5rem', 'borderRadius': '0.5rem',
                 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)', 'flex': '1'}),

    ], style={'display': 'flex', 'gap': '1rem', 'padding': '2rem', 'background': COLORS['bg']}),

    # Main Charts Row
    html.Div([
        # FCR by Team Chart
        html.Div([
            html.H3("First Call Resolution by Team",
                   style={'color': COLORS['text'], 'fontSize': '1.25rem', 'marginBottom': '1rem'}),
            dcc.Graph(
                figure={
                    'data': [go.Bar(
                        y=fcr_data['team'],
                        x=fcr_data['fcr_rate'],
                        orientation='h',
                        marker={'color': fcr_data['color']},
                        text=fcr_data['fcr_rate'].apply(lambda x: f"{x}%"),
                        textposition='auto',
                        hovertemplate='<b>%{y}</b><br>FCR Rate: %{x}%<br>Total: %{customdata}<extra></extra>',
                        customdata=fcr_data['total']
                    )],
                    'layout': go.Layout(
                        xaxis={'title': 'FCR Rate (%)', 'range': [0, 100]},
                        yaxis={'title': '', 'autorange': 'reversed'},
                        margin={'l': 200, 'r': 20, 't': 20, 'b': 50},
                        height=400,
                        shapes=[
                            dict(type='line', x0=70, x1=70, y0=-0.5, y1=len(fcr_data)-0.5,
                                line=dict(color=COLORS['success'], width=2, dash='dash'))
                        ],
                        annotations=[
                            dict(x=70, y=-0.8, text="Target: 70%", showarrow=False,
                                font=dict(color=COLORS['success'], size=10))
                        ]
                    )
                },
                config={'displayModeBar': False}
            )
        ], style={'background': COLORS['card'], 'padding': '1.5rem', 'borderRadius': '0.5rem',
                 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)', 'flex': '1'}),

        # Automation Opportunities Table
        html.Div([
            html.H3("Top Automation Opportunities",
                   style={'color': COLORS['text'], 'fontSize': '1.25rem', 'marginBottom': '1rem'}),
            dash_table.DataTable(
                data=auto_data.to_dict('records'),
                columns=[
                    {'name': 'Alert Pattern', 'id': 'pattern'},
                    {'name': 'Volume', 'id': 'volume', 'type': 'numeric'},
                    {'name': '% Total', 'id': 'pct_total', 'type': 'numeric'},
                    {'name': 'Hours Saved', 'id': 'hours_saved', 'type': 'numeric'}
                ],
                style_cell={
                    'textAlign': 'left',
                    'padding': '0.75rem',
                    'fontSize': '0.875rem',
                    'fontFamily': 'system-ui'
                },
                style_header={
                    'backgroundColor': COLORS['bg'],
                    'fontWeight': 'bold',
                    'color': COLORS['text']
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': COLORS['bg']
                    }
                ]
            )
        ], style={'background': COLORS['card'], 'padding': '1.5rem', 'borderRadius': '0.5rem',
                 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)', 'flex': '1'}),

    ], style={'display': 'flex', 'gap': '1rem', 'padding': '0 2rem 2rem 2rem', 'background': COLORS['bg']})

], style={'fontFamily': 'system-ui, -apple-system, sans-serif', 'background': COLORS['bg'], 'minHeight': '100vh'})

if __name__ == '__main__':
    print("🚀 Starting ServiceDesk Operations Dashboard...")
    print("📊 Dashboard: http://127.0.0.1:8065")
    app.run(debug=True, host='0.0.0.0', port=8065)
