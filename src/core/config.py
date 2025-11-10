# src/core/config.py
import os
from typing import Dict, Any
from dotenv import load_dotenv

def load_config() -> Dict[str, Any]:
    """Load configuration from environment and defaults"""
    load_dotenv()  # Load from .env file if present
    
    return {
        'threat_detection': {
            'enabled': True,
            'sensitivity': 'high',
            'patterns': []
        },
        'sanitization': {
            'enabled': True,
            'remove_patterns': []
        },
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO')
        },
        'quarantined_llm': {
            'model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.0')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '1000')),
            'api_key': os.getenv('OPENAI_API_KEY')  # Read from environment
        },
        'rule_engine': {
            'enabled': True,
            'strict_mode': True
        }
    }