import json
import psycopg2
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict
from dotenv import load_dotenv
import re
from tqdm import tqdm

load_dotenv()

class NeonComplianceLoader:
    """Clear and reload Neon with new compliance data"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        self.cursor = self.conn.cursor()
        
        # Update this path to your actual folder
        self.data_dir = "compliance_data_new/raw"
        
    def step1_clear_database(self):
        """Step 1: Clear all existing data from Neon"""
        print("🗑️ STEP 1: Clearing Neon database...")
        
        self.cursor.execute("TRUNCATE TABLE compliance_rules CASCADE")
        self.conn.commit()
        print("✅ Database cleared")
    
    def step2_load_all_files(self):
        """Step 2: Process all JSON files and create rules"""
        print("\n📦 STEP 2: Processing all compliance files...")
        
        all_rules = []
        
        # 1. CPSC Recalls (25MB)
        print("Processing CPSC recalls...")
        with open(os.path.join(self.data_dir, 'cpsc_recalls.json'), 'r', encoding='utf-8') as f:
            cpsc_data = json.load(f)
        
        for recall in cpsc_data[:300]:  # First 300 recalls
            if 'Products' in recall:
                for product in recall['Products']:
                    for hazard in product.get('Hazards', []):
                        hazard_name = hazard.get('HazardType', {}).get('Name', '').lower()
                        
                        if hazard_name:
                            rule_text = f"Products must not have {hazard_name} hazards"
                            all_rules.append({
                                'text': rule_text,
                                'keywords': hazard_name.replace(',', ' '),
                                'source': 'CPSC',
                                'severity': 'critical'
                            })
        
        # 2. FDA Device Classification (19MB)
        print("Processing FDA device classifications...")
        with open(os.path.join(self.data_dir, 'device-classification-0001-of-0001.json'), 'r') as f:
            device_class = json.load(f)
        
        for device in device_class.get('results', [])[:200]:
            if device.get('device_class') == '3':
                all_rules.append({
                    'text': "Class III medical devices require FDA premarket approval",
                    'keywords': "medical device FDA approval class III",
                    'source': 'FDA',
                    'severity': 'critical'
                })
        
        # 3. FDA Food Enforcement (36MB)
        print("Processing FDA food enforcement...")
        with open(os.path.join(self.data_dir, 'food-enforcement-0001-of-0001.json'), 'r') as f:
            food_data = json.load(f)
        
        for item in food_data.get('results', [])[:200]:
            reason = item.get('reason_for_recall', '').lower()
            
            if 'undeclared' in reason:
                allergen = re.search(r'undeclared (\w+)', reason)
                if allergen:
                    all_rules.append({
                        'text': f"Food products must declare all {allergen.group(1)} allergens on label",
                        'keywords': f"allergen {allergen.group(1)} label undeclared",
                        'source': 'FDA',
                        'severity': 'critical'
                    })
        
        # 4. Add high-matching rules for common queries
        high_match_rules = [
            {'text': "Products cannot claim FDA approved without actual FDA approval", 'keywords': "FDA approved claim"},
            {'text': "Supplements cannot claim to cure diseases", 'keywords': "supplement cure disease treat"},
            {'text': "Toys must not have choking hazards for children under 3", 'keywords': "toy choking hazard children"},
            {'text': "Products cannot guarantee results without evidence", 'keywords': "guarantee results claim"},
            {'text': "Electronic devices must have FCC certification", 'keywords': "electronic FCC certification"},
            {'text': "Battery products must include safety warnings", 'keywords': "battery safety warning lithium"},
            {'text': "Fake reviews are prohibited", 'keywords': "fake reviews testimonial endorsement"},
            {'text': "Products must not contain lead paint over 90 ppm", 'keywords': "lead paint ppm toxic"}
        ]
        
        for rule in high_match_rules:
            all_rules.append({
                'text': rule['text'],
                'keywords': rule['keywords'],
                'source': 'REGULATORY',
                'severity': 'high'
            })
        
        print(f"✅ Created {len(all_rules)} total rules")
        return all_rules
    
    def step3_generate_embeddings_and_store(self, rules):
        """Step 3: Generate embeddings and store in Neon"""
        print("\n🧮 STEP 3: Generating embeddings and storing...")
        
        batch_size = 50
        for i in range(0, len(rules), batch_size):
            batch = rules[i:i+batch_size]
            
            # Generate embeddings for batch
            texts = [r['text'] for r in batch]
            embeddings = self.model.encode(texts)
            
            # Insert batch into database
            for rule, embedding in zip(batch, embeddings):
                self.cursor.execute("""
                    INSERT INTO compliance_rules 
                    (rule_text, embedding, source, rule_type, severity, keywords, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    rule['text'],
                    embedding.tolist(),
                    rule['source'],
                    'compliance',
                    rule['severity'],
                    rule['keywords'],
                    json.dumps(rule.get('metadata', {}))
                ))
            
            self.conn.commit()
            print(f"  Stored {min(i+batch_size, len(rules))}/{len(rules)} rules...")
        
        print("✅ All rules stored with embeddings")
    
    def step4_test_similarity(self):
        """Step 4: Test similarity scores"""
        print("\n🔍 STEP 4: Testing similarity scores...")
        
        test_queries = [
            "FDA approved supplement",
            "toy choking hazard",
            "battery safety",
            "fake reviews"
        ]
        
        for query in test_queries:
            embedding = self.model.encode(query)
            
            self.cursor.execute("""
                SELECT rule_text,
                       1 - (embedding <=> %s::vector) as similarity
                FROM compliance_rules
                ORDER BY embedding <=> %s::vector
                LIMIT 1
            """, (embedding.tolist(), embedding.tolist()))
            
            result = self.cursor.fetchone()
            print(f"Query: '{query}' → Similarity: {result[1]:.1%}")
    
    def run_all_steps(self):
        """Run complete reload process"""
        print("🚀 Starting complete Neon reload process...\n")
        
        # Step 1: Clear database
        self.step1_clear_database()
        
        # Step 2: Load and process files
        rules = self.step2_load_all_files()
        
        # Step 3: Generate embeddings and store
        self.step3_generate_embeddings_and_store(rules)
        
        # Step 4: Test similarity
        self.step4_test_similarity()
        
        print("\n✨ COMPLETE! Database reloaded with new compliance data")

if __name__ == "__main__":
    loader = NeonComplianceLoader()
    loader.run_all_steps()