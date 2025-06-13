# PyTaskAI v0.3.0

> **Minimal AI-powered task management with MCP integration and hexagonal architecture**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Project Status: ✅ COMPLETE - PRODUCTION READY

**🚀 Hexagonal architecture implementation completed successfully!**

- **Achievement**: Clean 2900-line codebase with 6 essential MCP tools
- **Quality**: 168 tests passing, 80% coverage, SOLID principles
- **Architecture**: Complete hexagonal (ports & adapters) implementation

## 🏗️ New Architecture: Hexagonal (Ports & Adapters)

```
pytaskai/
├── domain/               # 🔵 CORE - Pure business logic
│   ├── entities/         # Task, SubTask business entities  
│   ├── repositories/     # Abstract interfaces (ports)
│   └── services/         # Domain services
├── application/          # 🟡 USE CASES - Orchestration
│   ├── use_cases/        # Application use cases
│   ├── dto/              # Data Transfer Objects
│   └── interfaces/       # Ports for external services
├── infrastructure/       # 🟢 IMPLEMENTATION - Details
│   ├── persistence/      # SQLite implementation
│   └── external/         # OpenAI service
└── adapters/            # 🟠 EXTERNAL - User interfaces
    ├── mcp/              # MCP server adapter
    └── cli/              # CLI adapter
```

## 📊 Achievement Metrics (vs Previous)

| Aspect | Previous | ✅ Achieved |
|--------|----------|-------------|
| **Total Lines** | 5000+ | 2900 lines |
| **Dependencies** | 26+ | 6 core |
| **MCP Tools** | 27 | 6 essential |
| **AI Providers** | 9 | 1 (OpenAI) |
| **Test Coverage** | None | 80% (168 tests) |
| **Architecture** | Monolithic | Hexagonal |

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Setup environment
export OPENAI_API_KEY="your-key-here"

# CLI usage
pytaskai init                         # Initialize database
pytaskai task add "My new task"       # Add task
pytaskai task list                    # List tasks
pytaskai task generate 1              # AI subtask generation

# Run tests
python -m pytest pytaskai/tests/     # All 168 tests

# MCP integration (Claude Code)
# Configure in ~/.claude.json or MCP client
```

## 🔧 Essential Features (6 MCP Tools)

1. **list_tasks** - List tasks with filters
2. **get_task** - Get task details
3. **add_task** - Create new task
4. **update_task** - Modify task
5. **delete_task** - Remove task
6. **generate_subtasks** - AI-powered task breakdown

## 📊 Dependencies (Minimal)

```toml
dependencies = [
    "fastmcp>=0.3.0",      # MCP server
    "pydantic>=2.0.0",     # Data models
    "sqlalchemy>=2.0.0",   # Database
    "openai>=1.0.0",       # AI (OpenAI only)
    "click>=8.0.0",        # CLI
    "python-dotenv>=1.0.0" # Config
]
```

## 🏁 Implementation Status

### ✅ All Milestones Completed:
- [x] **MILESTONE 1**: Domain Layer - Entities, value objects, repository interfaces
- [x] **MILESTONE 2**: Application Layer - Use cases, DTOs, dependency injection
- [x] **MILESTONE 3**: Infrastructure Persistence - SQLite repository implementation
- [x] **MILESTONE 4**: MCP Adapter - FastMCP server with 6 essential tools
- [x] **MILESTONE 5**: Infrastructure AI - OpenAI service integration
- [x] **MILESTONE 6**: CLI Adapter - Click-based command line interface
- [x] **MILESTONE 7**: Integration & Testing - E2E tests, architecture validation

### 🎯 Quality Metrics Achieved:
- **168 tests passing** with **80% code coverage**
- **Zero business logic duplication** between CLI and MCP adapters  
- **Complete hexagonal architecture** with proper dependency inversion
- **SOLID principles compliance** validated through architecture tests

## 🎯 Design Principles

- **SOLID Principles**: Rigorously applied
- **DRY Implementation**: Zero code duplication
- **Hexagonal Architecture**: Clean separation of concerns
- **Domain-Driven Design**: Business logic in domain layer
- **Test-Driven**: Every layer fully testable
- **Incremental**: Each milestone is complete and functional

## 🤝 Contributing

This project now has a stable hexagonal architecture foundation! Contributions are welcome:

1. **Fork and clone** the repository
2. **Install development dependencies**: `pip install -e ".[dev]"`
3. **Run tests**: `python -m pytest pytaskai/tests/`
4. **Follow architecture**: Maintain hexagonal architecture principles
5. **Submit PR** with tests and documentation

See `CLAUDE.md` for detailed development guidelines.

## 📄 License

MIT License - see [LICENSE.md](LICENSE.md) for details.

---

**PyTaskAI v0.3.0** - Production-ready hexagonal architecture implementation complete! 🎉