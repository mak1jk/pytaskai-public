# 🚀 PyTaskAI Streamlit Frontend

Modern web interface for PyTaskAI task management with AI-powered features.

## ✨ Features

### 📋 PRD Parser
- **Text Input**: Paste PRD content directly
- **File Upload**: Upload .txt or .md PRD files
- **AI Generation**: Generate tasks automatically from PRD
- **Smart Configuration**: 
  - Target task count (1-50)
  - AI research toggle
  - LTS dependencies preference
  - Overwrite protection

### 📝 Task Management
- **Task List**: View all tasks with filtering
- **Status Filters**: pending, in-progress, done, cancelled
- **Priority Filters**: high, medium, low
- **Task Details**: Full task information and subtasks
- **Statistics**: Real-time project metrics

### 🤖 AI Assistant
- **Custom Task Generation**: Chat with AI to create tasks
- **Research Integration**: Optional AI research for better tasks
- **Configuration Options**: Research, LTS deps, priority
- **Interactive Chat**: Natural language task requests

### 🔍 Task Details
- **Comprehensive View**: All task information
- **Implementation Details**: Step-by-step guidance
- **Test Strategy**: Testing approaches
- **Dependencies**: Task relationships
- **Metadata**: Creation time, complexity, estimates

## 🏗️ Architecture

### Core Components

```python
# Main UI Sections
├── render_prd_parser()     # PRD parsing interface
├── render_task_list()      # Task management view  
├── render_ai_chat()        # AI assistant chat
└── render_task_details()   # Detailed task view

# Utility Functions
├── call_mcp_tool()         # MCP tool wrapper
├── load_tasks_data()       # Task data loader
└── render_task_card()      # Task display component
```

### MCP Integration

The app integrates with PyTaskAI MCP tools:

- `parse_prd_tool`: Generate tasks from PRD
- `list_tasks_tool`: Get all project tasks
- `get_task_tool`: Get specific task details
- `get_next_task_tool`: Find next task to work on
- `validate_tasks_tool`: Validate task structure

### AI Service Integration

Direct integration with PyTaskAI AI Service:
- Multi-provider LLM support (OpenAI, Anthropic, etc.)
- Research-backed task generation
- LTS dependency recommendations
- Intelligent prompt engineering

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Streamlit and dependencies
pip install streamlit>=1.28.0

# Or install full PyTaskAI package
pip install -e .
```

### 2. Launch Application

```bash
# Using the launcher script
python3 run_streamlit.py

# Or directly with Streamlit
streamlit run frontend/streamlit_app.py
```

### 3. Access Interface

Open your browser to: `http://localhost:8501`

## 📖 Usage Guide

### Generating Tasks from PRD

1. **Navigate** to "📋 PRD Parser" tab
2. **Input PRD** via text area or file upload
3. **Configure** generation settings:
   - Set target task count
   - Enable AI research (slower, more detailed)
   - Prefer LTS dependencies
4. **Generate** tasks with "🚀 Generate Tasks from PRD"
5. **Review** generated tasks in preview
6. **Navigate** to "📝 Task Management" to see all tasks

### Managing Tasks

1. **View Tasks** in "📝 Task Management" tab
2. **Filter** by status or priority
3. **Select Task** to view details
4. **Use Sidebar** for quick actions:
   - Refresh tasks
   - Get next task
   - Validate task structure

### AI Assistant

1. **Open** "🤖 AI Assistant" tab
2. **Describe** what you want to accomplish
3. **Configure** AI settings
4. **Generate** custom task with AI
5. **Review** detailed task breakdown

### Task Details

1. **Select** a task from Task Management
2. **View** in "🔍 Task Details" tab
3. **See** complete task information:
   - Description and details
   - Implementation steps
   - Test strategy
   - Dependencies and subtasks
   - Metadata and estimates

## 🛠️ Configuration

### Environment Variables

Configure AI models via environment variables:

```bash
# Model Selection
export PYTASKAI_DEFAULT_MODEL="gpt-4o-mini"
export PYTASKAI_RESEARCH_MODEL="anthropic/claude-3-haiku-20240307"

# API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export PERPLEXITY_API_KEY="your-perplexity-key"
```

### Project Root

The app automatically detects the project root directory. Ensure your project has:

```
project/
├── tasks/
│   └── tasks.json          # Task storage
├── .taskmaster/            # PyTaskAI config
└── frontend/
    └── streamlit_app.py    # This app
```

## 🧪 Testing

### Basic Functionality Test

```bash
# Test app logic without Streamlit installation
python3 test_streamlit_logic.py
```

### Full Integration Test

```bash
# Test all components (requires dependencies)
python3 test_streamlit_basic.py
```

## 🎨 UI Features

### Modern Interface
- **Responsive Design**: Works on desktop and tablet
- **Intuitive Navigation**: Tab-based interface
- **Interactive Elements**: Buttons, filters, selections
- **Real-time Updates**: Dynamic data loading

### Visual Indicators
- **Status Colors**: 🔵 Pending, 🟡 In Progress, 🟢 Done, 🔴 Cancelled
- **Priority Colors**: 🔴 High, 🟡 Medium, 🟢 Low
- **Progress Metrics**: Task statistics and completion rates
- **Loading States**: Spinners for async operations

### Smart Features
- **Auto-refresh**: Automatically reload task data
- **Error Handling**: Graceful error messages
- **Validation**: Input validation and feedback
- **Responsive Layout**: Adapts to screen size

## 🔧 Troubleshooting

### Common Issues

**Streamlit not found:**
```bash
pip install streamlit>=1.28.0
```

**MCP tools error:**
```bash
pip install fastmcp>=0.4.0
```

**AI Service error:**
```bash
# Check API keys are set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

**Task loading error:**
```bash
# Check project structure
ls tasks/tasks.json
ls .taskmaster/
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Future Enhancements

- **Real-time Collaboration**: Multi-user task editing
- **Advanced Filtering**: Search, tags, date ranges
- **Export/Import**: Task data export to various formats
- **Gantt Charts**: Visual project timeline
- **Integration**: GitHub, Jira, Slack connections
- **Mobile App**: Native mobile interface

## 📝 Implementation Notes

### Async Handling

The app handles async MCP tools using `call_mcp_tool()` wrapper:

```python
def call_mcp_tool(tool_func, *args, **kwargs):
    """Safely execute async/sync MCP tools in Streamlit."""
    if asyncio.iscoroutinefunction(tool_func):
        return asyncio.run(tool_func(*args, **kwargs))
    else:
        return tool_func(*args, **kwargs)
```

### Session State

Key session state variables:

- `project_root`: Project directory path
- `ai_service`: AIService instance
- `tasks_data`: Cached task data
- `selected_task_id`: Currently selected task

### Error Handling

Comprehensive error handling for:
- MCP tool failures
- AI service errors
- File I/O issues
- Network timeouts
- Invalid user input

---

**Built with ❤️ using Streamlit and PyTaskAI**