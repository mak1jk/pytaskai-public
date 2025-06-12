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
    list_tasks_tool,
    get_task_tool,
    get_next_task_tool,
    validate_tasks_tool,
    parse_prd_tool,
    add_task_tool,
    update_task_test_coverage_tool,
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
    initial_sidebar_state="expanded",
)

# Initialize session state
if "project_root" not in st.session_state:
    st.session_state.project_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
if "ai_service" not in st.session_state:
    st.session_state.ai_service = AIService()
if "tasks_data" not in st.session_state:
    st.session_state.tasks_data = None
if "selected_task_id" not in st.session_state:
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
        ["Dashboard", "Task Management", "Bug Analytics", "PRD Parser", "AI Assistant", "Settings"],
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Task Management":
        show_task_management()
    elif page == "Bug Analytics":
        show_bug_analytics()
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
    """Display task management interface with bug tracking support"""
    st.header("📋 Task Management")

    # Load and display tasks
    tasks_result = call_mcp_tool(
        list_tasks_tool,
        project_root=st.session_state.project_root,
        include_subtasks=True,
        include_stats=True,
    )

    if tasks_result.get("error"):
        st.error(f"Error loading tasks: {tasks_result['error']}")
        return

    tasks = tasks_result.get("tasks", [])
    stats = tasks_result.get("statistics", {})

    # Filter controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "in-progress", "review", "done", "blocked", "cancelled"],
            key="status_filter"
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Filter by Priority", 
            ["All", "highest", "high", "medium", "low", "lowest"],
            key="priority_filter"
        )
    
    with col3:
        type_filter = st.selectbox(
            "Filter by Type",
            ["All", "task", "bug", "feature", "enhancement", "research", "documentation"],
            key="type_filter"
        )
    
    with col4:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Apply filters
    filtered_tasks = tasks
    if status_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get("status") == status_filter]
    if priority_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get("priority") == priority_filter]
    if type_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get("type", "task") == type_filter]

    # Display statistics
    if stats:
        st.subheader("📊 Project Statistics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Tasks", stats.get("total_tasks", 0))
        with col2:
            st.metric("Bugs", len([t for t in tasks if t.get("type") == "bug"]))
        with col3:
            st.metric("Features", len([t for t in tasks if t.get("type") == "feature"]))
        with col4:
            st.metric("Completed", len([t for t in tasks if t.get("status") == "done"]))
        with col5:
            st.metric("In Progress", len([t for t in tasks if t.get("status") == "in-progress"]))

    # Display task list
    st.subheader(f"📋 Tasks ({len(filtered_tasks)} of {len(tasks)})")
    
    if not filtered_tasks:
        st.info("No tasks match the current filters. Try adjusting the filters above.")
    else:
        for task in filtered_tasks:
            render_task_card(task)

    # Add new task/bug form
    st.markdown("---")
    show_add_task_form()


def render_task_card(task: Dict[str, Any]):
    """Render a task card with bug tracking and test coverage support"""
    task_type = task.get("type", "task")
    task_id = task.get("id")
    title = task.get("title", "Untitled")
    status = task.get("status", "pending")
    priority = task.get("priority", "medium")
    
    # Card container with color coding based on type and priority
    type_colors = {
        "bug": "#ffebee",      # Light red
        "feature": "#e3f2fd",  # Light blue
        "task": "#f5f5f5",     # Light gray
        "enhancement": "#fff3e0", # Light orange
        "research": "#f3e5f5",    # Light purple
        "documentation": "#e8f5e8" # Light green
    }
    
    priority_borders = {
        "highest": "#d32f2f",  # Red
        "high": "#f57c00",     # Orange
        "medium": "#1976d2",   # Blue
        "low": "#388e3c",      # Green
        "lowest": "#616161"    # Gray
    }
    
    with st.container():
        # Task header with type icon and status
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            type_icon = {
                "bug": "🐛",
                "feature": "⭐",
                "task": "📋",
                "enhancement": "🔧",
                "research": "🔍",
                "documentation": "📚"
            }.get(task_type, "📋")
            
            st.markdown(f"### {type_icon} #{task_id}: {title}")
        
        with col2:
            st.markdown(f"**Status:** {status}")
        
        with col3:
            st.markdown(f"**Priority:** {priority}")
        
        # Task description
        description = task.get("description", "No description")
        if len(description) > 150:
            description = description[:150] + "..."
        st.markdown(f"**Description:** {description}")
        
        # Bug-specific fields
        if task_type == "bug":
            show_bug_details(task)
        
        # Test coverage info
        show_test_coverage_info(task)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(f"📝 Edit", key=f"edit_{task_id}"):
                st.session_state.selected_task_id = task_id
                st.session_state.show_edit_modal = True
        
        with col2:
            if st.button(f"🔍 Details", key=f"details_{task_id}"):
                show_task_details(task)
        
        with col3:
            if task_type != "bug" and st.button(f"🐛 Report Bug", key=f"bug_{task_id}"):
                st.session_state.create_bug_for_task = task_id
        
        with col4:
            if st.button(f"📊 Update Coverage", key=f"coverage_{task_id}"):
                st.session_state.update_coverage_task = task_id
        
        st.markdown("---")


def show_bug_details(task: Dict[str, Any]):
    """Show bug-specific details in task card"""
    severity = task.get("severity")
    if severity:
        severity_colors = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        st.markdown(f"**Severity:** {severity_colors.get(severity, '⚪')} {severity}")
    
    # Show bug details in expandable section
    with st.expander("🐛 Bug Details"):
        if task.get("steps_to_reproduce"):
            st.markdown(f"**Steps to Reproduce:**\n{task['steps_to_reproduce']}")
        
        if task.get("expected_result"):
            st.markdown(f"**Expected Result:**\n{task['expected_result']}")
        
        if task.get("actual_result"):
            st.markdown(f"**Actual Result:**\n{task['actual_result']}")
        
        if task.get("environment"):
            st.markdown(f"**Environment:**\n{task['environment']}")


def show_test_coverage_info(task: Dict[str, Any]):
    """Show test coverage information"""
    target_coverage = task.get("target_test_coverage")
    achieved_coverage = task.get("achieved_test_coverage")
    related_tests = task.get("related_tests", [])
    
    if target_coverage is not None or achieved_coverage is not None or related_tests:
        with st.expander("📊 Test Coverage"):
            col1, col2 = st.columns(2)
            
            with col1:
                if target_coverage is not None:
                    st.metric("Target Coverage", f"{target_coverage}%")
                
            with col2:
                if achieved_coverage is not None:
                    delta = None
                    if target_coverage is not None:
                        delta = f"{achieved_coverage - target_coverage:+.1f}%"
                    st.metric("Achieved Coverage", f"{achieved_coverage}%", delta=delta)
            
            if related_tests:
                st.markdown("**Related Tests:**")
                for test in related_tests:
                    st.markdown(f"- {test}")
            
            if task.get("test_report_url"):
                st.markdown(f"[📊 View Coverage Report]({task['test_report_url']})")


def show_task_details(task: Dict[str, Any]):
    """Show detailed task information in modal"""
    st.markdown("### 📋 Task Details")
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**ID:** {task.get('id')}")
        st.markdown(f"**Type:** {task.get('type', 'task')}")
        st.markdown(f"**Status:** {task.get('status')}")
        st.markdown(f"**Priority:** {task.get('priority')}")
    
    with col2:
        st.markdown(f"**Created:** {task.get('created_at', 'Unknown')}")
        st.markdown(f"**Updated:** {task.get('updated_at', 'Unknown')}")
        if task.get("estimated_hours"):
            st.markdown(f"**Estimated Hours:** {task['estimated_hours']}")
    
    # Full description
    st.markdown("**Description:**")
    st.markdown(task.get("description", "No description"))
    
    # Dependencies
    if task.get("dependencies"):
        st.markdown("**Dependencies:**")
        for dep in task["dependencies"]:
            st.markdown(f"- Task #{dep}")
    
    # Subtasks
    if task.get("subtasks"):
        st.markdown("**Subtasks:**")
        for subtask in task["subtasks"]:
            st.markdown(f"- {subtask.get('title', 'Untitled')} ({subtask.get('status', 'pending')})")


def show_add_task_form():
    """Show form for adding new tasks/bugs with enhanced fields"""
    st.subheader("➕ Add New Task/Bug")
    
    tab1, tab2 = st.tabs(["📋 Task", "🐛 Bug Report"])
    
    with tab1:
        show_task_form()
    
    with tab2:
        show_bug_form()


def show_task_form():
    """Show form for adding regular tasks"""
    with st.form("add_task_form"):
        st.markdown("#### Create New Task")
        
        col1, col2 = st.columns(2)
        
        with col1:
            task_type = st.selectbox(
                "Task Type",
                ["task", "feature", "enhancement", "research", "documentation"],
                index=0
            )
            priority = st.selectbox(
                "Priority",
                ["lowest", "low", "medium", "high", "highest"],
                index=2
            )
        
        with col2:
            target_coverage = st.number_input(
                "Target Test Coverage (%)",
                min_value=0.0,
                max_value=100.0,
                value=80.0,
                step=5.0,
                help="Optional target test coverage percentage"
            )
            use_research = st.checkbox("Use AI Research", value=False)
        
        prompt = st.text_area(
            "Task Description",
            height=100,
            help="Describe what needs to be done. Be specific about requirements."
        )
        
        related_tests = st.text_input(
            "Related Tests (comma-separated)",
            help="List test files or test names related to this task"
        )
        
        submitted = st.form_submit_button("🚀 Create Task")
        
        if submitted and prompt:
            create_task(
                prompt=prompt,
                task_type=task_type,
                priority=priority,
                target_test_coverage=target_coverage if target_coverage > 0 else None,
                related_tests=related_tests,
                use_research=use_research
            )


def show_bug_form():
    """Show form for reporting bugs"""
    with st.form("add_bug_form"):
        st.markdown("#### 🐛 Report Bug")
        
        col1, col2 = st.columns(2)
        
        with col1:
            severity = st.selectbox(
                "Severity",
                ["low", "medium", "high", "critical"],
                index=1
            )
            priority = st.selectbox(
                "Priority",
                ["lowest", "low", "medium", "high", "highest"],
                index=3  # Default to high for bugs
            )
        
        with col2:
            environment = st.text_input(
                "Environment",
                placeholder="e.g., Chrome 120, Python 3.11, macOS 14"
            )
        
        prompt = st.text_area(
            "Bug Summary",
            height=60,
            help="Brief description of the bug"
        )
        
        steps_to_reproduce = st.text_area(
            "Steps to Reproduce",
            height=80,
            help="Detailed steps to reproduce the bug"
        )
        
        expected_result = st.text_area(
            "Expected Result",
            height=60,
            help="What should happen"
        )
        
        actual_result = st.text_area(
            "Actual Result",
            height=60,
            help="What actually happens"
        )
        
        submitted = st.form_submit_button("🐛 Report Bug")
        
        if submitted and prompt:
            create_bug(
                prompt=prompt,
                severity=severity,
                priority=priority,
                steps_to_reproduce=steps_to_reproduce,
                expected_result=expected_result,
                actual_result=actual_result,
                environment=environment
            )


def create_task(prompt: str, task_type: str, priority: str, target_test_coverage: Optional[float] = None, related_tests: str = "", use_research: bool = False):
    """Create a new task using MCP tools"""
    try:
        with st.spinner("Creating task..."):
            result = call_mcp_tool(
                add_task_tool,
                project_root=st.session_state.project_root,
                prompt=prompt,
                task_type=task_type,
                priority=priority,
                target_test_coverage=target_test_coverage,
                related_tests=related_tests,
                use_research=use_research
            )
            
            if result.get("error"):
                st.error(f"Error creating task: {result['error']}")
            else:
                st.success(f"✅ Task created successfully! ID: {result.get('task_id')}")
                st.rerun()
                
    except Exception as e:
        st.error(f"Failed to create task: {str(e)}")


def create_bug(prompt: str, severity: str, priority: str, steps_to_reproduce: str, expected_result: str, actual_result: str, environment: str):
    """Create a new bug report using MCP tools"""
    try:
        with st.spinner("Creating bug report..."):
            result = call_mcp_tool(
                add_task_tool,
                project_root=st.session_state.project_root,
                prompt=prompt,
                task_type="bug",
                severity=severity,
                priority=priority,
                steps_to_reproduce=steps_to_reproduce,
                expected_result=expected_result,
                actual_result=actual_result,
                environment=environment
            )
            
            if result.get("error"):
                st.error(f"Error creating bug report: {result['error']}")
            else:
                st.success(f"🐛 Bug report created successfully! ID: {result.get('task_id')}")
                st.rerun()
                
    except Exception as e:
        st.error(f"Failed to create bug report: {str(e)}")


def show_prd_parser():
    """Display PRD parser interface"""
    st.header("📄 PRD Parser")

    st.markdown(
        """
    Upload or paste your Product Requirements Document (PRD) to automatically 
    generate structured tasks with AI assistance.
    """
    )

    # PRD input options
    input_method = st.radio("Input Method", ["Upload File", "Paste Text"])

    if input_method == "Upload File":
        uploaded_file = st.file_uploader("Choose a PRD file", type=["txt", "md"])
        if uploaded_file:
            st.text_area(
                "PRD Content Preview",
                uploaded_file.read().decode(),
                height=200,
                disabled=True,
            )
    else:
        prd_text = st.text_area(
            "Paste PRD Content",
            height=300,
            placeholder="Paste your PRD content here...",
        )

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
        project_root = st.text_input(
            "Project Root Directory", value=st.session_state.project_root
        )

    if st.button("💾 Save Settings"):
        st.success("Settings would be saved!")


def show_bug_analytics():
    """Display bug analytics dashboard"""
    try:
        from components.bug_analytics import render_bug_analytics_dashboard, render_quick_bug_report_form
        
        # Main analytics dashboard
        render_bug_analytics_dashboard(st.session_state.project_root)
        
        # Quick bug report form
        st.markdown("---")
        render_quick_bug_report_form(st.session_state.project_root)
        
    except ImportError:
        st.error("Bug analytics component not available")
    except Exception as e:
        st.error(f"Error loading bug analytics: {str(e)}")


if __name__ == "__main__":
    main()
