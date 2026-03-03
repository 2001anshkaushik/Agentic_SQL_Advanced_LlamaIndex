"""
Database Configuration and Query Execution

This module handles PostgreSQL database connections and SQL query execution.
Uses SQLAlchemy for connection management with robust connection pooling.
"""

# ================== Imports ==================
import os
import pandas as pd
from sqlalchemy import create_engine, text


# ================== Functions ==================

def get_db_engine():
    """
    Create SQLAlchemy engine for PostgreSQL database connection.
    
    Constructs connection string from environment variables for secure configuration.
    The engine uses connection pooling automatically for improved performance.
    
    Returns:
        Engine: SQLAlchemy engine configured for PostgreSQL with connection string:
        - **Format**: postgresql://user:password@host:port/database
        - **Components**: Loaded from POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST,
          POSTGRES_PORT, and POSTGRES_DB environment variables
    """
    connection_string = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(connection_string, echo=False)


def run_sql_query(query: str) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a Pandas DataFrame.
    
    Uses SQLAlchemy's text() function to safely handle raw SQL strings. Results are
    converted to a DataFrame immediately for easy manipulation and passing between tools.
    
    Args:
        query: SQL query string in PostgreSQL syntax. Must be a valid SELECT statement
            that can be executed against the robot_vacuum_orders table.
    
    Returns:
        pd.DataFrame: Query results with:
        - **Columns**: Automatically inferred from query result column names
        - **Rows**: All rows returned by the query
        - **Types**: Preserved from PostgreSQL (NUMERIC, INTEGER, VARCHAR, TIMESTAMP, etc.)
    
    Raises:
        Exception: If the SQL query execution fails. The error message includes details
            about what went wrong (syntax errors, missing columns, connection issues, etc.).
    """
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
    except Exception as e:
        raise Exception(f"SQL query execution failed: {str(e)}")

