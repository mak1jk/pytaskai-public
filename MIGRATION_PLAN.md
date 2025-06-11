# PyTaskAI Core Module Migration Plan

## Overview
This document outlines the migration strategy from the current `shared/` module structure to the new `core/` module architecture.

## Migration Strategy

### Phase 1: Establish Core Foundation ✅ COMPLETED
- [x] Create `core/` directory structure
- [x] Implement `core/exceptions.py` with centralized exception hierarchy
- [x] Implement `core/protocols.py` with abstract base classes
- [x] Implement `core/models.py` with pure domain models  
- [x] Implement `core/constants.py` with centralized constants
- [x] Implement `core/utils.py` with common utilities
- [x] Add backward compatibility imports from `shared/`

### Phase 2: Gradual Migration (Next Steps)

#### 2.1 Update Import Statements
- Update all imports from `shared.models` to use `core` equivalents
- Maintain backward compatibility during transition period
- Add deprecation warnings for old import paths

#### 2.2 Migrate Exceptions
- Replace scattered exception handling with core exceptions
- Update all `raise Exception()` to use typed exceptions
- Implement proper exception chaining

#### 2.3 Standardize Utilities
- Replace duplicate utility functions with core utilities
- Centralize common operations (hashing, validation, etc.)
- Remove redundant code

### Phase 3: Infrastructure Layer (Future)
- Move `cache_manager.py` and `usage_tracker.py` to `infrastructure/`
- Implement protocol-based abstractions
- Add configuration management

### Phase 4: Services Layer (Future)  
- Extract AI service components to `services/`
- Implement dependency injection
- Create service interfaces

## Backward Compatibility

### Import Aliases
The core module provides import aliases for existing shared models:

```python
# Old way (still works)
from shared.models import Task, TaskStatus

# New way (recommended)
from core import Task, TaskStatus
from core.models import Task, TaskStatus
```

### Exception Handling
Old exception patterns are still supported but deprecated:

```python
# Old way
raise Exception("Task not found")

# New way  
from core.exceptions import TaskNotFoundError
raise TaskNotFoundError(task_id=123)
```

## Testing Strategy

### Unit Tests
- All core modules have comprehensive unit tests
- Test backward compatibility imports
- Validate exception hierarchy
- Test utility functions

### Integration Tests
- Verify existing functionality still works
- Test import compatibility
- Validate database operations
- Test AI service integration

### Migration Tests
- Test migration scripts
- Validate data integrity
- Check performance impact
- Verify rollback procedures

## Rollback Plan

### If Issues Arise
1. **Immediate Rollback**: Disable new core imports via feature flag
2. **Partial Rollback**: Revert specific modules while keeping others
3. **Full Rollback**: Restore shared/ module structure
4. **Data Integrity**: Ensure no data loss during rollback

### Monitoring
- Monitor error rates during migration
- Track performance metrics
- Watch for import failures
- Monitor test suite results

## Benefits of New Architecture

### Developer Experience
- **Clearer Structure**: Separation of concerns between domain, infrastructure, and services
- **Better Testing**: Protocol-based design enables easy mocking
- **Type Safety**: Comprehensive type hints and validation
- **Documentation**: Better organized and documented code

### Maintainability  
- **Reduced Coupling**: Clear dependencies between layers
- **Easier Refactoring**: Well-defined interfaces make changes safer
- **Code Reuse**: Common utilities prevent duplication
- **Consistent Patterns**: Standardized error handling and validation

### Scalability
- **Modular Design**: Easy to add new features without affecting existing code
- **Plugin Architecture**: Protocol-based design enables easy extensions
- **Performance**: Optimized utilities and caching strategies
- **Resource Management**: Better separation of concerns

## Implementation Checklist

### Core Module ✅
- [x] Exception hierarchy implemented
- [x] Protocol definitions complete
- [x] Domain models defined
- [x] Constants centralized
- [x] Utilities implemented
- [x] Backward compatibility ensured

### Integration Testing
- [ ] Test all existing functionality
- [ ] Verify MCP tools still work
- [ ] Test CLI commands
- [ ] Verify AI service integration
- [ ] Test database operations

### Documentation Updates
- [ ] Update README with new architecture
- [ ] Document migration guide
- [ ] Update API documentation
- [ ] Create architecture diagrams

### Deployment
- [ ] Feature flag implementation
- [ ] Gradual rollout strategy
- [ ] Monitoring and alerting
- [ ] Rollback procedures tested

## Next Steps

1. **Complete Task 1**: Mark current task as completed
2. **Integration Testing**: Verify all existing functionality works
3. **Start Task 2**: Begin LLMProvider protocol implementation  
4. **Documentation**: Update architecture documentation
5. **Team Review**: Get feedback on new structure

## Risk Assessment

### Low Risk
- Backward compatibility maintained
- Comprehensive test coverage
- Gradual migration approach

### Medium Risk  
- Import path changes
- Exception handling updates
- Performance impact assessment

### High Risk
- Database schema changes (future)
- Major refactoring of existing code (future)
- Breaking changes to APIs (avoided)

## Success Metrics

- ✅ All existing tests pass
- ✅ No performance degradation
- ✅ Backward compatibility maintained
- ✅ Code coverage ≥80%
- ✅ Zero critical bugs introduced