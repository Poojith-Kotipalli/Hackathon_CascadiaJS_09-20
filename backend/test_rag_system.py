# backend/test_rag_system.py
import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.compliance_engine import ComplianceEngine

async def test_rag():
    engine = ComplianceEngine()
    
    test_cases = [
        "This supplement is FDA approved and cures diabetes!",
        "Beautiful handmade toy for babies",
        "Guaranteed weight loss - 30 pounds in 30 days or money back!",
        "High quality cotton t-shirt, made in USA"
    ]
    
    print("\n🧪 TESTING RAG-POWERED COMPLIANCE ENGINE")
    print("=" * 60)
    
    for text in test_cases:
        print(f"\n📝 Testing: '{text}'")
        print("-" * 40)
        
        try:
            result = await engine.check_compliance(text, "realtime")
            
            print(f"✅ Compliant: {result['compliant']}")
            print(f"📊 Score: {result['score']}/100")
            print(f"⚠️  Severity: {result['severity']}")
            
            if result['violations']:
                print(f"🚫 Violations:")
                for v in result['violations']:
                    print(f"   - {v}")
            
            if result['suggestions']:
                print(f"💡 Suggestions:")
                for s in result['suggestions']:
                    print(f"   - {s}")
            
            print(f"\n📚 Relevant Rules Used:")
            for rule in result['relevant_rules']:
                print(f"   [{rule['source']}] {rule['similarity']} - {rule['text_preview']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Verify environment is loaded
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env file!")
        print("   Make sure your .env file has: DATABASE_URL=postgresql://...")
    else:
        print(f"✅ Using database: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
        asyncio.run(test_rag())