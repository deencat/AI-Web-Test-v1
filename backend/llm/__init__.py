"""
LLM clients for Phase 3 multi-agent system.

Available clients:
- AzureClient: Enterprise Azure OpenAI (GPT-4o)
- CerebrasClient: Fast, free Llama inference
- LocalVllmClient: On-premises vLLM OpenAI-compatible servers (Sprint 10.13)
"""

from llm.azure_client import AzureClient, get_azure_client
from llm.cerebras_client import CerebrasClient, get_cerebras_client
from llm.local_vllm_client import LocalVllmClient

__all__ = [
    "AzureClient",
    "get_azure_client",
    "CerebrasClient",
    "get_cerebras_client",
    "LocalVllmClient",
]
