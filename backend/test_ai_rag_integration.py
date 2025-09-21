# backend/test_ai_rag_integration.py
import asyncio
import json
import os
import sys
from dotenv import load_dotenv
import time

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.compliance_engine import ComplianceEngine
from app.services.ai_router import AIRouter
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

async def test_ai_rag_integration():
    """Test if both Ollama and Gemini can properly use RAG context"""
    
    print("\n" + "="*70)
    print("🧪 TESTING AI MODELS WITH RAG INTEGRATION")
    print("="*70)
    
    engine = ComplianceEngine()
    ai_router = AIRouter()
    
    # Test scenarios specifically designed to require RAG context
    test_scenarios = [
        {
            "text": "This toy contains small magnets perfect for kids under 3",
            "expected_issue": "choking hazard",
            "description": "Should detect CPSC magnet/choking hazard rules"
        },
        {
            "text": "Our supplement is FDA approved to cure arthritis pain",
            "expected_issue": "FDA medical claims",
            "description": "Should detect FDA health claim violations"
        },
        {
            "text": "100% guaranteed results or triple your money back",
            "expected_issue": "FTC deceptive advertising",
            "description": "Should detect FTC guarantee violations"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*70}")
        print(f"📋 Test: {scenario['description']}")
        print(f"📝 Input: \"{scenario['text']}\"")
        print(f"🎯 Expected to find: {scenario['expected_issue']}")
        print("-"*70)
        
        # First, show what RAG finds
        print("\n🔍 STEP 1: RAG RETRIEVAL")
        relevant_rules = await engine.search_compliance_rules(scenario['text'], limit=3)
        
        for i, rule in enumerate(relevant_rules, 1):
            print(f"\n  Rule {i} [{rule['source']}] - Similarity: {rule['similarity']:.2%}")
            print(f"  Preview: {rule['rule_text'][:150]}...")
        
        # Build context
        context = "\n\n".join([
            f"[{rule['source']} - {rule['severity'].upper()}]: {rule['rule_text']}"
            for rule in relevant_rules[:3]
        ])
        
        # Test with OLLAMA
        print("\n\n🤖 STEP 2A: TESTING OLLAMA (Local)")
        print("-"*40)
        
        ollama_prompt = f"""You are a compliance expert. Based on the following regulations, analyze this product listing.

REGULATIONS:
{context}

PRODUCT LISTING:
"{scenario['text']}"

Respond with ONLY valid JSON:
{{
    "uses_context": true/false (did you use the provided regulations?),
    "relevant_rule_cited": "which regulation from context was most relevant",
    "compliant": true/false,
    "main_violation": "primary violation found",
    "confidence": 0.0-1.0
}}"""
        
        try:
            start = time.time()
            ollama_result = await ai_router.route("realtime", ollama_prompt)
            latency = (time.time() - start) * 1000
            
            print(f"⏱️  Latency: {latency:.0f}ms")
            
            # Try to parse response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', ollama_result['response'], re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    print(f"✅ Uses Context: {parsed.get('uses_context', False)}")
                    print(f"📌 Cited Rule: {parsed.get('relevant_rule_cited', 'None')[:100]}")
                    print(f"⚖️  Compliant: {parsed.get('compliant', 'Unknown')}")
                    print(f"🚫 Main Violation: {parsed.get('main_violation', 'None')}")
                    print(f"📊 Confidence: {parsed.get('confidence', 0):.2f}")
                else:
                    print("⚠️  Could not parse JSON, raw response:")
                    print(ollama_result['response'][:300])
            except Exception as e:
                print(f"⚠️  Parse error: {e}")
                print(f"Raw: {ollama_result['response'][:300]}")
                
        except Exception as e:
            print(f"❌ Ollama error: {e}")
        
        # Test with GEMINI
        print("\n🌐 STEP 2B: TESTING GEMINI (Cloud)")
        print("-"*40)
        
        try:
            start = time.time()
            gemini_result = await ai_router.route("ai-powered", ollama_prompt)
            latency = (time.time() - start) * 1000
            
            print(f"⏱️  Latency: {latency:.0f}ms")
            
            # Try to parse response
            try:
                json_match = re.search(r'\{.*\}', gemini_result['response'], re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    print(f"✅ Uses Context: {parsed.get('uses_context', False)}")
                    print(f"📌 Cited Rule: {parsed.get('relevant_rule_cited', 'None')[:100]}")
                    print(f"⚖️  Compliant: {parsed.get('compliant', 'Unknown')}")
                    print(f"🚫 Main Violation: {parsed.get('main_violation', 'None')}")
                    print(f"📊 Confidence: {parsed.get('confidence', 0):.2f}")
                else:
                    print("⚠️  Could not parse JSON, raw response:")
                    print(gemini_result['response'][:300])
            except Exception as e:
                print(f"⚠️  Parse error: {e}")
                print(f"Raw: {gemini_result['response'][:300]}")
                
        except Exception as e:
            print(f"❌ Gemini error: {e}")
        
        # Test the full compliance engine (uses structured response)
        print("\n🔧 STEP 3: FULL COMPLIANCE ENGINE TEST")
        print("-"*40)
        
        try:
            # Test with realtime (Ollama)
            result_ollama = await engine.check_compliance(scenario['text'], "realtime")
            print(f"Ollama Result: Compliant={result_ollama['compliant']}, Score={result_ollama['score']}")
            
            # Test with ai-powered (Gemini)
            result_gemini = await engine.check_compliance(scenario['text'], "ai-powered")
            print(f"Gemini Result: Compliant={result_gemini['compliant']}, Score={result_gemini['score']}")
            
        except Exception as e:
            print(f"❌ Compliance engine error: {e}")
    
    # Summary test
    print("\n" + "="*70)
    print("📊 SUMMARY: Direct Context Test")
    print("="*70)
    
    # Test if models can answer questions about the regulations themselves
    context_test_prompt = """Based on these regulations:
    
[CPSC] Toys with small parts are choking hazards for children under 3
[FDA] Products cannot claim to cure diseases without FDA approval
[FTC] Guarantees must be truthful and substantiated

What are the three regulatory agencies mentioned and their main concerns?
Answer in one sentence."""
    
    print("\n🤖 Ollama understanding of regulations:")
    ollama_test = await ai_router.route("realtime", context_test_prompt)
    print(ollama_test['response'][:200])
    
    print("\n🌐 Gemini understanding of regulations:")
    gemini_test = await ai_router.route("ai-powered", context_test_prompt)
    print(gemini_test['response'][:200])

if __name__ == "__main__":
    asyncio.run(test_ai_rag_integration())