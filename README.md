# PyTaskAI v0.3.0

> **Minimal AI-powered task management with MCP integration and hexagonal architecture**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Project Status: COMPLETE ARCHITECTURAL REFACTORING

**⚠️ This project is undergoing a complete reimplementation with hexagonal architecture.**

- **Previous version**: 5000+ lines, 27 MCP tools, over-engineered
- **New version**: Target 1000-1500 lines, 6 essential MCP tools, SOLID principles

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

## 🎯 Target Metrics (vs Previous)

| Aspect | Previous | New Target |
|--------|----------|------------|
| **Total Lines** | 5000+ | 1000-1500 |
| **Dependencies** | 26+ | 6 core |
| **MCP Tools** | 27 | 6 essential |
| **AI Providers** | 9 | 1 (OpenAI) |
| **Architectures** | 4 parallel | 1 hexagonal |
| **CLI Variants** | 2 duplicated | 1 unified |

## 🚀 Quick Start (Post-Implementation)

```bash
# Install
pip install pytaskai

# Setup environment
export OPENAI_API_KEY="your-key-here"

# CLI usage
pytaskai list                    # List tasks
pytaskai add "My new task"       # Add task
pytaskai generate 1              # AI subtask generation

# MCP integration (Claude Code)
# Add to your MCP client configuration
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

### ✅ Completed:
- [x] Complete cleanup of legacy code
- [x] New hexagonal architecture structure
- [x] Minimal dependency configuration

### 🚧 In Progress:
- [ ] **MILESTONE 1**: Domain Layer (Week 1)
- [ ] **MILESTONE 2**: Application Layer (Week 1-2)
- [ ] **MILESTONE 3**: Infrastructure Persistence (Week 2)
- [ ] **MILESTONE 4**: MCP Adapter (Week 2-3)
- [ ] **MILESTONE 5**: Infrastructure AI (Week 3)
- [ ] **MILESTONE 6**: CLI Adapter (Week 3-4)
- [ ] **MILESTONE 7**: Integration & Testing (Week 4)

## 🎯 Design Principles

- **SOLID Principles**: Rigorously applied
- **DRY Implementation**: Zero code duplication
- **Hexagonal Architecture**: Clean separation of concerns
- **Domain-Driven Design**: Business logic in domain layer
- **Test-Driven**: Every layer fully testable
- **Incremental**: Each milestone is complete and functional

## 🤝 Contributing

This project is currently under active refactoring. Please wait for the completion of the hexagonal architecture implementation before contributing.

## 📄 License

MIT License - see [LICENSE.md](LICENSE.md) for details.

---

**Note**: This README will be updated as the implementation progresses through the 7 milestones.