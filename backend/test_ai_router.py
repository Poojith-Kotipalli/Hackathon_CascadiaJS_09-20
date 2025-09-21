# backend/test_structured_response.py
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

from app.services.ai_router import AIRouter
import logging

logging.basicConfig(level=logging.INFO)

async def test_structured():
    router = AIRouter()
    
    prompt = """
    Analyze this product listing for compliance:
    "This amazing weight loss pill guarantees you'll lose 30 pounds in 30 days or your money back! 
    100% natural and FDA approved for rapid fat burning."
    """
    
    print("\n🧪 Testing Structured Response")
    print("="*50)
    
    # Test with Ollama
    print("\n📍 Ollama (Local):")
    result = await router.get_structured_response(prompt, "realtime")
    if result['parsed']:
        print("✅ Successfully parsed JSON:")
        print(json.dumps(result['parsed'], indent=2))
    else:
        print("❌ Failed to parse, raw response:")
        print(result['response'][:300])
    
    # Test with Gemini
    print("\n📍 Gemini (Cloud):")
    result = await router.get_structured_response(prompt, "ai-powered")
    if result['parsed']:
        print("✅ Successfully parsed JSON:")
        print(json.dumps(result['parsed'], indent=2))
    else:
        print("❌ Failed to parse, raw response:")
        print(result['response'][:300])

if __name__ == "__main__":
    import json
    asyncio.run(test_structured())