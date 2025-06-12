"""
PyTaskAI - Bug Analytics Dashboard Component

Streamlit component for visualizing bug statistics and analytics.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def render_bug_analytics_dashboard(project_root: str):
    """Render comprehensive bug analytics dashboard"""
    
    st.header("🐛 Bug Analytics Dashboard")
    
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from mcp_server.task_manager import get_bug_statistics_tool, list_tasks_tool
    
    try:
        # Get bug statistics
        stats_result = get_bug_statistics_tool(
            project_root=project_root,
            include_resolved=True,
            group_by="severity"
        )
        
        if stats_result.get("error"):
            st.error(f"Error loading bug statistics: {stats_result['error']}")
            return
        
        stats = stats_result.get("statistics", {})
        
        # Overview metrics
        render_bug_overview_metrics(stats)
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            render_severity_distribution_chart(stats)
            
        with col2:
            render_status_distribution_chart(stats)
        
        # Resolution trend (if we have historical data)
        render_bug_trends(project_root)
        
        # Detailed tables
        render_bug_details_tables(stats)
        
        # Action items and recommendations
        render_bug_recommendations(stats)
        
    except Exception as e:
        st.error(f"Failed to load bug analytics: {str(e)}")


def render_bug_overview_metrics(stats: Dict[str, Any]):
    """Render overview metrics cards"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Bugs", 
            stats.get("total_bugs", 0),
            help="Total number of bugs in the system"
        )
    
    with col2:
        critical_high = stats.get("critical_high_count", 0)
        st.metric(
            "Critical/High", 
            critical_high,
            delta=f"{critical_high} priority bugs" if critical_high > 0 else None,
            delta_color="inverse" if critical_high > 0 else "normal",
            help="Number of critical and high severity bugs"
        )
    
    with col3:
        resolution_rate = stats.get("resolution_rate", 0)
        st.metric(
            "Resolution Rate", 
            f"{resolution_rate:.1f}%",
            delta=f"{'Good' if resolution_rate > 80 else 'Needs improvement'}" if resolution_rate > 0 else None,
            delta_color="normal" if resolution_rate > 80 else "inverse",
            help="Percentage of resolved bugs"
        )
    
    with col4:
        severity_dist = stats.get("severity_distribution", {})
        open_bugs = stats.get("total_bugs", 0) - severity_dist.get("done", 0)
        st.metric(
            "Open Bugs", 
            open_bugs,
            help="Number of unresolved bugs"
        )
    
    with col5:
        # Calculate average age of open bugs (simplified)
        oldest_bugs = stats.get("oldest_unresolved", [])
        avg_age = "N/A"
        if oldest_bugs:
            avg_age = f"{len(oldest_bugs)} oldest"
        
        st.metric(
            "Oldest Bugs", 
            avg_age,
            help="Number of oldest unresolved bugs"
        )


def render_severity_distribution_chart(stats: Dict[str, Any]):
    """Render severity distribution pie chart"""
    
    st.subheader("🔥 Severity Distribution")
    
    severity_dist = stats.get("severity_distribution", {})
    
    if not any(severity_dist.values()):
        st.info("No bugs found for severity analysis")
        return
    
    # Filter out zero values
    filtered_severity = {k: v for k, v in severity_dist.items() if v > 0}
    
    # Color mapping for severity
    severity_colors = {
        "critical": "#d32f2f",  # Red
        "high": "#f57c00",      # Orange
        "medium": "#ffa000",    # Amber
        "low": "#388e3c",       # Green
        "unknown": "#757575"    # Gray
    }
    
    labels = list(filtered_severity.keys())
    values = list(filtered_severity.values())
    colors = [severity_colors.get(label, "#757575") for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        textinfo='label+percent',
        hole=0.3
    )])
    
    fig.update_layout(
        title="Bug Distribution by Severity",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_status_distribution_chart(stats: Dict[str, Any]):
    """Render status distribution bar chart"""
    
    st.subheader("📊 Status Distribution")
    
    status_dist = stats.get("status_distribution", {})
    
    if not any(status_dist.values()):
        st.info("No bugs found for status analysis")
        return
    
    # Create DataFrame for plotting
    df_status = pd.DataFrame([
        {"Status": status, "Count": count}
        for status, count in status_dist.items()
        if count > 0
    ])
    
    # Color mapping for status
    status_colors = {
        "pending": "#2196f3",     # Blue
        "in-progress": "#ff9800", # Orange
        "review": "#9c27b0",      # Purple
        "done": "#4caf50",        # Green
        "blocked": "#f44336",     # Red
        "cancelled": "#757575"    # Gray
    }
    
    fig = px.bar(
        df_status, 
        x="Status", 
        y="Count",
        title="Bug Distribution by Status",
        color="Status",
        color_discrete_map=status_colors
    )
    
    fig.update_layout(
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_bug_trends(project_root: str):
    """Render bug trend analysis"""
    
    st.subheader("📈 Bug Trends")
    
    try:
        # Get all bugs for trend analysis
        bugs_result = list_tasks_tool(
            project_root=project_root,
            type_filter="bug",
            include_subtasks=False
        )
        
        if bugs_result.get("error"):
            st.warning("Could not load bug trend data")
            return
        
        bugs = bugs_result.get("tasks", [])
        
        if not bugs:
            st.info("No bugs available for trend analysis")
            return
        
        # Analyze bugs by creation date
        bug_dates = []
        for bug in bugs:
            created_at = bug.get("created_at")
            if created_at:
                try:
                    # Parse ISO format date
                    date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    bug_dates.append({
                        "date": date.date(),
                        "severity": bug.get("severity", "unknown"),
                        "status": bug.get("status", "unknown")
                    })
                except:
                    continue
        
        if not bug_dates:
            st.info("No valid date information for trend analysis")
            return
        
        # Create trend DataFrame
        df_trends = pd.DataFrame(bug_dates)
        
        # Group by date and count
        daily_counts = df_trends.groupby("date").size().reset_index(name="bugs_created")
        
        if len(daily_counts) > 1:
            fig = px.line(
                daily_counts,
                x="date",
                y="bugs_created",
                title="Bug Creation Trend",
                markers=True
            )
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Bugs Created",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient data for trend analysis (need multiple days)")
            
    except Exception as e:
        st.warning(f"Could not generate trend analysis: {str(e)}")


def render_bug_details_tables(stats: Dict[str, Any]):
    """Render detailed bug information tables"""
    
    st.subheader("📋 Detailed Bug Information")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["By Severity", "Oldest Unresolved", "Summary"])
    
    with tab1:
        render_bugs_by_severity_table(stats)
    
    with tab2:
        render_oldest_bugs_table(stats)
    
    with tab3:
        render_bug_summary_table(stats)


def render_bugs_by_severity_table(stats: Dict[str, Any]):
    """Render bugs grouped by severity"""
    
    grouped_stats = stats.get("grouped_stats", {})
    
    if not grouped_stats:
        st.info("No bug grouping data available")
        return
    
    for severity, data in grouped_stats.items():
        count = data.get("count", 0)
        percentage = data.get("percentage", 0)
        bugs = data.get("bugs", [])
        
        if count > 0:
            with st.expander(f"{severity.title()} Severity ({count} bugs - {percentage:.1f}%)"):
                if bugs:
                    df_bugs = pd.DataFrame(bugs)
                    st.dataframe(
                        df_bugs[["id", "title", "status", "created_at"]],
                        use_container_width=True
                    )
                else:
                    st.info("No bug details available")


def render_oldest_bugs_table(stats: Dict[str, Any]):
    """Render table of oldest unresolved bugs"""
    
    oldest_bugs = stats.get("oldest_unresolved", [])
    
    if not oldest_bugs:
        st.info("🎉 No unresolved bugs found!")
        return
    
    st.markdown("**Oldest Unresolved Bugs** (need attention)")
    
    df_oldest = pd.DataFrame(oldest_bugs)
    
    # Format the dataframe for better display
    if not df_oldest.empty:
        display_df = df_oldest[["id", "title", "severity", "status", "created_at"]].copy()
        
        # Format created_at for better readability
        if "created_at" in display_df.columns:
            try:
                display_df["created_at"] = pd.to_datetime(display_df["created_at"]).dt.strftime("%Y-%m-%d")
            except:
                pass  # Keep original format if parsing fails
        
        st.dataframe(display_df, use_container_width=True)
        
        # Highlight critical issues
        critical_bugs = [bug for bug in oldest_bugs if bug.get("severity") == "critical"]
        if critical_bugs:
            st.error(f"⚠️ {len(critical_bugs)} critical bugs need immediate attention!")


def render_bug_summary_table(stats: Dict[str, Any]):
    """Render summary statistics table"""
    
    st.markdown("**Bug Statistics Summary**")
    
    summary_data = [
        {"Metric": "Total Bugs", "Value": stats.get("total_bugs", 0)},
        {"Metric": "Critical/High Priority", "Value": stats.get("critical_high_count", 0)},
        {"Metric": "Resolution Rate", "Value": f"{stats.get('resolution_rate', 0):.1f}%"},
    ]
    
    # Add severity breakdown
    severity_dist = stats.get("severity_distribution", {})
    for severity, count in severity_dist.items():
        if count > 0:
            summary_data.append({
                "Metric": f"{severity.title()} Severity",
                "Value": count
            })
    
    # Add status breakdown
    status_dist = stats.get("status_distribution", {})
    for status, count in status_dist.items():
        if count > 0:
            summary_data.append({
                "Metric": f"Status: {status.title()}",
                "Value": count
            })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)


def render_bug_recommendations(stats: Dict[str, Any]):
    """Render actionable recommendations based on bug analysis"""
    
    st.subheader("💡 Recommendations")
    
    recommendations = []
    
    # Check critical/high severity bugs
    critical_high = stats.get("critical_high_count", 0)
    if critical_high > 0:
        recommendations.append({
            "type": "error",
            "message": f"🚨 {critical_high} high/critical severity bugs need immediate attention"
        })
    
    # Check resolution rate
    resolution_rate = stats.get("resolution_rate", 0)
    if resolution_rate < 50:
        recommendations.append({
            "type": "warning",
            "message": f"📉 Low resolution rate ({resolution_rate:.1f}%) - consider improving bug triage process"
        })
    elif resolution_rate > 90:
        recommendations.append({
            "type": "success",
            "message": f"✅ Excellent resolution rate ({resolution_rate:.1f}%) - keep up the good work!"
        })
    
    # Check for old unresolved bugs
    oldest_bugs = stats.get("oldest_unresolved", [])
    if len(oldest_bugs) > 5:
        recommendations.append({
            "type": "warning",
            "message": f"🕐 {len(oldest_bugs)} old unresolved bugs - consider reviewing and prioritizing"
        })
    
    # Check total bug count
    total_bugs = stats.get("total_bugs", 0)
    if total_bugs == 0:
        recommendations.append({
            "type": "info",
            "message": "🎉 No bugs reported yet - great job on quality!"
        })
    elif total_bugs > 50:
        recommendations.append({
            "type": "info",
            "message": f"📊 {total_bugs} total bugs - consider implementing automated testing to catch issues early"
        })
    
    # Display recommendations
    if recommendations:
        for rec in recommendations:
            if rec["type"] == "error":
                st.error(rec["message"])
            elif rec["type"] == "warning":
                st.warning(rec["message"])
            elif rec["type"] == "success":
                st.success(rec["message"])
            else:
                st.info(rec["message"])
    else:
        st.info("No specific recommendations at this time - bug metrics look good!")


def render_quick_bug_report_form(project_root: str):
    """Render quick bug reporting form"""
    
    st.subheader("🐛 Quick Bug Report")
    
    with st.form("quick_bug_report"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Bug Title", placeholder="Brief description of the bug")
            severity = st.selectbox("Severity", ["low", "medium", "high", "critical"], index=1)
        
        with col2:
            priority = st.selectbox("Priority", ["lowest", "low", "medium", "high", "highest"], index=3)
            environment = st.text_input("Environment", placeholder="Browser, OS, version, etc.")
        
        description = st.text_area("Description", placeholder="Detailed description of the bug")
        steps = st.text_area("Steps to Reproduce", placeholder="1. Go to...\n2. Click on...\n3. Observe...")
        
        col1, col2 = st.columns(2)
        with col1:
            expected = st.text_area("Expected Result", placeholder="What should happen?")
        with col2:
            actual = st.text_area("Actual Result", placeholder="What actually happens?")
        
        submitted = st.form_submit_button("🐛 Report Bug", type="primary")
        
        if submitted and title and description:
            try:
                # Import here to avoid circular imports
                import asyncio
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                
                from mcp_server.task_manager import report_bug_tool
                
                # Run async function
                async def create_bug():
                    return await report_bug_tool(
                        project_root=project_root,
                        title=title,
                        description=description,
                        severity=severity,
                        priority=priority,
                        steps_to_reproduce=steps if steps else None,
                        expected_result=expected if expected else None,
                        actual_result=actual if actual else None,
                        environment=environment if environment else None
                    )
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(create_bug())
                finally:
                    loop.close()
                
                if result.get("success"):
                    st.success(f"✅ Bug report created successfully! ID: #{result.get('bug_report', {}).get('bug_id')}")
                    
                    # Show recommendations
                    recommendations = result.get("recommendations", [])
                    if recommendations:
                        st.info("💡 **Recommendations:**\n" + "\n".join(f"• {rec}" for rec in recommendations))
                    
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create bug report: {result.get('error')}")
                    
            except Exception as e:
                st.error(f"❌ Error creating bug report: {str(e)}")
        elif submitted:
            st.warning("Please fill in at least the title and description fields")