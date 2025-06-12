"""
Basic tests for PyTaskAI functionality
"""


def test_imports():
    """Test that core modules can be imported"""
    try:
        from mcp_server.ai_service import AIService
        from shared.models import Task

        assert True, "Core imports successful"
    except ImportError as e:
        assert False, f"Import failed: {e}"


def test_aiservice_creation():
    """Test AIService can be created"""
    try:
        from mcp_server.ai_service import AIService

        service = AIService()
        assert service is not None, "AIService created successfully"
    except Exception as e:
        assert False, f"AIService creation failed: {e}"


if __name__ == "__main__":
    test_imports()
    test_aiservice_creation()
    print("✅ Basic tests passed")
