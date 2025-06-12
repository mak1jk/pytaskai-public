# PyTaskAI Testing Guide

Comprehensive testing framework for PyTaskAI with multiple test suites covering functionality, integration, performance, and end-to-end workflows.

## Test Suite Overview

PyTaskAI includes six comprehensive test suites:

1. **Basic Tests** - Core functionality and imports
2. **MCP Tools Tests** - Bug reporting, analytics, and task management
3. **Integration Tests** - Workflow integration and data consistency
4. **Jira Integration Tests** - Jira mapping and sync functionality  
5. **Performance Tests** - Large dataset handling and concurrent operations
6. **End-to-End Tests** - Complete user workflows and real-world scenarios

## Quick Start

### Run All Tests
```bash
cd tests
python run_all_tests.py
```

### Quick Test (Basic + MCP Tools Only)
```bash
python run_all_tests.py --quick
```

### Skip Performance Tests (Faster Execution)
```bash
python run_all_tests.py --skip-performance
```

### Run Specific Test Suite
```bash
python run_all_tests.py --test basic
python run_all_tests.py --test mcp
python run_all_tests.py --test integration
python run_all_tests.py --test jira
python run_all_tests.py --test performance
python run_all_tests.py --test e2e
```

## Test Suite Details

### 1. Basic Tests (`test_basic.py`)

**Purpose:** Verify core functionality and imports
**Duration:** ~1-2 seconds
**Coverage:**
- Module imports (AIService, models)
- Basic object creation
- Core dependencies

**Run individually:**
```bash
python test_basic.py
```

### 2. MCP Tools Tests (`test_mcp_tools.py`) 

**Purpose:** Test all MCP tools functionality
**Duration:** ~5-10 seconds
**Coverage:**
- Task creation with all field types
- Bug reporting with dedicated tool
- Bug analytics and statistics
- Test coverage tracking
- Task filtering and search
- Error handling and validation

**Key Test Classes:**
- `TestMCPToolsBasic` - Basic task/bug creation
- `TestBugReportingTool` - Dedicated bug reporting functionality
- `TestBugAnalytics` - Statistics and analytics generation
- `TestTestCoverageTracking` - Test coverage management
- `TestTaskFiltering` - Enhanced filtering capabilities
- `TestErrorHandling` - Error scenarios and edge cases

### 3. Integration Tests (`test_integration_workflows.py`)

**Purpose:** Test complete workflows and integration scenarios
**Duration:** ~10-20 seconds
**Coverage:**
- Complete bug lifecycle (report → analyze → resolve)
- Multi-bug analytics workflows
- Task creation with test coverage requirements
- Dependency validation workflows
- Concurrent operations handling

**Key Test Classes:**
- `TestBugTrackingWorkflow` - End-to-end bug management
- `TestTaskWorkflowIntegration` - Task management integration
- `TestConcurrentOperations` - Concurrent access scenarios
- `TestErrorRecoveryWorkflows` - Error recovery and resilience

### 4. Jira Integration Tests (`test_jira_integration.py`)

**Purpose:** Test Jira integration architecture and mapping
**Duration:** ~3-5 seconds  
**Coverage:**
- Jira configuration and validation
- Task-to-Jira field mapping
- Priority and status mapping
- Integration service functionality
- Sync strategy validation
- Custom field mappings

**Key Test Classes:**
- `TestJiraConfiguration` - Configuration validation
- `TestJiraTaskMapping` - Mapping relationships
- `TestTaskToJiraMapper` - Field mapping logic
- `TestJiraIntegrationService` - Main service functionality
- `TestJiraFieldMappings` - Custom field scenarios

### 5. Performance Tests (`test_performance.py`)

**Purpose:** Validate performance with large datasets and concurrent operations
**Duration:** ~30-60 seconds (can be skipped)
**Coverage:**
- Large dataset handling (1000+ tasks)
- Concurrent task creation and updates
- Complex query performance
- Memory usage validation
- Filter performance with large datasets

**Key Test Classes:**
- `TestLargeDatasetPerformance` - 1000+ task scenarios
- `TestConcurrentOperationPerformance` - Concurrent access
- `TestComplexQueryPerformance` - Complex analytics queries
- `TestMemoryUsagePerformance` - Memory efficiency validation

**Performance Benchmarks:**
- List 1000 tasks: < 5 seconds
- Filtered searches: < 2 seconds
- Bug statistics: < 3 seconds
- Concurrent operations: 80%+ success rate
- Memory growth: < 500MB for large datasets

### 6. End-to-End Tests (`test_end_to_end_workflows.py`)

**Purpose:** Test complete user journeys and real-world scenarios
**Duration:** ~15-30 seconds
**Coverage:**
- Complete bug discovery to resolution workflow
- Feature development with testing lifecycle
- Sprint planning and execution scenarios
- Project management workflows
- Error recovery scenarios

**Key Test Classes:**
- `TestBugLifecycleWorkflow` - Complete bug management journey
- `TestFeatureDevelopmentWorkflow` - Feature development lifecycle
- `TestProjectManagementWorkflow` - Sprint and project management
- `TestErrorRecoveryWorkflows` - Real-world error scenarios

## Testing Best Practices

### For Development

1. **Always run quick tests before committing:**
   ```bash
   python run_all_tests.py --quick
   ```

2. **Run full test suite for major changes:**
   ```bash
   python run_all_tests.py
   ```

3. **Test specific areas when making focused changes:**
   ```bash
   python run_all_tests.py --test mcp  # For MCP tool changes
   python run_all_tests.py --test integration  # For workflow changes
   ```

### For CI/CD

1. **Use quick tests for fast feedback:**
   ```bash
   python run_all_tests.py --quick
   ```

2. **Run full tests on main branch:**
   ```bash
   python run_all_tests.py --skip-performance
   ```

3. **Run performance tests nightly:**
   ```bash
   python run_all_tests.py --test performance
   ```

### For Manual Testing

1. **Test new MCP tools:**
   ```bash
   python test_mcp_tools.py
   ```

2. **Validate workflows:**
   ```bash
   python test_integration_workflows.py
   ```

3. **Check performance:**
   ```bash
   python test_performance.py
   ```

## Test Data and Fixtures

### Test Project Structure
Tests create temporary directories with realistic task data:
- JSON-based task storage
- Sample bugs with various severities
- Tasks with dependencies and subtasks
- Test coverage data and metrics

### Mock Data Patterns
- **Small datasets:** 3-10 tasks for functionality testing
- **Medium datasets:** 50-100 tasks for integration testing  
- **Large datasets:** 1000+ tasks for performance testing
- **Complex relationships:** Dependencies, subtasks, test coverage

## Interpreting Test Results

### Success Indicators
- ✅ All test suites pass
- Performance metrics within benchmarks
- 100% success rate on basic functionality
- 80%+ success rate on concurrent operations

### Common Issues and Solutions

**Import Errors:**
```
ImportError: No module named 'shared.models'
```
*Solution:* Ensure you're running from the tests directory and the project is properly installed.

**File Permission Errors:**
```
PermissionError: [Errno 13] Permission denied
```
*Solution:* Check write permissions in test directory or run with appropriate permissions.

**Timeout Errors:**
```
asyncio.TimeoutError
```
*Solution:* Performance tests may need adjustment for slower systems. Consider using `--skip-performance`.

**Concurrent Access Failures:**
```
Failed to acquire lock
```
*Solution:* Normal for concurrent tests - acceptable if success rate > 80%.

## Adding New Tests

### Creating New Test Files

1. **Follow naming convention:** `test_<feature_name>.py`
2. **Include comprehensive docstrings**
3. **Use pytest fixtures for setup/teardown**
4. **Add to test runner in `run_all_tests.py`**

### Test Class Structure
```python
class TestNewFeature:
    """Test new feature functionality"""
    
    @pytest.fixture
    def test_setup(self):
        """Setup test environment"""
        # Create test data
        yield test_data
        # Cleanup
    
    def test_basic_functionality(self, test_setup):
        """Test basic feature operation"""
        # Test implementation
        assert result["success"] is True
    
    async def test_async_functionality(self, test_setup):
        """Test async feature operation"""
        # Async test implementation
        result = await async_function()
        assert result is not None
```

### Integration with Test Runner

Add new test suite to `run_all_tests.py`:
```python
test_suites.append({
    "name": "New Feature Tests",
    "func": run_new_feature_tests,
    "description": "Test new feature functionality"
})
```

## Continuous Integration Integration

### GitHub Actions Example
```yaml
- name: Run PyTaskAI Tests
  run: |
    cd tests
    python run_all_tests.py --skip-performance
```

### Pre-commit Hook
```bash
#!/bin/sh
cd tests && python run_all_tests.py --quick
```

## Troubleshooting

### Common Test Failures

1. **Async Event Loop Issues**
   - Ensure proper async/await usage
   - Use `asyncio.run()` for top-level calls

2. **File Lock Conflicts** 
   - Use temporary directories for isolation
   - Implement proper cleanup in fixtures

3. **Performance Test Timeouts**
   - Adjust timeout values for slower systems
   - Skip performance tests during development

### Debug Mode

Run tests with verbose output:
```bash
python -v run_all_tests.py --test mcp
```

Check specific test failures:
```bash
python test_mcp_tools.py
```

## Test Coverage

The testing framework covers:
- ✅ **MCP Tools:** 100% of exposed MCP functions
- ✅ **Core Models:** All Pydantic model validation
- ✅ **Workflows:** Complete user journeys  
- ✅ **Integration:** Cross-component functionality
- ✅ **Performance:** Large-scale operation validation
- ✅ **Error Handling:** Edge cases and error scenarios

## Future Enhancements

Planned testing improvements:
- [ ] UI component testing for Streamlit components
- [ ] Real Jira API integration testing (with mocks)
- [ ] Database performance testing
- [ ] Security testing for API endpoints
- [ ] Load testing for concurrent users

---

For questions or issues with testing, please refer to the test output or create an issue in the project repository.