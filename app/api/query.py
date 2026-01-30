from fastapi import APIRouter, Depends
from app.services.query_service import QueryService, get_query_service
from app.core.auth import get_current_user

router = APIRouter(prefix="/query", tags=["query"])

@router.post("/")
def query_response(
    question: str,
    session_id: str,
    top_k: int=5,
    source_id: str=None,
    user_id = Depends(get_current_user),
    query_service: QueryService = Depends(get_query_service)
):
    response = query_service.query(user_id=user_id, question=question, session_id=session_id, top_k= top_k, source_id=source_id)

    return response