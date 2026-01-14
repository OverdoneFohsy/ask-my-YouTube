from fastapi import Depends
from app.services import transcript_service, chunk, vector_db, embedding_service, llm_service

class QueryService:
    def __init__(self, embedding_service: embedding_service.EmbeddingService, vector_db_service: vector_db.VectorDBService, llm_service:llm_service.LLMService):
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.llm_service = llm_service

    def retrieve_context(self, question: str, top_k: int=5, video_id: str=None):
        try:
            print(f"Embedding query: {question}")
            query_vector = self.embedding_service.embed_texts([question])[0]
            if not query_vector:
                raise ValueError("Embedding service returned no data")

            print(f"retrieving documents:")# {query_vector}")
            result = self.vector_db_service.query_documents(query_vector, top_k=top_k, video_id=video_id)
            
            print(f"result: {result}")
            return result
        
        except Exception as e:
            print(f"Error in Retrieval Pipeline: {e}")
            return []
        
    def generate_response(self, question: str, context_chunks:list):
        try:
            response = self.llm_service.generate_response(question=question, context_chunks=context_chunks)
            
            return response
        
        except Exception as e:
            print(f"Error in Retrieval Pipeline: {e}")
            return None
        
    def query(self, question: str, top_k: int=5, video_id: str=None):
        chunks = self.retrieve_context(question=question, top_k=top_k, video_id=video_id)

        if not chunks:
            return {"answer": "No relevant info found.", "sources": []}
        
        answer = self.generate_response(question=question, context_chunks=chunks)

        return {
            "answer": answer,
            "sources": chunks
        }
        
def get_query_service(embedding_service: embedding_service.EmbeddingService = Depends(embedding_service.get_embedding_service),
                          vector_db_service: vector_db.VectorDBService = Depends(vector_db.get_vector_db_service),
                          llm_service: llm_service.LLMService = Depends(llm_service.get_llm_service)
                          ):
        return QueryService(embedding_service=embedding_service, vector_db_service=vector_db_service, llm_service=llm_service)

        