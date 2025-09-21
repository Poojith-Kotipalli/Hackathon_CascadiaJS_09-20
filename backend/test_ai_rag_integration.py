# backend/test_multi_table_compliance.py
import asyncio
import json
import os
import sys
from dotenv import load_dotenv
import time
import asyncpg
from sentence_transformers import SentenceTransformer
import re

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_router import AIRouter
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

class MultiTableComplianceTester:
    def __init__(self):
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        self.ai_router = AIRouter()
        
    def format_embedding(self, text):
        """Convert text to pgvector-compatible embedding string"""
        embedding_list = model.encode(text[:1000]).tolist()
        return '[' + ','.join(map(str, embedding_list)) + ']'
    
    async def search_table(self, conn, table_name, query_text, limit=3):
        """Search a specific table for relevant regulations"""
        try:
            embedding = self.format_embedding(query_text)
            
            # Build query based on table structure
            if table_name == 'cpsc_recalls':
                query = '''
                    SELECT rule_text, 
                           1 - (embedding <=> $1::vector) as similarity,
                           severity,
                           hazard_type as type_info
                    FROM cpsc_recalls
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                '''
            elif table_name in ['fda_drug_enforcement', 'fda_food_enforcement']:
                query = '''
                    SELECT rule_text, 
                           1 - (embedding <=> $1::vector) as similarity,
                           severity,
                           violation_type as type_info
                    FROM ''' + table_name + '''
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                '''
            elif table_name == 'fda_device_data':
                query = '''
                    SELECT rule_text, 
                           1 - (embedding <=> $1::vector) as similarity,
                           severity,
                           device_category as type_info
                    FROM fda_device_data
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                '''
            elif table_name == 'fda_drug_labels':
                query = '''
                    SELECT rule_text, 
                           1 - (embedding <=> $1::vector) as similarity,
                           severity,
                           brand_name as type_info
                    FROM fda_drug_labels
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                '''
            elif table_name == 'electronics_compliance':
                query = '''
                    SELECT rule_text, 
                           1 - (embedding <=> $1::vector) as similarity,
                           severity,
                           hazard_type as type_info
                    FROM electronics_compliance
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                '''
            else:
                # Default query without type_info
                query = '''
                    SELECT rule_text, 
                           1 - (embedding <=> $1::vector) as similarity,
                           severity,
                           '' as type_info
                    FROM ''' + table_name + '''
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                '''
            
            results = await conn.fetch(query, embedding, limit)
            
            return [
                {
                    'rule_text': r['rule_text'],
                    'similarity': float(r['similarity']),
                    'severity': r['severity'],
                    'type_info': r['type_info'] or ''
                }
                for r in results
            ]
        except Exception as e:
            print(f"Error searching {table_name}: {str(e)}")
            return []
    
    async def test_with_models(self, context, query_text, table_name):
        """Test both Ollama and Gemini with the given context"""
        
        prompt = f"""You are a compliance expert. Based on the following regulations from {table_name}, analyze this product listing.

REGULATIONS FROM {table_name}:
{context}

PRODUCT LISTING:
"{query_text}"

Respond with ONLY valid JSON:
{{
    "uses_context": true,
    "compliant": false,
    "main_violation": "describe the violation found",
    "confidence": 0.8,
    "severity": "high"
}}"""
        
        results = {}
        
        # Test OLLAMA
        print("\n  🤖 OLLAMA (Local):")
        try:
            start = time.time()
            ollama_result = await self.ai_router.route("realtime", prompt)
            latency = (time.time() - start) * 1000
            
            json_match = re.search(r'\{.*\}', ollama_result['response'], re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                print(f"    ⏱️ Latency: {latency:.0f}ms")
                print(f"    ⚖️ Compliant: {parsed.get('compliant', 'Unknown')}")
                print(f"    🚫 Violation: {parsed.get('main_violation', 'None')}")
                print(f"    📊 Confidence: {parsed.get('confidence', 0):.2f}")
                results['ollama'] = parsed
            else:
                print(f"    ⚠️ Could not parse JSON response")
                results['ollama'] = None
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:100]}")
            results['ollama'] = None
        
        # Test GEMINI
        print("\n  🌐 GEMINI (Cloud):")
        try:
            start = time.time()
            gemini_result = await self.ai_router.route("ai-powered", prompt)
            latency = (time.time() - start) * 1000
            
            json_match = re.search(r'\{.*\}', gemini_result['response'], re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                print(f"    ⏱️ Latency: {latency:.0f}ms")
                print(f"    ⚖️ Compliant: {parsed.get('compliant', 'Unknown')}")
                print(f"    🚫 Violation: {parsed.get('main_violation', 'None')}")
                print(f"    📊 Confidence: {parsed.get('confidence', 0):.2f}")
                results['gemini'] = parsed
            else:
                print(f"    ⚠️ Could not parse JSON response")
                results['gemini'] = None
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:100]}")
            results['gemini'] = None
        
        return results
    
    async def run_comprehensive_test(self):
        """Run tests on all tables with relevant queries"""
        
        # Define test cases for each table
        test_cases = {
            'cpsc_recalls': [
                {
                    'query': 'Magnetic building blocks for toddlers ages 2-4',
                    'expected': 'magnet/choking hazard',
                    'description': 'Testing CPSC toy safety violations'
                },
                {
                    'query': 'Battery-powered toy with small removable battery compartment',
                    'expected': 'button battery hazard',
                    'description': 'Testing CPSC battery safety'
                }
            ],
            'fda_drug_enforcement': [
                {
                    'query': 'FDA approved dietary supplement that cures diabetes',
                    'expected': 'false FDA approval claim',
                    'description': 'Testing FDA drug/supplement violations'
                },
                {
                    'query': 'Natural herbal remedy that prevents cancer',
                    'expected': 'disease prevention claim',
                    'description': 'Testing FDA health claims'
                }
            ],
            'fda_food_enforcement': [
                {
                    'query': 'Chocolate bars made in facility that processes peanuts',
                    'expected': 'allergen labeling',
                    'description': 'Testing FDA food allergen requirements'
                },
                {
                    'query': 'All natural energy drink with artificial flavors',
                    'expected': 'natural claim violation',
                    'description': 'Testing FDA labeling violations'
                }
            ],
            'fda_device_data': [
                {
                    'query': 'Bluetooth heart rate monitor for medical diagnosis',
                    'expected': 'medical device classification',
                    'description': 'Testing FDA device compliance'
                },
                {
                    'query': 'Software app that detects skin cancer from photos',
                    'expected': 'unclassified medical software',
                    'description': 'Testing FDA digital health'
                }
            ],
            'fda_drug_labels': [
                {
                    'query': 'Pain relief medication safe for pregnant women',
                    'expected': 'pregnancy warning requirements',
                    'description': 'Testing FDA drug label warnings'
                }
            ],
            'electronics_compliance': [
                {
                    'query': 'USB charger with exposed wiring sold online',
                    'expected': 'electrical hazard',
                    'description': 'Testing electronics safety standards'
                },
                {
                    'query': 'Lithium battery pack without safety certification',
                    'expected': 'battery safety violation',
                    'description': 'Testing battery compliance'
                }
            ]
        }
        
        print("\n" + "="*80)
        print("🧪 MULTI-TABLE COMPLIANCE TESTING SYSTEM")
        print("="*80)
        print("Testing all 6 compliance tables with both Ollama and Gemini")
        
        # Connect to database
        conn = await asyncpg.connect(self.DATABASE_URL)
        
        # Statistics tracking
        stats = {
            'total_tests': 0,
            'ollama_successes': 0,
            'gemini_successes': 0,
            'table_results': {}
        }
        
        try:
            # First, print database statistics
            print("\n📊 DATABASE STATISTICS:")
            for table_name in test_cases.keys():
                try:
                    count = await conn.fetchval(f'SELECT COUNT(*) FROM {table_name}')
                    print(f"  {table_name}: {count:,} records")
                except:
                    print(f"  {table_name}: Not found")
            
            # Test each table
            for table_name, test_scenarios in test_cases.items():
                print(f"\n{'='*80}")
                print(f"📊 TESTING TABLE: {table_name}")
                print(f"{'='*80}")
                
                # Check if table exists and has data
                try:
                    count = await conn.fetchval(f'SELECT COUNT(*) FROM {table_name}')
                    
                    if count == 0:
                        print(f"⚠️ Skipping {table_name} - no data loaded")
                        continue
                        
                except Exception as e:
                    print(f"❌ Table {table_name} error: {str(e)[:50]}")
                    continue
                
                table_stats = {'tests': 0, 'ollama_correct': 0, 'gemini_correct': 0}
                
                # Run each test scenario
                for scenario in test_scenarios:
                    stats['total_tests'] += 1
                    table_stats['tests'] += 1
                    
                    print(f"\n{'-'*70}")
                    print(f"📋 Test: {scenario['description']}")
                    print(f"🔍 Query: \"{scenario['query']}\"")
                    print(f"🎯 Expected: {scenario['expected']}")
                    
                    # Search the specific table
                    print(f"\n📚 RAG Retrieval from {table_name}:")
                    results = await self.search_table(conn, table_name, scenario['query'], limit=3)
                    
                    if not results:
                        print("  ⚠️ No results found")
                        continue
                    
                    # Display top results
                    for i, result in enumerate(results, 1):
                        print(f"\n  Result {i} - Similarity: {result['similarity']:.2%}")
                        print(f"  Type: {result.get('type_info', 'N/A')}")
                        print(f"  Severity: {result['severity']}")
                        print(f"  Preview: {result['rule_text'][:150]}...")
                    
                    # Build context for AI models
                    context = "\n\n".join([
                        f"[Rule {i+1} - {r['severity'].upper()}]: {r['rule_text']}"
                        for i, r in enumerate(results[:3])
                    ])
                    
                    # Test with both models
                    model_results = await self.test_with_models(
                        context, 
                        scenario['query'],
                        table_name
                    )
                    
                    # Track success
                    if model_results.get('ollama') and not model_results['ollama'].get('compliant', True):
                        stats['ollama_successes'] += 1
                        table_stats['ollama_correct'] += 1
                    
                    if model_results.get('gemini') and not model_results['gemini'].get('compliant', True):
                        stats['gemini_successes'] += 1
                        table_stats['gemini_correct'] += 1
                
                # Store table statistics
                stats['table_results'][table_name] = table_stats
                
                # Print table summary
                if table_stats['tests'] > 0:
                    print(f"\n📈 {table_name} Summary:")
                    print(f"  Ollama: {table_stats['ollama_correct']}/{table_stats['tests']} violations detected")
                    print(f"  Gemini: {table_stats['gemini_correct']}/{table_stats['tests']} violations detected")
        
        finally:
            await conn.close()
        
        # Print final summary
        print("\n" + "="*80)
        print("📊 FINAL TEST SUMMARY")
        print("="*80)
        
        if stats['total_tests'] > 0:
            print(f"\n🔢 Total Tests Run: {stats['total_tests']}")
            print(f"🤖 Ollama: {stats['ollama_successes']}/{stats['total_tests']} violations detected")
            print(f"🌐 Gemini: {stats['gemini_successes']}/{stats['total_tests']} violations detected")

async def main():
    tester = MultiTableComplianceTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())