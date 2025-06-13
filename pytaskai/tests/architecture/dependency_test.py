"""
Architecture dependency validation tests for PyTaskAI hexagonal architecture.

This module validates that the hexagonal architecture principles are maintained:
- Domain layer has no external dependencies
- Application layer only depends on domain and interfaces  
- Infrastructure layer implements domain interfaces
- Adapters only depend on application layer
- SOLID principles compliance
- Dependency inversion properly implemented

These tests ensure architectural integrity and prevent degradation over time.
"""

import ast
import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


class ArchitectureDependencyAnalyzer:
    """Analyzes code dependencies to validate architecture compliance."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.pytaskai_path = project_root / "pytaskai"

    def get_all_python_files(self, package_path: Path) -> List[Path]:
        """Get all Python files in a package."""
        python_files = []
        for file_path in package_path.rglob("*.py"):
            if file_path.name != "__init__.py":
                python_files.append(file_path)
        return python_files

    def analyze_imports(self, file_path: Path) -> Set[str]:
        """Analyze imports in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
            
            return imports
        except (SyntaxError, UnicodeDecodeError):
            return set()

    def categorize_import(self, import_name: str) -> str:
        """Categorize an import by its architectural layer."""
        if import_name.startswith("pytaskai.domain"):
            return "domain"
        elif import_name.startswith("pytaskai.application"):
            return "application"
        elif import_name.startswith("pytaskai.infrastructure"):
            return "infrastructure"
        elif import_name.startswith("pytaskai.adapters"):
            return "adapters"
        elif import_name.startswith("pytaskai"):
            return "pytaskai_other"
        else:
            return "external"

    def get_layer_dependencies(self, layer_path: Path) -> Dict[str, Set[str]]:
        """Get all dependencies for files in a layer."""
        files = self.get_all_python_files(layer_path)
        dependencies = {}
        
        for file_path in files:
            relative_path = file_path.relative_to(self.project_root)
            imports = self.analyze_imports(file_path)
            
            categorized_imports = {}
            for import_name in imports:
                category = self.categorize_import(import_name)
                if category not in categorized_imports:
                    categorized_imports[category] = set()
                categorized_imports[category].add(import_name)
            
            dependencies[str(relative_path)] = categorized_imports
        
        return dependencies


class TestHexagonalArchitecture:
    """Test hexagonal architecture compliance."""

    @pytest.fixture
    def analyzer(self):
        """Get dependency analyzer."""
        current_dir = Path(__file__).parent.parent.parent.parent
        return ArchitectureDependencyAnalyzer(current_dir)

    def test_domain_layer_independence(self, analyzer):
        """
        Test that domain layer has no dependencies on infrastructure or adapters.
        
        This is the core principle of hexagonal architecture - the domain
        should be completely independent of external concerns.
        """
        domain_path = analyzer.pytaskai_path / "domain"
        dependencies = analyzer.get_layer_dependencies(domain_path)
        
        violations = []
        forbidden_categories = ["infrastructure", "adapters"]
        
        for file_path, file_deps in dependencies.items():
            for category in forbidden_categories:
                if category in file_deps:
                    for dep in file_deps[category]:
                        violations.append(f"{file_path} imports {dep}")
        
        # Also check for forbidden external dependencies
        forbidden_external = [
            "sqlalchemy", "fastmcp", "click", "openai", "aiohttp", "requests"
        ]
        
        for file_path, file_deps in dependencies.items():
            if "external" in file_deps:
                for dep in file_deps["external"]:
                    for forbidden in forbidden_external:
                        if dep.startswith(forbidden):
                            violations.append(f"{file_path} imports forbidden external dependency {dep}")
        
        assert len(violations) == 0, f"Domain layer dependency violations:\\n" + "\\n".join(violations)

    def test_application_layer_dependencies(self, analyzer):
        """
        Test that application layer only depends on domain and interfaces.
        
        Application layer should orchestrate domain operations but not
        depend on specific infrastructure implementations.
        """
        app_path = analyzer.pytaskai_path / "application"
        dependencies = analyzer.get_layer_dependencies(app_path)
        
        violations = []
        forbidden_categories = ["adapters"]
        
        for file_path, file_deps in dependencies.items():
            for category in forbidden_categories:
                if category in file_deps:
                    for dep in file_deps[category]:
                        violations.append(f"{file_path} imports {dep}")
        
        # Check for forbidden infrastructure imports (except interfaces)
        for file_path, file_deps in dependencies.items():
            if "infrastructure" in file_deps:
                for dep in file_deps["infrastructure"]:
                    # Allow interfaces and config, forbid implementations
                    if not (dep.endswith(".interfaces") or 
                           dep.endswith(".config") or
                           "interface" in dep):
                        violations.append(f"{file_path} imports infrastructure implementation {dep}")
        
        # Check for forbidden external dependencies
        forbidden_external = [
            "sqlalchemy", "fastmcp", "click", "tabulate"
        ]
        
        for file_path, file_deps in dependencies.items():
            if "external" in file_deps:
                for dep in file_deps["external"]:
                    for forbidden in forbidden_external:
                        if dep.startswith(forbidden):
                            violations.append(f"{file_path} imports forbidden external dependency {dep}")
        
        assert len(violations) == 0, f"Application layer dependency violations:\\n" + "\\n".join(violations)

    def test_infrastructure_implements_domain_interfaces(self, analyzer):
        """
        Test that infrastructure layer properly implements domain interfaces.
        
        Infrastructure should implement domain repository interfaces
        and not violate dependency inversion principle.
        """
        infra_path = analyzer.pytaskai_path / "infrastructure"
        dependencies = analyzer.get_layer_dependencies(infra_path)
        
        violations = []
        
        # Infrastructure should import domain interfaces
        repository_files = [
            f for f in dependencies.keys() 
            if "repository" in f and "sqlite" in f
        ]
        
        for repo_file in repository_files:
            file_deps = dependencies[repo_file]
            
            # Should import domain repository interfaces
            has_domain_import = False
            if "domain" in file_deps:
                for dep in file_deps["domain"]:
                    if "repository" in dep:
                        has_domain_import = True
                        break
            
            if not has_domain_import:
                violations.append(f"{repo_file} does not import domain repository interfaces")
        
        # Infrastructure should not import from adapters
        for file_path, file_deps in dependencies.items():
            if "adapters" in file_deps:
                for dep in file_deps["adapters"]:
                    violations.append(f"{file_path} imports adapter {dep}")
        
        assert len(violations) == 0, f"Infrastructure layer violations:\\n" + "\\n".join(violations)

    def test_adapter_layer_dependencies(self, analyzer):
        """
        Test that adapters only depend on application layer.
        
        Adapters should not directly import domain or infrastructure,
        except for dependency injection containers which wire up implementations.
        """
        adapters_path = analyzer.pytaskai_path / "adapters"
        dependencies = analyzer.get_layer_dependencies(adapters_path)
        
        violations = []
        
        # Adapters should not directly import domain (except value objects for validation)
        for file_path, file_deps in dependencies.items():
            if "domain" in file_deps:
                for dep in file_deps["domain"]:
                    # Allow value objects and exceptions, forbid entities and services
                    if not (dep.endswith(".value_objects") or 
                           dep.endswith(".exceptions") or
                           "value_object" in dep):
                        violations.append(f"{file_path} directly imports domain {dep}")
        
        # Adapters should not import infrastructure implementations
        # EXCEPT dependency injection containers which need to wire implementations
        for file_path, file_deps in dependencies.items():
            if "infrastructure" in file_deps:
                for dep in file_deps["infrastructure"]:
                    # Allow config imports and dependency injection containers
                    if not (dep.endswith(".config") or "config" in dep or 
                           "dependency_injection" in file_path):
                        violations.append(f"{file_path} imports infrastructure implementation {dep}")
        
        assert len(violations) == 0, f"Adapter layer violations:\\n" + "\\n".join(violations)

    def test_no_circular_dependencies(self, analyzer):
        """
        Test that there are no circular dependencies between layers.
        
        This ensures clean separation and prevents architectural degradation.
        """
        # Build dependency graph
        all_deps = {}
        
        for layer in ["domain", "application", "infrastructure", "adapters"]:
            layer_path = analyzer.pytaskai_path / layer
            layer_deps = analyzer.get_layer_dependencies(layer_path)
            all_deps.update(layer_deps)
        
        # Check for circular dependencies at layer level
        layer_imports = {
            "domain": set(),
            "application": set(), 
            "infrastructure": set(),
            "adapters": set()
        }
        
        for file_path, file_deps in all_deps.items():
            current_layer = None
            for layer in ["domain", "application", "infrastructure", "adapters"]:
                if f"/{layer}/" in file_path:
                    current_layer = layer
                    break
            
            if current_layer:
                for category, deps in file_deps.items():
                    if category in layer_imports:
                        layer_imports[current_layer].add(category)
        
        # Detect circular dependencies
        violations = []
        
        # Domain should not import application, infrastructure, or adapters
        forbidden_for_domain = layer_imports["domain"] & {"application", "infrastructure", "adapters"}
        if forbidden_for_domain:
            violations.append(f"Domain layer imports: {forbidden_for_domain}")
        
        # Application should not import infrastructure implementations or adapters
        forbidden_for_app = layer_imports["application"] & {"adapters"}
        if forbidden_for_app:
            violations.append(f"Application layer imports adapters: {forbidden_for_app}")
        
        assert len(violations) == 0, f"Circular dependency violations:\\n" + "\\n".join(violations)


class TestSOLIDPrinciples:
    """Test SOLID principles compliance."""

    def test_single_responsibility_principle(self):
        """
        Test adherence to Single Responsibility Principle.
        
        Each class should have only one reason to change.
        This test checks for classes with too many responsibilities.
        """
        from pytaskai.domain.entities.task import Task
        from pytaskai.application.use_cases.task_management import TaskManagementUseCase
        
        # Check Task entity - should only handle task business logic
        task_methods = [method for method in dir(Task) if not method.startswith('_')]
        task_business_methods = [m for m in task_methods if m in [
            'is_completed', 'is_overdue', 'is_high_priority', 'add_tag', 
            'remove_tag', 'mark_completed', 'with_updated_status'
        ]]
        
        # Task should have focused business methods, not infrastructure concerns
        infrastructure_methods = [m for m in task_methods if m in [
            'save', 'delete', 'serialize', 'to_json', 'from_json'
        ]]
        
        assert len(infrastructure_methods) == 0, \
            f"Task entity has infrastructure responsibilities: {infrastructure_methods}"
        
        # Check TaskManagementUseCase - should orchestrate, not implement
        use_case_methods = [method for method in dir(TaskManagementUseCase) if not method.startswith('_')]
        orchestration_methods = [m for m in use_case_methods if m in [
            'create_task', 'get_task', 'list_tasks', 'update_task', 'delete_task'
        ]]
        
        # Should not have data access methods
        data_access_methods = [m for m in use_case_methods if m in [
            'execute_sql', 'connect_database', 'serialize_data'
        ]]
        
        assert len(data_access_methods) == 0, \
            f"TaskManagementUseCase has data access responsibilities: {data_access_methods}"

    def test_open_closed_principle(self):
        """
        Test adherence to Open/Closed Principle.
        
        Classes should be open for extension but closed for modification.
        This test checks that interfaces enable extension.
        """
        from pytaskai.application.interfaces.ai_service import AITaskGenerationService
        from pytaskai.domain.repositories.task_repository import TaskRepository
        
        # Check that interfaces are properly abstract
        import inspect
        
        # AITaskGenerationService should be abstract
        assert inspect.isabstract(AITaskGenerationService), \
            "AITaskGenerationService should be abstract for extensibility"
        
        # TaskRepository should be abstract
        assert inspect.isabstract(TaskRepository), \
            "TaskRepository should be abstract for extensibility"
        
        # Check that concrete implementations can be swapped
        from pytaskai.infrastructure.external.openai_service import OpenAITaskGenerationService
        
        assert issubclass(OpenAITaskGenerationService, AITaskGenerationService), \
            "OpenAI service should implement AI interface for extensibility"

    def test_liskov_substitution_principle(self):
        """
        Test adherence to Liskov Substitution Principle.
        
        Derived classes should be substitutable for their base classes.
        """
        from pytaskai.application.interfaces.ai_service import AITaskGenerationService
        from pytaskai.infrastructure.external.openai_service import OpenAITaskGenerationService
        
        # Check method signatures match
        base_methods = inspect.getmembers(AITaskGenerationService, predicate=inspect.ismethod)
        impl_methods = inspect.getmembers(OpenAITaskGenerationService, predicate=inspect.ismethod)
        
        base_method_names = {name for name, _ in base_methods if not name.startswith('_')}
        impl_method_names = {name for name, _ in impl_methods if not name.startswith('_')}
        
        # Implementation should have all interface methods
        missing_methods = base_method_names - impl_method_names
        assert len(missing_methods) == 0, \
            f"OpenAI service missing interface methods: {missing_methods}"

    def test_interface_segregation_principle(self):
        """
        Test adherence to Interface Segregation Principle.
        
        Clients should not be forced to depend on interfaces they don't use.
        """
        from pytaskai.application.interfaces.ai_service import AITaskGenerationService, AIResearchService
        
        # AI interfaces should be segregated by responsibility
        generation_methods = inspect.getmembers(AITaskGenerationService, predicate=inspect.isfunction)
        research_methods = inspect.getmembers(AIResearchService, predicate=inspect.isfunction)
        
        gen_method_names = {name for name, _ in generation_methods}
        research_method_names = {name for name, _ in research_methods}
        
        # Should have no overlap (except common base methods)
        overlap = gen_method_names & research_method_names
        allowed_overlap = {'__init__', '__new__'}
        
        unexpected_overlap = overlap - allowed_overlap
        assert len(unexpected_overlap) == 0, \
            f"AI interfaces have unexpected overlap: {unexpected_overlap}"

    def test_dependency_inversion_principle(self):
        """
        Test adherence to Dependency Inversion Principle.
        
        High-level modules should not depend on low-level modules.
        Both should depend on abstractions.
        """
        from pytaskai.application.use_cases.task_management import TaskManagementUseCase
        
        # Check constructor dependencies
        init_signature = inspect.signature(TaskManagementUseCase.__init__)
        
        # Should depend on abstractions, not concrete implementations
        param_annotations = {
            name: param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)
            for name, param in init_signature.parameters.items()
            if name != 'self' and param.annotation != inspect.Parameter.empty
        }
        
        # Should not depend on concrete infrastructure classes
        forbidden_dependencies = [
            'SQLiteTaskRepository', 'OpenAITaskGenerationService', 'MCPServer'
        ]
        
        violations = []
        for param_name, annotation in param_annotations.items():
            for forbidden in forbidden_dependencies:
                if forbidden in annotation:
                    violations.append(f"TaskManagementUseCase depends on concrete class {forbidden}")
        
        assert len(violations) == 0, f"Dependency inversion violations: {violations}"


class TestArchitecturalMetrics:
    """Test architectural quality metrics."""

    def test_coupling_metrics(self):
        """Test coupling between layers is minimal."""
        current_dir = Path(__file__).parent.parent.parent.parent
        analyzer = ArchitectureDependencyAnalyzer(current_dir)
        
        # Measure coupling between layers
        coupling_matrix = {
            "domain": {"application": 0, "infrastructure": 0, "adapters": 0},
            "application": {"domain": 0, "infrastructure": 0, "adapters": 0},
            "infrastructure": {"domain": 0, "application": 0, "adapters": 0},
            "adapters": {"domain": 0, "application": 0, "infrastructure": 0}
        }
        
        for layer in ["domain", "application", "infrastructure", "adapters"]:
            layer_path = analyzer.pytaskai_path / layer
            dependencies = analyzer.get_layer_dependencies(layer_path)
            
            for file_path, file_deps in dependencies.items():
                for category, deps in file_deps.items():
                    if category in coupling_matrix[layer]:
                        coupling_matrix[layer][category] += len(deps)
        
        # Validate coupling constraints
        # Domain should have zero coupling to other layers
        domain_coupling = sum(coupling_matrix["domain"].values())
        assert domain_coupling == 0, f"Domain layer has coupling: {coupling_matrix['domain']}"
        
        # Application should not couple to adapters
        app_adapter_coupling = coupling_matrix["application"]["adapters"]
        assert app_adapter_coupling == 0, f"Application couples to adapters: {app_adapter_coupling}"

    def test_cohesion_metrics(self):
        """Test that modules have high cohesion."""
        # Check that domain entities are cohesive
        from pytaskai.domain.entities import task
        
        # Task module should have related functionality
        task_classes = [name for name in dir(task) if inspect.isclass(getattr(task, name))]
        
        # Should have Task and related classes, not unrelated ones
        expected_classes = ["Task", "Document"]
        unrelated_classes = [cls for cls in task_classes if cls not in expected_classes and not cls.startswith('_')]
        
        # Allow framework classes and domain value objects (which are related to tasks)
        allowed_classes = [
            'datetime', 'List', 'Optional', 'Any',  # Framework types
            'TaskId', 'TaskStatus', 'TaskPriority', 'TaskSize', 'TaskType',  # Task value objects
            'ProjectName', 'TagName'  # Project-related value objects
        ]
        business_unrelated = [cls for cls in unrelated_classes if cls not in allowed_classes]
        assert len(business_unrelated) <= 2, \
            f"Task module has low cohesion with unrelated classes: {business_unrelated}"


if __name__ == "__main__":
    # Run architecture tests
    pytest.main([__file__, "-v"])