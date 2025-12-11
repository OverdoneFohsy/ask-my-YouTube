from typing import List
from fastapi import APIRouter, Depends

from app.services.embedding_service import EmbeddingService, get_embedding_service

router = APIRouter(prefix="/embedding", tags=["Embedding"])

@router.post("/")
def get_embedding(
    texts: List[str],
    service: EmbeddingService = Depends(get_embedding_service)
    ):
    return service.embed_texts(texts=texts)