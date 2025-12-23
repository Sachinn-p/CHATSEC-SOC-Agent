"""
Main application entry point for SOC Agent Automation.
"""
import streamlit as st
import asyncio
import pandas as pd
from typing import List, Dict, Any

# Import from new structured modules
from src.core.agent import init_agent, run_agent
from src.database.models import init_db, get_all_messages
from src.core.proactive_agents import add_proactive_agent, remove_proactive_agent
from src.ui.dashboard import render_dashboard
from src.ui.chat import get_chat_interface
from config.settings import Config

# Configure Streamlit
st.set_page_config(
    page_title="SOC Agent Automation", 
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize configuration
try:
    config = Config()
    config.validate_config()
except Exception as e:
    st.error(f"Configuration error: {e}")
    st.stop()

# Initialize database
try:
    init_db()
except Exception as e:
    st.warning(f"Database initialization warning: {e}")

# Main application title
st.title("🤖 SOC Agent Automation Platform")
st.markdown("*MCP + Wazuh Chat with Proactive Agents & Dashboard*")

# Initialize session state
if "agent" not in st.session_state:
    try:
        st.session_state.agent = init_agent()
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()

if "current_tool" not in st.session_state:
    st.session_state.current_tool = None

# Sidebar - System Status
st.sidebar.header("🔧 System Status")
if st.session_state.agent:
    st.sidebar.success("✅ Agent Ready")
else:
    st.sidebar.error("❌ Agent Not Ready")

# Chat History in Sidebar
st.sidebar.header("💬 Recent Activity")
try:
    conversations = pd.DataFrame(get_all_messages())
    if not conversations.empty:
        recent_count = min(10, len(conversations))
        st.sidebar.info(f"📊 {len(conversations)} total messages")
        
        # Show last few messages
        recent_messages = conversations.tail(5)
        for _, msg in recent_messages.iterrows():
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            truncated_content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            st.sidebar.caption(f"{role_icon} {truncated_content}")
    else:
        st.sidebar.info("No conversation history yet")
except Exception as e:
    st.sidebar.warning(f"Error loading history: {e}")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat Interface", "⚙️ Proactive Agents", "📊 Dashboard"])

# Chat Tab
with tab1:
    st.header("💬 Interactive Chat")
    
    # Get chat interface and set up agent runner
    chat_interface = get_chat_interface()
    
    async def agent_runner(prompt: str, previous_messages: List[Dict[str, Any]]) -> str:
        """Run agent with proper error handling"""
        try:
            result = await run_agent(st.session_state.agent, prompt, previous_messages)
            return result
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def sync_agent_runner(prompt: str, previous_messages: List[Dict[str, Any]]) -> str:
        """Synchronous wrapper for agent runner"""
        try:
            return asyncio.run(agent_runner(prompt, previous_messages))
        except Exception as e:
            return f"❌ Error running agent: {str(e)}"
    
    # Render chat interface with agent runner
    chat_interface.render_chat_tab(agent_runner_callback=sync_agent_runner)

# Proactive Agents Tab
with tab2:
    st.header("⚙️ Proactive Agent Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("➕ Add New Proactive Agent")
        
        with st.form("add_agent_form"):
            agent_name = st.text_input(
                "Agent Name", 
                placeholder="e.g., security_monitor",
                help="Unique identifier for this proactive agent"
            )
            
            agent_prompt = st.text_area(
                "Prompt", 
                placeholder="e.g., Check for any new security alerts in the last hour",
                help="The prompt that will be executed periodically",
                height=100
            )
            
            interval_minutes = st.number_input(
                "Interval (minutes)", 
                min_value=1, 
                value=config.DEFAULT_PROACTIVE_INTERVAL,
                help="How often to execute this agent"
            )
            
            retries = st.number_input(
                "Retry Attempts", 
                min_value=0, 
                value=2, 
                max_value=5,
                help="Number of retry attempts on failure"
            )
            
            submitted = st.form_submit_button("🚀 Add Proactive Agent")
            
            if submitted:
                if agent_name and agent_prompt:
                    try:
                        add_proactive_agent(
                            agent_name, 
                            interval_minutes, 
                            agent_prompt, 
                            st.session_state.agent, 
                            retries
                        )
                        st.success(f"✅ Added proactive agent '{agent_name}' with {interval_minutes} minute interval")
                    except Exception as e:
                        st.error(f"❌ Error adding agent: {e}")
                else:
                    st.error("Please provide both agent name and prompt")
    
    with col2:
        st.subheader("🗑️ Manage Agents")
        
        # Show existing agents (this would need to be implemented in the proactive_agents module)
        st.info("Active agents management will be shown here")
        
        # Remove agent functionality
        st.subheader("❌ Remove Agent")
        remove_name = st.text_input("Agent name to remove")
        if st.button("Remove Agent"):
            if remove_name:
                try:
                    remove_proactive_agent(remove_name)
                    st.success(f"✅ Removed proactive agent '{remove_name}'")
                except Exception as e:
                    st.error(f"❌ Error removing agent: {e}")
            else:
                st.error("Please provide agent name to remove")
    
    # Agent Status Section
    st.subheader("📊 Agent Status")
    st.info("Proactive agent status monitoring will be displayed here")

# Dashboard Tab  
with tab3:
    st.header("📊 SOC Automation Dashboard")
    
    try:
        render_dashboard()
    except Exception as e:
        st.error(f"Error rendering dashboard: {e}")
        st.info("Dashboard features are being loaded...")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div style='text-align: center; color: #666;'>
        <small>
        SOC Agent Automation v1.0<br/>
        Powered by MCP + Groq + Wazuh
        </small>
    </div>
    """, 
    unsafe_allow_html=True
)