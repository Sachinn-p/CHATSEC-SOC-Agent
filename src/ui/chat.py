"""
Chat interface module for SOC automation.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.database.models import DatabaseManager


class ChatManager:
    """Manager for chat functionality and history"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def load_chat_history(self, session_id: str = "default", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load chat history for a session"""
        return self.db_manager.get_all_messages(session_id=session_id, limit=limit)
    
    def save_user_message(self, message: str, session_id: str = "default") -> int:
        """Save user message to chat history"""
        return self.db_manager.save_message("user", message, session_id)
    
    def save_assistant_message(self, message: str, session_id: str = "default") -> int:
        """Save assistant message to chat history"""
        return self.db_manager.save_message("assistant", message, session_id)
    
    def get_chat_sessions(self) -> List[str]:
        """Get list of available chat sessions"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT session_id FROM messages ORDER BY session_id")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
    
    def create_new_session(self, session_id: str = None) -> str:
        """Create a new chat session"""
        if session_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"session_{timestamp}"
        return session_id
    
    def delete_chat_session(self, session_id: str) -> None:
        """Delete a chat session and all its messages"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM tools_log WHERE session_id = ?", (session_id,))
            conn.commit()
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a chat session"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get message count by role
            cursor.execute("""
                SELECT role, COUNT(*) as count 
                FROM messages 
                WHERE session_id = ? 
                GROUP BY role
            """, (session_id,))
            
            message_counts = dict(cursor.fetchall())
            
            # Get first and last message timestamps
            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM messages 
                WHERE session_id = ?
            """, (session_id,))
            
            first_msg, last_msg = cursor.fetchone()
            
            # Get tool usage count
            cursor.execute("""
                SELECT COUNT(*) 
                FROM tools_log 
                WHERE session_id = ?
            """, (session_id,))
            
            tool_usage_count = cursor.fetchone()[0]
        
        return {
            "session_id": session_id,
            "message_counts": message_counts,
            "first_message": first_msg,
            "last_message": last_msg,
            "tool_usage_count": tool_usage_count,
            "total_messages": sum(message_counts.values())
        }


class ChatInterface:
    """Streamlit chat interface"""
    
    def __init__(self, chat_manager: ChatManager = None):
        self.chat_manager = chat_manager or ChatManager()
    
    def render_chat_history_sidebar(self) -> Optional[str]:
        """Render chat history sidebar and return selected session"""
        st.sidebar.header("💬 Chat Sessions")
        
        sessions = self.chat_manager.get_chat_sessions()
        
        if not sessions:
            st.sidebar.info("No chat history available")
            return None
        
        # Session selection
        selected_session = st.sidebar.selectbox(
            "Select Session",
            options=["Current"] + sessions,
            index=0
        )
        
        if selected_session != "Current":
            # Show session stats
            stats = self.chat_manager.get_session_stats(selected_session)
            st.sidebar.metric("Messages", stats["total_messages"])
            st.sidebar.metric("Tool Uses", stats["tool_usage_count"])
            
            # Show delete button
            if st.sidebar.button(f"Delete {selected_session}", key=f"delete_{selected_session}"):
                self.chat_manager.delete_chat_session(selected_session)
                st.sidebar.success("Session deleted!")
                st.experimental_rerun()
            
            return selected_session
        
        return "default"
    
    def render_message_history(self, session_id: str = "default", limit: Optional[int] = None):
        """Render chat message history"""
        messages = self.chat_manager.load_chat_history(session_id, limit)
        
        # Display messages
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"], unsafe_allow_html=True)
    
    def render_chat_input(self, session_id: str = "default", placeholder: str = "Type your message...") -> Optional[str]:
        """Render chat input and return the user's message"""
        user_input = st.chat_input(placeholder)
        
        if user_input:
            # Save user message
            self.chat_manager.save_user_message(user_input, session_id)
            
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(user_input)
        
        return user_input
    
    def display_assistant_response(self, response: str, session_id: str = "default"):
        """Display and save assistant response"""
        # Display response
        with st.chat_message("assistant"):
            st.markdown(response, unsafe_allow_html=True)
        
        # Save response
        self.chat_manager.save_assistant_message(response, session_id)
    
    def render_session_manager(self):
        """Render session management interface"""
        st.sidebar.header("🗂️ Session Management")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("New Session", key="new_session"):
                new_session = self.chat_manager.create_new_session()
                st.session_state.current_session = new_session
                st.sidebar.success(f"Created {new_session}")
                st.experimental_rerun()
        
        with col2:
            if st.button("Clear Current", key="clear_current"):
                current_session = getattr(st.session_state, 'current_session', 'default')
                self.chat_manager.delete_chat_session(current_session)
                st.sidebar.success("Session cleared!")
                st.experimental_rerun()
    
    def render_chat_tab(self, agent_runner_callback=None):
        """Render complete chat tab interface"""
        # Initialize session state
        if 'current_session' not in st.session_state:
            st.session_state.current_session = 'default'
        
        # Render session management
        self.render_session_manager()
        
        # Render history sidebar and get selected session
        selected_session = self.render_chat_history_sidebar()
        current_session = selected_session or st.session_state.current_session
        
        # Session info
        if current_session != 'default':
            st.info(f"📁 Viewing session: {current_session}")
        
        # Render message history
        if current_session == st.session_state.current_session:
            # Show recent messages for current session
            self.render_message_history(current_session, limit=50)
        else:
            # Show all messages for selected historical session
            self.render_message_history(current_session)
        
        # Chat input (only for current session)
        if current_session == st.session_state.current_session:
            user_input = self.render_chat_input(current_session)
            
            # Process user input if provided and callback is available
            if user_input and agent_runner_callback:
                try:
                    with st.spinner("Processing your request..."):
                        # Get recent messages for context
                        recent_messages = self.chat_manager.load_chat_history(current_session, limit=10)
                        
                        # Run agent
                        response = agent_runner_callback(user_input, recent_messages)
                        
                        # Display response
                        self.display_assistant_response(response, current_session)
                        
                        # Rerun to show the new messages
                        st.experimental_rerun()
                
                except Exception as e:
                    error_msg = f"❌ Error processing your request: {str(e)}"
                    self.display_assistant_response(error_msg, current_session)
                    st.error("An error occurred while processing your request.")


# Global chat interface instance
_chat_interface = None


def get_chat_interface() -> ChatInterface:
    """Get or create global chat interface"""
    global _chat_interface
    if _chat_interface is None:
        _chat_interface = ChatInterface()
    return _chat_interface


# Legacy functions for backward compatibility
def load_chat(chat_id: str = "default"):
    """Load chat (legacy function)"""
    manager = ChatManager()
    return manager.load_chat_history(chat_id)


def delete_chat_history(chat_id: str):
    """Delete chat history (legacy function)"""
    manager = ChatManager()
    manager.delete_chat_session(chat_id)


def list_chats():
    """List chats (legacy function)"""
    manager = ChatManager()
    return manager.get_chat_sessions()