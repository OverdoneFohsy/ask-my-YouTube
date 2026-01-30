from fastapi import APIRouter, Depends, UploadFile
from app.services.ingestion_service import IngestionService, get_ingestion_service
from app.core.auth import get_current_user

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

@router.get("/")
def get_user_sources(
    user_id = Depends(get_current_user),
    ingestion_service = Depends(get_ingestion_service)
):
    # Pass current_user.id so the service knows which namespace to use
    response = ingestion_service.get_user_sources(
        user_id=user_id
    )

    return response

@router.post("/video")
def process_video_pipeline(
    video_id:str, 
    max_chars: int = 2000, 
    overlap_chars: int = 300, 
    user_id = Depends(get_current_user),
    ingestion_service: IngestionService = Depends(get_ingestion_service)):

    response = ingestion_service.process_video(video_id=video_id, user_id=user_id, max_chars=max_chars, overlap_chars=overlap_chars)

    return response

@router.post("/pdf")
async def ingest_pdf_pipeline(
    file: UploadFile,
    user_id = Depends(get_current_user),
    ingestion_service = Depends(get_ingestion_service)
):
    # Pass current_user.id so the service knows which namespace to use
    response = await ingestion_service.process_pdf(
        file=file, 
        user_id=user_id
    )

    return response

@router.delete("/user")
def clear_by_user(
    user_id = Depends(get_current_user),
    ingestion_service = Depends(get_ingestion_service)
):
    return ingestion_service.delete_by_user(
        user_id=user_id,
    )

@router.delete("/user/source")
def clear_by_source(
    source_id: str,
    user_id = Depends(get_current_user),
    ingestion_service = Depends(get_ingestion_service)
):
    return ingestion_service.delete_by_source_id(
        user_id=user_id,
        source_id=source_id
    )

