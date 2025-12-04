from fastapi import APIRouter, Depends

from app.services.transcript_service import TranscriptService, get_transcript_service

from app.schemas.transcript import TranscriptResponse

router = APIRouter(prefix="/transcript", tags=["Transcript"])

@router.get("/", response_model=TranscriptResponse)
def get_transcript(
    video_id: str,
    service: TranscriptService = Depends(get_transcript_service)
    ):
    return service.get_transcript(video_id=video_id)