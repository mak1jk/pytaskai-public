"""
PyTaskAI - Streamlit Frontend Application

Modern web interface for PyTaskAI task management with MCP integration.
Provides comprehensive UI for PRD parsing, task management, and AI interaction.
"""

import streamlit as st
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.task_manager import (
    list_tasks_tool, get_task_tool, get_next_task_tool, 
    validate_tasks_tool, parse_prd_tool
)
from mcp_server.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="PyTaskAI - AI Task Management",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'project_root' not in st.session_state:
    st.session_state.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if 'ai_service' not in st.session_state:
    st.session_state.ai_service = AIService()
if 'tasks_data' not in st.session_state:
    st.session_state.tasks_data = None
if 'selected_task_id' not in st.session_state:
    st.session_state.selected_task_id = None

def call_mcp_tool(tool_func, *args, **kwargs) -> Dict[str, Any]:
    """
    Safely call MCP tools with proper async handling.
    """
    try:
        # Handle async functions
        if asyncio.iscoroutinefunction(tool_func):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(tool_func(*args, **kwargs))
            finally:
                loop.close()
        else:
            result = tool_func(*args, **kwargs)
        
        return result
    except Exception as e:
        st.error(f"Error calling MCP tool: {str(e)}")
        logger.error(f"MCP tool error: {str(e)}")
        return {"error": str(e)}

def main():
    """Main Streamlit application"""
    
    st.title("🤖 PyTaskAI - AI Task Management")
    st.markdown("*Advanced task management with AI-powered insights*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Task Management", "PRD Parser", "AI Assistant", "Settings"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Task Management":
        show_task_management()
    elif page == "PRD Parser":
        show_prd_parser()
    elif page == "AI Assistant":
        show_ai_assistant()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    """Display main dashboard"""
    st.header("📊 Project Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", "0", "0")
    with col2:
        st.metric("Completed", "0", "0")
    with col3:
        st.metric("In Progress", "0", "0")
    with col4:
        st.metric("Pending", "0", "0")
    
    st.markdown("---")
    
    # Recent activity placeholder
    st.subheader("📈 Recent Activity")
    st.info("No recent activity. Start by parsing a PRD or adding tasks!")

def show_task_management():
    """Display task management interface"""
    st.header("📋 Task Management")
    
    # Task list placeholder
    st.subheader("Current Tasks")
    st.info("No tasks found. Use the PRD Parser to generate tasks or add them manually.")
    
    # Add task form
    st.subheader("➕ Add New Task")
    with st.form("add_task_form"):
        title = st.text_input("Task Title")
        description = st.text_area("Description")
        priority = st.selectbox("Priority", ["low", "medium", "high"])
        
        submitted = st.form_submit_button("Add Task")
        if submitted and title:
            st.success(f"Task '{title}' would be added with {priority} priority")

def show_prd_parser():
    """Display PRD parser interface"""
    st.header("📄 PRD Parser")
    
    st.markdown("""
    Upload or paste your Product Requirements Document (PRD) to automatically 
    generate structured tasks with AI assistance.
    """)
    
    # PRD input options
    input_method = st.radio("Input Method", ["Upload File", "Paste Text"])
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader("Choose a PRD file", type=['txt', 'md'])
        if uploaded_file:
            st.text_area("PRD Content Preview", uploaded_file.read().decode(), height=200, disabled=True)
    else:
        prd_text = st.text_area("Paste PRD Content", height=300, placeholder="Paste your PRD content here...")
    
    # Parsing options
    col1, col2 = st.columns(2)
    with col1:
        num_tasks = st.slider("Number of Tasks to Generate", 5, 30, 10)
    with col2:
        use_research = st.checkbox("Enable AI Research", value=True)
    
    if st.button("🚀 Parse PRD and Generate Tasks", type="primary"):
        st.info("PRD parsing would be initiated here...")

def show_ai_assistant():
    """Display AI assistant interface"""
    st.header("🤖 AI Assistant")
    
    st.markdown("Ask questions about your project or get AI-powered task suggestions.")
    
    # Chat interface placeholder
    st.subheader("💬 Chat with AI")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your project..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI response placeholder
        with st.chat_message("assistant"):
            response = f"I would help you with: {prompt}"
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

def show_settings():
    """Display settings interface"""
    st.header("⚙️ Settings")
    
    # API Configuration
    st.subheader("🔑 API Configuration")
    
    with st.expander("AI Model Settings"):
        openai_key = st.text_input("OpenAI API Key", type="password")
        anthropic_key = st.text_input("Anthropic API Key", type="password")
        perplexity_key = st.text_input("Perplexity API Key", type="password")
    
    with st.expander("Project Settings"):
        project_name = st.text_input("Project Name", value="My Project")
        project_root = st.text_input("Project Root Directory", value=st.session_state.project_root)
    
    if st.button("💾 Save Settings"):
        st.success("Settings would be saved!")

if __name__ == "__main__":
    main()