from fastapi import APIRouter, Depends
from app.services.ingestion_service import IngestionService, get_ingestion_service
router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

@router.get("/")
def process_video_pipeline(
    video_id:str, 
    max_chars: int = 2000, 
    overlap_chars: int = 300, 
    ingestopm_service: IngestionService = Depends(get_ingestion_service)):

    response = ingestopm_service.process_video(video_id=video_id, max_chars=max_chars, overlap_chars=overlap_chars)

    return response
