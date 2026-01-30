from fastapi import Depends
from app.services import vector_db, embedding_service, llm_service, session_service
class QueryService:
    def __init__(self, embedding_service: embedding_service.EmbeddingService, vector_db_service: vector_db.VectorDBService, llm_service:llm_service.LLMService, session_service:session_service.SessionService):
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.llm_service = llm_service
        self.session_service = session_service

    def retrieve_context(self, user_id: str, question: str, top_k: int=5, source_id: str=None):
        try:
            print(f"Embedding query: {question}")
            query_vector = self.embedding_service.embed_texts([question])[0]
            if not query_vector:
                raise ValueError("Embedding service returned no data")

            metadata_filter = {"user_id": user_id}
            if source_id:
                metadata_filter["source_id"] = source_id
            print(f"retrieving documents:{query_vector}")
            result = self.vector_db_service.query_documents(query_vector, top_k=top_k, filter=metadata_filter, namespace=f"user_{user_id}")
            
            print(f"result: {result}")
            return result
        
        except Exception as e:
            print(f"Error in Retrieval Pipeline: {e}")
            return []
        
    def generate_response(self, question: str, context_chunks:list, history:list):
        try:
            response = self.llm_service.generate_response(question=question, context_chunks=context_chunks, history=history)
            
            return response
        
        except Exception as e:
            print(f"Error in Retrieval Pipeline: {e}")
            return None
        
    def query(self, question: str, user_id: str, session_id: str, top_k: int=5, source_id: str=None):
        history = self.session_service.get_history(user_id=user_id, session_id=session_id, limit=5)
        
        chunks = self.retrieve_context(user_id=user_id, question=question, top_k=top_k, source_id=source_id)
        
        answer = self.generate_response(question=question, context_chunks=chunks, history=history)

        if answer:
            try:
                self.session_service.add_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="user",
                    content=question
                )
                
                self.session_service.add_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="assistant",
                    content=answer
                )
            
            except Exception as e:
                print(f"Error saving chat history: {e}")

        return {
            "answer": answer,
            "sources": chunks
        }
        
def get_query_service(embedding_service: embedding_service.EmbeddingService = Depends(embedding_service.get_embedding_service),
                          vector_db_service: vector_db.VectorDBService = Depends(vector_db.get_vector_db_service),
                          llm_service: llm_service.LLMService = Depends(llm_service.get_llm_service),
                          session_service: session_service.SessionService = Depends(session_service.get_session_service)
                          ):
        return QueryService(embedding_service=embedding_service, vector_db_service=vector_db_service, llm_service=llm_service, session_service=session_service)

        

        