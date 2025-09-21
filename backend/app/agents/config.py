import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class AgentConfig:
    """Configuration for AG2 compliance agents"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL = "gpt-4o-mini"  # Using the standard gpt-4o-mini model
    
    # Validate API key exists
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-proj-xxxxx":
        raise ValueError("Please set your actual OpenAI API key in the .env file")
    
    # LLM Config for AutoGen
    LLM_CONFIG = {
        "config_list": [{
            "model": "gpt-4o-mini",  # AutoGen might add date suffix
            "api_key": OPENAI_API_KEY,
            "temperature": 0.1,
            "max_tokens": 1000,
            "top_p": 0.95,
            # Add cost tracking
            "price": [0.15, 0.60]  # [$0.15 per 1M input, $0.60 per 1M output]
        }],
        "cache_seed": 42,
        "timeout": 30,
    }
    
    # Backend API Configuration  
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # Agent Roles and Responsibilities
    AGENTS = {
        "classifier": {
            "name": "ProductClassifier",
            "description": "Analyzes products and determines which compliance agents to activate",
            "triggers": ["all"]  # Always runs first
        },
        "cpsc": {
            "name": "CPSC_Safety_Expert", 
            "description": "Checks toy safety, lead paint, choking hazards, recalls",
            "triggers": ["toy", "children", "play", "game", "furniture", "baby"],
            "table": "cpsc_recalls"
        },
        "fda_food": {
            "name": "FDA_Food_Inspector",
            "description": "Verifies allergen labeling, food safety, contamination",
            "triggers": ["food", "snack", "drink", "organic", "natural", "ingredient", "allergen"],
            "table": "fda_food_enforcement"
        },
        "fda_drug": {
            "name": "FDA_Drug_Analyst",
            "description": "Checks supplements, drugs, health claims, banned substances",
            "triggers": ["supplement", "vitamin", "pill", "drug", "medicine", "health", "weight loss", "muscle"],
            "table": "fda_drug_enforcement"
        },
        "electronics": {
            "name": "Electronics_Safety_Expert",
            "description": "Verifies FCC compliance, battery safety, EMI standards",
            "triggers": ["electronic", "battery", "wireless", "charger", "phone", "led", "bluetooth"],
            "table": "electronics_compliance"
        },
        "medical": {
            "name": "FDA_Medical_Device_Expert",
            "description": "Checks medical device classifications and recalls",
            "triggers": ["medical", "device", "diagnostic", "therapeutic", "monitor", "implant"],
            "table": "fda_device_data"
        }
    }
    
    # Compliance Thresholds
    COMPLIANCE_THRESHOLDS = {
        "critical": 30,   # Below 30: Multiple major violations
        "warning": 60,    # 30-60: Significant issues
        "caution": 80,    # 60-80: Minor issues
        "pass": 100       # 80-100: Safe to list
    }
    
    # Token usage tracking
    MAX_TOKENS_PER_CHECK = 5000  # Approximately $0.002 per check