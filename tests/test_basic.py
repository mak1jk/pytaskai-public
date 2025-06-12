"""
Basic tests for PyTaskAI functionality
"""


def test_imports():
    """Test that core modules can be imported"""
    try:
        from services.ai_service_facade import AIServiceFacade as AIService
        from shared.models import Task

        # If imports succeed the test passes
    except ImportError as e:
        assert False, f"Import failed: {e}"


def test_aiservice_creation():
    """Test AIService can be created"""
    try:
        from services.ai_service_facade import AIServiceFacade as AIService

        service = AIService()
        # Service instance should be truthy
        assert service
    except Exception as e:
        assert False, f"AIService creation failed: {e}"


if __name__ == "__main__":
    test_imports()
    test_aiservice_creation()
    print("✅ Basic tests passed")
