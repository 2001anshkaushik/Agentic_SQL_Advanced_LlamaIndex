"""
LLM and Embedding Configuration

This module handles initialization of OpenAI language models and embeddings.
Uses gpt-4o-mini for cost-effective SQL and code generation, and text-embedding-3-small
for efficient vector embeddings.
"""

# ================== Imports ==================
import os
from pathlib import Path
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# ================== Configuration ==================
# Load environment variables from .env file in the src directory
load_dotenv(Path(__file__).parent.parent / '.env')


# ================== Functions ==================

def initialize_llm():
    """
    Initialize OpenAI LLM with gpt-4o-mini model.
    
    Uses low temperature (0.1) for deterministic and consistent query generation,
    which is critical for database operations.
    
    Returns:
        OpenAI: Configured OpenAI LLM instance with:
        - **model**: gpt-4o-mini
        - **temperature**: 0.1 (for deterministic output)
        - **api_key**: Loaded from OPENAI_API_KEY environment variable
    """
    return OpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )


def initialize_embeddings():
    """
    Initialize OpenAI Embeddings with text-embedding-3-small model.
    
    Returns:
        OpenAIEmbedding: Configured OpenAI embedding instance with:
        - **model**: text-embedding-3-small
        - **api_key**: Loaded from OPENAI_API_KEY environment variable
    """
    return OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )

