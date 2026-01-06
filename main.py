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
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat Interface", "🖥️ Agent Management", "⚙️ Proactive Agents", "📊 Dashboard"])

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

# Agent Management Tab
with tab2:
    st.header("🖥️ Wazuh Agent Management")
    
    # Show current agents
    st.subheader("📋 Current Agents")
    try:
        agents_result = st.session_state.agent.get_all_agents_info()
        
        if agents_result.get("success"):
            agents = agents_result.get("agents", [])
            
            if agents:
                # Create a summary
                st.metric("Total Agents", len(agents))
                
                # Display agents in a table
                agent_data = []
                for agent in agents:
                    agent_data.append({
                        "ID": agent.get("id", "N/A"),
                        "Name": agent.get("name", "N/A"),
                        "IP": agent.get("ip", "N/A"),
                        "Status": agent.get("status", "N/A"),
                        "Version": agent.get("version", "N/A"),
                        "Last Keep Alive": agent.get("lastKeepAlive", "N/A")
                    })
                
                st.dataframe(agent_data, use_container_width=True)
            else:
                st.info("No agents found")
        else:
            st.error(f"Failed to load agents: {agents_result.get('error')}")
    except Exception as e:
        st.error(f"Error loading agents: {str(e)}")
    
    st.divider()
    
    # Add new agent section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("➕ Add New Agent")
        
        with st.form("add_wazuh_agent_form"):
            st.markdown("""
            Register a new agent to monitor with Wazuh. After registration, you'll receive 
            an agent key that needs to be installed on the target system.
            """)
            
            new_agent_name = st.text_input(
                "Agent Name (Hostname)*",
                placeholder="e.g., srv-web-01, win-workstation-05",
                help="The hostname of the system to monitor"
            )
            
            new_agent_ip = st.text_input(
                "IP Address",
                value="any",
                placeholder="e.g., 192.168.1.100 or 'any' for dynamic IP",
                help="Use 'any' for DHCP systems or provide static IP"
            )
            
            new_agent_groups = st.text_input(
                "Groups (comma-separated)",
                placeholder="e.g., webservers, production",
                help="Optional: Assign agent to groups for easier management"
            )
            
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                submit_agent = st.form_submit_button("🚀 Register Agent", use_container_width=True)
            
            if submit_agent:
                if not new_agent_name:
                    st.error("❌ Agent name is required")
                else:
                    try:
                        with st.spinner("Registering agent..."):
                            # Parse groups
                            groups = None
                            if new_agent_groups:
                                groups = [g.strip() for g in new_agent_groups.split(",")]
                            
                            # Register agent
                            result = st.session_state.agent.add_new_agent(
                                name=new_agent_name,
                                ip=new_agent_ip,
                                groups=groups
                            )
                            
                            if result.get("success"):
                                agent_info = result.get("agent", {})
                                st.success(f"✅ {result.get('message')}")
                                
                                # Display agent details
                                st.subheader("Agent Registration Details")
                                
                                col_info1, col_info2 = st.columns(2)
                                with col_info1:
                                    st.metric("Agent ID", agent_info.get("id", "N/A"))
                                    st.metric("Agent Name", agent_info.get("name", "N/A"))
                                with col_info2:
                                    st.metric("IP Address", agent_info.get("ip", "N/A"))
                                    st.metric("Status", agent_info.get("status", "pending"))
                                
                                # Show agent key
                                agent_key = agent_info.get("key")
                                if agent_key:
                                    st.info("🔑 **Agent Authentication Key**")
                                    st.code(agent_key, language="text")
                                    
                                    st.markdown("""
                                    **Next Steps:**
                                    1. Copy the agent key above
                                    2. Install Wazuh agent on the target system
                                    3. Import the key using: `wazuh-agent-auth -k <KEY>`
                                    4. Start the agent service
                                    
                                    For detailed installation instructions, visit: 
                                    https://documentation.wazuh.com/current/installation-guide/wazuh-agent/
                                    """)
                                
                                # Rerun to refresh agent list
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('error')}")
                    except Exception as e:
                        st.error(f"❌ Error registering agent: {str(e)}")
    
    with col2:
        st.subheader("🗑️ Remove Agent")
        
        with st.form("remove_agent_form"):
            st.markdown("Remove an agent from Wazuh monitoring.")
            
            remove_agent_id = st.text_input(
                "Agent ID",
                placeholder="e.g., 001, 005",
                help="The ID of the agent to remove"
            )
            
            purge_agent = st.checkbox(
                "Purge completely",
                help="Remove all agent data from database"
            )
            
            submit_remove = st.form_submit_button("🗑️ Remove Agent", use_container_width=True)
            
            if submit_remove:
                if not remove_agent_id:
                    st.error("❌ Agent ID is required")
                else:
                    try:
                        with st.spinner("Removing agent..."):
                            result = st.session_state.agent.remove_agent(
                                agent_id=remove_agent_id,
                                purge=purge_agent
                            )
                            
                            if result.get("success"):
                                st.success(f"✅ {result.get('message')}")
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('error')}")
                    except Exception as e:
                        st.error(f"❌ Error removing agent: {str(e)}")

# Proactive Agents Tab
with tab3:
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
with tab4:
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