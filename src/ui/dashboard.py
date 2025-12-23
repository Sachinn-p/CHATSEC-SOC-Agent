"""
Dashboard module for visualizing SOC automation metrics and data.
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta

from src.database.models import DatabaseManager


class DashboardRenderer:
    """Dashboard renderer for SOC automation metrics"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def get_tool_usage_data(self, days: int = 30) -> pd.DataFrame:
        """Get tool usage statistics"""
        with self.db_manager.get_connection() as conn:
            query = """
                SELECT tool_name, COUNT(*) as usage_count 
                FROM tools_log 
                WHERE timestamp >= date('now', '-{} days')
                GROUP BY tool_name 
                ORDER BY usage_count DESC
            """.format(days)
            
            df = pd.read_sql(query, conn)
        
        return df
    
    def get_proactive_execution_stats(self, days: int = 7) -> pd.DataFrame:
        """Get proactive agent execution statistics"""
        with self.db_manager.get_connection() as conn:
            query = """
                SELECT 
                    DATE(timestamp) as date,
                    strftime('%H', timestamp) as hour,
                    tool_name,
                    COUNT(*) as executions
                FROM tools_log 
                WHERE timestamp >= date('now', '-{} days')
                  AND tool_name NOT IN ('system', 'user')
                GROUP BY date, hour, tool_name
                ORDER BY date, hour
            """.format(days)
            
            df = pd.read_sql(query, conn)
        
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['hour'] + ':00:00')
        
        return df
    
    def get_alerts_data(self, days: int = 7) -> pd.DataFrame:
        """Get alert messages"""
        with self.db_manager.get_connection() as conn:
            query = """
                SELECT content, timestamp, 'alert' as type
                FROM messages 
                WHERE content LIKE '⚠️%' 
                  AND timestamp >= date('now', '-{} days')
                UNION ALL
                SELECT content, timestamp, 'proactive' as type
                FROM messages 
                WHERE content LIKE '🔔%' 
                  AND timestamp >= date('now', '-{} days')
                ORDER BY timestamp DESC
            """.format(days)
            
            df = pd.read_sql(query, conn)
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def get_message_volume_stats(self, days: int = 30) -> pd.DataFrame:
        """Get message volume statistics"""
        with self.db_manager.get_connection() as conn:
            query = """
                SELECT 
                    DATE(timestamp) as date,
                    role,
                    COUNT(*) as message_count
                FROM messages 
                WHERE timestamp >= date('now', '-{} days')
                GROUP BY date, role
                ORDER BY date
            """.format(days)
            
            df = pd.read_sql(query, conn)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def get_agent_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        with self.db_manager.get_connection() as conn:
            # Get total messages
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            # Get total tool executions
            cursor.execute("SELECT COUNT(*) FROM tools_log")
            total_tool_executions = cursor.fetchone()[0]
            
            # Get active proactive agents
            cursor.execute("SELECT COUNT(*) FROM proactive_agents WHERE enabled = 1")
            active_agents = cursor.fetchone()[0]
            
            # Get recent activity (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            recent_messages = cursor.fetchone()[0]
            
            # Get error rate (last 7 days)
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN content LIKE '⚠️%' THEN 1 END) as errors,
                    COUNT(*) as total
                FROM messages 
                WHERE timestamp >= date('now', '-7 days')
            """)
            error_stats = cursor.fetchone()
            error_rate = (error_stats[0] / error_stats[1] * 100) if error_stats[1] > 0 else 0
        
        return {
            "total_messages": total_messages,
            "total_tool_executions": total_tool_executions,
            "active_proactive_agents": active_agents,
            "recent_activity_24h": recent_messages,
            "error_rate_7d": round(error_rate, 2)
        }
    
    def render_metrics_overview(self) -> None:
        """Render metrics overview cards"""
        st.subheader("📊 SOC Automation Metrics")
        
        metrics = self.get_agent_performance_metrics()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Messages", metrics["total_messages"])
        
        with col2:
            st.metric("Tool Executions", metrics["total_tool_executions"])
        
        with col3:
            st.metric("Active Agents", metrics["active_proactive_agents"])
        
        with col4:
            st.metric("24h Activity", metrics["recent_activity_24h"])
        
        with col5:
            st.metric("Error Rate (7d)", f"{metrics['error_rate_7d']}%")
    
    def render_tool_usage_chart(self, days: int = 30) -> None:
        """Render tool usage bar chart"""
        st.subheader("🛠️ Tool Usage Statistics")
        
        df_tools = self.get_tool_usage_data(days)
        
        if not df_tools.empty:
            # Create horizontal bar chart for better readability with long tool names
            st.bar_chart(df_tools.set_index('tool_name')['usage_count'])
            
            # Show top tools in a table
            if len(df_tools) > 5:
                st.subheader("Top 10 Tools")
                st.dataframe(df_tools.head(10), use_container_width=True)
        else:
            st.info(f"No tool usage data available for the last {days} days.")
    
    def render_proactive_execution_timeline(self, days: int = 7) -> None:
        """Render proactive agent execution timeline"""
        st.subheader("⏰ Proactive Agent Activity")
        
        df_proactive = self.get_proactive_execution_stats(days)
        
        if not df_proactive.empty:
            # Create a pivot table for better visualization
            pivot_df = df_proactive.pivot_table(
                index='datetime', 
                columns='tool_name', 
                values='executions', 
                fill_value=0
            )
            
            if not pivot_df.empty:
                st.line_chart(pivot_df)
            
            # Show execution summary
            st.subheader("Execution Summary")
            summary = df_proactive.groupby('tool_name')['executions'].sum().reset_index()
            summary = summary.sort_values('executions', ascending=False)
            st.dataframe(summary, use_container_width=True)
        else:
            st.info(f"No proactive agent execution data for the last {days} days.")
    
    def render_alerts_table(self, days: int = 7) -> None:
        """Render alerts and notifications table"""
        st.subheader("🚨 Recent Alerts & Notifications")
        
        df_alerts = self.get_alerts_data(days)
        
        if not df_alerts.empty:
            # Format the content for better display
            df_display = df_alerts.copy()
            df_display['timestamp'] = df_display['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_display['content'] = df_display['content'].str[:100] + '...'  # Truncate long content
            
            # Add color coding
            df_display['priority'] = df_display['type'].map({
                'alert': '🚨 High',
                'proactive': '🔔 Info'
            })
            
            # Reorder columns
            df_display = df_display[['timestamp', 'priority', 'content']]
            
            st.dataframe(df_display, use_container_width=True)
            
            # Show summary stats
            alert_counts = df_alerts['type'].value_counts()
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Alerts", alert_counts.get('alert', 0))
            
            with col2:
                st.metric("Proactive Notifications", alert_counts.get('proactive', 0))
        else:
            st.info(f"No alerts or notifications in the last {days} days.")
    
    def render_message_volume_chart(self, days: int = 30) -> None:
        """Render message volume over time"""
        st.subheader("💬 Message Volume Trends")
        
        df_volume = self.get_message_volume_stats(days)
        
        if not df_volume.empty:
            # Pivot for better visualization
            pivot_df = df_volume.pivot_table(
                index='date', 
                columns='role', 
                values='message_count', 
                fill_value=0
            )
            
            st.line_chart(pivot_df)
            
            # Show daily totals
            daily_totals = df_volume.groupby('date')['message_count'].sum().reset_index()
            daily_totals['date'] = daily_totals['date'].dt.strftime('%Y-%m-%d')
            
            st.subheader("Daily Message Totals")
            st.dataframe(daily_totals.tail(10), use_container_width=True)
        else:
            st.info(f"No message data available for the last {days} days.")
    
    def render_dashboard(self, days_filter: int = 7) -> None:
        """Render the complete dashboard"""
        st.title("🎛️ SOC Automation Dashboard")
        
        # Time range selector
        time_options = {
            "Last 24 Hours": 1,
            "Last Week": 7,
            "Last Month": 30,
            "Last 3 Months": 90
        }
        
        selected_range = st.selectbox(
            "Select Time Range", 
            options=list(time_options.keys()),
            index=1  # Default to "Last Week"
        )
        
        days = time_options[selected_range]
        
        # Render dashboard sections
        self.render_metrics_overview()
        
        st.divider()
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "Tool Usage", 
            "Agent Activity", 
            "Alerts & Notifications", 
            "Message Volume"
        ])
        
        with tab1:
            self.render_tool_usage_chart(days)
        
        with tab2:
            self.render_proactive_execution_timeline(days)
        
        with tab3:
            self.render_alerts_table(days)
        
        with tab4:
            self.render_message_volume_chart(days)


# Global dashboard instance
_dashboard_renderer = None


def get_dashboard_renderer() -> DashboardRenderer:
    """Get or create global dashboard renderer"""
    global _dashboard_renderer
    if _dashboard_renderer is None:
        _dashboard_renderer = DashboardRenderer()
    return _dashboard_renderer


# Legacy function for backward compatibility
def render_dashboard():
    """Render dashboard (legacy function)"""
    renderer = get_dashboard_renderer()
    renderer.render_dashboard()