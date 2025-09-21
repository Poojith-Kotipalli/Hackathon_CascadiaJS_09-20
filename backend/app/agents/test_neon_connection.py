# test_neon_connection.py
import os
import sys
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd

load_dotenv()

def test_neon_connection():
    """Test connection to Neon PostgreSQL"""
    print("=" * 50)
    print("TESTING NEON DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        # Get connection string
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found in .env")
            return False
            
        print(f"✅ Database URL found: {DATABASE_URL[:30]}...")
        
        # Test with SQLAlchemy
        engine = create_engine(DATABASE_URL)
        
        # Test query
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            
            tables = result.fetchall()
            print(f"\n✅ Connected to Neon! Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Check for products table
            result = conn.execute(text("""
                SELECT COUNT(*) FROM products
            """))
            count = result.scalar()
            print(f"\n✅ Products table has {count} records")
            
            # Check for violations tables
            violation_tables = ['fda_violations', 'cpsc_violations', 'ftc_violations']
            for table in violation_tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"✅ {table}: {count} records")
                except:
                    print(f"⚠️ {table}: not found")
            
            # Check for pgvector extension
            result = conn.execute(text("""
                SELECT * FROM pg_extension WHERE extname = 'vector'
            """))
            if result.fetchone():
                print("\n✅ pgvector extension is installed")
            else:
                print("⚠️ pgvector extension not found")
                
            # Test embedding search (if you have embeddings)
            try:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'products' 
                    AND data_type = 'USER-DEFINED'
                """))
                vector_columns = result.fetchall()
                if vector_columns:
                    print(f"✅ Found vector columns: {[col[0] for col in vector_columns]}")
            except:
                pass
                
        return True
        
    except Exception as e:
        print(f"❌ Database Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_compliance_check():
    """Test if your OLD compliance system is still working"""
    print("\n" + "=" * 50)
    print("TESTING EXISTING COMPLIANCE SYSTEM")
    print("=" * 50)
    
    try:
        # Try to import your existing compliance function
        from agents.compliance_agents import check_compliance
        
        # Test with a sample product
        test_text = "Children's toy with bright paint"
        result = check_compliance(test_text)
        
        print(f"✅ Existing compliance check works!")
        print(f"Result: {result}")
        return True
        
    except ImportError as e:
        print(f"⚠️ No existing check_compliance function found")
        print(f"This is OK if you're replacing it with the new system")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_neon_connection()
    test_existing_compliance_check()