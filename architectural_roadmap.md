# 🚀 PyTaskAI Architectural Improvement Roadmap

## High-Level Objectives
- **Reduce coupling, duplication, and complexity**
- **Apply DRY & SOLID principles, favor testability and scalability**
- **Introduce clear modular structure and centralized configuration/resource management**

---

## Phase 1: Analysis & Baseline (1-2 days)
- ✅ **COMPLETED**: Identify "God-object" modules (ai_service.py, task_manager.py) and overlapping responsibilities
- ✅ **COMPLETED**: Map dependencies between components (cache_manager, usage_tracker, prompts, MCP tools)
- ✅ **COMPLETED**: Collect complexity metrics (radon) to define pre-refactor KPIs

**Current Baseline:**
- 40 Python files, 19,774 lines of code
- Complexity hotspots: task_manager.py (3,870 lines), ai_service.py (1,233 lines)
- Target KPIs established: ≤15 CC, ≥80% test coverage, ≥9.0 pylint score

---

## Phase 2: Project Layout Restructuring (2-3 days)

### Target Structure:
```
/pytaskai/
├── core/               # Pure domain (models & interfaces)
│   ├── models.py       # Pydantic domain models
│   ├── exceptions.py   # Shared exceptions
│   └── protocols.py    # Abstract Base Classes (LLMProvider, CacheBackend, UsageTracker…)
├── services/           # Application logic
│   ├── llm/            # Provider adapters (OpenAI, Anthropic…)
│   ├── research.py     # ResearchService
│   ├── generation.py   # TaskGenerationService
│   └── best_practices.py
├── infrastructure/     # Concrete protocol implementations
│   ├── cache/
│   ├── trackers/
│   └── settings.py     # Centralized config (pydantic-settings)
├── mcp_server/         # FastMCP API → calls *services*, no business logic
├── shared/             # Legacy compatibility
├── tests/
└── scripts/
```

---

## Phase 3: Responsibility Isolation (SOLID) (3-5 days)
- **LLMProvider protocol + factory** → each provider in dedicated module
- **ResearchService, BestPracticesService, TaskService** with small methods (<15 CC)
- **AIService becomes facade/orchestrator** that composes services, doesn't implement them
- **Dependency inversion**: services receive provider/cache/usage via dependency injection

---

## Phase 4: Eliminate Duplications & Constants (1-2 days)
- **Unify messages** like "Attempting fallback model" in core.constants
- **Singleton PromptRegistry** to load prompts from .tmpl files → centralized reuse
- **Common helpers** (estimate_cost, JSON-LLM parsing, cache-key generator) in core.utils

---

## Phase 5: Configuration Management (0.5 days)
- **Move env-vars to Settings model** (pydantic-settings) → validation, CLI/test overrides
- **Version settings.schema.json** for CI
- **Centralized configuration** with environment-specific overrides

---

## Phase 6: Error Handling & Logging (1 day)
- **Exception hierarchy** in core.exceptions
- **@log_exceptions decorator** and structured logger (JSON/ECS) with context (task_id, op_type)
- **Consistent error messages** and recovery strategies

---

## Phase 7: Testing, Quality & CI (2 days)
- **Pytest + coverage**; fixtures for fake providers
- **Pre-commit hooks**: black, isort, flake8, mypy, commitlint
- **GitHub Actions**: unit-tests, sonar scan, wheels build
- **Quality gates**: >80% coverage, <15 CC, >9.0 pylint score

---

## Phase 8: Incremental Migration (ongoing)
- **Extract providers first** (services/llm/*), then move research/generation functions
- **Feature flags** (env PYTASKAI_V2=1) for safe releases
- **Minimum 80% coverage** on migrated modules

---

## Phase 9: Documentation & DX (1 day)
- **High-level README** + C4 diagram (PlantUML)
- **docs/ with mkdocs** and updated MCP tools examples
- **API documentation** and architecture decision records (ADRs)

---

## Success KPIs
- ✅ Functions with CC ≤ 15
- ✅ Unit-test coverage ≥ 80%
- ✅ Pylint score ≥ 9.0
- ✅ Average CI build time < 3 min
- ✅ Module coupling reduced by 50%
- ✅ Code duplication < 5%

---

## Next Immediate Step
**Create core modules**: core.exceptions, core.protocols, core.models and move existing classes/exceptions.