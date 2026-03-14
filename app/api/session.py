from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.services.query_service import QueryService, get_query_service
from app.services.session_service import SessionService, get_session_service
from app.schemas.session import ChatMessage
from app.schemas.chat_request import ChatRequest
from app.core.auth import get_current_user

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)

@router.post("/")
async def chat(
    request: ChatRequest, 
    session_service: SessionService = Depends(get_session_service),
    query_service: QueryService = Depends(get_query_service),
    user_id = Depends(get_current_user),
):
    ai_response = query_service.query(
        user_id=user_id,
        question=request.message,
        session_id=request.session_id,
        top_k=request.top_k,
        source_id=request.source_id
    )
    
    print("Endpoint completed")
    return {"response": ai_response["response"],
            "sources": ai_response["sources"]}

@router.get("/")
async def get_sessions(
    service: SessionService = Depends(get_session_service),
    user_id = Depends(get_current_user)
):
    return service.get_sessions(user_id=user_id)

@router.get("/history")
def get_chat_history(session_id:str, user_id = Depends(get_current_user), service: SessionService = Depends(get_session_service)):
    """Retrieve the full conversation history for a specific session."""
    history = service.get_history(user_id=user_id, session_id=session_id)

    if not history:
        return {"session_id": session_id, "history":[], "message": "No history found."}
    
    return {
        "session_id": session_id, 
        "history":[{
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp
        } for msg in history], 
        "message": "History retrieve successfully."}

@router.delete("/{session_id}")
def clear_session(session_id: str, user_id = Depends(get_current_user), service: SessionService = Depends(get_session_service)):
    """Wipe the history for a session."""
    success = service.delete_session(user_id=user_id, session_id=session_id)

    if not success:
        raise HTTPException(404, detail="Session not found")
    
    return {"status": "deleted"}

@router.delete("/")
def clear_session(user_id = Depends(get_current_user), service: SessionService = Depends(get_session_service)):
    """Wipe the history for a session."""
    success = service.delete_all_session(user_id=user_id)

    if not success:
        raise HTTPException(404, detail="Deletion Failed")
    
    return {"status": "deleted"}