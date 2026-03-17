from fastapi import Depends, HTTPException
from app.services import vector_db, embedding_service, llm_service, session_service
from sentence_transformers import CrossEncoder

class QueryService:
    def __init__(self, embedding_service: embedding_service.EmbeddingService, vector_db_service: vector_db.VectorDBService, llm_service:llm_service.LLMService, session_service:session_service.SessionService):
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.llm_service = llm_service
        self.session_service = session_service
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

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

            pairs = [[question, doc['text']] for doc in initial_result]
            rerank_scores = self.reranker.predict(pairs)

            for i, doc in enumerate(initial_result):
                doc['rerank_score'] = float(rerank_scores[i])

            reranked_result = sorted(
                initial_result,
                key=lambda x: x['rerank_score'],
                reverse=True
            )[:10]

            print(f"reranked_result: {reranked_result}")

            return reranked_result
        
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
        
    # def _update_session_title(self, user_id: str, session_id: str, question: str, chunks: list):
    #     """
    #     Refines the session title using LLM without blocking the main response.
    #     Reuses chunks already fetched during the main query.
    #     """
    #     try:

    #         session = self.session_service.get_or_create_session(user_id=user_id, session_id=session_id)
            
    #         # 2. Final check: Only generate if title is empty or the "..." fallback
    #         if session and (not session.title or "..." in session.title):
    #             print(f"Background Task: Generating refined title for session {session_id}")
                
    #             # 3. Call your LLM title generation method
    #             refined_title = self._generate_title(message=question, context_chunks=chunks)

    #             if refined_title:
                    
    #                 # 4. Use the "Black Magic": Update the attribute and commit
    #                 session.title = refined_title
    #                 self.session_service.db.commit()
    #                 print(f"Background Task: Title successfully updated to '{refined_title}'")
    #             else:
    #                 print("Background Task: LLM returned no title, skipping update.")
                    
    #     except Exception as e:
    #         # Important: Rollback the session if anything goes wrong in the background
    #         if self.session_service.db:
    #             self.session_service.db.rollback()
    #         print(f"Error in Background Title Update: {e}")
        
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

        

        