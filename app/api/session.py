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
    source_id: str,
    top_k: Optional[int] = None,
    session_service: SessionService = Depends(get_session_service),
    query_service: QueryService = Depends(get_query_service),
    user_id = Depends(get_current_user),
):
    # 1. Save the User's message to Supabase immediately
    session_service.add_message(
        user_id=user_id,
        session_id=request.session_id, 
        role="user", 
        content=request.message
    )
    
    # 2. Generate Response
    ai_response = query_service.query(
        user_id=user_id,
        session_id=request.session_id,
        top_k=top_k,
        source_id=source_id
    )
    
    # 3. Save the response to the same session
    session_service.add_message(
        user_id=user_id,
        session_id=request.session_id, 
        role="assistant", 
        content=ai_response
    )
    print("Endpoint completed")
    return {"response": ai_response}

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
def clear_session(session_id: str, service: SessionService = Depends(get_session_service)):
    """Wipe the history for a session."""
    service.delete_session(session_id=session_id)
    return {"status": "deleted"}