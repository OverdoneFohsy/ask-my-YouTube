import os
from typing import List, Dict, Any, Union
from pinecone import Pinecone 
from itertools import islice
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_HOST = os.environ.get("PINECONE_HOST") 
COLLECTION_NAME = os.environ.get("PINECONE_INDEX_NAME")
BATCH_SIZE = 100 

# --- Singleton Class for the DB Connection ---
class VectorDBService:
    """
    A service class to abstract all interactions with the Pinecone vector store.
    """
    def __init__(self, index: "Index"): 
        self.index = index
        self.namespace = "default"

    def ingest_documents(self, documents: List[Dict[str, Any]], namespace: str) -> Dict[str, Union[str, int]]:
        """
        Takes processed documents and performs a batched upsert into the Pinecone index, 
        returning status and count.
        """
        vectors_to_upsert = []
        
        # Format documents for Pinecone upsert
        for i, doc in enumerate(documents):
            # Generate a unique ID using the source_id (filename or video_id)
            source_id = doc['metadata'].get("source_id", "unknown")
            chunk_id = f"{source_id}-{i}"
            
            # Use the flexible metadata passed from IngestionService
            vectors_to_upsert.append({
                "id": chunk_id,
                "values": doc['vector'], 
                "metadata": {
                    "text": doc['text'],
                    **doc['metadata']  # Spreads user_id, source_id, source_type, etc.
                }
            })
            
        total_count = 0
        
        # Helper for batching the upsert requests
        def batch_iterator(iterable, size):
            it = iter(iterable)
            while True:
                chunk = list(islice(it, size))
                if not chunk:
                    return
                yield chunk

        # 2. Perform batched upsert
        for batch in batch_iterator(vectors_to_upsert, BATCH_SIZE): 
            try:
                self.index.upsert(
                    vectors=batch, 
                    namespace=namespace
                )
                total_count += len(batch)
            except Exception as e:
                print(f"Pinecone Upsert Error: {e}")
                raise HTTPException(status_code=500, detail=f"Pinecone upsert failed: {str(e)}")

        return {
            "status": "success",
            "total_count": total_count
        }

    def query_documents(self, query_vector: List[float], filter: dict, top_k: int = 5, source_id: str = None, namespace: str = None) -> List[Dict[str, Any]]:
        """
        Performs a similarity search using the query vector to retrieve relevant chunks (Retrieval step).
        """
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter = filter,
                include_values=False,
                include_metadata=True,
                namespace=namespace
            )
            
        except Exception as e:
            print(f"Pinecone Query Error: {e}")
            raise HTTPException(status_code=500, detail=f"Pinecone query failed: {str(e)}")

        retrieved_documents = []

        # 3. Structure the results for the RAG pipeline
        for match in results.matches:
            # Extract the stored text and other metadata
            text_content = match.metadata.pop("text") 
            retrieved_documents.append({
                "text": text_content,
                "metadata": match.metadata,
                "score": match.score
            })
            
        return retrieved_documents

    def delete_by_user(self, user_id: str):
            try:
                # We target the specific user's namespace
                namespace = f"user_{user_id}"
                
                # Delete all vectors where the 'source' metadata matches
                self.index.delete(
                    delete_all=True,
                    namespace=namespace
                )
                return True
            except Exception as e:
                print(f"Error deleting from Pinecone: {e}")
                return False
    
    def delete_by_source(self, user_id: str, source_id: str):
        """
        Removes all vectors associated with a specific file or video 
        for a specific user.
        """
        try:
            namespace = f"user_{user_id}"

            # self.index.delete(
            #     filter={
            #         "user_id": {"$eq": user_id},
            #         "source_id": {"$eq": source_id}
            #     }
            # )
            self.index.delete(
                    namespace=namespace,
                    filter={"source_id": {"$eq": source_id}}
                )
            return True
        except Exception as e:
            print(f"Error deleting from Pinecone: {e}")
            return False

# --- Factory Function for FastAPI Dependency Injection (Requires Index type hint) ---

_db_service_instance: "VectorDBService" = None

def get_vector_db_service() -> VectorDBService:
    """
    FastAPI dependency factory function. 
    Initializes the VectorDBService as a singleton for thread-safe access.
    """
    global _db_service_instance

    if _db_service_instance is None:
        if not PINECONE_API_KEY or not PINECONE_HOST:
            raise RuntimeError("PINECONE_API_KEY and PINECONE_HOST environment variables must be set.")
        
        try:
            from pinecone import Pinecone # Ensure Pinecone is accessed here
            pc = Pinecone(api_key=PINECONE_API_KEY)

            index = pc.Index(host=PINECONE_HOST) 

            
            index_stats = index.describe_index_stats() 
            print(f"Successfully connected to Pinecone Index: {COLLECTION_NAME}. Total vectors: {index_stats.total_vector_count}")

            _db_service_instance = VectorDBService(index)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize VectorDBService with Pinecone. Ensure API Key/Host are correct and the index exists. Error: {str(e)}")
            
    return _db_service_instance