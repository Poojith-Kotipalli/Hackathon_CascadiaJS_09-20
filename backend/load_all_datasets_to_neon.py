import json
import asyncio
import asyncpg
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

class ComprehensiveDataLoader:
    def __init__(self):
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        self.stats = {}
    
    def format_embedding(self, text):
        """Convert text to pgvector-compatible embedding string"""
        embedding_list = model.encode(text[:1000]).tolist()
        return '[' + ','.join(map(str, embedding_list)) + ']'
    
    def truncate(self, text, length):
        """Safely truncate text to specified length"""
        if text is None:
            return ''
        return str(text)[:length]
        
    async def load_cpsc_recalls(self, conn, filepath='compliance_data_new/raw/cpsc_recalls.json'):
        """Load CPSC recalls - handles toys, electronics, furniture, etc."""
        print("\n📦 Loading CPSC Product Recalls...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        recalls = data if isinstance(data, list) else data.get('results', [])
        loaded_general = 0
        loaded_electronics = 0
        errors = 0
        
        for recall in recalls[:3000]:
            if isinstance(recall, dict):
                title = recall.get('Title', '')
                desc = recall.get('Description', '')
                text = f"{title}. {desc}"
                
                # Extract hazards and products
                hazards = [h.get('Name', '') for h in recall.get('Hazards', []) if isinstance(h, dict)]
                products = [p.get('Name', '') for p in recall.get('Products', []) if isinstance(p, dict)]
                
                # Determine category
                product_text = ' '.join(products).lower()
                is_electronic = any(term in product_text for term in 
                    ['battery', 'charger', 'electronic', 'computer', 'phone', 'power', 'electrical', 'cord'])
                
                embedding = self.format_embedding(text)
                
                # Get manufacturer name safely
                manufacturer = 'Unknown'
                if recall.get('Manufacturers'):
                    manuf_list = recall.get('Manufacturers', [])
                    if manuf_list and isinstance(manuf_list[0], dict):
                        manufacturer = manuf_list[0].get('Name', 'Unknown')
                
                try:
                    # Insert into main CPSC table with truncated fields
                    await conn.execute('''
                        INSERT INTO cpsc_recalls 
                        (rule_text, embedding, hazard_type, product_category, product_name, 
                         manufacturer, severity, keywords, metadata)
                        VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8, $9)
                    ''',
                        self.truncate(text, 1500),
                        embedding,
                        self.truncate(hazards[0] if hazards else 'Unknown', 100),  # Truncate to 100
                        self.truncate('electronics' if is_electronic else 'consumer_product', 100),  # Truncate to 100
                        self.truncate(', '.join(products[:3]), 500),  # TEXT field, can be longer
                        self.truncate(manufacturer, 200),  # Truncate to 200
                        'critical' if any(h in str(hazards) for h in ['Death', 'Fire']) else 'high',
                        self.truncate(', '.join(hazards + products[:2]), 500),
                        json.dumps({'recall_id': recall.get('RecallID')})
                    )
                    loaded_general += 1
                    
                    # Also add to electronics table if applicable
                    if is_electronic:
                        hazard = 'fire' if 'fire' in str(hazards).lower() else 'electrical'
                        await conn.execute('''
                            INSERT INTO electronics_compliance
                            (rule_text, embedding, product_type, hazard_type, standard_violated, 
                             source, severity, keywords, metadata)
                            VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8, $9)
                        ''',
                            self.truncate(text, 1500),
                            embedding,
                            self.truncate('electronic_device', 100),  # Truncate to 100
                            self.truncate(hazard, 100),  # Truncate to 100
                            self.truncate('CPSC Safety Standard', 100),  # Truncate to 100
                            'CPSC',
                            'high',
                            self.truncate(', '.join(hazards), 500),
                            json.dumps({'recall_id': recall.get('RecallID')})
                        )
                        loaded_electronics += 1
                        
                except Exception as e:
                    errors += 1
                    if errors <= 5:  # Only show first 5 errors
                        print(f"    Error: {str(e)[:100]}")
                    continue
        
        print(f"  ✅ Loaded {loaded_general} general recalls")
        print(f"  ✅ Loaded {loaded_electronics} electronics recalls")
        if errors > 0:
            print(f"  ⚠️ {errors} records skipped due to errors")
        self.stats['cpsc'] = loaded_general
        self.stats['electronics'] = loaded_electronics
    
    async def load_fda_drug_enforcement(self, conn, filepath='compliance_data_new/raw/drug-enforcement-0001-of-0001.json'):
        """Load FDA drug enforcement data"""
        print("\n💊 Loading FDA Drug Enforcement...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            loaded = 0
            errors = 0
            
            for item in results[:2000]:  # Load 2000 drug enforcements
                if isinstance(item, dict):
                    text = f"FDA Drug Recall: {item.get('product_description', '')}. Reason: {item.get('reason_for_recall', '')}. Classification: {item.get('classification', '')}"
                    embedding = self.format_embedding(text)
                    
                    try:
                        await conn.execute('''
                            INSERT INTO fda_drug_enforcement
                            (rule_text, embedding, violation_type, product_type, product_description, 
                             reason_for_recall, classification, severity, keywords, metadata)
                            VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8, $9, $10)
                        ''',
                            self.truncate(text, 1500),
                            embedding,
                            self.truncate('recall' if 'recall' in item.get('status', '').lower() else 'violation', 100),
                            self.truncate('drug' if 'drug' in text.lower() else 'supplement', 50),
                            self.truncate(item.get('product_description', ''), 500),
                            self.truncate(item.get('reason_for_recall', ''), 500),  # TEXT field
                            self.truncate(item.get('classification', ''), 20),
                            'critical' if 'Class I' in item.get('classification', '') else 'high',
                            self.truncate(item.get('reason_for_recall', ''), 500),
                            json.dumps({'recall_number': item.get('recall_number')})
                        )
                        loaded += 1
                    except Exception as e:
                        errors += 1
                        if errors <= 5:
                            print(f"    Error: {str(e)[:100]}")
                        continue
                    
            print(f"  ✅ Loaded {loaded} drug enforcements")
            if errors > 0:
                print(f"  ⚠️ {errors} records skipped due to errors")
            self.stats['drug_enforcement'] = loaded
            
        except Exception as e:
            print(f"  ⚠️ Error loading drug enforcements: {str(e)[:100]}")
    
    async def load_fda_food_enforcement(self, conn, filepath='compliance_data_new/raw/food-enforcement-0001-of-0001.json'):
        """Load FDA food enforcement data"""
        print("\n🍔 Loading FDA Food Enforcement...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            loaded = 0
            errors = 0
            
            for item in results[:2000]:  # Load 2000 food enforcements
                if isinstance(item, dict):
                    reason = item.get('reason_for_recall', '')
                    text = f"FDA Food Recall: {item.get('product_description', '')}. Reason: {reason}"
                    
                    # Check for allergens
                    allergens = []
                    for allergen in ['milk', 'egg', 'peanut', 'wheat', 'soy', 'fish', 'shellfish', 'tree nut', 'sesame']:
                        if allergen in reason.lower():
                            allergens.append(allergen)
                    
                    embedding = self.format_embedding(text)
                    
                    try:
                        await conn.execute('''
                            INSERT INTO fda_food_enforcement
                            (rule_text, embedding, violation_type, allergen_info, product_description, 
                             distribution_pattern, severity, keywords, metadata)
                            VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8, $9)
                        ''',
                            self.truncate(text, 1500),
                            embedding,
                            self.truncate('allergen' if allergens else 'contamination' if 'contamin' in reason.lower() else 'other', 100),
                            self.truncate(', '.join(allergens) if allergens else '', 200),
                            self.truncate(item.get('product_description', ''), 500),
                            self.truncate(item.get('distribution_pattern', ''), 200),
                            'critical' if allergens or 'Class I' in item.get('classification', '') else 'high',
                            self.truncate(reason, 500),
                            json.dumps({'recall_number': item.get('recall_number')})
                        )
                        loaded += 1
                    except Exception as e:
                        errors += 1
                        if errors <= 5:
                            print(f"    Error: {str(e)[:100]}")
                        continue
                    
            print(f"  ✅ Loaded {loaded} food enforcements")
            if errors > 0:
                print(f"  ⚠️ {errors} records skipped due to errors")
            self.stats['food_enforcement'] = loaded
            
        except Exception as e:
            print(f"  ⚠️ Error loading food enforcements: {str(e)[:100]}")
    
    async def load_fda_device_data(self, conn, 
                                   recall_file='compliance_data_new/raw/device-recall-0001-of-0001.json',
                                   class_file='compliance_data_new/raw/device-classification-0001-of-0001.json'):
        """Load FDA device recalls and classifications"""
        print("\n🏥 Loading FDA Device Data...")
        
        loaded_recalls = 0
        loaded_class = 0
        loaded_electronics = 0
        errors = 0
        
        # Load device recalls
        try:
            with open(recall_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            
            for item in results[:1500]:  # Limit due to file size
                if isinstance(item, dict):
                    text = f"Medical Device Recall: {item.get('product_description', '')}. Reason: {item.get('reason_for_recall', '')}"
                    embedding = self.format_embedding(text)
                    
                    # Determine if it's also electronic
                    is_electronic = any(term in text.lower() for term in 
                        ['electronic', 'software', 'digital', 'monitor', 'sensor'])
                    
                    try:
                        await conn.execute('''
                            INSERT INTO fda_device_data
                            (rule_text, embedding, record_type, device_class, device_name, 
                             device_category, recall_reason, severity, keywords, metadata)
                            VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8, $9, $10)
                        ''',
                            self.truncate(text, 1500),
                            embedding,
                            'recall',
                            self.truncate(item.get('product_class', 'Unknown'), 10),
                            self.truncate(item.get('product_description', ''), 200),
                            self.truncate('medical_device', 100),
                            self.truncate(item.get('reason_for_recall', ''), 500),  # TEXT field
                            'high',
                            self.truncate(item.get('reason_for_recall', ''), 500),
                            json.dumps({'recall_number': item.get('recall_number')})
                        )
                        loaded_recalls += 1
                        
                        # Add to electronics if applicable
                        if is_electronic:
                            await conn.execute('''
                                INSERT INTO electronics_compliance
                                (rule_text, embedding, product_type, hazard_type, 
                                 standard_violated, source, severity, keywords, metadata)
                                VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8, $9)
                            ''',
                                self.truncate(text, 1500),
                                embedding,
                                self.truncate('medical_electronic', 100),
                                self.truncate('malfunction', 100),
                                self.truncate('FDA Medical Device Standard', 100),
                                'FDA',
                                'high',
                                self.truncate('medical device, electronic', 500),
                                json.dumps({})
                            )
                            loaded_electronics += 1
                    except Exception as e:
                        errors += 1
                        if errors <= 5:
                            print(f"    Error: {str(e)[:100]}")
                        continue
                        
        except Exception as e:
            print(f"  ⚠️ Error loading device recalls: {str(e)[:100]}")
        
        # Load device classifications
        try:
            with open(class_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            
            for item in results[:1000]:
                if isinstance(item, dict):
                    text = f"Device Classification: {item.get('device_name', '')}. Class {item.get('device_class', '')}. {item.get('definition', '')}"
                    embedding = self.format_embedding(text)
                    
                    try:
                        await conn.execute('''
                            INSERT INTO fda_device_data
                            (rule_text, embedding, record_type, device_class, device_name, 
                             device_category, severity, keywords, metadata)
                            VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8, $9)
                        ''',
                            self.truncate(text, 1500),
                            embedding,
                            'classification',
                            self.truncate(item.get('device_class', 'Unknown'), 10),
                            self.truncate(item.get('device_name', ''), 200),
                            self.truncate(item.get('medical_specialty_description', 'general'), 100),
                            'medium',
                            self.truncate(f"class {item.get('device_class', '')}, medical device", 500),
                            json.dumps({'product_code': item.get('product_code')})
                        )
                        loaded_class += 1
                    except Exception as e:
                        errors += 1
                        if errors <= 5:
                            print(f"    Error: {str(e)[:100]}")
                        continue
                    
        except Exception as e:
            print(f"  ⚠️ Error loading device classifications: {str(e)[:100]}")
        
        print(f"  ✅ Loaded {loaded_recalls} device recalls")
        print(f"  ✅ Loaded {loaded_class} device classifications")
        print(f"  ✅ Loaded {loaded_electronics} medical electronics")
        if errors > 0:
            print(f"  ⚠️ {errors} records skipped due to errors")
        self.stats['device_recalls'] = loaded_recalls
        self.stats['device_class'] = loaded_class
    
    async def load_fda_drug_labels(self, conn, filepath='compliance_data_new/raw/drug-label-0001-of-0012.json'):
        """Load FDA drug label data"""
        print("\n🏷️ Loading FDA Drug Labels...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            loaded = 0
            errors = 0
            
            for item in results[:500]:  # Limited due to huge file
                if isinstance(item, dict):
                    brand = 'Unknown'
                    if item.get('openfda'):
                        brand_list = item.get('openfda', {}).get('brand_name', ['Unknown'])
                        if brand_list:
                            brand = brand_list[0]
                    
                    warnings = ''
                    if item.get('warnings'):
                        warnings_list = item.get('warnings', [''])
                        if warnings_list:
                            warnings = warnings_list[0]
                    
                    text = f"Drug Label for {brand}: {warnings}"
                    embedding = self.format_embedding(text)
                    
                    try:
                        await conn.execute('''
                            INSERT INTO fda_drug_labels
                            (rule_text, embedding, brand_name, warnings, label_section, 
                             severity, keywords, metadata)
                            VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8)
                        ''',
                            self.truncate(text, 1500),
                            embedding,
                            self.truncate(brand, 200),
                            self.truncate(warnings, 1000),  # TEXT field
                            self.truncate('warnings', 100),
                            'medium',
                            self.truncate(f"{brand}, warnings", 500),
                            json.dumps({})
                        )
                        loaded += 1
                    except Exception as e:
                        errors += 1
                        if errors <= 5:
                            print(f"    Error: {str(e)[:100]}")
                        continue
                    
            print(f"  ✅ Loaded {loaded} drug labels")
            if errors > 0:
                print(f"  ⚠️ {errors} records skipped due to errors")
            self.stats['drug_labels'] = loaded
            
        except Exception as e:
            print(f"  ⚠️ Error loading drug labels: {str(e)[:100]}")
    
    async def test_similarity_search(self, conn):
        """Test similarity search on loaded data"""
        print("\n🔍 Testing similarity search...")
        
        test_queries = [
            ("FDA approved supplement", "fda_drug_enforcement"),
            ("choking hazard toy", "cpsc_recalls"),
            ("undeclared peanuts", "fda_food_enforcement"),
            ("medical device software", "fda_device_data")
        ]
        
        for query_text, table_name in test_queries:
            try:
                embedding = self.format_embedding(query_text)
                
                results = await conn.fetch(f'''
                    SELECT rule_text, 1 - (embedding <=> $1::vector) as similarity
                    FROM {table_name}
                    ORDER BY embedding <=> $1::vector
                    LIMIT 3
                ''', embedding)
                
                print(f"\n  Query: '{query_text}' in {table_name}")
                for r in results:
                    print(f"    Similarity: {r['similarity']:.2%} | {r['rule_text'][:80]}...")
            except Exception as e:
                print(f"  ⚠️ Could not test {table_name}: {str(e)[:50]}")

    async def print_summary(self, conn):
        """Print summary statistics"""
        print("\n" + "="*50)
        print("📊 LOADING COMPLETE - Summary Statistics:")
        print("="*50)
        
        tables = [
            ('cpsc_recalls', 'CPSC Product Safety'),
            ('fda_drug_enforcement', 'FDA Drug Enforcement'),
            ('fda_food_enforcement', 'FDA Food Safety'),
            ('fda_device_data', 'FDA Medical Devices'),
            ('fda_drug_labels', 'FDA Drug Labels'),
            ('electronics_compliance', 'Electronics Compliance')
        ]
        
        total_records = 0
        for table_name, display_name in tables:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {table_name}')
                print(f"  {display_name}: {count:,} records")
                total_records += count
            except:
                print(f"  {display_name}: Table not found")
        
        print(f"\n  📊 TOTAL RECORDS LOADED: {total_records:,}")
        print("\n🎯 Ready for AG2 Multi-Agent System!")
        print("  Each agent can now query their specialized table")

async def main():
    loader = ComprehensiveDataLoader()
    
    print("🚀 Starting ComplianceMonster Data Loading...")
    print("  Connecting to Neon database...")
    
    conn = await asyncpg.connect(loader.DATABASE_URL)
    
    try:
        # Load ALL 6 datasets
        await loader.load_cpsc_recalls(conn)                    # Dataset 1: CPSC
        await loader.load_fda_drug_enforcement(conn)            # Dataset 2: FDA Drug
        await loader.load_fda_food_enforcement(conn)            # Dataset 3: FDA Food
        await loader.load_fda_device_data(conn)                 # Dataset 4 & 5: FDA Device (recall + classification)
        await loader.load_fda_drug_labels(conn)                 # Dataset 6: FDA Drug Labels
        
        # Test similarity search
        await loader.test_similarity_search(conn)
        
        # Print summary
        await loader.print_summary(conn)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())