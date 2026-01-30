from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.services.session_service import SessionService, get_session_service
from app.schemas.session import ChatMessage
from app.schemas.chat_request import ChatRequest
from app.core.auth import get_current_user

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)

@router.post("/")
async def chat_with_video(
    request: ChatRequest, 
    service: SessionService = Depends(get_session_service),
    user_id = Depends(get_current_user)
):
    # 1. Save the User's message to Supabase immediately
    service.add_message(
        user_id=user_id,
        session_id=request.session_id, 
        role="user", 
        content=request.message
    )
    
    # 2. (Placeholder)
    ai_response = f"I'm processing your question about the video: {request.message}"
    
    # 3. Save the AI's response to the same session
    service.add_message(
        user_id=user_id,
        session_id=request.session_id, 
        role="assistant", 
        content=ai_response
    )
    
    return {"response": ai_response}

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
            "context": msg.content,
            "timestamp": msg.timestamp
        } for msg in history], 
        "message": "No history found."}

@router.delete("/{session_id}")
def clear_session(session_id: str, service: SessionService = Depends(get_session_service)):
    """Wipe the history for a session."""
    service.delete_session(session_id=session_id)
    return {"status": "deleted"}