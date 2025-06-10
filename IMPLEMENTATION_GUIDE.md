# Guida Implementazione Features UI Avanzate

## 🔧 Task 26: Tracking Token e Costi LiteLLM

### Implementazione Tecnica

**1. Estensione AIService per Usage Tracking**
```python
# mcp_server/ai_service.py

import litellm
from datetime import datetime
from typing import Dict, Any
from .usage_tracker import UsageTracker

class AIService:
    def __init__(self):
        self.usage_tracker = UsageTracker()
    
    async def _research_llm_call(self, model_name: str, system_prompt: str, user_prompt: str, operation_type: str = "unknown") -> Dict:
        start_time = datetime.now()
        
        try:
            response = await litellm.acompletion(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Estrai usage data dalla response LiteLLM
            usage_data = {
                "model": model_name,
                "provider": model_name.split('/')[0] if '/' in model_name else 'openai',
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "operation_type": operation_type,
                "timestamp": start_time.isoformat(),
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "success": True
            }
            
            # Calcola costo basato su pricing LiteLLM
            cost = self._calculate_cost(model_name, usage_data["input_tokens"], usage_data["output_tokens"])
            usage_data["cost_usd"] = cost
            
            # Salva tracking data
            self.usage_tracker.record_usage(usage_data)
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # Track failed calls (no cost)
            self.usage_tracker.record_usage({
                "model": model_name,
                "operation_type": operation_type,
                "timestamp": start_time.isoformat(),
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "success": False,
                "error": str(e),
                "cost_usd": 0.0
            })
            raise
    
    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        # Pricing data per model (aggiornare periodicamente)
        pricing = {
            "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},  # per 1K tokens
            "anthropic/claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "perplexity/llama-3-sonar-large-32k-online": {"input": 0.001, "output": 0.001}
        }
        
        if model_name not in pricing:
            return 0.0  # Unknown model
            
        model_pricing = pricing[model_name]
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return round(input_cost + output_cost, 6)
```

**2. Usage Tracker**
```python
# mcp_server/usage_tracker.py

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

class UsageTracker:
    def __init__(self, data_dir: str = ".taskmaster/usage"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.usage_file = self.data_dir / "usage.json"
        
    def record_usage(self, usage_data: Dict[str, Any]):
        """Record a single usage event"""
        # Load existing data
        all_usage = self._load_usage_data()
        
        # Add new usage
        all_usage.append(usage_data)
        
        # Save updated data
        with open(self.usage_file, 'w') as f:
            json.dump(all_usage, f, indent=2)
    
    def _load_usage_data(self) -> List[Dict]:
        if not self.usage_file.exists():
            return []
        
        with open(self.usage_file, 'r') as f:
            return json.load(f)
    
    def get_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        all_usage = self._load_usage_data()
        
        # Filter recent usage
        recent_usage = [
            u for u in all_usage 
            if datetime.fromisoformat(u["timestamp"]) > cutoff_date and u.get("success", True)
        ]
        
        # Aggregate data
        summary = {
            "total_calls": len(recent_usage),
            "total_tokens": sum(u.get("total_tokens", 0) for u in recent_usage),
            "total_cost_usd": sum(u.get("cost_usd", 0) for u in recent_usage),
            "by_model": defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0}),
            "by_operation": defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0}),
            "daily_breakdown": self._get_daily_breakdown(recent_usage)
        }
        
        # Aggregate by model and operation
        for usage in recent_usage:
            model = usage.get("model", "unknown")
            operation = usage.get("operation_type", "unknown")
            tokens = usage.get("total_tokens", 0)
            cost = usage.get("cost_usd", 0)
            
            summary["by_model"][model]["calls"] += 1
            summary["by_model"][model]["tokens"] += tokens
            summary["by_model"][model]["cost"] += cost
            
            summary["by_operation"][operation]["calls"] += 1
            summary["by_operation"][operation]["tokens"] += tokens
            summary["by_operation"][operation]["cost"] += cost
        
        return summary
    
    def _get_daily_breakdown(self, usage_data: List[Dict]) -> Dict[str, Dict]:
        daily = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0})
        
        for usage in usage_data:
            date = datetime.fromisoformat(usage["timestamp"]).date().isoformat()
            daily[date]["calls"] += 1
            daily[date]["tokens"] += usage.get("total_tokens", 0)
            daily[date]["cost"] += usage.get("cost_usd", 0)
        
        return dict(daily)
```

**3. Dashboard Streamlit per Usage**
```python
# frontend/components/usage_dashboard.py

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

def render_usage_dashboard(usage_tracker):
    st.header("📊 AI Usage & Costs")
    
    # Time filter
    col1, col2 = st.columns(2)
    with col1:
        days = st.selectbox("Periodo", [1, 7, 30, 90], index=2)
    with col2:
        auto_refresh = st.checkbox("Auto-refresh", value=True)
    
    # Get usage data
    summary = usage_tracker.get_usage_summary(days=days)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Calls", summary["total_calls"])
    with col2:
        st.metric("Total Tokens", f"{summary['total_tokens']:,}")
    with col3:
        st.metric("Total Cost", f"${summary['total_cost_usd']:.4f}")
    with col4:
        avg_cost_per_call = summary['total_cost_usd'] / max(summary['total_calls'], 1)
        st.metric("Avg Cost/Call", f"${avg_cost_per_call:.4f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Model breakdown pie chart
        if summary["by_model"]:
            model_data = summary["by_model"]
            df_models = pd.DataFrame([
                {"Model": model, "Cost": data["cost"], "Calls": data["calls"]}
                for model, data in model_data.items()
            ])
            
            fig = px.pie(df_models, values="Cost", names="Model", title="Cost by Model")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Operation breakdown
        if summary["by_operation"]:
            op_data = summary["by_operation"]
            df_ops = pd.DataFrame([
                {"Operation": op, "Cost": data["cost"], "Calls": data["calls"]}
                for op, data in op_data.items()
            ])
            
            fig = px.bar(df_ops, x="Operation", y="Cost", title="Cost by Operation")
            st.plotly_chart(fig, use_container_width=True)
    
    # Daily trend
    if summary["daily_breakdown"]:
        df_daily = pd.DataFrame([
            {"Date": date, "Cost": data["cost"], "Calls": data["calls"], "Tokens": data["tokens"]}
            for date, data in summary["daily_breakdown"].items()
        ])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_daily["Date"], y=df_daily["Cost"], name="Cost ($)"))
        fig.add_trace(go.Scatter(x=df_daily["Date"], y=df_daily["Calls"], name="Calls", yaxis="y2"))
        
        fig.update_layout(
            title="Daily Usage Trend",
            yaxis=dict(title="Cost ($)"),
            yaxis2=dict(title="Calls", overlaying="y", side="right")
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Budget alert
    daily_budget = st.number_input("Daily Budget ($)", min_value=0.0, value=5.0, step=0.1)
    today_cost = summary["daily_breakdown"].get(datetime.now().date().isoformat(), {}).get("cost", 0)
    
    if today_cost > daily_budget:
        st.error(f"⚠️ Budget exceeded! Today: ${today_cost:.4f} / Budget: ${daily_budget:.2f}")
    elif today_cost > daily_budget * 0.8:
        st.warning(f"🔶 Near budget limit: ${today_cost:.4f} / ${daily_budget:.2f}")
    else:
        st.success(f"✅ Within budget: ${today_cost:.4f} / ${daily_budget:.2f}")
```

## 📋 Task 27: UI Kanban Stile Trello

### Implementazione Tecnica

**1. Board Kanban con Streamlit**
```python
# frontend/components/kanban_board.py

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import streamlit.components.v1 as components

def render_kanban_board(tasks):
    st.header("📋 Task Board")
    
    # Columns definition
    columns = {
        "backlog": {"title": "📝 Backlog", "color": "#f0f0f0"},
        "todo": {"title": "📌 To Do", "color": "#e3f2fd"},
        "in_progress": {"title": "🔄 In Progress", "color": "#fff3e0"},
        "review": {"title": "👀 Review", "color": "#f3e5f5"},
        "done": {"title": "✅ Done", "color": "#e8f5e8"}
    }
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        priority_filter = st.multiselect("Priority", ["high", "medium", "low"], default=["high", "medium", "low"])
    with col2:
        search_term = st.text_input("Search tasks")
    with col3:
        show_subtasks = st.checkbox("Show subtasks", value=True)
    
    # Filter tasks
    filtered_tasks = [
        task for task in tasks 
        if task.priority in priority_filter 
        and (not search_term or search_term.lower() in task.title.lower())
    ]
    
    # Group tasks by status
    tasks_by_status = {status: [] for status in columns.keys()}
    for task in filtered_tasks:
        status = task.status if task.status in columns else "backlog"
        tasks_by_status[status].append(task)
    
    # Render columns
    cols = st.columns(len(columns))
    
    for i, (status, column_config) in enumerate(columns.items()):
        with cols[i]:
            st.markdown(f"### {column_config['title']}")
            st.markdown(f"<div style='background-color: {column_config['color']}; padding: 10px; border-radius: 5px; min-height: 400px;'>", unsafe_allow_html=True)
            
            # Task cards
            for task in tasks_by_status[status]:
                render_task_card(task, show_subtasks)
            
            # Add task button
            if st.button(f"➕ Add to {column_config['title']}", key=f"add_{status}"):
                st.session_state[f"show_add_form_{status}"] = True
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Bulk actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh Board"):
            st.rerun()
    with col2:
        if st.button("📊 Analytics"):
            show_board_analytics(tasks)
    with col3:
        if st.button("📤 Export"):
            export_board_data(tasks)

def render_task_card(task, show_subtasks=True):
    # Priority color coding
    priority_colors = {
        "high": "#ffebee",
        "medium": "#fff8e1", 
        "low": "#e8f5e8"
    }
    
    # Card container
    with st.container():
        st.markdown(
            f"""
            <div style='
                background-color: {priority_colors.get(task.priority, "#f5f5f5")};
                padding: 12px;
                margin: 8px 0;
                border-radius: 8px;
                border-left: 4px solid {"#f44336" if task.priority == "high" else "#ff9800" if task.priority == "medium" else "#4caf50"};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            '>
                <div style='font-weight: bold; margin-bottom: 8px;'>#{task.id} {task.title}</div>
                <div style='font-size: 0.9em; color: #666; margin-bottom: 8px;'>{task.description[:100]}{'...' if len(task.description) > 100 else ''}</div>
            """,
            unsafe_allow_html=True
        )
        
        # Badges
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<span style='background-color: #2196f3; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;'>{task.priority}</span>", unsafe_allow_html=True)
        with col2:
            if hasattr(task, 'subtasks') and task.subtasks:
                st.markdown(f"<span style='background-color: #9c27b0; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;'>{len(task.subtasks)} subtasks</span>", unsafe_allow_html=True)
        with col3:
            if task.dependencies:
                st.markdown(f"<span style='background-color: #ff5722; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;'>{len(task.dependencies)} deps</span>", unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📝", key=f"edit_{task.id}", help="Edit task"):
                st.session_state[f"edit_task_{task.id}"] = True
        with col2:
            if st.button("🔍", key=f"expand_{task.id}", help="Expand with AI"):
                # Trigger AI expansion
                pass
        with col3:
            if st.button("📊", key=f"analyze_{task.id}", help="Analyze complexity"):
                # Trigger complexity analysis
                pass
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_board_analytics(tasks):
    st.subheader("📊 Board Analytics")
    
    # Status distribution
    status_counts = {}
    for task in tasks:
        status = task.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    col1, col2 = st.columns(2)
    with col1:
        # Donut chart for status
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=.3
        )])
        fig.update_layout(title="Task Distribution by Status")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Priority breakdown
        priority_counts = {}
        for task in tasks:
            priority = task.priority
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        import plotly.express as px
        df_priority = pd.DataFrame([
            {"Priority": p, "Count": c} 
            for p, c in priority_counts.items()
        ])
        fig = px.bar(df_priority, x="Priority", y="Count", title="Tasks by Priority")
        st.plotly_chart(fig, use_container_width=True)

# Custom Drag-and-Drop Component (JavaScript)
def render_drag_drop_board():
    # Custom HTML/JS component for true drag-and-drop
    drag_drop_html = """
    <div id="kanban-board">
        <style>
            .kanban-column {
                display: inline-block;
                width: 18%;
                margin: 1%;
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 10px;
                vertical-align: top;
                min-height: 500px;
            }
            .task-card {
                background-color: white;
                border-radius: 4px;
                padding: 10px;
                margin: 8px 0;
                cursor: move;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: box-shadow 0.2s;
            }
            .task-card:hover {
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .task-card.dragging {
                opacity: 0.5;
            }
        </style>
        
        <div class="kanban-column" id="backlog">
            <h4>📝 Backlog</h4>
            <div class="task-list" ondrop="drop(event)" ondragover="allowDrop(event)">
                <!-- Tasks will be populated here -->
            </div>
        </div>
        
        <!-- More columns... -->
        
        <script>
            function allowDrop(ev) {
                ev.preventDefault();
            }
            
            function drag(ev) {
                ev.dataTransfer.setData("text", ev.target.id);
                ev.target.classList.add("dragging");
            }
            
            function drop(ev) {
                ev.preventDefault();
                var data = ev.dataTransfer.getData("text");
                var draggedElement = document.getElementById(data);
                var dropZone = ev.target.closest('.task-list');
                
                if (dropZone) {
                    dropZone.appendChild(draggedElement);
                    draggedElement.classList.remove("dragging");
                    
                    // Notify Streamlit of status change
                    var taskId = data.replace('task-', '');
                    var newStatus = dropZone.closest('.kanban-column').id;
                    window.parent.postMessage({
                        type: 'task-moved',
                        taskId: taskId,
                        newStatus: newStatus
                    }, '*');
                }
            }
        </script>
    </div>
    """
    
    components.html(drag_drop_html, height=600)
```

### Features Principali Implementate:

1. **👀 Task 26 - Token Usage Tracking:**
   - Tracking automatico di input/output tokens per ogni chiamata LiteLLM
   - Calcolo costi in tempo reale basato su pricing aggiornato
   - Dashboard con grafici per analisi usage
   - Budget controls e alerting
   - Breakdown per modello/operazione

2. **📋 Task 27 - Kanban Board:**
   - Board visuale con colonne drag-and-drop  
   - Card colorate per priorità
   - Badge per subtask e dipendenze
   - Filtri avanzati e ricerca
   - Analytics board con charts
   - Quick actions per AI operations

Questi task trasformano il tuo pytaskai Python in una piattaforma completa e moderna che compete con strumenti enterprise come Jira, ma con l'AI intelligence integrata!

Le implementazioni sono modulari e possono essere sviluppate incrementalmente. Il tracking dei costi è particolarmente importante per gestire i budget AI in progetti di produzione.