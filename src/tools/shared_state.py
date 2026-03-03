"""
Shared State Management for Tool Communication

This module manages global state that allows tools to share data with each other.
Uses a simple global variable approach to enable the SQL tool and visualization tool
to pass DataFrames between them in the agent workflow.
"""

# ================== Imports ==================
from typing import Optional
import pandas as pd


# ================== Shared State ==================
# Global variable to store the last query result dataframe
# This allows the visualization tool to access data from the SQL tool
_last_query_result: Optional[pd.DataFrame] = None


# ================== Functions ==================

def get_last_query_result() -> Optional[pd.DataFrame]:
    """
    Get the last SQL query result dataframe.
    
    This function retrieves the most recent DataFrame that was stored by the SQL tool.
    The visualization tool uses this to access data without needing to re-execute queries.
    
    Returns:
        Optional[pd.DataFrame]: The last query result, or None if no query has been executed yet.
    """
    return _last_query_result


def set_last_query_result(df: pd.DataFrame):
    """
    Set the last SQL query result dataframe.
    
    Stores a DataFrame so it can be accessed by subsequent tool calls. This pattern
    allows the visualization tool to access SQL results when the agent chains tool calls.
    
    Args:
        df: The DataFrame to store. This should be the result of a SQL query execution.
    """
    global _last_query_result
    _last_query_result = df

