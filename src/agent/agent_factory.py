"""
Agent Factory for Creating ReAct Agents

This module creates and configures the LlamaIndex ReAct agent with SQL and visualization
tools. Uses a factory pattern to keep agent creation logic separate from the tools
and prompts, making it easier to test and modify agent configuration independently.
"""

# ================== Imports ==================
from typing import Optional
from llama_index.core.agent import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI

from config.llm import initialize_llm
from tools.sql_tool import create_sql_tool
from tools.visualizer_tool import create_visualizer_tool
from tools.vector_search_tool import create_vector_search_tool
from agent.prompts import get_system_prompt


# ================== Functions ==================

def create_agent(llm: Optional[OpenAI] = None, verbose: bool = True) -> ReActAgent:
    """
    Create and configure the ReAct Agent with SQL and visualization tools.
    
    Assembles all components needed for the agent: the LLM, tools, memory buffer, and
    system prompt. Uses ChatMemoryBuffer to maintain conversation context across queries.
    Max iterations set to 20 to allow complex multi-step reasoning while preventing loops.
    
    Args:
        llm: Optional OpenAI LLM instance. If not provided, initializes a new one using
            initialize_llm(). Allows callers to provide a custom LLM for testing or
            different model configurations.
        verbose: Whether to enable verbose logging. When True, prints detailed reasoning
            steps, useful for debugging but can be noisy in production.
    
    Returns:
        ReActAgent: Fully configured agent instance with:
        - **Tools**: sql_tool, python_visualizer_tool, and vector_search_tool
        - **LLM**: gpt-4o-mini (or provided LLM)
        - **Memory**: ChatMemoryBuffer for conversation context
        - **Context**: System prompt with database schema and instructions
        - **Max iterations**: 20 (allows complex reasoning without infinite loops)
    """
    # Initialize LLM if not provided
    if llm is None:
        llm = initialize_llm()
    
    # Create tools
    # Creates fresh tool instances for each agent instance
    sql_tool = create_sql_tool()
    python_visualizer_tool = create_visualizer_tool()
    vector_search_tool = create_vector_search_tool()
    
    # Get system prompt with database schema and instructions
    system_prompt = get_system_prompt()
    
    # Create memory buffer for conversation context
    # ChatMemoryBuffer maintains a simple conversation history that allows the agent
    # to reference previous queries and responses
    memory = ChatMemoryBuffer.from_defaults()
    
    # Create and configure the ReAct agent
    # ReAct (Reasoning + Acting) is a pattern where the agent reasons about what to do,
    # takes action using tools, observes results, and repeats until it has an answer
    agent = ReActAgent(
        tools=[sql_tool, python_visualizer_tool, vector_search_tool],
        llm=llm,
        memory=memory,
        verbose=verbose,
        context=system_prompt,
        max_iterations=20  # Increased to handle complex warehouse queries
    )
    
    return agent

