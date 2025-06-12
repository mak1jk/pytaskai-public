# PyTaskAI Changelog

## 0.2.0 - 2024-12-06

### 🏗️ **Major Architectural Improvements**

#### Added
- **Core Domain Layer**: New `core/` module implementing clean architecture principles
  - Pure domain models without infrastructure dependencies
  - Comprehensive exception hierarchy with contextual error handling
  - Protocol-based abstractions for dependency injection
  - Centralized constants and business rules
  - Common utilities with comprehensive test coverage

- **Architectural Roadmap**: Comprehensive PRD and implementation plan
  - 12 detailed architectural improvement tasks (Tasks 14-25)
  - 5-phase implementation strategy covering service layer, infrastructure, testing, and documentation
  - Clear separation of concerns and SOLID principles application

#### Fixed
- **MCP Tool Integration**: Resolved critical issue with FastMCP tool calling
  - Fixed `'FunctionTool' object is not callable` error
  - Implemented proper `.fn` attribute access for external MCP tool calls
  - Systematic debugging identified and resolved MCP-database disconnect

- **Database Integration**: Enhanced SQLite database functionality
  - Improved error handling for enum validation
  - Fixed task creation with proper enum value formatting
  - Better integration between MCP tools and database layer

#### Improved
- **Error Handling**: Enhanced exception hierarchy with typed exceptions
  - `PyTaskAIError` base class with contextual details
  - Specialized exceptions: `ValidationError`, `ConfigurationError`, `AIServiceError`
  - `TaskNotFoundError` and `DependencyError` for domain-specific errors

- **Configuration Management**: Centralized configuration constants
  - AI provider models and cost estimates
  - Default model configurations by role
  - Environment variable definitions
  - Quality metrics thresholds

#### Technical Debt Reduction
- **Backward Compatibility**: Full compatibility maintained with existing `shared/` module
  - Import aliases ensure zero breaking changes
  - Gradual migration path established
  - Comprehensive migration plan documented

### 🔧 **Infrastructure & Development**

#### Added
- **Debug Tools**: Systematic debugging utilities for development
  - MCP tool integration testing scripts
  - Database connection verification tools
  - External calling pattern validation

#### Documentation
- **Architecture Documentation**: Comprehensive architectural improvement PRD
- **Migration Guide**: Detailed migration strategy with phases and rollback plans
- **Development Scripts**: Tools for manual task creation and debugging

### 📊 **Task Management**

#### Enhanced
- **Task Database**: 25 total tasks including 12 new architectural improvement tasks
  - Phase 2: Service Layer Implementation (Tasks 14-17)
  - Phase 3: Infrastructure Layer (Tasks 18-21)  
  - Phase 4: Quality & Testing (Tasks 22-23)
  - Phase 5: Documentation & Security (Tasks 24-25)

### 🏃‍♂️ **Performance & Reliability**

#### Improved
- **Database Performance**: Optimized SQLite operations with proper enum handling
- **MCP Tool Reliability**: Resolved calling issues ensuring consistent tool access
- **Error Recovery**: Better error context and recovery mechanisms

### 🔬 **Testing & Quality**

#### Added
- **Debug Test Suite**: Comprehensive testing for MCP tool integration
- **Integration Verification**: End-to-end testing of database and MCP connectivity
- **Error Scenario Testing**: Systematic testing of failure modes and recovery

### ⚡ **Next Phase Ready**

The release establishes the foundation for Phase 2 implementation:
- LLM Provider Factory Pattern (Task 14) - Ready to implement
- AI Service Orchestration refactoring (Task 15) - Dependencies resolved
- Enhanced Task Management Service (Task 16) - Architecture in place
- Multi-tier Cache Service (Task 17) - Specifications defined

### 🔄 **Migration Notes**

This release maintains full backward compatibility. Existing code continues to work without changes:

```python
# Old way (still works)
from shared.models import Task, TaskStatus

# New way (recommended)
from core import Task, TaskStatus
from core.models import Task, TaskStatus
```

### 🐛 **Bug Fixes**

- Fixed MCP tool calling pattern for external interfaces
- Resolved enum validation issues in task creation
- Corrected database constraint handling for task IDs
- Fixed asyncio event loop conflicts in AI service integration

---

## 0.0.5 - 2025-01-06

### 🚀 Advanced Features
- **Dedicated Bug Reporting Tool**: New `report_bug_tool` MCP tool for streamlined bug reporting
  - Enhanced validation and recommendations
  - Automatic bug report formatting
  - Integration with related tasks
- **Bug Analytics Dashboard**: Comprehensive bug statistics and visualization
  - Severity and status distribution charts
  - Bug trend analysis and resolution metrics
  - Actionable recommendations based on bug data
- **Jira Integration Architecture**: Foundation for bidirectional Jira sync
  - Task-to-Jira mapping strategies
  - Configurable sync options and conflict resolution
  - Intelligent issue type determination

### 🔧 Enhanced MCP Tools
- **`report_bug_tool`**: Dedicated bug reporting with enhanced validation
- **`get_bug_statistics_tool`**: Comprehensive bug analytics and metrics
- **Quick Bug Report Form**: Streamlit UI component for rapid bug reporting

### 📊 Analytics & Insights  
- **Bug Metrics Dashboard**: Visual analytics for bug tracking
- **Resolution Rate Tracking**: Monitor bug resolution efficiency
- **Severity Distribution Analysis**: Understand bug impact patterns
- **Historical Trend Analysis**: Track bug patterns over time

### 🎨 UI Enhancements
- **Bug Analytics Page**: Dedicated Streamlit page for bug insights
- **Interactive Charts**: Plotly-powered bug visualization
- **Quick Action Forms**: Streamlined bug reporting interface
- **Recommendations Engine**: Automated suggestions based on bug data

### 📚 Architecture Improvements
- **Modular Component System**: Reusable Streamlit components
- **Enhanced Error Handling**: Better error reporting and recovery
- **Flexible Configuration**: Extensible settings for integrations

## 0.0.4 - 2025-01-06

### 🚀 New Features
- **Bug Tracking System**: Comprehensive bug tracking with dedicated fields
  - Support for `type` field (task, bug, feature, enhancement, research, documentation)
  - Bug-specific fields: severity, steps_to_reproduce, expected_result, actual_result, environment
  - Enhanced MCP tools support for bug creation and filtering
- **Test Coverage Tracking**: Built-in test coverage management
  - `target_test_coverage` and `achieved_test_coverage` fields
  - `test_report_url` for coverage reports
  - `related_tests` field for test file associations
  - New `update_task_test_coverage_tool` MCP tool for coverage updates
- **Enhanced Task Management**: Extended task model with new capabilities
  - Support for attachments field
  - Test metadata tracking (tests_passed, total_tests, failed_tests)
  - Improved task filtering by type in `list_tasks_tool`

### 🔧 Technical Improvements  
- Extended Pydantic models with new enums: `TaskType`, `BugSeverity`
- Enhanced `add_task_tool` with support for bug-specific parameters
- Improved validation for new task fields
- Better error handling for invalid task types and coverage values

### 📚 Documentation
- Updated `IMPLEMENTATION_GUIDE.md` with complete PRD requirements
- Enhanced tool documentation with bug tracking workflows
- Added comprehensive examples for new task types

### 🎯 Workflow Integration
- Designed for coding agent integration where agents execute tests and report results
- MCP tools focused on data management rather than test execution
- Support for external test reporting and coverage analysis

## 0.0.3 - 2025-01-06

### 🚀 Features
- **LiteLLM Integration**: Complete integration with real AI providers (OpenAI, Anthropic, Perplexity, Google, xAI)
- **Environment Configuration**: Comprehensive `.env` support for API keys and model configuration
- **Fallback Strategy**: Intelligent model fallback when primary providers are unavailable
- **Cost Tracking**: Built-in usage tracking and budget management

### 🐛 Bug Fixes  
- **MCP Tools**: Fixed AsyncIO event loop conflicts preventing task creation
- **Path Issues**: Resolved `.taskmaster` path problems, now uses `.pytaskai` correctly
- **Error Handling**: Improved error handling and graceful degradation
- **Code Structure**: Fixed code corruption in ai_service.py

### 🔧 Technical Improvements
- All MCP tools now properly async/await compatible
- Enhanced project root validation and path management
- Better try/catch error handling throughout codebase
- Improved logging and debugging capabilities

### 📚 Documentation
- Updated PRD with LiteLLM integration requirements
- Added comprehensive `.env.example` configuration file
- Enhanced implementation guides and troubleshooting

### 🔒 Security
- API keys managed through environment variables
- No hardcoded credentials in codebase
- Secure configuration management

## 0.0.1 - 2025-01-01

### 🎉 Initial Release

- Added `DISABLE_INTERLEAVED_THINKING` to give users the option to opt out of interleaved thinking.
- Improved model references to show provider-specific names (Sonnet 3.7 for Bedrock, Sonnet 4 for Console)
- Updated documentation links and OAuth process descriptions

## 0.3.0

- Claude Code is now generally available
- Introducing Sonnet 4 and Opus 4 models

## 0.2.125

- Breaking change: Bedrock ARN passed to `ANTHROPIC_MODEL` or `ANTHROPIC_SMALL_FAST_MODEL` should no longer contain an escaped slash (specify `/` instead of `%2F`)
- Removed `DEBUG=true` in favor of `ANTHROPIC_LOG=debug`, to log all requests

## 0.2.117

- Breaking change: --print JSON output now returns nested message objects, for forwards-compatibility as we introduce new metadata fields
- Introduced settings.cleanupPeriodDays
- Introduced CLAUDE_CODE_API_KEY_HELPER_TTL_MS env var
- Introduced --debug mode

## 0.2.108

- You can now send messages to Claude while it works to steer Claude in real-time
- Introduced BASH_DEFAULT_TIMEOUT_MS and BASH_MAX_TIMEOUT_MS env vars
- Fixed a bug where thinking was not working in -p mode
- Fixed a regression in /cost reporting
- Deprecated MCP wizard interface in favor of other MCP commands
- Lots of other bugfixes and improvements

## 0.2.107

- CLAUDE.md files can now import other files. Add @path/to/file.md to ./CLAUDE.md to load additional files on launch

## 0.2.106

- MCP SSE server configs can now specify custom headers
- Fixed a bug where MCP permission prompt didn't always show correctly

## 0.2.105

- Claude can now search the web
- Moved system & account status to /status
- Added word movement keybindings for Vim
- Improved latency for startup, todo tool, and file edits

## 0.2.102

- Improved thinking triggering reliability
- Improved @mention reliability for images and folders
- You can now paste multiple large chunks into one prompt

## 0.2.100

- Fixed a crash caused by a stack overflow error
- Made db storage optional; missing db support disables --continue and --resume

## 0.2.98

- Fixed an issue where auto-compact was running twice

## 0.2.96

- Claude Code can now also be used with a Claude Max subscription (https://claude.ai/upgrade)

## 0.2.93

- Resume conversations from where you left off from with "claude --continue" and "claude --resume"
- Claude now has access to a Todo list that helps it stay on track and be more organized

## 0.2.82

- Added support for --disallowedTools
- Renamed tools for consistency: LSTool -> LS, View -> Read, etc.

## 0.2.75

- Hit Enter to queue up additional messages while Claude is working
- Drag in or copy/paste image files directly into the prompt
- @-mention files to directly add them to context
- Run one-off MCP servers with `claude --mcp-config <path-to-file>`
- Improved performance for filename auto-complete

## 0.2.74

- Added support for refreshing dynamically generated API keys (via apiKeyHelper), with a 5 minute TTL
- Task tool can now perform writes and run bash commands

## 0.2.72

- Updated spinner to indicate tokens loaded and tool usage

## 0.2.70

- Network commands like curl are now available for Claude to use
- Claude can now run multiple web queries in parallel
- Pressing ESC once immediately interrupts Claude in Auto-accept mode

## 0.2.69

- Fixed UI glitches with improved Select component behavior
- Enhanced terminal output display with better text truncation logic

## 0.2.67

- Shared project permission rules can be saved in .claude/settings.json

## 0.2.66

- Print mode (-p) now supports streaming output via --output-format=stream-json
- Fixed issue where pasting could trigger memory or bash mode unexpectedly

## 0.2.63

- Fixed an issue where MCP tools were loaded twice, which caused tool call errors

## 0.2.61

- Navigate menus with vim-style keys (j/k) or bash/emacs shortcuts (Ctrl+n/p) for faster interaction
- Enhanced image detection for more reliable clipboard paste functionality
- Fixed an issue where ESC key could crash the conversation history selector

## 0.2.59

- Copy+paste images directly into your prompt
- Improved progress indicators for bash and fetch tools
- Bugfixes for non-interactive mode (-p)

## 0.2.54

- Quickly add to Memory by starting your message with '#'
- Press ctrl+r to see full output for long tool results
- Added support for MCP SSE transport

## 0.2.53

- New web fetch tool lets Claude view URLs that you paste in
- Fixed a bug with JPEG detection

## 0.2.50

- New MCP "project" scope now allows you to add MCP servers to .mcp.json files and commit them to your repository

## 0.2.49

- Previous MCP server scopes have been renamed: previous "project" scope is now "local" and "global" scope is now "user"

## 0.2.47

- Press Tab to auto-complete file and folder names
- Press Shift + Tab to toggle auto-accept for file edits
- Automatic conversation compaction for infinite conversation length (toggle with /config)

## 0.2.44

- Ask Claude to make a plan with thinking mode: just say 'think' or 'think harder' or even 'ultrathink'

## 0.2.41

- MCP server startup timeout can now be configured via MCP_TIMEOUT environment variable
- MCP server startup no longer blocks the app from starting up

## 0.2.37

- New /release-notes command lets you view release notes at any time
- `claude config add/remove` commands now accept multiple values separated by commas or spaces

## 0.2.36

- Import MCP servers from Claude Desktop with `claude mcp add-from-claude-desktop`
- Add MCP servers as JSON strings with `claude mcp add-json <n> <json>`

## 0.2.34

- Vim bindings for text input - enable with /vim or /config

## 0.2.32

- Interactive MCP setup wizard: Run "claude mcp add" to add MCP servers with a step-by-step interface
- Fix for some PersistentShell issues

## 0.2.31

- Custom slash commands: Markdown files in .claude/commands/ directories now appear as custom slash commands to insert prompts into your conversation
- MCP debug mode: Run with --mcp-debug flag to get more information about MCP server errors

## 0.2.30

- Added ANSI color theme for better terminal compatibility
- Fixed issue where slash command arguments weren't being sent properly
- (Mac-only) API keys are now stored in macOS Keychain

## 0.2.26

- New /approved-tools command for managing tool permissions
- Word-level diff display for improved code readability
- Fuzzy matching for slash commands

## 0.2.21

- Fuzzy matching for /commands
