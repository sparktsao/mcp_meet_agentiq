"""
LLM client for making API calls to language models.
"""
import requests
from typing import List, Dict, Any

class SingleLLMClient:
    """
    Client for making API calls to a single LLM provider.
    """
    def __init__(self, endpoint: str, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the LLM client.
        
        Args:
            endpoint (str): The API endpoint.
            api_key (str): The API key.
            model (str): The model name.
        """
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model

    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """
        Invoke the LLM with the given messages.
        
        Args:
            messages (List[Dict[str, str]]): The messages to send to the LLM.
            
        Returns:
            str: The LLM response.
        """
        print()
        print("invoke:", self.model)
        print(f"\033[33m {messages} \033[0m")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        r = requests.post(f"{self.endpoint}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        print()
        print(f"\033[35m {data} \033[0m")
        return data["choices"][0]["message"]["content"]
