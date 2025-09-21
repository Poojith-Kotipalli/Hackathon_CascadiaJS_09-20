# backend/app/services/compliance_engine.py
import asyncpg
from typing import Dict, List, Any
from sentence_transformers import SentenceTransformer
import json
import os
from ..services.ai_router import AIRouter
from ..config import settings

class ComplianceEngine:
    def __init__(self):
        self.ai_router = AIRouter()
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.neon_url = os.getenv("DATABASE_URL")
        
    async def search_compliance_rules(self, text: str, limit: int = 5) -> List[Dict]:
        """Search for relevant compliance rules using semantic search"""
        
        # Create embedding for the product text
        query_embedding = self.embedder.encode([text])[0].tolist()
        query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Connect to Neon
        conn = await asyncpg.connect(self.neon_url)
        
        try:
            # Semantic search for relevant rules
            results = await conn.fetch(
                """
                SELECT 
                    rule_text,
                    source,
                    severity,
                    keywords,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM compliance_rules
                WHERE 1 - (embedding <=> $1::vector) > 0.3  -- Similarity threshold
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                query_embedding_str, limit
            )
            
            return [dict(r) for r in results]
            
        finally:
            await conn.close()
    
    async def check_compliance(self, text: str, check_type: str = "realtime") -> Dict[str, Any]:
        """Enhanced compliance check with RAG from Neon"""
        
        # Get relevant rules from Neon using RAG
        relevant_rules = await self.search_compliance_rules(text)
        
        # Build context from retrieved rules
        context = "\n\n".join([
            f"[{rule['source']} - {rule['severity'].upper()}]: {rule['rule_text']}"
            for rule in relevant_rules[:3]  # Top 3 most relevant
        ])
        
        # Create structured prompt
        prompt = f"""You are an e-commerce compliance expert. Analyze this product listing for violations.

RELEVANT COMPLIANCE RULES:
{context}

PRODUCT LISTING TO CHECK:
"{text}"

Analyze for compliance violations based on the rules above. Return ONLY valid JSON:
{{
    "compliant": true/false,
    "violations": ["specific violation 1", "specific violation 2"],
    "severity": "high/medium/low",
    "suggestions": ["how to fix violation 1", "how to fix violation 2"],
    "confidence": 0.0-1.0
}}"""
        
        # Get AI analysis with structured response
        ai_result = await self.ai_router.get_structured_response(prompt, check_type)
        
        # Use parsed response if available, otherwise create default
        if ai_result.get('parsed'):
            analysis = ai_result['parsed']
        else:
            analysis = {
                "compliant": True,
                "violations": ["Could not parse AI response"],
                "severity": "low",
                "suggestions": ["Please try again"],
                "confidence": 0.5
            }
        
        # Calculate compliance score
        score = 100.0
        if not analysis.get('compliant'):
            if analysis.get('severity') == 'high':
                score -= 40
            elif analysis.get('severity') == 'medium':
                score -= 25
            else:
                score -= 10
        
        score = max(0, score) if not analysis.get('compliant') else 100
        
        return {
            "compliant": analysis.get("compliant", True),
            "score": score,
            "violations": analysis.get("violations", []),
            "suggestions": analysis.get("suggestions", []),
            "severity": analysis.get("severity", "low"),
            "confidence": analysis.get("confidence", 0.5),
            "relevant_rules": [
                {
                    "source": rule["source"],
                    "similarity": f"{rule['similarity']:.2%}",
                    "text_preview": rule["rule_text"][:100] + "..."
                }
                for rule in relevant_rules[:3]
            ],
            "model_used": ai_result["model_used"],
            "latency_ms": ai_result["latency_ms"]
        }