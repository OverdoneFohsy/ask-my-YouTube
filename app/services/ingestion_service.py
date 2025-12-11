from fastapi import Depends
# from app.services.chunk import ChunkService
from app.services import chunk_service, transcript_service, vector_db, embedding_service

class IngestionService:
    def __init__(self, transcript_service: transcript_service.TranscriptService, chunk_service: chunk_service.ChunkService, embedding_service: embedding_service.EmbeddingService,vector_db_service:vector_db.VectorDBService):
        self.transcript_service = transcript_service
        self.chunk_service = chunk_service
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service

    def process_video(self, video_id: str, max_chars: int = 2000, overlap_chars: int = 300):
        transcript_response = self.transcript_service.get_transcript(video_id=video_id)

        chunk_response = self.chunk_service.get_chunks(transcript=transcript_response, max_chars=max_chars, overlap_chars=overlap_chars)

        chunks = chunk_response.chunk

        texts_to_embed = [c.text for c in chunks]

        if not chunks:
            return {"status": "success", "total_count": 0, "message": "No chunks generated."}
        
        print(f"Generating embeddings for {len(texts_to_embed)} chunks...")

        vectors = self.embedding_service.embed_texts(texts_to_embed)

        if len(vectors) != len(texts_to_embed):
            raise RuntimeError(f"Embedding service vector count mismatch. Expected {len(chunks)}, got {len(vectors)}.")

        documents_to_ingest = []

        for chunk_model, vector_data in zip(chunks, vectors):

            chunk_model.vector = vector_data

            documents_to_ingest.append(chunk_model.model_dump(exclude_none=True))

        print(f"Starting ingestion of {len(documents_to_ingest)} documents into Pinecone...")

        upload_status = self.vector_db_service.ingest_documents(documents=documents_to_ingest)

        print(upload_status)

        return upload_status

def get_ingestion_service(
        transcript_service: transcript_service.TranscriptService = Depends(transcript_service.get_transcript_service),
        chunk_service: chunk_service.ChunkService = Depends(chunk_service.get_chunk_service),
        embedding_service: embedding_service.EmbeddingService = Depends(embedding_service.get_embedding_service),
        vector_db_service: vector_db.VectorDBService = Depends(vector_db.get_vector_db_service)
):
    return IngestionService(transcript_service=transcript_service, chunk_service=chunk_service, embedding_service=embedding_service,vector_db_service=vector_db_service)
