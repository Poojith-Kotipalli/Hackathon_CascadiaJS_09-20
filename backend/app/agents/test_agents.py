"""
Test script to verify the multi-agent system is working
"""

import sys
import os
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agents.orchestrator import ComplianceOrchestrator
import json
from datetime import datetime

def test_compliance_system():
    """Test the multi-agent system with sample products"""
    
    # Initialize the orchestrator
    orchestrator = ComplianceOrchestrator()
    
    # Test products that will trigger different agents
    test_products = [
        {
            "id": 1,
            "name": "Magic Growing Dinosaurs - Kids Bath Toy",
            "description": "Colorful foam dinosaurs that expand 600% in water. Small parts included. Perfect for ages 2+",
            "category": "toys",
            "age_range": "2+",
            "materials": "Polyurethane foam with painted surface",
            "warnings": "Contains small parts",
            "price": 12.99
        },
        {
            "id": 2,
            "name": "Ultra Burn Fat Destroyer Supreme",
            "description": "Lose 30 pounds in 30 days guaranteed! Boosts metabolism 500% naturally. Burns fat while you sleep.",
            "category": "supplements",
            "ingredients": "Proprietary blend including green tea extract, garcinia cambogia, secret formula",
            "price": 89.99
        },
        {
            "id": 3,
            "name": "Grandma's Homemade Peanut-Free Cookies",
            "description": "Traditional recipe cookies, absolutely no peanuts, completely allergen-free and safe for everyone",
            "category": "food",
            "ingredients": "Wheat flour, butter, eggs, sugar, vanilla, almond extract, cashew pieces",
            "price": 8.99
        },
        {
            "id": 4,
            "name": "Wireless Fast Charging Pad 50W",
            "description": "Ultra-fast wireless charging for all phones. No certifications needed - it just works!",
            "category": "electronics",
            "warnings": "May get warm during use",
            "price": 29.99
        }
    ]
    
    # Test each product
    for product in test_products:
        print(f"\n{'='*80}")
        print(f"Testing Product: {product['name']}")
        print(f"Category: {product['category']}")
        print('='*80)
        
        try:
            # Run compliance check
            result = orchestrator.check_product_compliance(product)
            
            # Display results
            print(f"\n📊 COMPLIANCE RESULTS:")
            print(f"├─ Final Verdict: {result.get('final_verdict')} ", end="")
            
            # Add emoji based on verdict
            if result.get('final_verdict') == 'REJECTED':
                print("❌")
            elif result.get('final_verdict') == 'CONDITIONAL':
                print("⚠️")
            else:
                print("✅")
            
            print(f"├─ Compliance Score: {result.get('overall_score')}/100")
            print(f"├─ Risk Level: {result.get('risk_level')}")
            print(f"├─ Total Violations: {result.get('total_violations')}")
            print(f"├─ Critical Violations: {len(result.get('critical_violations', []))}")
            print(f"├─ Processing Time: {result.get('processing_time_ms'):.0f}ms")
            print(f"└─ Agents Consulted: {', '.join(result.get('agents_consulted', []))}")
            
            # Show critical violations if any
            if result.get('critical_violations'):
                print(f"\n🚨 CRITICAL VIOLATIONS:")
                for i, violation in enumerate(result['critical_violations'][:3], 1):
                    print(f"  {i}. {violation}")
            
            # Show required actions
            if result.get('required_actions'):
                print(f"\n📋 REQUIRED ACTIONS:")
                for i, action in enumerate(result['required_actions'][:3], 1):
                    print(f"  {i}. {action}")
            
            # Show agent reasoning chain
            print(f"\n🤖 AGENT REASONING CHAIN:")
            for msg in result.get('agent_reasoning_chain', []):
                print(f"  [{msg['agent']}]: {msg['message']}")
            
        except Exception as e:
            print(f"❌ Error testing product: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Show token usage
    print(f"\n{'='*80}")
    print("💰 TOKEN USAGE SUMMARY:")
    usage = orchestrator.get_token_usage()
    print(f"├─ Total Tokens Used: {usage['total_tokens']:,}")
    print(f"├─ Total Checks: {usage['total_checks']}")
    print(f"└─ Estimated Cost: ${usage['estimated_cost']:.4f}")
    
    print(f"\n✅ Testing complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🚀 Starting ComplianceMonster Multi-Agent System Test...")
    print("📝 Using gpt-4o-mini model for all agents")
    test_compliance_system()