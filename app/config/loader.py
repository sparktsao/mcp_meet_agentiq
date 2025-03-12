"""
Configuration loading module.
"""
import os
import json
from typing import List, Dict, Any

# Load Server Configuration from External File
CONFIG_FILE_PATH = "config.json"

def load_server_config():
    """Loads server configurations from an external JSON file."""
    if not os.path.exists(CONFIG_FILE_PATH):
        raise FileNotFoundError(f"Configuration file '{CONFIG_FILE_PATH}' not found.")
    
    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    # print(config_data)
    
    return config_data.get("servers", [])
