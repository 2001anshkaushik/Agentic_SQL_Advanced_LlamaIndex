"""Verify ChromaDB vector store was created successfully."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    
    chroma_db_path = Path(__file__).parent.parent / 'data' / 'chroma_db'
    
    if not chroma_db_path.exists():
        print(f"ERROR: ChromaDB directory not found at {chroma_db_path}")
        sys.exit(1)
    
    client = chromadb.PersistentClient(path=str(chroma_db_path))
    collection = client.get_collection('review_embeddings')
    
    count = collection.count()
    
    print(f"[OK] ChromaDB Verification Successful")
    print(f"   Collection: {collection.name}")
    print(f"   Documents stored: {count}")
    
    if count > 0:
        sample = collection.peek(limit=1)
        if sample['metadatas']:
            print(f"   Sample metadata keys: {list(sample['metadatas'][0].keys())}")
    
    if count == 3350:
        print(f"   [OK] Expected count (3350) matches!")
    else:
        print(f"   [WARNING] Expected 3350, found {count}")
    
except ImportError as e:
    print(f"ERROR: Could not import chromadb: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

