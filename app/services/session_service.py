# app/services/session_db.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import delete
from app.schemas.session import ChatSession, ChatMessage
from typing import List
from app.core.database import get_db
from fastapi import Depends

class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_session(self, session_id: str, user_id: str) -> ChatSession:
        """Ensures a session exists in the cloud before adding messages."""
        try:
            session = self.db.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.id == session_id).first()
            if not session:
                session = ChatSession(id=session_id, user_id=user_id)
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)
            return session
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Error in get_or_create_session: {e}")
            raise e

    def add_message(self, session_id: str, user_id: str, role: str, content: str):
        """Persists a single message to the cloud database."""
        try:
            # Step 1: Ensure session exists
            self.get_or_create_session(user_id=user_id, session_id = session_id)
            
            # Step 2: Add message
            message = ChatMessage(user_id=user_id, session_id=session_id, role=role, content=content)
            self.db.add(message)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Error adding message to session {session_id}: {e}")
            raise e

    def get_history(self, session_id: str, user_id: str, limit: int = 10) -> List[ChatMessage]:
        """Retrieves the last X messages. No try/catch needed for simple reads."""
        return self.db.query(ChatMessage)\
            .filter( ChatMessage.user_id == user_id, ChatMessage.session_id == session_id)\
            .order_by(ChatMessage.timestamp.asc())\
            .limit(limit)\
            .all()
    
    def delete_session(self, session_id: str):#, user_id: str):
        """Wipes a session and all its messages using cascading deletes."""
        try:
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                #ChatSession.user_id == user_id
            ).first()
            if session:
                self.db.delete(session)
                self.db.commit()
                return True
            else:
                return False
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Error deleting session {session_id}: {e}")
            raise e

def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    return SessionService(db)