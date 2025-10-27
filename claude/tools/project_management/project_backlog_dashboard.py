#!/usr/bin/env python3
"""
Maia Project Backlog Dashboard - Streamlit Web Interface
Project: PROJ-REG-001
Purpose: Interactive visualization of project backlog, status, and analytics

Usage:
    streamlit run claude/tools/project_management/project_backlog_dashboard.py

    # Custom port
    streamlit run claude/tools/project_management/project_backlog_dashboard.py --server.port=8505
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = "claude/data/project_registry.db"
MAIA_ROOT = os.environ.get("MAIA_ROOT", os.path.expanduser("~/git/maia"))

# Colors for consistent branding
COLORS = {
    'critical': '#E74C3C',    # Red
    'high': '#E67E22',        # Orange
    'medium': '#F39C12',      # Yellow
    'low': '#95A5A6',         # Gray
    'active': '#3498DB',      # Blue
    'completed': '#2ECC71',   # Green
    'blocked': '#E74C3C',     # Red
    'planned': '#95A5A6',     # Gray
}

STATUS_EMOJI = {
    'planned': '📋',
    'active': '🚀',
    'blocked': '🚫',
    'completed': '✅',
    'archived': '📦',
}

PRIORITY_EMOJI = {
    'critical': '🔥',
    'high': '⚡',
    'medium': '📊',
    'low': '📌',
}

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@st.cache_resource
def get_database_path():
    """Get absolute path to database."""
    if not os.path.isabs(DB_PATH):
        return os.path.join(MAIA_ROOT, DB_PATH)
    return DB_PATH

def get_db_connection():
    """Create database connection with error handling."""
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        st.error(f"❌ Database connection failed: {e}")
        st.error(f"Database path: {get_database_path()}")
        st.stop()

# ============================================================================
# DATA QUERIES
# ============================================================================

@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_executive_summary() -> Dict[str, Any]:
    """Get high-level statistics for executive summary."""
    conn = get_db_connection()

    summary = {}

    # Total project counts by status
    cursor = conn.execute("""
        SELECT status, COUNT(*) as count
        FROM projects
        GROUP BY status
    """)
    summary['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

    # Active projects with effort
    cursor = conn.execute("""
        SELECT
            COUNT(*) as active_count,
            SUM(effort_hours) as total_effort
        FROM projects
        WHERE status = 'active'
    """)
    row = cursor.fetchone()
    summary['active_count'] = row['active_count'] or 0
    summary['active_effort'] = row['total_effort'] or 0

    # Backlog size
    cursor = conn.execute("""
        SELECT COUNT(*) as backlog_count, SUM(effort_hours) as backlog_effort
        FROM projects
        WHERE status = 'planned'
    """)
    row = cursor.fetchone()
    summary['backlog_count'] = row['backlog_count'] or 0
    summary['backlog_effort'] = row['backlog_effort'] or 0

    # Recent velocity (last 30 days)
    cursor = conn.execute("""
        SELECT
            COUNT(*) as completed_last_30,
            SUM(actual_hours) as actual_hours,
            SUM(effort_hours) as estimated_hours
        FROM projects
        WHERE status = 'completed'
        AND completed_date > datetime('now', '-30 days')
    """)
    row = cursor.fetchone()
    summary['velocity_30d'] = row['completed_last_30'] or 0
    summary['actual_hours'] = row['actual_hours'] or 0
    summary['estimated_hours'] = row['estimated_hours'] or 0

    # Blocked projects
    cursor = conn.execute("""
        SELECT COUNT(*) as blocked_count
        FROM projects
        WHERE status = 'blocked'
    """)
    summary['blocked_count'] = cursor.fetchone()['blocked_count'] or 0

    conn.close()
    return summary

@st.cache_data(ttl=60)
def get_projects_by_status(status: str) -> pd.DataFrame:
    """Get all projects for a specific status."""
    conn = get_db_connection()

    query = """
        SELECT
            p.id,
            p.name,
            p.status,
            p.priority,
            p.effort_hours,
            p.actual_hours,
            p.impact,
            p.category,
            p.created_date,
            p.started_date,
            p.completed_date,
            p.description,
            COUNT(DISTINCT d.id) as deliverable_count,
            COUNT(DISTINCT dep.id) as dependency_count
        FROM projects p
        LEFT JOIN deliverables d ON p.id = d.project_id
        LEFT JOIN dependencies dep ON p.id = dep.project_id
        WHERE p.status = ?
        GROUP BY p.id
        ORDER BY
            CASE p.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END,
            p.created_date DESC
    """

    df = pd.read_sql_query(query, conn, params=[status])
    conn.close()
    return df

@st.cache_data(ttl=60)
def get_priority_matrix() -> pd.DataFrame:
    """Get projects for impact vs effort matrix."""
    conn = get_db_connection()

    query = """
        SELECT
            id,
            name,
            priority,
            effort_hours,
            impact,
            status,
            category
        FROM projects
        WHERE status IN ('planned', 'active')
        AND effort_hours IS NOT NULL
        AND impact IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=60)
def get_analytics_data() -> Dict[str, pd.DataFrame]:
    """Get data for analytics charts."""
    conn = get_db_connection()

    analytics = {}

    # Completion trend (last 90 days by week)
    analytics['completion_trend'] = pd.read_sql_query("""
        SELECT
            strftime('%Y-%W', completed_date) as week,
            COUNT(*) as completed_count,
            SUM(actual_hours) as actual_hours,
            SUM(effort_hours) as estimated_hours
        FROM projects
        WHERE status = 'completed'
        AND completed_date > datetime('now', '-90 days')
        GROUP BY week
        ORDER BY week
    """, conn)

    # Category distribution
    analytics['category_distribution'] = pd.read_sql_query("""
        SELECT
            category,
            COUNT(*) as count,
            SUM(effort_hours) as total_effort
        FROM projects
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
        LIMIT 10
    """, conn)

    # Status distribution
    analytics['status_distribution'] = pd.read_sql_query("""
        SELECT
            status,
            COUNT(*) as count,
            SUM(effort_hours) as total_effort
        FROM projects
        GROUP BY status
    """, conn)

    # Priority distribution
    analytics['priority_distribution'] = pd.read_sql_query("""
        SELECT
            priority,
            status,
            COUNT(*) as count
        FROM projects
        GROUP BY priority, status
    """, conn)

    # Effort variance for completed projects
    analytics['effort_variance'] = pd.read_sql_query("""
        SELECT
            id,
            name,
            effort_hours,
            actual_hours,
            (actual_hours - effort_hours) as variance,
            CAST((actual_hours - effort_hours) * 100.0 / effort_hours AS INTEGER) as variance_pct
        FROM projects
        WHERE status = 'completed'
        AND effort_hours IS NOT NULL
        AND actual_hours IS NOT NULL
        ORDER BY ABS(variance) DESC
        LIMIT 20
    """, conn)

    conn.close()
    return analytics

@st.cache_data(ttl=60)
def get_project_details(project_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information for a specific project."""
    conn = get_db_connection()

    # Get project
    cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()

    if not project:
        conn.close()
        return None

    project_dict = dict(project)

    # Get deliverables
    cursor = conn.execute("""
        SELECT * FROM deliverables
        WHERE project_id = ?
        ORDER BY status, name
    """, (project_id,))
    project_dict['deliverables'] = [dict(row) for row in cursor.fetchall()]

    # Get dependencies
    cursor = conn.execute("""
        SELECT d.*, p.name as depends_on_name, p.status as depends_on_status
        FROM dependencies d
        JOIN projects p ON d.depends_on_project_id = p.id
        WHERE d.project_id = ?
    """, (project_id,))
    project_dict['dependencies'] = [dict(row) for row in cursor.fetchall()]

    # Get recent updates
    cursor = conn.execute("""
        SELECT * FROM project_updates
        WHERE project_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (project_id,))
    project_dict['updates'] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return project_dict

# ============================================================================
# STREAMLIT UI COMPONENTS
# ============================================================================

def render_executive_summary():
    """Render executive summary section."""
    st.header("🎯 Executive Summary")

    summary = get_executive_summary()

    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Active Projects",
            value=summary['active_count'],
            delta=f"{summary['active_effort']}h effort"
        )

    with col2:
        st.metric(
            label="Backlog Items",
            value=summary['backlog_count'],
            delta=f"{summary['backlog_effort']}h effort"
        )

    with col3:
        velocity_label = "Completed (30d)"
        if summary['estimated_hours'] and summary['estimated_hours'] > 0:
            variance_pct = ((summary['actual_hours'] - summary['estimated_hours']) /
                          summary['estimated_hours']) * 100
            delta_str = f"{variance_pct:+.1f}% vs estimate"
        else:
            delta_str = None

        st.metric(
            label=velocity_label,
            value=summary['velocity_30d'],
            delta=delta_str
        )

    with col4:
        st.metric(
            label="Blocked Projects",
            value=summary['blocked_count'],
            delta="Needs attention" if summary['blocked_count'] > 0 else None,
            delta_color="inverse"
        )

    # Status breakdown
    st.subheader("Project Status Breakdown")
    status_data = summary['by_status']

    fig = go.Figure(data=[
        go.Bar(
            x=list(status_data.keys()),
            y=list(status_data.values()),
            marker_color=[COLORS.get(s, '#95A5A6') for s in status_data.keys()],
            text=list(status_data.values()),
            textposition='auto',
        )
    ])

    fig.update_layout(
        height=300,
        xaxis_title="Status",
        yaxis_title="Count",
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

def render_project_status_board():
    """Render project status board with tabs."""
    st.header("📋 Project Status Board")

    tabs = st.tabs(["🚀 Active", "📋 Planned", "🚫 Blocked", "✅ Completed"])

    # Active Projects
    with tabs[0]:
        df = get_projects_by_status('active')
        render_project_table(df, "No active projects")

    # Planned Projects
    with tabs[1]:
        df = get_projects_by_status('planned')
        render_project_table(df, "No planned projects")

    # Blocked Projects
    with tabs[2]:
        df = get_projects_by_status('blocked')
        render_project_table(df, "No blocked projects")

    # Completed Projects
    with tabs[3]:
        df = get_projects_by_status('completed')
        render_project_table(df, "No completed projects")

def render_project_table(df: pd.DataFrame, empty_message: str):
    """Render a table of projects with click-to-drill functionality."""
    if df.empty:
        st.info(empty_message)
        return

    # Format dataframe for display
    display_df = df[['id', 'name', 'priority', 'effort_hours', 'impact', 'category']].copy()
    display_df.columns = ['ID', 'Name', 'Priority', 'Effort (h)', 'Impact', 'Category']

    # Add emoji to priority
    display_df['Priority'] = display_df['Priority'].apply(
        lambda x: f"{PRIORITY_EMOJI.get(x, '')} {x.upper()}" if pd.notna(x) else x
    )

    # Make table interactive
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=400
    )

    # Project selection for details
    st.subheader("Project Details")
    selected_id = st.selectbox(
        "Select project to view details:",
        options=df['id'].tolist(),
        format_func=lambda x: f"{x}: {df[df['id'] == x]['name'].iloc[0]}",
        key=f"select_{df['status'].iloc[0] if not df.empty else 'empty'}"
    )

    if selected_id:
        render_project_details(selected_id)

def render_project_details(project_id: str):
    """Render detailed view of a specific project."""
    project = get_project_details(project_id)

    if not project:
        st.error(f"Project {project_id} not found")
        return

    # Project header
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"### {STATUS_EMOJI.get(project['status'], '')} {project['name']}")

    with col2:
        st.markdown(f"**Status:** {project['status']}")
        st.markdown(f"**Priority:** {PRIORITY_EMOJI.get(project['priority'], '')} {project['priority']}")

    with col3:
        if project.get('effort_hours'):
            st.markdown(f"**Estimated:** {project['effort_hours']}h")
        if project.get('actual_hours'):
            st.markdown(f"**Actual:** {project['actual_hours']}h")

    # Description
    if project.get('description'):
        st.markdown("**Description:**")
        st.info(project['description'])

    # Metadata
    metadata_col1, metadata_col2 = st.columns(2)

    with metadata_col1:
        if project.get('category'):
            st.markdown(f"**Category:** {project['category']}")
        if project.get('impact'):
            st.markdown(f"**Impact:** {project['impact']}")

    with metadata_col2:
        st.markdown(f"**Created:** {project['created_date'][:10]}")
        if project.get('started_date'):
            st.markdown(f"**Started:** {project['started_date'][:10]}")
        if project.get('completed_date'):
            st.markdown(f"**Completed:** {project['completed_date'][:10]}")

    # Deliverables
    if project.get('deliverables'):
        st.markdown("**Deliverables:**")
        deliv_df = pd.DataFrame(project['deliverables'])
        st.dataframe(
            deliv_df[['name', 'type', 'status', 'file_path']],
            hide_index=True,
            use_container_width=True
        )

    # Dependencies
    if project.get('dependencies'):
        st.markdown("**Dependencies:**")
        for dep in project['dependencies']:
            dep_status = dep.get('depends_on_status', 'unknown')
            dep_emoji = STATUS_EMOJI.get(dep_status, '•')
            st.markdown(
                f"- {dep_emoji} **{dep['depends_on_project_id']}**: {dep['depends_on_name']} "
                f"({dep['dependency_type']}) - *{dep_status}*"
            )

def render_priority_heatmap():
    """Render impact vs effort priority matrix."""
    st.header("🔥 Priority Heatmap")

    df = get_priority_matrix()

    if df.empty:
        st.info("No projects with both impact and effort estimates")
        return

    # Map impact to numeric scale
    impact_map = {'low': 1, 'medium': 2, 'high': 3}
    df['impact_num'] = df['impact'].map(impact_map)

    # Create scatter plot
    fig = px.scatter(
        df,
        x='effort_hours',
        y='impact_num',
        color='priority',
        size='effort_hours',
        hover_data=['id', 'name', 'category', 'status'],
        labels={
            'effort_hours': 'Effort (hours)',
            'impact_num': 'Impact',
            'priority': 'Priority'
        },
        color_discrete_map=COLORS,
        title="Impact vs Effort Matrix"
    )

    # Update y-axis to show impact labels
    fig.update_yaxis(
        ticktext=['Low', 'Medium', 'High'],
        tickvals=[1, 2, 3],
        range=[0.5, 3.5]
    )

    # Add quadrant lines
    avg_effort = df['effort_hours'].median()

    fig.add_hline(y=2, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=avg_effort, line_dash="dash", line_color="gray", opacity=0.5)

    # Add quadrant labels
    fig.add_annotation(
        x=avg_effort * 0.5, y=2.5,
        text="Quick Wins<br>(High Impact, Low Effort)",
        showarrow=False,
        font=dict(size=10, color="green"),
        bgcolor="rgba(255, 255, 255, 0.8)"
    )

    fig.add_annotation(
        x=avg_effort * 1.5, y=2.5,
        text="Strategic Initiatives<br>(High Impact, High Effort)",
        showarrow=False,
        font=dict(size=10, color="blue"),
        bgcolor="rgba(255, 255, 255, 0.8)"
    )

    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Show projects by quadrant
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Quick Wins")
        quick_wins = df[(df['impact_num'] >= 2) & (df['effort_hours'] <= avg_effort)]
        if not quick_wins.empty:
            for _, row in quick_wins.iterrows():
                st.markdown(
                    f"- {PRIORITY_EMOJI.get(row['priority'], '')} **{row['id']}**: "
                    f"{row['name']} ({row['effort_hours']}h)"
                )
        else:
            st.info("No quick wins identified")

    with col2:
        st.subheader("🚀 Strategic Initiatives")
        strategic = df[(df['impact_num'] >= 2) & (df['effort_hours'] > avg_effort)]
        if not strategic.empty:
            for _, row in strategic.iterrows():
                st.markdown(
                    f"- {PRIORITY_EMOJI.get(row['priority'], '')} **{row['id']}**: "
                    f"{row['name']} ({row['effort_hours']}h)"
                )
        else:
            st.info("No strategic initiatives identified")

def render_analytics():
    """Render analytics and trends section."""
    st.header("📊 Analytics")

    analytics = get_analytics_data()

    # Completion trend
    st.subheader("Completion Velocity (Last 90 Days)")
    trend_df = analytics['completion_trend']

    if not trend_df.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=trend_df['week'],
            y=trend_df['completed_count'],
            mode='lines+markers',
            name='Completed Projects',
            line=dict(color=COLORS['completed'], width=2)
        ))

        fig.update_layout(
            height=300,
            xaxis_title="Week",
            yaxis_title="Projects Completed",
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No completed projects in the last 90 days")

    # Category and Status distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Projects by Category")
        cat_df = analytics['category_distribution']

        if not cat_df.empty:
            fig = px.pie(
                cat_df,
                values='count',
                names='category',
                title='Category Distribution'
            )
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available")

    with col2:
        st.subheader("Effort by Status")
        status_df = analytics['status_distribution']

        if not status_df.empty:
            fig = px.bar(
                status_df,
                x='status',
                y='total_effort',
                color='status',
                color_discrete_map=COLORS,
                title='Total Effort by Status'
            )
            fig.update_layout(
                height=300,
                showlegend=False,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available")

    # Effort variance analysis
    st.subheader("Estimation Accuracy (Completed Projects)")
    variance_df = analytics['effort_variance']

    if not variance_df.empty:
        fig = go.Figure()

        colors = ['red' if v > 0 else 'green' for v in variance_df['variance']]

        fig.add_trace(go.Bar(
            x=variance_df['name'],
            y=variance_df['variance_pct'],
            marker_color=colors,
            text=variance_df['variance_pct'],
            texttemplate='%{text:+.0f}%',
            textposition='outside'
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Project",
            yaxis_title="Variance (%)",
            title="Effort Estimation Variance (Actual vs Estimated)",
            showlegend=False,
            xaxis_tickangle=-45,
            margin=dict(l=0, r=0, t=40, b=100)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Statistics
        avg_variance = variance_df['variance_pct'].mean()
        st.markdown(f"**Average Variance:** {avg_variance:+.1f}% "
                   f"({'overestimated' if avg_variance < 0 else 'underestimated'})")
    else:
        st.info("No completed projects with effort tracking")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main Streamlit application."""

    # Page config
    st.set_page_config(
        page_title="Maia Project Backlog Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding-left: 20px;
            padding-right: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title
    st.title("📊 Maia Project Backlog Dashboard")
    st.markdown("**Real-time project tracking and analytics from SQLite database**")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("Dashboard Controls")

        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # Database info
        st.markdown("---")
        st.subheader("Database Info")
        st.markdown(f"**Path:** `{get_database_path()}`")

        # Last updated
        st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Quick stats
        st.markdown("---")
        st.subheader("Quick Stats")
        summary = get_executive_summary()
        total_projects = sum(summary['by_status'].values())
        st.metric("Total Projects", total_projects)

        # View selection
        st.markdown("---")
        st.subheader("Navigation")
        view = st.radio(
            "Select view:",
            options=[
                "Executive Summary",
                "Project Status Board",
                "Priority Heatmap",
                "Analytics"
            ],
            label_visibility="collapsed"
        )

    # Main content based on selection
    if view == "Executive Summary":
        render_executive_summary()
    elif view == "Project Status Board":
        render_project_status_board()
    elif view == "Priority Heatmap":
        render_priority_heatmap()
    elif view == "Analytics":
        render_analytics()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Maia Project Registry Dashboard | "
        "Powered by Streamlit + SQLite | "
        "Real-time data from project_registry.db"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
