#!/usr/bin/env python3
"""
Simple integration test for LLM Provider Factory

This script tests the LLM factory with real API keys if available.
Safe to run - uses minimal tokens.
"""

import asyncio
import os
from services.llm import get_llm_provider, ModelRole

async def test_llm_integration():
    """Test LLM integration with minimal API calls"""
    
    print("🧪 Testing LLM Provider Factory Integration")
    print("=" * 50)
    
    # Test cases with minimal token usage
    test_cases = [
        {
            "prompt": "Hello",
            "role": ModelRole.DEFAULT,
            "description": "Simple greeting test"
        },
        {
            "prompt": "What is 2+2?",
            "role": ModelRole.TASK_GENERATION,
            "description": "Basic math test"
        }
    ]
    
    total_cost = 0.0
    successful_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        
        try:
            response = await get_llm_provider(
                prompt=test_case["prompt"],
                role=test_case["role"],
                max_tokens=20  # Keep token usage minimal
            )
            
            print(f"✅ Provider: {response.provider.value}")
            print(f"🤖 Model: {response.model}")
            print(f"💬 Response: {response.content[:100]}...")
            print(f"🪙 Tokens: {response.tokens_used}")
            print(f"💰 Cost: ${response.cost:.6f}")
            print(f"⏱️ Latency: {response.latency_ms}ms")
            
            total_cost += response.cost
            successful_tests += 1
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print(f"🔍 This might be due to missing API keys or network issues")
    
    print(f"\n📊 Test Summary")
    print(f"✅ Successful tests: {successful_tests}/{len(test_cases)}")
    print(f"💰 Total cost: ${total_cost:.6f}")
    
    if successful_tests > 0:
        print("🎉 LLM Provider Factory is working!")
    else:
        print("⚠️ No tests passed - check API keys and network connection")
    
    # Test factory health status
    try:
        from services.llm.factory import get_factory
        factory = await get_factory()
        
        print(f"\n🏥 Health Status:")
        health_summary = factory.get_health_summary()
        for provider, status in health_summary.items():
            health_emoji = "✅" if status["is_healthy"] else "❌"
            print(f"{health_emoji} {provider}: {'Healthy' if status['is_healthy'] else 'Unhealthy'}")
        
        print(f"\n💰 Cost Summary:")
        cost_summary = factory.get_cost_summary()
        for provider_model, cost in cost_summary.items():
            print(f"💸 {provider_model}: ${cost:.6f}")
            
    except Exception as e:
        print(f"⚠️ Could not get factory status: {e}")

if __name__ == "__main__":
    print("🚀 Starting LLM Provider Factory Integration Test")
    print("📋 This test requires API keys to be set in environment variables")
    print("🔐 Supported: OPENAI_API_KEY, ANTHROPIC_API_KEY, PERPLEXITY_API_KEY")
    print("")
    
    # Check for available API keys
    available_keys = []
    if os.getenv("OPENAI_API_KEY"):
        available_keys.append("OpenAI")
    if os.getenv("ANTHROPIC_API_KEY"):
        available_keys.append("Anthropic")
    if os.getenv("PERPLEXITY_API_KEY"):
        available_keys.append("Perplexity")
    
    if available_keys:
        print(f"🔑 Found API keys for: {', '.join(available_keys)}")
    else:
        print("⚠️ No API keys found - tests will show initialization behavior only")
    
    print("")
    
    try:
        asyncio.run(test_llm_integration())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()