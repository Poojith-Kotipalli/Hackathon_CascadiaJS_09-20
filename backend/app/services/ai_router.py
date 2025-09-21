# backend/app/services/ai_router.py
import time
import logging
import asyncio
import httpx
from openai import OpenAI  # NEW: Added OpenAI import
import google.generativeai as genai
from typing import Dict, Any
import json
import re
from ..config import settings

logger = logging.getLogger(__name__)

class AIRouter:
    def __init__(self):
        self.ollama_base = settings.OLLAMA_HOST
        
        # NEW: Configure OpenAI
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.openai_model = "gpt-4o-mini"
            logger.info("✅ OpenAI configured successfully")
        else:
            logger.warning("⚠️ No OpenAI API key found")
        
        # Keep Gemini as fallback
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini configured as fallback")
        
    async def route(self, task_type: str, prompt: str, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        
        # Route to OpenAI instead of Ollama/Gemini
        if task_type == "realtime":
            logger.info("📡 Routing to OpenAI for realtime check...")
            response = await self.call_openai(prompt)  # CHANGED: call_openai instead of call_local
            model_used = "gpt-4o-mini"
        else:
            logger.info("🌐 Routing to OpenAI for complex analysis...")
            response = await self.call_openai(prompt)  # CHANGED: call_openai instead of call_gemini
            model_used = "gpt-4o-mini"
            
        return {
            "response": response,
            "latency_ms": (time.time() - start_time) * 1000,
            "model_used": model_used
        }
    
    async def call_openai(self, prompt: str) -> str:  # NEW: Added OpenAI method
        """Call OpenAI API"""
        try:
            logger.info("🔄 Calling OpenAI...")
            # Run in thread since it's not async
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a compliance expert. Provide detailed analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                top_p=0.9
            )
            result = response.choices[0].message.content
            logger.info(f"✅ OpenAI responded: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"❌ OpenAI error: {e}")
            # Fallback to Gemini if OpenAI fails
            if settings.GEMINI_API_KEY:
                logger.info("🔄 Falling back to Gemini...")
                return await self.call_gemini(prompt)
            else:
                return f"❌ OpenAI error and no fallback available: {str(e)}"
    
    async def call_local(self, prompt: str) -> str:  # KEPT: In case you want to use it later
        """Call Ollama running locally"""
        try:
            logger.info("🔄 Calling Ollama...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": "llama3.2:3b",
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
        except Exception as e:
            logger.error(f"❌ Ollama error: {e}")
            return await self.call_openai(prompt)  # CHANGED: Fallback to OpenAI
    
    async def call_gemini(self, prompt: str) -> str:  # KEPT: As fallback
        """Call Google Gemini API"""
        try:
            if not settings.GEMINI_API_KEY:
                return "❌ Gemini API key not configured"
            
            logger.info("🔄 Calling Gemini...")
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