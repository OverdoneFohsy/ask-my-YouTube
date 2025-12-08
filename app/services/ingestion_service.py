from fastapi import Depends
from app.services.transcript_service import TranscriptService
from app.services.chunk import ChunkService
from app.services.vector_db import VectorDBService

class IngestionService:
    def __init__(self, transcript_service: TranscriptService, chunk_service: ChunkService, vector_db_service:VectorDBService):
        self.transcript_service = transcript_service
        self.chunk_service = chunk_service
        self.vector_db_service = vector_db_service

    def process_video(self, video_id: str, max_chars: int = 2000, overlap_chars: int = 300):
        transcript_response = self.transcript_service.get_transcript(video_id=video_id)

        chunk_response = self.chunk_service.get_chunks(transcript=transcript_response, max_chars=max_chars, overlap_chars=overlap_chars)

        upload_status = self.vector_db_service.ingest_documents(documents=chunk_response)

        return upload_status

def get_ingestion_service(
        transcript_service: TranscriptService = Depends(TranscriptService()),
        chunk_service: ChunkService = Depends(ChunkService()),
        vector_db_service: VectorDBService = Depends(VectorDBService)
):
    return IngestionService(transcript_service=transcript_service, chunk_service=chunk_service, vector_db_service=vector_db_service)
