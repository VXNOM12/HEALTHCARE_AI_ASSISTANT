# utils.py (Utility Functions)
import json
import logging
from typing import Dict, Any
import os

def load_config(config_path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file {config_path} not found")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Config loading failed: {str(e)}")

def setup_logger():
    logger = logging.getLogger("chatbot")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger