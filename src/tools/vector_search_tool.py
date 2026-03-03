"""
Vector Search Tool for Semantic Search on ReviewText

This module implements a vector search tool for finding reviews based on semantic similarity.
It uses LlamaIndex VectorStoreIndex with ChromaDB for persistent local storage of embeddings,
enabling semantic search on ReviewText for complaint queries and similar analysis tasks.
"""

# ================== Imports ==================
import json
from typing import Optional
from pathlib import Path
import logging
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import NodeWithScore

from config.llm import initialize_embeddings

# Global cache for vector store index
_vector_index: Optional[VectorStoreIndex] = None
logger = logging.getLogger(__name__)


# ================== Vector Store Initialization ==================

def get_or_create_vector_index() -> VectorStoreIndex:
    """
    Get or create the vector store index for ReviewText semantic search.
    
    This function loads the persistent ChromaDB vector store from src/data/chroma_db.
    The index is cached globally to avoid rebuilding on every query. If ChromaDB
    doesn't exist, it falls back to generating embeddings on-the-fly.
    
    Returns:
        VectorStoreIndex: Configured index for semantic search on ReviewText
    
    Raises:
        ValueError: If ChromaDB doesn't exist and no fallback is available
    """
    global _vector_index
    
    # Return cached index if available
    if _vector_index is not None:
        return _vector_index
    
    # Define ChromaDB path (persistent local storage)
    chroma_db_path = Path(__file__).parent.parent / 'data' / 'chroma_db'
    
    # Try to load from ChromaDB (persistent storage)
    if chroma_db_path.exists():
        try:
            from llama_index.vector_stores.chroma import ChromaVectorStore
            import chromadb
            
            logger.info(f"Loading vector index from ChromaDB at {chroma_db_path}")
            
            # Initialize ChromaDB client with existing persistent storage
            chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
            
            # Get the collection
            collection_name = "review_embeddings"
            try:
                chroma_collection = chroma_client.get_collection(name=collection_name)
            except Exception as e:
                logger.warning(f"Could not load ChromaDB collection '{collection_name}': {e}")
                logger.warning("Vector index may not have been created yet. Run db_setup.py first.")
                raise ValueError(f"ChromaDB collection not found. Please run db_setup.py to create it.")
            
            # Create ChromaVectorStore from existing collection
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Load embeddings model
            embeddings = initialize_embeddings()
            
            # Load existing index from ChromaDB
            _vector_index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=embeddings,
                storage_context=storage_context
            )
            
            logger.info("Successfully loaded vector index from ChromaDB")
            return _vector_index
            
        except ImportError as e:
            logger.error(f"Could not import ChromaDB modules: {str(e)}")
            logger.error("Please install: pip install chromadb llama-index-vector-stores-chroma")
            raise
        except Exception as e:
            logger.error(f"Error loading ChromaDB vector index: {str(e)}")
            raise
    
    else:
        # ChromaDB doesn't exist - need to run db_setup.py first
        error_msg = (
            f"ChromaDB vector store not found at {chroma_db_path}. "
            "Please run 'python src/db_setup.py' first to create the vector store."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)


# ================== Tool Function ==================

def vector_search_tool_function(query: str, top_k: int = 10) -> str:
    """
    Perform semantic search on ReviewText to find reviews matching the query.
    
    This function uses vector similarity search to find reviews that are semantically
    similar to the query text. Useful for finding complaints, specific feedback topics,
    or analyzing review content. Uses ChromaDB for persistent, fast semantic search.
    
    Args:
        query: Search query text describing what to find in reviews
               (e.g., "battery issues", "delivery problems", "defective product")
        top_k: Number of most similar reviews to return (default: 10)
    
    Returns:
        str: JSON string with search results containing:
        - **matches**: List of matching reviews with metadata
        - **count**: Number of matches found
        - **query**: The search query used
    """
    try:
        # Get or create vector index
        index = get_or_create_vector_index()
        
        # Create query engine
        query_engine = index.as_query_engine(similarity_top_k=top_k)
        
        # Perform semantic search
        response = query_engine.query(query)
        
        # Extract results
        results = []
        if hasattr(response, 'source_nodes'):
            for node_with_score in response.source_nodes:
                if isinstance(node_with_score, NodeWithScore):
                    node = node_with_score.node
                    score = node_with_score.score
                else:
                    node = node_with_score
                    score = getattr(node_with_score, 'score', None)
                
                result = {
                    'review_text': node.text,
                    'similarity_score': float(score) if score is not None else None,
                    'metadata': node.metadata or {}
                }
                results.append(result)
        
        # Build response
        response_data = {
            "query": query,
            "count": len(results),
            "matches": results,
            "message": f"Found {len(results)} reviews matching your query"
        }
        
        return json.dumps(response_data, indent=2, default=str)
        
    except Exception as e:
        import traceback
        logger.error(f"Vector search failed: {str(e)}")
        logger.error(traceback.format_exc())
        return json.dumps({
            "error": f"Vector search failed: {str(e)}",
            "query": query,
            "hint": "Make sure you have run 'python src/db_setup.py' to create the ChromaDB vector store."
        })


# ================== Tool Creation ==================

def create_vector_search_tool() -> FunctionTool:
    """
    Create a FunctionTool wrapper for the vector search tool.
    
    This tool enables semantic search on ReviewText, allowing the agent to find
    reviews based on meaning rather than exact keyword matching. Essential for
    complaint queries and review content analysis. Uses ChromaDB for persistent storage.
    
    Returns:
        FunctionTool: Configured tool instance that the agent can call with:
        - **name**: "vector_search_tool"
        - **description**: Explains semantic search capability for ReviewText
        - **function**: vector_search_tool_function
    """
    return FunctionTool.from_defaults(
        fn=vector_search_tool_function,
        name="vector_search_tool",
        description=(
            "REQUIRED for semantic search on customer review text (ReviewText column). "
            "MUST be used when the user asks about complaints, issues, problems, sentiment, "
            "or any qualitative analysis of review content. "
            "DO NOT use SQL filters like 'ReviewRating < 3' to infer complaints - use this tool instead. "
            "This tool searches reviews by meaning using embeddings, not just keywords. "
            "Uses ChromaDB for fast, persistent semantic search. "
            "Input should be a natural language query describing what to find in reviews. "
            "Returns matching reviews with their text, metadata (product, rating, etc.), "
            "and similarity scores. "
            "Example queries: 'battery problems', 'delivery issues', 'defective products', "
            "'customer complaints about quality'. "
            "After getting results from this tool, you can use sql_tool to aggregate by product or other dimensions."
        )
    )
