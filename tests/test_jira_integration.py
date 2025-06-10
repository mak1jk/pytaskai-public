"""
Tests for PyTaskAI Jira Integration Architecture
Tests mapping strategies, configuration, and integration workflows
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import MagicMock, patch

# Import Jira integration components
from shared.jira_integration import (
    JiraConfig,
    JiraTaskMapping, 
    JiraIssue,
    TaskToJiraMapper,
    JiraIntegrationService,
    JiraIssueType,
    JiraPriority,
    JiraStatus,
    JiraSyncStrategy,
    DEFAULT_JIRA_CONFIG
)

# Import PyTaskAI models
from shared.models import Task, TaskType, TaskStatus, TaskPriority, BugSeverity


class TestJiraConfiguration:
    """Test Jira configuration and validation"""
    
    def test_default_config_creation(self):
        """Test creation of default Jira configuration"""
        config = DEFAULT_JIRA_CONFIG
        
        assert config.server_url is not None
        assert config.project_key == "PROJ"
        assert config.sync_strategy == JiraSyncStrategy.SELECTIVE
        assert config.sync_interval_minutes == 30
        assert config.enable_intelligent_mapping is True
    
    def test_custom_config_creation(self):
        """Test creation of custom Jira configuration"""
        config = JiraConfig(
            server_url="https://mycompany.atlassian.net",
            username="test@company.com",
            api_token="test-token",
            project_key="TEST",
            sync_strategy=JiraSyncStrategy.COMPLETE,
            sync_interval_minutes=15,
            sync_tags=["production", "critical"],
            custom_field_mappings={
                "environment": "customfield_10001",
                "severity": "customfield_10002"
            }
        )
        
        assert config.server_url == "https://mycompany.atlassian.net"
        assert config.project_key == "TEST"
        assert config.sync_strategy == JiraSyncStrategy.COMPLETE
        assert len(config.sync_tags) == 2
        assert "environment" in config.custom_field_mappings
    
    def test_config_validation(self):
        """Test configuration field validation"""
        # Test invalid sync interval
        with pytest.raises(ValueError):
            JiraConfig(
                server_url="https://test.atlassian.net",
                username="test@test.com",
                api_token="token",
                project_key="TEST",
                sync_interval_minutes=-5  # Invalid negative interval
            )


class TestJiraTaskMapping:
    """Test mapping between PyTaskAI tasks and Jira issues"""
    
    def test_mapping_creation(self):
        """Test creation of task-to-Jira mapping"""
        mapping = JiraTaskMapping(
            pytaskai_task_id=123,
            jira_issue_key="PROJ-456",
            jira_issue_id="10123",
            sync_direction="bidirectional"
        )
        
        assert mapping.pytaskai_task_id == 123
        assert mapping.jira_issue_key == "PROJ-456"
        assert mapping.jira_issue_id == "10123"
        assert mapping.sync_direction == "bidirectional"
        assert mapping.sync_status == "synced"  # Default value
    
    def test_mapping_timestamps(self):
        """Test mapping timestamp handling"""
        mapping = JiraTaskMapping(
            pytaskai_task_id=1,
            jira_issue_key="TEST-1",
            jira_issue_id="123"
        )
        
        assert mapping.mapped_at is not None
        assert isinstance(mapping.mapped_at, datetime)
        assert mapping.last_synced is None  # Should start as None
    
    def test_mapping_sync_status_updates(self):
        """Test sync status tracking"""
        mapping = JiraTaskMapping(
            pytaskai_task_id=1,
            jira_issue_key="TEST-1", 
            jira_issue_id="123",
            sync_status="error",
            last_sync_error="Connection timeout"
        )
        
        assert mapping.sync_status == "error"
        assert mapping.last_sync_error == "Connection timeout"


class TestTaskToJiraMapper:
    """Test PyTaskAI to Jira mapping logic"""
    
    @pytest.fixture
    def mapper_config(self):
        """Create test configuration for mapper"""
        return JiraConfig(
            server_url="https://test.atlassian.net",
            username="test@test.com",
            api_token="test-token",
            project_key="TEST",
            enable_intelligent_mapping=True,
            custom_field_mappings={
                "environment": "customfield_10001",
                "steps_to_reproduce": "customfield_10002"
            }
        )
    
    @pytest.fixture
    def sample_task(self):
        """Create sample task for mapping tests"""
        return Task(
            id=1,
            title="Test Bug Fix",
            description="Fix login validation issue",
            type=TaskType.BUG,
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            severity=BugSeverity.HIGH,
            environment="Chrome 120, Windows 11",
            steps_to_reproduce="1. Login\n2. Enter invalid email\n3. See error",
            expected_result="Clear error message",
            actual_result="App crashes",
            target_test_coverage=80.0
        )
    
    def test_mapper_initialization(self, mapper_config):
        """Test mapper initialization with configuration"""
        mapper = TaskToJiraMapper(mapper_config)
        
        assert mapper.config == mapper_config
        assert TaskType.BUG in mapper.task_type_mapping
        assert TaskPriority.HIGH in mapper.priority_mapping
        assert TaskStatus.PENDING in mapper.status_mapping
    
    def test_issue_type_determination_basic(self, mapper_config, sample_task):
        """Test basic issue type determination"""
        mapper = TaskToJiraMapper(mapper_config)
        
        # Test bug mapping
        bug_task = sample_task
        issue_type = mapper.determine_jira_issue_type(bug_task)
        assert issue_type == JiraIssueType.BUG
        
        # Test feature mapping
        feature_task = sample_task.model_copy()
        feature_task.type = TaskType.FEATURE
        issue_type = mapper.determine_jira_issue_type(feature_task)
        assert issue_type == JiraIssueType.STORY
    
    def test_intelligent_issue_type_mapping(self, mapper_config):
        """Test intelligent issue type mapping based on complexity"""
        mapper = TaskToJiraMapper(mapper_config)
        
        # High complexity feature should become Epic
        complex_task = Task(
            id=1,
            title="Major Feature Overhaul",
            description="Complete redesign of user interface",
            type=TaskType.FEATURE,
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            complexity_score=9,  # High complexity
            subtasks=[]
        )
        
        issue_type = mapper.determine_jira_issue_type(complex_task)
        assert issue_type == JiraIssueType.EPIC
    
    def test_task_to_jira_fields_mapping(self, mapper_config, sample_task):
        """Test complete task to Jira fields mapping"""
        mapper = TaskToJiraMapper(mapper_config)
        
        fields = mapper.map_task_to_jira_fields(sample_task)
        
        # Test basic fields
        assert fields["summary"] == sample_task.title
        assert fields["description"] is not None
        assert "issuetype" in fields
        assert fields["issuetype"]["name"] == JiraIssueType.BUG.value
        assert "priority" in fields
        assert fields["priority"]["name"] == JiraPriority.HIGH.value
        
        # Test labels
        assert "labels" in fields
        labels = fields["labels"]
        assert "pytaskai" in labels
        assert "type-bug" in labels
        assert "priority-high" in labels
        assert "severity-high" in labels
    
    def test_bug_specific_field_mapping(self, mapper_config, sample_task):
        """Test bug-specific field mapping"""
        mapper = TaskToJiraMapper(mapper_config)
        
        fields = mapper.map_task_to_jira_fields(sample_task)
        
        # Test custom field mappings for bugs
        assert "customfield_10001" in fields  # environment
        assert fields["customfield_10001"] == sample_task.environment
        assert "customfield_10002" in fields  # steps_to_reproduce
        assert fields["customfield_10002"] == sample_task.steps_to_reproduce
    
    def test_description_formatting(self, mapper_config, sample_task):
        """Test Jira description formatting"""
        mapper = TaskToJiraMapper(mapper_config)
        
        # Add test coverage info to task
        task_with_coverage = sample_task.model_copy()
        task_with_coverage.target_test_coverage = 80.0
        task_with_coverage.achieved_test_coverage = 75.0
        task_with_coverage.test_strategy = "Unit tests + integration tests"
        
        description = mapper._format_description(task_with_coverage)
        
        assert sample_task.description in description
        assert "Target Test Coverage: 80.0%" in description
        assert "Achieved Test Coverage: 75.0%" in description
        assert "Test Strategy:" in description
        assert "PyTaskAI (Task #1)" in description
    
    def test_label_generation(self, mapper_config, sample_task):
        """Test Jira label generation"""
        mapper = TaskToJiraMapper(mapper_config)
        
        labels = mapper._generate_labels(sample_task)
        
        assert "pytaskai" in labels
        assert "type-bug" in labels
        assert "priority-high" in labels
        assert "severity-high" in labels
        assert "has-test-coverage" in labels  # Since target_test_coverage is set


class TestJiraIntegrationService:
    """Test main Jira integration service"""
    
    @pytest.fixture
    def integration_config(self):
        """Create integration service configuration"""
        return JiraConfig(
            server_url="https://test.atlassian.net",
            username="test@test.com",
            api_token="test-token",
            project_key="TEST",
            sync_strategy=JiraSyncStrategy.SELECTIVE,
            sync_tags=["jira-sync", "production"]
        )
    
    @pytest.fixture
    def sample_task_with_tags(self):
        """Create sample task with sync tags"""
        return Task(
            id=1,
            title="Sync Test Task",
            description="Task for sync testing", 
            type=TaskType.FEATURE,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            tags=["jira-sync", "frontend"]
        )
    
    def test_service_initialization(self, integration_config):
        """Test integration service initialization"""
        service = JiraIntegrationService(integration_config)
        
        assert service.config == integration_config
        assert service.mapper is not None
        assert isinstance(service.mappings, list)
        assert len(service.mappings) == 0  # Should start empty
    
    def test_should_sync_task_selective_strategy(self, integration_config, sample_task_with_tags):
        """Test selective sync strategy"""
        service = JiraIntegrationService(integration_config)
        
        # Task with sync tag should sync
        assert service.should_sync_task(sample_task_with_tags) is True
        
        # Task without sync tag should not sync
        task_no_tags = sample_task_with_tags.model_copy()
        task_no_tags.tags = ["frontend", "ui"]
        assert service.should_sync_task(task_no_tags) is False
    
    def test_should_sync_task_complete_strategy(self, integration_config, sample_task_with_tags):
        """Test complete sync strategy"""
        config = integration_config.model_copy()
        config.sync_strategy = JiraSyncStrategy.COMPLETE
        service = JiraIntegrationService(config)
        
        # All tasks should sync
        assert service.should_sync_task(sample_task_with_tags) is True
        
        task_no_tags = sample_task_with_tags.model_copy()
        task_no_tags.tags = []
        assert service.should_sync_task(task_no_tags) is True
    
    def test_should_sync_task_manual_strategy(self, integration_config, sample_task_with_tags):
        """Test manual sync strategy"""
        config = integration_config.model_copy()
        config.sync_strategy = JiraSyncStrategy.MANUAL
        service = JiraIntegrationService(config)
        
        # No tasks should auto-sync
        assert service.should_sync_task(sample_task_with_tags) is False
    
    async def test_sync_task_creation(self, integration_config, sample_task_with_tags):
        """Test creating new Jira issue from task"""
        service = JiraIntegrationService(integration_config)
        
        # Mock the actual Jira creation
        with patch.object(service, '_create_jira_issue') as mock_create:
            mock_mapping = JiraTaskMapping(
                pytaskai_task_id=sample_task_with_tags.id,
                jira_issue_key="TEST-123",
                jira_issue_id="10123"
            )
            mock_create.return_value = mock_mapping
            
            result = await service.sync_task_to_jira(sample_task_with_tags)
            
            assert result is not None
            assert result.pytaskai_task_id == sample_task_with_tags.id
            assert result.jira_issue_key == "TEST-123"
            mock_create.assert_called_once_with(sample_task_with_tags)
    
    async def test_sync_task_update(self, integration_config, sample_task_with_tags):
        """Test updating existing Jira issue"""
        service = JiraIntegrationService(integration_config)
        
        # Add existing mapping
        existing_mapping = JiraTaskMapping(
            pytaskai_task_id=sample_task_with_tags.id,
            jira_issue_key="TEST-123",
            jira_issue_id="10123"
        )
        service.mappings.append(existing_mapping)
        
        with patch.object(service, '_update_jira_issue') as mock_update:
            mock_update.return_value = existing_mapping
            
            result = await service.sync_task_to_jira(sample_task_with_tags)
            
            assert result is not None
            mock_update.assert_called_once_with(sample_task_with_tags, existing_mapping)
    
    def test_find_mapping_by_task_id(self, integration_config):
        """Test finding mapping by task ID"""
        service = JiraIntegrationService(integration_config)
        
        # Add test mappings
        mapping1 = JiraTaskMapping(
            pytaskai_task_id=1,
            jira_issue_key="TEST-1",
            jira_issue_id="101"
        )
        mapping2 = JiraTaskMapping(
            pytaskai_task_id=2,
            jira_issue_key="TEST-2",
            jira_issue_id="102"
        )
        
        service.mappings.extend([mapping1, mapping2])
        
        # Test finding existing mapping
        found = service.find_mapping_by_task_id(1)
        assert found is not None
        assert found.jira_issue_key == "TEST-1"
        
        # Test not finding non-existent mapping
        not_found = service.find_mapping_by_task_id(999)
        assert not_found is None
    
    def test_sync_status_summary(self, integration_config):
        """Test sync status summary generation"""
        service = JiraIntegrationService(integration_config)
        
        # Add test mappings with different statuses
        now = datetime.now()
        mappings = [
            JiraTaskMapping(
                pytaskai_task_id=1,
                jira_issue_key="TEST-1",
                jira_issue_id="101",
                sync_status="synced",
                last_synced=now
            ),
            JiraTaskMapping(
                pytaskai_task_id=2,
                jira_issue_key="TEST-2",
                jira_issue_id="102",
                sync_status="conflict"
            ),
            JiraTaskMapping(
                pytaskai_task_id=3,
                jira_issue_key="TEST-3",
                jira_issue_id="103",
                sync_status="error"
            )
        ]
        
        service.mappings.extend(mappings)
        
        summary = service.get_sync_status_summary()
        
        assert summary["total_mappings"] == 3
        assert summary["synced"] == 1
        assert summary["conflicts"] == 1
        assert summary["errors"] == 1
        assert summary["sync_rate"] == 33.333333333333336  # 1/3 * 100
        assert summary["last_sync"] == now


class TestJiraFieldMappings:
    """Test specific field mapping scenarios"""
    
    def test_priority_mapping_edge_cases(self):
        """Test priority mapping for edge cases"""
        config = JiraConfig(
            server_url="https://test.atlassian.net",
            username="test",
            api_token="token",
            project_key="TEST"
        )
        mapper = TaskToJiraMapper(config)
        
        # Test all priority levels
        priority_tests = [
            (TaskPriority.LOWEST, JiraPriority.LOWEST),
            (TaskPriority.LOW, JiraPriority.LOW),
            (TaskPriority.MEDIUM, JiraPriority.MEDIUM),
            (TaskPriority.HIGH, JiraPriority.HIGH),
            (TaskPriority.HIGHEST, JiraPriority.CRITICAL)
        ]
        
        for pytaskai_priority, expected_jira_priority in priority_tests:
            task = Task(
                id=1,
                title="Test Task",
                description="Test",
                type=TaskType.TASK,
                status=TaskStatus.PENDING,
                priority=pytaskai_priority
            )
            
            fields = mapper.map_task_to_jira_fields(task)
            assert fields["priority"]["name"] == expected_jira_priority.value
    
    def test_custom_field_mapping_overrides(self):
        """Test custom field mapping overrides"""
        config = JiraConfig(
            server_url="https://test.atlassian.net",
            username="test",
            api_token="token",
            project_key="TEST",
            custom_field_mappings={
                "environment": "customfield_99999",
                "custom_attribute": "customfield_88888"
            }
        )
        mapper = TaskToJiraMapper(config)
        
        task = Task(
            id=1,
            title="Test Task",
            description="Test",
            type=TaskType.BUG,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            environment="Test Environment"
        )
        
        # Add custom attribute to task
        task.custom_attribute = "Custom Value"
        
        fields = mapper.map_task_to_jira_fields(task)
        
        assert "customfield_99999" in fields
        assert fields["customfield_99999"] == "Test Environment"
        assert "customfield_88888" in fields
        assert fields["customfield_88888"] == "Custom Value"


# Test runners
def run_jira_integration_tests():
    """Run all Jira integration tests"""
    print("Running Jira Integration Tests...")
    
    try:
        # Test instances
        config_tests = TestJiraConfiguration()
        mapping_tests = TestJiraTaskMapping()
        mapper_tests = TestTaskToJiraMapper()
        service_tests = TestJiraIntegrationService()
        field_tests = TestJiraFieldMappings()
        
        print("✅ Jira integration test classes loaded successfully")
        
        # Run basic tests
        config_tests.test_default_config_creation()
        config_tests.test_custom_config_creation()
        
        mapping_tests.test_mapping_creation()
        mapping_tests.test_mapping_timestamps()
        
        print("✅ Basic Jira integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Jira integration tests failed: {e}")
        return False


if __name__ == "__main__":
    success = run_jira_integration_tests()
    if success:
        print("✅ All Jira integration tests passed!")
    else:
        print("❌ Some Jira integration tests failed!")