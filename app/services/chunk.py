from fastapi import APIRouter, HTTPException
from app.schemas.transcript import TranscriptResponse
from app.schemas.chunk import ChunkResponse, Chunk
from app.core.chunker import chunk_transcript

class ChunkService:
    
    def get_chunks(
        self,
        transcript: TranscriptResponse,
        max_chars: int = 2000,
        overlap_chars: int = 300
    ):
        try:
            segments = [{
                "text": snippet.text,
                "start": snippet.start,
                "duration": snippet.duration
            } for snippet in transcript.snippets]

            chunks = chunk_transcript(
                segments=segments,
                max_chars=max_chars,
                overlap_chars=overlap_chars
            )

            chunk_model = [
                Chunk( video_id = transcript.video_id,
                text = chunk["text"],
                start = chunk["start"],
                end = chunk["end"]
                ) for chunk in chunks
            ]

            response = ChunkResponse(video_id = transcript.video_id, chunk = chunk_model)

            return response

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )

def get_chunk_service():
    return ChunkService()
