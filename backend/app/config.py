import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # NEW: Added OpenAI key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # App Settings
    APP_NAME = "ComplianceMonster"
    VERSION = "0.1.0"
    DEBUG = True
    
    # CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]

settings = Settings()