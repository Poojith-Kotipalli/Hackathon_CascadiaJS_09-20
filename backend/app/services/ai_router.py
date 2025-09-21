# backend/app/services/ai_router.py
import time
import logging
import asyncio
import httpx
import google.generativeai as genai
from typing import Dict, Any
import json
import re
from ..config import settings

logger = logging.getLogger(__name__)

class AIRouter:
    def __init__(self):
        self.ollama_base = settings.OLLAMA_HOST
        
        # Configure Gemini
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini configured successfully")
        else:
            logger.warning("⚠️ No Gemini API key found")
        
        logger.info(f"🔧 Ollama base URL: {self.ollama_base}")
        
    async def route(self, task_type: str, prompt: str, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        
        # Route based on task complexity
        if task_type == "realtime":
            logger.info("📡 Routing to Ollama for realtime check...")
            response = await self.call_local(prompt)
            model_used = "ollama-llama3.2"
        else:
            logger.info("🌐 Routing to Gemini for complex analysis...")
            response = await self.call_gemini(prompt)
            model_used = "gemini-1.5-flash"
            
        return {
            "response": response,
            "latency_ms": (time.time() - start_time) * 1000,
            "model_used": model_used
        }
    
    async def call_local(self, prompt: str) -> str:
        """Call Ollama running locally"""
        try:
            logger.info("🔄 Calling Ollama...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": "llama3.2:3b",  # Make sure you have this model
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()["response"]
                logger.info(f"✅ Ollama responded: {len(result)} chars")
                return result
        except httpx.ConnectError:
            error_msg = "❌ Cannot connect to Ollama. Make sure Ollama is running (ollama serve)"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            logger.error(f"❌ Ollama error: {e}")
            # Fallback to Gemini if local fails
            logger.info("🔄 Falling back to Gemini...")
            return await self.call_gemini(prompt)
    
    async def call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            if not settings.GEMINI_API_KEY:
                return "❌ Gemini API key not configured"
            
            logger.info("🔄 Calling Gemini...")
            # Run in thread since it's not async
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, prompt
            )
            result = response.text
            logger.info(f"✅ Gemini responded: {len(result)} chars")
            return result
        except Exception as e:
            error_msg = f"❌ Gemini error: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def get_structured_response(self, prompt: str, model_type: str = "realtime") -> Dict:
        """Get AI response in structured JSON format"""
        structured_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON in this exact format:
{{
    "compliant": true/false,
    "violations": ["violation1", "violation2"],
    "severity": "high/medium/low",
    "suggestions": ["suggestion1", "suggestion2"],
    "confidence": 0.0-1.0
}}"""
        
        result = await self.route(model_type, structured_prompt)
        
        # Try to parse JSON from response
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', result['response'], re.DOTALL)
            if json_match:
                result['parsed'] = json.loads(json_match.group())
            else:
                result['parsed'] = None
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            result['parsed'] = None
        
        return result