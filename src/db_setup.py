"""
Database Setup Script for Bonus Assignment 1
Loads RobotVacuumDepot_MasterData_v125.csv into Postgres database.

This script:
1. Loads environment variables from .env file
2. Reads CSV using Polaris (fast) and converts to Pandas
3. Connects to Postgres using psycopg2 and sqlalchemy
4. Creates/Recreates robot_vacuum_orders table (idempotent)
5. Bulk inserts all CSV data into Postgres
"""

import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

import polars as pl
import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.types import (
    VARCHAR, INTEGER, DECIMAL, DATE, TIMESTAMP, TEXT
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get script directory
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent


def load_environment_variables():
    """Load environment variables from .env file."""
    env_path = SCRIPT_DIR / '.env'
    
    if not env_path.exists():
        logger.error(f".env file not found at {env_path}")
        logger.error("Please copy env.example to .env and fill in your Postgres credentials")
        sys.exit(1)
    
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
    
    # Get Postgres connection details
    config = {
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
    }
    
    # Validate required variables
    missing = [k for k, v in config.items() if not v]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please check your .env file")
        sys.exit(1)
    
    return config


def create_database_if_not_exists(config):
    """Create database if it doesn't exist."""
    # Connect to default postgres database to create target database
    temp_config = config.copy()
    temp_config['database'] = 'postgres'
    
    try:
        conn = psycopg2.connect(**temp_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (config['database'],)
        )
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database: {config['database']}")
            cursor.execute(f'CREATE DATABASE "{config["database"]}"')
            logger.info(f"Database {config['database']} created successfully")
        else:
            logger.info(f"Database {config['database']} already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise


def get_csv_path():
    """Get path to CSV file."""
    # Check multiple possible locations for CSV
    possible_paths = [
        SCRIPT_DIR / 'data' / 'RobotVacuumDepot_MasterData_v125.csv',  # In src/data/ directory
        SCRIPT_DIR / 'RobotVacuumDepot_MasterData_v125.csv',  # In src/ directory (legacy)
        PROJECT_ROOT.parent / 'RobotVacuumDepot_MasterData_v125.csv',  # In Bonus_Assignment_1-1 directory
    ]
    
    for csv_path in possible_paths:
        if csv_path.exists():
            logger.info(f"Found CSV file at {csv_path}")
            return csv_path
    
    logger.error(f"CSV file not found in any of these locations:")
    for path in possible_paths:
        logger.error(f"  - {path}")
    logger.error("Please ensure RobotVacuumDepot_MasterData_v125.csv is in the src/ directory")
    sys.exit(1)


def load_csv_with_polars(csv_path):
    """Load CSV using Polaris (fast) and convert to Pandas."""
    logger.info("Loading CSV with Polaris...")
    
    try:
        # Read CSV with Polaris (fast)
        df_polars = pl.read_csv(csv_path)
        logger.info(f"Loaded {len(df_polars)} rows with Polaris")
        
        # Convert to Pandas
        df = df_polars.to_pandas()
        logger.info(f"Converted to Pandas DataFrame: {len(df)} rows, {len(df.columns)} columns")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading CSV: {str(e)}")
        raise


def prepare_dataframe_types(df):
    """Prepare DataFrame with correct data types for Postgres."""
    logger.info("Preparing DataFrame data types...")
    
    # Parse date columns (format: MM/DD/YYYY HH:MM)
    date_columns = [
        'OrderDate', 'LastRestockDate', 'LastUpdated', 
        'ExpectedDeliveryDate', 'ActualDeliveryDate', 'ReviewDate'
    ]
    
    for col in date_columns:
        if col in df.columns:
            # Convert to datetime, handling empty strings
            df[col] = pd.to_datetime(df[col], format='%m/%d/%Y %H:%M', errors='coerce')
    
    # Ensure numeric columns are properly typed
    numeric_columns = [
        'ShippingCost', 'ProductPrice', 'TaxAmount', 'DiscountAmount', 
        'TotalAmount', 'UnitPrice', 'ReviewRating'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            # Convert to numeric, handling empty strings
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Integer columns (explicitly convert to nullable integer)
    integer_columns = [
        'CustomerZipCode', 'BillingZipCode', 'DeliveryZipCode',
        'WarehouseZipCode', 'DistributionCenterZipCode',
        'StockLevel', 'WarehouseCapacity', 'LeadTimeDays',
        'ReliabilityScore', 'FleetSize', 'RestockThreshold',
        'Quantity'
    ]
    
    for col in integer_columns:
        if col in df.columns:
            # Convert to nullable integer (Int64 allows NaN)
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    
    logger.info("Data types prepared successfully")
    return df


def get_table_schema():
    """Define Postgres table schema with correct data types."""
    return {
        'OrderID': VARCHAR(50),
        'OrderDate': TIMESTAMP,
        'CustomerID': VARCHAR(50),
        'CustomerName': VARCHAR(255),
        'CustomerEmail': VARCHAR(255),
        'CustomerZipCode': INTEGER,
        'CustomerAddress': TEXT,
        'BillingZipCode': INTEGER,
        'BillingAddress': TEXT,
        'DeliveryStatus': VARCHAR(50),
        'DeliveryAddress': TEXT,
        'DeliveryZipCode': INTEGER,
        'ShippingCost': DECIMAL(10, 2),
        'ShippingCarrier': VARCHAR(50),
        'Region': VARCHAR(50),
        'ProductID': VARCHAR(50),
        'ProductName': VARCHAR(255),
        'ProductDescription': TEXT,
        'ModelNumber': VARCHAR(100),
        'ManufacturerID': VARCHAR(50),
        'ManufacturerName': VARCHAR(255),
        'ProductPrice': DECIMAL(10, 2),
        'TaxAmount': DECIMAL(10, 2),
        'DiscountAmount': DECIMAL(10, 2),
        'TotalAmount': DECIMAL(10, 2),
        'StockLevel': INTEGER,
        'WarehouseID': VARCHAR(50),
        'WarehouseAddress': TEXT,
        'WarehouseZipCode': INTEGER,
        'WarehouseCapacity': INTEGER,
        'DistributionCenterID': VARCHAR(50),
        'DistributionCenterAddress': TEXT,
        'DistributionCenterZipCode': INTEGER,
        'Segment': VARCHAR(50),
        'LeadTimeDays': INTEGER,
        'ReliabilityScore': INTEGER,
        'UnitPrice': DECIMAL(10, 2),
        'FleetSize': INTEGER,
        'RestockThreshold': INTEGER,
        'LastRestockDate': TIMESTAMP,
        'LastUpdated': TIMESTAMP,
        'Quantity': INTEGER,
        'PromoCode': VARCHAR(50),
        'ExpectedDeliveryDate': TIMESTAMP,
        'ActualDeliveryDate': TIMESTAMP,
        'PaymentMethod': VARCHAR(50),
        'CardNumber': VARCHAR(50),
        'CardBrand': VARCHAR(50),
        'ReviewID': VARCHAR(50),
        'ReviewRating': DECIMAL(3, 1),
        'ReviewText': TEXT,
        'ReviewDate': TIMESTAMP,
        'Country': VARCHAR(100),
    }


def get_postgres_type_string(sqlalchemy_type):
    """Convert SQLAlchemy type to Postgres SQL type string."""
    type_mapping = {
        VARCHAR: lambda t: f"VARCHAR({t.length})" if hasattr(t, 'length') and t.length else "VARCHAR",
        INTEGER: "INTEGER",
        DECIMAL: lambda t: f"DECIMAL({t.precision}, {t.scale})" if hasattr(t, 'precision') and hasattr(t, 'scale') else "DECIMAL",
        TEXT: "TEXT",
        TIMESTAMP: "TIMESTAMP",
        DATE: "DATE",
    }
    
    # Get the base type class
    type_class = type(sqlalchemy_type)
    
    if type_class in type_mapping:
        mapper = type_mapping[type_class]
        if callable(mapper):
            return mapper(sqlalchemy_type)
        return mapper
    
    # Fallback: try to get string representation
    if hasattr(sqlalchemy_type, 'compile'):
        return str(sqlalchemy_type.compile(dialect=engine.dialect))
    
    # Default fallback
    return "TEXT"


def create_or_recreate_table(engine, schema):
    """Create or recreate table (idempotent)."""
    table_name = 'robot_vacuum_orders'
    
    logger.info(f"Checking if table {table_name} exists...")
    
    inspector = inspect(engine)
    if table_name in inspector.get_table_names():
        logger.info(f"Table {table_name} exists. Dropping for clean state...")
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
            conn.commit()
        logger.info(f"Table {table_name} dropped successfully")
    
    logger.info(f"Creating table {table_name}...")
    
    # Create table SQL - properly convert SQLAlchemy types to Postgres types
    from sqlalchemy.dialects import postgresql
    postgres_dialect = postgresql.dialect()
    
    columns_sql = []
    for col_name, col_type in schema.items():
        # Convert SQLAlchemy type to Postgres type string
        if isinstance(col_type, VARCHAR):
            pg_type = f"VARCHAR({col_type.length})" if hasattr(col_type, 'length') and col_type.length else "VARCHAR"
        elif isinstance(col_type, INTEGER):
            pg_type = "INTEGER"
        elif isinstance(col_type, DECIMAL):
            precision = getattr(col_type, 'precision', 10)
            scale = getattr(col_type, 'scale', 2)
            pg_type = f"DECIMAL({precision}, {scale})"
        elif isinstance(col_type, TEXT):
            pg_type = "TEXT"
        elif isinstance(col_type, TIMESTAMP):
            pg_type = "TIMESTAMP"
        elif isinstance(col_type, DATE):
            pg_type = "DATE"
        else:
            # Fallback: use SQLAlchemy compiler on the instance
            try:
                pg_type = col_type.compile(dialect=postgres_dialect)
            except:
                pg_type = "TEXT"  # Ultimate fallback
        
        columns_sql.append(f'"{col_name}" {pg_type}')
    
    create_table_sql = f'''
    CREATE TABLE "{table_name}" (
        {', '.join(columns_sql)}
    )
    '''
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    logger.info(f"Table {table_name} created successfully")


def bulk_insert_data(engine, df, schema):
    """Bulk insert data into Postgres using pandas to_sql with proper type handling."""
    table_name = 'robot_vacuum_orders'
    
    logger.info(f"Bulk inserting {len(df)} rows into {table_name}...")
    
    try:
        # Convert Int64 columns to regular int64 if no NaNs (for better compatibility)
        # This ensures pandas to_sql properly recognizes integer types
        for col in df.columns:
            if df[col].dtype == 'Int64':
                if df[col].isna().any():
                    # Keep as Int64 if there are NaNs
                    continue
                else:
                    # Convert to regular int64 if no NaNs
                    df[col] = df[col].astype('int64')
                    logger.info(f"Converted {col} from Int64 to int64 (no NaNs)")
        
        # Use pandas to_sql with sqlalchemy engine
        # Note: dtype parameter should work, but we also ensure DataFrame types are correct
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000,  # Insert in batches
            dtype=schema
        )
        logger.info(f"Successfully inserted {len(df)} rows")
        
        # Fix any columns that were incorrectly inserted as TEXT
        # This is a workaround for pandas to_sql not always respecting dtype
        logger.info("Verifying and fixing column types if needed...")
        with engine.connect() as conn:
            # Check if Quantity is TEXT and needs to be converted to INTEGER
            result = conn.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'robot_vacuum_orders' 
                AND column_name = 'Quantity'
            """))
            qty_type = result.scalar()
            
            if qty_type == 'text':
                logger.info("Converting Quantity column from TEXT to INTEGER...")
                # Convert TEXT to INTEGER using ALTER TABLE
                conn.execute(text(f"""
                    ALTER TABLE "{table_name}" 
                    ALTER COLUMN "Quantity" TYPE INTEGER 
                    USING "Quantity"::INTEGER
                """))
                conn.commit()
                logger.info("Quantity column successfully converted to INTEGER")
        
    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")
        raise


def create_vector_store_and_embeddings(engine):
    """Create ChromaDB vector store and generate embeddings for ReviewText."""
    logger.info("Creating ChromaDB vector store and generating embeddings...")
    
    try:
        # Import ChromaDB dependencies
        try:
            from config.llm import initialize_embeddings
            from llama_index.core import VectorStoreIndex, Document, StorageContext
            from llama_index.vector_stores.chroma import ChromaVectorStore
            import chromadb
        except ImportError as e:
            logger.error(f"Could not import ChromaDB modules: {str(e)}")
            logger.error("Please install: pip install chromadb llama-index-vector-stores-chroma")
            raise
        
        # Check if OpenAI key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Skipping embedding generation.")
            logger.warning("Embeddings will be generated on-the-fly during queries.")
            return
        
        logger.info("OpenAI API key found. Generating embeddings...")
        
        # Define ChromaDB path (persistent local storage)
        chroma_db_path = SCRIPT_DIR / 'data' / 'chroma_db'
        
        # Delete existing ChromaDB directory for idempotency (fresh build)
        if chroma_db_path.exists():
            logger.info(f"Removing existing ChromaDB directory at {chroma_db_path} for fresh build...")
            import shutil
            shutil.rmtree(chroma_db_path)
            logger.info("Removed existing ChromaDB directory")
        
        # Create data directory if it doesn't exist
        chroma_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load embeddings model
        embeddings = initialize_embeddings()
        
        # Load ReviewText data from PostgreSQL
        query = """
            SELECT "ReviewID", "ReviewText", "ProductName", "ManufacturerName", 
                   "ReviewRating", "ReviewDate"
            FROM robot_vacuum_orders
            WHERE "ReviewText" IS NOT NULL 
            AND "ReviewText" != '' 
            AND LENGTH(TRIM("ReviewText")) > 0
        """
        
        import pandas as pd
        df = pd.read_sql(query, engine)
        
        if len(df) == 0:
            logger.warning("No ReviewText data found. Skipping embedding generation.")
            return
        
        logger.info(f"Found {len(df)} reviews with text. Generating embeddings...")
        
        # Initialize ChromaDB client with persistent storage
        chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
        
        # Create or get collection for reviews
        collection_name = "review_embeddings"
        try:
            chroma_client.delete_collection(collection_name)
            logger.info(f"Deleted existing collection '{collection_name}' for fresh build")
        except Exception:
            pass  # Collection doesn't exist, which is fine
        
        chroma_collection = chroma_client.create_collection(
            name=collection_name,
            metadata={"description": "ReviewText embeddings for semantic search"}
        )
        
        # Create LlamaIndex Documents from ReviewText
        documents = []
        for _, row in df.iterrows():
            doc_text = row['ReviewText']
            metadata = {
                'review_id': str(row['ReviewID']) if pd.notna(row['ReviewID']) else '',
                'product_name': str(row['ProductName']) if pd.notna(row['ProductName']) else '',
                'manufacturer_name': str(row['ManufacturerName']) if pd.notna(row['ManufacturerName']) else '',
                'review_rating': float(row['ReviewRating']) if pd.notna(row['ReviewRating']) else None,
                'review_date': str(row['ReviewDate']) if pd.notna(row['ReviewDate']) else '',
            }
            
            doc = Document(text=doc_text, metadata=metadata)
            documents.append(doc)
        
        logger.info(f"Created {len(documents)} documents from ReviewText")
        
        # Create ChromaVectorStore
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create VectorStoreIndex with embeddings (will generate and store embeddings)
        logger.info("Generating embeddings and building vector index...")
        logger.info("This may take a few minutes depending on the number of reviews...")
        
        vector_index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embeddings,
            show_progress=True
        )
        
        logger.info(f"Successfully created ChromaDB vector store at {chroma_db_path}")
        logger.info(f"Stored embeddings for {len(documents)} reviews in persistent ChromaDB")
        
        # Verify the index was created
        docstore = vector_index.storage_context.docstore
        doc_hashes = docstore.get_all_document_hashes()
        logger.info(f"Vector store contains {len(doc_hashes)} documents")
        
    except ImportError as e:
        logger.error(f"Could not import required modules: {str(e)}")
        logger.error("Please install: pip install chromadb llama-index-vector-stores-chroma")
        raise
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def verify_data_load(engine):
    """Verify data was loaded correctly."""
    table_name = 'robot_vacuum_orders'
    
    logger.info(f"Verifying data load for {table_name}...")
    
    with engine.connect() as conn:
        # Count rows
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        row_count = result.scalar()
        logger.info(f"Total rows in {table_name}: {row_count}")
        
        # Get sample row
        result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT 1'))
        sample = result.fetchone()
        if sample:
            logger.info("Sample row retrieved successfully")
        
    return row_count


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Starting Database Setup for Bonus Assignment 1")
    logger.info("=" * 60)
    
    try:
        # Step 1: Load environment variables
        config = load_environment_variables()
        
        # Step 2: Create database if not exists
        create_database_if_not_exists(config)
        
        # Step 3: Get CSV path
        csv_path = get_csv_path()
        
        # Step 4: Load CSV with Polaris and convert to Pandas
        df = load_csv_with_polars(csv_path)
        
        # Step 5: Prepare data types
        df = prepare_dataframe_types(df)
        
        # Step 6: Create SQLAlchemy engine
        connection_string = (
            f"postgresql://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['database']}"
        )
        engine = create_engine(connection_string, echo=False)
        logger.info(f"Connected to Postgres database: {config['database']}")
        
        # Step 7: Get table schema
        schema = get_table_schema()
        
        # Step 8: Create or recreate table (idempotent)
        create_or_recreate_table(engine, schema)
        
        # Step 9: Bulk insert data
        bulk_insert_data(engine, df, schema)
        
        # Step 10: Create ChromaDB vector store and generate embeddings
        create_vector_store_and_embeddings(engine)
        
        # Step 11: Verify load
        row_count = verify_data_load(engine)
        
        logger.info("=" * 60)
        logger.info("Database setup completed successfully!")
        logger.info(f"Total rows loaded: {row_count}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

