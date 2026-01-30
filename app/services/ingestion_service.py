from fastapi import Depends, HTTPException, UploadFile
import os
# from app.services.chunk import ChunkService
from app.schemas.ingestion_source import IngestionSource
from app.services import chunk_service, transcript_service, vector_db, embedding_service
from langchain_community.document_loaders import PyPDFLoader
from sqlalchemy.orm import Session
from app.core.database import get_db

_ingestion_service_instance = None

class IngestionService:
    def __init__(self, transcript_service: transcript_service.TranscriptService, chunk_service: chunk_service.ChunkService, embedding_service: embedding_service.EmbeddingService,vector_db_service:vector_db.VectorDBService, db: Session):
        self.transcript_service = transcript_service
        self.chunk_service = chunk_service
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.db = db

    def register_source(self, user_id: str, source_id: str, source_type: str, display_name: str):
        # Create a new record instance
        new_source = IngestionSource(
            user_id=user_id,
            source_id=source_id,
            source_type=source_type,
            display_name=display_name
        )
        
        # Use merge (upsert) to handle re-uploads gracefully
        self.db.merge(new_source)
        self.db.commit()

    def get_user_sources(self, user_id: str):
        return self.db.query(IngestionSource).filter(IngestionSource.user_id == user_id).all()

    def delete_by_source_id(self, user_id: str, source_id: str):
        # 1. Pinecone Clean-up
        vector_success = self.vector_db_service.delete_by_source(user_id, source_id)
        
        # 2. SQL Clean-up
        source_record = self.db.query(IngestionSource).filter(
            IngestionSource.user_id == user_id,
            IngestionSource.source_id == source_id
        ).first()
        
        if source_record:
            try:
                self.db.delete(source_record)
                self.db.commit()
                sql_sucess = True
            except Exception:
                self.db.rollback()
                sql_sucess = False

        if vector_success and sql_sucess:
            return {
                    "status": "success", 
                    "message": f"Archive wiped. Removed source {source_id} for user_{user_id}."
                }
        
        return {
            "status": "Error",
            "message": "Wipe incomplete. Check logs for database or vector sync issues."
        }

    def delete_by_user(self, user_id: str):
        """
        DANGEROUS: Deletes everything for the current user. 
        Ensures SQL and Vector DB stay in sync.
        """
        # 1. Clear Pinecone
        vector_success = self.vector_db_service.delete_by_user(user_id)
        
        # 2. Clear SQL
        try:
            num_deleted = self.db.query(IngestionSource).filter(
                IngestionSource.user_id == user_id
            ).delete(synchronize_session=False) 
            
            self.db.commit()
            sql_success = True
        except Exception:
            self.db.rollback()
            sql_success = False

        # 3. Combined Response
        if vector_success and sql_success:
            return {
                "status": "success", 
                "message": f"Archive wiped. Removed {num_deleted} sources for user_{user_id}."
            }
        
        return {
            "status": "Error",
            "message": "Wipe incomplete. Check logs for database or vector sync issues."
        }

    def process_video(self, video_id: str, user_id: str, max_chars: int = 2000, overlap_chars: int = 300):
        transcript = self.transcript_service.get_transcript(video_id=video_id)
        segments = [{"text": s.text, "start": s.start, "duration": s.duration} for s in transcript.snippets]
        return self._run_ingestion_pipeline(segments=segments, user_id=user_id, source_id=video_id, display_name=transcript.title,source_type="video", max_chars=max_chars, overlap_chars=overlap_chars)
    
    async def process_pdf(self, file: UploadFile, user_id: str, max_chars: int = 2000, overlap_chars: int = 300):
        # 1. Temporarily save the file because PyPDFLoader needs a path
        temp_file_path = f"temp_{user_id}_{file.filename}"
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        try:
            # 2. Extract text using LangChain
            loader = PyPDFLoader(temp_file_path)
            pages = loader.load()
            full_text = "\n".join([p.page_content for p in pages])
            
            segments = [{"text": full_text, "start": 0.0, "duration": 0.0}]
            
            # 3. Run the shared pipeline
            return self._run_ingestion_pipeline(segments=segments, user_id=user_id, source_id=file.filename, display_name=file.filename, source_type="pdf", max_chars=max_chars, overlap_chars=overlap_chars)
        
        except Exception as e:
            print (f"Error when processing pdf: {e}")
            
        finally:
            # 4. Clean up
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    # In your _run_ingestion_pipeline
    def _run_ingestion_pipeline(self, segments, user_id: str, source_id: str, source_type: str, display_name: str, max_chars: int, overlap_chars: int):
            existing = self.db.query(IngestionSource).filter_by(
                user_id=user_id, 
                source_id=source_id
            ).first()

            if existing:
                return {"status": "Failed", "message": "Source already exist."}
            
            # 1. Chunking

            chunk_response = self.chunk_service.get_chunks(segments=segments, source_id=source_id, max_chars=max_chars, overlap_chars=overlap_chars)
            chunks = chunk_response.chunk
            
            if not chunks:
                return {"status": "success", "total_count": 0, "message": "No chunks generated."}

            # 2. Embedding
            texts_to_embed = [c.text for c in chunks]
            vectors = self.embedding_service.embed_texts(texts_to_embed)

            # 3. Metadata & Namespace Preparation
            documents_to_ingest = []
            for i, (chunk_model, vector_data) in enumerate(zip(chunks, vectors)):
                chunk_dict = chunk_model.model_dump(exclude_none=True)
                chunk_id = f"{source_id}_chunk_{i}"
                chunk_dict["id"] = chunk_id
                chunk_dict["vector"] = vector_data
                chunk_dict["metadata"] = {
                    "user_id": user_id,
                    "source": source_id,
                    "source_type": source_type
                }
                documents_to_ingest.append(chunk_dict)

            # 4. Ingest into Pinecone (Pass the user_id as namespace)
            pinecone_response = self.vector_db_service.ingest_documents(
                documents=documents_to_ingest, 
                namespace=f"user_{user_id}"
            )

            self.register_source(
                user_id=user_id,
                source_id=source_id,
                source_type=source_type,
                display_name=display_name
            )

            return pinecone_response

def get_ingestion_service(
        transcript_service: transcript_service.TranscriptService = Depends(transcript_service.get_transcript_service),
        chunk_service: chunk_service.ChunkService = Depends(chunk_service.get_chunk_service),
        embedding_service: embedding_service.EmbeddingService = Depends(embedding_service.get_embedding_service),
        vector_db_service: vector_db.VectorDBService = Depends(vector_db.get_vector_db_service),
        db: Session = Depends(get_db)
):
    global _ingestion_service_instance
    if not _ingestion_service_instance:
        _ingestion_service_instance = IngestionService(transcript_service=transcript_service, chunk_service=chunk_service, embedding_service=embedding_service,vector_db_service=vector_db_service, db=db)
    
    return _ingestion_service_instance
