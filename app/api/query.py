from fastapi import APIRouter, Depends
from app.services.query_service import QueryService, get_query_service

router = APIRouter(prefix="/query", tags=["query"])

@router.get("/")
def query_response(
    question: str,
    top_k: int=5,
    video_id: str=None,
    query_service: QueryService = Depends(get_query_service)
):
    response = query_service.query(question=question, top_k= top_k, video_id=video_id)

    return response