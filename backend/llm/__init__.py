"""
LLM clients for Phase 3 multi-agent system.

Available clients:
- AzureClient: Enterprise Azure OpenAI (GPT-4o)
- CerebrasClient: Fast, free Llama inference
"""

from llm.azure_client import AzureClient, get_azure_client
from llm.cerebras_client import CerebrasClient, get_cerebras_client

__all__ = [
    "AzureClient",
    "get_azure_client",
    "CerebrasClient",
    "get_cerebras_client"
]
