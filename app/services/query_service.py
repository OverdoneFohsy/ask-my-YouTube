import os
from fastapi import Depends, HTTPException
from app.services import vector_db, embedding_service, llm_service, session_service
from pinecone import Pinecone

class QueryService:
    def __init__(self, embedding_service: embedding_service.EmbeddingService, vector_db_service: vector_db.VectorDBService, llm_service:llm_service.LLMService, session_service:session_service.SessionService):
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.llm_service = llm_service
        self.session_service = session_service
        self.pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

    def _retrieve_context(self, user_id: str, question: str, top_k: int=5, source_id: str=None):
        try:
            candidate_pool = 100

            print(f"Embedding query: {question}")
            query_vector = self.embedding_service.embed_texts([question])[0]
            if not query_vector or len(query_vector) == 0:
                raise ValueError("Embedding service returned no data")

            metadata_filter = {}
            if source_id:
                metadata_filter["source_id"] = source_id
            print(f"retrieving documents:{query_vector}")
            
            initial_result = self.vector_db_service.query_documents(query_vector, top_k=candidate_pool, filter={}, namespace=f"user_{user_id}")
            print(f"initial_result: {initial_result}")
            
            if not initial_result:
                print("No documents found in vector store.")
                return []
            
            rerank_results = self.pc.inference.rerank(
                model="bge-reranker-v2-m3",
                query=question,
                documents=[doc['text'] for doc in initial_result],
                top_n=top_k,
                return_documents=True
                )

            # 4. Format results to match original structure
            final_results = []
            for res in rerank_results.data:
                # Reconstruct the doc with its new score
                original_doc = next(d for d in initial_result if d['text'] == res.document['text'])
                original_doc['rerank_score'] = res.score
                final_results.append(original_doc)

            return final_results
        
        except Exception as e:
            print(f"Error in Retrieval Pipeline: {e}")
            raise e
        
    def _generate_response(self, question: str, context_chunks:list, history:list):
        try:
            response = self.llm_service.generate_response(question=question, context_chunks=context_chunks, history=history)
            
            return response
        
        except Exception as e:
            print(f"Error in Retrieval Pipeline: {e}")
            raise e
    
    def _generate_title(self, message: str, context_chunks:list):
        try:
            response = self.llm_service.generate_title(context_chunks=context_chunks, message=message)

            return response

        except Exception as e:
            print(f"Error in Retrieval Pipeline: {e}")
            raise e
        
    def query(self, question: str, user_id: str, session_id: str, top_k: int=5, source_id: str=None):
        history = self.session_service.get_history(user_id=user_id, session_id=session_id, limit=5)
        
        chunks = self._retrieve_context(user_id=user_id, question=question, top_k=top_k, source_id=source_id)
        
        response = self._generate_response(question=question, context_chunks=chunks, history=history)

        if response:
            try:
                session = self.session_service.add_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="user",
                    content=question
                )
                
                self.session_service.add_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="assistant",
                    content=response
                )

                if session and (not session.title):
                    generated_title = self._generate_title(question, chunks)
                    if generated_title:
                        session.title = generated_title
                        self.session_service.db.commit()
                
            except ValueError as e:
                if str(e) == "LLM_QUOTA_RECHED":
                    raise 
                raise HTTPException(status_code=500, detail=str(e))
            
            except Exception as e:
                print(f"Error saving chat history: {e}")

        return {
            "response": response,
            "sources": chunks
        }
        
def get_query_service(embedding_service: embedding_service.EmbeddingService = Depends(embedding_service.get_embedding_service),
                          vector_db_service: vector_db.VectorDBService = Depends(vector_db.get_vector_db_service),
                          llm_service: llm_service.LLMService = Depends(llm_service.get_llm_service),
                          session_service: session_service.SessionService = Depends(session_service.get_session_service)
                          ):
        return QueryService(embedding_service=embedding_service, vector_db_service=vector_db_service, llm_service=llm_service, session_service=session_service)

        

        