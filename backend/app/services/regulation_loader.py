import os
import json
import requests
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from pathlib import Path
import logging
import asyncpg
from pgvector.asyncpg import register_vector
import numpy as np
from sentence_transformers import SentenceTransformer
from ..config import settings
import PyPDF2
import io

logger = logging.getLogger(__name__)

class RegulationLoader:
    """
    Downloads REAL regulation datasets and stores in Neon PostgreSQL with pgvector
    """
    
    def __init__(self):
        self.data_dir = Path("backend/data/downloads")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Sentence transformer for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Neon PostgreSQL connection
        self.db_url = settings.DATABASE_URL
        
    async def setup_database(self):
        """Create tables in Neon PostgreSQL with pgvector"""
        
        conn = await asyncpg.connect(self.db_url)
        
        # Install pgvector extension
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        
        # Create regulations table with vector column
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS regulations (
                id SERIAL PRIMARY KEY,
                source TEXT,
                regulation_id TEXT,
                title TEXT,
                content TEXT,
                category TEXT,
                url TEXT,
                chunk_index INTEGER,
                embedding vector(384),  -- all-MiniLM-L6-v2 produces 384 dimensions
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Create index for vector similarity search
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS regulations_embedding_idx 
            ON regulations USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        ''')
        
        await conn.close()
        logger.info("Neon PostgreSQL tables created with pgvector")
    
    async def download_and_load_all_regulations(self):
        """Download REAL regulation data from actual sources"""
        
        await self.setup_database()
        
        # Check if already loaded
        conn = await asyncpg.connect(self.db_url)
        count = await conn.fetchval('SELECT COUNT(*) FROM regulations')
        await conn.close()
        
        if count > 0:
            logger.info(f"Found {count} existing regulations in Neon DB")
            return {"existing": count}
        
        results = {}
        
        # Download from REAL sources
        results['fda'] = await self.download_fda_data()
        results['ftc'] = await self.download_ftc_data()
        results['cpsc'] = await self.download_cpsc_data()
        results['cfr'] = await self.download_cfr_data()
        
        return results
    
    async def download_fda_data(self) -> int:
        """Download FDA data from openFDA API and FDA datasets"""
        
        chunks_added = 0
        
        # 1. FDA Recalls Dataset (REAL DATA)
        recalls_url = "https://api.fda.gov/food/enforcement.json?limit=100"
        try:
            response = requests.get(recalls_url)
            if response.status_code == 200:
                data = response.json()
                
                for result in data.get('results', []):
                    chunk = {
                        'source': 'FDA',
                        'regulation_id': f"FDA_RECALL_{result.get('recall_number', 'unknown')}",
                        'title': result.get('product_description', 'FDA Recall'),
                        'content': f"""
                        FDA Recall Information:
                        Product: {result.get('product_description', '')}
                        Reason: {result.get('reason_for_recall', '')}
                        Classification: {result.get('classification', '')}
                        Code Info: {result.get('code_info', '')}
                        """,
                        'category': 'recall',
                        'url': recalls_url
                    }
                    chunks_added += await self.store_regulation_chunk(chunk)
        except Exception as e:
            logger.error(f"Error downloading FDA recalls: {e}")
        
        # 2. FDA Warning Letters (REAL DATA)
        warning_letters_url = "https://api.fda.gov/food/compliance.json?limit=100"
        try:
            response = requests.get(warning_letters_url)
            if response.status_code == 200:
                data = response.json()
                
                for result in data.get('results', []):
                    chunk = {
                        'source': 'FDA',
                        'regulation_id': f"FDA_WARNING_{result.get('warning_letter_number', 'unknown')}",
                        'title': 'FDA Warning Letter',
                        'content': json.dumps(result),
                        'category': 'warning_letter',
                        'url': warning_letters_url
                    }
                    chunks_added += await self.store_regulation_chunk(chunk)
        except Exception as e:
            logger.error(f"Error downloading FDA warning letters: {e}")
        
        # 3. FDA Food Code (downloadable PDF/dataset)
        food_code_url = "https://www.fda.gov/media/164194/download"  # FDA Food Code 2022
        try:
            response = requests.get(food_code_url)
            if response.status_code == 200:
                # Parse PDF
                pdf_file = io.BytesIO(response.content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                for page_num, page in enumerate(pdf_reader.pages[:50]):  # First 50 pages
                    text = page.extract_text()
                    if text.strip():
                        chunk = {
                            'source': 'FDA',
                            'regulation_id': f'FDA_FOOD_CODE_2022_PAGE_{page_num}',
                            'title': f'FDA Food Code 2022 - Page {page_num}',
                            'content': text[:2000],  # Limit chunk size
                            'category': 'food_code',
                            'url': food_code_url
                        }
                        chunks_added += await self.store_regulation_chunk(chunk)
        except Exception as e:
            logger.error(f"Error downloading FDA Food Code: {e}")
        
        logger.info(f"Added {chunks_added} FDA regulation chunks to Neon")
        return chunks_added
    
    async def download_ftc_data(self) -> int:
        """Download FTC consumer complaints and enforcement data"""
        
        chunks_added = 0
        
        # FTC Consumer Sentinel Network Data (CSV dataset)
        sentinel_url = "https://www.ftc.gov/system/files/ftc_gov/csv/fraud_consumer_sentinel_en_2023_complaints.csv"
        
        try:
            # Download CSV
            response = requests.get(sentinel_url, stream=True)
            if response.status_code == 200:
                # Save locally first
                csv_path = self.data_dir / "ftc_complaints.csv"
                with open(csv_path, 'wb') as f:
                    f.write(response.content)
                
                # Read and process CSV
                import pandas as pd
                df = pd.read_csv(csv_path, nrows=1000)  # First 1000 rows
                
                # Group by violation type and create chunks
                for violation_type in df['Issue'].unique()[:50]:  # Top 50 issue types
                    if pd.notna(violation_type):
                        subset = df[df['Issue'] == violation_type]
                        
                        chunk = {
                            'source': 'FTC',
                            'regulation_id': f'FTC_COMPLAINT_TYPE_{violation_type.replace(" ", "_")}',
                            'title': f'FTC Complaints - {violation_type}',
                            'content': f"""
                            FTC Consumer Complaints for: {violation_type}
                            Number of complaints: {len(subset)}
                            Common issues: {subset['Consumer complaint narrative'].head(5).to_string() if 'Consumer complaint narrative' in subset.columns else 'N/A'}
                            This indicates potential FTC violations in this category.
                            """,
                            'category': 'consumer_complaints',
                            'url': sentinel_url
                        }
                        chunks_added += await self.store_regulation_chunk(chunk)
        except Exception as e:
            logger.error(f"Error downloading FTC data: {e}")
        
        return chunks_added
    
    async def download_cpsc_data(self) -> int:
        """Download CPSC recall and violation data"""
        
        chunks_added = 0
        
        # CPSC Recalls API (REAL DATA)
        cpsc_url = "https://www.saferproducts.gov/RestWebServices/Recall?format=json&limit=100"
        
        try:
            response = requests.get(cpsc_url)
            if response.status_code == 200:
                data = response.json()
                
                for recall in data[:100]:  # First 100 recalls
                    chunk = {
                        'source': 'CPSC',
                        'regulation_id': f"CPSC_RECALL_{recall.get('RecallNumber', 'unknown')}",
                        'title': recall.get('Title', 'CPSC Recall'),
                        'content': f"""
                        CPSC Recall:
                        Product: {recall.get('Products', [{}])[0].get('Name', '') if recall.get('Products') else ''}
                        Hazard: {recall.get('Hazards', [{}])[0].get('Name', '') if recall.get('Hazards') else ''}
                        Remedy: {recall.get('Remedies', [{}])[0].get('Name', '') if recall.get('Remedies') else ''}
                        Description: {recall.get('Description', '')}
                        """,
                        'category': 'product_recall',
                        'url': cpsc_url
                    }
                    chunks_added += await self.store_regulation_chunk(chunk)
        except Exception as e:
            logger.error(f"Error downloading CPSC data: {e}")
        
        return chunks_added
    
    async def download_cfr_data(self) -> int:
        """Download Code of Federal Regulations (CFR) data"""
        
        chunks_added = 0
        
        # eCFR API for Title 21 (FDA) and Title 16 (FTC/CPSC)
        cfr_titles = [
            {"title": 21, "parts": [101, 111, 201, 301]},  # FDA regulations
            {"title": 16, "parts": [255, 260, 1500, 1501]}  # FTC/CPSC regulations
        ]
        
        for title_info in cfr_titles:
            title = title_info["title"]
            for part in title_info["parts"]:
                url = f"https://www.ecfr.gov/api/versioner/v1/full/{title}/{part}?format=json"
                
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract regulation text
                        content = json.dumps(data.get('content', {}))[:3000]  # Limit size
                        
                        chunk = {
                            'source': 'CFR',
                            'regulation_id': f'{title}_CFR_{part}',
                            'title': f'Title {title} CFR Part {part}',
                            'content': content,
                            'category': 'federal_regulation',
                            'url': url
                        }
                        chunks_added += await self.store_regulation_chunk(chunk)
                except Exception as e:
                    logger.error(f"Error downloading CFR {title}.{part}: {e}")
        
        return chunks_added
    
    async def store_regulation_chunk(self, chunk: Dict) -> int:
        """Store regulation chunk in Neon PostgreSQL with embedding"""
        
        try:
            # Generate embedding
            embedding = self.model.encode(chunk['content'])
            
            # Store in Neon
            conn = await asyncpg.connect(self.db_url)
            await register_vector(conn)
            
            await conn.execute('''
                INSERT INTO regulations 
                (source, regulation_id, title, content, category, url, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', 
                chunk['source'],
                chunk['regulation_id'],
                chunk['title'],
                chunk['content'],
                chunk['category'],
                chunk['url'],
                embedding.tolist()
            )
            
            await conn.close()
            return 1
            
        except Exception as e:
            logger.error(f"Error storing chunk: {e}")
            return 0
    
    async def search_regulations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search regulations using pgvector similarity search in Neon"""
        
        # Generate query embedding
        query_embedding = self.model.encode(query)
        
        # Search in Neon PostgreSQL
        conn = await asyncpg.connect(self.db_url)
        await register_vector(conn)
        
        results = await conn.fetch('''
            SELECT 
                source, regulation_id, title, content, category, url,
                1 - (embedding <=> $1) as similarity
            FROM regulations
            ORDER BY embedding <=> $1
            LIMIT $2
        ''', query_embedding.tolist(), limit)
        
        await conn.close()
        
        return [dict(r) for r in results]