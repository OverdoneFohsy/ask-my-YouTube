from fastapi import APIRouter, Depends
from app.schemas.transcript import TranscriptResponse
from app.schemas.chunk import ChunkResponse
from app.services.chunk_service import ChunkService, get_chunk_service

router = APIRouter(prefix="/chunk", tags=["Chunk"])

@router.post("/", response_model = ChunkResponse)
def get_chunk(
    transcript: TranscriptResponse,
    max_chars: int = 2000,
    overlap_chars: int = 300,
    service: ChunkService = Depends(get_chunk_service)
):
    return service.get_chunks(transcript=transcript, max_chars=max_chars, overlap_chars=overlap_chars)


