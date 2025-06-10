#!/usr/bin/env python3
"""
Debug script to test async functionality directly
"""
import asyncio
import sys
import os
sys.path.append('/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public')

from mcp_server.ai_service import AIService

async def test_ai_service():
    try:
        ai_service = AIService(project_root="/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public")
        
        result = await ai_service.generate_task_with_ai(
            user_prompt="Test task creation",
            use_research=False,
            use_lts_deps=True,
            priority="medium"
        )
        
        print("SUCCESS:", result)
        return True
        
    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test if we can run async directly
    try:
        result = asyncio.run(test_ai_service())
        print(f"Direct async test result: {result}")
    except Exception as e:
        print(f"Direct async test failed: {e}")
        import traceback
        traceback.print_exc()