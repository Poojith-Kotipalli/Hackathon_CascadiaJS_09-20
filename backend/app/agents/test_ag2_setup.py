# test_ag2_setup.py
import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def test_basic_openai():
    """Test 1: Basic OpenAI connection"""
    print("=" * 50)
    print("TEST 1: Basic OpenAI Connection")
    print("=" * 50)
    
    try:
        import openai
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Simple test
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'OpenAI connected'"}],
            max_tokens=10
        )
        
        print(f"✅ OpenAI Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return False

def test_autogen_setup():
    """Test 2: AutoGen basic setup"""
    print("\n" + "=" * 50)
    print("TEST 2: AutoGen Setup")
    print("=" * 50)
    
    try:
        import autogen
        
        config_list = [{
            "model": "gpt-4o-mini",
            "api_key": os.getenv('OPENAI_API_KEY'),
        }]
        
        # Create a simple agent
        assistant = autogen.AssistantAgent(
            name="TestAgent",
            llm_config={"config_list": config_list}
        )
        
        print("✅ AutoGen agent created successfully")
        return True
        
    except Exception as e:
        print(f"❌ AutoGen Error: {e}")
        return False

def test_compliance_agents():
    """Test 3: Your ComplianceAgentSystem"""
    print("\n" + "=" * 50)
    print("TEST 3: Compliance Agent System")
    print("=" * 50)
    
    try:
        from agents.compliance_agents import ComplianceAgents
        
        # Initialize
        print("Initializing ComplianceAgentSystem...")
        agent_system = ComplianceAgents()
        
        print("✅ System initialized")
        print(f"Agents created: {[agent.name for agent in agent_system.agents if hasattr(agent_system, 'agents')]}")
        
        return True
        
    except Exception as e:
        print(f"❌ ComplianceAgentSystem Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_full_compliance_check():
    """Test 4: Full compliance check on a product"""
    print("\n" + "=" * 50)
    print("TEST 4: Full Product Compliance Check")
    print("=" * 50)
    
    try:
        from agents.compliance_agents import ComplianceAgentSystem
        
        # Test product that should trigger violations
        test_product = {
            "name": "Super Kids Paint Set",
            "description": "Bright colorful paints for children ages 2+. Contains lead-based pigments for extra brightness!",
            "category": "toys",
            "price": 19.99,
            "claims": ["Non-toxic", "Safe for toddlers"],
            "ingredients": "Lead-based pigments, mercury compounds"
        }
        
        print(f"Testing product: {test_product['name']}")
        print("This should trigger CPSC violations...")
        
        # Initialize and run
        agent_system = ComplianceAgentSystem(
            openai_key=os.getenv('OPENAI_API_KEY')
        )
        
        start_time = datetime.now()
        result = agent_system.check_product_compliance(test_product)
        end_time = datetime.now()
        
        print(f"\n✅ Compliance check completed in {(end_time - start_time).total_seconds():.2f} seconds")
        print("\nResults:")
        print(f"  - Status: {result.get('status', 'Unknown')}")
        print(f"  - Risk Level: {result.get('risk_level', 'Unknown')}")
        print(f"  - Agents Consulted: {result.get('agents_consulted', [])}")
        print(f"  - Violations Found: {len(result.get('violations', []))}")
        
        if result.get('violations'):
            print("\nViolations Detected:")
            for v in result['violations'][:3]:  # Show first 3
                print(f"  - {v}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full Check Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n🚀 TESTING AG2 SETUP FOR COMPLIANCEMONSTER")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return
    else:
        print(f"✅ API Key found: {api_key[:8]}...")
    
    # Run tests
    tests = [
        test_basic_openai,
        test_autogen_setup,
        test_compliance_agents,
        test_full_compliance_check
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"Test failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\nAG2 is working! Ready to proceed with next steps.")
    else:
        print(f"⚠️ {passed}/{total} tests passed")
        print("\nFix the errors above before proceeding.")

if __name__ == "__main__":
    main()